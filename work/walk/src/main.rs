//! Word-scoped mixed-alphabet cipher solver for Liber Primus LP2.
//!
//! Model F1(m):  c[w][j] = D( Q[j mod m](p[w][j]) + k_w )  (mod 29)
//!   D, Q_0..Q_{m-1}: unknown permutations of the 29 runes (freely designed alphabets)
//!   k_w:             unknown shift, one per word
//! With m = 5 this reproduces LP2's within-word distance-5 equality leak (positions j and j+5 of a
//! word share an alphabet) while every word gets a fresh alphabet offset (flat statistics).
//!
//! Fitness = sum over words of max_k log P(decrypted word), using an English rune trigram model
//! with word boundaries (token 29). The per-word key never has to be searched explicitly.
//!
//! Modes:
//!   synth <plain.txt> <out.txt> <truth.txt> <m> <seed> <keep>
//!       encrypt a plaintext windows file; keep < 1 adds an anti-repeat rule: when a rune would
//!       equal the previous cipher rune, with probability 1-keep the word key is redrawn
//!   truth <cipher.txt> <truth.txt> <lm3.bin>          fitness of the true key (reference)
//!   solve <cipher.txt> <lm3.bin> <m> <iters> <restarts> <threads> <out_prefix> [plain.txt]
//!       multi-start simulated annealing; with plain.txt, reports rune accuracy of the best key

use std::env;
use std::fs;
use std::io::Write;
use std::sync::{Arc, Mutex};
use std::time::Instant;

mod dsearch;

const N: usize = 29;
const BND: usize = 29;

// ------------------------------------------------------------------ utils

struct Rng(u64);

impl Rng {
    fn new(seed: u64) -> Rng {
        Rng(seed.wrapping_mul(0x9E3779B97F4A7C15) | 1)
    }
    fn next(&mut self) -> u64 {
        let mut x = self.0;
        x ^= x >> 12;
        x ^= x << 25;
        x ^= x >> 27;
        self.0 = x;
        x.wrapping_mul(0x2545F4914F6CDD1D)
    }
    fn below(&mut self, n: usize) -> usize {
        (self.next() % n as u64) as usize
    }
    fn unit(&mut self) -> f64 {
        (self.next() >> 11) as f64 / (1u64 << 53) as f64
    }
}

type Perm = [u8; N];

fn rand_perm(rng: &mut Rng) -> Perm {
    let mut p = [0u8; N];
    for i in 0..N {
        p[i] = i as u8;
    }
    for i in (1..N).rev() {
        let j = rng.below(i + 1);
        p.swap(i, j);
    }
    p
}

fn inverse(p: &Perm) -> Perm {
    let mut q = [0u8; N];
    for i in 0..N {
        q[p[i] as usize] = i as u8;
    }
    q
}

const LATIN: [&str; 29] = ["F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B",
    "E", "M", "L", "ING", "OE", "D", "A", "AE", "Y", "IA", "EA"];

// ------------------------------------------------------------------ data

struct Text {
    runes: Vec<u8>,
    starts: Vec<usize>,
    lens: Vec<usize>,
}

fn load_text(path: &str) -> Text {
    let txt = fs::read_to_string(path).expect("text file");
    let mut runes = Vec::new();
    let mut starts = Vec::new();
    let mut lens = Vec::new();
    let mut lines = txt.lines();
    while let Some(h) = lines.next() {
        if !h.starts_with("W ") {
            continue;
        }
        let r: Vec<u8> = lines.next().unwrap()[2..].split_whitespace().map(|x| x.parse().unwrap()).collect();
        let l: Vec<usize> = lines.next().unwrap()[2..].split_whitespace().map(|x| x.parse().unwrap()).collect();
        let base = runes.len();
        let mut pos = 0;
        for len in l {
            starts.push(base + pos);
            lens.push(len);
            pos += len;
        }
        assert_eq!(pos, r.len());
        runes.extend(r);
    }
    Text { runes, starts, lens }
}

