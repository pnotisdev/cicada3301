//! h5rs: the Rust engine for the H5 first slice (drift-tracking decoder of the two-stack model,
//! docs/HYPOTHESES.md H1), ported with bit-exact parity from work/h5slice (the verified Python
//! reference: h5slice.beam_coincidence_nats / h5slice_nb / h5slice.decode).
//!
//!   c_i = D(p_i) + t_j + w_(j mod L) + b   (mod 29)
//!
//! with the anti-repeat rule on the combined key k_j = t_j + w_(j mod L) + b:
//!   * model 0 ("skip"): on a collision the encryptor re-draws with the next key value,
//!     probability q = 1 - keep = 0.81 per attempt, up to 5 attempts;
//!   * model 1 ("coin"): on a collision one key value is always spent, then with
//!     probability 1 - keep the value is re-drawn from the next key value.
//! and the optional literal-F rule (plaintext F passes through, consumes no key position).
//!
//! Decoder per (offset, L): a nats-scored coincidence init beam over FREE pointer branches
//! (+1/+2/+3 per rune, plus the literal-F branch), scored by the per-column SHIFT-MARGINALIZED
//! English log-likelihood G[col,v] = sum_i logf[(x_i - v) mod 29], score =
//! sum_col logsumexp_v G[col,v] + skips*ln(0.028); then est_cols (per-column ML shift) and an EM
//! over the keyword columns with collision-consistency skip branches (model 0 skip with
//! keep q = 0.81), scoring the periodic IoC of the final columns (docs/HYPOTHESES.md:70-78).
//!
//! Engines:
//!   scalar     - the numba-exact reference port (flat G buffers, one logsumexp of 29 exps per
//!                candidate; identical merge/tie-break/abort semantics to h5slice_nb.py)
//!   fastscalar - the algebraically identical normalized-vector port (no exps at all: the state
//!                keeps the sum-1-normalized column vectors u = exp(G - M)/sum; the score
//!                increment of a letter is ln(sum_v u_v * f[(q-v) mod 29]), one log per
//!                candidate; scores agree with the reference within ~1e-12 nats)
//!   fast       - fastscalar with AVX2/FMA intrinsics (x86_64 only)
//!
//! The totient stream is generated internally: t_n = p_n - 1 mod 29 (the library's
//! "primes-1 (totient)", work/keystreams.py:44).

use std::env;
use std::fs;
use std::io::{BufWriter, Write};
use std::process::exit;

mod logf;
use logf::{LN028, LN29, LOGF, UNI};

const Q: usize = 29;

// ------------------------------------------------------------------ mod-29 tables

const fn build_sub() -> [[u8; Q]; Q] {
    let mut t = [[0u8; Q]; Q];
    let mut a = 0;
    while a < Q {
        let mut b = 0;
        while b < Q {
            t[a][b] = ((a + Q - b) % Q) as u8;
            b += 1;
        }
        a += 1;
    }
    t
}
const SUB: [[u8; Q]; Q] = build_sub();

const fn build_add() -> [[u8; Q]; Q] {
    let mut t = [[0u8; Q]; Q];
    let mut a = 0;
    while a < Q {
        let mut b = 0;
        while b < Q {
            t[a][b] = ((a + b) % Q) as u8;
            b += 1;
        }
        a += 1;
    }
    t
}
const ADD: [[u8; Q]; Q] = build_add();

/// MT[q][v] = logf[(q - v) mod 29]  (h5slice_nb: MT = _ls_matrix(logf).T)
const fn build_mt() -> [[f64; Q]; Q] {
    let mut t = [[0.0f64; Q]; Q];
    let mut x = 0;
    while x < Q {
        let mut v = 0;
        while v < Q {
            t[x][v] = LOGF[(x + Q - v) % Q];
            v += 1;
        }
        x += 1;
    }
    t
}
static MT: [[f64; Q]; Q] = build_mt();

/// FR[q][v] = f[(q - v) mod 29] with f = exp(logf) - the row access the fast engine uses
/// (u_v * f[(q-v)]). Built at startup (const-fn exp is not available).
static FR: std::sync::OnceLock<[[f64; Q]; Q]> = std::sync::OnceLock::new();

fn fr_tab() -> &'static [[f64; Q]; Q] {
    FR.get_or_init(|| {
        let mut t = [[0.0f64; Q]; Q];
        for x in 0..Q {
            for v in 0..Q {
                t[x][v] = LOGF[(x + Q - v) % Q].exp();
            }
        }
        t
    })
}

// ------------------------------------------------------------------ totient stream

/// First n primes via a self-contained sieve (mirrors h5slice.sieve_primes).
pub fn sieve_primes(n: usize) -> Vec<u64> {
    if n < 1 {
        return Vec::new();
    }
    if n < 8 {
        return vec![2, 3, 5, 7, 11, 13, 17][..n].to_vec();
    }
    let mut bound = (n as f64 * ((n as f64).ln() + (n as f64).ln().ln())) as usize + 16;
    loop {
        let mut m = vec![true; bound + 1];
        if m.len() > 2 {
            m[0] = false;
            m[1] = false;
        }
        // m[4::2] = False
        let mut i = 4;
        while i <= bound {
            m[i] = false;
            i += 2;
        }
        let sqrt = (bound as f64).sqrt() as usize;
        let mut i = 3;
        while i <= sqrt {
            if m[i] {
                let mut j = i * i;
                while j <= bound {
                    m[j] = false;
                    j += i;
                }
            }
            i += 2;
        }
        let ps: Vec<u64> = m
            .iter()
            .enumerate()
            .filter(|&(_, b)| *b)
            .map(|(i, _)| i as u64)
            .collect();
        if ps.len() >= n {
            return ps[..n].to_vec();
        }
        bound *= 2;
    }
}

/// The library's "primes-1 (totient)": t_n = (p_n - 1) mod 29.
pub fn totient(n: usize) -> Vec<u8> {
    sieve_primes(n).iter().map(|&p| ((p - 1) % Q as u64) as u8).collect()
}

// ------------------------------------------------------------------ statistics

/// np.mean over a short list of floats: numpy's pairwise summation (sequential blocks of 8,
/// then sequential over the block sums), then division by n - bit-identical to np.mean(vals)
/// for len < 64.
fn np_mean_pairwise(vals: &[f64]) -> f64 {
    let mut blocks: Vec<f64> = Vec::with_capacity((vals.len() + 7) / 8);
    for chunk in vals.chunks(8) {
        let mut acc = 0.0;
        for &x in chunk {
            acc += x;
        }
        blocks.push(acc);
    }
    let mut total = 0.0;
    for b in blocks {
        total += b;
    }
    total / vals.len() as f64
}

/// Mean column IoC of the decoded text: columns are the key-pointer phases j(i) mod L
/// (docs/HYPOTHESES.md:70-78; h5slice.periodic_ioc).
pub fn periodic_ioc(plain: &[u8], ptrs: &[i64], L: usize) -> f64 {
    let mut cols: Vec<Vec<u8>> = vec![Vec::new(); L];
    for (&p, &j) in plain.iter().zip(ptrs.iter()) {
        cols[(j % L as i64) as usize].push(p);
    }
    let mut vals: Vec<f64> = Vec::with_capacity(L);
    for col in &cols {
        if col.len() >= 2 {
            let mut cnt = [0u64; Q];
            for &x in col {
                cnt[x as usize] += 1;
            }
            let mut s = 0u64;
            for &c in &cnt {
                s += c * (c - 1);
            }
            vals.push(Q as f64 * (s as f64) / ((col.len() * (col.len() - 1)) as f64));
        }
    }
    if vals.is_empty() {
        0.0
    } else {
        np_mean_pairwise(&vals)
    }
}

/// ML column shifts: w[col] = argmax_v sum_x logf[(x - v) mod 29] * cnt[x] over
/// x_i = c_i - t_{j(i)} (h5slice.est_cols; the distribution-aware modal class).
pub fn est_cols(c: &[u8], ts: &[u8], ptrs: &[i64], L: usize) -> Vec<u8> {
    let mut cols: Vec<Vec<u8>> = vec![Vec::new(); L];
    for i in 0..c.len() {
        cols[(ptrs[i] % L as i64) as usize].push(SUB[c[i] as usize][ts[ptrs[i] as usize] as usize]);
    }
    let mut wcol = vec![0u8; L];
    for (col_idx, col) in cols.iter().enumerate() {
        if col.is_empty() {
            continue;
        }
        let mut cnt = [0u64; Q];
        for &x in col {
            cnt[x as usize] += 1;
        }
        let mut best_v = 0usize;
        let mut best_s = f64::NEG_INFINITY;
        for v in 0..Q {
            let mut s = 0.0;
            for x in 0..Q {
                s += LOGF[(x + Q - v) % Q] * cnt[x] as f64;
            }
            if s > best_s {
                best_s = s;
                best_v = v;
            }
        }
        wcol[col_idx] = best_v as u8;
    }
    wcol
}

// ------------------------------------------------------------------ EM core (beam_pass)

struct BeamOut {
    best: (i64, f64, i64), // (j, s, node)
    plains: Vec<u8>,
    parents: Vec<i64>,
    js: Vec<i64>,
}

