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
//!          [threads=T] [top=2000] [abort=150:1.2|0] [only=<item>] [items=a:b] [minlen=50] [dir=back]
//!          [nulledge=0|1|2]
//!   trace  <windows.txt> <family> <out.txt> [same options as screen] [offs=a:b]
//!          (one line per decode, for the decode-by-decode comparison with the GPU port)
//!   plant  <plain_windows.txt> <family> <item> <offset> <mult> <model> <keep> <seed> <subst 0|1> <out.txt>
//!   verify <windows.txt> <family> <item> <offset> <mult> <model> <window|all> [n=0] [beam=64] [controls=K]
//!          [nulledge=0|1|2]
//!          (controls=K also decodes K random offsets of the same keystream: a keystream-matched null)
//!   info   <family>
//!
//! nulledge=1|2 (docs: work/kscreen/NULLEDGE.md; the keyless word-edge null of NEGATIVE_SPACE.md blind spot 9):
//! the word edges come from the window's L line, which lists the CIPHERTEXT word lengths (a null adds a rune,
//! so a nulled word's L entry includes it). Every word-FINAL (1) or word-INITIAL (2) rune is a keyless null:
//! it is NOT scored, it does NOT advance the key pointer, and it is invisible to the anti-repeat prev chain
//! (the next rune's collision check compares against the last scored rune). This tests the "null at every word
//! edge" variant; the ~42%-of-words mixture is NOT testable by a single-window IoC screen (NULLEDGE.md,
//! measured). A window whose L line is missing, whose lengths do not sum to its rune count, or that carries a
//! P line (per-position prev values) gets no null positions and decodes exactly as with nulledge=0. nulledge=0
//! runs the untouched original code path, byte-identical to before.
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
use std::sync::atomic::{AtomicBool, AtomicUsize, Ordering};
use std::time::Instant;

const Q: usize = 29;

/// dir=back: the key runs BACKWARD through the text (read from the end) while the encryptor still works front to back.
/// Decoding then follows the text with a forward pointer into the reversed key; since a re-draw uses a LOWER key index,
/// in pointer order the used key comes first and the colliding draws follow it (the opposite of the forward model).
static BACK: AtomicBool = AtomicBool::new(false);

/// clock=<kind> (docs/HYPOTHESES.md H3): after enciphering a rune the key pointer moves on by g instead of 1, where g is
/// read from the cipher rune c (c1: 1 + index, cp: its Gematria prime, ct: prime - 1) or from the deciphered rune t
/// (p1, pp, pt; t is the plaintext only if no substitution or shift was applied). Anti-repeat draws still take the
/// next key value; only the final step after a rune is clocked. Not supported with dir=back or by gpu.py.
static CLOCK: AtomicUsize = AtomicUsize::new(0);
const CLOCKS: [&str; 7] = ["none", "c1", "cp", "ct", "p1", "pp", "pt"];
const GP: [usize; 29] = [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97, 101, 103, 107, 109];

/// nulledge=0|1|2: 0 off (the untouched decode); 1 = each word-FINAL rune (per the window's L line) is a
/// candidate keyless null; 2 = each word-INITIAL rune. See `null_positions` and NULLEDGE.md for the semantics.
static NULLEDGE: AtomicUsize = AtomicUsize::new(0);

fn set_clock(o: &std::collections::HashMap<String, String>) {
    let k = o.get("clock").map_or(0, |c| CLOCKS.iter().position(|x| x == c).unwrap_or_else(|| panic!("clock={c}: use {CLOCKS:?}")));
    assert!(k == 0 || !BACK.load(Ordering::Relaxed), "clock= is not supported with dir=back");
    CLOCK.store(k, Ordering::Relaxed);
}

/// The pointer after a rune: `nj` is where an unclocked decoder would continue (last key index used + 1).
#[inline]
fn clocked(nj: usize, c: usize, t: u8) -> usize {
    let k = CLOCK.load(Ordering::Relaxed);
    if k == 0 {
        return nj;
    }
    let r = if k <= 3 { c } else { t as usize };
    nj - 1 + match k % 3 { 1 => 1 + r, 2 => GP[r], _ => GP[r] - 1 }
}

