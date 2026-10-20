"""Quarantine the corrupt task file w013_c04.npz, recompute the task with the real campaign code, and compare the two."""
import ctypes
import shutil
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "work" / "chanscreen" / "v2" / "step3"))
import common as C  # noqa: E402
import campaign as K  # noqa: E402

k = ctypes.windll.kernel32
h = k.GetCurrentProcess()
k.SetPriorityClass(h, 0x4000)                  # below normal
k.SetProcessAffinityMask(h, 0xF000)            # logical processors 12-15

wi, ci = 13, 4
src = C.OUT / "n300" / f"w{wi:03d}_c{ci:02d}.npz"
qdir = C.OUT / "quarantine"
qdir.mkdir(exist_ok=True)
bad = qdir / f"n300_w{wi:03d}_c{ci:02d}_corrupt.npz"
if src.exists() and not bad.exists():
    shutil.move(str(src), str(bad))
print("quarantined ->", bad.relative_to(ROOT).as_posix(), flush=True)
K._init("n300")
t = time.time()
r = K.task(("n300", wi, ci))
print(f"recomputed w{wi:03d} c{ci:02d} in {time.time() - t:.0f} s, candidates {r[3]}", flush=True)
a, b = np.load(bad), np.load(src)
for key in ("res", "cand", "logW"):
    same = np.array_equal(a[key], b[key], equal_nan=True)
    print(f"  {key}: identical {same}", flush=True)
ra, rb = a["res"], b["res"]
diff = np.argwhere(~((ra == rb) | (np.isnan(ra) & np.isnan(rb))).all(axis=2))
print("  (stream, column) rows that differ:", [(int(s) + 250, int(c)) for s, c in diff][:12], "of", ra.shape[0] * ra.shape[1], flush=True)
print("  tier-1 cells corrupt vs recomputed:", int(ra[:, :, 8].sum()), int(rb[:, :, 8].sum()), flush=True)