/// One beam pass with the fixed combined key comb over the collision-consistency skip branches
/// (h5slice.beam_pass; work/layer2's outer_cands applied to the combined key). Returns None on
/// abort/empty. Merge keeps the first strict maximum per pointer (dict semantics), truncation
/// is a stable sort by score desc (only when longer than beam), abort fires at i+1 >= abort_at.
fn beam_pass(
    c: &[u8],
    prev: i64,
    comb: &[u8],
    model: u8,
    litf: bool,
    beam: usize,
    logf: &[f64; Q],
    abort_at: usize,
    abort_ll: f64,
) -> Option<BeamOut> {
    let n = c.len();
    let clen = comb.len() as i64;
    let mut plains: Vec<u8> = Vec::with_capacity(n * (beam + 1) * 3);
    let mut parents: Vec<i64> = Vec::with_capacity(n * (beam + 1) * 3);
    let mut js: Vec<i64> = Vec::with_capacity(n * (beam + 1) * 3);
    let mut cur: Vec<(i64, f64, i64)> = vec![(0, 0.0, -1)];
    let lf0 = logf[0];
    for i in 0..n {
        let ci = c[i] as usize;
        let pv = if i == 0 { prev } else { c[i - 1] as i64 };
        let mut cand: Vec<(i64, f64, i64)> = Vec::with_capacity(cur.len() * 3);
        for &(j, s, node) in &cur {
            let k0 = comb[j as usize] as usize;
            let q0 = SUB[ci][k0];
            let nj0 = if model == 1 && pv == ci as i64 { j + 2 } else { j + 1 };
            plains.push(q0);
            parents.push(node);
            js.push(j);
            cand.push((nj0, s + logf[q0 as usize], (plains.len() - 1) as i64));
            if litf && ci == 0 {
                plains.push(0);
                parents.push(node);
                js.push(j);
                cand.push((j, s + lf0, (plains.len() - 1) as i64));
            }
            if pv >= 0 {
                if model == 0 {
                    if j + 1 < clen {
                        let k1 = comb[(j + 1) as usize] as usize;
                        let t1 = SUB[ci][k1];
                        if ADD[t1 as usize][k0] as i64 == pv {
                            plains.push(t1);
                            parents.push(node);
                            js.push(j + 1);
                            cand.push((j + 2, s + logf[t1 as usize], (plains.len() - 1) as i64));
                        }
                        if j + 2 < clen {
                            let k2 = comb[(j + 2) as usize] as usize;
                            let t2 = SUB[ci][k2];
                            if ADD[t2 as usize][k0] as i64 == pv && ADD[t2 as usize][k1] as i64 == pv {
                                plains.push(t2);
                                parents.push(node);
                                js.push(j + 2);
                                cand.push((j + 3, s + logf[t2 as usize], (plains.len() - 1) as i64));
                            }
                        }
                    }
                } else if j + 2 < clen {
                    let k2 = comb[(j + 2) as usize] as usize;
                    let t2 = SUB[ci][k2];
                    if ADD[t2 as usize][k0] as i64 == pv {
                        plains.push(t2);
                        parents.push(node);
                        js.push(j + 2);
                        cand.push((j + 3, s + logf[t2 as usize], (plains.len() - 1) as i64));
                    }
                }
            }
        }
        // merge: first strict maximum per nj, first-appearance order (dict semantics)
        let mut items: Vec<(i64, f64, i64)> = Vec::with_capacity(cand.len());
        for &(nj, s, node) in &cand {
            let mut found = None;
            for (k, it) in items.iter().enumerate() {
                if it.0 == nj {
                    found = Some(k);
                    break;
                }
            }
            match found {
                None => items.push((nj, s, node)),
                Some(k) => {
                    if s > items[k].1 {
                        items[k] = (nj, s, node);
                    }
                }
            }
        }
        if items.len() > beam {
            items.sort_by(|a, b| b.1.partial_cmp(&a.1).unwrap());
            items.truncate(beam);
        }
        if abort_at != 0 && i + 1 >= abort_at {
            if items.is_empty() || items.iter().map(|t| t.1).fold(f64::NEG_INFINITY, f64::max) < abort_ll {
                return None;
            }
        }
        cur = items;
    }
    if cur.is_empty() {
        return None;
    }
    let mut best = cur[0];
    for &st in &cur[1..] {
        if st.1 > best.1 {
            best = st;
        }
    }
    Some(BeamOut { best, plains, parents, js })
}

fn traceback(node: i64, plains: &[u8], parents: &[i64], js: &[i64]) -> (Vec<u8>, Vec<i64>) {
    let mut plain: Vec<u8> = Vec::new();
    let mut ptrs: Vec<i64> = Vec::new();
    let mut nd = node;
    while nd >= 0 {
        plain.push(plains[nd as usize]);
        ptrs.push(js[nd as usize]);
        nd = parents[nd as usize];
    }
    plain.reverse();
    ptrs.reverse();
    (plain, ptrs)
}

// ------------------------------------------------------------------ init beam (numba-exact scalar)

/// The verified reference init: exact port of h5slice_nb._kernel (flat buffers, per-pointer
/// merge keeps the FIRST strict maximum, truncation is an ALWAYS-run stable sort by -score,
/// the abort fires only at the abort_at checkpoint). Returns (ptrs, score) or None on abort.
#[allow(clippy::too_many_arguments)]
pub fn init_beam_scalar(
    c: &[u8],
    ts: &[u8],
    L: usize,
    litf: bool,
    beam: usize,
    abort_at: usize,
    abort_ll: f64,
) -> Option<(Vec<i64>, f64)> {
    let n = c.len();
    let tlen = ts.len() as i64;
    let lq = L * Q;
    let b = beam;
    let mut g = vec![0.0f64; b * lq];
    let mut g2 = vec![0.0f64; b * lq];
    let mut lc = vec![LN29; b * L];
    let mut lc2 = vec![LN29; b * L];
    let mut s = vec![0.0f64; b];
    let mut s2 = vec![0.0f64; b];
    let mut js = vec![0i64; b];
    let mut js2 = vec![0i64; b];
    let mut nds = vec![-1i64; b];
    let mut nds2 = vec![-1i64; b];
    s[0] = L as f64 * LN29;
    let mut w = 1usize;
    let max_nodes = 1 + n * b * 4;
    let mut ks_all = vec![0i64; max_nodes];
    let mut parents = vec![-1i64; max_nodes];
    let mut n_nodes = 1usize;
    let nmax = b * 4;
    let mut par = vec![0usize; nmax];
    let mut kidx = vec![0i64; nmax];
    let mut cost = vec![0.0f64; nmax];
    let mut q = vec![0usize; nmax];
    let mut col = vec![0usize; nmax];
    let mut lse2 = vec![0.0f64; nmax];
    let mut sc2 = vec![0.0f64; nmax];
    let mut nj = vec![0i64; nmax];
    let mut nju = vec![0i64; nmax];
    let mut s2u = vec![0.0f64; nmax];
    let mut tu = vec![0usize; nmax];
    for i in 0..n {
        let ci = c[i] as usize;
        let nb = if litf && ci == 0 { 4 } else { 3 };
        let mut n_cand = 0usize;
        for ww in 0..w {
            let j = js[ww];
            for dk in 0..3i64 {
                let k = j + dk;
                let (kk, cst) = if k < tlen { (k, dk as f64 * LN028) } else { (tlen - 1, -1e18) };
                par[n_cand] = ww;
                kidx[n_cand] = k;
                cost[n_cand] = cst;
                q[n_cand] = SUB[ci][ts[kk as usize] as usize] as usize;
                col[n_cand] = (kk % L as i64) as usize;
                n_cand += 1;
            }
            if nb == 4 {
                par[n_cand] = ww;
                kidx[n_cand] = j;
                cost[n_cand] = 0.0;
                q[n_cand] = 0;
                col[n_cand] = (j % L as i64) as usize;
                n_cand += 1;
            }
        }
        for t in 0..n_cand {
            let p = par[t];
            let gbase = p * lq + col[t] * Q;
            let qv = q[t];
            let mut m = -1e300;
            for v in 0..Q {
                let u = g[gbase + v] + MT[qv][v];
                if u > m {
                    m = u;
                }
            }
            let mut acc = 0.0;
            for v in 0..Q {
                acc += (g[gbase + v] + MT[qv][v] - m).exp();
            }
            lse2[t] = m + acc.ln();
            sc2[t] = s[p] + (lse2[t] - lc[p * L + col[t]]) + cost[t];
            nj[t] = kidx[t] + 1;
        }
        // merge: first strict maximum per nj, first-appearance order
        let mut ucount = 0usize;
        for t in 0..n_cand {
            let mut found = usize::MAX;
            for u in 0..ucount {
                if nju[u] == nj[t] {
                    found = u;
                    break;
                }
            }
            if found == usize::MAX {
                nju[ucount] = nj[t];
                s2u[ucount] = sc2[t];
                tu[ucount] = t;
                ucount += 1;
            } else if sc2[t] > s2u[found] {
                s2u[found] = sc2[t];
                tu[found] = t;
            }
        }
        // stable insertion sort by score desc, ALWAYS (the abort reads s2u[0] as the max)
        for a in 1..ucount {
            let xnj = nju[a];
            let xs = s2u[a];
            let xt = tu[a];
            let mut bpos = a;
            while bpos > 0 && s2u[bpos - 1] < xs {
                nju[bpos] = nju[bpos - 1];
                s2u[bpos] = s2u[bpos - 1];
                tu[bpos] = tu[bpos - 1];
                bpos -= 1;
            }
            nju[bpos] = xnj;
            s2u[bpos] = xs;
            tu[bpos] = xt;
        }
        if ucount > b {
            ucount = b;
        }
        if abort_at != 0 && i + 1 == abort_at {
            if ucount == 0 || s2u[0] < abort_ll {
                return None;
            }
        }
        // survivors (each rebuilt from its parent + the new letter)
        for ii in 0..ucount {
            let t = tu[ii];
            let p = par[t];
            let node = n_nodes;
            ks_all[node] = kidx[t];
            parents[node] = nds[p];
            g2[ii * lq..(ii + 1) * lq].copy_from_slice(&g[p * lq..(p + 1) * lq]);
            let gbase = ii * lq + col[t] * Q;
            for v in 0..Q {
                g2[gbase + v] += MT[q[t]][v];
            }
            lc2[ii * L..(ii + 1) * L].copy_from_slice(&lc[p * L..(p + 1) * L]);
            lc2[ii * L + col[t]] = lse2[t];
            s2[ii] = sc2[t];
            js2[ii] = nj[t];
            nds2[ii] = node as i64;
            n_nodes += 1;
        }
        let m2 = ucount;
        for r in 0..m2 {
            g[r * lq..(r + 1) * lq].copy_from_slice(&g2[r * lq..(r + 1) * lq]);
            lc[r * L..(r + 1) * L].copy_from_slice(&lc2[r * L..(r + 1) * L]);
            s[r] = s2[r];
            js[r] = js2[r];
            nds[r] = nds2[r];
        }
        w = m2;
    }
    if w == 0 {
        return None;
    }
    let mut best = 0usize;
    for r in 1..w {
        if s[r] > s[best] {
            best = r;
        }
    }
    let mut node = nds[best];
    let mut ptrs = vec![0i64; n];
    for i in (0..n).rev() {
        ptrs[i] = ks_all[node as usize];
        node = parents[node as usize];
    }
    Some((ptrs, s[best]))
}

