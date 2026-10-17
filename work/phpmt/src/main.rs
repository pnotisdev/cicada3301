//! PHP legacy mt_rand (MT_RAND_PHP, i.e. PHP < 7.1) keystream sweep over Liber Primus LP2.
//!
//! Modes:
//!   vectors <vectors.txt>                         bit-exact check against real PHP output
//!   plant <plain.txt> <seed> <map> <model> <sign> <atb> <keep> <out.txt>
//!                                                 encrypt synthetic plaintext with a known seed
//!   sweep <windows.txt> <dict.txt> <lo> <hi> <out.tsv> [threads]
//!                                                 score every seed in [lo, hi) (hi exclusive, u64)
//!   verify <windows.txt> <dict.txt> <seed> <window> <map> <model> <sign> <atb>
//!                                                 full-length decode of one candidate
//!   raw    <gen> <lo> <hi> <out.txt>               the first K raw generator outputs of every seed (php/glibc/net)
//!   keys   <gen> <lo> <hi> <out.txt> [km]          the first K key values of both maps of every seed (every generator);
//!                                                 km = 28 reduces to the 28 step classes instead of 29 (default 29)
//!   keysn  <gen> <lo> <hi> <out.txt> <km> <count>   <count> key values of both maps of every seed under the alphabet size km
//!   scores <gen> <windows.txt> <dict.txt> <lo> <hi> <out.txt>
//!                                                 the sweep score of every (seed, window, variant), one line each
//!                                                 (the reference gpu.py is compared with decode by decode)
//!
//! map: 0 = mt_rand(0,28) (PHP 5 RAND_RANGE scaling), 1 = mt_rand() % 29
//! model: 0 = skip (on a collision the next key value is drawn; a missed check keeps the doublet)
//!        1 = coin (on a collision one value is drawn as a coin; keep, or draw a fresh key value)
//! sign: +1 means c = t + k, -1 means c = t - k;  atb: 1 means t = 28 - p (Atbash), else t = p

mod gens;

use std::env;
use std::fs;
use std::io::Write;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Instant;

const N: usize = 624;
const M: usize = 397;
const K: usize = 160; // key values available to the fast sweep decoder
const MOD: i32 = 29;

#[inline]
fn tw(m: u32, u: u32, v: u32, php: bool) -> u32 {
    let lo = if php { u & 1 } else { v & 1 };
    m ^ (((u & 0x8000_0000) | (v & 0x7fff_ffff)) >> 1) ^ (0u32.wrapping_sub(lo) & 0x9908_b0df)
}

#[inline]
fn temper(mut y: u32) -> u32 {
    y ^= y >> 11;
    y ^= (y << 7) & 0x9d2c_5680;
    y ^= (y << 15) & 0xefc6_0000;
    y ^ (y >> 18)
}

#[inline]
fn init_next(prev: u32, i: usize) -> u32 {
    1812433253u32.wrapping_mul(prev ^ (prev >> 30)).wrapping_add(i as u32)
}

/// Full generator (any number of outputs).
struct Mt {
    s: [u32; N],
    next: usize,
    php: bool,
}

impl Mt {
    fn new(seed: u32, php: bool) -> Mt {
        let mut s = [0u32; N];
        s[0] = seed;
        for i in 1..N {
            s[i] = init_next(s[i - 1], i);
        }
        let mut m = Mt { s, next: N, php };
        m.reload();
        m
    }
    fn reload(&mut self) {
        let p = self.php;
        let s = &mut self.s;
        for i in 0..N - M {
            s[i] = tw(s[i + M], s[i], s[i + 1], p);
        }
        for i in N - M..N - 1 {
            s[i] = tw(s[i + M - N], s[i], s[i + 1], p);
        }
        s[N - 1] = tw(s[M - 1], s[N - 1], s[0], p);
        self.next = 0;
    }
    /// PHP mt_rand(): 31-bit value.
    fn rand31(&mut self) -> u32 {
        if self.next == N {
            self.reload();
        }
        let y = self.s[self.next];
        self.next += 1;
        temper(y) >> 1
    }
}

/// First K outputs of PHP's legacy generator for a seed, without building the full state.
#[inline]
fn fast_outputs(seed: u32, out: &mut [u32; K]) {
    let mut s = [0u32; M + K + 1];
    s[0] = seed;
    for i in 1..=M + K {
        s[i] = init_next(s[i - 1], i);
    }
    for i in 0..K {
        out[i] = temper(tw(s[i + M], s[i], s[i + 1], true)) >> 1;
    }
}

