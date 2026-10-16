//! kscreen: a language- and alphabet-agnostic keystream screen for LP2 under the anti-repeat rule.
//!
//! Hypothesis tested for each (keystream, start offset, key multiplier m, anti-repeat model):
//!
//!     c_i = D(p_i) + m * k_{j_i} + b   (mod 29)
//!
//! for ANY fixed substitution D of the plaintext alphabet (identity, Atbash, a mixed alphabet), any constant
//! shift b, and a plaintext in ANY natural language. The key pointer j_i runs ahead of the rune index at
//! anti-repeat events:
//!   model 0 (skip): when c_i would equal c_{i-1}, the encryptor usually moves on to the next key value
//!                   (a missed check keeps the doublet);
//!   model 1 (coin): on a collision one key value is spent as a coin, then the doublet is kept or a fresh
//!                   key value is used.
//! The decoder keeps a beam of key pointers (states merged on the pointer; the future depends only on it)
//! and scores the decoded letters by their index of coincidence. None of D, b, Atbash or the language
//! changes the IoC, so one run covers all of them. English rune text gives ~1.75; a wrong key gives
//! 1.00 +- 0.025 at 300 runes.
//!
//! Modes:
//!   screen <windows.txt> <family> <out.tsv> [n=300] [beam=16] [mults=1,28|all|a,b,..] [models=0,1]
//!          [threads=T] [top=2000] [abort=150:1.2|0] [only=<item>] [items=a:b] [minlen=50]
//!   plant  <plain_windows.txt> <family> <item> <offset> <mult> <model> <keep> <seed> <subst 0|1> <out.txt>
//!   verify <windows.txt> <family> <item> <offset> <mult> <model> <window|all> [n=0] [beam=64] [controls=K]
//!          (controls=K also decodes K random offsets of the same keystream: a keystream-matched null)
//!   info   <family>
//!
//! Families:
//!   file:<path.ksb>      keystreams written by export.py (binary "KSB1"); offsets 0..len-need
//!   rand:<count>:<seed>  i.i.d. uniform keystreams of length 20000 (null controls)
//!   lin:<d>              every linear recurrence x_n = a_1 x_{n-1} + .. + a_d x_{n-d} mod 29 with a_d != 0;
//!                        offsets = every nonzero start state, i.e. every phase of every sequence
//!   poly:<d>             k_n = a_1 n + .. + a_d n^d mod 29 for every nonzero coefficient vector; offsets 0..28
//! For lin and poly the multiplier is redundant (scaled sequences are in the family), so use mults=1.

use std::env;
use std::fs;
use std::io::{BufWriter, Write};
use std::sync::Mutex;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::time::Instant;

const Q: usize = 29;
const HBINS: usize = 400; // IoC histogram, bins of 0.01 over [0, 4)

// ------------------------------------------------------------------ inputs

