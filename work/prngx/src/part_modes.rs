
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
    let t0 = Instant::now();
    let mut hs = Vec::new();
    for _ in 0..threads {
        let (wins, dict, next, done, top) = (wins.clone(), dict.clone(), next.clone(), done.clone(), top.clone());
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
                    for m in 0..nm {
                        keys_from(g, &raw, m, &mut keys[m as usize], K);
                    }
                    for (wi, w) in wins.iter().enumerate() {
                        for v in 0..(nm * 8) {
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

fn main() {
    let args: Vec<String> = env::args().collect();
    match args.get(1).map(|s| s.as_str()) {
        Some("vectors") => mode_vectors(&args[2]),
        Some("plant") => mode_plant(&args[2..]),
        Some("sweep") => mode_sweep(&args[2..]),
        Some("verify") => mode_verify(&args[2..]),
        _ => eprintln!("usage: prngx vectors|plant|sweep|verify ... (see the header of src/main.rs)"),
    }
}