// ------------------------------------------------------------------ init beam (fast: normalized vectors)

/// The algebraically identical fast init. The state keeps per column the SUM-1-normalized
/// vector u[col][v] = exp(G[col][v] - M) / sum_v exp(G[col][v] - M). The score increment of a
/// letter with shift q in column col is ln(sum_v u_v * f[(q-v) mod 29]) - ln(sum_v u_v) with
/// ln(sum_v u_v) = ln 1 = 0, so one log per candidate and NO exponentials anywhere; the child's
/// column is p_v / sum (p_v = u_v * f[(q-v)]), which stays in [0,1] with sum 1, so no scale
/// (max/M/Lc) bookkeeping is needed at all. Scores agree with the reference within ~1e-12 nats
/// (both compute the same telescoped increment, in a different rounding order); the merge,
/// tie-break, truncation, abort and traceback semantics are identical to init_beam_scalar.
pub fn init_beam_fastscalar(
    c: &[u8],
    ts: &[u8],
    L: usize,
    litf: bool,
    beam: usize,
    abort_at: usize,
    abort_ll: f64,
) -> Option<(Vec<i64>, f64)> {
    let fr = fr_tab();
    let n = c.len();
    let tlen = ts.len() as i64;
    let lq = L * Q;
    let b = beam;
    let inv29 = 1.0 / Q as f64;
    let mut u = vec![inv29; b * lq];
    let mut u2 = vec![inv29; b * lq];
    let mut s = vec![0.0f64; b];
    let mut s2 = vec![0.0f64; b];
    let mut js = vec![0i64; b];
    let mut js2 = vec![0i64; b];
    let mut nds = vec![-1i64; b];
    let mut nds2 = vec![-1i64; b];
    s[0] = L as f64 * LN29;
    let mut w = 1usize;
    let max_nodes = 1 + n * b * 4;
    let mut ks_all = vec![0i64; max_nodes];
    let mut parents = vec![-1i64; max_nodes];
    let mut n_nodes = 1usize;
    let nmax = b * 4;
    let mut par = vec![0usize; nmax];
    let mut kidx = vec![0i64; nmax];
    let mut cost = vec![0.0f64; nmax];
    let mut q = vec![0usize; nmax];
    let mut col = vec![0usize; nmax];
    let mut inc = vec![0.0f64; nmax]; // ln(sum_v u_v f[(q-v)]) - ln(sum u) = ln(sum ...)
    let mut sc2 = vec![0.0f64; nmax];
    let mut nj = vec![0i64; nmax];
    let mut nju = vec![0i64; nmax];
    let mut s2u = vec![0.0f64; nmax];
    let mut tu = vec![0usize; nmax];
    let mut side = vec![0.0f64; nmax * Q]; // normalized child columns, one per candidate
    for i in 0..n {
        let ci = c[i] as usize;
        let nb = if litf && ci == 0 { 4 } else { 3 };
        let mut n_cand = 0usize;
        for ww in 0..w {
            let j = js[ww];
            for dk in 0..3i64 {
                let k = j + dk;
                let (kk, cst) = if k < tlen { (k, dk as f64 * LN028) } else { (tlen - 1, -1e18) };
                par[n_cand] = ww;
                kidx[n_cand] = k;
                cost[n_cand] = cst;
                q[n_cand] = SUB[ci][ts[kk as usize] as usize] as usize;
                col[n_cand] = (kk % L as i64) as usize;
                n_cand += 1;
            }
            if nb == 4 {
                par[n_cand] = ww;
                kidx[n_cand] = j;
                cost[n_cand] = 0.0;
                q[n_cand] = 0;
                col[n_cand] = (j % L as i64) as usize;
                n_cand += 1;
            }
        }
        for t in 0..n_cand {
            let p = par[t];
            let gbase = p * lq + col[t] * Q;
            let frrow = &fr[q[t]];
            let mut sum = 0.0;
            for v in 0..Q {
                let pv = u[gbase + v] * frrow[v];
                side[t * Q + v] = pv;
                sum += pv;
            }
            let r = 1.0 / sum;
            for v in 0..Q {
                side[t * Q + v] *= r;
            }
            // inc = ln(sum)  (ln(sum_v u_v) = 0 for the sum-1 normalization)
            inc[t] = fast_ln(sum);
            sc2[t] = s[p] + inc[t] + cost[t];
            nj[t] = kidx[t] + 1;
        }
        // merge: first strict maximum per nj, first-appearance order
        let mut ucount = 0usize;
        for t in 0..n_cand {
            let mut found = usize::MAX;
            for u in 0..ucount {
                if nju[u] == nj[t] {
                    found = u;
                    break;
                }
            }
            if found == usize::MAX {
                nju[ucount] = nj[t];
                s2u[ucount] = sc2[t];
                tu[ucount] = t;
                ucount += 1;
            } else if sc2[t] > s2u[found] {
                s2u[found] = sc2[t];
                tu[found] = t;
            }
        }
        for a in 1..ucount {
            let xnj = nju[a];
            let xs = s2u[a];
            let xt = tu[a];
            let mut bpos = a;
            while bpos > 0 && s2u[bpos - 1] < xs {
                nju[bpos] = nju[bpos - 1];
                s2u[bpos] = s2u[bpos - 1];
                tu[bpos] = tu[bpos - 1];
                bpos -= 1;
            }
            nju[bpos] = xnj;
            s2u[bpos] = xs;
            tu[bpos] = xt;
        }
        if ucount > b {
            ucount = b;
        }
        if abort_at != 0 && i + 1 == abort_at {
            if ucount == 0 || s2u[0] < abort_ll {
                return None;
            }
        }
        for ii in 0..ucount {
            let t = tu[ii];
            let p = par[t];
            let node = n_nodes;
            ks_all[node] = kidx[t];
            parents[node] = nds[p];
            u2[ii * lq..(ii + 1) * lq].copy_from_slice(&u[p * lq..(p + 1) * lq]);
            let gbase = ii * lq + col[t] * Q;
            u2[gbase..gbase + Q].copy_from_slice(&side[t * Q..t * Q + Q]);
            s2[ii] = sc2[t];
            js2[ii] = nj[t];
            nds2[ii] = node as i64;
            n_nodes += 1;
        }
        let m2 = ucount;
        for r in 0..m2 {
            u[r * lq..(r + 1) * lq].copy_from_slice(&u2[r * lq..(r + 1) * lq]);
            s[r] = s2[r];
            js[r] = js2[r];
            nds[r] = nds2[r];
        }
        w = m2;
    }
    if w == 0 {
        return None;
    }
    let mut best = 0usize;
    for r in 1..w {
        if s[r] > s[best] {
            best = r;
        }
    }
    let mut node = nds[best];
    let mut ptrs = vec![0i64; n];
    for i in (0..n).rev() {
        ptrs[i] = ks_all[node as usize];
        node = parents[node as usize];
    }
    Some((ptrs, s[best]))
}

// ------------------------------------------------------------------ init beam (fast: AVX2)

/// Per-thread scratch for the fast engine: allocated once per thread, resized on demand,
/// never re-zeroed (every read is of a value written earlier in the same decode: the beam
/// rows are fully rewritten each rune, ks_all/parents are written at their node ids before
/// the traceback reads them, and the merge arrays are written up to ucount each rune).
struct InitScratch {
    arena: Vec<f64>, // immutable column storage: arena[idx*29 + v]; written once per column
    cols: Vec<i32>,  // per-survivor column indices: cols[i*L + cc]
    cols2: Vec<i32>,
    s: Vec<f64>,
    s2: Vec<f64>,
    js: Vec<i64>,
    js2: Vec<i64>,
    nds: Vec<i64>,
    nds2: Vec<i64>,
    ks_all: Vec<i64>,
    parents: Vec<i64>,
    par: Vec<usize>,
    kidx: Vec<i64>,
    cost: Vec<f64>,
    q: Vec<usize>,
    col: Vec<usize>,
    inc: Vec<f64>,
    sc2: Vec<f64>,
    sums: Vec<f64>, // per-candidate product sums (the rebuild reuses them verbatim)
    nj: Vec<i64>,
    nju: Vec<i64>,
    s2u: Vec<f64>,
    tu: Vec<usize>,
    idx: Vec<usize>,
    keys: Vec<u64>,
    stamp: Vec<i64>,
    spos: Vec<usize>,
}

