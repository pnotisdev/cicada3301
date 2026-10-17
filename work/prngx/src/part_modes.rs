
// ------------------------------------------------------------------ modes

fn mode_vectors(path: &str) {
    // lines: <gen> <seed> <map|raw> <values...>; reference values come from real implementations
    let txt = fs::read_to_string(path).expect("vectors file");
    let (mut ok, mut bad) = (0, 0);
    for line in txt.lines() {
        let f: Vec<&str> = line.split_whitespace().collect();
        if f.len() < 4 || f[0].starts_with('#') {
            continue;
        }
        let g = parse_gen(f[0]);
        let seed: i64 = f[1].parse().unwrap();
        let vals: Vec<i64> = f[3..].iter().map(|x| x.parse().unwrap()).collect();
        let raw = raw_n(g, seed, vals.len() * 6 + 40);
        let got: Vec<i64> = if f[2] == "raw" {
            raw[..vals.len()].iter().map(|&x| x as i64).collect()
        } else if f[2] == "javaint" {
            raw[..vals.len()].iter().map(|&x| x as i32 as i64).collect()
        } else {
            let mut k = Vec::new();
            keys_from(g, &raw, f[2].parse().unwrap(), &mut k, vals.len());
            k.iter().map(|&x| x as i64).collect()
        };
        if got == vals {
            ok += 1;
        } else {
            bad += 1;
            println!("MISMATCH {} {} {}: got {:?} want {:?}", f[0], f[1], f[2], &got[..got.len().min(6)], &vals[..vals.len().min(6)]);
        }
    }
    println!("prngx vectors: {} match, {} mismatch", ok, bad);
}

fn mode_plant(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = load_windows(&args[0]);
    let seed: i64 = args[1].parse().unwrap();
    let map: u8 = args[2].parse().unwrap();
    let model: u8 = args[3].parse().unwrap();
    let sign: i32 = args[4].parse().unwrap();
    let atb = args[5] == "1";
    let keep: f64 = args[6].parse().unwrap();
    let mut out = String::new();
    let mut lcg: u64 = 0x2545F4914F6CDD1D ^ seed as u64;
    let mut coin = || {
        lcg = lcg.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        (lcg >> 11) as f64 / (1u64 << 53) as f64
    };
    for w in &wins {
        let need = w.runes.len() * 4 + 64;
        let raw = raw_n(g, seed, need * 3 + 200);
        let mut key = Vec::new();
        keys_from(g, &raw, map, &mut key, need);
        let mut j = 0usize;
        let mut prev: i32 = -1;
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
                j += 1; // the coin value
                if coin() >= keep {
                    y = md(t + sign * key[j] as i32);
                    j += 1;
                }
            }
            c.push(y as u8);
            prev = y;
        }
        let mut lens = Vec::new();
        let mut l = 0;
        for i in 0..w.runes.len() {
            l += 1;
            if w.word_end[i] {
                lens.push(l.to_string());
                l = 0;
            }
        }
        out += &format!("W planted_{} -1\nR {}\nL {}\n", w.name,
                        c.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "), lens.join(" "));
    }
    fs::write(&args[7], out).unwrap();
    println!("planted seed {} into {} windows -> {}", seed, wins.len(), args[7]);
}

#[derive(Clone, Copy)]
struct Cand {
    score: u16,
    seed: i64,
    win: u8,
    variant: u8,
}

fn variant_parts(v: u8) -> (u8, u8, i32, bool) {
    // v = map * 8 + model * 4 + sign_idx * 2 + atb
    let sub = v & 7;
    (sub >> 2 & 1, v >> 3, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1)
}

/// PRNGX_MAPS=a,b,..: sweep / bgsweep only these key maps (default: every map of the generator). The prng-time campaign
/// uses it to keep the maps a language that seeds with two 32-bit words can produce (pymt: 2 randrange, 3 Ruby rand(n), 5 random()).
fn sweep_maps(g: Gen) -> Vec<u8> {
    match env::var("PRNGX_MAPS") {
        Ok(s) if !s.trim().is_empty() => {
            let v: Vec<u8> = s.split(',').map(|x| x.trim().parse().expect("PRNGX_MAPS: comma-separated map numbers")).collect();
            assert!(v.iter().all(|&m| m < n_maps(g)), "PRNGX_MAPS: map out of range for this generator");
            v
        }
        _ => (0..n_maps(g)).collect(),
    }
}

