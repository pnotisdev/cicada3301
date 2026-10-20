//! ogcoef: own baseline-JPEG entropy decoder that lists the "usable" DCT coefficients of a single-scan JPEG in the order a
//! libjpeg one-pass decoder hands them over (MCU rows, MCU columns, components in scan order, blocks inside the MCU,
//! coefficient k = 0..63 in natural order, only blocks inside the component's real block grid), keeping the least significant
//! bit of every coefficient that is not 0 or 1 (two's complement of the signed value). That is the bit sequence an LSB
//! steganography reader of the OutGuess kind works on. Written from the JPEG standard; no third-party code.
//!
//! usage: ogcoef <in.jpg> <out.bits>      out.bits = u32 little-endian count, then one byte (0/1) per usable coefficient
use std::env;
use std::fs;
use std::io::Write;

const ZIGZAG: [usize; 64] = [
    0, 1, 8, 16, 9, 2, 3, 10, 17, 24, 32, 25, 18, 11, 4, 5, 12, 19, 26, 33, 40, 48, 41, 34, 27, 20, 13, 6, 7, 14, 21, 28, 35,
    42, 49, 56, 57, 50, 43, 36, 29, 22, 15, 23, 30, 37, 44, 51, 58, 59, 52, 45, 38, 31, 39, 46, 53, 60, 61, 54, 47, 55, 62, 63,
];

#[derive(Clone, Default)]
struct Huff {
    mincode: [i32; 17],
    maxcode: [i32; 18],
    valptr: [i32; 17],
    vals: Vec<u8>,
}

fn build(counts: &[u8], vals: &[u8]) -> Huff {
    let mut h = Huff::default();
    h.vals = vals.to_vec();
    let mut code = 0i32;
    let mut k = 0i32;
    for l in 1..=16usize {
        h.valptr[l] = k;
        h.mincode[l] = code;
        code += counts[l - 1] as i32;
        k += counts[l - 1] as i32;
        h.maxcode[l] = if counts[l - 1] > 0 { code - 1 } else { -1 };
        code <<= 1;
    }
    h.maxcode[17] = i32::MAX;
    h
}

struct Bits<'a> {
    d: &'a [u8],
    pos: usize,
    buf: u32,
    n: u32,
    marker: Option<u8>,
}

impl<'a> Bits<'a> {
    fn fill(&mut self) {
        while self.n <= 24 {
            let b = if self.marker.is_some() || self.pos >= self.d.len() {
                0
            } else {
                let b = self.d[self.pos];
                self.pos += 1;
                if b == 0xFF {
                    let nx = if self.pos < self.d.len() { self.d[self.pos] } else { 0xD9 };
                    if nx == 0 {
                        self.pos += 1;
                        0xFF
                    } else {
                        self.marker = Some(nx);
                        self.pos += 1;
                        0
                    }
                } else {
                    b
                }
            };
            self.buf |= (b as u32) << (24 - self.n);
            self.n += 8;
        }
    }
    fn bit(&mut self) -> u32 {
        if self.n == 0 {
            self.fill();
        }
        let b = self.buf >> 31;
        self.buf <<= 1;
        self.n -= 1;
        b
    }
    fn bits(&mut self, k: u32) -> i32 {
        let mut v = 0i32;
        for _ in 0..k {
            v = (v << 1) | self.bit() as i32;
        }
        v
    }
    fn decode(&mut self, h: &Huff) -> u8 {
        let mut code = 0i32;
        for l in 1..=16usize {
            code = (code << 1) | self.bit() as i32;
            if h.maxcode[l] >= 0 && code <= h.maxcode[l] && code >= h.mincode[l] {
                return h.vals[(h.valptr[l] + code - h.mincode[l]) as usize];
            }
        }
        0
    }
    fn restart(&mut self) {
        // drop the remaining bits and step over the RSTn marker
        self.buf = 0;
        self.n = 0;
        if self.marker.is_none() {
            while self.pos + 1 < self.d.len() && !(self.d[self.pos] == 0xFF && (0xD0..=0xD7).contains(&self.d[self.pos + 1])) {
                self.pos += 1;
            }
            self.pos += 2;
        } else {
            self.marker = None;
        }
    }
}

fn extend(v: i32, s: u32) -> i32 {
    if s == 0 {
        0
    } else if v < (1 << (s - 1)) {
        v - (1 << s) + 1
    } else {
        v
    }
}

