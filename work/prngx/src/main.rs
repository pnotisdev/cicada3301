//! prngx: more seeded-PRNG pads for Liber Primus LP2 (companion to work/phpmt, same decoder and CLI).
//!
//! Generators (a seed -> a stream of raw 32-bit values -> key values 0..28 by one of several "maps"):
//!   mt     std MT19937, init_genrand(seed): C++ std::mt19937, PHP >= 7.1 mt_srand, numpy RandomState(seed)
//!   pymt   MT19937, init_by_array(32-bit words of |seed|): Python random.seed(int), Ruby Random.new(int); one word
//!          below 2^32, two words above (e.g. a millisecond timestamp, see the prng-time campaign)
//!   (java takes the full 48-bit seed of java.util.Random(long), so millisecond timestamps need no change there)
//!   msvc   Microsoft C rand(): s = s * 214013 + 2531011; (s >> 16) & 0x7fff
//!   java   java.util.Random(seed): 48-bit LCG; raw = next(32)
//!   rand48 drand48 family (Perl srand/rand, C srand48): 48-bit LCG, seed << 16 | 0x330E; raw = X >> 16
//! Maps (m): mt/pymt: 0 raw%29, 1 floor(raw*29/2^32), 2 top-5-bits with rejection (Python randrange/randint),
//!   3 low-5-bits with rejection (numpy randint), 4 (raw>>1)%29 (31-bit), 5 float53 (two raws) * 29
//!   msvc: 0 v%29, 1 v*29>>15, 2 v*29/32767     java: 0 nextInt(29), 1 (int)(nextDouble()*29), 2 abs(nextInt())%29
//!   rand48: 0 lrand48()%29, 1 floor(29*drand48()) (uses the top 32 bits of X)
//! Model, sign and atbash as in work/phpmt (model 0 skip, 1 coin; sign +-1; atb = Atbash on the plaintext).
//!
//! Modes (same arguments as phpmt, generator first):
//!   vectors <vectors.txt>
//!   keys <gen> <seed> <map> <count>                                         (one seed's key values)
//!   plant <gen> <plain.txt> <seed> <map> <model> <sign> <atb> <keep> <out.txt>
//!   sweep <gen> <windows.txt> <dict.txt> <lo> <hi> <out.tsv> [threads]     (lo, hi: i64, hi exclusive)
//!   verify <gen> <windows.txt> <dict.txt> <seed> <window> <map> <model> <sign> <atb>

use std::env;
use std::fs;
use std::io::Write;
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Instant;

const K: usize = 160; // key values the fast decoder looks at
const RK: usize = 400; // raw outputs generated per seed in a sweep
const MOD: i32 = 29;


// ------------------------------------------------------------------ generators

#[derive(Clone, Copy, PartialEq)]
enum Gen {
    Mt,
    PyMt,
    Msvc,
    Java,
    Rand48,
    Seq,
}

fn parse_gen(s: &str) -> Gen {
    match s {
        "mt" => Gen::Mt,
        "pymt" => Gen::PyMt,
        "msvc" => Gen::Msvc,
        "java" => Gen::Java,
        "rand48" => Gen::Rand48,
        "seq" => Gen::Seq,
        _ => panic!("generator must be mt, pymt, msvc, java, rand48 or seq"),
    }
}

fn n_maps(g: Gen) -> u8 {
    match g {
        Gen::Mt | Gen::PyMt => 6,
        Gen::Msvc | Gen::Java => 3,
        Gen::Rand48 => 2,
        Gen::Seq => 28,
    }
}

/// Integer-sequence library for the `seq` generator: file given by the environment variable PRNGX_SEQ, one
/// sequence per line: `<id> <v0> <v1> ...` with values already reduced mod 29. Seed = index * 128 + start offset.
static SEQS: std::sync::OnceLock<Vec<Vec<u8>>> = std::sync::OnceLock::new();