#[inline]
fn map_range(n: u32, lo: i64, hi: i64) -> i64 {
    // PHP 5 RAND_RANGE: min + (long)((double)(max - min + 1.0) * (n / (PHP_MT_RAND_MAX + 1.0)))
    lo + (((hi - lo) as f64 + 1.0) * (n as f64 / 2147483648.0)) as i64
}



// ------------------------------------------------------------------ other generators

/// php   = PHP < 7.1 mt_rand (MT_RAND_PHP); mt_rand(0,28) / mt_rand() % 29
/// glibc = glibc random() TYPE_3 after srandom(seed) = PHP 5 rand() on Linux; rand(0,28) / random() % 29
/// net   = .NET System.Random(seed) (Knuth subtractive); Next(29) / Next() % 29
#[derive(Clone, Copy, PartialEq)]
enum Gen {
    Php,
    Glibc,
    Net,
    New(gens::Kind), // py3 mt32 mt31 java msvc drand48 ruby: see gens.rs
}

fn parse_gen(s: &str) -> Gen {
    match s {
        "php" => Gen::Php,
        "glibc" => Gen::Glibc,
        "net" => Gen::Net,
        _ => match gens::parse(s) {
            Some(k) => Gen::New(k),
            None => panic!("generator must be php, glibc, net, py3, mt32, mt31, java, msvc, drand48 or ruby"),
        },
    }
}

#[inline]
fn glibc_init(seed: u32, r: &mut [u32]) {
    let mut word: i32 = if seed == 0 { 1 } else { seed as i32 };
    r[0] = word as u32;
    for i in 1..31 {
        let hi = word / 127773;
        let lo = word % 127773;
        word = 16807i32.wrapping_mul(lo).wrapping_sub(2836i32.wrapping_mul(hi));
        if word < 0 {
            word = word.wrapping_add(2147483647);
        }
        r[i] = word as u32;
    }
    for i in 31..34 {
        r[i] = r[i - 31];
    }
    for i in 34..r.len() {
        r[i] = r[i - 31].wrapping_add(r[i - 3]);
    }
}

fn glibc_fill(seed: u32, out: &mut [u32]) {
    let k = out.len();
    let mut r = vec![0u32; 344 + k];
    glibc_init(seed, &mut r);
    for i in 0..k {
        out[i] = r[344 + i] >> 1;
    }
}

#[inline]
fn glibc_fast(seed: u32, out: &mut [u32; K]) {
    let mut r = [0u32; 344 + K];
    glibc_init(seed, &mut r);
    for i in 0..K {
        out[i] = r[344 + i] >> 1;
    }
}

#[inline]
fn net_fill(seed: u32, out: &mut [u32]) {
    const MBIG: i32 = i32::MAX;
    const MSEED: i32 = 161803398;
    let s = seed as i32;
    let sub = if s == i32::MIN { i32::MAX } else { s.abs() };
    let mut a = [0i32; 56];
    let mut mj = MSEED - sub;
    a[55] = mj;
    let mut mk = 1i32;
    for i in 1..55 {
        let ii = (21 * i) % 55;
        a[ii] = mk;
        mk = mj - mk;
        if mk < 0 {
            mk += MBIG;
        }
        mj = a[ii];
    }
    for _ in 1..5 {
        for i in 1..56 {
            a[i] = a[i].wrapping_sub(a[1 + (i + 30) % 55]);
            if a[i] < 0 {
                a[i] += MBIG;
            }
        }
    }
    let (mut inext, mut inextp) = (0usize, 21usize);
    for o in out.iter_mut() {
        inext += 1;
        if inext >= 56 {
            inext = 1;
        }
        inextp += 1;
        if inextp >= 56 {
            inextp = 1;
        }
        let mut v = a[inext].wrapping_sub(a[inextp]);
        if v == MBIG {
            v -= 1;
        }
        if v < 0 {
            v += MBIG;
        }
        a[inext] = v;
        *o = v as u32;
    }
}

/// Raw outputs of any generator (full length, for plant / verify / vectors).
fn gen_outputs(rng: Gen, seed: u32, count: usize) -> Vec<u32> {
    let mut v = vec![0u32; count];
    match rng {
        Gen::Php => {
            let mut mt = Mt::new(seed, true);
            for x in v.iter_mut() {
                *x = mt.rand31();
            }
        }
        Gen::Glibc => glibc_fill(seed, &mut v),
        Gen::Net => net_fill(seed, &mut v),
        Gen::New(_) => panic!("this generator has no one-output-per-key stream; use key_stream"),
    }
    v
}