struct Win {
    name: String,
    prev: i32,
    runes: Vec<u8>,
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
            out.push(Win { name, prev, runes: Vec::new(), lens: String::new() });
        } else if let Some(rest) = line.strip_prefix("R ") {
            let w = out.last_mut().expect("R line before W line");
            w.runes = rest.split_whitespace().map(|x| x.parse::<u8>().expect("rune")).collect();
        } else if let Some(rest) = line.strip_prefix("L ") {
            out.last_mut().expect("L line before W line").lens = rest.to_string();
        }
    }
    for w in &out {
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

/// splitmix64: controls, plant coins and substitutions (not a hypothesis generator)
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

// ------------------------------------------------------------------ keystream families

enum Fam {
    Ks(Vec<Ks>),
    Lin(usize),
    Poly(usize),
}

fn pow29(e: usize) -> usize {
    (0..e).fold(1, |a, _| a * Q)
}

fn join<T: ToString>(v: &[T]) -> String {
    v.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(",")
}

impl Fam {
    fn parse(spec: &str) -> Fam {
        let (kind, arg) = spec.split_once(':').unwrap_or((spec, ""));
        match kind {
            "file" => Fam::Ks(load_ksb(arg)),
            "rand" => {
                let (cnt, seed) = arg.split_once(':').unwrap_or((arg, "1"));
                let cnt: usize = cnt.parse().expect("rand:<count>:<seed>");
                let mut r = Rng(seed.parse::<u64>().expect("rand seed") ^ 0x05EE_D5EE_D5EE_D5EE);
                Fam::Ks(
                    (0..cnt)
                        .map(|i| Ks { name: format!("RANDOM {i}"), v: (0..20000).map(|_| r.below(Q as u64) as u8).collect() })
                        .collect(),
                )
            }
            "lin" => {
                let d: usize = arg.parse().expect("lin:<order>");
                assert!((1..=4).contains(&d), "order 1..4");
                Fam::Lin(d)
            }
            "poly" => {
                let d: usize = arg.parse().expect("poly:<degree>");
                assert!((1..=4).contains(&d), "degree 1..4");
                Fam::Poly(d)
            }
            _ => panic!("unknown family {spec}: use file:<path> rand:<count>:<seed> lin:<order> poly:<degree>"),
        }
    }

    fn items(&self) -> usize {
        match self {
            Fam::Ks(v) => v.len(),
            Fam::Lin(d) => 28 * pow29(d - 1),
            Fam::Poly(d) => pow29(*d) - 1,
        }
    }

    fn offsets(&self, item: usize, need: usize) -> usize {
        match self {
            Fam::Ks(v) => (v[item].v.len() + 1).saturating_sub(need),
            Fam::Lin(d) => pow29(*d) - 1,
            Fam::Poly(_) => Q,
        }
    }

    /// lin: (a_1..a_d), a_d != 0; poly: (a_1..a_d) != 0
    fn coeffs(&self, item: usize) -> Vec<usize> {
        match self {
            Fam::Lin(d) => {
                let mut a = vec![0; *d];
                a[d - 1] = item % 28 + 1;
                let mut x = item / 28;
                for e in 0..d - 1 {
                    a[e] = x % Q;
                    x /= Q;
                }
                a
            }
            Fam::Poly(d) => {
                let mut a = vec![0; *d];
                let mut x = item + 1;
                for e in 0..*d {
                    a[e] = x % Q;
                    x /= Q;
                }
                a
            }
            Fam::Ks(_) => vec![],
        }
    }

    fn item_name(&self, item: usize) -> String {
        match self {
            Fam::Ks(v) => v[item].name.clone(),
            Fam::Lin(d) => format!("lin{d}:{}", join(&self.coeffs(item))),
            Fam::Poly(d) => format!("poly{d}:{}", join(&self.coeffs(item))),
        }
    }

    fn find_item(&self, name: &str) -> usize {
        (0..self.items()).find(|&i| self.item_name(i) == name).unwrap_or_else(|| panic!("no keystream named {name:?}"))
    }

    /// lin offsets are start states x_0..x_{d-1} (base-29 digits of offset+1)
    fn offset_name(&self, off: usize) -> String {
        match self {
            Fam::Lin(d) => {
                let mut x = off + 1;
                let mut s = Vec::new();
                for _ in 0..*d {
                    s.push(x % Q);
                    x /= Q;
                }
                format!("state={}", join(&s))
            }
            _ => off.to_string(),
        }
    }

    fn parse_offset(&self, s: &str) -> usize {
        let s = s.trim_start_matches("state=");
        match self {
            Fam::Lin(d) if s.contains(',') => {
                let digits: Vec<usize> = s.split(',').map(|x| x.parse().expect("state digit")).collect();
                assert_eq!(digits.len(), *d, "state needs {d} digits");
                digits.iter().rev().fold(0, |a, &x| a * Q + x) - 1
            }
            _ => s.parse().expect("offset"),
        }
    }

    fn fill(&self, item: usize, coeffs: &[usize], off: usize, buf: &mut [u8]) {
        match self {
            Fam::Ks(v) => buf.copy_from_slice(&v[item].v[off..off + buf.len()]),
            Fam::Lin(d) => {
                let d = *d;
                let mut x = off + 1;
                for e in 0..d.min(buf.len()) {
                    buf[e] = (x % Q) as u8;
                    x /= Q;
                }
                for n in d..buf.len() {
                    let mut s = 0usize;
                    for e in 1..=d {
                        s += coeffs[e - 1] * buf[n - e] as usize;
                    }
                    buf[n] = (s % Q) as u8;
                }
            }
            Fam::Poly(d) => {
                for (j, b) in buf.iter_mut().enumerate() {
                    let n = (off + j) % Q;
                    let (mut s, mut pw) = (0usize, 1usize);
                    for e in 0..*d {
                        pw = pw * n % Q;
                        s += coeffs[e] * pw;
                    }
                    *b = (s % Q) as u8;
                }
            }
        }
    }
}

// ------------------------------------------------------------------ decoder

#[derive(Clone, Copy)]
struct St {
    j: u32,
    s: u32,
    cnt: [u16; Q],
}

struct Tb {
    sub: [[u8; Q]; Q], // sub[c][k] = c - k mod 29
    add: [[u8; Q]; Q], // add[t][k] = t + k mod 29
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

#[inline]
fn take(st: &mut St, t: u8, nj: usize) {
    let x = t as usize;
    st.s += 2 * st.cnt[x] as u32;
    st.cnt[x] += 1;
    st.j = nj as u32;
}

/// Beam decode of c[0..n] with additive key values mk (already multiplied). Returns (best coincidence
/// pair count sum n_x(n_x-1), runes used). Aborts at `abort_at` runes when the best count is below `abort_s`.
#[allow(clippy::too_many_arguments)]
fn ioc_beam(
    c: &[u8],
    prev0: i32,
    mk: &[u8],
    model: u8,
    n: usize,
    beam: usize,
    abort_at: usize,
    abort_s: u32,
    tb: &Tb,
    cur: &mut Vec<St>,
    extra: &mut Vec<St>,
) -> (u32, usize) {
    cur.clear();
    cur.push(St { j: 0, s: 0, cnt: [0; Q] });
    let klen = mk.len();
    for i in 0..n {
        let ci = c[i] as usize;
        let prev: i32 = if i == 0 { prev0 } else { c[i - 1] as i32 };
        extra.clear();
        let mut idx = 0;
        while idx < cur.len() {
            let j = cur[idx].j as usize;
            if j + 3 > klen {
                cur.swap_remove(idx);
                continue;
            }
            let k0 = mk[j] as usize;
            if prev >= 0 {
                let pv = prev as u8;
                if model == 0 {
                    let k1 = mk[j + 1] as usize;
                    let t1 = tb.sub[ci][k1];
                    if tb.add[t1 as usize][k0] == pv {
                        let mut s2 = cur[idx];
                        take(&mut s2, t1, j + 2);
                        extra.push(s2);
                    }
                    let k2 = mk[j + 2] as usize;
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv && tb.add[t2 as usize][k1] == pv {
                        let mut s3 = cur[idx];
                        take(&mut s3, t2, j + 3);
                        extra.push(s3);
                    }
                } else {
                    let k2 = mk[j + 2] as usize;
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv {
                        let mut s3 = cur[idx];
                        take(&mut s3, t2, j + 3);
                        extra.push(s3);
                    }
                }
            }
            let nj = if model == 1 && prev == ci as i32 { j + 2 } else { j + 1 };
            take(&mut cur[idx], tb.sub[ci][k0], nj);
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
                    if cur[b].j == cur[a].j {
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
                cur.sort_unstable_by(|x, y| y.s.cmp(&x.s));
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

fn ioc_of(s: u32, n: usize) -> f64 {
    if n < 2 { 0.0 } else { Q as f64 * s as f64 / (n as f64 * (n as f64 - 1.0)) }
}

/// Full decode for verification: like ioc_beam (no abort) but keeps each state's plaintext and pointers.
fn full_decode(c: &[u8], prev0: i32, mk: &[u8], model: u8, n: usize, beam: usize) -> (f64, Vec<u8>, Vec<u32>) {
    #[derive(Clone)]
    struct S2 {
        j: usize,
        s: u32,
        cnt: [u16; Q],
        plain: Vec<u8>,
        ptr: Vec<u32>,
    }
    let tb = tables();
    let mut cur = vec![S2 { j: 0, s: 0, cnt: [0; Q], plain: Vec::new(), ptr: Vec::new() }];
    let step = |st: &S2, t: u8, at: usize, nj: usize| -> S2 {
        let mut x = st.clone();
        x.s += 2 * x.cnt[t as usize] as u32;
        x.cnt[t as usize] += 1;
        x.plain.push(t);
        x.ptr.push(at as u32);
        x.j = nj;
        x
    };
    for i in 0..n {
        let ci = c[i] as usize;
        let prev: i32 = if i == 0 { prev0 } else { c[i - 1] as i32 };
        let mut next: Vec<S2> = Vec::new();
        for st in &cur {
            let j = st.j;
            if j + 3 > mk.len() {
                continue;
            }
            let k0 = mk[j] as usize;
            let nj = if model == 1 && prev == ci as i32 { j + 2 } else { j + 1 };
            next.push(step(st, tb.sub[ci][k0], j, nj));
            if prev >= 0 {
                let pv = prev as u8;
                let k1 = mk[j + 1] as usize;
                let k2 = mk[j + 2] as usize;
                if model == 0 {
                    let t1 = tb.sub[ci][k1];
                    if tb.add[t1 as usize][k0] == pv {
                        next.push(step(st, t1, j + 1, j + 2));
                    }
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv && tb.add[t2 as usize][k1] == pv {
                        next.push(step(st, t2, j + 2, j + 3));
                    }
                } else {
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv {
                        next.push(step(st, t2, j + 2, j + 3));
                    }
                }
            }
        }
        next.sort_by(|a, b| a.j.cmp(&b.j).then(b.s.cmp(&a.s)));
        next.dedup_by(|b, a| a.j == b.j);
        next.sort_by(|a, b| b.s.cmp(&a.s));
        next.truncate(beam);
        if next.is_empty() {
            break;
        }
        cur = next;
    }
    let best = cur.into_iter().max_by_key(|s| s.s).unwrap();
    let used = best.plain.len();
    (ioc_of(best.s, used), best.plain, best.ptr)
}

// ------------------------------------------------------------------ options

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
    if s == "all" { (1..Q as u8).collect() } else { s.split(',').map(|x| x.parse().expect("number")).collect() }
}

// ------------------------------------------------------------------ screen

#[derive(Clone, Copy)]
struct Hit {
    ioc: f32,
    item: u32,
    off: u32,
    mult: u8,
    model: u8,
    win: u16,
    n: u16,
}

fn keep_top(v: &mut Vec<Hit>, top: usize) {
    v.sort_unstable_by(|a, b| b.ioc.partial_cmp(&a.ioc).unwrap());
    v.truncate(top);
}

fn mode_screen(args: &[String]) {
    if args.len() < 3 {
        eprintln!("usage: screen <windows.txt> <family> <out.tsv> [key=value ...]");
        std::process::exit(2);
    }
    let all_wins = load_windows(&args[0]);
    let fam = Fam::parse(&args[1]);
    let out_path = &args[2];
    let o = opts(&args[3..]);
    let n_req: usize = get(&o, "n", 300);
    let beam: usize = get(&o, "beam", 16);
    let mults = list_u8(&get(&o, "mults", "1,28".to_string()));
    let models = list_u8(&get(&o, "models", "0,1".to_string()));
    let threads: usize = get(&o, "threads", std::thread::available_parallelism().map(|x| x.get()).unwrap_or(4));
    let top: usize = get(&o, "top", 2000);
    let minlen: usize = get(&o, "minlen", 50);
    let abort_spec: String = get(&o, "abort", "150:1.2".to_string());
    let (abort_at, abort_ioc) = if abort_spec == "0" {
        (0usize, 0.0f64)
    } else {
        let (a, b) = abort_spec.split_once(':').expect("abort=<runes>:<ioc>");
        (a.parse().expect("abort runes"), b.parse().expect("abort ioc"))
    };
    let abort_s = (abort_ioc * abort_at as f64 * (abort_at as f64 - 1.0) / Q as f64).ceil() as u32;
    assert!(models.iter().all(|&m| m <= 1), "models are 0 (skip) and 1 (coin)");
    assert!(mults.iter().all(|&m| m >= 1 && (m as usize) < Q), "multipliers 1..28");

    let wins: Vec<&Win> = all_wins.iter().filter(|w| w.runes.len() >= minlen).collect();
    let wn: Vec<usize> = wins.iter().map(|w| w.runes.len().min(n_req)).collect();
    let nmax = *wn.iter().max().expect("no windows");
    let need = nmax + nmax / 4 + 8;
    let items: Vec<usize> = if let Some(name) = o.get("only") {
        vec![fam.find_item(name)]
    } else if let Some(r) = o.get("items") {
        let (a, b) = r.split_once(':').expect("items=a:b");
        let a: usize = a.parse().unwrap();
        let b: usize = b.parse::<usize>().unwrap().min(fam.items());
        (a..b).collect()
    } else {
        (0..fam.items()).collect()
    };
    let total_runs: u64 = items.iter().map(|&it| fam.offsets(it, need) as u64).sum::<u64>()
        * (mults.len() * models.len() * wins.len()) as u64;
    eprintln!(
        "kscreen: {} items, {} windows (n<={}), mults {:?}, models {:?}, {} decodes, {} threads",
        items.len(),
        wins.len(),
        nmax,
        mults,
        models,
        total_runs,
        threads
    );

    let t0 = Instant::now();
    let next = AtomicUsize::new(0);
    let done_runs = AtomicUsize::new(0);
    let merged: Mutex<(Vec<Hit>, Vec<u64>, Vec<Hit>, u64, u64)> = Mutex::new((
        Vec::new(),
        vec![0u64; HBINS],
        vec![Hit { ioc: 0.0, item: 0, off: 0, mult: 0, model: 0, win: 0, n: 0 }; wins.len()],
        0,
        0,
    ));
    std::thread::scope(|sc| {
        for tid in 0..threads {
            let (fam, items, wins, wn, mults, models) = (&fam, &items, &wins, &wn, &mults, &models);
            let (next, done_runs, merged) = (&next, &done_runs, &merged);
            sc.spawn(move || {
                let tb = tables();
                let mut cur: Vec<St> = Vec::with_capacity(64);
                let mut extra: Vec<St> = Vec::with_capacity(64);
                let mut key = vec![0u8; need];
                let mut mk = vec![0u8; need];
                let mut hits: Vec<Hit> = Vec::new();
                let mut hist = vec![0u64; HBINS];
                let mut wbest = vec![Hit { ioc: 0.0, item: 0, off: 0, mult: 0, model: 0, win: 0, n: 0 }; wins.len()];
                let (mut runs, mut aborted) = (0u64, 0u64);
                let mut last = Instant::now();
                loop {
                    let k = next.fetch_add(1, Ordering::Relaxed);
                    if k >= items.len() {
                        break;
                    }
                    let item = items[k];
                    let coeffs = fam.coeffs(item);
                    let noff = fam.offsets(item, need);
                    for off in 0..noff {
                        fam.fill(item, &coeffs, off, &mut key);
                        for &m in mults.iter() {
                            for (a, b) in mk.iter_mut().zip(key.iter()) {
                                *a = ((*b as usize * m as usize) % Q) as u8;
                            }
                            for &model in models.iter() {
                                for (wi, w) in wins.iter().enumerate() {
                                    let n = wn[wi];
                                    let ab = if abort_at > 0 && abort_at < n { abort_at } else { 0 };
                                    let (s, used) =
                                        ioc_beam(&w.runes, w.prev, &mk, model, n, beam, ab, abort_s, &tb, &mut cur, &mut extra);
                                    let ioc = ioc_of(s, used) as f32;
                                    runs += 1;
                                    if used < n {
                                        aborted += 1;
                                    }
                                    hist[((ioc * 100.0) as usize).min(HBINS - 1)] += 1;
                                    let h = Hit { ioc, item: item as u32, off: off as u32, mult: m, model, win: wi as u16, n: used as u16 };
                                    if used == n && ioc > wbest[wi].ioc {
                                        wbest[wi] = h;
                                    }
                                    if used == n && (hits.len() < top || ioc > hits[top - 1].ioc) {
                                        hits.push(h);
                                        if hits.len() >= 2 * top {
                                            keep_top(&mut hits, top);
                                        }
                                    }
                                }
                            }
                        }
                    }
                    let per_item = noff * mults.len() * models.len() * wins.len();
                    let d = done_runs.fetch_add(per_item, Ordering::Relaxed) + per_item;
                    if tid == 0 && last.elapsed().as_secs() >= 20 {
                        last = Instant::now();
                        let el = t0.elapsed().as_secs_f64();
                        let frac = d as f64 / total_runs.max(1) as f64;
                        eprintln!(
                            "{:6.2}% ({} decodes) {:.0} decodes/s, eta {:.0} s",
                            100.0 * frac,
                            d,
                            d as f64 / el,
                            el * (1.0 - frac) / frac.max(1e-9)
                        );
                    }
                }
                keep_top(&mut hits, top);
                let mut g = merged.lock().unwrap();
                g.0.extend(hits);
                for (a, b) in g.1.iter_mut().zip(hist.iter()) {
                    *a += b;
                }
                for (a, b) in g.2.iter_mut().zip(wbest.iter()) {
                    if b.ioc > a.ioc {
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
    let f = fs::File::create(out_path).unwrap_or_else(|e| panic!("{out_path}: {e}"));
    let mut f = BufWriter::new(f);
    writeln!(
        f,
        "# kscreen screen family={} windows={} n={} beam={} mults={} models={} abort={} runs={} aborted={} secs={:.0}",
        args[1],
        args[0],
        nmax,
        beam,
        join(&mults),
        join(&models),
        abort_spec,
        runs,
        aborted,
        secs
    )
    .unwrap();
    let best = hits.first().map(|h| h.ioc).unwrap_or(0.0);
    writeln!(f, "# best {:.4}", best).unwrap();
    for (wi, h) in wbest.iter().enumerate() {
        writeln!(
            f,
            "# window {} best {:.4} item={} offset={} mult={} model={}",
            wins[wi].name,
            h.ioc,
            if h.ioc > 0.0 { fam.item_name(h.item as usize) } else { "-".into() },
            fam.offset_name(h.off as usize),
            h.mult,
            h.model
        )
        .unwrap();
    }
    let hs: Vec<String> = hist.iter().enumerate().filter(|(_, c)| **c > 0).map(|(b, c)| format!("{:.2}:{}", b as f64 / 100.0, c)).collect();
    writeln!(f, "# hist {}", hs.join(" ")).unwrap();
    writeln!(f, "ioc\titem\toffset\tmult\tmodel\twindow\tn").unwrap();
    for h in &hits {
        writeln!(
            f,
            "{:.4}\t{}\t{}\t{}\t{}\t{}\t{}",
            h.ioc,
            fam.item_name(h.item as usize),
            fam.offset_name(h.off as usize),
            h.mult,
            h.model,
            wins[h.win as usize].name,
            h.n
        )
        .unwrap();
    }
    eprintln!("kscreen: {runs} decodes ({aborted} aborted early) in {secs:.0} s; best IoC {best:.4}; wrote {out_path}");
}

// ------------------------------------------------------------------ plant / verify / info

fn mode_plant(args: &[String]) {
    if args.len() < 10 {
        eprintln!("usage: plant <plain_windows.txt> <family> <item> <offset> <mult> <model> <keep> <seed> <subst 0|1> <out.txt>");
        std::process::exit(2);
    }
    let wins = load_windows(&args[0]);
    let fam = Fam::parse(&args[1]);
    let item = fam.find_item(&args[2]);
    let off0 = fam.parse_offset(&args[3]);
    let m: usize = args[4].parse().expect("mult");
    let model: u8 = args[5].parse().expect("model");
    let keep: f64 = args[6].parse().expect("keep");
    let mut rng = Rng(args[7].parse::<u64>().expect("seed") ^ 0x0123_4567_89AB_CDEF);
    let subst = args[8] == "1";
    let mut d: Vec<u8> = (0..Q as u8).collect();
    if subst {
        for i in (1..Q).rev() {
            let j = rng.below(i as u64 + 1) as usize;
            d.swap(i, j);
        }
    }
    let coeffs = fam.coeffs(item);
    let mut out = String::new();
    for (wi, w) in wins.iter().enumerate() {
        let len = w.runes.len() * 4 + 64;
        let noff = fam.offsets(item, len);
        assert!(noff > 0, "keystream too short to plant");
        let off = (off0 + 997 * wi) % noff;
        let mut key = vec![0u8; len];
        fam.fill(item, &coeffs, off, &mut key);
        let mk: Vec<usize> = key.iter().map(|&k| k as usize * m % Q).collect();
        let (mut j, mut prev, mut c) = (0usize, -1i32, Vec::with_capacity(w.runes.len()));
        for &p in &w.runes {
            let t = d[p as usize] as usize;
            let mut y = ((t + mk[j]) % Q) as i32;
            j += 1;
            if model == 0 {
                let mut tries = 0;
                while prev >= 0 && y == prev && rng.unit() >= keep && tries < 5 {
                    y = ((t + mk[j]) % Q) as i32;
                    j += 1;
                    tries += 1;
                }
            } else if prev >= 0 && y == prev {
                j += 1; // the coin
                if rng.unit() >= keep {
                    y = ((t + mk[j]) % Q) as i32;
                    j += 1;
                }
            }
            c.push(y as u8);
            prev = y;
        }
        out += &format!(
            "# truth plant_{wi} item={} offset={} mult={m} model={model} keep={keep} subst={}\nW plant_{wi} -1\nR {}\nL {}\n",
            fam.item_name(item),
            fam.offset_name(off),
            subst as u8,
            c.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "),
            w.lens
        );
    }
    fs::write(&args[9], out).unwrap_or_else(|e| panic!("{}: {e}", args[9]));
}

fn mode_verify(args: &[String]) {
    if args.len() < 7 {
        eprintln!("usage: verify <windows.txt> <family> <item> <offset> <mult> <model> <window|all> [n=0] [beam=64]");
        std::process::exit(2);
    }
    let wins = load_windows(&args[0]);
    let fam = Fam::parse(&args[1]);
    let item = fam.find_item(&args[2]);
    let off = fam.parse_offset(&args[3]);
    let m: usize = args[4].parse().expect("mult");
    let model: u8 = args[5].parse().expect("model");
    let o = opts(&args[7..]);
    let n_req: usize = get(&o, "n", 0);
    let beam: usize = get(&o, "beam", 64);
    let coeffs = fam.coeffs(item);
    for w in wins.iter().filter(|w| args[6] == "all" || w.name == args[6]) {
        let n = if n_req == 0 { w.runes.len() } else { n_req.min(w.runes.len()) };
        let len = n + n / 4 + 16;
        let noff = fam.offsets(item, len);
        if off >= noff {
            println!("window {} skipped: keystream too short for offset {off}", w.name);
            continue;
        }
        let mut key = vec![0u8; len];
        fam.fill(item, &coeffs, off, &mut key);
        let mk: Vec<u8> = key.iter().map(|&k| (k as usize * m % Q) as u8).collect();
        let (ioc, plain, ptr) = full_decode(&w.runes, w.prev, &mk, model, n, beam);
        let skips = ptr.windows(2).filter(|p| p[1] != p[0] + 1).count();
        println!("window {} n {} ioc {:.4} pointer_jumps {}", w.name, plain.len(), ioc, skips);
        println!("plain {}", join(&plain));
        println!("ptr {}", join(&ptr));
        // keystream-matched null: the same keystream, multiplier and model at random offsets on this window.
        // A structured (e.g. short-period) keystream can let the beam overfit; a real hit must beat this.
        let nctl: usize = get(&o, "controls", 0);
        if nctl > 0 {
            let mut rng = Rng(0xC0FFEE ^ off as u64);
            let mut vals = Vec::with_capacity(nctl);
            for _ in 0..nctl {
                let co = rng.below(noff as u64) as usize;
                fam.fill(item, &coeffs, co, &mut key);
                let cmk: Vec<u8> = key.iter().map(|&k| (k as usize * m % Q) as u8).collect();
                vals.push(full_decode(&w.runes, w.prev, &cmk, model, n, beam).0);
            }
            let mx = vals.iter().cloned().fold(0.0f64, f64::max);
            let mean = vals.iter().sum::<f64>() / vals.len() as f64;
            println!("controls {} random offsets: mean {:.4} max {:.4}", nctl, mean, mx);
        }
    }
}

fn mode_info(args: &[String]) {
    let fam = Fam::parse(&args[0]);
    let n = fam.items();
    println!("items {n}");
    for i in 0..n.min(20) {
        println!("  {} offsets(need 400)={}", fam.item_name(i), fam.offsets(i, 400));
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        eprintln!("modes: screen | plant | verify | info  (see the header of src/main.rs)");
        std::process::exit(2);
    }
    let rest = &args[2..];
    match args[1].as_str() {
        "screen" => mode_screen(rest),
        "plant" => mode_plant(rest),
        "verify" => mode_verify(rest),
        "info" => mode_info(rest),
        m => {
            eprintln!("unknown mode {m}");
            std::process::exit(2);
        }
    }
}
