"""Phase 23 LP2 screen: the frozen rule of work/log/phase23_book_key_decoder.md, stage 1 (beam score only).

For each candidate book and key spelling, every book offset in steps of 8, the first 729 runes of each of LP2's 8 sections
of >= 729 runes are decoded with the table-free beam (book_key_decoder.beam_decode, spread 8). Stage-1 hit: beam score per
rune above the frozen 729-rune threshold (digraph -0.0112, letters -0.0417). Hits are only candidates for the whole-section
verification of the spec; nothing here verifies anything.

    python work/book_key_screen.py selftest            # plants through this file's own code path; must pass first
    python work/book_key_screen.py run <book> [workers] # resumable: finished chunks are skipped
    python work/book_key_screen.py summary             # -> results/analysis/book_key_screen_<machine>.txt
"""
import os
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402
from book_key_decoder import LN_SKIP, SPREAD, beam_decode, encrypt_skip_ptr, log_ratio  # noqa: E402
from book_key_flatness import HERE, dist, flattest_table, gutenberg_body, to_runes  # noqa: E402

ROOT = os.path.dirname(HERE)
N, WIN, TOPK = lp.N, 729, 10
THR = {"digraph": -0.0112, "letters": -0.0417}      # frozen in the spec (gate tail, p = 5e-10)
GATE_TAIL = {"digraph": (-0.2312, 0.0213), "letters": (-0.2441, 0.0220)}   # mu, sd of the gate's 729-rune tail
C = os.path.join(HERE, "ref", "corpora")
BOOKS = {   # smallest first; the queue runs them in this order
    "liber_al": (os.path.join(C, "cited", "liber_al_oto.txt"), False),
    "blake_songs": (os.path.join(C, "cited", "pg1934.txt"), True),
    "blake_mhh": (os.path.join(C, "cited", "pg45315.txt"), True),
    "emerson": (os.path.join(HERE, "ref", "emerson_essays1.txt"), True),
    "mabinogion": (os.path.join(C, "cited", "pg5160.txt"), True),
    "agrippa": (os.path.join(C, "cited", "agrippa_1651_archive_djvu.txt"), False),
    "kjv": (os.path.join(C, "pg10.txt"), True),
    # Cicada's Agrippa (Gibson's poem; edition confirmed by reproducing the 2012 book code, phase 31 addendum 2)
    "agrippa_gibson": (os.path.join(HERE, "ref", "user_downloads", "agrippa_gibson_wayback_20190322.txt"), False),
}
_cache = {}


def machine():
    try:
        return open(os.path.join(ROOT, ".lp_machine")).read().strip() or "unknown"
    except OSError:
        return "unknown"


OUT = os.path.join(ROOT, "results", "book_key_screen", machine())


def key_of(book, spell):
    if (book, spell) not in _cache:
        path, pg = BOOKS[book]
        raw = gutenberg_body(path) if pg else open(path, encoding="utf-8", errors="ignore").read()
        _cache[(book, spell)] = to_runes(raw, letters=spell == "letters")
    return _cache[(book, spell)]


def model():
    if "MT" not in _cache:
        _cache["MT"] = log_ratio(to_runes(gutenberg_body(os.path.join(C, "pg205.txt"))))
    return _cache["MT"]


def lp2_windows():
    segs = lp.load_segments()
    out = []
    for i in range(7, 16):
        r = lp.runes_of(segs[i])
        if len(r) >= WIN:
            out.append((f"0.{i}", np.array(r[:WIN], dtype=np.int64)))
    assert len(out) == 8, [w for w, _ in out]
    return out


def scan(windows, K, offsets, thr):
    """Beam score per rune of every window at every offset: per-window stats, top-K and all stage-1 hits."""
    MT = model()
    rows = []
    for name, c in windows:
        s = np.array([beam_decode(c, K, int(o), MT, 64, LN_SKIP, 8, SPREAD)[0] / len(c) for o in offsets])
        top = np.argsort(-s)[:TOPK]
        rows.append({"window": name, "n": len(s), "sum": float(s.sum()), "sumsq": float((s ** 2).sum()),
                     "top": [(int(offsets[t]), float(s[t])) for t in top],
                     "hits": [(int(offsets[t]), float(s[t])) for t in np.nonzero(s > thr)[0]]})
    return rows