/// Key values a decode of n runes may need: n plus slack, times the clock's mean step with a margin.
fn key_need(n: usize) -> usize {
    let scale = match CLOCK.load(Ordering::Relaxed) { 0 => 1, 1 | 4 => 19, _ => 55 };
    (n + n / 4 + 8) * scale
}
const HBINS: usize = 400; // IoC histogram, bins of 0.01 over [0, 4)

// ------------------------------------------------------------------ inputs

struct Win {
    name: String,
    prev: i32,
    runes: Vec<u8>,
    /// the value the collision check compares a candidate ciphertext with, per position: by default the previous
    /// rune (`prev` before the first). A `P` line in the windows file overrides it, which is how ciphertext-feedback
    /// hypotheses c_i = a*c_{i-1} + p_i + k_i are screened (chain_windows.py): there the window holds
    /// c'_i = c_i - a*c_{i-1} and the check compares with (1-a)*c_{i-1}.
    pv: Vec<i32>,
    /// whether the window's pv came from an explicit P line (per-position prev values; nulledge falls back for it)
    has_p: bool,
    lens: String,
    /// `G <index>`: the window's own first rune sits at this index of the keystream (LP2's ciphertext used as its
    /// own key, export_hyp.py). The decoder then never deciphers rune i with key index g + i, which would give the
    /// all-zero "plaintext" c_i - c_i. -1 (no G line): no restriction. Not supported with dir=back or by gpu.py.
    g: i64,
    /// `S <+1|-1 per rune>` (word-level sign rules, signrules.py): rune i is deciphered with the key sign s_i, c_i = p_i + s_i * k, so every key value an attempt for rune i reads (first try, skip, coin)
    /// is negated when s_i = -1. Empty (no S line): all +1, decodes byte-identical. Not supported with dir=back or by gpu.py.
    sg: Vec<i8>,
}

/// a key value read for a rune whose sign is negative
fn sgn(k: u8, neg: bool) -> usize {
    if neg && k != 0 { Q - k as usize } else { k as usize }
}

/// The guard index for a decode starting at keystream offset `off`: rune i must not use key index guard + i.
fn guard_of(w: &Win, off: usize) -> i64 {
    assert!(w.g < 0 || !BACK.load(Ordering::Relaxed), "{}: G lines are not supported with dir=back", w.name);
    if w.g >= off as i64 { w.g - off as i64 } else { -1 }
}

fn load_windows(path: &str) -> Vec<Win> {
    let txt = fs::read_to_string(path).unwrap_or_else(|e| panic!("{path}: {e}"));
    let mut out: Vec<Win> = Vec::new();
    for line in txt.lines() {
        if let Some(rest) = line.strip_prefix("W ") {
            let mut it = rest.split_whitespace();
            let name = it.next().expect("window name").to_string();
            let prev = it.next().map(|x| x.parse().expect("prev rune")).unwrap_or(-1);
            out.push(Win { name, prev, runes: Vec::new(), pv: Vec::new(), has_p: false, lens: String::new(), g: -1, sg: Vec::new() });
        } else if let Some(rest) = line.strip_prefix("R ") {
            let w = out.last_mut().expect("R line before W line");
            w.runes = rest.split_whitespace().map(|x| x.parse::<u8>().expect("rune")).collect();
        } else if let Some(rest) = line.strip_prefix("L ") {
            out.last_mut().expect("L line before W line").lens = rest.to_string();
        } else if let Some(rest) = line.strip_prefix("P ") {
            let w = out.last_mut().expect("P line before W line");
            w.pv = rest.split_whitespace().map(|x| x.parse().expect("pv")).collect();
            w.has_p = true;
        } else if let Some(rest) = line.strip_prefix("S ") {
            out.last_mut().expect("S line before W line").sg = rest.split_whitespace().map(|x| x.parse::<i8>().expect("sign")).collect();
        } else if let Some(rest) = line.strip_prefix("G ") {
            out.last_mut().expect("G line before W line").g = rest.trim().parse().expect("G index");
        }
    }
    for w in out.iter_mut() {
        if w.pv.is_empty() {
            w.pv = (0..w.runes.len()).map(|i| if i == 0 { w.prev } else { w.runes[i - 1] as i32 }).collect();
        }
        assert_eq!(w.pv.len(), w.runes.len(), "{}: P line length", w.name);
        assert!(w.sg.is_empty() || (w.sg.len() == w.runes.len() && w.sg.iter().all(|&x| x == 1 || x == -1)), "{}: S line must hold one +1/-1 per rune", w.name);
    }
    for w in &out {
        assert!(w.runes.iter().all(|&r| (r as usize) < Q), "{}: rune out of range", w.name);
    }
    out
}