fn mode_sweep(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = Arc::new(load_windows(&args[0]));
    let dict = Arc::new(Dict::load(&args[1]));
    let lo: i64 = args[2].parse().unwrap();
    let hi: i64 = args[3].parse().unwrap();
    let out = args[4].clone();
    let threads: usize = if args.len() > 5 { args[5].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let next = Arc::new(AtomicU64::new(0));
    let done = Arc::new(AtomicU64::new(0));
    let top: Arc<Mutex<Vec<Cand>>> = Arc::new(Mutex::new(Vec::new()));
    const CHUNK: u64 = 1 << 16;
    const TOPK: usize = 400;
    let total = (hi - lo) as u64;
    let nm = n_maps(g);
    let maps = Arc::new(sweep_maps(g));
    let t0 = Instant::now();
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (wins, dict, next, done, top, maps) = (wins.clone(), dict.clone(), next.clone(), done.clone(), top.clone(), maps.clone());
        hs.push(std::thread::spawn(move || {
            let mut local: Vec<Cand> = Vec::new();
            let mut floor: u16 = 0;
            let mut keys: Vec<Vec<u8>> = (0..nm).map(|_| Vec::with_capacity(K)).collect();
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= total {
                    break;
                }
                let b = (a + CHUNK).min(total);
                for off in a..b {
                    let seed = lo + off as i64;
                    let raw = raw_n(g, seed, RK);
                    for &m in maps.iter() {
                        keys_from(g, &raw, m, &mut keys[m as usize], K);
                    }
                    for (wi, w) in wins.iter().enumerate() {
                        for v in maps.iter().flat_map(|&m| (0..8u8).map(move |sub| m * 8 + sub)) {
                            let (model, map, sign, atb) = variant_parts(v);
                            let s = decode_fast(w, &keys[map as usize], sign, atb, model, &dict);
                            if s > floor || (local.len() < TOPK && s > 0) {
                                local.push(Cand { score: s, seed, win: wi as u8, variant: v });
                                if local.len() >= 2 * TOPK {
                                    local.sort_by(|x, y| y.score.cmp(&x.score));
                                    local.truncate(TOPK);
                                    floor = local[TOPK - 1].score;
                                }
                            }
                        }
                    }
                }
                let d = done.fetch_add(b - a, Ordering::Relaxed) + (b - a);
                if d % (CHUNK * 256) < CHUNK {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} seeds) {:.0} seeds/s, eta {:.0} s", 100.0 * d as f64 / total as f64, d, rate,
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
    writeln!(f, "score\tseed\twindow\tmodel\tmap\tsign\tatbash").unwrap();
    for c in &all {
        let (model, map, sign, atb) = variant_parts(c.variant);
        writeln!(f, "{}\t{}\t{}\t{}\t{}\t{}\t{}", c.score, c.seed, wins[c.win as usize].name, model, map, sign, atb as u8)
            .unwrap();
    }
    eprintln!("swept {} seeds in {:.0} s; best score {}", total, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score).unwrap_or(0));
}

fn mode_verify(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = load_windows(&args[0]);
    let dict = Dict::load(&args[1]);
    let seed: i64 = args[2].parse().unwrap();
    let w = wins.iter().find(|w| w.name == args[3]).expect("window");
    let map: u8 = args[4].parse().unwrap();
    let model: u8 = args[5].parse().unwrap();
    let sign: i32 = args[6].parse().unwrap();
    let atb = args[7] == "1";
    let raw = raw_n(g, seed, w.runes.len() * 9 + 200);
    let mut key = Vec::new();
    keys_from(g, &raw, map, &mut key, w.runes.len() * 3 + 50);
    let (score, plain) = decode_full(w, &key, sign, atb, model, &dict);
    let mut txt = String::new();
    for (i, p) in plain.iter().enumerate() {
        txt += LATIN[*p as usize];
        if w.word_end[i] {
            txt.push(' ');
        }
    }
    println!("{:.3}\t{}\t{}", score, seed, &txt[..txt.len().min(400)]);
}

#[derive(Clone)]
struct BgCand {
    score: i32,
    seed: i64,
    win: u8,
    variant: u8,
}

/// bgsweep <gen> <windows.txt> <bigram.txt> <lo> <hi> <out.tsv> [threads]
/// Boundary-free score (decode_bg): the first 120 runes of every window (36 for the OEIS windows), no word separators involved.
fn mode_bgsweep(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let args = &args_all[1..];
    let wins = Arc::new(load_windows(&args[0]));
    let tbl = Arc::new(load_bigram(&args[1]));
    let lo: i64 = args[2].parse().unwrap();
    let hi: i64 = args[3].parse().unwrap();
    let out = args[4].clone();
    let threads: usize = if args.len() > 5 { args[5].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let next = Arc::new(AtomicU64::new(0));
    let done = Arc::new(AtomicU64::new(0));
    let top: Arc<Mutex<Vec<BgCand>>> = Arc::new(Mutex::new(Vec::new()));
    const CHUNK: u64 = 1 << 16;
    const TOPK: usize = 400;
    let total = (hi - lo) as u64;
    let nm = n_maps(g);
    let maps = Arc::new(sweep_maps(g));
    let t0 = Instant::now();
    let hist: Arc<Mutex<[u64; 64]>> = Arc::new(Mutex::new([0u64; 64]));
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (wins, tbl, next, done, top, hist, maps) =
            (wins.clone(), tbl.clone(), next.clone(), done.clone(), top.clone(), hist.clone(), maps.clone());
        hs.push(std::thread::spawn(move || {
            let mut local: Vec<BgCand> = Vec::new();
            let mut floor: i32 = -1000;
            let mut lh = [0u64; 64];
            let mut keys: Vec<Vec<u8>> = (0..nm).map(|_| Vec::with_capacity(K)).collect();
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= total {
                    break;
                }
                let b = (a + CHUNK).min(total);
                for off in a..b {
                    let seed = lo + off as i64;
                    let raw = raw_n(g, seed, RK);
                    for &m in maps.iter() {
                        keys_from(g, &raw, m, &mut keys[m as usize], K);
                    }
                    for (wi, w) in wins.iter().enumerate() {
                        for v in maps.iter().flat_map(|&m| (0..8u8).map(move |sub| m * 8 + sub)) {
                            let (model, map, sign, atb) = variant_parts(v);
                            let s = decode_bg(&w.runes, w.prev, &keys[map as usize], sign, atb, model, &tbl);
                            lh[((s + 400) / 20).clamp(0, 63) as usize] += 1;
                            if s > floor && s >= 0 {
                                local.push(BgCand { score: s, seed, win: wi as u8, variant: v });
                                if local.len() >= 2 * TOPK {
                                    local.sort_by(|x, y| y.score.cmp(&x.score));
                                    local.truncate(TOPK);
                                    floor = local[TOPK - 1].score;
                                }
                            }
                        }
                    }
                }
                let d = done.fetch_add(b - a, Ordering::Relaxed) + (b - a);
                if d % (CHUNK * 256) < CHUNK {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} seeds) {:.0} seeds/s, eta {:.0} s", 100.0 * d as f64 / total as f64, d, rate,
                              (total as f64 - d as f64) / rate);
                }
            }
            local.sort_by(|x, y| y.score.cmp(&x.score));
            local.truncate(TOPK);
            top.lock().unwrap().extend(local);
            let mut h = hist.lock().unwrap();
            for i in 0..64 {
                h[i] += lh[i];
            }
        }));
    }
    for h in hs {
        h.join().unwrap();
    }
    let mut all = top.lock().unwrap().clone();
    all.sort_by(|x, y| y.score.cmp(&x.score));
    all.truncate(4000);
    let mut f = fs::File::create(&out).unwrap();
    writeln!(f, "score\tseed\twindow\tmodel\tmap\tsign\tatbash").unwrap();
    for c in &all {
        let (model, map, sign, atb) = variant_parts(c.variant);
        writeln!(f, "{}\t{}\t{}\t{}\t{}\t{}\t{}", c.score, c.seed, wins[c.win as usize].name, model, map, sign, atb as u8).unwrap();
    }
    let h = hist.lock().unwrap();
    eprintln!("swept {} seeds in {:.0} s; best score {}", total, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score.to_string()).unwrap_or("none".into()));
    eprintln!("hist (bins of 20 from -400) {}", h.iter().enumerate().filter(|(_, c)| **c > 0).map(|(b, c)| format!("{b}:{c}")).collect::<Vec<_>>().join(" "));
}