fn write_text(path: &str, name: &str, runes: &[u8], lens: &[usize]) {
    let r: Vec<String> = runes.iter().map(|x| x.to_string()).collect();
    let l: Vec<String> = lens.iter().map(|x| x.to_string()).collect();
    fs::write(path, format!("W {} -1\nR {}\nL {}\n", name, r.join(" "), l.join(" "))).unwrap();
}

struct Lm(Vec<f32>);

fn load_lm(path: &str) -> Lm {
    let b = fs::read(path).expect("lm file");
    assert_eq!(b.len(), 30 * 30 * 30 * 4);
    Lm(b.chunks(4).map(|c| f32::from_le_bytes([c[0], c[1], c[2], c[3]])).collect())
}

#[inline]
fn li(a: usize, b: usize, c: usize) -> usize {
    (a * 30 + b) * 30 + c
}

// ------------------------------------------------------------------ model and fitness

#[derive(Clone)]
struct Model {
    m: usize,
    d: Perm,
    q: Vec<Perm>,
}

impl Model {
    fn random(m: usize, rng: &mut Rng) -> Model {
        Model { m, d: rand_perm(rng), q: (0..m).map(|_| rand_perm(rng)).collect() }
    }
}

struct Scratch {
    xs: Vec<u8>,
    sub: Vec<u8>, // sub[x*29 + k] = (x - k) mod 29
}

impl Scratch {
    fn new(n: usize) -> Scratch {
        let mut sub = vec![0u8; N * N];
        for x in 0..N {
            for k in 0..N {
                sub[x * N + k] = ((x + N - k) % N) as u8;
            }
        }
        Scratch { xs: vec![0; n], sub }
    }
}

/// Sum over words of max_k log P(word decrypted with k). Optionally records best k per word.
fn fitness(t: &Text, lm: &Lm, md: &Model, sc: &mut Scratch, mut best_k: Option<&mut Vec<u8>>) -> f64 {
    let dinv = inverse(&md.d);
    let qinv: Vec<Perm> = md.q.iter().map(inverse).collect();
    for (x, &c) in sc.xs.iter_mut().zip(t.runes.iter()) {
        *x = dinv[c as usize];
    }
    let m = md.m;
    let lmv = &lm.0;
    let mut total = 0f64;
    for w in 0..t.lens.len() {
        let s = t.starts[w];
        let l = t.lens[w];
        let mut best = f32::NEG_INFINITY;
        let mut bk = 0u8;
        for k in 0..N {
            let (mut a, mut b) = (BND, BND);
            let mut score = 0f32;
            let mut ph = 0usize;
            for j in 0..l {
                let y = sc.sub[sc.xs[s + j] as usize * N + k] as usize;
                let p = qinv[ph][y] as usize;
                score += lmv[li(a, b, p)];
                a = b;
                b = p;
                ph += 1;
                if ph == m {
                    ph = 0;
                }
            }
            score += lmv[li(a, b, BND)];
            if score > best {
                best = score;
                bk = k as u8;
            }
        }
        total += best as f64;
        if let Some(v) = best_k.as_deref_mut() {
            v[w] = bk;
        }
    }
    total
}

fn decrypt(t: &Text, md: &Model, ks: &[u8]) -> Vec<u8> {
    let dinv = inverse(&md.d);
    let qinv: Vec<Perm> = md.q.iter().map(inverse).collect();
    let mut out = vec![0u8; t.runes.len()];
    for w in 0..t.lens.len() {
        for j in 0..t.lens[w] {
            let i = t.starts[w] + j;
            let y = (dinv[t.runes[i] as usize] as usize + N - ks[w] as usize) % N;
            out[i] = qinv[j % md.m][y];
        }
    }
    out
}

