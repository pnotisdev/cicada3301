
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
