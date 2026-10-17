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

