"""H5 first slice: capped LP2 first look (45-min cap, 4 workers, numba fast_init).

Grid: 8 section windows (first 300 runes of work/kscreen/data/segments.txt) x streams
{0 = totient, 1..8 = uniform matched nulls} x offsets 0..2000 x L 2..20 x models {0,1}
= 5,474,736 cells. Chunks are 25 offsets x 19 L per (window, stream, model); chunks are
submitted in block-major order (offset block first, then window, stream, model) so that
a wall-time cap gives every (window, stream, model) combo the same prefix of offsets and
the partial-grid statement is exact. Abort (120, 0.9) everywhere.

Candidate rule: a real-grid (totient) cell with periodic IoC >= 1.6 AND >= the window's
matched-null max + 0.15 gets an in-process whole-window re-decode (beam 64, max_em 10,
slow verified init) and is reported as a CANDIDATE - flagged UNVERIFIED, not a
decryption. Writes lp2_look.txt.
"""
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "lp2_look.txt")
SEGMENTS = os.path.join(HERE, "..", "kscreen", "data", "segments.txt")

N_WIN = 8
N_NULL = 8
STREAMS = 1 + N_NULL               # 0 = totient, 1..8 = matched nulls
OFFS = list(range(0, 2001))
LS = list(range(2, 21))
MODELS = (0, 1)
ABORT_AT = 120
ABORT_MARGIN = 0.9
WORKERS = 4
CAP_S = 45 * 60
CHUNK_OFF = 25
HIT_THRESH = 1.6
MARGIN_ABOVE_NULL = 0.15
SEED_BASE = 9000

CFG = dict(litf=False, beam=24, max_em=5, abort_at=ABORT_AT, abort_margin=ABORT_MARGIN,
           beam_a=12, fast_init=True)

logf = H.english_logf()
windows = H.load_windows(SEGMENTS, n=300)
windows = windows[:N_WIN]
names = [w[0] for w in windows]
win_pairs = [(w[2], w[1]) for w in windows]          # (runes, prev) for the workers
tvals = H.totient(4000)
streams = [tvals] + [H.random_stream(4000, SEED_BASE + k) for k in range(N_NULL)]

_G = {}


def init_worker(logf_, streams_, windows_, cfg_):
    global _G
    _G = dict(logf=logf_, streams=streams_, windows=windows_, cfg=cfg_)


def run_cells(args):
    """One chunk: (wi, sid, model, off0, off1) x all L -> dict."""
    wi, sid, model, off0, off1 = args
    c, prev = _G["windows"][wi]
    tvals_ = _G["streams"][sid]
    logf_ = _G["logf"]
    cfg = _G["cfg"]
    best = (0.0, -1, -1)
    hits = []
    decodes = aborts = surv = 0
    for off in range(off0, off1):
        for L in LS:
            ioc, _ = H.decode(c, prev, tvals_, off, L, model, cfg["litf"], cfg["beam"],
                              cfg["max_em"], logf_, cfg["abort_at"], cfg["abort_margin"],
                              False, cfg.get("beam_a", 12), cfg["fast_init"])
            decodes += 1
            if ioc == 0.0:
                aborts += 1
            else:
                surv += 1
                if ioc > best[0]:
                    best = (ioc, off, L)
            if sid == 0 and ioc >= HIT_THRESH:
                hits.append((round(ioc, 4), off, L, model))
    return dict(wi=wi, sid=sid, model=model, off0=off0, off1=off1, best=best,
                decodes=decodes, aborts=aborts, surv=surv, hits=hits)


