"""H5 first slice: controls (a), (b), (d) + (c) degeneracy record. Writes control.txt.

Abort (120, 0.9) everywhere (recalibrated; FAST_REPORT.md sec 2). Grid chunks run in 4
worker processes; any grid is capped at 45 min of wall time with exact partial-grid
accounting. decode() uses fast_init=True (the verified v3 init).

Control (a): grid offsets 0..2000 x L 1..20 x models {0,1} on the truth plant
(Self-Reliance 3000:3300, totient + DIVINITY at offset 1234, model 0, keep 0.19, seed 42,
per calib.py) must return EXACTLY (1234, 8, model 0) with periodic IoC >= 1.6 and
wcol = DIVINITY.
Control (b): 8 random-window/random-stream nulls over the same grid; everything < 1.45.
Control (c): the no-keyword plant (L=1 constant key) decoded at L=8 - the L=1/L=8
degeneracy is a model-class issue (a constant keyword IS an L=8 keyword); recorded, NOT
a decoder failure.
Control (d): wrong-L decodes of the truth plant (L in {7, 9, 16}) stay < 1.4 (plus wrong
offsets for extra info).
"""
import math
import os
import random
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h5slice as H
import sim

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "control.txt")

OFFS = list(range(0, 2001))
LS_ALL = list(range(1, 21))
MODELS = (0, 1)
ABORT_AT = 120
ABORT_MARGIN = 0.9
WORKERS = 4
CAP_S = 45 * 60
CHUNK_OFF = 25

logf = H.english_logf()
plain = sim.english_runes()[3000:3300]
tvals = H.totient(4000)
TRUTH_OFF = 1234
c_truth = H.plant(plain, tvals, TRUTH_OFF, H.DIVINITY, 0, keep=0.19, litf=False, b=0, seed=42)

CFG = dict(litf=False, beam=24, max_em=5, abort_at=ABORT_AT, abort_margin=ABORT_MARGIN,
           beam_a=12, fast_init=True)

_G = {}


def init_worker(logf_, streams_, windows_, cfg_):
    global _G
    _G = dict(logf=logf_, streams=streams_, windows=windows_, cfg=cfg_)


def run_cells(args):
    """One chunk: (wi, stream_id, model, off0, off1, Ls) -> dict of results."""
    wi, stream_id, model, off0, off1, Ls = args
    c, prev = _G["windows"][wi]
    tvals_ = _G["streams"][stream_id]
    logf_ = _G["logf"]
    cfg = _G["cfg"]
    best = (0.0, -1, -1)
    hits = []
    hit_thresh = cfg.get("hit_thresh", 0.0)
    decodes = 0
    aborts = 0
    for off in range(off0, off1):
        for L in Ls:
            ioc, _ = H.decode(c, prev, tvals_, off, L, model, cfg["litf"], cfg["beam"],
                              cfg["max_em"], logf_, cfg["abort_at"], cfg["abort_margin"],
                              False, cfg.get("beam_a", 12), cfg["fast_init"])
            decodes += 1
            if ioc == 0.0:
                aborts += 1
            if ioc > best[0]:
                best = (ioc, off, L)
            if ioc >= hit_thresh:
                hits.append((round(ioc, 4), off, L))
    return dict(wi=wi, stream_id=stream_id, model=model, off0=off0, off1=off1,
                best=best, decodes=decodes, aborts=aborts, hits=hits)


def chunks(offs, ls, models, ch):
    out = []
    for m in models:
        for a in range(0, len(offs), ch):
            out.append((m, offs[a], offs[min(a + ch, len(offs))], ls))
    return out


def run_grid(windows, streams, grid_models, offs, ls, cfg, cap_s, label, hit_thresh=0.0,
             order=None):
    """Run grid chunks in WORKERS processes with a wall-time cap.

    order: list of (wi, stream_id) pairs to prioritize; chunks are submitted per pair,
    models interleaved. Returns (per_pair_best, per_pair_hits, stats) where stats
    records completed (wi, stream_id, model, off0, off1) chunks and timing.
    """
    cfg = dict(cfg)
    cfg["hit_thresh"] = hit_thresh
    pairs = order if order is not None else [(wi, sid) for wi in range(len(windows))
                                             for sid in range(len(streams))]
    task_chunks = []
    for wi, sid in pairs:
        for m, a, b, lss in chunks(offs, ls, grid_models, CHUNK_OFF):
            task_chunks.append((wi, sid, m, a, b, lss))
    per_pair_best = {p: (0.0, -1, -1, -1) for p in pairs}
    per_pair_hits = {p: [] for p in pairs}
    completed = []
    decodes = aborts = 0
    t0 = time.time()
    finished_at = None
    with ProcessPoolExecutor(max_workers=WORKERS, initializer=init_worker,
                             initargs=(logf, streams, windows, cfg)) as ex:
        in_flight = {}
        it = iter(task_chunks)
        while True:
            # top up in-flight to WORKERS
            while len(in_flight) < WORKERS:
                try:
                    t = next(it)
                except StopIteration:
                    break
                if time.time() - t0 > cap_s:
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
                except Exception as e:  # worker crash: record, keep going
                    completed.append((t[0], t[1], t[2], t[3], t[4], "ERR %s" % e))
                    continue
                completed.append((t[0], t[1], t[2], t[3], t[4], "ok"))
                decodes += r["decodes"]
                aborts += r["aborts"]
                p = (r["wi"], r["stream_id"])
                if r["best"][0] > per_pair_best[p][0]:
                    per_pair_best[p] = (r["best"][0], r["best"][1], r["best"][2], r["model"])
                per_pair_hits[p].extend((h[0], h[1], h[2], r["model"]) for h in r["hits"])
            if time.time() - t0 > cap_s:
                # stop submitting new chunks; drain whatever is in flight
                it = iter(())
    if finished_at is None:
        finished_at = time.time() - t0
    stats = dict(label=label, secs=finished_at, decodes=decodes, aborts=aborts,
                 chunks_done=len(completed), chunks_total=len(task_chunks), completed=completed)
    return per_pair_best, per_pair_hits, stats


