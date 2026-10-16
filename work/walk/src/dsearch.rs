//! Key-free search for the outer alphabet D of a per-word additive key.
//!
//! If c[w][j] = D( y[w][j] + k_w ) with any within-word structure y (e.g. y = Q_{j mod m}(p)), then
//! x = D^{-1}(c) satisfies x[w][j+g] - x[w][j] = y[w][j+g] - y[w][j]: the word key k_w cancels. For the
//! right D these within-word differences follow the plaintext's structure (uneven histogram); for a
//! wrong D they are scrambled (flat). We anneal D to maximise the likelihood-ratio statistic
//! G = sum over histograms of 2 * sum_d n_d ln(n_d / E), with the d = 0 bin excluded (LP2's anti-repeat
//! rule empties it for every D). Histograms are split by gap g and by the pair's start phase j mod m.
//!
//! Modes (from main):
//!   dsearch <cipher.txt> <m> <gaps e.g. 1,2> <iters> <restarts> <threads> [truth.txt]
//!   surrogate <cipher.txt> <out.txt> <seed> <keep>   same word lengths, random runes, anti-repeat keep prob

use super::*;

pub struct Pairs {
    s: Vec<u32>,
    e: Vec<u32>,
    h: Vec<u32>,
    by_pos: Vec<Vec<u32>>,
    nhist: usize,
}

pub fn build_pairs(t: &Text, m: usize, gaps: &[usize]) -> Pairs {
    let mut s = Vec::new();
    let mut e = Vec::new();
    let mut h = Vec::new();
    let mut by_pos = vec![Vec::new(); t.runes.len()];
    for (gi, &g) in gaps.iter().enumerate() {
        for w in 0..t.lens.len() {
            let l = t.lens[w];
            for j in 0..l.saturating_sub(g) {
                let a = t.starts[w] + j;
                let idx = s.len() as u32;
                s.push(a as u32);
                e.push((a + g) as u32);
                h.push((gi * m + j % m) as u32);
                by_pos[a].push(idx);
                by_pos[a + g].push(idx);
            }
        }
    }
    Pairs { s, e, h, by_pos, nhist: gaps.len() * m }
}

fn g_of(hist: &[i32; N]) -> f64 {
    let n: i32 = hist[1..].iter().sum();
    if n == 0 {
        return 0.0;
    }
    let e = n as f64 / (N - 1) as f64;
    let mut g = 0.0;
    for d in 1..N {
        let c = hist[d] as f64;
        if c > 0.0 {
            g += c * (c / e).ln();
        }
    }
    2.0 * g
}

struct DState {
    dinv: Perm,
    x: Vec<u8>,
    hist: Vec<[i32; N]>,
    gs: Vec<f64>,
    total: f64,
}

#[inline]
fn diff(x: &[u8], a: u32, b: u32) -> usize {
    (x[b as usize] as usize + N - x[a as usize] as usize) % N
}

impl DState {
    fn new(t: &Text, pr: &Pairs, dinv: Perm) -> DState {
        let x: Vec<u8> = t.runes.iter().map(|&c| dinv[c as usize]).collect();
        let mut hist = vec![[0i32; N]; pr.nhist];
        for p in 0..pr.s.len() {
            hist[pr.h[p] as usize][diff(&x, pr.s[p], pr.e[p])] += 1;
        }
        let gs: Vec<f64> = hist.iter().map(g_of).collect();
        let total = gs.iter().sum();
        DState { dinv, x, hist, gs, total }
    }
}

struct DBuf {
    mark: Vec<u32>,
    stamp: u32,
    pairs: Vec<u32>,
    hmark: Vec<u32>,
    hs: Vec<u32>,
}

/// Swap the D-preimages of cipher runes c1 and c2; updates everything and returns the new total.
fn dswap(t: &Text, pos_by_cipher: &[Vec<u32>], pr: &Pairs, st: &mut DState, b: &mut DBuf, c1: usize, c2: usize) -> f64 {
    b.stamp = b.stamp.wrapping_add(1);
    b.pairs.clear();
    b.hs.clear();
    for &c in &[c1, c2] {
        for &i in &pos_by_cipher[c] {
            for &p in &pr.by_pos[i as usize] {
                if b.mark[p as usize] != b.stamp {
                    b.mark[p as usize] = b.stamp;
                    b.pairs.push(p);
                }
            }
        }
    }
    for &p in &b.pairs {
        let hh = pr.h[p as usize] as usize;
        st.hist[hh][diff(&st.x, pr.s[p as usize], pr.e[p as usize])] -= 1;
        if b.hmark[hh] != b.stamp {
            b.hmark[hh] = b.stamp;
            b.hs.push(hh as u32);
        }
    }
    st.dinv.swap(c1, c2);
    for &c in &[c1, c2] {
        for &i in &pos_by_cipher[c] {
            st.x[i as usize] = st.dinv[c];
        }
    }
    let _ = t;
    for &p in &b.pairs {
        let hh = pr.h[p as usize] as usize;
        st.hist[hh][diff(&st.x, pr.s[p as usize], pr.e[p as usize])] += 1;
    }
    for &hh in &b.hs {
        let g = g_of(&st.hist[hh as usize]);
        st.total += g - st.gs[hh as usize];
        st.gs[hh as usize] = g;
    }
    st.total
}