#[inline]
fn fast_gen(rng: Gen, seed: u32, out: &mut [u32; K]) {
    match rng {
        Gen::Php => fast_outputs(seed, out),
        Gen::Glibc => glibc_fast(seed, out),
        Gen::Net => net_fill(seed, out),
        Gen::New(_) => panic!("this generator has no one-output-per-key stream; use fast_keys"),
    }
}

/// `count` key values 0..28 of a seed under map 0 or 1.
fn key_stream(rng: Gen, seed: u32, map: u8, count: usize) -> Vec<u8> {
    match rng {
        Gen::New(k) => {
            let mut v = vec![0u8; count];
            gens::fill_keys(k, seed, map, &mut v);
            v
        }
        _ => gen_outputs(rng, seed, count).iter().map(|&n| key_gen(rng, n, map)).collect(),
    }
}

/// The first K key values of both maps (the sweeps' hot path).
fn fast_keys(rng: Gen, seed: u32, keys: &mut [[u8; K]; 2]) {
    match rng {
        Gen::New(k) => {
            gens::fill_keys(k, seed, 0, &mut keys[0]);
            gens::fill_keys(k, seed, 1, &mut keys[1]);
        }
        _ => {
            let mut raw = [0u32; K];
            fast_gen(rng, seed, &mut raw);
            for i in 0..K {
                keys[0][i] = key_gen(rng, raw[i], 0);
                keys[1][i] = key_gen(rng, raw[i], 1);
            }
        }
    }
}

/// map 0 = the language's own range call, map 1 = raw % 29.
#[inline]
fn key_gen(rng: Gen, n: u32, map: u8) -> u8 {
    let km = gens::km();
    if map == 1 {
        return (n % km) as u8;
    }
    match rng {
        Gen::Net => ((n as f64 * (1.0 / 2147483647.0)) * km as f64) as u8, // (int)(Sample() * 29)
        _ => (km as f64 * (n as f64 / 2147483648.0)) as u8,                  // PHP 5 RAND_RANGE
    }
}

// ------------------------------------------------------------------ data

struct Win {
    name: String,
    prev: i32,
    runes: Vec<u8>,
    word_end: Vec<bool>,
    n: usize,      // runes decoded by the sweep: word-aligned cut at about WLEN
    abort1: usize, // end of the second word of length >= 3
    abort2: usize, // word end at or after 30 runes
}

const WLEN: usize = 60;

fn load_windows(path: &str) -> Vec<Win> {
    let txt = fs::read_to_string(path).expect("windows file");
    let mut out = Vec::new();
    let mut lines = txt.lines();
    while let Some(h) = lines.next() {
        if !h.starts_with("W ") {
            continue;
        }
        let f: Vec<&str> = h.split_whitespace().collect();
        let name = f[1].to_string();
        let prev: i32 = f[2].parse().unwrap();
        let r: Vec<u8> = lines.next().unwrap()[2..].split_whitespace().map(|x| x.parse().unwrap()).collect();
        let l: Vec<usize> = lines.next().unwrap()[2..].split_whitespace().map(|x| x.parse().unwrap()).collect();
        let mut word_end = vec![false; r.len()];
        let mut pos = 0;
        for len in l {
            pos += len;
            word_end[pos - 1] = true;
        }
        assert_eq!(pos, r.len());
        let (mut n, mut abort1, mut abort2, mut long_words, mut start) = (0, 0, 0, 0, 0);
        for i in 0..r.len() {
            if word_end[i] {
                if i + 1 <= WLEN {
                    n = i + 1;
                }
                if i + 1 - start >= 3 {
                    long_words += 1;
                    if long_words == 2 && abort1 == 0 {
                        abort1 = i + 1;
                    }
                }
                if abort2 == 0 && i + 1 >= 30 {
                    abort2 = i + 1;
                }
                start = i + 1;
            }
        }
        out.push(Win { name, prev, runes: r, word_end, n, abort1, abort2 });
    }
    out
}

struct Dict {
    by_len: Vec<Vec<u64>>,
}

