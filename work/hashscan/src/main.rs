//! hashscan: keystreams derived from a passphrase by a hash, for a large candidate list (Dukotah's "derived-key
//! dictionary lane"). Companion to work/phpmt and work/prngx: same skip-aware decoder, same windows and dictionary.
//!
//! A candidate string s becomes a byte stream under one of these conventions (conv):
//!   0  H(s || ctr)  ctr = 4-byte big-endian counter from 0     1  H(s || ctr)  ctr = decimal ASCII from 0
//!   2  H(s || ctr)  ctr = decimal ASCII from 1                 3  chain: x0 = H(s), x(n+1) = H(x(n)); output x0 x1 ...
//! with H in {md5, sha1, sha256, sha512} (algo 0..3). Bytes become key values 0..28 by a map:
//!   0  b % 29     1  floor(b * 29 / 256)     2  bytes >= 232 rejected, then b % 29
//! Each (algo, conv, map) is decoded under model (0 skip, 1 coin), sign (+-1) and atbash (the phpmt variants), on the
//! windows of the windows file (use windows_07.txt: the key starts on LP2 page 0).
//!
//! Modes:
//!   sweep <cands.txt> <windows.txt> <dict.txt> <out.tsv> [threads] [algos=0,1,2,3] [convs=0,1,2,3]
//!   plant <algo> <conv> <map> <model> <sign> <atb> <keep> <candidate> <plain.txt> <out.txt>
//!   verify <algo> <conv> <map> <model> <sign> <atb> <candidate> <windows.txt> <dict.txt> <window>
//!   vectors            prints the first 40 bytes of every (algo, conv) stream for "cicada" (checked against Python)

use md5::Md5;
use sha1::Sha1;
use sha2::{Digest, Sha256, Sha512};
use std::env;
use std::fs;
use std::io::Write;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::{Arc, Mutex};
use std::time::Instant;

const K: usize = 160; // key values the fast decoder looks at
const MOD: i32 = 29;
const ALGOS: usize = 4;
const CONVS: usize = 4;
const MAPS: usize = 3;
const NEED: usize = 200; // stream bytes per candidate and convention (a map needs at most ~175 for 160 keys)


// ------------------------------------------------------------------ hash streams

fn hash_bytes(algo: usize, data: &[u8]) -> Vec<u8> {
    match algo {
        0 => Md5::digest(data).to_vec(),
        1 => Sha1::digest(data).to_vec(),
        2 => Sha256::digest(data).to_vec(),
        _ => Sha512::digest(data).to_vec(),
    }
}

/// First `count` bytes of the stream for candidate `s` under (algo, conv).
fn stream_bytes(algo: usize, conv: usize, s: &[u8], count: usize) -> Vec<u8> {
    let mut out: Vec<u8> = Vec::with_capacity(count + 64);
    let mut buf: Vec<u8> = Vec::with_capacity(s.len() + 16);
    match conv {
        3 => {
            let mut x = hash_bytes(algo, s);
            while out.len() < count {
                out.extend_from_slice(&x);
                x = hash_bytes(algo, &x);
            }
        }
        _ => {
            let mut ctr: u64 = if conv == 2 { 1 } else { 0 };
            while out.len() < count {
                buf.clear();
                buf.extend_from_slice(s);
                if conv == 0 {
                    buf.extend_from_slice(&(ctr as u32).to_be_bytes());
                } else {
                    buf.extend_from_slice(ctr.to_string().as_bytes());
                }
                out.extend_from_slice(&hash_bytes(algo, &buf));
                ctr += 1;
            }
        }
    }
    out.truncate(count);
    out
}

