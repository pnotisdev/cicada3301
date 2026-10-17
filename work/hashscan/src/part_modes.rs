
// ------------------------------------------------------------------ modes

fn parse_list(s: &str) -> Vec<usize> {
    s.split(',').map(|x| x.parse().unwrap()).collect()
}

fn mode_vectors() {
    for algo in 0..ALGOS {
        for conv in 0..CONVS {
            let b = stream_bytes(algo, conv, b"cicada", 40);
            println!("{} {} {}", algo, conv, b.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "));
        }
    }
}

fn lens_of(w: &Win) -> Vec<String> {
    let mut lens = Vec::new();
    let mut l = 0;
    for i in 0..w.runes.len() {
        l += 1;
        if w.word_end[i] {
            lens.push(l.to_string());
            l = 0;
        }
    }
    lens
}

fn mode_plant(a: &[String]) {
    let algo: usize = a[0].parse().unwrap();
    let conv: usize = a[1].parse().unwrap();
    let map: usize = a[2].parse().unwrap();
    let model: u8 = a[3].parse().unwrap();
    let sign: i32 = a[4].parse().unwrap();
    let atb = a[5] == "1";
    let keep: f64 = a[6].parse().unwrap();
    let cand = a[7].as_bytes();
    let wins = load_windows(&a[8]);
    let mut lcg: u64 = 0x2545F4914F6CDD1D ^ cand.len() as u64;
    let mut coin = || {
        lcg = lcg.wrapping_mul(6364136223846793005).wrapping_add(1442695040888963407);
        (lcg >> 11) as f64 / (1u64 << 53) as f64
    };
    let mut out = String::new();
    for w in &wins {
        let need = w.runes.len() * 4 + 64;
        let bytes = stream_bytes(algo, conv, cand, need * 2 + 64);
        let mut key = Vec::new();
        keys_from(&bytes, map, &mut key, need);
        let (mut j, mut prev) = (0usize, -1i32);
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
                j += 1;
                if coin() >= keep {
                    y = md(t + sign * key[j] as i32);
                    j += 1;
                }
            }
            c.push(y as u8);
            prev = y;
        }
        out += &format!("W planted_{} -1\nR {}\nL {}\n", w.name,
                        c.iter().map(|x| x.to_string()).collect::<Vec<_>>().join(" "), lens_of(w).join(" "));
    }
    fs::write(&a[9], out).unwrap();
}

fn mode_verify(a: &[String]) {
    let algo: usize = a[0].parse().unwrap();
    let conv: usize = a[1].parse().unwrap();
    let map: usize = a[2].parse().unwrap();
    let model: u8 = a[3].parse().unwrap();
    let sign: i32 = a[4].parse().unwrap();
    let atb = a[5] == "1";
    let cand = a[6].as_bytes();
    let wins = load_windows(&a[7]);
    let dict = Dict::load(&a[8]);
    let w = wins.iter().find(|w| w.name == a[9]).expect("window");
    let bytes = stream_bytes(algo, conv, cand, w.runes.len() * 9 + 200);
    let mut key = Vec::new();
    keys_from(&bytes, map, &mut key, w.runes.len() * 3 + 50);
    let (score, plain) = decode_full(w, &key, sign, atb, model, &dict);
    let mut txt = String::new();
    for (i, p) in plain.iter().enumerate() {
        txt += LATIN[*p as usize];
        if w.word_end[i] {
            txt.push(' ');
        }
    }
    println!("{:.3}\t{}\t{}", score, a[6], &txt[..txt.len().min(400)]);
}

#[derive(Clone)]
struct Cand {
    score: u16,
    idx: u32,
    win: u8,
    variant: u16,
}

/// variant = ((algo * CONVS + conv) * MAPS + map) * 8 + model * 4 + sign_idx * 2 + atb
fn variant_parts(v: u16) -> (usize, usize, usize, u8, i32, bool) {
    let sub = (v & 7) as u8;
    let rest = (v >> 3) as usize;
    let map = rest % MAPS;
    let conv = (rest / MAPS) % CONVS;
    let algo = rest / (MAPS * CONVS);
    (algo, conv, map, (sub >> 2) & 1, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1)
}