impl Dict {
    fn load(path: &str) -> Dict {
        let mut by_len = vec![Vec::new(); 13];
        for line in fs::read_to_string(path).expect("dict file").lines() {
            let mut it = line.split_whitespace();
            let l: usize = it.next().unwrap().parse().unwrap();
            let c: u64 = it.next().unwrap().parse().unwrap();
            if l < by_len.len() {
                by_len[l].push(c);
            }
        }
        for v in by_len.iter_mut() {
            v.sort_unstable();
        }
        Dict { by_len }
    }
    #[inline]
    fn has(&self, len: usize, code: u64) -> bool {
        len < self.by_len.len() && self.by_len[len].binary_search(&code).is_ok()
    }
}

// ------------------------------------------------------------------ decoder

#[derive(Clone, Copy)]
struct St {
    j: u16,
    code: u64,
    len: u8,
    score: u16,
}

#[inline]
fn md(x: i32) -> i32 {
    ((x % MOD) + MOD) % MOD
}

/// Skip-aware Viterbi decode of the first `w.n` runes (word-aligned, about 60). Score = number of
/// runes inside dictionary words of length >= 3. Two early aborts: after the window's second word of
/// length >= 3 (`w.abort1`) the best state must have scored, and at `w.abort2` it must reach 6.
#[inline]
fn decode_fast(w: &Win, key: &[u8], sign: i32, atb: bool, model: u8, dict: &Dict) -> u16 {
    const Z: St = St { j: 0, code: 0, len: 0, score: 0 };
    let mut states: [St; 16] = [Z; 16];
    let mut ns = 1usize;
    let mut next: [St; 48] = [Z; 48];
    let klen = key.len();
    // t = c - sign * k (mod 29), via add of the "negated" key
    let sub = |c: i32, k: u8| -> i32 {
        let v = if sign > 0 { c - k as i32 } else { c + k as i32 };
        if v < 0 { v + MOD } else if v >= MOD { v - MOD } else { v }
    };
    let add = |t: i32, k: u8| -> i32 {
        let v = if sign > 0 { t + k as i32 } else { t - k as i32 };
        if v < 0 { v + MOD } else if v >= MOD { v - MOD } else { v }
    };
    for i in 0..w.n {
        let c = w.runes[i] as i32;
        let prev = if i == 0 { w.prev } else { w.runes[i - 1] as i32 };
        let mut nn = 0usize;
        for si in 0..ns {
            let s = states[si];
            let j = s.j as usize;
            if j + 3 >= klen {
                continue;
            }
            macro_rules! push {
                ($t:expr, $nj:expr) => {{
                    if nn < 48 {
                        let t: i32 = $t;
                        let p = if atb { 28 - t } else { t } as u64;
                        next[nn] = St { j: $nj as u16, code: s.code * 29 + p, len: s.len + 1, score: s.score };
                        nn += 1;
                    }
                }};
            }
            let k0 = key[j];
            if model == 0 {
                push!(sub(c, k0), j + 1);
                if prev >= 0 {
                    let t1 = sub(c, key[j + 1]);
                    if add(t1, k0) == prev {
                        push!(t1, j + 2);
                    }
                    let t2 = sub(c, key[j + 2]);
                    if add(t2, k0) == prev && add(t2, key[j + 1]) == prev {
                        push!(t2, j + 3);
                    }
                }
            } else {
                if prev >= 0 && c == prev {
                    push!(sub(c, k0), j + 2);
                } else {
                    push!(sub(c, k0), j + 1);
                }
                if prev >= 0 {
                    let t = sub(c, key[j + 2]);
                    if add(t, k0) == prev {
                        push!(t, j + 3);
                    }
                }
            }
        }
        if nn == 0 {
            return 0;
        }
        if w.word_end[i] {
            ns = 0;
            for q in 0..nn {
                let mut s = next[q];
                if s.len >= 3 && dict.has(s.len as usize, s.code) {
                    s.score += s.len as u16;
                }
                s.code = 0;
                s.len = 0;
                // merge equal key pointers (the future depends only on j)
                let mut found = false;
                for r in 0..ns {
                    if states[r].j == s.j {
                        if s.score > states[r].score {
                            states[r] = s;
                        }
                        found = true;
                        break;
                    }
                }
                if !found {
                    if ns < 16 {
                        states[ns] = s;
                        ns += 1;
                    } else {
                        // replace the worst state if this one is better
                        let (wi, ws) = states.iter().enumerate().map(|(a, b)| (a, b.score)).min_by_key(|x| x.1).unwrap();
                        if s.score > ws {
                            states[wi] = s;
                        }
                    }
                }
            }
            if i + 1 == w.abort1 || i + 1 == w.abort2 {
                let best = states[..ns].iter().map(|s| s.score).max().unwrap();
                if (i + 1 == w.abort1 && best == 0) || (i + 1 == w.abort2 && best < 6) {
                    return best;
                }
            }
        } else {
            ns = nn.min(16);
            states[..ns].copy_from_slice(&next[..ns]);
        }
    }
    states[..ns].iter().map(|s| s.score).max().unwrap_or(0)
}