/// The fast engine with AVX2/FMA intrinsics: same normalized-vector algebra and the same
/// merge/tie-break/abort/traceback semantics as init_beam_fastscalar; the per-candidate
/// product-and-sum uses 4-lane vectors with order-preserving lane extraction (block i covers
/// v = 4i..4i+3, summed (p0+p1)+(p2+p3), blocks ascending, scalar tail last), so scores
/// stay within ~1e-12 nats of the reference. x86_64 only; callers check the CPU flags.
/// NOTE: _mm256_hadd_pd with IDENTICAL operands is NOT used (LLVM's Zen1 expansion of
/// same-operand VHADDPD produced wrong lane sums - found by the parity gate at the first
/// rune); the lane extraction below is register-only and unambiguous.
#[cfg(target_arch = "x86_64")]
#[target_feature(enable = "avx2,fma")]
pub fn init_beam_fast_avx2(
    c: &[u8],
    ts: &[u8],
    L: usize,
    litf: bool,
    beam: usize,
    abort_at: usize,
    abort_ll: f64,
) -> Option<(Vec<i64>, f64)> {
    unsafe {
    use std::arch::x86_64::*;
    let fr = fr_tab();
    let n = c.len();
    let tlen = ts.len() as i64;
    let b = beam;
    let inv29 = 1.0 / Q as f64;
    let scratch = scratch_get(L, b, n, tlen as usize);
    let arena = &mut scratch.arena;
    let cols = &mut scratch.cols;
    let cols2 = &mut scratch.cols2;
    let s = &mut scratch.s;
    let s2 = &mut scratch.s2;
    let js = &mut scratch.js;
    let js2 = &mut scratch.js2;
    let nds = &mut scratch.nds;
    let nds2 = &mut scratch.nds2;
    let ks_all = &mut scratch.ks_all;
    let parents = &mut scratch.parents;
    let par = &mut scratch.par;
    let kidx = &mut scratch.kidx;
    let cost = &mut scratch.cost;
    let q = &mut scratch.q;
    let col = &mut scratch.col;
    let inc = &mut scratch.inc;
    let sc2 = &mut scratch.sc2;
    let sums = &mut scratch.sums;
    let nj = &mut scratch.nj;
    let nju = &mut scratch.nju;
    let s2u = &mut scratch.s2u;
    let tu = &mut scratch.tu;
    let idx = &mut scratch.idx;
    let keys = &mut scratch.keys;
    let stamp = &mut scratch.stamp;
    let spos = &mut scratch.spos;
    // root column (the initial state's L columns all share it) - written per decode
    for v in 0..Q {
        arena[v] = inv29;
    }
    for cc in 0..L {
        cols[cc] = 0;
    }
    s[0] = L as f64 * LN29;
    js[0] = 0;
    nds[0] = -1;
    let mut w = 1usize;
    let mut n_nodes = 1usize;
    let mut n_cols: i32 = 1;
    // monotonic per-thread stamp base: the stamp array entries persist across decodes in the
    // thread-local scratch, so stamp_ids must never be reused (a reset id would collide with
    // stale entries from the previous decode and corrupt the merge)
    let stamp_base = next_stamp_base();
    let mut stamp_id: i64 = stamp_base;
    for i in 0..n {
        let ci = c[i] as usize;
        let nb = if litf && ci == 0 { 4 } else { 3 };
        let mut n_cand = 0usize;
        for ww in 0..w {
            let j = js[ww];
            for dk in 0..3i64 {
                let k = j + dk;
                let (kk, cst) = if k < tlen { (k, dk as f64 * LN028) } else { (tlen - 1, -1e18) };
                par[n_cand] = ww;
                kidx[n_cand] = k;
                cost[n_cand] = cst;
                q[n_cand] = SUB[ci][ts[kk as usize] as usize] as usize;
                col[n_cand] = (kk % L as i64) as usize;
                n_cand += 1;
            }
            if nb == 4 {
                par[n_cand] = ww;
                kidx[n_cand] = j;
                cost[n_cand] = 0.0;
                q[n_cand] = 0;
                col[n_cand] = (j % L as i64) as usize;
                n_cand += 1;
            }
        }
        for t in 0..n_cand {
            let p = par[t];
            let aidx = cols[p * L + col[t]] as usize;
            let ubase = aidx * Q;
            let frrow = &fr[q[t]];
            // products via SIMD (bit-identical per lane); the sum is SEQUENTIAL ascending-v,
            // bit-identical to init_beam_fastscalar (a different reduction order can flip an
            // exact-tie merge and diverge from the reference - found by the parity gate)
            let mut sum = 0.0;
            for blk in 0..7 {
                let uv = _mm256_loadu_pd(arena.as_ptr().add(ubase + 4 * blk));
                let fv = _mm256_loadu_pd(frrow.as_ptr().add(4 * blk));
                let pv = _mm256_mul_pd(uv, fv);
                let lo = _mm256_castpd256_pd128(pv);
                let hi = _mm256_extractf128_pd::<1>(pv);
                sum += _mm_cvtsd_f64(lo);
                sum += _mm_cvtsd_f64(_mm_unpackhi_pd(lo, lo));
                sum += _mm_cvtsd_f64(hi);
                sum += _mm_cvtsd_f64(_mm_unpackhi_pd(hi, hi));
            }
            sum += arena[ubase + 28] * frrow[28];
            sums[t] = sum;
            inc[t] = fast_ln(sum);
            sc2[t] = s[p] + inc[t] + cost[t];
            nj[t] = kidx[t] + 1;
        }
        // merge: first strict maximum per nj, first-appearance order (stamp-index lookup)
        let mut ucount = 0usize;
        for t in 0..n_cand {
            let njv = nj[t] as usize;
            if stamp[njv] != stamp_id {
                stamp[njv] = stamp_id;
                spos[njv] = ucount;
                s2u[ucount] = sc2[t];
                tu[ucount] = t;
                ucount += 1;
            } else {
                let uu = spos[njv];
                if sc2[t] > s2u[uu] {
                    s2u[uu] = sc2[t];
                    tu[uu] = t;
                }
            }
        }
        stamp_id += 1;
        // sort by the reference total order (score desc, tie -> first appearance): map the
        // score to a monotone u64 (negative floats have reversed bit order, so invert their
        // bits; then invert again for descending) and sort (key, candidate-index) tuples -
        // identical to the reference's stable sort + truncate, since the total order is unique
        for u in 0..ucount {
            let b = s2u[u].to_bits();
            let mb = if b >> 63 == 1 { !b } else { b | (1u64 << 63) };
            keys[u] = !mb;
            idx[u] = u;
        }
        idx[..ucount].sort_unstable_by_key(|&i| (keys[i], tu[i]));
        if ucount > b {
            ucount = b;
        }
        if abort_at != 0 && i + 1 == abort_at {
            if ucount == 0 || s2u[idx[0]] < abort_ll {
                return None;
            }
        }
        // survivors: share the parent's columns; write ONE new normalized column each
        for ii in 0..ucount {
            let t = tu[idx[ii]];
            let p = par[t];
            let node = n_nodes;
            ks_all[node] = kidx[t];
            parents[node] = nds[p];
            cols2[ii * L..(ii + 1) * L].copy_from_slice(&cols[p * L..(p + 1) * L]);
            let newc = n_cols;
            n_cols += 1;
            let nbase = newc as usize * Q;
            let frrow = &fr[q[t]];
            let pbase = cols[p * L + col[t]] as usize * Q;
            // write the products straight into the fresh arena column, then scale in place;
            // the sum is the SAME value computed in the scoring phase (sums[t], sequential
            // ascending-v, bit-identical to fastscalar)
            let sum2 = sums[t];
            for blk in 0..7 {
                let uv = _mm256_loadu_pd(arena.as_ptr().add(pbase + 4 * blk));
                let fv = _mm256_loadu_pd(frrow.as_ptr().add(4 * blk));
                let pv = _mm256_mul_pd(uv, fv);
                _mm256_storeu_pd(arena.as_mut_ptr().add(nbase + 4 * blk), pv);
            }
            let tv = arena[pbase + 28] * frrow[28];
            arena[nbase + 28] = tv;
            let r = _mm256_set1_pd(1.0 / sum2);
            for blk in 0..7 {
                let pv = _mm256_loadu_pd(arena.as_ptr().add(nbase + 4 * blk));
                _mm256_storeu_pd(arena.as_mut_ptr().add(nbase + 4 * blk), _mm256_mul_pd(pv, r));
            }
            arena[nbase + 28] = tv * (1.0 / sum2);
            cols2[ii * L + col[t]] = newc;
            s2[ii] = sc2[t];
            js2[ii] = nj[t];
            nds2[ii] = node as i64;
            n_nodes += 1;
        }
        let m2 = ucount;
        for r in 0..m2 {
            cols[r * L..(r + 1) * L].copy_from_slice(&cols2[r * L..(r + 1) * L]);
            s[r] = s2[r];
            js[r] = js2[r];
            nds[r] = nds2[r];
        }
        w = m2;
    }
    if w == 0 {
        return None;
    }
    let mut best = 0usize;
    for r in 1..w {
        if s[r] > s[best] {
            best = r;
        }
    }
    let mut node = nds[best];
    let mut ptrs = vec![0i64; n];
    for i in (0..n).rev() {
        ptrs[i] = ks_all[node as usize];
        node = parents[node as usize];
    }
    Some((ptrs, s[best]))
    }
}