/// The word-edge null positions for a window under the current `nulledge` (0: none, 1: each word's LAST rune,
/// 2: each word's FIRST rune). Words come from the window's L line, which lists the CIPHERTEXT word lengths:
/// a keyless null adds a rune, so a nulled word's L entry includes it (NULLEDGE.md). Safety fallbacks return no
/// positions (the decode is then byte-identical to nulledge=0 for that window): nulledge off, a P line present
/// (its prev values are per-position and cannot skip over nulls), the L line missing/not parseable, a word of
/// length 0, or the lengths not summing to the window's rune count.
fn null_positions(w: &Win) -> Vec<bool> {
    let kind = NULLEDGE.load(Ordering::Relaxed);
    if kind == 0 || w.has_p {
        return Vec::new();
    }
    let lens: Vec<usize> = match w.lens.split_whitespace().map(|x| x.parse()).collect::<Result<Vec<usize>, _>>() {
        Ok(v) => v,
        Err(_) => return Vec::new(),
    };
    if lens.iter().any(|&l| l == 0) || lens.iter().sum::<usize>() != w.runes.len() {
        return Vec::new();
    }
    let mut flags = vec![false; w.runes.len()];
    let mut b = 0usize;
    for &l in &lens {
        let e = b + l;
        flags[if kind == 1 { e - 1 } else { b }] = true;
        b = e;
    }
    flags
}

