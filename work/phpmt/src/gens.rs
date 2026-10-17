//! More key generators for the seed sweeps. Unlike php / glibc / .NET (one output per key), several of these map
//! the generator's output to 0..28 with a rule that consumes a variable number of outputs (rejection) or two outputs
//! per key, so they produce the key stream directly: `fill_keys(kind, seed, map, out)`.
//!
//!   kind     generator (seed)                                   map 0                          map 1
//!   py3      CPython random.seed(n): MT19937 init_by_array([n])   randrange(29): getrandbits(5)      int(random() * 29)  (= Python 2 randrange)
//!                                                               with rejection of 29..31
//!   mt32     std::mt19937(n) / PHP >= 7.1: MT19937 init_genrand   uniform_int_distribution(0,28)      gen() % 29  (PHP 7 mt_rand(0,28))
//!                                                               (Lemire form, GCC >= 11)
//!   mt31     the same, 31-bit output y >> 1                       (y >> 1) % 29 (PHP 7 mt_rand()%29)  floor(29 * (y >> 1) / 2^31)
//!   java     java.util.Random(n), n a signed 32-bit int           nextInt(29)                     (int)(nextDouble() * 29)
//!   msvc     MSVC rand() after srand(n): x*214013+2531011         rand() % 29                    rand() * 29 / 32768
//!   drand48  drand48 / Perl >= 5.20 srand(n): X = n<<16|0x330E   int(drand48() * 29)            lrand48() % 29
//!   ruby     Ruby <= 2.7 Random.new(n): init_by_array([n])        rand(29): y & 31, retry > 28   int(rand() * 29) (res53)
//! Every rule is the documented algorithm; work/tests/test_gens.py checks them against CPython, NumPy and published vectors.

use std::sync::atomic::{AtomicU32, Ordering};

pub const N: usize = 624;
const M: usize = 397;

/// Size of the key alphabet the maps reduce to: 29 for the ordinary cipher (every earlier sweep), 28 for the step-domain
/// cipher of work/kscreen/step28.py. Set once before generating (the `keys` mode reads it from its last argument).
static KM: AtomicU32 = AtomicU32::new(29);

pub fn set_km(k: u32) {
    KM.store(k, Ordering::Relaxed);
}

pub fn km() -> u32 {
    KM.load(Ordering::Relaxed)
}

#[derive(Clone, Copy, PartialEq, Debug)]
pub enum Kind {
    Py3,
    Mt32,
    Mt31,
    Java,
    Msvc,
    Drand48,
    Ruby,
}

pub fn parse(s: &str) -> Option<Kind> {
    Some(match s {
        "py3" => Kind::Py3,
        "mt32" => Kind::Mt32,
        "mt31" => Kind::Mt31,
        "java" => Kind::Java,
        "msvc" => Kind::Msvc,
        "drand48" => Kind::Drand48,
        "ruby" => Kind::Ruby,
        _ => return None,
    })
}

#[inline]
fn temper(mut y: u32) -> u32 {
    y ^= y >> 11;
    y ^= (y << 7) & 0x9d2c_5680;
    y ^= (y << 15) & 0xefc6_0000;
    y ^ (y >> 18)
}

/// Standard MT19937 (the reference implementation).
pub struct Mt {
    s: [u32; N],
    next: usize,
}

impl Mt {
    pub fn init_genrand(seed: u32) -> Mt {
        let mut s = [0u32; N];
        s[0] = seed;
        for i in 1..N {
            s[i] = 1812433253u32.wrapping_mul(s[i - 1] ^ (s[i - 1] >> 30)).wrapping_add(i as u32);
        }
        Mt { s, next: N }
    }

    pub fn init_by_array(key: &[u32]) -> Mt {
        let mut m = Mt::init_genrand(19650218);
        let (mut i, mut j) = (1usize, 0usize);
        let mut k = N.max(key.len());
        while k > 0 {
            let prev = m.s[i - 1];
            m.s[i] = (m.s[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1664525)).wrapping_add(key[j]).wrapping_add(j as u32);
            i += 1;
            j += 1;
            if i >= N {
                m.s[0] = m.s[N - 1];
                i = 1;
            }
            if j >= key.len() {
                j = 0;
            }
            k -= 1;
        }
        k = N - 1;
        while k > 0 {
            let prev = m.s[i - 1];
            m.s[i] = (m.s[i] ^ (prev ^ (prev >> 30)).wrapping_mul(1566083941)).wrapping_sub(i as u32);
            i += 1;
            if i >= N {
                m.s[0] = m.s[N - 1];
                i = 1;
            }
            k -= 1;
        }
        m.s[0] = 0x8000_0000;
        m
    }