fn seqs() -> &'static Vec<Vec<u8>> {
    SEQS.get_or_init(|| {
        let path = env::var("PRNGX_SEQ").expect("set PRNGX_SEQ to the sequence file for the seq generator");
        fs::read_to_string(&path)
            .unwrap_or_else(|e| panic!("{path}: {e}"))
            .lines()
            .filter(|l| !l.is_empty() && !l.starts_with('#'))
            .map(|l| l.split_whitespace().skip(1).map(|x| x.parse::<u8>().unwrap()).collect())
            .collect()
    })
}

const N: usize = 624;
const M: usize = 397;

#[inline]
fn temper(mut y: u32) -> u32 {
    y ^= y >> 11;
    y ^= (y << 7) & 0x9d2c_5680;
    y ^= (y << 15) & 0xefc6_0000;
    y ^ (y >> 18)
}

#[inline]
fn init_genrand(seed: u32, s: &mut [u32; N]) {
    s[0] = seed;
    for i in 1..N {
        s[i] = 1812433253u32.wrapping_mul(s[i - 1] ^ (s[i - 1] >> 30)).wrapping_add(i as u32);
    }
}

fn init_by_array(key: &[u32], s: &mut [u32; N]) {
    init_genrand(19650218, s);
    let (mut i, mut j) = (1usize, 0usize);
    for _ in 0..N.max(key.len()) {
        s[i] = (s[i] ^ (s[i - 1] ^ (s[i - 1] >> 30)).wrapping_mul(1664525)).wrapping_add(key[j]).wrapping_add(j as u32);
        i += 1;
        j += 1;
        if i >= N {
            s[0] = s[N - 1];
            i = 1;
        }
        if j >= key.len() {
            j = 0;
        }
    }
    for _ in 0..N - 1 {
        s[i] = (s[i] ^ (s[i - 1] ^ (s[i - 1] >> 30)).wrapping_mul(1566083941)).wrapping_sub(i as u32);
        i += 1;
        if i >= N {
            s[0] = s[N - 1];
            i = 1;
        }
    }
    s[0] = 0x8000_0000;
}

/// Standard MT19937 twist over the whole state, in place (indices wrap, new values feed later ones).
fn twist(s: &mut [u32; N]) {
    for i in 0..N {
        let u = s[i];
        let v = s[(i + 1) % N];
        let m = s[(i + M) % N];
        s[i] = m ^ (((u & 0x8000_0000) | (v & 0x7fff_ffff)) >> 1) ^ (0u32.wrapping_sub(v & 1) & 0x9908_b0df);
    }
}

/// First `count` raw 32-bit outputs of a generator.
fn raw_n(g: Gen, seed: i64, count: usize) -> Vec<u32> {
    let mut v = Vec::with_capacity(count);
    match g {
        Gen::Mt | Gen::PyMt => {
            let mut s = [0u32; N];
            if g == Gen::Mt {
                init_genrand(seed as u32, &mut s);
            } else {
                // CPython random.seed(n) (and Ruby Random.new(n) for n >= 2^32): the 32-bit words of |n|, least
                // significant first; one word below 2^32 (all earlier sweeps), two up to 2^64 (millisecond timestamps)
                let n = seed.unsigned_abs();
                if n >> 32 == 0 {
                    init_by_array(&[n as u32], &mut s);
                } else {
                    init_by_array(&[n as u32, (n >> 32) as u32], &mut s);
                }
            }
            while v.len() < count {
                twist(&mut s);
                for &y in s.iter() {
                    if v.len() < count {
                        v.push(temper(y));
                    }
                }
            }
        }
        Gen::Msvc => {
            let mut st = seed as u32;
            for _ in 0..count {
                st = st.wrapping_mul(214013).wrapping_add(2531011);
                v.push((st >> 16) & 0x7fff);
            }
        }
        Gen::Java => {
            let mask = (1u64 << 48) - 1;
            let mut s = ((seed as u64) ^ 0x5DEECE66D) & mask;
            for _ in 0..count {
                s = s.wrapping_mul(0x5DEECE66D).wrapping_add(0xB) & mask;
                v.push((s >> 16) as u32);
            }
        }
        Gen::Seq => {
            let (idx, off) = ((seed / 128) as usize, (seed % 128) as usize);
            // PRNGX_SEQ_OFFMAX limits the start offsets that are tried (default: all 128)
            let offmax: usize = env::var("PRNGX_SEQ_OFFMAX").ok().and_then(|v| v.parse().ok()).unwrap_or(128);
            if off >= offmax {
                return v;
            }
            if let Some(s) = seqs().get(idx) {
                for i in 0..count {
                    match s.get(off + i) {
                        Some(&x) => v.push(x as u32),
                        None => break,
                    }
                }
            }
        }
        Gen::Rand48 => {
            let mask = (1u64 << 48) - 1;
            let mut x = (((seed as u32) as u64) << 16) | 0x330E;
            for _ in 0..count {
                x = x.wrapping_mul(0x5DEECE66D).wrapping_add(0xB) & mask;
                v.push((x >> 16) as u32);
            }
        }
    }
    v
}