def grid_of(K):
    return np.arange(0, max(1, len(K) - WIN - 40), SPREAD)


def chunk_size(n_grid):
    """About 32 chunks for a small book (all workers busy), at most 1024 grid offsets per chunk for a large one."""
    return int(min(1024, max(64, -(-n_grid // 32))))


def chunk_path(book, spell, k):
    return os.path.join(OUT, book, f"{spell}_{k:05d}.tsv")


def run_chunk(args):
    book, spell, k = args
    path = chunk_path(book, spell, k)
    if os.path.exists(path):
        return path, 0.0
    K = key_of(book, spell)
    grid = grid_of(K)
    cs = chunk_size(len(grid))
    offs = grid[k * cs:(k + 1) * cs]
    t0 = time.perf_counter()
    rows = scan(lp2_windows(), K, offs, THR[spell])
    lines = [f"# book {book} spelling {spell} chunk {k} offsets {int(offs[0])}..{int(offs[-1])} step {SPREAD}; "
             f"threshold {THR[spell]}; window = first {WIN} runes"]
    for r in rows:
        lines.append(f"stats\t{r['window']}\t{r['n']}\t{r['sum']:.6f}\t{r['sumsq']:.6f}")
        lines += [f"top\t{r['window']}\t{o}\t{v:.6f}" for o, v in r["top"]]
        lines += [f"HIT\t{r['window']}\t{o}\t{v:.6f}" for o, v in r["hits"]]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    os.replace(path + ".tmp", path)
    return path, time.perf_counter() - t0


def run(book, workers):
    from multiprocessing import Pool
    tasks = []
    for spell in ("digraph", "letters"):
        n = len(grid_of(key_of(book, spell)))
        tasks += [(book, spell, k) for k in range(-(-n // chunk_size(n)))]
    todo = [t for t in tasks if not os.path.exists(chunk_path(*t))]
    print(f"{book}: {len(tasks)} chunks x 8 windows, {len(todo)} to do, {workers} workers", flush=True)
    model()
    beam_decode(np.zeros(20, np.int64), np.zeros(100, np.int64), 0, model(), 64, LN_SKIP, 8, SPREAD)   # compile once
    t0 = time.time()
    with Pool(workers) as pool:
        for i, (path, dt) in enumerate(pool.imap_unordered(run_chunk, todo), 1):
            print(f"  {i}/{len(todo)} {os.path.relpath(path, ROOT)} {dt:.0f} s (elapsed {time.time() - t0:.0f} s)", flush=True)


def selftest():
    """Plants with a flattening table through scan(): the true offset's grid point must be a stage-1 hit; uniform-key
    ciphers must give none. Power at 729 runes is 80-93%, so 4 of 6 plants per spelling is the pass mark."""
    rng = np.random.default_rng(3323)
    em = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    P = to_runes(em)
    ok = True
    for spell in ("digraph", "letters"):
        K = key_of("liber_al", spell)
        _, pi = flattest_table(dist(P), dist(K), rng, restarts=3)
        table = np.argsort(pi)
        found, null_hits, t0, calls = 0, 0, time.perf_counter(), 0
        for r in range(6):
            o = int(rng.integers(100, len(K) - 3 * WIN))
            po = int(rng.integers(0, len(P) - WIN))
            c, _ = encrypt_skip_ptr(P[po:po + WIN], table[K[o:o + 3 * WIN]], rng)
            cu, _ = encrypt_skip_ptr(P[po:po + WIN], rng.integers(0, N, 3 * WIN), rng)
            g = o - o % SPREAD                                     # the screen's grid point at or below the truth
            offs = np.arange(g - 4 * SPREAD, g + 5 * SPREAD, SPREAD)
            rows = scan([("plant", c), ("uniform", cu)], K, offs, THR[spell])
            calls += 2 * len(offs)
            hit = any(abs(h - g) <= SPREAD for h, _ in rows[0]["hits"])
            found += hit
            null_hits += len(rows[1]["hits"])
            print(f"  {spell} plant {r}: true offset {o}, best {rows[0]['top'][0]}, hit {hit}; "
                  f"uniform best {rows[1]['top'][0][1]:+.4f}", flush=True)
        dt = (time.perf_counter() - t0) / calls
        print(f"selftest {spell}: {found}/6 plants found, {null_hits} uniform-key hits, beam {dt * 1e3:.1f} ms per "
              f"decode = {dt / SPREAD * 1e3:.2f} ms per book-offset per window", flush=True)
        ok &= found >= 4 and null_hits == 0
    w = lp2_windows()
    print("LP2 windows:", ", ".join(f"{n} ({len(c)})" for n, c in w))
    print("SELFTEST", "PASS" if ok else "FAIL")
    if ok:
        os.makedirs(OUT, exist_ok=True)
        open(os.path.join(OUT, "SELFTEST_PASS"), "w").write("book_key_screen selftest passed\n")
    return ok


def summary():
    out = [f"Phase 23 LP2 screen, stage 1 (beam score per rune, first {WIN} runes of 8 sections, offsets step {SPREAD}); "
           f"machine {machine()}. Nothing in LP2 is solved; a stage-1 hit is unverified.",
           f"Thresholds (frozen): digraph {THR['digraph']}, letters {THR['letters']}. Gate tail at 729 runes (uniform-key "
           f"ciphers vs KJV offsets): digraph {GATE_TAIL['digraph'][0]} +- {GATE_TAIL['digraph'][1]}, letters "
           f"{GATE_TAIL['letters'][0]} +- {GATE_TAIL['letters'][1]}.", ""]
    for book in BOOKS:
        for spell in ("digraph", "letters"):
            d = os.path.join(OUT, book)
            files = sorted(f for f in os.listdir(d) if f.startswith(spell) and f.endswith(".tsv")) if os.path.isdir(d) else []
            n_all = len(grid_of(key_of(book, spell)))
            need = -(-n_all // chunk_size(n_all))
            st, top, hits = {}, {}, []
            for f in files:
                for line in open(os.path.join(d, f), encoding="utf-8"):
                    p = line.rstrip("\n").split("\t")
                    if p[0] == "stats":
                        a = st.setdefault(p[1], [0, 0.0, 0.0])
                        a[0] += int(p[2]); a[1] += float(p[3]); a[2] += float(p[4])
                    elif p[0] == "top":
                        top.setdefault(p[1], []).append((float(p[3]), int(p[2])))
                    elif p[0] == "HIT":
                        hits.append((p[1], int(p[2]), float(p[3])))
            mu0, sd0 = GATE_TAIL[spell]
            out.append(f"{book} / {spell}: {len(files)}/{need} chunks done; stage-1 hits {len(hits)}")
            for w in sorted(st):
                n, s1, s2 = st[w]
                mu = s1 / n
                sd = max(s2 / n - mu * mu, 0) ** 0.5
                best = max(top[w])
                out.append(f"    {w}: {n} offsets, mean {mu:+.4f} sd {sd:.4f}, best {best[0]:+.4f} at offset {best[1]} "
                           f"(gate z {(best[0] - mu0) / sd0:+.1f}, own z {(best[0] - mu) / sd:+.1f})")
            for h in sorted(hits, key=lambda x: -x[2])[:50]:
                out.append(f"    HIT {h[0]} offset {h[1]} score {h[2]:+.4f}")
    text = "\n".join(out) + "\n"
    path = os.path.join(ROOT, "results", "analysis", f"book_key_screen_{machine()}.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "selftest"
    if cmd == "selftest":
        sys.exit(0 if selftest() else 1)
    elif cmd == "run":
        if not os.path.exists(os.path.join(OUT, "SELFTEST_PASS")):
            sys.exit("run the selftest first (it writes SELFTEST_PASS)")
        run(sys.argv[2], int(sys.argv[3]) if len(sys.argv) > 3 else 15)
    elif cmd == "summary":
        summary()