/// (null flags, collision-check values) for a window: the pvs array with the keyless nulls made invisible to the
/// anti-repeat chain, i.e. the check value of a rune after a null is the last SCORED rune's value, not the
/// null's. With no null positions this is just the window's own pvs.
fn null_adjust(w: &Win) -> (Vec<bool>, Vec<i32>) {
    let flags = null_positions(w);
    if flags.is_empty() {
        return (flags, w.pv.clone());
    }
    let mut pv = vec![0i32; w.runes.len()];
    let mut last = w.pv[0];
    for i in 0..w.runes.len() {
        pv[i] = last;
        if !flags[i] {
            last = if i + 1 < w.pv.len() { w.pv[i + 1] } else { w.runes[i] as i32 };
        }
    }
    (flags, pv)
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
/// pair count sum n_x(n_x-1), letters used, complete): `letters` is the scored-letter count for a complete
/// decode (rune count minus the keyless-null positions, so it equals n when `nulls` is empty) and `complete`
/// is false exactly for an abort or an empty beam. Aborts at `abort_at` runes when the best count over the
/// letters scored so far is below `abort_ioc` (with no nulls this reproduces the original `abort_s` gate
/// exactly).
/// `guard` >= 0 forbids deciphering rune i with key index guard + i (see `Win::g`).
/// `nulls` (empty unless nulledge > 0): nulls[i] = rune i is a keyless null (the last rune of its word for
/// nulledge=1, the first for 2). It is NOT scored and does NOT advance the key pointer; `pvs` is then the
/// null-adjusted array (see `null_adjust`), so a null is invisible to the anti-repeat chain. With `nulls`
/// empty this is exactly the original decode.
#[allow(clippy::too_many_arguments)]
fn ioc_beam(
    c: &[u8],
    pvs: &[i32],
    mk: &[u8],
    model: u8,
    n: usize,
    beam: usize,
    abort_at: usize,
    abort_s: u32,
    abort_ioc: f64,
    tb: &Tb,
    cur: &mut Vec<St>,
    extra: &mut Vec<St>,
    guard: i64,
    sg: &[i8],
    nulls: &[bool],
) -> (u32, usize, bool) {
    cur.clear();
    cur.push(St { j: 0, s: 0, cnt: [0; Q] });
    let klen = mk.len();
    let back = BACK.load(Ordering::Relaxed);
    assert!(sg.is_empty() || !back, "S lines are not supported with dir=back");
    for i in 0..n {
        if !nulls.is_empty() && nulls[i] {
            // a keyless null: not scored, the key pointer and the prev chain stay put
            if i + 1 == abort_at {
                let best = cur.iter().map(|s| s.s).max().unwrap_or(0);
                let letters = i + 1 - (0..=i).filter(|&r| nulls[r]).count();
                if ioc_of(best, letters) < abort_ioc {
                    return (best, abort_at, false);
                }
            }
            continue;
        }
        let ci = c[i] as usize;
        let prev: i32 = pvs[i];
        let neg = !sg.is_empty() && sg[i] < 0;
        let bad = if guard >= 0 { guard as usize + i } else { usize::MAX };
        extra.clear();
        let mut idx = 0;
        while idx < cur.len() {
            let j = cur[idx].j as usize;
            if j + 3 > klen {
                cur.swap_remove(idx);
                continue;
            }
            let k0 = sgn(mk[j], neg);
            let t0 = tb.sub[ci][k0];
            if prev >= 0 {
                let pv = prev as u8;
                if back {
                    let k1 = sgn(mk[j + 1], neg);
                    let k2 = sgn(mk[j + 2], neg);
                    if model == 0 {
                        if tb.add[t0 as usize][k1] == pv {
                            let mut s2 = cur[idx];
                            take(&mut s2, t0, j + 2);
                            extra.push(s2);
                        }
                        if tb.add[t0 as usize][k1] == pv && tb.add[t0 as usize][k2] == pv {
                            let mut s3 = cur[idx];
                            take(&mut s3, t0, j + 3);
                            extra.push(s3);
                        }
                    } else if tb.add[t0 as usize][k2] == pv {
                        let mut s3 = cur[idx];
                        take(&mut s3, t0, j + 3);
                        extra.push(s3);
                    }
                } else if model == 0 {
                    let k1 = sgn(mk[j + 1], neg);
                    let t1 = tb.sub[ci][k1];
                    if tb.add[t1 as usize][k0] == pv && j + 1 != bad {
                        let mut s2 = cur[idx];
                        take(&mut s2, t1, clocked(j + 2, ci, t1));
                        extra.push(s2);
                    }
                    let k2 = sgn(mk[j + 2], neg);
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv && tb.add[t2 as usize][k1] == pv && j + 2 != bad {
                        let mut s3 = cur[idx];
                        take(&mut s3, t2, clocked(j + 3, ci, t2));
                        extra.push(s3);
                    }
                } else {
                    let k2 = sgn(mk[j + 2], neg);
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv && j + 2 != bad {
                        let mut s3 = cur[idx];
                        take(&mut s3, t2, clocked(j + 3, ci, t2));
                        extra.push(s3);
                    }
                }
            }
            if back && model == 1 && prev >= 0 && prev == ci as i32 {
                // a kept doublet, backward: the coin has the lower key index and the used key follows it
                take(&mut cur[idx], tb.sub[ci][sgn(mk[j + 1], neg)], j + 2);
            } else if j == bad {
                cur.swap_remove(idx);
                continue;
            } else {
                let nj = if !back && model == 1 && prev == ci as i32 { j + 2 } else { j + 1 };
                take(&mut cur[idx], t0, if back { nj } else { clocked(nj, ci, t0) });
            }
            idx += 1;
        }
        cur.extend_from_slice(extra);
        if cur.is_empty() {
            return (0, i.max(2), false);
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
                // stable, so ties at the cut are resolved by position: the GPU port (gpu.py) reproduces this exactly
                cur.sort_by(|x, y| y.s.cmp(&x.s));
                cur.truncate(beam);
            }
        }
        if i + 1 == abort_at {
            let best = cur.iter().map(|s| s.s).max().unwrap_or(0);
            let below = if nulls.is_empty() {
                // the original integer gate, unchanged for nulledge=0
                best < abort_s
            } else {
                // keyless nulls are not scored, so the gate uses the letters scored so far
                ioc_of(best, i + 1 - (0..=i).filter(|&r| nulls[r]).count()) < abort_ioc
            };
            if below {
                return (best, abort_at, false);
            }
        }
    }
    let letters = if nulls.is_empty() { n } else { (0..n).filter(|&i| !nulls[i]).count() };
    (cur.iter().map(|s| s.s).max().unwrap_or(0), letters, true)
}

fn ioc_of(s: u32, n: usize) -> f64 {
    if n < 2 { 0.0 } else { Q as f64 * s as f64 / (n as f64 * (n as f64 - 1.0)) }
}