/// Key values 0..28 from raw outputs under a map (rejection maps consume a variable number of raws).
fn keys_from(g: Gen, raw: &[u32], map: u8, out: &mut Vec<u8>, limit: usize) {
    out.clear();
    let mut i = 0usize;
    while i < raw.len() && out.len() < limit {
        let r = raw[i];
        match (g, map) {
            (Gen::Mt | Gen::PyMt, 0) => out.push((r % 29) as u8),
            (Gen::Mt | Gen::PyMt, 1) => out.push(((r as u64 * 29) >> 32) as u8),
            (Gen::Mt | Gen::PyMt, 2) => {
                let v = r >> 27;
                if v < 29 {
                    out.push(v as u8);
                }
            }
            (Gen::Mt | Gen::PyMt, 3) => {
                let v = r & 31;
                if v < 29 {
                    out.push(v as u8);
                }
            }
            (Gen::Mt | Gen::PyMt, 4) => out.push(((r >> 1) % 29) as u8),
            (Gen::Mt | Gen::PyMt, 5) => {
                if i + 1 >= raw.len() {
                    break;
                }
                let x = (((r >> 5) as u64) << 26) | (raw[i + 1] >> 6) as u64;
                out.push(((x as u128 * 29) >> 53) as u8);
                i += 1;
            }
            (Gen::Msvc, 0) => out.push((r % 29) as u8),
            (Gen::Msvc, 1) => out.push(((r * 29) >> 15) as u8),
            (Gen::Msvc, 2) => out.push((r * 29 / 32767) as u8),
            (Gen::Java, 0) => {
                let b = (r >> 1) as i64;
                let val = b % 29;
                if b - val + 28 <= i32::MAX as i64 {
                    out.push(val as u8);
                }
            }
            (Gen::Java, 1) => {
                if i + 1 >= raw.len() {
                    break;
                }
                let x = (((r >> 6) as u64) << 27) | (raw[i + 1] >> 5) as u64;
                out.push(((x as u128 * 29) >> 53) as u8);
                i += 1;
            }
            (Gen::Java, 2) => out.push(((r as i32).wrapping_abs() as u32 % 29) as u8),
            (Gen::Rand48, 0) => out.push(((r >> 1) % 29) as u8),
            (Gen::Rand48, 1) => out.push(((r as u64 * 29) >> 32) as u8),
            (Gen::Seq, m) => out.push(((r * (m as u32 + 1)) % 29) as u8),
            _ => panic!("map out of range"),
        }
        i += 1;
    }
}

#[inline]
fn md(x: i32) -> i32 {
    ((x % MOD) + MOD) % MOD
}