/// ln(1 + k/16) table for fast_ln (and its reciprocal table).
static LN1P16: std::sync::OnceLock<[f64; 16]> = std::sync::OnceLock::new();
static R1P16: std::sync::OnceLock<[f64; 16]> = std::sync::OnceLock::new();

fn ln1p16() -> &'static [f64; 16] {
    LN1P16.get_or_init(|| {
        let mut t = [0.0f64; 16];
        for k in 0..16 {
            t[k] = (1.0 + k as f64 / 16.0).ln();
        }
        t
    })
}

fn r1p16() -> &'static [f64; 16] {
    R1P16.get_or_init(|| {
        let mut t = [0.0f64; 16];
        for k in 0..16 {
            t[k] = 1.0 / (1.0 + k as f64 / 16.0);
        }
        t
    })
}

/// Fast ln for the known sum domain [f_min, f_max] = [e^-10.5, e^-0.8]:
/// x = m * 2^e with m in [1,2); ln x = ln(1+u) + e*ln2 with u = m-1 in [0,1), reduced by a
/// 16-entry table: k = floor(16u), t = (u - k/16)/(1 + k/16), |t| <= 1/17, degree-8 Taylor.
/// Max error ~2e-13 per call - far inside the 1e-9-nats score tolerance.
#[inline]
fn fast_ln(x: f64) -> f64 {
    const LN2: f64 = 0.6931471805599453;
    let bits = x.to_bits();
    let e = ((bits >> 52) & 0x7FF) as i64 - 1023;
    let m = f64::from_bits((bits & 0xF_FFFF_FFFF_FFFF) | (1023u64 << 52));
    // u = m-1 in [0,1); k = floor(16u) is exactly the top 4 fraction bits of m
    let k = ((bits >> 48) & 0xF) as usize;
    let u = m - 1.0;
    let u0 = k as f64 * 0.0625;
    let t = (u - u0) * r1p16()[k];
    // ln(1+t) = t - t^2/2 + t^3/3 - ... - t^8/8, |t| <= 1/17
    let t2 = t * t;
    let t4 = t2 * t2;
    let p = t - t2 / 2.0 + t2 * t / 3.0 - t4 / 4.0 + t4 * t / 5.0 - t4 * t2 / 6.0
        + t4 * t2 * t / 7.0 - t4 * t4 / 8.0;
    ln1p16()[k] + p + e as f64 * LN2
}

fn next_stamp_base() -> i64 {
    thread_local! {
        static STAMP_BASE: std::cell::Cell<i64> = const { std::cell::Cell::new(1) };
    }
    STAMP_BASE.with(|c| {
        let v = c.get();
        c.set(v.wrapping_add(1 << 20));
        v
    })
}

fn scratch_get(L: usize, beam: usize, n: usize, tlen: usize) -> &'static mut InitScratch {
    thread_local! {
        static SCRATCH: std::cell::RefCell<Option<InitScratch>> =
            const { std::cell::RefCell::new(None) };
    }
    SCRATCH.with(|cell| {
        let mut sc = cell.borrow_mut();
        let slot = sc.get_or_insert_with(|| InitScratch {
            arena: Vec::new(),
            cols: Vec::new(),
            cols2: Vec::new(),
            s: Vec::new(),
            s2: Vec::new(),
            js: Vec::new(),
            js2: Vec::new(),
            nds: Vec::new(),
            nds2: Vec::new(),
            ks_all: Vec::new(),
            parents: Vec::new(),
            par: Vec::new(),
            kidx: Vec::new(),
            cost: Vec::new(),
            q: Vec::new(),
            col: Vec::new(),
            inc: Vec::new(),
            sc2: Vec::new(),
            sums: Vec::new(),
            nj: Vec::new(),
            nju: Vec::new(),
            s2u: Vec::new(),
            tu: Vec::new(),
            idx: Vec::new(),
            keys: Vec::new(),
            stamp: Vec::new(),
            spos: Vec::new(),
        });
        let b = beam;
        let nmax = b * 4;
        let max_nodes = 1 + n * b * 4;
        let max_cols = (1 + n * b) * Q; // 1 root column + one new column per rune per survivor
        if slot.arena.len() < max_cols {
            slot.arena.resize(max_cols, 0.0);
        }
        if slot.cols.len() < b * L {
            slot.cols.resize(b * L, 0);
        }
        if slot.cols2.len() < b * L {
            slot.cols2.resize(b * L, 0);
        }
        for v in [&mut slot.s, &mut slot.s2].iter_mut() {
            if v.len() < b {
                v.resize(b, 0.0);
            }
        }
        for v in [&mut slot.js, &mut slot.js2, &mut slot.nds, &mut slot.nds2].iter_mut() {
            if v.len() < b {
                v.resize(b, 0);
            }
        }
        if slot.ks_all.len() < max_nodes {
            slot.ks_all.resize(max_nodes, 0);
        }
        if slot.parents.len() < max_nodes {
            slot.parents.resize(max_nodes, 0);
        }
        if slot.par.len() < nmax {
            slot.par.resize(nmax, 0);
        }
        if slot.kidx.len() < nmax {
            slot.kidx.resize(nmax, 0);
        }
        if slot.cost.len() < nmax {
            slot.cost.resize(nmax, 0.0);
        }
        if slot.q.len() < nmax {
            slot.q.resize(nmax, 0);
        }
        if slot.col.len() < nmax {
            slot.col.resize(nmax, 0);
        }
        if slot.inc.len() < nmax {
            slot.inc.resize(nmax, 0.0);
        }
        if slot.sc2.len() < nmax {
            slot.sc2.resize(nmax, 0.0);
        }
        if slot.sums.len() < nmax {
            slot.sums.resize(nmax, 0.0);
        }
        if slot.nj.len() < nmax {
            slot.nj.resize(nmax, 0);
        }
        if slot.nju.len() < nmax {
            slot.nju.resize(nmax, 0);
        }
        if slot.s2u.len() < nmax {
            slot.s2u.resize(nmax, 0.0);
        }
        if slot.tu.len() < nmax {
            slot.tu.resize(nmax, 0);
        }
        if slot.idx.len() < nmax {
            slot.idx.resize(nmax, 0);
        }
        if slot.keys.len() < nmax {
            slot.keys.resize(nmax, 0);
        }
        if slot.stamp.len() < tlen + 4 {
            slot.stamp.resize(tlen + 4, 0);
        }
        if slot.spos.len() < tlen + 4 {
            slot.spos.resize(tlen + 4, 0);
        }
        // SAFETY: the RefCell borrow is held for the whole decode; the caller is
        // non-reentrant (no nested decode on the same thread) - the standard pattern
        // for per-thread scratch in this engine.
        unsafe {
            let raw = slot as *mut InitScratch;
            &mut *raw
        }
    })
}

#[cfg(not(target_arch = "x86_64"))]
pub fn init_beam_fast_avx2(
    _c: &[u8],
    _ts: &[u8],
    _L: usize,
    _litf: bool,
    _beam: usize,
    _abort_at: usize,
    _abort_ll: f64,
) -> Option<(Vec<i64>, f64)> {
    panic!("engine 'fast' requires x86_64 with AVX2+FMA");
}

pub fn avx2_available() -> bool {
    #[cfg(target_arch = "x86_64")]
    {
        std::arch::is_x86_feature_detected!("avx2") && std::arch::is_x86_feature_detected!("fma")
    }
    #[cfg(not(target_arch = "x86_64"))]
    {
        false
    }
}

#[derive(Clone, Copy, PartialEq, Eq, Debug)]
pub enum Engine {
    Scalar,
    FastScalar,
    Fast,
}

impl Engine {
    fn name(self) -> &'static str {
        match self {
            Engine::Scalar => "scalar",
            Engine::FastScalar => "fastscalar",
            Engine::Fast => "fast",
        }
    }
}

pub struct DecInfo {
    pub ioc: f64,
    pub wcol: Vec<u8>,
    pub skips: i64,
    pub ptrs: Vec<i64>,
    pub ll: f64, // mean LL per rune of the final path (0.0 when the init path was scored)
    pub aborted: bool,
}

pub fn skips_of(ptrs: &[i64]) -> i64 {
    let mut sk = 0i64;
    for i in 1..ptrs.len() {
        sk += ptrs[i] - ptrs[i - 1] - 1;
    }
    sk
}