/// bgscore <gen> <windows.txt> <bigram.txt> <seed> <map> <model> <sign> <atb>: the boundary-free score of one (seed, variant) on window 0 (for the tests)
fn mode_bgscore(args_all: &[String]) {
    let g = parse_gen(&args_all[0]);
    let a = &args_all[1..];
    let wins = load_windows(&a[0]);
    let tbl = load_bigram(&a[1]);
    let seed: i64 = a[2].parse().unwrap();
    let map: u8 = a[3].parse().unwrap();
    let model: u8 = a[4].parse().unwrap();
    let sign: i32 = a[5].parse().unwrap();
    let atb = a[6] == "1";
    let raw = raw_n(g, seed, RK);
    let mut keys = Vec::new();
    keys_from(g, &raw, map, &mut keys, K);
    println!("{}", decode_bg(&wins[0].runes, wins[0].prev, &keys, sign, atb, model, &tbl));
}

/// keys <gen> <seed> <map> <count>: the first `count` key values of one seed (reference for a GPU port: docs/GPU_PORT.md)
fn mode_keys(a: &[String]) {
    let g = parse_gen(&a[0]);
    let seed: i64 = a[1].parse().unwrap();
    let map: u8 = a[2].parse().unwrap();
    let count: usize = a[3].parse().unwrap();
    let raw = raw_n(g, seed, count * 3 + 64);
    let mut k = Vec::new();
    keys_from(g, &raw, map, &mut k, count);
    println!("{}", k.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("vectors") => mode_vectors(&args[2]),
        Some("keys") => mode_keys(&args[2..]),
        Some("plant") => mode_plant(&args[2..]),
        Some("sweep") => mode_sweep(&args[2..]),
        Some("verify") => mode_verify(&args[2..]),
        Some("bgsweep") => mode_bgsweep(&args[2..]),
        Some("bgscore") => mode_bgscore(&args[2..]),
        _ => eprintln!("usage: prngx vectors|keys|plant|sweep|bgsweep|bgscore|verify ... (see the header of src/main.rs)"),
    }
}