fn latin(t: &Text, plain: &[u8], max_words: usize) -> String {
    let mut s = String::new();
    for w in 0..t.lens.len().min(max_words) {
        for j in 0..t.lens[w] {
            s += LATIN[plain[t.starts[w] + j] as usize];
        }
        s.push(' ');
    }
    s
}

// ------------------------------------------------------------------ annealing (incremental)

/// Index structures shared by all restarts.
struct Index {
    word_of: Vec<u32>,
    pos_by_phase: Vec<Vec<u32>>,  // positions with phase j
    pos_by_cipher: Vec<Vec<u32>>, // positions with cipher rune c
}

impl Index {
    fn new(t: &Text, m: usize) -> Index {
        let mut word_of = vec![0u32; t.runes.len()];
        let mut pos_by_phase = vec![Vec::new(); m];
        let mut pos_by_cipher = vec![Vec::new(); N];
        for w in 0..t.lens.len() {
            for j in 0..t.lens[w] {
                let i = t.starts[w] + j;
                word_of[i] = w as u32;
                pos_by_phase[j % m].push(i as u32);
                pos_by_cipher[t.runes[i] as usize].push(i as u32);
            }
        }
        Index { word_of, pos_by_phase, pos_by_cipher }
    }
}

struct State {
    md: Model,
    dinv: Perm,
    qinv: Vec<Perm>,
    xs: Vec<u8>,
    wk: Vec<f32>,   // score of word w under key k at [w*29+k]
    best: Vec<f32>, // max over k per word
    total: f64,
}

#[inline]
fn word_score(t: &Text, lm: &[f32], xs: &[u8], qinv: &[Perm], m: usize, w: usize, k: usize) -> f32 {
    let s = t.starts[w];
    let (mut a, mut b) = (BND, BND);
    let mut score = 0f32;
    let mut ph = 0usize;
    for j in 0..t.lens[w] {
        let mut y = xs[s + j] as usize + N - k;
        if y >= N {
            y -= N;
        }
        let p = qinv[ph][y] as usize;
        score += lm[li(a, b, p)];
        a = b;
        b = p;
        ph += 1;
        if ph == m {
            ph = 0;
        }
    }
    score + lm[li(a, b, BND)]
}

impl State {
    fn new(t: &Text, lm: &Lm, md: Model) -> State {
        let dinv = inverse(&md.d);
        let qinv: Vec<Perm> = md.q.iter().map(inverse).collect();
        let xs: Vec<u8> = t.runes.iter().map(|&c| dinv[c as usize]).collect();
        let nw = t.lens.len();
        let mut wk = vec![0f32; nw * N];
        let mut best = vec![f32::NEG_INFINITY; nw];
        let mut total = 0f64;
        for w in 0..nw {
            for k in 0..N {
                let s = word_score(t, &lm.0, &xs, &qinv, md.m, w, k);
                wk[w * N + k] = s;
                if s > best[w] {
                    best[w] = s;
                }
            }
            total += best[w] as f64;
        }
        State { md, dinv, qinv, xs, wk, best, total }
    }
}

/// Scratch buffers for one proposed move.
struct MoveBuf {
    changed: Vec<(u32, u8, f32)>, // (word, k, new score)
    word_mark: Vec<u32>,          // stamp per word
    stamp: u32,
    words: Vec<u32>,
}