/// t alone (L = 0, the blind old-screen view): beam over the skip branches pruned by the
/// running IoC of the decoded symbols (h5slice.decode_t_only).
fn decode_t_only(c: &[u8], prev: i64, ts: &[u8], model: u8, beam: usize) -> (f64, Vec<u8>) {
    let n = c.len();
    let clen = ts.len() as i64;
    let mut states: Vec<(i64, [u32; Q], u32, f64)> = vec![(0, [0; Q], 0, 0.0)];
    for i in 0..n {
        let ci = c[i] as usize;
        let pv = if i == 0 { prev } else { c[i - 1] as i64 };
        let mut cand: Vec<(i64, [u32; Q], u32, f64)> = Vec::with_capacity(states.len() * 3);
        for &(j, cnt, used, _) in &states {
            let k0 = ts[j as usize] as usize;
            let q0 = SUB[ci][k0];
            let nj0 = if model == 1 && pv == ci as i64 { j + 2 } else { j + 1 };
            let mut t1v = 0u8;
            let mut t2v = 0u8;
            let mut has1 = false;
            let mut has2 = false;
            if pv >= 0 {
                if model == 0 {
                    if j + 1 < clen {
                        let k1 = ts[(j + 1) as usize] as usize;
                        let t1 = SUB[ci][k1];
                        if ADD[t1 as usize][k0] as i64 == pv {
                            t1v = t1;
                            has1 = true;
                        }
                        if j + 2 < clen {
                            let k2 = ts[(j + 2) as usize] as usize;
                            let t2 = SUB[ci][k2];
                            if ADD[t2 as usize][k0] as i64 == pv
                                && ADD[t2 as usize][k1] as i64 == pv
                            {
                                t2v = t2;
                                has2 = true;
                            }
                        }
                    }
                } else if j + 2 < clen {
                    let k2 = ts[(j + 2) as usize] as usize;
                    let t2 = SUB[ci][k2];
                    if ADD[t2 as usize][k0] as i64 == pv {
                        t2v = t2;
                        has2 = true;
                    }
                }
            }
            // score each candidate by the running IoC
            let mut scored: Vec<(i64, [u32; Q], u32, f64)> = Vec::with_capacity(3);
            scored.push((nj0, cnt, used, q0 as f64));
            if has1 {
                scored.push((j + 2, cnt, used, t1v as f64));
            }
            if has2 {
                scored.push((j + 3, cnt, used, t2v as f64));
            }
            for (njj, c2, u2, qv) in scored {
                let mut c3 = c2;
                c3[qv as usize] += 1;
                let u3 = u2 + 1;
                let sc = if u3 > 1 {
                    Q as f64 * (c3.iter().map(|&x| (x * (x - 1)) as f64).sum::<f64>())
                        / ((u3 * (u3 - 1)) as f64)
                } else {
                    0.0
                };
                cand.push((njj, c3, u3, sc));
            }
        }
        let mut items: Vec<(i64, [u32; Q], u32, f64)> = Vec::with_capacity(cand.len());
        for &(njj, c2, u2, sc) in &cand {
            let mut found = None;
            for (k, it) in items.iter().enumerate() {
                if it.0 == njj {
                    found = Some(k);
                    break;
                }
            }
            match found {
                None => items.push((njj, c2, u2, sc)),
                Some(k) => {
                    if sc > items[k].3 {
                        items[k] = (njj, c2, u2, sc);
                    }
                }
            }
        }
        if items.len() > beam {
            items.sort_by(|a, b| b.3.partial_cmp(&a.3).unwrap());
            items.truncate(beam);
        }
        states = items;
    }
    if states.is_empty() {
        return (0.0, Vec::new());
    }
    let mut best = states[0].3;
    for st in &states[1..] {
        if st.3 > best {
            best = st.3;
        }
    }
    (best, Vec::new())
}

/// Decode one window at one (offset, L): init beam -> est_cols -> EM over w -> periodic IoC
/// (h5slice.decode, fast_init=True). abort_margin is the recalibrated 0.9.
#[allow(clippy::too_many_arguments)]
pub fn decode(
    c: &[u8],
    prev: i64,
    tvals: &[u8],
    offset: i64,
    L: usize,
    model: u8,
    litf: bool,
    beam: usize,
    max_em: usize,
    beam_a: usize,
    abort_at: usize,
    abort_margin: f64,
    engine: Engine,
) -> DecInfo {
    let n = c.len();
    let margin = n / 4 + 32;
    let aborted = || DecInfo {
        ioc: 0.0,
        wcol: Vec::new(),
        skips: 0,
        ptrs: Vec::new(),
        ll: 0.0,
        aborted: true,
    };
    if offset < 0 || offset + n as i64 + margin as i64 > tvals.len() as i64 {
        return aborted();
    }
    let ts = &tvals[offset as usize..offset as usize + n + margin];
    if L == 0 {
        let (ioc, wcol) = decode_t_only(c, prev, ts, model, beam);
        return DecInfo { ioc, wcol, skips: 0, ptrs: Vec::new(), ll: 0.0, aborted: false };
    }
    let abort_ll_init = if abort_at != 0 {
        abort_at as f64 * (UNI + abort_margin) + L as f64 * LN29
    } else {
        0.0
    };
    let a = match engine {
        Engine::Scalar => init_beam_scalar(c, ts, L, litf, beam_a, abort_at, abort_ll_init),
        Engine::FastScalar => init_beam_fastscalar(c, ts, L, litf, beam_a, abort_at, abort_ll_init),
        Engine::Fast => {
            debug_assert!(avx2_available());
            // #[target_feature] calls are unsafe to call (the caller must check the CPU flags)
            unsafe { init_beam_fast_avx2(c, ts, L, litf, beam_a, abort_at, abort_ll_init) }
        }
    };
    let (ptrs_a, _ll_a) = match a {
        None => return aborted(),
        Some(x) => x,
    };
    let mut wcol = est_cols(c, ts, &ptrs_a, L);
    let mut last_out: Option<BeamOut> = None;
    for _ in 0..max_em {
        let mut comb = vec![0u8; n + margin];
        for j in 0..n + margin {
            comb[j] = ((ts[j] as usize + wcol[j % L] as usize) % Q) as u8;
        }
        let out = beam_pass(c, prev, &comb, model, litf, beam, &LOGF, 0, 0.0);
        if out.is_none() {
            break;
        }
        last_out = out;
        let o = last_out.as_ref().unwrap();
        let (_plain, ptrs) = traceback(o.best.2, &o.plains, &o.parents, &o.js);
        let new_wcol = est_cols(c, ts, &ptrs, L);
        let changed = new_wcol != wcol;
        wcol = new_wcol;
        if !changed {
            break;
        }
    }
    let (plain, ptrs, ll) = match &last_out {
        None => {
            // the init found no LL-EM path: score the coincidence-init path as-is
            let mut plain = vec![0u8; n];
            for i in 0..n {
                plain[i] = SUB[c[i] as usize][ts[ptrs_a[i] as usize] as usize];
            }
            return DecInfo {
                ioc: periodic_ioc(&plain, &ptrs_a, L),
                wcol,
                skips: skips_of(&ptrs_a),
                ptrs: ptrs_a.clone(),
                ll: 0.0,
                aborted: false,
            };
        }
        Some(o) => {
            let mut comb = vec![0u8; n + margin];
            for j in 0..n + margin {
                comb[j] = ((ts[j] as usize + wcol[j % L] as usize) % Q) as u8;
            }
            let out = beam_pass(c, prev, &comb, model, litf, beam, &LOGF, 0, 0.0);
            let o = out.as_ref().unwrap_or(o);
            let (plain, ptrs) = traceback(o.best.2, &o.plains, &o.parents, &o.js);
            let ll = o.best.1 / n as f64;
            (plain, ptrs, ll)
        }
    };
    DecInfo {
        ioc: periodic_ioc(&plain, &ptrs, L),
        wcol,
        skips: skips_of(&ptrs),
        ptrs,
        ll,
        aborted: false,
    }
}

// ------------------------------------------------------------------ inputs (kscreen window format)

struct Win {
    name: String,
    prev: i64,
    runes: Vec<u8>,
}

/// kscreen's window format (W name prev / R runes / optional L, P lines). First 300 runes
/// per window are used (the H5 decode is word-agnostic; L/B lines are not needed).
fn load_windows(path: &str) -> Vec<Win> {
    let txt = fs::read_to_string(path).unwrap_or_else(|e| panic!("{path}: {e}"));
    let mut out: Vec<Win> = Vec::new();
    for line in txt.lines() {
        if let Some(rest) = line.strip_prefix("W ") {
            let mut it = rest.split_whitespace();
            let name = it.next().expect("window name").to_string();
            let prev = it.next().map(|x| x.parse().expect("prev rune")).unwrap_or(-1);
            out.push(Win { name, prev, runes: Vec::new() });
        } else if let Some(rest) = line.strip_prefix("R ") {
            out.last_mut()
                .expect("R line before W line")
                .runes
                .extend(rest.split_whitespace().map(|x| x.parse::<u8>().expect("rune")));
        }
    }
    for w in out.iter_mut() {
        assert!(
            w.runes.iter().all(|&r| (r as usize) < Q),
            "{}: rune out of range",
            w.name
        );
        w.runes.truncate(300);
        assert!(w.runes.len() >= 100, "{}: fewer than 100 runes", w.name);
    }
    out
}

// splitmix64 (bench windows and rand streams only)
struct Rng(u64);

impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn rand29(&mut self) -> u8 {
        (self.next() % Q as u64) as u8
    }
}

fn random_stream(n: usize, seed: u64) -> Vec<u8> {
    let mut r = Rng(seed);
    (0..n).map(|_| r.rand29()).collect()
}

fn engine_from(name: &str) -> Engine {
    match name {
        "scalar" => Engine::Scalar,
        "fastscalar" => Engine::FastScalar,
        "fast" => Engine::Fast,
        other => panic!("unknown engine {other} (scalar|fastscalar|fast)"),
    }
}