/// Full decode with plaintext, for verification (beam 64, no abort). Returns (score fraction of
/// runes in dictionary words of any length, plaintext runes).
fn decode_full(w: &Win, key: &[u8], sign: i32, atb: bool, model: u8, dict: &Dict) -> (f64, Vec<u8>) {
    #[derive(Clone)]
    struct F {
        j: usize,
        plain: Vec<u8>,
        wstart: usize,
        score: f64,
    }
    let mut states = vec![F { j: 0, plain: Vec::new(), wstart: 0, score: 0.0 }];
    for i in 0..w.runes.len() {
        let c = w.runes[i] as i32;
        let prev = if i == 0 { w.prev } else { w.runes[i - 1] as i32 };
        let mut nx: Vec<F> = Vec::new();
        for s in &states {
            let j = s.j;
            if j + 3 >= key.len() {
                continue;
            }
            let mut opts: Vec<(i32, usize)> = Vec::new();
            let k0 = key[j] as i32;
            if model == 0 {
                opts.push((md(c - sign * k0), j + 1));
                if prev >= 0 {
                    for m in 1..=2usize {
                        let t = md(c - sign * key[j + m] as i32);
                        if (0..m).all(|u| md(t + sign * key[j + u] as i32) == prev) {
                            opts.push((t, j + m + 1));
                        }
                    }
                }
            } else {
                if prev >= 0 && c == prev {
                    opts.push((md(c - sign * k0), j + 2));
                } else {
                    opts.push((md(c - sign * k0), j + 1));
                }
                if prev >= 0 {
                    let t = md(c - sign * key[j + 2] as i32);
                    if md(t + sign * k0) == prev {
                        opts.push((t, j + 3));
                    }
                }
            }
            for (t, nj) in opts {
                let mut f = s.clone();
                f.plain.push(if atb { (28 - t) as u8 } else { t as u8 });
                f.j = nj;
                nx.push(f);
            }
        }
        if w.word_end[i] {
            for f in nx.iter_mut() {
                let word = &f.plain[f.wstart..];
                let mut code = 0u64;
                for &x in word {
                    code = code * 29 + x as u64;
                }
                if dict.has(word.len(), code) {
                    f.score += word.len() as f64;
                }
                f.wstart = f.plain.len();
            }
            nx.sort_by(|a, b| b.score.partial_cmp(&a.score).unwrap());
            let mut seen = std::collections::HashSet::new();
            nx.retain(|f| seen.insert(f.j));
        }
        nx.truncate(64);
        states = nx;
        if states.is_empty() {
            return (0.0, Vec::new());
        }
    }
    let best = states.into_iter().max_by(|a, b| a.score.partial_cmp(&b.score).unwrap()).unwrap();
    (best.score / w.runes.len() as f64, best.plain)
}

const LATIN: [&str; 29] = ["F", "U", "TH", "O", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B",
    "E", "M", "L", "ING", "OE", "D", "A", "AE", "Y", "IA", "EA"];

// ------------------------------------------------------------------ modes

fn mode_vectors_other(net_path: &str) {
    // .NET Framework System.Random reference (PowerShell 5.1 / .NET 4.x)
    let txt = fs::read_to_string(net_path).expect("net vectors");
    let (mut ok, mut bad) = (0, 0);
    for line in txt.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        let seed = f[1].parse::<i64>().unwrap() as i32 as u32;
        let vals: Vec<u32> = f[3..].iter().map(|x| x.parse().unwrap()).collect();
        let raw = gen_outputs(Gen::Net, seed, vals.len());
        let got: Vec<u32> = if f[2] == "raw" { raw } else { raw.iter().map(|&n| key_gen(Gen::Net, n, 0) as u32).collect() };
        let mut fast = [0u32; K];
        fast_gen(Gen::Net, seed, &mut fast);
        let fast_ok = f[2] != "raw" || fast.iter().zip(vals.iter()).all(|(a, b)| a == b);
        if got == vals && fast_ok { ok += 1 } else { bad += 1; println!("MISMATCH net {} {}", f[1], f[2]); }
    }
    println!(".NET vectors: {} match, {} mismatch", ok, bad);
    // glibc random() after srandom(1): the classic published sequence
    let known = [1804289383u32, 846930886, 1681692777, 1714636915, 1957747793, 424238335, 719885386, 1649760492,
                 596516649, 1189641421];
    let g = gen_outputs(Gen::Glibc, 1, 10);
    let mut fast = [0u32; K];
    fast_gen(Gen::Glibc, 1, &mut fast);
    let g0 = gen_outputs(Gen::Glibc, 0, 10);
    println!("glibc srandom(1): {} (seed 0 == seed 1: {}; fast path: {})", if g == known { "match" } else { "MISMATCH" },
             g0 == known, fast[..10] == known[..]);
}