/// Propose swapping entries a,b of D (which = None) or of Q_j (which = Some(j)); returns the new total
/// and leaves the state's tables updated tentatively (call commit or revert).
fn propose(t: &Text, lm: &Lm, ix: &Index, st: &mut State, mb: &mut MoveBuf, which: Option<usize>, a: usize, b: usize)
           -> f64 {
    mb.changed.clear();
    mb.words.clear();
    mb.stamp = mb.stamp.wrapping_add(1);
    let m = st.md.m;
    match which {
        None => {
            // D[a] <-> D[b]: cipher runes c1 = D[a], c2 = D[b] swap their preimages
            let (c1, c2) = (st.md.d[a] as usize, st.md.d[b] as usize);
            st.md.d.swap(a, b);
            st.dinv[c1] = b as u8;
            st.dinv[c2] = a as u8;
            for &c in &[c1, c2] {
                for &i in &ix.pos_by_cipher[c] {
                    st.xs[i as usize] = st.dinv[c];
                    let w = ix.word_of[i as usize];
                    if mb.word_mark[w as usize] != mb.stamp {
                        mb.word_mark[w as usize] = mb.stamp;
                        mb.words.push(w);
                    }
                }
            }
            for wi in 0..mb.words.len() {
                let w = mb.words[wi] as usize;
                for k in 0..N {
                    let s = word_score(t, &lm.0, &st.xs, &st.qinv, m, w, k);
                    mb.changed.push((w as u32, k as u8, s));
                }
            }
        }
        Some(j) => {
            // Q_j[a] <-> Q_j[b]: qinv changes at y1 = Q_j[a], y2 = Q_j[b]
            let (y1, y2) = (st.md.q[j][a] as usize, st.md.q[j][b] as usize);
            st.md.q[j].swap(a, b);
            st.qinv[j][y1] = b as u8;
            st.qinv[j][y2] = a as u8;
            // affected (w, k): a phase-j position i with (xs[i] - k) mod 29 in {y1, y2}
            let mut seen: Vec<(u32, u8)> = Vec::new();
            for &i in &ix.pos_by_phase[j] {
                let x = st.xs[i as usize] as usize;
                let w = ix.word_of[i as usize];
                for &y in &[y1, y2] {
                    let k = (x + N - y) % N;
                    seen.push((w, k as u8));
                }
            }
            seen.sort_unstable();
            seen.dedup();
            for (w, k) in seen {
                let s = word_score(t, &lm.0, &st.xs, &st.qinv, m, w as usize, k as usize);
                mb.changed.push((w, k, s));
                if mb.word_mark[w as usize] != mb.stamp {
                    mb.word_mark[w as usize] = mb.stamp;
                    mb.words.push(w);
                }
            }
        }
    }
    // new total: for every affected word, the max over its row with the changes applied
    let mut total = st.total;
    // group changes by word (changed is grouped by word for D moves; sorted for Q moves)
    let mut idx = 0;
    while idx < mb.changed.len() {
        let w = mb.changed[idx].0 as usize;
        let mut row = [0f32; N];
        row.copy_from_slice(&st.wk[w * N..w * N + N]);
        while idx < mb.changed.len() && mb.changed[idx].0 as usize == w {
            row[mb.changed[idx].1 as usize] = mb.changed[idx].2;
            idx += 1;
        }
        let nb = row.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
        total += (nb - st.best[w]) as f64;
    }
    total
}

fn commit(st: &mut State, mb: &MoveBuf, total: f64) {
    for &(w, k, s) in &mb.changed {
        st.wk[w as usize * N + k as usize] = s;
    }
    for &w in &mb.words {
        let w = w as usize;
        st.best[w] = st.wk[w * N..w * N + N].iter().cloned().fold(f32::NEG_INFINITY, f32::max);
    }
    st.total = total;
}

fn revert(ix: &Index, st: &mut State, which: Option<usize>, a: usize, b: usize) {
    match which {
        None => {
            let (c1, c2) = (st.md.d[a] as usize, st.md.d[b] as usize);
            st.md.d.swap(a, b);
            st.dinv[c1] = b as u8;
            st.dinv[c2] = a as u8;
            for &c in &[c1, c2] {
                for &i in &ix.pos_by_cipher[c] {
                    st.xs[i as usize] = st.dinv[c];
                }
            }
        }
        Some(j) => {
            let (y1, y2) = (st.md.q[j][a] as usize, st.md.q[j][b] as usize);
            st.md.q[j].swap(a, b);
            st.qinv[j][y1] = b as u8;
            st.qinv[j][y2] = a as u8;
        }
    }
}

