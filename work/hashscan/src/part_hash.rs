
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

