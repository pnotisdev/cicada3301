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