def wait_futures(futs, timeout):
    """Wait up to timeout for any future; return (done, not_done)."""
    if not futs:
        return [], []
    try:
        return list(as_completed(futs, timeout=timeout)), []
    except TimeoutError:
        return [], futs


def fmt_cells(stats):
    return (f"{stats['label']}: {stats['decodes']} decodes, {stats['aborts']} aborted "
            f"({100.0 * stats['aborts'] / max(1, stats['decodes']):.1f}%), "
            f"{stats['chunks_done']}/{stats['chunks_total']} chunks in {stats['secs']:.0f}s "
            f"({stats['decodes'] / max(1, stats['secs']):.0f} decodes/s wall, {WORKERS} workers)")


def main():
    lines = []
    def log(s=""):
        print(s, flush=True)
        lines.append(s)

    log(f"# control.txt - H5 first slice controls, abort ({ABORT_AT}, {ABORT_MARGIN}), "
        f"fast_init=True, {WORKERS} workers, cap {CAP_S // 60} min")
    log(f"# machine: 16 logical procs at ~100% load (screen campaign); Python {sys.version.split()[0]}")
    log(f"# plant: Self-Reliance 3000:3300, totient + DIVINITY, offset {TRUTH_OFF}, model 0, "
        f"keep 0.19, seed 42")
    log(f"# started {time.strftime('%Y-%m-%d %H:%M:%S')}")
    log()

    # ---- (a) truth grid -----------------------------------------------------
    log("== control (a): truth plant grid offsets 0..2000 x L 1..20 x models {0,1} ==")
    t0 = time.time()
    per_best, per_hits, stats = run_grid(
        [(c_truth, -1)], [tvals], MODELS, OFFS, LS_ALL, CFG, CAP_S, "ctrl-a truth grid")
    log(fmt_cells(stats))
    best = per_best[(0, 0)]
    log(f"  grid argmax: IoC {best[0]:.4f} at (offset {best[1]}, L {best[2]}, model {best[3]})")
    a_ok = (best[1], best[2], best[3]) == (TRUTH_OFF, 8, 0)
    if best[0] == 0.0:
        log("  FAIL: the grid argmax aborted (no score) - truth cell did not survive the abort")
        a_ok = False
    # verify the cell at the argmax (and at truth if argmax differs)
    verify_cells = [(TRUTH_OFF, 8, 0)]
    if (best[1], best[2], best[3]) != (TRUTH_OFF, 8, 0):
        verify_cells.append((best[1], best[2], best[3]))
    for off, L, m in verify_cells:
        ioc, wcol = H.decode(c_truth, -1, tvals, off, L, m, CFG["litf"], CFG["beam"],
                             CFG["max_em"], logf, ABORT_AT, ABORT_MARGIN, False, 12, True)
        log(f"  decode at (off {off}, L {L}, model {m}): IoC {ioc:.4f} wcol {wcol}")
        if (off, L, m) == (TRUTH_OFF, 8, 0):
            if ioc < 1.6 or wcol != H.DIVINITY:
                log("  FAIL: truth cell IoC < 1.6 or wcol != DIVINITY")
                a_ok = False
            else:
                log("  truth cell ok: IoC >= 1.6 and wcol == DIVINITY")
    if not a_ok:
        log(f"  CONTROL (a) FAIL: grid argmax is not exactly (1234, 8, model 0)")
    else:
        log(f"  CONTROL (a) PASS: argmax exactly (1234, 8, model 0), IoC {best[0]:.4f} >= 1.6")
    hits_a = per_hits[(0, 0)]
    hits_a_sorted = sorted(set(hits_a), reverse=True)[:10]
    log(f"  runner-up cells with IoC >= 1.5: {hits_a_sorted[:8]}")
    log(f"  (a) wall {time.time() - t0:.0f}s")
    log()

    # ---- (b) null grids -----------------------------------------------------
    log("== control (b): 8 random-window/random-stream nulls, same grid; all < 1.45 ==")
    rng = random.Random(11)
    null_windows = [(list(rng.randrange(29) for _ in range(300)), -1) for _ in range(8)]
    null_streams = [H.random_stream(4000, 400 + k) for k in range(8)]
    t0 = time.time()
    nb_best, nb_hits, nb_stats = run_grid(
        null_windows, null_streams, MODELS, OFFS, LS_ALL, CFG, CAP_S, "ctrl-b null grids",
        order=[(wi, wi) for wi in range(8)])
    log(fmt_cells(nb_stats))
    gmax = 0.0
    gmax_at = None
    b_ok = True
    for wi in range(8):
        b_ = nb_best[(wi, wi)]
        log(f"  null {wi}: max IoC {b_[0]:.4f} at (off {b_[1]}, L {b_[2]}, model {b_[3]})")
        if b_[0] > gmax:
            gmax, gmax_at = b_[0], (wi, b_[1], b_[2], b_[3])
        if b_[0] >= 1.45:
            b_ok = False
    log(f"  null global max IoC {gmax:.4f} at {gmax_at}")
    if not nb_stats["completed"] or len(nb_stats["completed"]) < nb_stats["chunks_total"]:
        log("  PARTIAL: not all null chunks completed before the cap (see below)")
    log(f"  CONTROL (b) {'PASS' if b_ok else 'FAIL'}: everything < 1.45 periodic IoC")
    log(f"  (b) wall {time.time() - t0:.0f}s")
    if nb_stats["completed"] and nb_stats["completed"][-1] and nb_stats["completed"][-1][5] != "ok":
        log("  (worker errors recorded in the completed list)")
    log()

    # ---- (c) no-keyword degeneracy (recorded, not a failure) ----------------
    log("== control (c): no-keyword plant (L=1 constant key) decoded at L=8 (degeneracy note) ==")
    c_nk = H.plant(plain, tvals, TRUTH_OFF, [7], 0, keep=0.19, litf=False, b=0, seed=42)
    ioc_nk, wcol_nk = H.decode(c_nk, -1, tvals, TRUTH_OFF, 8, 0, CFG["litf"], CFG["beam"],
                               CFG["max_em"], logf, ABORT_AT, ABORT_MARGIN, False, 12, True)
    log(f"  no-keyword plant at L=8: IoC {ioc_nk:.4f}, wcol {wcol_nk}")
    log(f"  wcol all-equal: {len(set(wcol_nk)) == 1}")
    log("  NOTE: L=1 is nested in the L=8 model class (a constant keyword IS an L=8 keyword);")
    log("  a fit here is a legitimate model-identification caveat, NOT a decoder failure.")
    log()

    # ---- (d) wrong-L / wrong-offset -----------------------------------------
    log("== control (d): wrong-L decodes of the truth plant stay < 1.4 ==")
    d_ok = True
    for desc, off, L in [("wrongL7", TRUTH_OFF, 7), ("wrongL9", TRUTH_OFF, 9),
                         ("wrongL16", TRUTH_OFF, 16)]:
        ioc, wcol = H.decode(c_truth, -1, tvals, off, L, 0, CFG["litf"], CFG["beam"],
                             CFG["max_em"], logf, ABORT_AT, ABORT_MARGIN, False, 12, True)
        log(f"  {desc}: IoC {ioc:.4f}" + (" (aborted)" if ioc == 0.0 else f" wcol {wcol}"))
        if ioc >= 1.4:
            d_ok = False
    for desc, off, L in [("off-1", TRUTH_OFF - 1, 8), ("off+1", TRUTH_OFF + 1, 8),
                         ("off+100", TRUTH_OFF + 100, 8)]:
        ioc, wcol = H.decode(c_truth, -1, tvals, off, L, 0, CFG["litf"], CFG["beam"],
                             CFG["max_em"], logf, ABORT_AT, ABORT_MARGIN, False, 12, True)
        log(f"  {desc} (extra info): IoC {ioc:.4f}" + (" (aborted)" if ioc == 0.0 else ""))
    log(f"  CONTROL (d) {'PASS' if d_ok else 'FAIL'}: wrong-L IoC < 1.4")
    log()

    # ---- verdict ------------------------------------------------------------
    verdict = "PASS" if (a_ok and b_ok and d_ok) else "FAIL"
    log(f"CONTROLS VERDICT: {verdict}  (a={a_ok} b={b_ok} d={d_ok}; (c) recorded as "
        f"model-class note)")
    if not a_ok or not b_ok or not d_ok:
        log("  -> LP2 first look must NOT be trusted on the failing control; see notes.")
    log(f"# finished {time.strftime('%Y-%m-%d %H:%M:%S')}")
    with open(OUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