// ---- decoder: verbatim copy from work/phpmt/src/main.rs (do not edit here) ----

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


// ---- boundary-free decoder (desktop, 2026-10-17): the same skip / coin beam, scored by an English rune-bigram log-likelihood ratio instead of
// ---- dictionary words between the transcription's word separators (which LP2's separators may not be: work/log/phase9_boundaries.md).
// ---- Mirrors work/phpmt/bg.py::ref_decode and bgmt.cu::bg_decode statement by statement.

const BG_N: usize = 120; // runes decoded
const BG_ABORT_AT: usize = 40;
const BG_ABORT_THR: i32 = 60; // a true key is near +300 after 40 runes, a wrong one far below zero
const BG_START: usize = 29; // row of the table for the first rune: unigram log-odds

#[derive(Clone, Copy)]
struct BS {
    score: i32,
    j: u16,
    last: u8,
}

/// Table of work/phpmt/data/bigram.txt: 30 rows x 29 columns of round(10 ln(29 P(b|a))); row 29 is the unigram row.
fn load_bigram(path: &str) -> Vec<i16> {
    let t: Vec<i16> = fs::read_to_string(path).expect("bigram table").split_whitespace().map(|x| x.parse().unwrap()).collect();
    assert_eq!(t.len(), 30 * 29, "bigram table must be 30 x 29");
    t
}

fn decode_bg(runes: &[u8], prev0: i32, key: &[u8], sign: i32, atb: bool, model: u8, tbl: &[i16]) -> i32 {
    const Z: BS = BS { score: 0, j: 0, last: BG_START as u8 };
    let n = runes.len().min(BG_N);
    let mut states: [BS; 16] = [Z; 16];
    let mut ns = 1usize;
    let mut next: [BS; 48] = [Z; 48];
    let klen = key.len();
    let sub = |c: i32, k: u8| -> i32 {
        let v = if sign > 0 { c - k as i32 } else { c + k as i32 };
        if v < 0 { v + MOD } else if v >= MOD { v - MOD } else { v }
    };
    let add = |t: i32, k: u8| -> i32 {
        let v = if sign > 0 { t + k as i32 } else { t - k as i32 };
        if v < 0 { v + MOD } else if v >= MOD { v - MOD } else { v }
    };
    for i in 0..n {
        let c = runes[i] as i32;
        let prev = if i == 0 { prev0 } else { runes[i - 1] as i32 };
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
                        let p = if atb { 28 - t } else { t };
                        next[nn] = BS { score: s.score + tbl[s.last as usize * 29 + p as usize] as i32, j: $nj as u16, last: p as u8 };
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
            return -100000;
        }
        ns = 0;
        for q in 0..nn {
            let s = next[q];
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
                    let mut wi = 0usize;
                    let mut ws = states[0].score;
                    for r in 1..16 {
                        if states[r].score < ws {
                            ws = states[r].score;
                            wi = r;
                        }
                    }
                    if s.score > ws {
                        states[wi] = s;
                    }
                }
            }
        }
        if i + 1 == BG_ABORT_AT {
            let best = states[..ns].iter().map(|s| s.score).max().unwrap();
            if best < BG_ABORT_THR {
                return best;
            }
        }
    }
    states[..ns].iter().map(|s| s.score).max().unwrap()
}

// ------------------------------------------------------------------ modes