fn mode_sweep(args: &[String]) {
    let cands: Arc<Vec<String>> = Arc::new(
        fs::read_to_string(&args[0]).expect("candidate file").lines().filter(|l| !l.is_empty()).map(|l| l.to_string()).collect(),
    );
    let wins = Arc::new(load_windows(&args[1]));
    let dict = Arc::new(Dict::load(&args[2]));
    let out = args[3].clone();
    let threads: usize = if args.len() > 4 { args[4].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let mut algos: Vec<usize> = (0..ALGOS).collect();
    let mut convs: Vec<usize> = (0..CONVS).collect();
    for extra in args.iter().skip(5) {
        if let Some(v) = extra.strip_prefix("algos=") {
            algos = parse_list(v);
        }
        if let Some(v) = extra.strip_prefix("convs=") {
            convs = parse_list(v);
        }
    }
    let (algos, convs) = (Arc::new(algos), Arc::new(convs));
    let next = Arc::new(AtomicUsize::new(0));
    let done = Arc::new(AtomicUsize::new(0));
    let top: Arc<Mutex<Vec<Cand>>> = Arc::new(Mutex::new(Vec::new()));
    const CHUNK: usize = 4096;
    const TOPK: usize = 400;
    let total = cands.len();
    let t0 = Instant::now();
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (cands, wins, dict, algos, convs, next, done, top) =
            (cands.clone(), wins.clone(), dict.clone(), algos.clone(), convs.clone(), next.clone(), done.clone(), top.clone());
        hs.push(std::thread::spawn(move || {
            let mut local: Vec<Cand> = Vec::new();
            let mut floor: u16 = 0;
            let mut keys = Vec::with_capacity(K);
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= total {
                    break;
                }
                let b = (a + CHUNK).min(total);
                for idx in a..b {
                    let s = cands[idx].as_bytes();
                    for &algo in algos.iter() {
                        for &conv in convs.iter() {
                            let bytes = stream_bytes(algo, conv, s, NEED);
                            for map in 0..MAPS {
                                keys_from(&bytes, map, &mut keys, K);
                                for (wi, w) in wins.iter().enumerate() {
                                    for sub in 0..8u16 {
                                        let (model, sign, atb) = ((sub >> 2 & 1) as u8, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1);
                                        let sc = decode_fast(w, &keys, sign, atb, model, &dict);
                                        if sc > floor || (local.len() < TOPK && sc > 0) {
                                            let variant = (((algo * CONVS + conv) * MAPS + map) as u16) * 8 + sub;
                                            local.push(Cand { score: sc, idx: idx as u32, win: wi as u8, variant });
                                            if local.len() >= 2 * TOPK {
                                                local.sort_by(|x, y| y.score.cmp(&x.score));
                                                local.truncate(TOPK);
                                                floor = local[TOPK - 1].score;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                let d = done.fetch_add(b - a, Ordering::Relaxed) + (b - a);
                if (d / CHUNK) % 256 == 0 {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} candidates) {:.0} cand/s, eta {:.0} s", 100.0 * d as f64 / total as f64, d, rate,
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
    writeln!(f, "score\tcandidate\twindow\talgo\tconv\tmap\tmodel\tsign\tatbash").unwrap();
    for c in &all {
        let (algo, conv, map, model, sign, atb) = variant_parts(c.variant);
        writeln!(f, "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}", c.score, cands[c.idx as usize], wins[c.win as usize].name, algo, conv,
                 map, model, sign, atb as u8)
            .unwrap();
    }
    eprintln!("swept {} candidates in {:.0} s; best score {}", total, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score).unwrap_or(0));
}

#[derive(Clone)]
struct BgCand {
    score: i32,
    idx: u32,
    win: u8,
    variant: u16,
}

/// bgsweep <cands.txt> <windows.txt> <bigram.txt> <out.tsv> [threads] [algos=..] [convs=..]
/// Boundary-free score (decode_bg): the first 120 runes of every window, no word separators involved.
fn mode_bgsweep(args: &[String]) {
    let cands: Arc<Vec<String>> = Arc::new(
        fs::read_to_string(&args[0]).expect("candidate file").lines().filter(|l| !l.is_empty()).map(|l| l.to_string()).collect(),
    );
    let wins = Arc::new(load_windows(&args[1]));
    let tbl = Arc::new(load_bigram(&args[2]));
    let out = args[3].clone();
    let threads: usize = if args.len() > 4 { args[4].parse().unwrap() } else {
        std::thread::available_parallelism().map(|n| n.get()).unwrap_or(4)
    };
    let mut algos: Vec<usize> = (0..ALGOS).collect();
    let mut convs: Vec<usize> = (0..CONVS).collect();
    for extra in args.iter().skip(5) {
        if let Some(v) = extra.strip_prefix("algos=") {
            algos = parse_list(v);
        }
        if let Some(v) = extra.strip_prefix("convs=") {
            convs = parse_list(v);
        }
    }
    let (algos, convs) = (Arc::new(algos), Arc::new(convs));
    let next = Arc::new(AtomicUsize::new(0));
    let done = Arc::new(AtomicUsize::new(0));
    let top: Arc<Mutex<Vec<BgCand>>> = Arc::new(Mutex::new(Vec::new()));
    const CHUNK: usize = 4096;
    const TOPK: usize = 400;
    let total = cands.len();
    let t0 = Instant::now();
    let hist: Arc<Mutex<[u64; 64]>> = Arc::new(Mutex::new([0u64; 64]));
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (cands, wins, tbl, algos, convs, next, done, top, hist) =
            (cands.clone(), wins.clone(), tbl.clone(), algos.clone(), convs.clone(), next.clone(), done.clone(), top.clone(), hist.clone());
        hs.push(std::thread::spawn(move || {
            let mut local: Vec<BgCand> = Vec::new();
            let mut floor: i32 = -1000;
            let mut lh = [0u64; 64];
            let mut keys = Vec::with_capacity(K);
            loop {
                let a = next.fetch_add(CHUNK, Ordering::Relaxed);
                if a >= total {
                    break;
                }
                let b = (a + CHUNK).min(total);
                for idx in a..b {
                    let s = cands[idx].as_bytes();
                    for &algo in algos.iter() {
                        for &conv in convs.iter() {
                            let bytes = stream_bytes(algo, conv, s, NEED);
                            for map in 0..MAPS {
                                keys_from(&bytes, map, &mut keys, K);
                                for (wi, w) in wins.iter().enumerate() {
                                    for sub in 0..8u16 {
                                        let (model, sign, atb) = ((sub >> 2 & 1) as u8, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1);
                                        let sc = decode_bg(&w.runes, w.prev, &keys, sign, atb, model, &tbl);
                                        lh[((sc + 400) / 20).clamp(0, 63) as usize] += 1;
                                        if sc > floor && sc >= 0 {
                                            let variant = (((algo * CONVS + conv) * MAPS + map) as u16) * 8 + sub;
                                            local.push(BgCand { score: sc, idx: idx as u32, win: wi as u8, variant });
                                            if local.len() >= 2 * TOPK {
                                                local.sort_by(|x, y| y.score.cmp(&x.score));
                                                local.truncate(TOPK);
                                                floor = local[TOPK - 1].score;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
                let d = done.fetch_add(b - a, Ordering::Relaxed) + (b - a);
                if (d / CHUNK) % 256 == 0 {
                    let el = t0.elapsed().as_secs_f64();
                    let rate = d as f64 / el;
                    eprintln!("{:.2}% ({} candidates) {:.0} cand/s, eta {:.0} s", 100.0 * d as f64 / total as f64, d, rate,
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
    writeln!(f, "score\tcandidate\twindow\talgo\tconv\tmap\tmodel\tsign\tatbash").unwrap();
    for c in &all {
        let (algo, conv, map, model, sign, atb) = variant_parts(c.variant);
        writeln!(f, "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}", c.score, cands[c.idx as usize], wins[c.win as usize].name, algo, conv,
                 map, model, sign, atb as u8)
            .unwrap();
    }
    let h = hist.lock().unwrap();
    eprintln!("swept {} candidates in {:.0} s; best score {}", total, t0.elapsed().as_secs_f64(),
              all.first().map(|c| c.score.to_string()).unwrap_or("none".into()));
    eprintln!("hist (bins of 20 from -400) {}", h.iter().enumerate().filter(|(_, c)| **c > 0).map(|(b, c)| format!("{b}:{c}")).collect::<Vec<_>>().join(" "));
}

/// bgscores <candidate> <windows.txt> <bigram.txt>: every (algo, conv, map, sub) score of the candidate on window 0 (for the tests)
fn mode_bgscores(a: &[String]) {
    let cand = a[0].as_bytes();
    let wins = load_windows(&a[1]);
    let tbl = load_bigram(&a[2]);
    let w = &wins[0];
    let mut keys = Vec::new();
    for algo in 0..ALGOS {
        for conv in 0..CONVS {
            let bytes = stream_bytes(algo, conv, cand, NEED);
            for map in 0..MAPS {
                keys_from(&bytes, map, &mut keys, K);
                for sub in 0..8u16 {
                    let (model, sign, atb) = ((sub >> 2 & 1) as u8, if (sub >> 1) & 1 == 0 { 1 } else { -1 }, sub & 1 == 1);
                    println!("{} {} {} {} {}", algo, conv, map, sub, decode_bg(&w.runes, w.prev, &keys, sign, atb, model, &tbl));
                }
            }
        }
    }
}

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("vectors") => mode_vectors(),
        Some("plant") => mode_plant(&args[2..]),
        Some("sweep") => mode_sweep(&args[2..]),
        Some("verify") => mode_verify(&args[2..]),
        Some("bgsweep") => mode_bgsweep(&args[2..]),
        Some("bgscores") => mode_bgscores(&args[2..]),
        _ => eprintln!("usage: hashscan vectors|plant|sweep|bgsweep|bgscores|verify ... (see the header of src/main.rs)"),
    }
}