fn mode_vectors(path: &str) {
    let txt = fs::read_to_string(path).expect("vectors");
    let (mut ok, mut bad) = (0, 0);
    for line in txt.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        let php = f[0] == "php";
        let seed64: i64 = f[1].parse().unwrap();
        let seed = seed64 as u32;
        let vals: Vec<i64> = f[3..].iter().map(|x| x.parse().unwrap()).collect();
        let mut mt = Mt::new(seed, php);
        let got: Vec<i64> = (0..vals.len())
            .map(|_| {
                let n = mt.rand31();
                if f[2] == "raw" { n as i64 } else { map_range(n, 0, 28) }
            })
            .collect();
        let mut same = got == vals;
        if php && f[2] == "raw" {
            let mut fo = [0u32; K];
            fast_outputs(seed, &mut fo);
            same &= fo.iter().zip(vals.iter()).all(|(a, b)| *a as i64 == *b);
        }
        if same { ok += 1 } else { bad += 1; println!("MISMATCH {} {} {}", f[0], f[1], f[2]); }
    }
    println!("vectors: {} match, {} mismatch", ok, bad);
}

fn mode_plant(args_all: &[String]) {
    let rng = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = load_windows(&args[0]);
    let seed: u32 = args[1].parse().unwrap();
    let map: u8 = args[2].parse().unwrap();
    let model: u8 = args[3].parse().unwrap();
    let sign: i32 = args[4].parse().unwrap();
    let atb = args[5] == "1";
    let keep: f64 = args[6].parse().unwrap();
    let mut out = String::new();
    let mut lcg: u64 = 0x2545F4914F6CDD1D ^ seed as u64;
    let mut coin = || {
        lcg = lcg.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        (lcg >> 11) as f64 / (1u64 << 53) as f64
    };
    for w in &wins {
        let keyed = matches!(rng, Gen::New(_));      // these generators give key values directly
        let len = w.runes.len() * 4 + 64;
        let stream: Vec<u32> = if keyed {
            key_stream(rng, seed, map, len).iter().map(|&x| x as u32).collect()
        } else {
            gen_outputs(rng, seed, len)
        };
        let kg = |n: u32| -> i32 { if keyed { n as i32 } else { key_gen(rng, n, map) as i32 } };
        let mut sp = 0usize;
        let mut draw = || {
            sp += 1;
            stream[sp - 1]
        };
        let mut prev: i32 = -1;
        let mut c = Vec::with_capacity(w.runes.len());
        for &p in &w.runes {
            let t = if atb { 28 - p as i32 } else { p as i32 };
            let mut y = md(t + sign * kg(draw()));
            if model == 0 {
                let mut tries = 0;
                while prev >= 0 && y == prev && coin() >= keep && tries < 5 {
                    y = md(t + sign * kg(draw()));
                    tries += 1;
                }
            } else if prev >= 0 && y == prev {
                let c100 = if keyed { draw() as f64 * (100.0 / 29.0) } else { (draw() % 100) as f64 }; // the coin spends one key value
                if c100 >= keep * 100.0 {
                    y = md(t + sign * kg(draw()));
                }
            }
            c.push(y as u8);
            prev = y;
        }
        let mut lens = Vec::new();
        let mut l = 0;
        for i in 0..w.runes.len() {
            l += 1;
            if w.word_end[i] {
                lens.push(l.to_string());
                l = 0;
            }
        }
        out += &format!("W planted_{} -1\nR {}\nL {}\n", w.name,
                        c.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "), lens.join(" "));
    }
    fs::write(&args[7], out).unwrap();
    println!("planted seed {} into {} windows -> {}", seed, wins.len(), args[7]);
}

#[derive(Clone, Copy)]
struct Cand {
    score: u16,
    seed: u32,
    win: u8,
    variant: u8,
}

fn variant_parts(v: u8) -> (u8, u8, i32, bool) {
    // v = ((model * 2 + map) * 2 + sign_idx) * 2 + atb
    let atb = v & 1 == 1;
    let sign = if (v >> 1) & 1 == 0 { 1 } else { -1 };
    let map = (v >> 2) & 1;
    let model = (v >> 3) & 1;
    (model, map, sign, atb)
}

fn mode_sweep(args_all: &[String]) {
    let rng = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = Arc::new(load_windows(&args[0]));
    let dict = Arc::new(Dict::load(&args[1]));
    let lo: u64 = args[2].parse().unwrap();
    let hi: u64 = args[3].parse().unwrap();
    let out = args[4].clone();
    let threads: usize = if args.len() > 5 { args[5].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let next = Arc::new(AtomicU64::new(lo));
    let done = Arc::new(AtomicU64::new(0));
    let top: Arc<Mutex<Vec<Cand>>> = Arc::new(Mutex::new(Vec::new()));
    let hist_all: Arc<Mutex<[u64; 64]>> = Arc::new(Mutex::new([0u64; 64]));
    const CHUNK: u64 = 1 << 18;
    const TOPK: usize = 400;
    let t0 = Instant::now();
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (wins, dict, next, done, top) = (wins.clone(), dict.clone(), next.clone(), done.clone(), top.clone());
        let hist_all = hist_all.clone();
        hs.push(std::thread::spawn(move || {
            let mut hist = [0u64; 64];
            let mut local: Vec<Cand> = Vec::new();
            let mut floor: u16 = 0;
            let mut keys = [[0u8; K]; 2];
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= hi {
                    break;
                }
                let b = (a + CHUNK).min(hi);
                for seed64 in a..b {
                    let seed = seed64 as u32;
                    fast_keys(rng, seed, &mut keys);
                    for (wi, w) in wins.iter().enumerate() {
                        for v in 0..16u8 {
                            let (model, map, sign, atb) = variant_parts(v);
                            let s = decode_fast(w, &keys[map as usize], sign, atb, model, &dict);
                            hist[(s as usize).min(63)] += 1;
                            if s > floor || (local.len() < TOPK && s > 0) {
                                local.push(Cand { score: s, seed, win: wi as u8, variant: v });
                                if local.len() >= 2 * TOPK {
                                    local.sort_by(|x, y| y.score.cmp(&x.score));
                                    local.truncate(TOPK);
                                    floor = local[TOPK - 1].score;
                                }
                            }
                        }
                    }
                }
                let d = done.fetch_add(b - a, Ordering::Relaxed) + (b - a);
                if d % (CHUNK * 64) < CHUNK {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} seeds) {:.0} seeds/s, eta {:.0} s", 100.0 * d as f64 / (hi - lo) as f64, d,
                              rate, ((hi - lo) as f64 - d as f64) / rate);
                }
            }
            local.sort_by(|x, y| y.score.cmp(&x.score));
            local.truncate(TOPK);
            top.lock().unwrap().extend(local);
            for (a, b) in hist_all.lock().unwrap().iter_mut().zip(hist.iter()) {
                *a += b;
            }
        }));
    }
    for h in hs {
        h.join().unwrap();
    }
    let mut all = top.lock().unwrap().clone();
    all.sort_by(|x, y| y.score.cmp(&x.score));
    all.truncate(4000);
    let mut f = fs::File::create(&out).unwrap();
    writeln!(f, "score\tseed\twindow\tmodel\tmap\tsign\tatbash").unwrap();
    for c in &all {
        let (model, map, sign, atb) = variant_parts(c.variant);
        writeln!(f, "{}\t{}\t{}\t{}\t{}\t{}\t{}", c.score, c.seed, wins[c.win as usize].name, model, map, sign, atb as u8)
            .unwrap();
    }
    eprintln!("swept {} seeds in {:.0} s; best score {}", hi - lo, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score).unwrap_or(0));
    let h = hist_all.lock().unwrap();
    eprintln!("hist {}", h.iter().enumerate().filter(|(_, c)| **c > 0).map(|(b, c)| format!("{b}:{c}")).collect::<Vec<_>>().join(" "));
}