fn anneal(t: &Text, lm: &Lm, ix: &Index, m: usize, iters: u64, seed: u64, t0: f64, t1: f64) -> (f64, Model) {
    let mut rng = Rng::new(seed);
    let mut st = State::new(t, lm, Model::random(m, &mut rng));
    let mut mb = MoveBuf { changed: Vec::new(), word_mark: vec![0; t.lens.len()], stamp: 0, words: Vec::new() };
    let mut best = st.md.clone();
    let mut best_f = st.total;
    let ratio = (t1 / t0).ln();
    for it in 0..iters {
        let temp = t0 * (ratio * it as f64 / iters as f64).exp();
        let a = rng.below(N);
        let mut b = rng.below(N - 1);
        if b >= a {
            b += 1;
        }
        let which = if rng.below(m + 2) < 2 { None } else { Some(rng.below(m)) };
        let f = propose(t, lm, ix, &mut st, &mut mb, which, a, b);
        let delta = f - st.total;
        if delta >= 0.0 || rng.unit() < (delta / temp).exp() {
            commit(&mut st, &mb, f);
            if st.total > best_f {
                best_f = st.total;
                best = st.md.clone();
            }
        } else {
            revert(ix, &mut st, which, a, b);
        }
    }
    (best_f, best)
}

// ------------------------------------------------------------------ modes

