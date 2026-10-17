//! layer2: a screen for LP2 as a TWO-LAYER cipher built from the methods of the solved pages, under the
//! anti-repeat rule (hypothesis H-LAYER, work/log/hypotheses_2026-10-17.md):
//!
//!   inner:  q_i = p_i + s_in * K[phi mod m]   Vigenere with a keyword of period m (Welcome, Koan 2), optionally with
//!           their literal-F rule: a plaintext F is written as F and does not advance phi;
//!   outer:  c_i = q_i + mult * S_j            a number stream with kscreen's anti-repeat models (skip / coin).
//!
//! kscreen cannot see this: decoding the outer stream leaves q, a Vigenere text with IoC ~1.1-1.2, far below its
//! 1.40 threshold, and the literal F of the inner layer is hidden by the outer one (no F excess in the ciphertext).
//! The collision check of the outer layer depends only on c and S (the encryptor compares q_i + S_j with c_{i-1}),
//! so the outer branch points are exactly kscreen's (forward key only); the inner layer only changes what is scored.
//!
//!   mode=bigram    keywords from a file, every phase, both inner signs, identity or Atbash plaintext alphabet: score =
//!                  English rune-bigram log-odds per rune (x10, work/phpmt/data/bigram.txt). The main screen: a true key
//!                  gives about +7, random decodes about -15, and unlike the IoC modes it does not overfit the literal-F
//!                  branch (which lets a decode re-phase the keyword at every decoded F)
//!   mode=known     the same keywords scored by the IoC of the decoded letters (any plaintext alphabet and language)
//!   mode=periodic  ANY keyword of period m (m in ms): score = z-score of the coincidences within the m columns (letters
//!                  grouped by phi mod m); with litf=1 a decoded F may be literal (phi does not advance; it is then left
//!                  out of the columns). Weaker than the keyword modes (short columns, overfitting with litf=1): its hits
//!                  are checked by estimating the keyword and rescoring in mode=bigram (verify.py)
//!
//! Modes:
//!   screen <windows.txt> <family> <out.tsv> [mode=bigram kw=<file> isigns=1,28 atb=0,1 | mode=known kw=<file> isigns=1,28
//!          | mode=periodic ms=2:16] [litf=0,1] [n=300] [beam=16] [mults=1,28] [models=0,1] [threads=T] [top=2000]
//!          [abort=<runes>:<score>|0] [items=a:b] [only=<item>] [offs=a:b] [minlen=50]
//!   plant  <plain_windows.txt> <family> <item> <offset> <mult> <model> <keep> <seed> <keyword a,b,c,..> <phase>
//!          <isign> <litf> <atb> <out.txt>
//!   verify <windows.txt> <family> <item> <offset> <mult> <model> <window|all> [mode=bigram|known kwvals=a,b,.. isign=1
//!          phase=0 litf=0 atb=0 | mode=periodic m=8 litf=0] [n=0] [beam=64] [controls=K]
//! Families: file:<path.ksb> (written by work/kscreen/export.py or work/layer2/export.py), rand:<count>:<seed>.
//! Windows: kscreen's format (W name prev / R runes / L lens / optional P collision values).

use std::env;
use std::fs;
use std::io::{BufWriter, Write};
use std::sync::Mutex;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;

const Q: usize = 29;
const MAXM: usize = 24;
const HBINS: usize = 400;

// ------------------------------------------------------------------ inputs (formats shared with kscreen)

struct Win {
    name: String,
    prev: i32,
    runes: Vec<u8>,
    pv: Vec<i32>,
    lens: String,
}

fn load_windows(path: &str) -> Vec<Win> {
    let txt = fs::read_to_string(path).unwrap_or_else(|e| panic!("{path}: {e}"));
    let mut out: Vec<Win> = Vec::new();
    for line in txt.lines() {
        if let Some(rest) = line.strip_prefix("W ") {
            let mut it = rest.split_whitespace();
            let name = it.next().expect("window name").to_string();
            let prev = it.next().map(|x| x.parse().expect("prev rune")).unwrap_or(-1);
            out.push(Win { name, prev, runes: Vec::new(), pv: Vec::new(), lens: String::new() });
        } else if let Some(rest) = line.strip_prefix("R ") {
            out.last_mut().expect("R line before W line").runes =
                rest.split_whitespace().map(|x| x.parse::<u8>().expect("rune")).collect();
        } else if let Some(rest) = line.strip_prefix("L ") {
            out.last_mut().expect("L line before W line").lens = rest.to_string();
        } else if let Some(rest) = line.strip_prefix("P ") {
            out.last_mut().expect("P line before W line").pv =
                rest.split_whitespace().map(|x| x.parse().expect("pv")).collect();
        }
    }
    for w in out.iter_mut() {
        if w.pv.is_empty() {
            w.pv = (0..w.runes.len()).map(|i| if i == 0 { w.prev } else { w.runes[i - 1] as i32 }).collect();
        }
        assert_eq!(w.pv.len(), w.runes.len(), "{}: P line length", w.name);
        assert!(w.runes.iter().all(|&r| (r as usize) < Q), "{}: rune out of range", w.name);
    }
    out
}

struct Ks {
    name: String,
    v: Vec<u8>,
}

fn rd_u32(b: &[u8], p: &mut usize) -> u32 {
    let v = u32::from_le_bytes([b[*p], b[*p + 1], b[*p + 2], b[*p + 3]]);
    *p += 4;
    v
}

fn load_ksb(path: &str) -> Vec<Ks> {
    let b = fs::read(path).unwrap_or_else(|e| panic!("{path}: {e}"));
    assert!(b.len() >= 8 && &b[..4] == b"KSB1", "{path}: not a KSB1 keystream file");
    let mut p = 4;
    let n = rd_u32(&b, &mut p) as usize;
    let mut out = Vec::with_capacity(n);
    for _ in 0..n {
        let l = u16::from_le_bytes([b[p], b[p + 1]]) as usize;
        p += 2;
        let name = String::from_utf8(b[p..p + l].to_vec()).expect("utf-8 keystream name");
        p += l;
        let len = rd_u32(&b, &mut p) as usize;
        let v = b[p..p + len].to_vec();
        p += len;
        assert!(v.iter().all(|&x| (x as usize) < Q), "{name}: key value out of range");
        out.push(Ks { name, v });
    }
    out
}

/// splitmix64 (controls and plant coins only)
struct Rng(u64);