fn mode_raw(args: &[String]) {
    let rng = parse_gen(&args[0]);
    let (lo, hi): (u64, u64) = (args[1].parse().unwrap(), args[2].parse().unwrap());
    let mut f = std::io::BufWriter::new(fs::File::create(&args[3]).unwrap());
    let mut raw = [0u32; K];
    for seed in lo..hi {
        fast_gen(rng, seed as u32, &mut raw);
        write!(f, "{seed}").unwrap();
        for x in raw.iter() {
            write!(f, " {x}").unwrap();
        }
        writeln!(f).unwrap();
    }
}

/// seed, then the first K values of key map 0 and of key map 1 (what gpu.py compares with, for every generator)
fn mode_keys(args: &[String]) {
    if let Some(km) = args.get(4) {
        gens::set_km(km.parse().expect("km"));                 // 28: the key alphabet of the step-domain cipher
    }
    let rng = parse_gen(&args[0]);
    let (lo, hi): (u64, u64) = (args[1].parse().unwrap(), args[2].parse().unwrap());
    let mut f = std::io::BufWriter::new(fs::File::create(&args[3]).unwrap());
    let mut keys = [[0u8; K]; 2];
    for seed in lo..hi {
        fast_keys(rng, seed as u32, &mut keys);
        write!(f, "{seed}").unwrap();
        for m in 0..2 {
            for x in keys[m].iter() {
                write!(f, " {x}").unwrap();
            }
        }
        writeln!(f).unwrap();
    }
}