fn default_engine() -> Engine {
    if avx2_available() {
        Engine::Fast
    } else {
        Engine::FastScalar
    }
}

// ------------------------------------------------------------------ parity runner

/// cells.txt format (written by parity.py):
///   # comment
///   cell <id> <off> <L> <model> <abort_at> <abort_margin> <stream>
///   R <300 ints>
///   T init0 | init1 | dec0 | dec1
/// stream: tot  |  v:1,2,3,... (n+margin values, the ts slice)
/// init1/dec1 use abort_at; init0/dec0 run without the abort. Writes actual.txt:
///   <id> <task> ok ptrs=<csv> score=<.17g> skips=<n>
///   <id> <task> abort
///   <id> <task> ok ioc=<.17g> wcol=<csv> skips=<n>
fn cmd_parity(args: &[String]) {
    let mut cells_path = String::from("cells.txt");
    let mut actual_path = String::from("actual.txt");
    let mut engine = default_engine();
    let mut positional = 0usize;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--engine" => {
                engine = engine_from(&args[i + 1]);
                i += 2;
            }
            "--out" => {
                actual_path = args[i + 1].clone();
                i += 2;
            }
            other => {
                if positional == 0 {
                    cells_path = other.to_string();
                } else if positional == 1 {
                    actual_path = other.to_string();
                } else {
                    panic!("too many positional args");
                }
                positional += 1;
                i += 1;
            }
        }
    }
    if engine == Engine::Fast && !avx2_available() {
        eprintln!("engine 'fast' requires AVX2+FMA; use --engine fastscalar");
        exit(2);
    }
    let txt = fs::read_to_string(&cells_path).unwrap_or_else(|e| panic!("{cells_path}: {e}"));
    let lines: Vec<&str> = txt.lines().collect();
    let mut out = BufWriter::new(fs::File::create(&actual_path).unwrap());
    let mut li = 0;
    let beam = 24usize;
    let max_em = 5usize;
    let beam_a = 12usize;
    while li < lines.len() {
        let line = lines[li];
        if line.is_empty() || line.starts_with('#') {
            li += 1;
            continue;
        }
        let parts: Vec<&str> = line.split_whitespace().collect();
        assert_eq!(parts[0], "cell", "bad cell line: {line}");
        let id = parts[1];
        let off: i64 = parts[2].parse().unwrap();
        let L: usize = parts[3].parse().unwrap();
        let model: u8 = parts[4].parse().unwrap();
        let abort_at: usize = parts[5].parse().unwrap();
        let abort_margin: f64 = parts[6].parse().unwrap();
        let stream = parts[7];
        li += 1;
        let runes: Vec<u8> = lines[li]
            .strip_prefix("R ")
            .unwrap()
            .split_whitespace()
            .map(|x| x.parse().unwrap())
            .collect();
        li += 1;
        assert_eq!(runes.len(), 300, "cell {id}: window is not 300 runes");
        // ts: the stream slice [off, off+n+margin) and a full tvals for decode()
        let n = runes.len();
        let margin = n / 4 + 32;
        let (ts, tvals): (Vec<u8>, Vec<u8>) = if stream == "tot" {
            let t = totient(off as usize + n + margin);
            (
                t[off as usize..off as usize + n + margin].to_vec(),
                t,
            )
        } else if let Some(v) = stream.strip_prefix("v:") {
            let vals: Vec<u8> = v.split(',').map(|x| x.parse().unwrap()).collect();
            assert_eq!(vals.len(), n + margin, "cell {id}: stream length");
            let mut full = vec![0u8; off as usize + n + margin];
            full[off as usize..off as usize + n + margin].copy_from_slice(&vals);
            (vals, full)
        } else {
            panic!("cell {id}: bad stream {stream}");
        };
        let abort_ll = |L: usize| -> f64 {
            if abort_at != 0 {
                abort_at as f64 * (UNI + abort_margin) + L as f64 * LN29
            } else {
                0.0
            }
        };
        // tasks
        while li < lines.len() {
            let tline = lines[li];
            let Some(task) = tline.strip_prefix("T ") else { break };
            li += 1;
            match task {
                "init0" | "init1" => {
                    let (at, ll) = if task == "init1" { (abort_at, abort_ll(L)) } else { (0, 0.0) };
                    let r = match engine {
                        Engine::Scalar => init_beam_scalar(&runes, &ts, L, false, beam_a, at, ll),
                        Engine::FastScalar => {
                            init_beam_fastscalar(&runes, &ts, L, false, beam_a, at, ll)
                        }
                        Engine::Fast => unsafe {
                            init_beam_fast_avx2(&runes, &ts, L, false, beam_a, at, ll)
                        },
                    };
                    match r {
                        None => writeln!(out, "{id} {task} abort").unwrap(),
                        Some((ptrs, score)) => {
                            let sk = skips_of(&ptrs);
                            let csv: Vec<String> = ptrs.iter().map(|x| x.to_string()).collect();
                            writeln!(
                                out,
                                "{id} {task} ok ptrs={} score={:.17} skips={sk}",
                                csv.join(","),
                                score
                            )
                            .unwrap();
                        }
                    }
                }
                "dec0" | "dec1" => {
                    let (at, mg) = if task == "dec1" { (abort_at, abort_margin) } else { (0, 0.0) };
                    let d = decode(
                        &runes,
                        -1,
                        &tvals,
                        off,
                        L,
                        model,
                        false,
                        beam,
                        max_em,
                        beam_a,
                        at,
                        mg,
                        engine,
                    );
                    if d.aborted {
                        writeln!(out, "{id} {task} abort").unwrap();
                    } else {
                        let csv: Vec<String> = d.wcol.iter().map(|x| x.to_string()).collect();
                        writeln!(
                            out,
                            "{id} {task} ok ioc={:.17} wcol={} skips={}",
                            d.ioc,
                            csv.join(","),
                            d.skips
                        )
                        .unwrap();
                    }
                }
                other => panic!("cell {id}: bad task {other}"),
            }
        }
    }
}

// ------------------------------------------------------------------ decode CLI

fn cmd_decode(args: &[String]) {
    if args.is_empty() || args[0].starts_with('-') {
        eprintln!(
            "usage: h5rs decode <window.txt> <offset> <L> <model> [--engine scalar|fastscalar|fast]\n\
             [--no-abort] [--abort <at> <margin>] [--litf] [--beam <n>] [--max-em <n>] [--beam-a <n>]"
        );
        exit(2);
    }
    let path = &args[0];
    let off: i64 = args[1].parse().unwrap();
    let L: usize = args[2].parse().unwrap();
    let model: u8 = args[3].parse().unwrap();
    let mut engine = default_engine();
    let mut litf = false;
    let mut beam = 24usize;
    let mut max_em = 5usize;
    let mut beam_a = 12usize;
    let mut abort_at = 120usize;
    let mut abort_margin = 0.9;
    let mut i = 4;
    while i < args.len() {
        match args[i].as_str() {
            "--engine" => {
                engine = engine_from(&args[i + 1]);
                i += 2;
            }
            "--litf" => {
                litf = true;
                i += 1;
            }
            "--beam" => {
                beam = args[i + 1].parse().unwrap();
                i += 2;
            }
            "--max-em" => {
                max_em = args[i + 1].parse().unwrap();
                i += 2;
            }
            "--beam-a" => {
                beam_a = args[i + 1].parse().unwrap();
                i += 2;
            }
            "--no-abort" => {
                abort_at = 0;
                abort_margin = 0.0;
                i += 1;
            }
            "--abort" => {
                abort_at = args[i + 1].parse().unwrap();
                abort_margin = args[i + 2].parse().unwrap();
                i += 3;
            }
            other => panic!("bad flag {other}"),
        }
    }
    if engine == Engine::Fast && !avx2_available() {
        eprintln!("engine 'fast' requires AVX2+FMA; using fastscalar");
        engine = Engine::FastScalar;
    }
    let wins = load_windows(path);
    let win = &wins[0];
    let c: Vec<u8> = win.runes.iter().copied().take(300).collect();
    // the totient stream is generated internally
    let tvals = totient(off as usize + c.len() + c.len() / 4 + 32 + 1);
    let d = decode(
        &c,
        win.prev,
        &tvals,
        off,
        L,
        model,
        litf,
        beam,
        max_em,
        beam_a,
        abort_at,
        abort_margin,
        engine,
    );
    if d.aborted {
        println!("ABORT");
    } else {
        let csv: Vec<String> = d.wcol.iter().map(|x| x.to_string()).collect();
        println!("ioc={:.10} wcol={} skips={}", d.ioc, csv.join(","), d.skips);
    }
}

// ------------------------------------------------------------------ sweep driver