fn mode_synth(a: &[String]) {
    let plain = load_text(&a[0]);
    let m: usize = a[3].parse().unwrap();
    let seed: u64 = a[4].parse().unwrap();
    let keep: f64 = a[5].parse().unwrap();
    let mut rng = Rng::new(seed);
    let md = Model::random(m, &mut rng);
    let mut c = vec![0u8; plain.runes.len()];
    let mut ks = Vec::new();
    let mut prev: i32 = -1;
    let mut redraws = 0;
    for w in 0..plain.lens.len() {
        let mut k = rng.below(N);
        ks.push(k as u8);
        for j in 0..plain.lens[w] {
            let i = plain.starts[w] + j;
            let enc = |k: usize| md.d[(md.q[j % m][plain.runes[i] as usize] as usize + k) % N];
            let mut y = enc(k);
            let mut tries = 0;
            while y as i32 == prev && rng.unit() >= keep && tries < 5 {
                k = rng.below(N);
                y = enc(k);
                tries += 1;
                redraws += 1;
            }
            c[i] = y;
            prev = y as i32;
        }
    }
    write_text(&a[1], "synthetic", &c, &plain.lens);
    let mut tr = format!("m {}\nD {}\n", m, md.d.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
    for q in &md.q {
        tr += &format!("Q {}\n", q.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
    }
    fs::write(&a[2], tr).unwrap();
    let d = c.windows(2).filter(|p| p[0] == p[1]).count();
    println!("synth: {} runes, {} words, m={}, redraws {}, doublets {:.2}%", c.len(), plain.lens.len(), m, redraws,
             100.0 * d as f64 / (c.len() - 1) as f64);
}

fn read_truth(path: &str) -> Model {
    let txt = fs::read_to_string(path).unwrap();
    let mut m = 0;
    let mut d = [0u8; N];
    let mut q = Vec::new();
    for line in txt.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        let to_perm = |f: &[&str]| -> Perm {
            let mut p = [0u8; N];
            for (i, x) in f.iter().enumerate() {
                p[i] = x.parse().unwrap();
            }
            p
        };
        match f[0] {
            "m" => m = f[1].parse().unwrap(),
            "D" => d = to_perm(&f[1..]),
            "Q" => q.push(to_perm(&f[1..])),
            _ => {}
        }
    }
    Model { m, d, q }
}

fn mode_truth(a: &[String]) {
    let t = load_text(&a[0]);
    let md = read_truth(&a[1]);
    let lm = load_lm(&a[2]);
    let mut sc = Scratch::new(t.runes.len());
    let f = fitness(&t, &lm, &md, &mut sc, None);
    println!("true-key fitness {:.1} ({:.4} per rune)", f, f / t.runes.len() as f64);
}

fn mode_solve(a: &[String]) {
    let t = Arc::new(load_text(&a[0]));
    let lm = Arc::new(load_lm(&a[1]));
    let m: usize = a[2].parse().unwrap();
    let iters: u64 = a[3].parse().unwrap();
    let restarts: u64 = a[4].parse().unwrap();
    let threads: usize = a[5].parse().unwrap();
    let prefix = a[6].clone();
    let plain = if a.len() > 7 && a[7] != "-" { Some(load_text(&a[7])) } else { None };
    let t0: f64 = if a.len() > 8 { a[8].parse().unwrap() } else { 25.0 };
    let t1: f64 = if a.len() > 9 { a[9].parse().unwrap() } else { 0.5 };
    let t_start = Instant::now();
    let results: Arc<Mutex<Vec<(f64, u64, Model)>>> = Arc::new(Mutex::new(Vec::new()));
    let next = Arc::new(Mutex::new(0u64));
    let ix = Arc::new(Index::new(&t, m));
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (t, lm, results, next, ix) = (t.clone(), lm.clone(), results.clone(), next.clone(), ix.clone());
        hs.push(std::thread::spawn(move || loop {
            let r = {
                let mut n = next.lock().unwrap();
                if *n >= restarts {
                    break;
                }
                *n += 1;
                *n - 1
            };
            let (f, md) = anneal(&t, &lm, &ix, m, iters, 1000 + r * 7919, t0, t1);
            let mut sc = Scratch::new(t.runes.len());
            let full = fitness(&t, &lm, &md, &mut sc, None);
            eprintln!("restart {:3}: fitness {:.1} ({:.4}/rune; full recompute {:.1})", r, f, f / t.runes.len() as f64, full);
            results.lock().unwrap().push((f, r, md));
        }));
    }
    for h in hs {
        h.join().unwrap();
    }
    let mut res = results.lock().unwrap().clone();
    res.sort_by(|x, y| y.0.partial_cmp(&x.0).unwrap());
    let (bf, br, bm) = res[0].clone();
    let mut sc = Scratch::new(t.runes.len());
    let mut ks = vec![0u8; t.lens.len()];
    fitness(&t, &lm, &bm, &mut sc, Some(&mut ks));
    let p = decrypt(&t, &bm, &ks);
    let mut report = format!("m={} iters={} restarts={} time={:.0}s\nbest restart {} fitness {:.1} ({:.4}/rune)\n",
                             m, iters, restarts, t_start.elapsed().as_secs_f64(), br, bf, bf / t.runes.len() as f64);
    if let Some(pl) = &plain {
        let acc = p.iter().zip(pl.runes.iter()).filter(|(x, y)| x == y).count() as f64 / p.len() as f64;
        report += &format!("rune accuracy vs plaintext: {:.3}\n", acc);
    }
    report += &format!("all restarts (fitness/rune): {}\n",
                       res.iter().map(|r| format!("{:.4}", r.0 / t.runes.len() as f64)).collect::<Vec<_>>().join(" "));
    report += &format!("plaintext (first 60 words): {}\n", latin(&t, &p, 60));
    report += &format!("D {}\n", bm.d.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
    for q in &bm.q {
        report += &format!("Q {}\n", q.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
    }
    print!("{}", report);
    let mut f = fs::File::create(format!("{}_report.txt", prefix)).unwrap();
    f.write_all(report.as_bytes()).unwrap();
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("synth") => mode_synth(&args[2..]),
        Some("truth") => mode_truth(&args[2..]),
        Some("solve") => mode_solve(&args[2..]),
        Some("dsearch") => dsearch::mode_dsearch(&args[2..]),
        Some("surrogate") => dsearch::mode_surrogate(&args[2..]),
        _ => eprintln!("usage: walk synth|truth|solve ..."),
    }
}