fn mode_vectors(path: &str) {
    // lines: <gen> <seed> <map|raw> <values...>; reference values come from real implementations
    let txt = fs::read_to_string(path).expect("vectors file");
    let (mut ok, mut bad) = (0, 0);
    for line in txt.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        if f.len() < 4 || f[0].starts_with('#') {
            continue;
        }
        let g = parse_gen(f[0]);
        let seed: i64 = f[1].parse().unwrap();
        let vals: Vec<i64> = f[3..].iter().map(|x| x.parse().unwrap()).collect();
        let raw = raw_n(g, seed, vals.len() * 6 + 40);
        let got: Vec<i64> = if f[2] == "raw" {
            raw[..vals.len()].iter().map(|&x| x as i64).collect()
        } else if f[2] == "javaint" {
            raw[..vals.len()].iter().map(|&x| x as i32 as i64).collect()
        } else {
            let mut k = Vec::new();
            keys_from(g, &raw, f[2].parse().unwrap(), &mut k, vals.len());
            k.iter().map(|&x| x as i64).collect()
        };
        if got == vals {
            ok += 1;
        } else {
            bad += 1;
            println!("MISMATCH {} {} {}: got {:?} want {:?}", f[0], f[1], f[2], &got[..got.len().min(6)], &vals[..vals.len().min(6)]);
        }
    }
    println!("prngx vectors: {} match, {} mismatch", ok, bad);
}