pub fn dsearch_anneal(t: &Text, pr: &Pairs, iters: u64, seed: u64, t0: f64, t1: f64) -> (f64, Perm) {
    let mut rng = Rng::new(seed);
    let mut pos_by_cipher = vec![Vec::new(); N];
    for (i, &c) in t.runes.iter().enumerate() {
        pos_by_cipher[c as usize].push(i as u32);
    }
    let mut st = DState::new(t, pr, rand_perm(&mut rng));
    let mut b = DBuf { mark: vec![0; pr.s.len()], stamp: 0, pairs: Vec::new(), hmark: vec![0; pr.nhist], hs: Vec::new() };
    let mut best = st.dinv;
    let mut best_f = st.total;
    let ratio = (t1 / t0).ln();
    for it in 0..iters {
        let temp = t0 * (ratio * it as f64 / iters as f64).exp();
        let c1 = rng.below(N);
        let mut c2 = rng.below(N - 1);
        if c2 >= c1 {
            c2 += 1;
        }
        let old = st.total;
        let f = dswap(t, &pos_by_cipher, pr, &mut st, &mut b, c1, c2);
        let delta = f - old;
        if delta >= 0.0 || rng.unit() < (delta / temp).exp() {
            if f > best_f {
                best_f = f;
                best = st.dinv;
            }
        } else {
            dswap(t, &pos_by_cipher, pr, &mut st, &mut b, c1, c2);
        }
    }
    (best_f, best)
}

/// How many symbols of `found` match `truth` up to an affine map y -> a*y + b (mod 29).
pub fn affine_agreement(found: &Perm, truth: &Perm) -> usize {
    let mut best = 0;
    for a in 1..N {
        for bb in 0..N {
            let n = (0..N).filter(|&c| found[c] as usize == (a * truth[c] as usize + bb) % N).count();
            best = best.max(n);
        }
    }
    best
}

pub fn mode_dsearch(a: &[String]) {
    let t = Arc::new(load_text(&a[0]));
    let m: usize = a[1].parse().unwrap();
    let gaps: Vec<usize> = a[2].split(',').map(|x| x.parse().unwrap()).collect();
    let iters: u64 = a[3].parse().unwrap();
    let restarts: u64 = a[4].parse().unwrap();
    let threads: usize = a[5].parse().unwrap();
    let truth = if a.len() > 6 { Some(inverse(&read_truth(&a[6]).d)) } else { None };
    let pr = Arc::new(build_pairs(&t, m, &gaps));
    let (t0, t1) = (10.0, 0.05);
    let results: Arc<Mutex<Vec<(f64, Perm)>>> = Arc::new(Mutex::new(Vec::new()));
    let next = Arc::new(Mutex::new(0u64));
    let start = Instant::now();
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (t, pr, results, next) = (t.clone(), pr.clone(), results.clone(), next.clone());
        hs.push(std::thread::spawn(move || loop {
            let r = {
                let mut n = next.lock().unwrap();
                if *n >= restarts {
                    break;
                }
                *n += 1;
                *n - 1
            };
            let (f, d) = dsearch_anneal(&t, &pr, iters, 77 + r * 104729, t0, t1);
            results.lock().unwrap().push((f, d));
        }));
    }
    for h in hs {
        h.join().unwrap();
    }
    let mut res = results.lock().unwrap().clone();
    res.sort_by(|x, y| y.0.partial_cmp(&x.0).unwrap());
    let base = DState::new(&t, &pr, {
        let mut r = Rng::new(1);
        rand_perm(&mut r)
    })
    .total;
    print!("dsearch m={} gaps={:?} pairs={} iters={} restarts={} time={:.0}s | random-D G {:.0} | best G {:.0} | all:",
           m, gaps, pr.s.len(), iters, restarts, start.elapsed().as_secs_f64(), base, res[0].0);
    for r in &res {
        print!(" {:.0}", r.0);
    }
    println!();
    if let Some(tr) = truth {
        let tg = DState::new(&t, &pr, tr).total;
        println!("  true-D G {:.0}; best D agrees with truth on {} of 29 symbols (up to affine)", tg,
                 affine_agreement(&res[0].1, &tr));
    }
    println!("  best Dinv {}", res[0].1.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
}

pub fn mode_surrogate(a: &[String]) {
    let t = load_text(&a[0]);
    let seed: u64 = a[2].parse().unwrap();
    let keep: f64 = a[3].parse().unwrap();
    let mut rng = Rng::new(seed);
    let mut c = vec![0u8; t.runes.len()];
    let mut prev: i32 = -1;
    for i in 0..c.len() {
        let mut y = rng.below(N) as i32;
        while y == prev && rng.unit() >= keep {
            y = rng.below(N) as i32;
        }
        c[i] = y as u8;
        prev = y;
    }
    write_text(&a[1], "surrogate", &c, &t.lens);
    let d = c.windows(2).filter(|p| p[0] == p[1]).count();
    println!("surrogate: {} runes, doublets {:.2}%", c.len(), 100.0 * d as f64 / (c.len() - 1) as f64);
}
