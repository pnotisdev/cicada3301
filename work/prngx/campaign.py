"""Resumable sweep campaign for prngx (standalone: does not touch jobs/overnight.py).

    python work/prngx/campaign.py list
    python work/prngx/campaign.py run [stageA|stageB|full] [--gens mt pymt msvc java rand48] [--threads N] [--low]

Stages (windows_07: the key starts on LP2 page 0):
  stageA  human-plausible seed mass: [0, 2^27) (small numbers, dates YYYYMMDD, ...) and [1.3e9, 1.5e9)
          (Unix time(NULL) between 2011 and 2017): about 3.3e8 seeds per generator, about 1.4 h for all five
          generators on 16 threads.
  stageB  every other 32-bit seed (java: also the negative ints): the rest of 2^32.
  full    stageA + stageB.
After each sweep the 20 best candidates are re-decoded over the whole segment against random-seed controls
(verify.py); a real key stands out at z ~ +60, selection noise at z <= +5.
Each sweep writes results/prngx/<gen>_<range>.tsv (+ .log, _verify.txt); a finished sweep is skipped on rerun.
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(HERE, "target", "release", "prngx" + (".exe" if os.name == "nt" else ""))
DATA = os.path.join(ROOT, "work", "phpmt", "data")
OUT = os.path.join(ROOT, "results", "prngx")
GENS = ["rand48", "msvc", "java", "mt", "pymt"]          # cheapest first
def _chunks(lo, hi, size=2 ** 28):
    out, a = [], lo
    while a < hi:
        out.append((f"b_{a // 2 ** 20}M", a, min(a + size, hi)))
        a += size
    return out


RANGES = {
    "stageA": [("a_small", 0, 2 ** 27), ("a_time", 1_300_000_000, 1_500_000_000)],
    # stage B in chunks of 2^28 seeds so an interrupted run loses at most one chunk
    "stageB": _chunks(2 ** 27, 1_300_000_000) + _chunks(1_500_000_000, 2 ** 32),
}
RANGES["full"] = RANGES["stageA"] + RANGES["stageB"]


def jobs(stage, gens):
    out = []
    for gen in gens:
        for tag, lo, hi in RANGES[stage]:
            out.append((gen, tag, lo, hi))
        if gen == "java" and stage in ("stageB", "full"):
            out.append((gen, "b_negative", -2 ** 31, 0))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["list", "run"])
    ap.add_argument("stage", nargs="?", default="stageA", choices=list(RANGES))
    ap.add_argument("--gens", nargs="+", default=GENS)
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--low", action="store_true", help="below-normal CPU priority (Windows) / nice (Linux)")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    todo = jobs(a.stage, a.gens)
    for gen, tag, lo, hi in todo:
        tsv = os.path.join(OUT, f"{gen}_{tag}.tsv")
        done = os.path.exists(tsv)
        print(f"{'done' if done else 'todo'}  {gen:7s} {tag:10s} [{lo}, {hi})  {(hi - lo) / 1e6:9.1f} M seeds")
        if a.action == "list" or done:
            continue
        log = os.path.join(OUT, f"{gen}_{tag}.log")
        cmd = [EXE, "sweep", gen, os.path.join(DATA, "windows_07.txt"), os.path.join(DATA, "dict.txt"), str(lo), str(hi),
               tsv + ".part", str(a.threads)]
        flags = 0
        if a.low and os.name == "nt":
            flags = 0x00004000                      # BELOW_NORMAL_PRIORITY_CLASS
        elif a.low:
            cmd = ["nice", "-n", "10"] + cmd
        t0 = time.time()
        with open(log, "w", encoding="utf-8", newline="\n") as lf:
            rc = subprocess.run(cmd, stderr=lf, creationflags=flags).returncode
        if rc != 0:
            sys.exit(f"sweep failed ({gen} {tag}); see {log}")
        os.replace(tsv + ".part", tsv)
        print(f"   finished in {(time.time() - t0) / 60:.1f} min", flush=True)
        subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), tsv, "--gen", gen, "--top", "20"],
                       stdout=open(os.path.join(OUT, f"{gen}_{tag}_verify.txt"), "w", encoding="utf-8", newline="\n"),
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))


if __name__ == "__main__":
    main()