def main():
    lines = []
    def log(s=""):
        print(s, flush=True)
        lines.append(s)
        # incremental write: the output survives a killed run
        with open(OUT, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

    log("# lp2_look.txt - H5 first slice, capped LP2 first look")
    log(f"# machine: 16 logical procs at ~100% load (screen campaign); Python {sys.version.split()[0]}")
    log(f"# windows: {', '.join(names)} (first 300 runes each), stream 0 = totient, "
        f"streams 1..{N_NULL} = uniform matched nulls (random_stream seeds {SEED_BASE}..)")
    log(f"# grid: offsets 0..2000 x L 2..20 x models {{0,1}}; abort ({ABORT_AT}, {ABORT_MARGIN}); "
        f"fast_init=True (verified numba init); {WORKERS} workers; cap {CAP_S // 60} min")
    log(f"# cells total: {N_WIN} x {STREAMS} x {len(OFFS)} x {len(LS)} x {len(MODELS)} = "
        f"{N_WIN * STREAMS * len(OFFS) * len(LS) * len(MODELS)}")
    log(f"# started {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log()

    # block-major chunk order: offset block first -> uniform coverage on cap
    blocks = [(a, min(a + CHUNK_OFF, len(OFFS))) for a in range(0, len(OFFS), CHUNK_OFF)]
    task_chunks = []
    for b0, b1 in blocks:
        for wi in range(N_WIN):
            for sid in range(STREAMS):
                for m in MODELS:
                    task_chunks.append((wi, sid, m, b0, b1))
    chunks_total = len(task_chunks)

    per_win_real = {wi: (0.0, -1, -1, -1) for wi in range(N_WIN)}   # best on totient
    per_win_null = {wi: 0.0 for wi in range(N_WIN)}                 # matched-null max
    per_win_hits = {wi: [] for wi in range(N_WIN)}                  # real cells >= 1.6
    per_win_nsurv = {wi: 0 for wi in range(N_WIN)}                  # null cells that survived
    completed = []
    decodes = aborts = 0
    t0 = time.time()
    finished_at = None
    with ProcessPoolExecutor(max_workers=WORKERS, initializer=init_worker,
                             initargs=(logf, streams, win_pairs, CFG)) as ex:
        in_flight = {}
        it = iter(task_chunks)
        done_count = 0
        while True:
            while len(in_flight) < WORKERS:
                try:
                    t = next(it)
                except StopIteration:
                    break
                if time.time() - t0 > CAP_S:
                    break
                in_flight[ex.submit(run_cells, t)] = t
            if not in_flight:
                finished_at = time.time() - t0
                break
            done, _ = wait_futures(list(in_flight), 5.0)
            for fut in done:
                t = in_flight.pop(fut)
                try:
                    r = fut.result()
                except Exception as e:
                    completed.append((t[0], t[1], t[2], t[3], t[4], "ERR %s" % e))
                    continue
                done_count += 1
                completed.append((t[0], t[1], t[2], t[3], t[4], "ok"))
                decodes += r["decodes"]
                aborts += r["aborts"]
                wi, sid = r["wi"], r["sid"]
                if sid == 0:
                    if r["best"][0] > per_win_real[wi][0]:
                        per_win_real[wi] = (r["best"][0], r["best"][1], r["best"][2], r["model"])
                    per_win_hits[wi].extend(r["hits"])
                else:
                    if r["best"][0] > per_win_null[wi]:
                        per_win_null[wi] = r["best"][0]
                    per_win_nsurv[wi] += r["surv"]
                if done_count % 100 == 0:
                    el = time.time() - t0
                    log(f"[lp2] {done_count}/{chunks_total} chunks, {decodes} decodes, "
                        f"{decodes / el:.0f} decodes/s wall, {el:.0f}s")
            if time.time() - t0 > CAP_S:
                it = iter(())   # stop submitting; drain in-flight
    if finished_at is None:
        finished_at = time.time() - t0
    partial = len(completed) < chunks_total
    log(f"grid: {decodes} decodes ({aborts} aborted, "
        f"{100.0 * aborts / max(1, decodes):.1f}%) in {finished_at:.0f}s "
        f"({decodes / max(1, finished_at):.0f} decodes/s wall, {WORKERS} workers); "
        f"{len(completed)}/{chunks_total} chunks "
        f"({'PARTIAL' if partial else 'complete'})")
    log()

    # exact completed coverage per (wi, sid, model)
    cov = {}
    for wi, sid, m, a, b, status in completed:
        if status != "ok":
            continue
        cov.setdefault((wi, sid, m), []).append((a, b))
    comp = []
    for k in sorted(cov):
        rs = sorted(cov[k])
        merged = []
        for a, b in rs:
            if merged and a <= merged[-1][1]:
                merged[-1] = (merged[-1][0], max(b, merged[-1][1]))
            else:
                merged.append((a, b))
        comp.append((k, merged))

    log("== per-window: best periodic IoC (totient grid) vs matched-null max ==")
    log(f"{'window':8} {'real best IoC':>14} {'@ (off,L,m)':>22} {'null max':>9} "
        f"{'null surv':>9} {'hits>=1.6':>9}")
    for wi in range(N_WIN):
        r = per_win_real[wi]
        log(f"{names[wi]:8} {r[0]:14.4f} {str((r[1], r[2], r[3])):>22} "
            f"{per_win_null[wi]:9.4f} {per_win_nsurv[wi]:>9} {len(per_win_hits[wi]):>9}")
    log()

    log("== candidates (real IoC >= 1.6 AND >= matched-null max + 0.15, over the "
        "completed grid) ==")
    n_cand = 0
    for wi in range(N_WIN):
        threshold = per_win_null[wi] + MARGIN_ABOVE_NULL
        cands = sorted({(ioc, off, L, m) for ioc, off, L, m in per_win_hits[wi]
                        if ioc >= HIT_THRESH and ioc >= threshold}, reverse=True)
        if not cands:
            continue
        for ioc, off, L, m in cands:
            n_cand += 1
            log(f"  {names[wi]} (off {off}, L {L}, model {m}): grid IoC {ioc:.4f} >= 1.6 "
                f"and >= null max {per_win_null[wi]:.4f} + 0.15 -> whole-window re-decode")
            rioc, info = H.redecode(win_pairs[wi][0], win_pairs[wi][1], tvals, off, L, m,
                                    litf=False, beam=64, max_em=10)
            if info is None:
                log(f"    re-decode: ABORTED/empty -> not a candidate")
                continue
            wcol_ok = "all-equal" if len(set(info["wcol"])) == 1 else "varied"
            log(f"    re-decode: IoC {rioc:.4f}, wcol {info['wcol']} ({wcol_ok}), "
                f"overall {info['overall']:.4f}, ll/rune {info['ll']:.3f}")
            log(f"    -> CANDIDATE (UNVERIFIED; not a decryption; needs whole-section "
                f"English verification per docs/CAMPAIGNS.md)")
    if n_cand == 0:
        log("  none")
    log()

    if partial:
        log("== PARTIAL-GRID STATEMENT (the cap stopped the grid early) ==")
        log(f"completed {len(completed)}/{chunks_total} chunks in {finished_at:.0f}s; "
            f"blocks are 25-offset x 19-L chunks, submitted in offset-block-major order, "
            f"so each of the {N_WIN}x{STREAMS}x{len(MODELS)} = {N_WIN * STREAMS * len(MODELS)} "
            f"(window, stream, model) combos has the same offset prefix. Completed offset "
            f"coverage per combo (block list):")
        for (wi, sid, m), merged in comp:
            log(f"  win {names[wi]}, stream {sid}, model {m}: offsets "
                f"{', '.join(f'{a}-{b - 1}' for a, b in merged)}")
        bad = [c for c in completed if c[5] != "ok"]
        if bad:
            log(f"  worker errors: {bad}")
        log("  All per-window scores above are over the completed grid ONLY.")
    else:
        log("== grid complete: all 5,474,736 cells ran ==")
        log("  (offsets 0..2000 x L 2..20 x models {0,1} for all 8 windows x 9 streams)")

    log(f"# finished {time.strftime('%Y-%m-%d %H:%M:%S')}")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nwrote {OUT}")


def wait_futures(futs, timeout):
    if not futs:
        return [], []
    try:
        return list(as_completed(futs, timeout=timeout)), []
    except TimeoutError:
        return [], futs


if __name__ == "__main__":
    main()