/// Full decode for verification: like ioc_beam (no abort) but keeps each state's plaintext and pointers.
/// `nulls`: the keyless-null positions (see ioc_beam; `pvs` must then be the null-adjusted array); a null is
/// not scored and does not advance the pointer. Empty = the original decode, byte-identical.
fn full_decode(c: &[u8], pvs: &[i32], mk: &[u8], model: u8, n: usize, beam: usize, guard: i64, sg: &[i8], nulls: &[bool]) -> (f64, Vec<u8>, Vec<u32>) {
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
    let back = BACK.load(Ordering::Relaxed);
    assert!(sg.is_empty() || !back, "S lines are not supported with dir=back");
    for i in 0..n {
        if !nulls.is_empty() && nulls[i] {
            // a keyless null: not scored, pointer and prev chain stay put
            continue;
        }
        let ci = c[i] as usize;
        let prev: i32 = pvs[i];
        let neg = !sg.is_empty() && sg[i] < 0;
        let mut next: Vec<S2> = Vec::new();
        for st in &cur {
            let j = st.j;
            if j + 3 > mk.len() {
                continue;
            }
            let k0 = sgn(mk[j], neg);
            if back {
                let t0 = tb.sub[ci][k0];
                let (k1, k2) = (sgn(mk[j + 1], neg), sgn(mk[j + 2], neg));
                if prev >= 0 && model == 1 && prev == ci as i32 {
                    next.push(step(st, tb.sub[ci][k1], j + 1, j + 2)); // kept doublet: the coin comes first, then the used key
                } else {
                    next.push(step(st, t0, j, j + 1));
                }
                if prev >= 0 {
                    let pv = prev as u8;
                    if model == 0 {
                        if tb.add[t0 as usize][k1] == pv {
                            next.push(step(st, t0, j, j + 2));
                        }
                        if tb.add[t0 as usize][k1] == pv && tb.add[t0 as usize][k2] == pv {
                            next.push(step(st, t0, j, j + 3));
                        }
                    } else if tb.add[t0 as usize][k2] == pv {
                        next.push(step(st, t0, j, j + 3));
                    }
                }
                continue;
            }
            let bad = if guard >= 0 { guard as usize + i } else { usize::MAX };
            let nj = if model == 1 && prev == ci as i32 { j + 2 } else { j + 1 };
            if j != bad {
                let t0 = tb.sub[ci][k0];
                next.push(step(st, t0, j, clocked(nj, ci, t0)));
            }
            if prev >= 0 {
                let pv = prev as u8;
                let k1 = sgn(mk[j + 1], neg);
                let k2 = sgn(mk[j + 2], neg);
                if model == 0 {
                    let t1 = tb.sub[ci][k1];
                    if tb.add[t1 as usize][k0] == pv && j + 1 != bad {
                        next.push(step(st, t1, j + 1, clocked(j + 2, ci, t1)));
                    }
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv && tb.add[t2 as usize][k1] == pv && j + 2 != bad {
                        next.push(step(st, t2, j + 2, clocked(j + 3, ci, t2)));
                    }
                } else {
                    let t2 = tb.sub[ci][k2];
                    if tb.add[t2 as usize][k0] == pv && j + 2 != bad {
                        next.push(step(st, t2, j + 2, clocked(j + 3, ci, t2)));
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
    BACK.store(o.get("dir").map_or(false, |d| d == "back"), Ordering::Relaxed);
    set_clock(&o);
    let nulledge: usize = get(&o, "nulledge", 0);
    assert!(nulledge <= 2, "nulledge=0|1|2 (0 = off; word-edge keyless nulls, see NULLEDGE.md)");
    NULLEDGE.store(nulledge, Ordering::Relaxed);
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
    let nulls: Vec<(Vec<bool>, Vec<i32>)> = wins.iter().map(|w| null_adjust(w)).collect();
    let wn: Vec<usize> = wins.iter().map(|w| w.runes.len().min(n_req)).collect();
    let nmax = *wn.iter().max().expect("no windows");
    let need = key_need(nmax);
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
            let (fam, items, wins, wn, mults, models, nulls) = (&fam, &items, &wins, &wn, &mults, &models, &nulls);
            let (next, done_runs, merged) = (&next, &done_runs, &merged);
            sc.spawn(move || {
                let tb = tables();
                let mut cur: Vec<St> = Vec::with_capacity(64);
                let mut extra: Vec<St> = Vec::with_capacity(64);
                let mut key = vec![0u8; need];
                let mut mk = vec![0u8; need];
                let mut hits: Vec<Hit> = Vec::new();
                // a hit must beat `thr`, the lowest IoC of the last pruned (sorted) list; before the first prune
                // the list is unsorted, so nothing may be rejected (hits[top - 1] would be an arbitrary entry)
                let mut thr = -1.0f32;
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
                                    let (s, used, full) = ioc_beam(
                                        &w.runes, &nulls[wi].1, &mk, model, n, beam, ab, abort_s, abort_ioc, &tb, &mut cur, &mut extra, guard_of(w, off), &w.sg, &nulls[wi].0,
                                    );
                                    let ioc = ioc_of(s, used) as f32;
                                    runs += 1;
                                    if !full {
                                        aborted += 1;
                                    }
                                    hist[((ioc * 100.0) as usize).min(HBINS - 1)] += 1;
                                    let h = Hit { ioc, item: item as u32, off: off as u32, mult: m, model, win: wi as u16, n: used as u16 };
                                    if full && ioc > wbest[wi].ioc {
                                        wbest[wi] = h;
                                    }
                                    if full && ioc > thr {
                                        hits.push(h);
                                        if hits.len() >= 2 * top {
                                            keep_top(&mut hits, top);
                                            thr = hits[top - 1].ioc;
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
        "# kscreen screen family={} windows={} n={} beam={} mults={} models={} abort={} runs={} aborted={} secs={:.0} dir={}{}{}",
        args[1],
        args[0],
        nmax,
        beam,
        join(&mults),
        join(&models),
        abort_spec,
        runs,
        aborted,
        secs,
        if BACK.load(Ordering::Relaxed) { "back" } else { "fwd" },
        // only a clocked run names its clock, so the default header stays byte-identical to gpu.py's
        match CLOCK.load(Ordering::Relaxed) { 0 => String::new(), k => format!(" clock={}", CLOCKS[k]) },
        // likewise only a nulledge run names it, so nulledge=0 headers stay byte-identical
        match NULLEDGE.load(Ordering::Relaxed) { 0 => String::new(), k => format!(" nulledge={k}") }
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

// ------------------------------------------------------------------ trace

/// One line per decode: `item offset mult model window s used`, in the order item, offset, mult, model, window.
/// This is what gpu.py is compared against decode by decode (tests/test_kscreen_gpu.py).
fn mode_trace(args: &[String]) {
    if args.len() < 3 {
        eprintln!("usage: trace <windows.txt> <family> <out.txt> [n=300] [beam=16] [mults=..] [models=..] [abort=..] [items=a:b] [offs=a:b] [minlen=50]");
        std::process::exit(2);
    }
    let all_wins = load_windows(&args[0]);
    let fam = Fam::parse(&args[1]);
    let o = opts(&args[3..]);
    BACK.store(o.get("dir").map_or(false, |d| d == "back"), Ordering::Relaxed);
    set_clock(&o);
    let nulledge: usize = get(&o, "nulledge", 0);
    assert!(nulledge <= 2, "nulledge=0|1|2 (0 = off; word-edge keyless nulls, see NULLEDGE.md)");
    NULLEDGE.store(nulledge, Ordering::Relaxed);
    let n_req: usize = get(&o, "n", 300);
    let beam: usize = get(&o, "beam", 16);
    let mults = list_u8(&get(&o, "mults", "1,28".to_string()));
    let models = list_u8(&get(&o, "models", "0,1".to_string()));
    let minlen: usize = get(&o, "minlen", 50);
    let abort_spec: String = get(&o, "abort", "150:1.2".to_string());
    let (abort_at, abort_ioc) = if abort_spec == "0" {
        (0usize, 0.0f64)
    } else {
        let (a, b) = abort_spec.split_once(':').expect("abort=<runes>:<ioc>");
        (a.parse().expect("abort runes"), b.parse().expect("abort ioc"))
    };
    let abort_s = (abort_ioc * abort_at as f64 * (abort_at as f64 - 1.0) / Q as f64).ceil() as u32;
    let range = |key: &str, hi: usize| -> (usize, usize) {
        o.get(key).map_or((0, hi), |r| {
            let (a, b) = r.split_once(':').expect("a:b");
            (a.parse().unwrap(), b.parse::<usize>().unwrap().min(hi))
        })
    };
    let wins: Vec<&Win> = all_wins.iter().filter(|w| w.runes.len() >= minlen).collect();
    let nulls: Vec<(Vec<bool>, Vec<i32>)> = wins.iter().map(|w| null_adjust(w)).collect();
    let nmax = wins.iter().map(|w| w.runes.len().min(n_req)).max().expect("no windows");
    let need = key_need(nmax);
    let tb = tables();
    let (mut cur, mut extra) = (Vec::new(), Vec::new());
    let (mut key, mut mk) = (vec![0u8; need], vec![0u8; need]);
    let mut out = BufWriter::new(fs::File::create(&args[2]).unwrap_or_else(|e| panic!("{}: {e}", args[2])));
    let (i0, i1) = range("items", fam.items());
    for item in i0..i1 {
        let coeffs = fam.coeffs(item);
        let (o0, o1) = range("offs", fam.offsets(item, need));
        for off in o0..o1 {
            fam.fill(item, &coeffs, off, &mut key);
            for &m in &mults {
                for (a, b) in mk.iter_mut().zip(key.iter()) {
                    *a = ((*b as usize * m as usize) % Q) as u8;
                }
                for &model in &models {
                    for (wi, w) in wins.iter().enumerate() {
                        let n = w.runes.len().min(n_req);
                        let ab = if abort_at > 0 && abort_at < n { abort_at } else { 0 };
                        let (s, used, _full) =
                            ioc_beam(&w.runes, &nulls[wi].1, &mk, model, n, beam, ab, abort_s, abort_ioc, &tb, &mut cur, &mut extra, guard_of(w, off), &w.sg, &nulls[wi].0);
                        writeln!(out, "{item} {off} {m} {model} {wi} {s} {used}").unwrap();
                    }
                }
            }
        }
    }
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
    set_clock(&opts(&args[10..]));
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
        let len = (w.runes.len() * 4).max(key_need(w.runes.len())) + 64;
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
            j = clocked(j, y as usize, t as u8);
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
    BACK.store(o.get("dir").map_or(false, |d| d == "back"), Ordering::Relaxed);
    set_clock(&o);
    let nulledge: usize = get(&o, "nulledge", 0);
    assert!(nulledge <= 2, "nulledge=0|1|2 (0 = off; word-edge keyless nulls, see NULLEDGE.md)");
    NULLEDGE.store(nulledge, Ordering::Relaxed);
    let n_req: usize = get(&o, "n", 0);
    let beam: usize = get(&o, "beam", 64);
    let coeffs = fam.coeffs(item);
    for w in wins.iter().filter(|w| args[6] == "all" || w.name == args[6]) {
        let nulls = null_adjust(w);
        let mut n = if n_req == 0 { w.runes.len() } else { n_req.min(w.runes.len()) };
        let mut len = key_need(n) + 8;
        // a keystream shorter than the window (e.g. a decimated one): verify over as much of the window as it covers
        while n > 300 && off >= fam.offsets(item, len) {
            n -= 50;
            len = key_need(n) + 8;
        }
        let mut noff = fam.offsets(item, len);
        if off >= noff {
            // a clocked pointer can need more key than the stream holds: decode as far as the key reaches
            if let Fam::Ks(_) = &fam {
                let avail = fam.offsets(item, 1).saturating_sub(off);
                if avail >= 64 {
                    len = avail;
                    noff = fam.offsets(item, len);
                }
            }
        }
        if off >= noff {
            println!("window {} skipped: keystream too short for offset {off}", w.name);
            continue;
        }
        let mut key = vec![0u8; len];
        fam.fill(item, &coeffs, off, &mut key);
        let mk: Vec<u8> = key.iter().map(|&k| (k as usize * m % Q) as u8).collect();
        let (ioc, plain, ptr) = full_decode(&w.runes, &nulls.1, &mk, model, n, beam, guard_of(w, off), &w.sg, &nulls.0);
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
                vals.push(full_decode(&w.runes, &nulls.1, &cmk, model, n, beam, guard_of(w, co), &w.sg, &nulls.0).0);
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
        eprintln!("modes: screen | trace | plant | verify | info  (see the header of src/main.rs)");
        std::process::exit(2);
    }
    let rest = &args[2..];
    match args[1].as_str() {
        "screen" => mode_screen(rest),
        "trace" => mode_trace(rest),
        "plant" => mode_plant(rest),
        "verify" => mode_verify(rest),
        "info" => mode_info(rest),
        m => {
            eprintln!("unknown mode {m}");
            std::process::exit(2);
        }
    }
}