/// Key values from stream bytes under a map; at most `limit` keys.
fn keys_from(bytes: &[u8], map: usize, out: &mut Vec<u8>, limit: usize) {
    out.clear();
    for &b in bytes {
        if out.len() >= limit {
            break;
        }
        match map {
            0 => out.push(b % 29),
            1 => out.push(((b as u32 * 29) >> 8) as u8),
            _ => {
                if b < 232 {
                    out.push(b % 29);
                }
            }
        }
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


// ------------------------------------------------------------------ modes

fn parse_list(s: &str) -> Vec<usize> {
    s.split(',').map(|x| x.parse().unwrap()).collect()
}

fn mode_vectors() {
    for algo in 0..ALGOS {
        for conv in 0..CONVS {
            let b = stream_bytes(algo, conv, b"cicada", 40);
            println!("{} {} {}", algo, conv, b.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
        }
    }
}

fn lens_of(w: &Win) -> Vec<String> {
    let mut lens = Vec::new();
    let mut l = 0;
    for i in 0..w.runes.len() {
        l += 1;
        if w.word_end[i] {
            lens.push(l.to_string());
            l = 0;
        }
    }
    lens
}

fn mode_plant(a: &[String]) {
    let algo: usize = a[0].parse().unwrap();
    let conv: usize = a[1].parse().unwrap();
    let map: usize = a[2].parse().unwrap();
    let model: u8 = a[3].parse().unwrap();
    let sign: i32 = a[4].parse().unwrap();
    let atb = a[5] == "1";
    let keep: f64 = a[6].parse().unwrap();
    let cand = a[7].as_bytes();
    let wins = load_windows(&a[8]);
    let mut lcg: u64 = 0x2545F4914F6CDD1D ^ cand.len() as u64;
    let mut coin = || {
        lcg = lcg.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        (lcg >> 11) as f64 / (1u64 << 53) as f64
    };
    let mut out = String::new();
    for w in &wins {
        let need = w.runes.len() * 4 + 64;
        let bytes = stream_bytes(algo, conv, cand, need * 2 + 64);
        let mut key = Vec::new();
        keys_from(&bytes, map, &mut key, need);
        let (mut j, mut prev) = (0usize, -1i32);
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
                j += 1;
                if coin() >= keep {
                    y = md(t + sign * key[j] as i32);
                    j += 1;
                }
            }
            c.push(y as u8);
            prev = y;
        }
        out += &format!("W planted_{} -1\nR {}\nL {}\n", w.name,
                        c.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "), lens_of(w).join(" "));
    }
    fs::write(&a[9], out).unwrap();
}

fn mode_verify(a: &[String]) {
    let algo: usize = a[0].parse().unwrap();
    let conv: usize = a[1].parse().unwrap();
    let map: usize = a[2].parse().unwrap();
    let model: u8 = a[3].parse().unwrap();
    let sign: i32 = a[4].parse().unwrap();
    let atb = a[5] == "1";
    let cand = a[6].as_bytes();
    let wins = load_windows(&a[7]);
    let dict = Dict::load(&a[8]);
    let w = wins.iter().find(|w| w.name == a[9]).expect("window");
    let bytes = stream_bytes(algo, conv, cand, w.runes.len() * 9 + 200);
    let mut key = Vec::new();
    keys_from(&bytes, map, &mut key, w.runes.len() * 3 + 50);
    let (score, plain) = decode_full(w, &key, sign, atb, model, &dict);
    let mut txt = String::new();
    for (i, p) in plain.iter().enumerate() {
        txt += LATIN[*p as usize];
        if w.word_end[i] {
            txt.push(' ');
        }
    }
    println!("{:.3}\t{}\t{}", score, a[6], &txt[..txt.len().min(400)]);
}

#[derive(Clone)]
struct Cand {
    score: u16,
    idx: u32,
    win: u8,
    variant: u16,
}

/// variant = ((algo * CONVS + conv) * MAPS + map) * 8 + model * 4 + sign_idx * 2 + atb
fn variant_parts(v: u16) -> (usize, usize, usize, u8, i32, bool) {
    let sub = (v & 7) as u8;
    let rest = (v >> 3) as usize;
    let map = rest % MAPS;
    let conv = (rest / MAPS) % CONVS;
    let algo = rest / (MAPS * CONVS);
    (algo, conv, map, (sub >> 2) & 1, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1)
}

fn mode_sweep(args: &[String]) {
    let cands: Arc<Vec<String>> = Arc::new(
        fs::read_to_string(&args[0]).expect("candidate file").lines().filter(|l| !l.is_empty()).map(|l| l.to_string()).collect(),
    );
    let wins = Arc::new(load_windows(&args[1]));
    let dict = Arc::new(Dict::load(&args[2]));
    let out = args[3].clone();
    let threads: usize = if args.len() > 4 { args[4].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let mut algos: Vec<usize> = (0..ALGOS).collect();
    let mut convs: Vec<usize> = (0..CONVS).collect();
    for extra in args.iter().skip(5) {
        if let Some(v) = extra.strip_prefix("algos=") {
            algos = parse_list(v);
        }
        if let Some(v) = extra.strip_prefix("convs=") {
            convs = parse_list(v);
        }
    }
    let (algos, convs) = (Arc::new(algos), Arc::new(convs));
    let next = Arc::new(AtomicUsize::new(0));
    let done = Arc::new(AtomicUsize::new(0));
    let top: Arc<Mutex<Vec<Cand>>> = Arc::new(Mutex::new(Vec::new()));
    const CHUNK: usize = 4096;
    const TOPK: usize = 400;
    let total = cands.len();
    let t0 = Instant::now();
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (cands, wins, dict, algos, convs, next, done, top) =
            (cands.clone(), wins.clone(), dict.clone(), algos.clone(), convs.clone(), next.clone(), done.clone(), top.clone());
        hs.push(std::thread::spawn(move || {
            let mut local: Vec<Cand> = Vec::new();
            let mut floor: u16 = 0;
            let mut keys = Vec::with_capacity(K);
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= total {
                    break;
                }
                let b = (a + CHUNK).min(total);
                for idx in a..b {
                    let s = cands[idx].as_bytes();
                    for &algo in algos.iter() {
                        for &conv in convs.iter() {
                            let bytes = stream_bytes(algo, conv, s, NEED);
                            for map in 0..MAPS {
                                keys_from(&bytes, map, &mut keys, K);
                                for (wi, w) in wins.iter().enumerate() {
                                    for sub in 0..8u16 {
                                        let (model, sign, atb) = ((sub >> 2 & 1) as u8, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1);
                                        let sc = decode_fast(w, &keys, sign, atb, model, &dict);
                                        if sc > floor || (local.len() < TOPK && sc > 0) {
                                            let variant = (((algo * CONVS + conv) * MAPS + map) as u16) * 8 + sub;
                                            local.push(Cand { score: sc, idx: idx as u32, win: wi as u8, variant });
                                            if local.len() >= 2 * TOPK {
                                                local.sort_by(|x, y| y.score.cmp(&x.score));
                                                local.truncate(TOPK);
                                                floor = local[TOPK - 1].score;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                let d = done.fetch_add(b - a, Ordering::Relaxed) + (b - a);
                if (d / CHUNK) % 256 == 0 {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} candidates) {:.0} cand/s, eta {:.0} s", 100.0 * d as f64 / total as f64, d, rate,
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
    writeln!(f, "score\tcandidate\twindow\talgo\tconv\tmap\tmodel\tsign\tatbash").unwrap();
    for c in &all {
        let (algo, conv, map, model, sign, atb) = variant_parts(c.variant);
        writeln!(f, "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}", c.score, cands[c.idx as usize], wins[c.win as usize].name, algo, conv,
                 map, model, sign, atb as u8)
            .unwrap();
    }
    eprintln!("swept {} candidates in {:.0} s; best score {}", total, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score).unwrap_or(0));
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("vectors") => mode_vectors(),
        Some("plant") => mode_plant(&args[2..]),
        Some("sweep") => mode_sweep(&args[2..]),
        Some("verify") => mode_verify(&args[2..]),
        _ => eprintln!("usage: hashscan vectors|plant|sweep|verify ... (see the header of src/main.rs)"),
    }
}