/// Small sweep driver for the later campaign: per window, run the (offset, L) grid on one
/// stream (tot = the internal totient; rand:<seed> = a matched-null replicate), tracking the
/// best cell and every cell with IoC >= the hit threshold. The candidate rule of the full
/// campaign (IoC >= 1.6 AND >= the window's matched-null max + 0.15, then a whole-window
/// re-decode in Python) is applied on top of this driver's output.
fn cmd_sweep(args: &[String]) {
    let mut pos = 0;
    let mut get = |args: &[String], pos: &mut usize, name: &str| -> String {
        assert!(*pos < args.len(), "missing {name}");
        let v = args[*pos].clone();
        *pos += 1;
        v
    };
    let path = get(args, &mut pos, "windows.txt");
    let stream = get(args, &mut pos, "stream (tot|rand:<seed>)");
    let off0: i64 = get(args, &mut pos, "off0").parse().unwrap();
    let off1: i64 = get(args, &mut pos, "off1").parse().unwrap();
    let L0: usize = get(args, &mut pos, "L0").parse().unwrap();
    let L1: usize = get(args, &mut pos, "L1").parse().unwrap();
    let model: u8 = get(args, &mut pos, "model (0|1)").parse().unwrap();
    let threads: usize = get(args, &mut pos, "threads").parse().unwrap();
    let out_path = get(args, &mut pos, "out.tsv");
    let mut engine = default_engine();
    let mut hits_thresh = 1.6f64;
    while pos < args.len() {
        match args[pos].as_str() {
            "--engine" => {
                engine = engine_from(&args[pos + 1]);
                pos += 2;
            }
            "--hits" => {
                hits_thresh = args[pos + 1].parse().unwrap();
                pos += 2;
            }
            other => panic!("bad flag {other}"),
        }
    }
    if engine == Engine::Fast && !avx2_available() {
        eprintln!("engine 'fast' requires AVX2+FMA; using fastscalar");
        engine = Engine::FastScalar;
    }
    let wins = load_windows(&path);
    let n = 300usize;
    let margin = n / 4 + 32;
    // build the stream once (max offset range + n + margin)
    let max_off = off1 as usize + n + margin;
    let tvals: Vec<u8> = if stream == "tot" {
        totient(max_off)
    } else if let Some(seed) = stream.strip_prefix("rand:") {
        random_stream(max_off, seed.parse().unwrap())
    } else {
        panic!("bad stream {stream}");
    };
    let t0 = std::time::Instant::now();
    let nw = wins.len();
    let counter = std::sync::atomic::AtomicUsize::new(0);
    let results: Vec<std::sync::Mutex<Vec<(usize, f64, i64, usize, usize)>>> = (0..nw)
        .map(|_| std::sync::Mutex::new(Vec::new()))
        .collect();
    let hits: Vec<std::sync::Mutex<Vec<(f64, i64, usize)>>> = (0..nw)
        .map(|_| std::sync::Mutex::new(Vec::new()))
        .collect();
    std::thread::scope(|scope| {
        for _ in 0..threads {
            let wins = &wins;
            let tvals = &tvals;
            let counter = &counter;
            let results = &results;
            let hits = &hits;
            scope.spawn(move || {
                loop {
                    let k = counter.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                    if k >= nw {
                        break;
                    }
                    let win = &wins[k];
                    let c: Vec<u8> = win.runes.iter().copied().take(n).collect();
                    let mut best: (f64, i64, usize) = (0.0, -1, 0);
                    for off in off0..off1 {
                        for L in L0..=L1 {
                            let d = decode(
                                &c,
                                win.prev,
                                tvals,
                                off,
                                L,
                                model,
                                false,
                                24,
                                5,
                                12,
                                120,
                                0.9,
                                engine,
                            );
                            if d.ioc > best.0 {
                                best = (d.ioc, off, L);
                            }
                            if d.ioc >= hits_thresh {
                                hits[k].lock().unwrap().push((d.ioc, off, L));
                            }
                        }
                    }
                    results[k].lock().unwrap().push((k, best.0, best.1, best.2, model as usize));
                }
            });
        }
    });
    let el = t0.elapsed().as_secs_f64();
    let total_cells = nw as u64 * (off1 - off0) as u64 * (L1 - L0 + 1) as u64;
    let mut o = BufWriter::new(fs::File::create(&out_path).unwrap());
    writeln!(o, "# h5rs sweep {stream} offs {off0}..{off1} L {L0}..{L1} model {model} \
             engine {} threads {threads}", engine.name()).unwrap();
    writeln!(o, "# {} cells in {:.1}s = {:.0} decodes/s wall ({:.0}/thread)",
             total_cells, el, total_cells as f64 / el, total_cells as f64 / el / threads as f64).unwrap();
    writeln!(o, "window\tbest_ioc\toff\tL\tmodel\thits").unwrap();
    for k in 0..nw {
        let r = results[k].lock().unwrap();
        let h = hits[k].lock().unwrap();
        let best = r.iter().map(|x| (x.1, x.2, x.3)).next().unwrap_or((0.0, -1, 0));
        writeln!(
            o,
            "{}\t{:.4}\t{}\t{}\t{}\t{}",
            wins[k].name,
            best.0,
            best.1,
            best.2,
            model,
            h.len()
        )
        .unwrap();
        for &(hi, ho, hl) in h.iter() {
            writeln!(o, "  hit\t{:.4}\t{}\t{}", hi, ho, hl).unwrap();
        }
    }
}

// ------------------------------------------------------------------ bench

fn cmd_bench(args: &[String]) {
    let mut threads = 1usize;
    let mut secs = 3.0f64;
    let mut engine = default_engine();
    let mut full_path: Option<String> = None;
    let mut i = 0;
    while i < args.len() {
        match args[i].as_str() {
            "--threads" => {
                threads = args[i + 1].parse().unwrap();
                i += 2;
            }
            "--secs" => {
                secs = args[i + 1].parse().unwrap();
                i += 2;
            }
            "--engine" => {
                engine = engine_from(&args[i + 1]);
                i += 2;
            }
            "--full" => {
                full_path = Some(args[i + 1].clone());
                i += 2;
            }
            other => panic!("bad flag {other}"),
        }
    }
    if engine == Engine::Fast && !avx2_available() {
        eprintln!("engine 'fast' requires AVX2+FMA; using fastscalar");
        engine = Engine::FastScalar;
    }
    println!("# h5rs bench: engine {}, threads {}, budget {secs}s/thread", engine.name(), threads);
    if let Some(path) = &full_path {
        // full-decode rate: the truth window (no abort, EM runs)
        let wins = load_windows(path);
        let c: Vec<u8> = wins[0].runes.iter().copied().take(300).collect();
        let tvals = totient(1234 + 300 + 107 + 1);
        let t0 = std::time::Instant::now();
        let mut reps = 0usize;
        while t0.elapsed().as_secs_f64() < secs {
            let _d = decode(&c, -1, &tvals, 1234, 8, 0, false, 24, 5, 12, 0, 0.0, engine);
            reps += 1;
        }
        let el = t0.elapsed().as_secs_f64();
        println!("full_decode_rate_dec_per_s {:.0}", reps as f64 / el);
    }
    // the campaign workhorse: aborting null cells (abort 120/0.9)
    let ncell = 64usize;
    let mut windows: Vec<Vec<u8>> = Vec::with_capacity(ncell);
    for k in 0..ncell {
        windows.push(random_stream(300, 1000 + k as u64));
    }
    let tvals = totient(4000);
    let counter = std::sync::atomic::AtomicUsize::new(0);
    let total = std::sync::atomic::AtomicU64::new(0);
    let t0 = std::time::Instant::now();
    std::thread::scope(|scope| {
        let windows = &windows;
        let tvals = &tvals;
        let counter = &counter;
        let total = &total;
        let t0 = &t0;
        for _ in 0..threads {
            scope.spawn(move || {
                loop {
                    if t0.elapsed().as_secs_f64() >= secs {
                        break;
                    }
                    let k = counter.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                    let c = &windows[k % ncell];
                    let off = (k * 37 % 1500) as i64;
                    let _d = decode(c, -1, tvals, off, 8, 0, false, 24, 5, 12, 120, 0.9, engine);
                    total.fetch_add(1, std::sync::atomic::Ordering::Relaxed);
                }
            });
        }
    });
    let el = t0.elapsed().as_secs_f64();
    let tot = total.load(std::sync::atomic::Ordering::Relaxed);
    println!("# null-abort cells decoded: {tot} in {el:.2}s");
    println!("null_abort_rate_dec_per_s {:.0}", tot as f64 / el);
    println!("null_abort_rate_per_thread {:.0}", tot as f64 / el / threads as f64);
    println!("# projection for the full library sweep (880,000,000 decodes):");
    println!("projection_hours_8_threads {:.1}", 880e6 / (tot as f64 / el));
}

// ------------------------------------------------------------------ totient cross-check

fn cmd_totient(args: &[String]) {
    let n: usize = args[0].parse().unwrap();
    let t = totient(n);
    let s: Vec<String> = t.iter().map(|x| x.to_string()).collect();
    println!("{}", s.join(" "));
}

fn main() {
    let args: Vec<String> = env::args().skip(1).collect();
    if args.is_empty() {
        eprintln!(
            "h5rs - the H5 first-slice engine (bit-exact with work/h5slice)\n\
             commands:\n\
             \x20 decode <window.txt> <offset> <L> <model> [--engine e] [--no-abort] [--litf] [--beam n] [--max-em n] [--beam-a n]\n\
             \x20 parity <cells.txt> [actual.txt] [--engine e]\n\
             \x20 sweep <windows.txt> <stream> <off0> <off1> <L0> <L1> <model> <threads> <out.tsv> [--hits t] [--engine e]\n\
             \x20 bench [--threads T] [--secs S] [--engine e] [--full <truth.txt>]\n\
             \x20 totient <n>"
        );
        exit(2);
    }
    match args[0].as_str() {
        "decode" => cmd_decode(&args[1..]),
        "parity" => cmd_parity(&args[1..]),
        "sweep" => cmd_sweep(&args[1..]),
        "bench" => cmd_bench(&args[1..]),
        "totient" => cmd_totient(&args[1..]),
        other => {
            eprintln!("unknown command {other}");
            exit(2);
        }
    }
}
