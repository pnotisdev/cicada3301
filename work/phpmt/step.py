#!/usr/bin/env python3
"""Seed sweeps for the STEP-DOMAIN cipher (work/kscreen/step28.py; research note C2): CUDA only (CuPy + NVRTC), the numpy
reference `ref_scores` (built on step28.py and the Rust `keys` mode) is the check.

    python work/phpmt/step.py sweep <gen> <07|all> <lo> <hi> <out.tsv> [thr]
    python work/phpmt/step.py probe

gen: php glibc net py3 mt32 mt31 java msvc drand48 ruby (the generators of phpmt.cu / src/gens.rs). Windows: `07` = the first
NS steps of section 0.7 (one pad from the start of LP2); `all` = every section at both pad starts (a fresh seed per section).
Per seed and window (240 steps) the kernel scores 144 settings: variant A (keys mod 28) / B (log2 of the non-zero keys of Z29) / C (rank) x key map 0/1 x
zero steps spending a key value or not x the 12 unit multipliers of Z28. Score = index of coincidence of the decoded classes.
"""
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(WORK / "kscreen"))
os.environ.setdefault("CUPY_CACHE_DIR", str(HERE / "target" / "cupy_cache"))      # git-ignored build folder
import gpu_common  # noqa: E402
import step28  # noqa: E402
from gpu_common import NVRTC_OPTIONS  # noqa: E402

NS = 240                         # steps per window (key values per seed: K = 256 in stepmt.cu)
NC, NM = 28, 12
NCOMBO = 144                     # 3 variants x 2 key maps x 2 modes x 12 multipliers
HB = 64
BLOCK = 128
CCAP = 1 << 20
TARGET_S = 0.3                   # seconds per launch (Windows' display watchdog resets the GPU after ~2 s)
TOPK = 4000
THR = 1.37                       # candidate floor: P(chi2_27 tail) 1e-12 at 240 steps; a random maximum over 4e11 settings is about 1.33
KERNEL = HERE / "stepmt.cu"
GENS = {"php": 0, "glibc": 1, "net": 2, "py3": 3, "mt32": 4, "mt31": 5, "java": 6, "msvc": 7, "drand48": 8, "ruby": 9}


def make_windows(spec):
    """[(name, prev rune, NS runes)]: `07` the first window of section 0.7; `all` every section at pad starts 0 and 1"""
    import lp
    import stats
    out = []
    for i in stats.UNSOLVED:
        c = np.array(lp.runes_of(stats.SEGS[i]))
        prev = int(lp.runes_of(stats.SEGS[i - 1])[-1]) if i > 7 else -1
        if spec == "07" and i != 7:
            continue
        if prev >= 0:
            out.append((f"sec0.{i}@0", prev, c[:NS]))
        out.append((f"sec0.{i}@1", int(c[0]), c[1:1 + NS]))
    return out


def window_arrays(wins):
    """J[nw][3 variants A, B, C][NS] (255 = zero step) and key indices [nw][2 modes (drop, keep)][NS]"""
    J = np.zeros((len(wins), 3, NS), np.uint8)
    ix = np.zeros((len(wins), 2, NS), np.uint8)
    for w, (_, prev, runes) in enumerate(wins):
        for v, variant in enumerate("ABC"):
            J[w, v] = step28.step_classes(runes, prev, variant)
        for m, mode in enumerate(("drop", "keep")):
            ix[w, m] = step28.key_index(step28.step_classes(runes, prev, "A"), mode)
    return J, ix


def combo_parts(c):
    """combo id -> (variant letter, key map, mode, multiplier)"""
    mi, c = c % NM, c // NM
    mode, c = c % 2, c // 2
    mp, var = c % 2, c // 2
    return "ABC"[var], mp, ("drop", "keep")[mode], step28.UNITS[mi]


def ref_scores(k28, k29, wins):
    """numpy reference of the kernel: {(window, combo): (sum of squares, steps counted)} from the two key sets
    (k28[map], k29[map]: arrays of the first 256 key values)"""
    J, ix = window_arrays(wins)
    out = {}
    for w in range(len(wins)):
        for combo in range(NCOMBO):
            variant, mp, mode, m = combo_parts(combo)
            if variant != "B":
                key = np.asarray(k28[mp], np.int64)
            else:
                v = np.asarray(k29[mp], np.int64)
                key = step28.LOG2[v[v != 0]]
            Jw = J[w, "ABC".index(variant)].astype(np.int64)
            idx = ix[w, 0 if mode == "drop" else 1].astype(np.int64)
            ok = (Jw != 255) & (idx < len(key))
            d = (Jw[ok] - (m * key[idx[ok]]) % NC) % NC
            out[(w, combo)] = (int((np.bincount(d, minlength=NC) ** 2).sum()), int(ok.sum()))
    return out