impl Rng {
    fn next(&mut self) -> u64 {
        self.0 = self.0.wrapping_add(0x9E37_79B9_7F4A_7C15);
        let mut z = self.0;
        z = (z ^ (z >> 30)).wrapping_mul(0xBF58_476D_1CE4_E5B9);
        z = (z ^ (z >> 27)).wrapping_mul(0x94D0_49BB_1331_11EB);
        z ^ (z >> 31)
    }
    fn below(&mut self, n: u64) -> u64 {
        ((self.next() >> 32) * n) >> 32
    }
    fn unit(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
}

fn family(spec: &str) -> Vec<Ks> {
    let (kind, arg) = spec.split_once(':').unwrap_or((spec, ""));
    match kind {
        "file" => load_ksb(arg),
        "rand" => {
            let (cnt, seed) = arg.split_once(':').unwrap_or((arg, "1"));
            let cnt: usize = cnt.parse().expect("rand:<count>:<seed>");
            let mut r = Rng(seed.parse::<u64>().expect("rand seed") ^ 0x05EE_D5EE_D5EE_D5EE);
            (0..cnt).map(|i| Ks { name: format!("RANDOM {i}"), v: (0..20000).map(|_| r.below(Q as u64) as u8).collect() }).collect()
        }
        _ => panic!("unknown family {spec}: use file:<path> or rand:<count>:<seed>"),
    }
}

fn find_item(fam: &[Ks], name: &str) -> usize {
    fam.iter().position(|k| k.name == name).unwrap_or_else(|| panic!("no keystream named {name:?}"))
}

/// keywords file: one keyword per line, `name v0 v1 ...` (rune values 0..28)
fn load_keywords(path: &str) -> Vec<(String, Vec<u8>)> {
    let txt = fs::read_to_string(path).unwrap_or_else(|e| panic!("{path}: {e}"));
    let mut out = Vec::new();
    for line in txt.lines().filter(|l| !l.trim().is_empty() && !l.starts_with('#')) {
        let mut it = line.split_whitespace();
        let name = it.next().unwrap().to_string();
        let v: Vec<u8> = it.map(|x| x.parse().expect("keyword value")).collect();
        assert!(!v.is_empty() && v.iter().all(|&x| (x as usize) < Q), "keyword {name}");
        out.push((name, v));
    }
    out
}

fn opts(args: &[String]) -> std::collections::HashMap<String, String> {
    args.iter()
        .map(|a| {
            let (k, v) = a.split_once('=').unwrap_or_else(|| panic!("option {a:?} must be key=value"));
            (k.to_string(), v.to_string())
        })
        .collect()
}

fn get<T: std::str::FromStr>(o: &std::collections::HashMap<String, String>, k: &str, d: T) -> T {
    o.get(k).map(|v| v.parse().unwrap_or_else(|_| panic!("bad value for {k}"))).unwrap_or(d)
}

fn list_u8(s: &str) -> Vec<u8> {
    s.split(',').filter(|x| !x.is_empty()).map(|x| x.parse().expect("number")).collect()
}

fn join<T: ToString>(v: &[T]) -> String {
    v.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(",")
}

// ------------------------------------------------------------------ decoding

struct Tb {
    sub: [[u8; Q]; Q],
    add: [[u8; Q]; Q],
}

fn tables() -> Tb {
    let mut t = Tb { sub: [[0; Q]; Q], add: [[0; Q]; Q] };
    for a in 0..Q {
        for b in 0..Q {
            t.sub[a][b] = ((a + Q - b) % Q) as u8;
            t.add[a][b] = ((a + b) % Q) as u8;
        }
    }
    t
}

/// The outer layer's candidates at one rune, exactly as kscreen's forward models: (q, next pointer).
/// cand[0] is the value without a re-draw.
#[inline]
fn outer_cands(ci: usize, pv: i32, mk: &[u8], j: usize, model: u8, tb: &Tb, cand: &mut [(u8, u32); 3]) -> usize {
    let k0 = mk[j] as usize;
    let nj0 = if model == 1 && pv == ci as i32 { j + 2 } else { j + 1 };
    cand[0] = (tb.sub[ci][k0], nj0 as u32);
    let mut n = 1;
    if pv >= 0 {
        let pvu = pv as u8;
        if model == 0 {
            let k1 = mk[j + 1] as usize;
            let t1 = tb.sub[ci][k1];
            if tb.add[t1 as usize][k0] == pvu {
                cand[n] = (t1, (j + 2) as u32);
                n += 1;
            }
            let k2 = mk[j + 2] as usize;
            let t2 = tb.sub[ci][k2];
            if tb.add[t2 as usize][k0] == pvu && tb.add[t2 as usize][k1] == pvu {
                cand[n] = (t2, (j + 3) as u32);
                n += 1;
            }
        } else {
            let k2 = mk[j + 2] as usize;
            let t2 = tb.sub[ci][k2];
            if tb.add[t2 as usize][k0] == pvu {
                cand[n] = (t2, (j + 3) as u32);
                n += 1;
            }
        }
    }
    n
}

#[derive(Clone, Copy)]
struct KSt {
    j: u32,
    ph: u16,
    s: u32,
    cnt: [u16; Q],
}

#[inline]
fn k_take(st: &mut KSt, p: usize, nj: u32, nph: u16) {
    st.s += 2 * st.cnt[p] as u32;
    st.cnt[p] += 1;
    st.j = nj;
    st.ph = nph;
}

/// Known keyword: beam over (outer pointer j, inner phase). Returns (best pair count, runes used).
#[allow(clippy::too_many_arguments)]
fn decode_known(
    c: &[u8],
    pvs: &[i32],
    mk: &[u8],
    kk: &[u8],
    ph0: usize,
    litf: bool,
    model: u8,
    n: usize,
    beam: usize,
    abort_at: usize,
    abort_s: u32,
    tb: &Tb,
    cur: &mut Vec<KSt>,
    extra: &mut Vec<KSt>,
) -> (u32, usize) {
    let m = kk.len();
    cur.clear();
    cur.push(KSt { j: 0, ph: ph0 as u16, s: 0, cnt: [0; Q] });
    let klen = mk.len();
    let mut cand = [(0u8, 0u32); 3];
    for i in 0..n {
        let ci = c[i] as usize;
        let pv = pvs[i];
        extra.clear();
        let mut idx = 0;
        while idx < cur.len() {
            let j = cur[idx].j as usize;
            if j + 3 > klen {
                cur.swap_remove(idx);
                continue;
            }
            let nc = outer_cands(ci, pv, mk, j, model, tb, &mut cand);
            let base = cur[idx];
            let ph = base.ph as usize;
            let nph = ((ph + 1) % m) as u16;
            for (k, &(q, nj)) in cand[..nc].iter().enumerate() {
                if k > 0 {
                    let mut s2 = base;
                    k_take(&mut s2, tb.sub[q as usize][kk[ph] as usize] as usize, nj, nph);
                    extra.push(s2);
                }
                if litf && q == 0 {
                    let mut s3 = base;
                    k_take(&mut s3, 0, nj, ph as u16);
                    extra.push(s3);
                }
            }
            let (q0, nj0) = cand[0];
            k_take(&mut cur[idx], tb.sub[q0 as usize][kk[ph] as usize] as usize, nj0, nph);
            idx += 1;
        }
        cur.extend_from_slice(extra);
        if cur.is_empty() {
            return (0, i.max(2));
        }
        if cur.len() > 1 {
            let mut a = 0;
            while a < cur.len() {
                let mut b = a + 1;
                while b < cur.len() {
                    if cur[b].j == cur[a].j && cur[b].ph == cur[a].ph {
                        if cur[b].s > cur[a].s {
                            cur[a] = cur[b];
                        }
                        cur.swap_remove(b);
                    } else {
                        b += 1;
                    }
                }
                a += 1;
            }
            if cur.len() > beam {
                cur.sort_by(|x, y| y.s.cmp(&x.s));
                cur.truncate(beam);
            }
        }
        if i + 1 == abort_at {
            let best = cur.iter().map(|s| s.s).max().unwrap_or(0);
            if best < abort_s {
                return (best, abort_at);
            }
        }
    }
    (cur.iter().map(|s| s.s).max().unwrap_or(0), n)
}

#[derive(Clone, Copy)]
struct PSt {
    j: u32,
    ph: u8,
    s: u32,
    d: u32,
    ncol: [u8; MAXM],
    cnt: [[u8; Q]; MAXM],
}

impl PSt {
    #[inline]
    /// z-score of the column coincidences against uniform letters: (29 s - d) / sqrt(56 d), where s and d count ordered
    /// pairs (equal letters, all letters) within columns. Unlike the column IoC it is comparable across m (short columns
    /// give large IoC swings) and across states that left different letters out (literal F).
    fn score(&self) -> f32 {
        if self.d == 0 { 0.0 } else { (Q as f32 * self.s as f32 - self.d as f32) / (56.0 * self.d as f32).sqrt() }
    }
}

#[inline]
fn p_take(st: &mut PSt, q: u8, nj: u32, m: usize) {
    let col = st.ph as usize;
    let x = q as usize;
    st.s += 2 * st.cnt[col][x] as u32;
    st.cnt[col][x] += 1;
    st.d += 2 * st.ncol[col] as u32;
    st.ncol[col] += 1;
    st.ph = ((col + 1) % m) as u8;
    st.j = nj;
}

/// Unknown keyword of period m: beam over (j, column phase); score = IoC within columns. Returns (best IoC, used).
#[allow(clippy::too_many_arguments)]
fn decode_periodic(
    c: &[u8],
    pvs: &[i32],
    mk: &[u8],
    m: usize,
    litf: bool,
    model: u8,
    n: usize,
    beam: usize,
    abort_at: usize,
    abort_score: f32,
    tb: &Tb,
    cur: &mut Vec<PSt>,
    extra: &mut Vec<PSt>,
) -> (f32, usize) {
    cur.clear();
    cur.push(PSt { j: 0, ph: 0, s: 0, d: 0, ncol: [0; MAXM], cnt: [[0; Q]; MAXM] });
    let klen = mk.len();
    let mut cand = [(0u8, 0u32); 3];
    for i in 0..n {
        let ci = c[i] as usize;
        let pv = pvs[i];
        extra.clear();
        let mut idx = 0;
        while idx < cur.len() {
            let j = cur[idx].j as usize;
            if j + 3 > klen {
                cur.swap_remove(idx);
                continue;
            }
            let nc = outer_cands(ci, pv, mk, j, model, tb, &mut cand);
            let needs_copy = nc > 1 || (litf && cand[..nc].iter().any(|&(q, _)| q == 0));
            if needs_copy {
                let base = cur[idx];
                for (k, &(q, nj)) in cand[..nc].iter().enumerate() {
                    if k > 0 {
                        let mut s2 = base;
                        p_take(&mut s2, q, nj, m);
                        extra.push(s2);
                    }
                    if litf && q == 0 {
                        let mut s3 = base;
                        s3.j = nj; // literal F: not keyed, phase unchanged, not counted
                        extra.push(s3);
                    }
                }
            }
            let (q0, nj0) = cand[0];
            p_take(&mut cur[idx], q0, nj0, m);
            idx += 1;
        }
        cur.extend_from_slice(extra);
        if cur.is_empty() {
            return (0.0, i.max(2));
        }
        if cur.len() > 1 {
            let mut a = 0;
            while a < cur.len() {
                let mut b = a + 1;
                while b < cur.len() {
                    if cur[b].j == cur[a].j && cur[b].ph == cur[a].ph {
                        if cur[b].score() > cur[a].score() {
                            cur[a] = cur[b];
                        }
                        cur.swap_remove(b);
                    } else {
                        b += 1;
                    }
                }
                a += 1;
            }
            while cur.len() > beam {
                // drop the worst (ties: the later one); states are large, so no sorting or shifting
                let mut w = 0;
                for k in 1..cur.len() {
                    if cur[k].score() <= cur[w].score() {
                        w = k;
                    }
                }
                cur.swap_remove(w);
            }
        }
        if i + 1 == abort_at {
            let best = cur.iter().map(|s| s.score()).fold(0.0f32, f32::max);
            if best < abort_score {
                return (best, abort_at);
            }
        }
    }
    (cur.iter().map(|s| s.score()).fold(0.0f32, f32::max), n)
}

/// English rune-bigram table (work/phpmt/data/bigram.txt): tbl[a][b] = round(10 ln(29 P(b | a))), row 29 = unigram log-odds
fn load_bigram(path: &str) -> Vec<[i16; Q]> {
    let txt = fs::read_to_string(path).unwrap_or_else(|e| panic!("{path}: {e}"));
    let rows: Vec<[i16; Q]> = txt
        .lines()
        .filter(|l| !l.trim().is_empty())
        .map(|l| {
            let v: Vec<i16> = l.split_whitespace().map(|x| x.parse().expect("bigram value")).collect();
            assert_eq!(v.len(), Q, "bigram row length");
            let mut r = [0i16; Q];
            r.copy_from_slice(&v);
            r
        })
        .collect();
    assert_eq!(rows.len(), Q + 1, "bigram table: 29 rows + unigram row");
    rows
}

#[derive(Clone, Copy)]
struct BSt {
    j: u32,
    ph: u16,
    last: u8,
    s: i32,
}

/// Known keyword scored by the English bigram table (identity or Atbash plaintext alphabet). Returns (total, runes used).
#[allow(clippy::too_many_arguments)]
fn decode_known_bg(
    c: &[u8],
    pvs: &[i32],
    mk: &[u8],
    kk: &[u8],
    ph0: usize,
    litf: bool,
    atb: bool,
    model: u8,
    n: usize,
    beam: usize,
    abort_at: usize,
    abort_total: i32,
    tb: &Tb,
    tbl: &[[i16; Q]],
    cur: &mut Vec<BSt>,
    extra: &mut Vec<BSt>,
) -> (i32, usize) {
    let m = kk.len();
    cur.clear();
    cur.push(BSt { j: 0, ph: ph0 as u16, last: Q as u8, s: 0 });
    let klen = mk.len();
    let mut cand = [(0u8, 0u32); 3];
    let letter = |q: u8, ph: usize| -> usize {
        let x = tb.sub[q as usize][kk[ph] as usize] as usize;
        if atb { Q - 1 - x } else { x }
    };
    for i in 0..n {
        let ci = c[i] as usize;
        let pv = pvs[i];
        extra.clear();
        let mut idx = 0;
        while idx < cur.len() {
            let j = cur[idx].j as usize;
            if j + 3 > klen {
                cur.swap_remove(idx);
                continue;
            }
            let nc = outer_cands(ci, pv, mk, j, model, tb, &mut cand);
            let base = cur[idx];
            let ph = base.ph as usize;
            let nph = ((ph + 1) % m) as u16;
            for (k, &(q, nj)) in cand[..nc].iter().enumerate() {
                if k > 0 {
                    let p = letter(q, ph);
                    extra.push(BSt { j: nj, ph: nph, last: p as u8, s: base.s + tbl[base.last as usize][p] as i32 });
                }
                if litf && q == 0 {
                    extra.push(BSt { j: nj, ph: ph as u16, last: 0, s: base.s + tbl[base.last as usize][0] as i32 });
                }
            }
            let (q0, nj0) = cand[0];
            let p = letter(q0, ph);
            let st = &mut cur[idx];
            st.s += tbl[st.last as usize][p] as i32;
            st.last = p as u8;
            st.j = nj0;
            st.ph = nph;
            idx += 1;
        }
        cur.extend_from_slice(extra);
        if cur.is_empty() {
            return (i32::MIN / 2, i.max(2));
        }
        if cur.len() > 1 {
            let mut a = 0;
            while a < cur.len() {
                let mut b = a + 1;
                while b < cur.len() {
                    if cur[b].j == cur[a].j && cur[b].ph == cur[a].ph {
                        if cur[b].s > cur[a].s {
                            cur[a] = cur[b];
                        }
                        cur.swap_remove(b);
                    } else {
                        b += 1;
                    }
                }
                a += 1;
            }
            if cur.len() > beam {
                cur.sort_by(|x, y| y.s.cmp(&x.s));
                cur.truncate(beam);
            }
        }
        if i + 1 == abort_at {
            let best = cur.iter().map(|s| s.s).max().unwrap_or(i32::MIN / 2);
            if best < abort_total {
                return (best, abort_at);
            }
        }
    }
    (cur.iter().map(|s| s.s).max().unwrap_or(i32::MIN / 2), n)
}

// ------------------------------------------------------------------ screen

#[derive(Clone, Copy)]
struct Hit {
    score: f32,
    item: u32,
    off: u32,
    mult: u8,
    model: u8,
    win: u16,
    n: u16,
    cfg: u16, // keyword index (known) or m (periodic)
    isign: u8,
    ph: u8,
    litf: u8,
    atb: u8,
}

const NOHIT: Hit = Hit { score: f32::MIN, item: 0, off: 0, mult: 0, model: 0, win: 0, n: 0, cfg: 0, isign: 0, ph: 0, litf: 0, atb: 0 };

fn keep_top(v: &mut Vec<Hit>, top: usize) {
    v.sort_unstable_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
    v.truncate(top);
}

/// One inner configuration: (cfg, isign, phase, litf, signed keyword values or empty for periodic)
struct Inner {
    cfg: u16,
    isign: u8,
    ph: u8,
    litf: u8,
    atb: u8,
    kk: Vec<u8>,
}

fn mode_screen(args: &[String]) {
    if args.len() < 3 {
        eprintln!("usage: screen <windows.txt> <family> <out.tsv> [key=value ...]");
        std::process::exit(2);
    }
    let all_wins = load_windows(&args[0]);
    let fam = family(&args[1]);
    let out_path = &args[2];
    let o = opts(&args[3..]);
    let mode: String = get(&o, "mode", "periodic".to_string());
    let (periodic, bigram) = match mode.as_str() {
        "periodic" => (true, false),
        "known" => (false, false),
        "bigram" => (false, true),
        _ => panic!("mode=known|periodic|bigram"),
    };
    let atbs = list_u8(&get(&o, "atb", "0,1".to_string()));
    let tbl = if bigram { load_bigram(&get(&o, "bg", "../phpmt/data/bigram.txt".to_string())) } else { Vec::new() };
    let n_req: usize = get(&o, "n", 300);
    let beam: usize = get(&o, "beam", 16);
    let mults = list_u8(&get(&o, "mults", "1,28".to_string()));
    let models = list_u8(&get(&o, "models", "0,1".to_string()));
    let litfs = list_u8(&get(&o, "litf", "0,1".to_string()));
    let threads: usize = get(&o, "threads", std::thread::available_parallelism().map(|x| x.get()).unwrap_or(4));
    let top: usize = get(&o, "top", 2000);
    let minlen: usize = get(&o, "minlen", 50);
    let abort_spec: String =
        get(&o, "abort", if periodic { "150:2.5".to_string() } else if bigram { "30:-4".to_string() } else { "150:1.2".to_string() });
    let (abort_at, abort_score) = if abort_spec == "0" {
        (0usize, 0.0f64)
    } else {
        let (a, b) = abort_spec.split_once(':').expect("abort=<runes>:<score>");
        (a.parse().expect("abort runes"), b.parse().expect("abort score"))
    };
    let abort_s = (abort_score * abort_at as f64 * (abort_at as f64 - 1.0) / Q as f64).ceil() as u32;
    let abort_total = (abort_score * abort_at as f64).floor() as i32; // bigram: average per rune times runes

    let mut inners: Vec<Inner> = Vec::new();
    let mut kwnames: Vec<String> = Vec::new();
    if periodic {
        let ms = get(&o, "ms", "2:16".to_string());
        let (a, b) = ms.split_once(':').expect("ms=a:b");
        let (a, b): (usize, usize) = (a.parse().unwrap(), b.parse().unwrap());
        assert!(a >= 2 && b <= MAXM, "ms within 2..{MAXM} (u8 column counts)");
        for m in a..=b {
            for &lf in &litfs {
                inners.push(Inner { cfg: m as u16, isign: 1, ph: 0, litf: lf, atb: 0, kk: Vec::new() });
            }
        }
    } else {
        let kws = load_keywords(&get(&o, "kw", String::new()));
        let isigns = list_u8(&get(&o, "isigns", "1,28".to_string()));
        for (ki, (name, v)) in kws.iter().enumerate() {
            kwnames.push(name.clone());
            for &is in &isigns {
                let kk: Vec<u8> = v.iter().map(|&x| (x as usize * is as usize % Q) as u8).collect();
                for ph in 0..v.len() {
                    for &lf in &litfs {
                        for &ab in if bigram { &atbs[..] } else { &[0u8][..] } {
                            inners.push(Inner { cfg: ki as u16, isign: is, ph: ph as u8, litf: lf, atb: ab, kk: kk.clone() });
                        }
                    }
                }
            }
        }
    }
    let wins: Vec<&Win> = all_wins.iter().filter(|w| w.runes.len() >= minlen).collect();
    let wn: Vec<usize> = wins.iter().map(|w| w.runes.len().min(n_req)).collect();
    let nmax = *wn.iter().max().expect("no windows");
    assert!(!periodic || nmax <= 500, "mode=periodic keeps u8 column counts: n <= 500");
    let need = nmax + nmax / 4 + 8;
    let items: Vec<usize> = if let Some(name) = o.get("only") {
        vec![find_item(&fam, name)]
    } else if let Some(r) = o.get("items") {
        let (a, b) = r.split_once(':').expect("items=a:b");
        (a.parse::<usize>().unwrap()..b.parse::<usize>().unwrap().min(fam.len())).collect()
    } else {
        (0..fam.len()).collect()
    };
    // offs=a:b restricts the start offsets (controls); default every offset
    let (olo, ohi): (usize, usize) = o.get("offs").map_or((0, usize::MAX), |r| {
        let (a, b) = r.split_once(':').expect("offs=a:b");
        (a.parse().unwrap(), b.parse().unwrap())
    });
    let orange = |it: usize| (olo.min((fam[it].v.len() + 1).saturating_sub(need)), ohi.min((fam[it].v.len() + 1).saturating_sub(need)));
    let per_off = (mults.len() * models.len() * inners.len() * wins.len()) as u64;
    let total_runs: u64 = items.iter().map(|&it| { let (a, b) = orange(it); (b - a) as u64 }).sum::<u64>() * per_off;
    // work units of up to CHUNK offsets of one item, so that a single-item screen still uses every thread
    const CHUNK: usize = 128;
    let units: Vec<(usize, usize, usize)> = items
        .iter()
        .flat_map(|&it| {
            let (a0, b0) = orange(it);
            (a0..b0).step_by(CHUNK).map(move |a| (it, a, (a + CHUNK).min(b0)))
        })
        .collect();
    eprintln!(
        "layer2: mode {mode}, {} items, {} windows (n<={nmax}), {} inner configs, mults {:?}, models {:?}, {} decodes, {threads} threads",
        items.len(),
        wins.len(),
        inners.len(),
        mults,
        models,
        total_runs
    );
    // histogram bins: known IoC 0.01 over [0, 4); periodic z 0.1 over [-10, 30); bigram per-rune score 0.2 over [-40, 40)
    let (hlo, hw): (f32, f32) = if periodic { (-10.0, 0.1) } else if bigram { (-40.0, 0.2) } else { (0.0, 0.01) };
    let hist_bin = move |x: f32| -> usize { (((x - hlo) / hw).max(0.0) as usize).min(HBINS - 1) };
    let t0 = Instant::now();
    let next = AtomicUsize::new(0);
    let done_runs = AtomicUsize::new(0);
    let merged: Mutex<(Vec<Hit>, Vec<u64>, Vec<Hit>, u64, u64)> =
        Mutex::new((Vec::new(), vec![0u64; HBINS], vec![NOHIT; wins.len()], 0, 0));
    std::thread::scope(|sc| {
        for tid in 0..threads {
            let (fam, units, wins, wn, mults, models, inners, hist_bin, tbl) =
                (&fam, &units, &wins, &wn, &mults, &models, &inners, &hist_bin, &tbl);
            let (next, done_runs, merged) = (&next, &done_runs, &merged);
            sc.spawn(move || {
                let tb = tables();
                let (mut kc, mut ke): (Vec<KSt>, Vec<KSt>) = (Vec::with_capacity(64), Vec::with_capacity(64));
                let (mut pc, mut pe): (Vec<PSt>, Vec<PSt>) = (Vec::with_capacity(64), Vec::with_capacity(64));
                let (mut bc, mut be): (Vec<BSt>, Vec<BSt>) = (Vec::with_capacity(64), Vec::with_capacity(64));

                let mut mk = vec![0u8; need];
                let mut hits: Vec<Hit> = Vec::new();
                let mut thr = f32::MIN;
                let mut hist = vec![0u64; HBINS];
                let mut wbest = vec![NOHIT; wins.len()];
                let (mut runs, mut aborted) = (0u64, 0u64);
                let mut last = Instant::now();
                loop {
                    let k = next.fetch_add(1, Ordering::Relaxed);
                    if k >= units.len() {
                        break;
                    }
                    let (item, o0, o1) = units[k];
                    let nof = o1 - o0;
                    for off in o0..o1 {
                        let key = &fam[item].v[off..off + need];
                        for &mult in mults.iter() {
                            for (a, b) in mk.iter_mut().zip(key.iter()) {
                                *a = ((*b as usize * mult as usize) % Q) as u8;
                            }
                            for &model in models.iter() {
                                for inn in inners.iter() {
                                    for (wi, w) in wins.iter().enumerate() {
                                        let n = wn[wi];
                                        let ab = if abort_at > 0 && abort_at < n { abort_at } else { 0 };
                                        let (score, used) = if periodic {
                                            decode_periodic(&w.runes, &w.pv, &mk, inn.cfg as usize, inn.litf == 1, model, n, beam, ab,
                                                abort_score as f32, &tb, &mut pc, &mut pe)
                                        } else if bigram {
                                            let (t, used) = decode_known_bg(&w.runes, &w.pv, &mk, &inn.kk, inn.ph as usize, inn.litf == 1,
                                                inn.atb == 1, model, n, beam, ab, abort_total, &tb, tbl, &mut bc, &mut be);
                                            (t as f32 / used as f32, used)
                                        } else {
                                            let (s, used) = decode_known(&w.runes, &w.pv, &mk, &inn.kk, inn.ph as usize, inn.litf == 1,
                                                model, n, beam, ab, abort_s, &tb, &mut kc, &mut ke);
                                            let sc = if used < 2 { 0.0 } else { Q as f32 * s as f32 / (used as f32 * (used as f32 - 1.0)) };
                                            (sc, used)
                                        };
                                        runs += 1;
                                        if used < n {
                                            aborted += 1;
                                        }
                                        hist[hist_bin(score)] += 1;
                                        let h = Hit { score, item: item as u32, off: off as u32, mult, model, win: wi as u16, n: used as u16,
                                            cfg: inn.cfg, isign: inn.isign, ph: inn.ph, litf: inn.litf, atb: inn.atb };
                                        if used == n && score > wbest[wi].score {
                                            wbest[wi] = h;
                                        }
                                        if used == n && score > thr {
                                            hits.push(h);
                                            if hits.len() >= 2 * top {
                                                keep_top(&mut hits, top);
                                                thr = hits[top - 1].score;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                    let per_item = nof * (per_off as usize);
                    let d = done_runs.fetch_add(per_item, Ordering::Relaxed) + per_item;
                    if tid == 0 && last.elapsed().as_secs() >= 20 {
                        last = Instant::now();
                        let el = t0.elapsed().as_secs_f64();
                        let frac = d as f64 / total_runs.max(1) as f64;
                        eprintln!("{:6.2}% ({} decodes) {:.0} decodes/s, eta {:.0} s", 100.0 * frac, d, d as f64 / el,
                            el * (1.0 - frac) / frac.max(1e-9));
                    }
                }
                keep_top(&mut hits, top);
                let mut g = merged.lock().unwrap();
                g.0.extend(hits);
                for (a, b) in g.1.iter_mut().zip(hist.iter()) {
                    *a += b;
                }
                for (a, b) in g.2.iter_mut().zip(wbest.iter()) {
                    if b.score > a.score {
                        *a = *b;
                    }
                }
                g.3 += runs;
                g.4 += aborted;
            });
        }
    });
    let (mut hits, hist, wbest, runs, aborted) = merged.into_inner().unwrap();
    keep_top(&mut hits, top);
    let secs = t0.elapsed().as_secs_f64();
    let cfg_name = |h: &Hit| -> String {
        if periodic {
            format!("m={} litf={}", h.cfg, h.litf)
        } else if bigram {
            format!("kw={} isign={} phase={} litf={} atb={}", kwnames[h.cfg as usize], h.isign, h.ph, h.litf, h.atb)
        } else {
            format!("kw={} isign={} phase={} litf={}", kwnames[h.cfg as usize], h.isign, h.ph, h.litf)
        }
    };
    let mut f = BufWriter::new(fs::File::create(out_path).unwrap_or_else(|e| panic!("{out_path}: {e}")));
    writeln!(f, "# layer2 screen mode={mode} family={} windows={} kw={} n={nmax} beam={beam} mults={} models={} litf={} abort={abort_spec} runs={runs} aborted={aborted} secs={secs:.0}",
        args[1], args[0], o.get("kw").map_or("-", |s| s.as_str()), join(&mults), join(&models), join(&litfs)).unwrap();
    writeln!(f, "# best {:.4}", hits.first().map(|h| h.score).unwrap_or(f32::MIN)).unwrap();
    for (wi, h) in wbest.iter().enumerate() {
        writeln!(f, "# window {} best {:.4} item={} offset={} mult={} model={} {}", wins[wi].name, h.score,
            if h.score > f32::MIN { fam[h.item as usize].name.clone() } else { "-".into() }, h.off, h.mult, h.model, cfg_name(h)).unwrap();
    }
    let hs: Vec<String> =
        hist.iter().enumerate().filter(|(_, c)| **c > 0).map(|(b, c)| format!("{:.2}:{}", hlo + hw * b as f32, c)).collect();
    writeln!(f, "# hist {}", hs.join(" ")).unwrap();
    writeln!(f, "score\titem\toffset\tmult\tmodel\twindow\tn\tinner").unwrap();
    for h in &hits {
        writeln!(f, "{:.4}\t{}\t{}\t{}\t{}\t{}\t{}\t{}", h.score, fam[h.item as usize].name, h.off, h.mult, h.model,
            wins[h.win as usize].name, h.n, cfg_name(h)).unwrap();
    }
    eprintln!("layer2: {runs} decodes ({aborted} aborted early) in {secs:.0} s; best {:.4}; wrote {out_path}",
        hits.first().map(|h| h.score).unwrap_or(0.0));
}

// ------------------------------------------------------------------ plant

fn mode_plant(args: &[String]) {
    if args.len() < 14 {
        eprintln!("usage: plant <plain_windows.txt> <family> <item> <offset> <mult> <model> <keep> <seed> <kw a,b,..> <phase> <isign> <litf> <atb> <out.txt>");
        std::process::exit(2);
    }
    let wins = load_windows(&args[0]);
    let fam = family(&args[1]);
    let item = find_item(&fam, &args[2]);
    let off0: usize = args[3].parse().expect("offset");
    let mult: usize = args[4].parse().expect("mult");
    let model: u8 = args[5].parse().expect("model");
    let keep: f64 = args[6].parse().expect("keep");
    let mut rng = Rng(args[7].parse::<u64>().expect("seed") ^ 0x0123_4567_89AB_CDEF);
    let kw = list_u8(&args[8]);
    let ph0: usize = args[9].parse().expect("phase");
    let isign: usize = args[10].parse().expect("isign");
    let litf = args[11] == "1";
    let atb = args[12] == "1"; // plaintext alphabet of the inner layer: Atbash (the literal F stays F)
    let m = kw.len();
    let mut out = String::new();
    for (wi, w) in wins.iter().enumerate() {
        let len = w.runes.len() * 4 + 64;
        let noff = (fam[item].v.len() + 1).saturating_sub(len);
        assert!(noff > 0, "keystream too short to plant");
        let off = (off0 + 997 * wi) % noff;
        let mk: Vec<usize> = fam[item].v[off..off + len].iter().map(|&k| k as usize * mult % Q).collect();
        let (mut j, mut ph, mut prev, mut c) = (0usize, ph0 % m, -1i32, Vec::with_capacity(w.runes.len()));
        for &p in &w.runes {
            let q = if litf && p == 0 {
                0
            } else {
                let x = if atb { Q - 1 - p as usize } else { p as usize };
                let q = (x + isign * kw[ph] as usize) % Q;
                ph = (ph + 1) % m;
                q
            };
            let mut y = ((q + mk[j]) % Q) as i32;
            j += 1;
            if model == 0 {
                let mut tries = 0;
                while prev >= 0 && y == prev && rng.unit() >= keep && tries < 5 {
                    y = ((q + mk[j]) % Q) as i32;
                    j += 1;
                    tries += 1;
                }
            } else if prev >= 0 && y == prev {
                j += 1;
                if rng.unit() >= keep {
                    y = ((q + mk[j]) % Q) as i32;
                    j += 1;
                }
            }
            c.push(y as u8);
            prev = y;
        }
        out += &format!(
            "# truth plant_{wi} item={} offset={off} mult={mult} model={model} keep={keep} kw={} phase={ph0} isign={isign} litf={} atb={}\nW plant_{wi} -1\nR {}\nL {}\n",
            fam[item].name,
            join(&kw),
            litf as u8,
            atb as u8,
            c.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "),
            w.lens
        );
    }
    fs::write(&args[13], out).unwrap_or_else(|e| panic!("{}: {e}", args[13]));
}

// ------------------------------------------------------------------ verify (slow decoder that keeps the plaintext)

/// verification state: counts kept incrementally; the decoded path is kept in an arena (traceback at the end)
#[derive(Clone)]
struct VSt {
    j: usize,
    ph: usize,
    node: u32,
    s: u64,
    d: u64,
    n: u64,
    cnt: Vec<u32>,  // periodic: m x 29 (column, symbol); known: 29
    ncol: Vec<u32>, // periodic: letters per column
}

struct Node {
    parent: u32,
    sym: u8, // known: decoded letter; periodic: q, or 255 for a literal F
    ptr: u32,
}

const NONE: u32 = u32::MAX;

impl VSt {
    /// periodic: the column z-score of the screen; known: IoC of the decoded letters
    fn score(&self, periodic: bool) -> f64 {
        if periodic {
            if self.d == 0 { 0.0 } else { (Q as f64 * self.s as f64 - self.d as f64) / (56.0 * self.d as f64).sqrt() }
        } else if self.n < 2 {
            0.0
        } else {
            Q as f64 * self.s as f64 / (self.n * (self.n - 1)) as f64
        }
    }
    fn ioc(&self, periodic: bool) -> f64 {
        let d = if periodic { self.d } else { self.n * self.n.saturating_sub(1) };
        if d == 0 { 0.0 } else { Q as f64 * self.s as f64 / d as f64 }
    }
    fn count(&mut self, col: usize, x: usize, periodic: bool) {
        let k = if periodic { col * Q + x } else { x };
        self.s += 2 * self.cnt[k] as u64;
        self.cnt[k] += 1;
        if periodic {
            self.d += 2 * self.ncol[col] as u64;
            self.ncol[col] += 1;
        }
        self.n += 1;
    }
}

/// Full decode for verification (no abort): returns (score, decoded symbols, pointer after each rune).
#[allow(clippy::too_many_arguments)]
fn full_decode(c: &[u8], pvs: &[i32], mk: &[u8], kk: &[u8], m: usize, ph0: usize, litf: bool, periodic: bool, model: u8,
    n: usize, beam: usize) -> (f64, f64, Vec<u8>, Vec<u32>) {
    let tb = tables();
    let cells = if periodic { m * Q } else { Q };
    let mut arena: Vec<Node> = Vec::with_capacity(n * beam * 2);
    let mut cur = vec![VSt { j: 0, ph: ph0, node: NONE, s: 0, d: 0, n: 0, cnt: vec![0; cells], ncol: vec![0; m] }];
    let mut cand = [(0u8, 0u32); 3];
    for i in 0..n {
        let mut next: Vec<(f64, VSt)> = Vec::new();
        for st in &cur {
            if st.j + 3 > mk.len() {
                continue;
            }
            let nc = outer_cands(c[i] as usize, pvs[i], mk, st.j, model, &tb, &mut cand);
            for &(q, nj) in &cand[..nc] {
                let mut a = st.clone();
                let sym = if periodic { q } else { tb.sub[q as usize][kk[a.ph] as usize] };
                a.count(a.ph, sym as usize, periodic);
                a.ph = (a.ph + 1) % m;
                a.j = nj as usize;
                arena.push(Node { parent: st.node, sym, ptr: nj });
                a.node = (arena.len() - 1) as u32;
                next.push((a.score(periodic), a));
                if litf && q == 0 {
                    let mut b = st.clone();
                    if !periodic {
                        b.count(0, 0, false); // the literal F is a plaintext letter (F); the phase does not advance
                    }
                    b.j = nj as usize;
                    arena.push(Node { parent: st.node, sym: if periodic { 255 } else { 0 }, ptr: nj });
                    b.node = (arena.len() - 1) as u32;
                    next.push((b.score(periodic), b));
                }
            }
        }
        next.sort_by(|a, b| (a.1.j, a.1.ph).cmp(&(b.1.j, b.1.ph)).then(b.0.partial_cmp(&a.0).unwrap()));
        next.dedup_by(|b, a| a.1.j == b.1.j && a.1.ph == b.1.ph);
        next.sort_by(|a, b| b.0.partial_cmp(&a.0).unwrap());
        next.truncate(beam);
        if next.is_empty() {
            break;
        }
        cur = next.into_iter().map(|x| x.1).collect();
    }
    let best = cur.iter().max_by(|a, b| a.score(periodic).partial_cmp(&b.score(periodic)).unwrap()).unwrap();
    let (mut syms, mut ptrs) = (Vec::new(), Vec::new());
    let mut k = best.node;
    while k != NONE {
        syms.push(arena[k as usize].sym);
        ptrs.push(arena[k as usize].ptr);
        k = arena[k as usize].parent;
    }
    syms.reverse();
    ptrs.reverse();
    (best.score(periodic), best.ioc(periodic), syms, ptrs)
}

/// Full decode for verification in mode=bigram: returns (score per rune, decoded letters, pointer after each rune).
#[allow(clippy::too_many_arguments)]
fn full_decode_bg(c: &[u8], pvs: &[i32], mk: &[u8], kk: &[u8], ph0: usize, litf: bool, atb: bool, model: u8, n: usize,
    beam: usize, tbl: &[[i16; Q]]) -> (f64, Vec<u8>, Vec<u32>) {
    #[derive(Clone, Copy)]
    struct S {
        j: usize,
        ph: usize,
        last: u8,
        s: i64,
        node: u32,
    }
    let tb = tables();
    let m = kk.len();
    let mut arena: Vec<Node> = Vec::with_capacity(n * beam * 2);
    let mut cur = vec![S { j: 0, ph: ph0, last: Q as u8, s: 0, node: NONE }];
    let mut cand = [(0u8, 0u32); 3];
    for i in 0..n {
        let mut next: Vec<S> = Vec::new();
        for st in &cur {
            if st.j + 3 > mk.len() {
                continue;
            }
            let nc = outer_cands(c[i] as usize, pvs[i], mk, st.j, model, &tb, &mut cand);
            for &(q, nj) in &cand[..nc] {
                let x = tb.sub[q as usize][kk[st.ph] as usize] as usize;
                let p = if atb { Q - 1 - x } else { x };
                arena.push(Node { parent: st.node, sym: p as u8, ptr: nj });
                next.push(S { j: nj as usize, ph: (st.ph + 1) % m, last: p as u8, s: st.s + tbl[st.last as usize][p] as i64,
                    node: (arena.len() - 1) as u32 });
                if litf && q == 0 {
                    arena.push(Node { parent: st.node, sym: 0, ptr: nj });
                    next.push(S { j: nj as usize, ph: st.ph, last: 0, s: st.s + tbl[st.last as usize][0] as i64,
                        node: (arena.len() - 1) as u32 });
                }
            }
        }
        next.sort_by(|a, b| (a.j, a.ph).cmp(&(b.j, b.ph)).then(b.s.cmp(&a.s)));
        next.dedup_by(|b, a| a.j == b.j && a.ph == b.ph);
        next.sort_by(|a, b| b.s.cmp(&a.s));
        next.truncate(beam);
        if next.is_empty() {
            break;
        }
        cur = next;
    }
    let best = cur.iter().max_by_key(|x| x.s).unwrap();
    let (mut syms, mut ptrs) = (Vec::new(), Vec::new());
    let mut k = best.node;
    while k != NONE {
        syms.push(arena[k as usize].sym);
        ptrs.push(arena[k as usize].ptr);
        k = arena[k as usize].parent;
    }
    syms.reverse();
    ptrs.reverse();
    (best.s as f64 / syms.len().max(1) as f64, syms, ptrs)
}

const LATIN: [&str; Q] = ["F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B", "E", "M", "L",
    "NG", "OE", "D", "A", "AE", "Y", "IA", "EA"];

fn mode_verify(args: &[String]) {
    if args.len() < 7 {
        eprintln!("usage: verify <windows.txt> <family> <item> <offset> <mult> <model> <window|all> [options]");
        std::process::exit(2);
    }
    let wins = load_windows(&args[0]);
    let fam = family(&args[1]);
    let item = find_item(&fam, &args[2]);
    let off: usize = args[3].parse().expect("offset");
    let mult: usize = args[4].parse().expect("mult");
    let model: u8 = args[5].parse().expect("model");
    let o = opts(&args[7..]);
    let vmode = get(&o, "mode", "periodic".to_string());
    let periodic = vmode == "periodic";
    let bigram = vmode == "bigram";
    let atb = get(&o, "atb", 0u8) == 1;
    let tbl = if bigram { load_bigram(&get(&o, "bg", "../phpmt/data/bigram.txt".to_string())) } else { Vec::new() };
    let n_req: usize = get(&o, "n", 0);
    let beam: usize = get(&o, "beam", 64);
    let litf = get(&o, "litf", 0u8) == 1;
    let (kk, m, ph0) = if periodic {
        (Vec::new(), get(&o, "m", 8usize), 0usize)
    } else {
        let v = list_u8(&get(&o, "kwvals", String::new()));
        let is: usize = get(&o, "isign", 1usize);
        let kk: Vec<u8> = v.iter().map(|&x| (x as usize * is % Q) as u8).collect();
        let m = kk.len();
        (kk, m, get(&o, "phase", 0usize))
    };
    for w in wins.iter().filter(|w| args[6] == "all" || w.name == args[6]) {
        let mut n = if n_req == 0 { w.runes.len() } else { n_req.min(w.runes.len()) };
        // a hit near the end of a stream: decode as much of the window as the stream allows (reported as `n`)
        let avail = fam[item].v.len().saturating_sub(off + 16) * 4 / 5;
        if avail < n {
            n = avail;
        }
        if n < 50 {
            println!("window {} skipped: keystream too short for offset {off}", w.name);
            continue;
        }
        let len = n + n / 4 + 16;
        let noff = (fam[item].v.len() + 1).saturating_sub(len);
        let mk: Vec<u8> = fam[item].v[off..off + len].iter().map(|&k| (k as usize * mult % Q) as u8).collect();
        let decode = |mk: &[u8]| -> (f64, f64, Vec<u8>, Vec<u32>) {
            if bigram {
                let (sc, syms, ptrs) = full_decode_bg(&w.runes, &w.pv, mk, &kk, ph0, litf, atb, model, n, beam, &tbl);
                let mut cnt = [0u64; Q];
                for &x in &syms {
                    cnt[x as usize] += 1;
                }
                let nn = syms.len() as f64;
                let ioc = Q as f64 * cnt.iter().map(|&c| c * c.saturating_sub(1)).sum::<u64>() as f64 / (nn * (nn - 1.0)).max(1.0);
                (sc, ioc, syms, ptrs)
            } else {
                full_decode(&w.runes, &w.pv, mk, &kk, m, ph0, litf, periodic, model, n, beam)
            }
        };
        let (score, ioc, syms, ptrs) = decode(&mk);
        let jumps = ptrs.windows(2).filter(|p| p[1] != p[0] + 1).count();
        println!("window {} n {} score {:.4} ioc {:.4} pointer_jumps {}", w.name, syms.len(), score, ioc, jumps);
        if bigram {
            println!("text {}", syms.iter().map(|&x| LATIN[x as usize]).collect::<Vec<_>>().join(""));
        }
        println!("plain {}", join(&syms.iter().map(|&x| if x == 255 { -1 } else { x as i32 }).collect::<Vec<_>>()));
        let nctl: usize = get(&o, "controls", 0);
        if nctl > 0 {
            let mut rng = Rng(0xC0FFEE ^ off as u64);
            let mut vals = Vec::with_capacity(nctl);
            for _ in 0..nctl {
                // a matched null must not sample the candidate's own neighbourhood: an offset 1 or 2 away decodes most of
                // a true key's text (the beam realigns through a re-draw), so redraw anything within 50 of it
                let mut co = rng.below(noff as u64) as usize;
                while co.abs_diff(off) <= 50 && noff > 101 {
                    co = rng.below(noff as u64) as usize;
                }
                let cmk: Vec<u8> = fam[item].v[co..co + len].iter().map(|&k| (k as usize * mult % Q) as u8).collect();
                vals.push(decode(&cmk).0);
            }
            let mx = vals.iter().cloned().fold(f64::MIN, f64::max);
            let mean = vals.iter().sum::<f64>() / vals.len() as f64;
            println!("controls {nctl} random offsets: mean {mean:.4} max {mx:.4}");
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("modes: screen | plant | verify  (see the header of src/main.rs)");
        std::process::exit(2);
    }
    let rest = &args[2..];
    match args[1].as_str() {
        "screen" => mode_screen(rest),
        "plant" => mode_plant(rest),
        "verify" => mode_verify(rest),
        m => {
            eprintln!("unknown mode {m}");
            std::process::exit(2);
        }
    }
}