fn mode_plant(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = load_windows(&args[0]);
    let seed: i64 = args[1].parse().unwrap();
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
        let need = w.runes.len() * 4 + 64;
        let raw = raw_n(g, seed, need * 3 + 200);
        let mut key = Vec::new();
        keys_from(g, &raw, map, &mut key, need);
        let mut j = 0usize;
        let mut prev: i32 = -1;
        let mut c = Vec::with_capacity(w.runes.len());
        for &p in &w.runes {
            let t = if atb { 28 - p as i32 } else { p as i32 };
            let mut y = md(t + sign * key[j] as i32);
            j += 1;
            if model == 0 {
                let mut tries = 0;
                while prev >= 0 && y == prev && coin() >= keep && tries < 5 {
                    y = md(t + sign * key[j] as i32);
                    j += 1;
                    tries += 1;
                }
            } else if prev >= 0 && y == prev {
                j += 1; // the coin value
                if coin() >= keep {
                    y = md(t + sign * key[j] as i32);
                    j += 1;
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
    seed: i64,
    win: u8,
    variant: u8,
}

fn variant_parts(v: u8) -> (u8, u8, i32, bool) {
    // v = map * 8 + model * 4 + sign_idx * 2 + atb
    let sub = v & 7;
    (sub >> 2 & 1, v >> 3, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1)
}

/// PRNGX_MAPS=a,b,..: sweep / bgsweep only these key maps (default: every map of the generator). The prng-time campaign
/// uses it to keep the maps a language that seeds with two 32-bit words can produce (pymt: 2 randrange, 3 Ruby rand(n), 5 random()).
fn sweep_maps(g: Gen) -> Vec<u8> {
    match env::var("PRNGX_MAPS") {
        Ok(s) if !s.trim().is_empty() => {
            let v: Vec<u8> = s.split(',').map(|x| x.trim().parse().expect("PRNGX_MAPS: comma-separated map numbers")).collect();
            assert!(v.iter().all(|&m| m < n_maps(g)), "PRNGX_MAPS: map out of range for this generator");
            v
        }
        _ => (0..n_maps(g)).collect(),
    }
}

fn mode_sweep(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = Arc::new(load_windows(&args[0]));
    let dict = Arc::new(Dict::load(&args[1]));
    let lo: i64 = args[2].parse().unwrap();
    let hi: i64 = args[3].parse().unwrap();
    let out = args[4].clone();
    let threads: usize = if args.len() > 5 { args[5].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let next = Arc::new(AtomicU64::new(0));
    let done = Arc::new(AtomicU64::new(0));
    let top: Arc<Mutex<Vec<Cand>>> = Arc::new(Mutex::new(Vec::new()));
    const CHUNK: u64 = 1 << 16;
    const TOPK: usize = 400;
    let total = (hi - lo) as u64;
    let nm = n_maps(g);
    let maps = Arc::new(sweep_maps(g));
    let t0 = Instant::now();
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (wins, dict, next, done, top, maps) = (wins.clone(), dict.clone(), next.clone(), done.clone(), top.clone(), maps.clone());
        hs.push(std::thread::spawn(move || {
            let mut local: Vec<Cand> = Vec::new();
            let mut floor: u16 = 0;
            let mut keys: Vec<Vec<u8>> = (0..nm).map(|_| Vec::with_capacity(K)).collect();
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= total {
                    break;
                }
                let b = (a + CHUNK).min(total);
                for off in a..b {
                    let seed = lo + off as i64;
                    let raw = raw_n(g, seed, RK);
                    for &m in maps.iter() {
                        keys_from(g, &raw, m, &mut keys[m as usize], K);
                    }
                    for (wi, w) in wins.iter().enumerate() {
                        for v in maps.iter().flat_map(|&m| (0..8u8).map(move |sub| m * 8 + sub)) {
                            let (model, map, sign, atb) = variant_parts(v);
                            let s = decode_fast(w, &keys[map as usize], sign, atb, model, &dict);
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
                if d % (CHUNK * 256) < CHUNK {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} seeds) {:.0} seeds/s, eta {:.0} s", 100.0 * d as f64 / total as f64, d, rate,
                              (total as f64 - d as f64) / rate);
                }
            }
            local.sort_by(|x, y| y.score.cmp(&x.score));
            local.truncate(TOPK);
            top.lock().unwrap().extend(local);
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
    eprintln!("swept {} seeds in {:.0} s; best score {}", total, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score).unwrap_or(0));
}

fn mode_verify(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = load_windows(&args[0]);
    let dict = Dict::load(&args[1]);
    let seed: i64 = args[2].parse().unwrap();
    let w = wins.iter().find(|w| w.name == args[3]).expect("window");
    let map: u8 = args[4].parse().unwrap();
    let model: u8 = args[5].parse().unwrap();
    let sign: i32 = args[6].parse().unwrap();
    let atb = args[7] == "1";
    let raw = raw_n(g, seed, w.runes.len() * 9 + 200);
    let mut key = Vec::new();
    keys_from(g, &raw, map, &mut key, w.runes.len() * 3 + 50);
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

#[derive(Clone)]
struct BgCand {
    score: i32,
    seed: i64,
    win: u8,
    variant: u8,
}

/// bgsweep <gen> <windows.txt> <bigram.txt> <lo> <hi> <out.tsv> [threads]
/// Boundary-free score (decode_bg): the first 120 runes of every window (36 for the OEIS windows), no word separators involved.
fn mode_bgsweep(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = Arc::new(load_windows(&args[0]));
    let tbl = Arc::new(load_bigram(&args[1]));
    let lo: i64 = args[2].parse().unwrap();
    let hi: i64 = args[3].parse().unwrap();
    let out = args[4].clone();
    let threads: usize = if args.len() > 5 { args[5].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let next = Arc::new(AtomicU64::new(0));
    let done = Arc::new(AtomicU64::new(0));
    let top: Arc<Mutex<Vec<BgCand>>> = Arc::new(Mutex::new(Vec::new()));
    const CHUNK: u64 = 1 << 16;
    const TOPK: usize = 400;
    let total = (hi - lo) as u64;
    let nm = n_maps(g);
    let maps = Arc::new(sweep_maps(g));
    let t0 = Instant::now();
    let hist: Arc<Mutex<[u64; 64]>> = Arc::new(Mutex::new([0u64; 64]));
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (wins, tbl, next, done, top, hist, maps) =
            (wins.clone(), tbl.clone(), next.clone(), done.clone(), top.clone(), hist.clone(), maps.clone());
        hs.push(std::thread::spawn(move || {
            let mut local: Vec<BgCand> = Vec::new();
            let mut floor: i32 = -1000;
            let mut lh = [0u64; 64];
            let mut keys: Vec<Vec<u8>> = (0..nm).map(|_| Vec::with_capacity(K)).collect();
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= total {
                    break;
                }
                let b = (a + CHUNK).min(total);
                for off in a..b {
                    let seed = lo + off as i64;
                    let raw = raw_n(g, seed, RK);
                    for &m in maps.iter() {
                        keys_from(g, &raw, m, &mut keys[m as usize], K);
                    }
                    for (wi, w) in wins.iter().enumerate() {
                        for v in maps.iter().flat_map(|&m| (0..8u8).map(move |sub| m * 8 + sub)) {
                            let (model, map, sign, atb) = variant_parts(v);
                            let s = decode_bg(&w.runes, w.prev, &keys[map as usize], sign, atb, model, &tbl);
                            lh[((s + 400) / 20).clamp(0, 63) as usize] += 1;
                            if s > floor && s >= 0 {
                                local.push(BgCand { score: s, seed, win: wi as u8, variant: v });
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
                if d % (CHUNK * 256) < CHUNK {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} seeds) {:.0} seeds/s, eta {:.0} s", 100.0 * d as f64 / total as f64, d, rate,
                              (total as f64 - d as f64) / rate);
                }
            }
            local.sort_by(|x, y| y.score.cmp(&x.score));
            local.truncate(TOPK);
            top.lock().unwrap().extend(local);
            let mut h = hist.lock().unwrap();
            for i in 0..64 {
                h[i] += lh[i];
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
        writeln!(f, "{}\t{}\t{}\t{}\t{}\t{}\t{}", c.score, c.seed, wins[c.win as usize].name, model, map, sign, atb as u8).unwrap();
    }
    let h = hist.lock().unwrap();
    eprintln!("swept {} seeds in {:.0} s; best score {}", total, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score.to_string()).unwrap_or("none".into()));
    eprintln!("hist (bins of 20 from -400) {}", h.iter().enumerate().filter(|(_, c)| **c > 0).map(|(b, c)| format!("{b}:{c}")).collect::<Vec<_>>().join(" "));
}

/// bgscore <gen> <windows.txt> <bigram.txt> <seed> <map> <model> <sign> <atb>: the boundary-free score of one (seed, variant) on window 0 (for the tests)
fn mode_bgscore(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let a = &args_all[1..];
    let wins = load_windows(&a[0]);
    let tbl = load_bigram(&a[1]);
    let seed: i64 = a[2].parse().unwrap();
    let map: u8 = a[3].parse().unwrap();
    let model: u8 = a[4].parse().unwrap();
    let sign: i32 = a[5].parse().unwrap();
    let atb = a[6] == "1";
    let raw = raw_n(g, seed, RK);
    let mut keys = Vec::new();
    keys_from(g, &raw, map, &mut keys, K);
    println!("{}", decode_bg(&wins[0].runes, wins[0].prev, &keys, sign, atb, model, &tbl));
}

/// keys <gen> <seed> <map> <count>: the first `count` key values of one seed (reference for a GPU port: docs/GPU_PORT.md)
fn mode_keys(a: &[String]) {
    let g = parse_gen(&a[0]);
    let seed: i64 = a[1].parse().unwrap();
    let map: u8 = a[2].parse().unwrap();
    let count: usize = a[3].parse().unwrap();
    let raw = raw_n(g, seed, count * 3 + 64);
    let mut k = Vec::new();
    keys_from(g, &raw, map, &mut k, count);
    println!("{}", k.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("vectors") => mode_vectors(&args[2]),
        Some("keys") => mode_keys(&args[2..]),
        Some("plant") => mode_plant(&args[2..]),
        Some("sweep") => mode_sweep(&args[2..]),
        Some("verify") => mode_verify(&args[2..]),
        Some("bgsweep") => mode_bgsweep(&args[2..]),
        Some("bgscore") => mode_bgscore(&args[2..]),
        _ => eprintln!("usage: prngx vectors|keys|plant|sweep|bgsweep|bgscore|verify ... (see the header of src/main.rs)"),
    }
}