/// seed, then `count` key values of map 0 and of map 1 under the key alphabet km (any count: the step-domain sweep reads 256)
fn mode_keysn(args: &[String]) {
    let rng = parse_gen(&args[0]);
    let (lo, hi): (u64, u64) = (args[1].parse().unwrap(), args[2].parse().unwrap());
    let mut f = std::io::BufWriter::new(fs::File::create(&args[3]).unwrap());
    gens::set_km(args[4].parse().expect("km"));
    let count: usize = args[5].parse().expect("count");
    for seed in lo..hi {
        write!(f, "{seed}").unwrap();
        for m in 0..2u8 {
            for x in key_stream(rng, seed as u32, m, count) {
                write!(f, " {x}").unwrap();
            }
        }
        writeln!(f).unwrap();
    }
}

fn mode_scores(args_all: &[String]) {
    let rng = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = load_windows(&args[0]);
    let dict = Dict::load(&args[1]);
    let (lo, hi): (u64, u64) = (args[2].parse().unwrap(), args[3].parse().unwrap());
    let mut f = std::io::BufWriter::new(fs::File::create(&args[4]).unwrap());
    let mut keys = [[0u8; K]; 2];
    for seed64 in lo..hi {
        fast_keys(rng, seed64 as u32, &mut keys);
        for (wi, w) in wins.iter().enumerate() {
            for v in 0..16u8 {
                let (model, map, sign, atb) = variant_parts(v);
                writeln!(f, "{seed64} {wi} {v} {}", decode_fast(w, &keys[map as usize], sign, atb, model, &dict)).unwrap();
            }
        }
    }
}

fn mode_verify(args_all: &[String]) {
    let rng = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = load_windows(&args[0]);
    let dict = Dict::load(&args[1]);
    let seed: u32 = args[2].parse().unwrap();
    let w = wins.iter().find(|w| w.name == args[3]).expect("window");
    let map: u8 = args[4].parse().unwrap();
    let model: u8 = args[5].parse().unwrap();
    let sign: i32 = args[6].parse().unwrap();
    let atb = args[7] == "1";
    let key: Vec<u8> = key_stream(rng, seed, map, w.runes.len() * 3 + 50);
    let (score, plain) = decode_full(w, &key, sign, atb, model, &dict);
    let mut txt = String::new();
    for (i, p) in plain.iter().enumerate() {
        txt += LATIN[*p as usize];
        if w.word_end[i] {
            txt.push(' ');
        }
    }
    println!("{:.3}\t{}\t{}", score, seed, &txt[..txt.len().min(400)]);
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("vectors") => mode_vectors(&args[2]),
        Some("vectors_other") => mode_vectors_other(&args[2]),
        Some("plant") => mode_plant(&args[2..]),
        Some("sweep") => mode_sweep(&args[2..]),
        Some("verify") => mode_verify(&args[2..]),
        Some("raw") => mode_raw(&args[2..]),
        Some("keys") => mode_keys(&args[2..]),
        Some("keysn") => mode_keysn(&args[2..]),
        Some("scores") => mode_scores(&args[2..]),
        _ => eprintln!("usage: phpmt vectors|plant|sweep|verify|raw|keys|scores ..."),
    }
}