class Step:
    def __init__(self, gen, wins, dump=0):
        import cupy as cp
        self.cp, self.gen, self.wins = cp, gen, wins
        defs = {"GEN": GENS[gen], "NW": len(wins), "NS": NS, "DUMP": dump}
        src = "".join(f"#define {k} {v}\n" for k, v in defs.items()) + KERNEL.read_text(encoding="utf-8")
        self.kernel = cp.RawModule(code=src, options=NVRTC_OPTIONS).get_function("step_kernel")
        J, ix = window_arrays(wins)
        self.d = [cp.asarray(J.ravel()), cp.asarray(ix.ravel())]
        self.hist = cp.zeros(HB, cp.uint64)
        self.cand = cp.zeros(2 * CCAP, cp.uint32)
        self.ccount = cp.zeros(1, cp.uint32)

    def launch(self, seed0, n, thr=THR, dump=None):
        cp = self.cp
        self.ccount[:] = 0
        self.kernel(((n + BLOCK - 1) // BLOCK,), (BLOCK,), (
            *self.d, np.uint64(seed0), np.uint64(n), np.float32(thr), self.hist, self.cand, self.ccount, np.uint32(CCAP),
            dump if dump is not None else self.cand))
        cp.cuda.Stream.null.synchronize()
        return int(self.ccount[0])

    def scores(self, lo, n):
        """GPU scores {(seed, window, combo): (ss, n)} of the seeds lo..lo+n (DUMP=1 build)"""
        d = self.cp.zeros(n * len(self.wins) * NCOMBO, self.cp.uint32)
        self.launch(lo, n, 1e9, d)
        d = d.get().reshape(n, len(self.wins), NCOMBO)
        return {(lo + g, w, c): (int(d[g, w, c] & 0xFFFF), int(d[g, w, c] >> 16))
                for g in range(n) for w in range(len(self.wins)) for c in range(NCOMBO)}

    def keys(self, lo, n):
        """GPU key sets (DUMP=2 build): {seed: (k28 [2][K], k29 [2][K])}"""
        d = self.cp.zeros(n * 4 * 256, self.cp.uint32)
        self.launch(lo, n, 1e9, d)
        d = d.get().reshape(n, 4, 256)
        return {lo + g: (d[g, :2], d[g, 2:]) for g in range(n)}


def mode_sweep(a):
    gen, spec, lo, hi, out = a[0], a[1], int(a[2]), int(a[3]), a[4]
    thr = float(a[5]) if len(a) > 5 else THR
    wins = make_windows(spec)
    S = Step(gen, wins)
    info = gpu_common.device_info()
    print(f"step: {gen} sweep of {hi - lo} seeds, {len(wins)} windows x 144 settings on CUDA {info['name']}", file=sys.stderr, flush=True)
    cand = np.zeros((0, 2), np.uint32)
    hist = np.zeros(HB, np.uint64)
    t_start = last = time.time()
    done, chunk = 0, 1 << 12
    total = hi - lo
    while done < total:
        n = min(chunk, total - done)
        while True:
            S.hist[:] = 0
            t1 = time.time()
            cnt = S.launch(lo + done, n, thr)
            dt = time.time() - t1
            if cnt <= CCAP:
                break
            thr += 0.01                                             # too many candidates for the buffer: raise the floor, redo
        hist += S.hist.get()
        if cnt:
            cand = np.concatenate([cand, S.cand[:2 * cnt].get().reshape(cnt, 2)])
            if len(cand) > 4 * TOPK:
                ioc = (cand[:, 1] >> 16).astype(np.int64)
                kth = int(np.sort(ioc)[-TOPK])
                cand = cand[ioc >= kth]
        done += n
        chunk = int(min(max(chunk * min(2.0, TARGET_S / max(dt, 1e-3)), 1 << 8), 1 << 22))
        if time.time() - last >= 20:
            last = time.time()
            el, frac = last - t_start, done / total
            print(f"{100 * frac:.2f}% ({done} seeds) {done / el:.0f} seeds/s, eta {el * (1 - frac) / max(frac, 1e-9):.0f} s",
                  file=sys.stderr, flush=True)
    secs = time.time() - t_start
    order = np.lexsort((cand[:, 1] & 0xFFFF, cand[:, 0], -(cand[:, 1] >> 16).astype(np.int64)))[:TOPK]
    rows = ["ioc\tseed\twindow\tvariant\tmap\tmode\tm"]
    for seed, packed in cand[order]:
        x, wi, combo = int(packed) >> 16, (int(packed) >> 8) & 0xFF, int(packed) & 0xFF
        variant, mp, mode, m = combo_parts(combo)
        rows.append(f"{x / 1000:.3f}\t{int(seed)}\t{wins[wi][0]}\t{variant}\t{mp}\t{mode}\t{m}")
    Path(out).write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    best = (int(cand[order[0], 1] >> 16) / 1000) if len(order) else 0
    print(f"swept {total} seeds in {secs:.0f} s; best ioc {best:.3f}; candidates >= {thr:.2f}: {len(cand)}", file=sys.stderr, flush=True)
    print("hist " + " ".join(f"{b}:{int(c)}" for b, c in enumerate(hist) if c), file=sys.stderr, flush=True)
    return 0


def main():
    a = sys.argv[1:]
    if a and a[0] == "probe":
        return gpu_common.probe()
    if a and a[0] == "sweep" and len(a) >= 6:
        return mode_sweep(a[1:])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
