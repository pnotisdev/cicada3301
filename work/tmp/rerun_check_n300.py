"""Fill the two failed n300 tasks with the real campaign code, and re-run 4 finished tasks into a temp folder to compare them bit for bit
(is the machine reproducible, or did the 13:29 failure come with silent corruption elsewhere?). Low priority, logical processors 12-15 only."""
import concurrent.futures as cf
import ctypes
import os
import random
import sys
import tempfile
import time
from pathlib import Path

import numpy as np

STEP3 = str(Path(__file__).resolve().parents[1] / "chanscreen" / "v2" / "step3")
sys.path.insert(0, STEP3)
import common as C  # noqa: E402
import campaign as K  # noqa: E402


def init():
    k = ctypes.windll.kernel32
    h = k.GetCurrentProcess()
    k.SetPriorityClass(h, 0x4000)                    # below normal
    k.SetProcessAffinityMask(h, 0xF000)              # logical processors 12-15
    K._init("n300")


def fill(wi, ci):
    t = time.time()
    r = K.task(("n300", wi, ci))
    return f"fill   w{wi:03d} c{ci:02d}: written, {time.time() - t:.0f} s, candidates {r[3]}"


def compare(wi, ci, tmp):
    orig = C.OUT
    C.OUT = Path(tmp)
    try:
        t = time.time()
        K.task(("n300", wi, ci))
    finally:
        C.OUT = orig
    f = f"n300/w{wi:03d}_c{ci:02d}.npz"
    a, b = np.load(orig / f), np.load(Path(tmp) / f)
    same = {k: bool(np.array_equal(a[k], b[k], equal_nan=True)) for k in ("res", "cand", "logW")}
    return f"compare w{wi:03d} c{ci:02d}: identical {all(same.values())} {same}, {time.time() - t:.0f} s"


if __name__ == "__main__":
    done = sorted((int(f[1:4]), int(f[6:8])) for f in os.listdir(C.OUT / "n300") if f.endswith(".npz") and not f.endswith(".tmp.npz"))
    pick = random.Random(20261019).sample([d for d in done if d[0] < 21], 4)
    print("comparing", pick, flush=True)
    tmp = tempfile.mkdtemp(prefix="recheck_")
    with cf.ProcessPoolExecutor(max_workers=6, initializer=init) as ex:
        futs = [ex.submit(fill, 1, 11), ex.submit(fill, 17, 4)] + [ex.submit(compare, w, c, tmp) for w, c in pick]
        for f in cf.as_completed(futs):
            try:
                print(f"[{time.strftime('%H:%M:%S')}] {f.result()}", flush=True)
            except Exception as e:                                  # report, do not hide
                print(f"[{time.strftime('%H:%M:%S')}] FAILED {type(e).__name__}: {e}", flush=True)