fn main() {
    let a: Vec<String> = env::args().collect();
    let d = fs::read(&a[1]).expect("read");
    assert!(d[0] == 0xFF && d[1] == 0xD8);
    let mut i = 2usize;
    let (mut width, mut height) = (0usize, 0usize);
    let mut comps: Vec<(u8, usize, usize)> = Vec::new(); // id, h, v
    let mut dc: [Huff; 4] = Default::default();
    let mut ac: [Huff; 4] = Default::default();
    let mut restart = 0usize;
    let mut scans = 0;
    let mut out: Vec<u8> = Vec::new();
    let mut total_coef = 0usize;
    let mut endpos = 0usize;
    while i + 4 <= d.len() {
        assert!(d[i] == 0xFF, "marker expected at {}", i);
        let m = d[i + 1];
        i += 2;
        if m == 0xD9 {
            break;
        }
        if m == 0x01 || (0xD0..=0xD7).contains(&m) || m == 0xFF {
            continue;
        }
        let len = ((d[i] as usize) << 8) | d[i + 1] as usize;
        let seg = &d[i + 2..i + len];
        match m {
            0xC0 | 0xC1 => {
                height = ((seg[1] as usize) << 8) | seg[2] as usize;
                width = ((seg[3] as usize) << 8) | seg[4] as usize;
                let nc = seg[5] as usize;
                comps.clear();
                for c in 0..nc {
                    let b = &seg[6 + 3 * c..9 + 3 * c];
                    comps.push((b[0], (b[1] >> 4) as usize, (b[1] & 15) as usize));
                }
            }
            0xC2 => panic!("progressive JPEG not supported"),
            0xC4 => {
                let mut p = 0;
                while p < seg.len() {
                    let tc = seg[p] >> 4;
                    let th = (seg[p] & 15) as usize;
                    let counts = &seg[p + 1..p + 17];
                    let n: usize = counts.iter().map(|&x| x as usize).sum();
                    let vals = &seg[p + 17..p + 17 + n];
                    if tc == 0 {
                        dc[th] = build(counts, vals);
                    } else {
                        ac[th] = build(counts, vals);
                    }
                    p += 17 + n;
                }
            }
            0xDD => restart = ((seg[0] as usize) << 8) | seg[1] as usize,
            0xDA => {
                scans += 1;
                assert!(scans == 1, "more than one scan: the one-pass path would not be used");
                let ns = seg[0] as usize;
                let mut sc: Vec<(usize, usize, usize)> = Vec::new(); // component index, dc table, ac table
                for s in 0..ns {
                    let cid = seg[1 + 2 * s];
                    let t = seg[2 + 2 * s];
                    let ci = comps.iter().position(|c| c.0 == cid).expect("component");
                    sc.push((ci, (t >> 4) as usize, (t & 15) as usize));
                }
                let hmax = comps.iter().map(|c| c.1).max().unwrap();
                let vmax = comps.iter().map(|c| c.2).max().unwrap();
                let wib = |ci: usize| (width * comps[ci].1 + hmax * 8 - 1) / (hmax * 8);
                let hib = |ci: usize| (height * comps[ci].2 + vmax * 8 - 1) / (vmax * 8);
                let (mcus_x, mcus_y, mw, mh): (usize, usize, Vec<usize>, Vec<usize>) = if ns == 1 {
                    let ci = sc[0].0;
                    (wib(ci), hib(ci), vec![1], vec![1])
                } else {
                    (
                        (width + hmax * 8 - 1) / (hmax * 8),
                        (height + vmax * 8 - 1) / (vmax * 8),
                        sc.iter().map(|s| comps[s.0].1).collect(),
                        sc.iter().map(|s| comps[s.0].2).collect(),
                    )
                };
                let start = i + len;
                let mut br = Bits { d: &d, pos: start, buf: 0, n: 0, marker: None };
                let mut pred = vec![0i32; ns];
                let mut count = 0usize;
                for my in 0..mcus_y {
                    for mx in 0..mcus_x {
                        if restart > 0 && count > 0 && count % restart == 0 {
                            br.restart();
                            pred.iter_mut().for_each(|p| *p = 0);
                        }
                        count += 1;
                        for (si, &(ci, td, ta)) in sc.iter().enumerate() {
                            let (bw, bh) = (mw[si], mh[si]);
                            let (wb, hb) = (wib(ci), hib(ci));
                            let last_col = if ns == 1 { 1 } else if wb % bw == 0 { bw } else { wb % bw };
                            let last_row = if ns == 1 { 1 } else if hb % bh == 0 { bh } else { hb % bh };
                            for yi in 0..bh {
                                for xi in 0..bw {
                                    let mut blk = [0i32; 64];
                                    let s = br.decode(&dc[td]) as u32;
                                    let diff = if s == 0 { 0 } else { extend(br.bits(s), s) };
                                    pred[si] += diff;
                                    blk[0] = pred[si];
                                    let mut k = 1;
                                    while k < 64 {
                                        let rs = br.decode(&ac[ta]);
                                        let r = (rs >> 4) as usize;
                                        let s = (rs & 15) as u32;
                                        if s == 0 {
                                            if r == 15 {
                                                k += 16;
                                                continue;
                                            }
                                            break;
                                        }
                                        k += r;
                                        if k > 63 {
                                            break;
                                        }
                                        blk[ZIGZAG[k]] = extend(br.bits(s), s);
                                        k += 1;
                                    }
                                    let useful = (mx < mcus_x - 1 || xi < last_col) && (my < mcus_y - 1 || yi < last_row);
                                    if useful {
                                        for kk in 0..64 {
                                            total_coef += 1;
                                            let v = blk[kk] as i16 as u16;
                                            if (v & 1) != v {
                                                out.push((v & 1) as u8);
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                endpos = br.pos;
                break;
            }
            _ => {}
        }
        i += len;
    }
    let mut f = fs::File::create(&a[2]).unwrap();
    f.write_all(&(out.len() as u32).to_le_bytes()).unwrap();
    f.write_all(&out).unwrap();
    println!("{} {}x{} comps {:?} restart {} coefficients {} usable {} stream end {} of {} bytes", a[1], width, height, comps, restart, total_coef, out.len(), endpos, d.len());
}
