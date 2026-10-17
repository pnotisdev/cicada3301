
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