    fn reload(&mut self) {
        let s = &mut self.s;
        let tw = |m: u32, u: u32, v: u32| m ^ (((u & 0x8000_0000) | (v & 0x7fff_ffff)) >> 1) ^ (0u32.wrapping_sub(v & 1) & 0x9908_b0df);
        for i in 0..N - M {
            s[i] = tw(s[i + M], s[i], s[i + 1]);
        }
        for i in N - M..N - 1 {
            s[i] = tw(s[i + M - N], s[i], s[i + 1]);
        }
        s[N - 1] = tw(s[M - 1], s[N - 1], s[0]);
        self.next = 0;
    }

    /// tempered 32-bit output (genrand_int32)
    pub fn next_u32(&mut self) -> u32 {
        if self.next == N {
            self.reload();
        }
        let y = self.s[self.next];
        self.next += 1;
        temper(y)
    }
}

/// genrand_res53: two outputs -> a double in [0, 1) (CPython random.random(), Ruby rand())
fn res53(mt: &mut Mt) -> f64 {
    let a = (mt.next_u32() >> 5) as f64;
    let b = (mt.next_u32() >> 6) as f64;
    (a * 67108864.0 + b) * (1.0 / 9007199254740992.0)
}

const MASK48: u64 = (1u64 << 48) - 1;
const JMUL: u64 = 0x5_DEEC_E66D;

pub fn fill_keys(kind: Kind, seed: u32, map: u8, out: &mut [u8]) {
    let km = km();
    let kf = km as f64;
    match kind {
        Kind::Py3 | Kind::Ruby => {
            let mut mt = Mt::init_by_array(&[seed]);
            for o in out.iter_mut() {
                *o = match (kind, map) {
                    (Kind::Py3, 0) => loop {
                        let r = mt.next_u32() >> 27;
                        if r < km {
                            break r as u8;
                        }
                    },
                    (Kind::Ruby, 0) => loop {
                        let r = mt.next_u32() & 31;
                        if r < km {
                            break r as u8;
                        }
                    },
                    _ => (res53(&mut mt) * kf) as u8,
                };
            }
        }
        Kind::Mt32 | Kind::Mt31 => {
            let mut mt = Mt::init_genrand(seed);
            for o in out.iter_mut() {
                *o = match (kind, map) {
                    (Kind::Mt32, 0) => loop {
                        // libstdc++ >= 11: nearly divisionless (Lemire) draw of 0..28
                        let mut prod = mt.next_u32() as u64 * km as u64;
                        if (prod as u32) < km {
                            let thr = 0u32.wrapping_sub(km) % km;
                            while (prod as u32) < thr {
                                prod = mt.next_u32() as u64 * km as u64;
                            }
                        }
                        break (prod >> 32) as u8;
                    },
                    (Kind::Mt32, _) => (mt.next_u32() % km) as u8,
                    (Kind::Mt31, 0) => ((mt.next_u32() >> 1) % km) as u8,
                    _ => (kf * ((mt.next_u32() >> 1) as f64 / 2147483648.0)) as u8,
                };
            }
        }
        Kind::Java => {
            let mut s = ((seed as i32 as i64 as u64) ^ JMUL) & MASK48;
            let mut next = |bits: u32| -> u32 {
                s = (s.wrapping_mul(JMUL).wrapping_add(0xB)) & MASK48;
                (s >> (48 - bits)) as u32
            };
            for o in out.iter_mut() {
                *o = if map == 0 {
                    loop {
                        let bits = next(31) as i32;
                        let val = bits % km as i32;
                        if bits.wrapping_sub(val).wrapping_add(km as i32 - 1) >= 0 {
                            break val as u8;
                        }
                    }
                } else {
                    let hi = next(26) as u64;
                    let lo = next(27) as u64;
                    ((((hi << 27) + lo) as f64 * (1.0 / 9007199254740992.0)) * kf) as u8
                };
            }
        }
        Kind::Msvc => {
            let mut x = seed;
            for o in out.iter_mut() {
                x = x.wrapping_mul(214013).wrapping_add(2531011);
                let r = (x >> 16) & 0x7fff;
                *o = if map == 0 { (r % km) as u8 } else { ((r * km) >> 15) as u8 };
            }
        }
        Kind::Drand48 => {
            let mut x = ((seed as u64) << 16) | 0x330E;
            for o in out.iter_mut() {
                x = (x.wrapping_mul(JMUL).wrapping_add(0xB)) & MASK48;
                *o = if map == 0 { ((x * km as u64) >> 48) as u8 } else { ((x >> 17) % km as u64) as u8 };
            }
        }
    }
}
