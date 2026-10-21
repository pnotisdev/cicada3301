"""Queue helper for the phase 37 word-jump screens: one advsep mode (3 = n_w of the word just ended, 4 = constant 2, 5 = n_w of the next word) over the 581 flat library streams x 8 section
windows (mults 1 and 28, both models), or a matched null (581 random streams), then verify.py on the top hits. Uses the advlen engine build (the one the controls ran on).

    python work/kscreen/wordjump_queue.py <mode 3|4|5> [--threads 14] [--null] [--streams N] [--out-dir results/kscreen/wordjump] [--top 15]

Runs from work/kscreen. A finished output is skipped (resume). --streams N screens only the first N library streams (dry run).
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BIN = os.path.join(HERE, "target", "advlen", "release", "kscreen" + (".exe" if os.name == "nt" else ""))

ap = argparse.ArgumentParser()
ap.add_argument("mode", type=int, choices=(3, 4, 5))
ap.add_argument("--threads", type=int, default=14)
ap.add_argument("--null", action="store_true")
ap.add_argument("--streams", type=int, default=0)
ap.add_argument("--out-dir", default="results/kscreen/wordjump")
ap.add_argument("--top", type=int, default=15)
a = ap.parse_args()

out_dir = os.path.join(ROOT, a.out_dir)
os.makedirs(out_dir, exist_ok=True)
tsv = os.path.join(out_dir, ("null_" if a.null else "") + f"advsep{a.mode}.tsv")
if os.path.exists(tsv):
    print("exists, skipped:", tsv)
    sys.exit(0)
fam = f"rand:581:{4370 + a.mode}" if a.null else "file:data/library_flat.ksb"
cmd = [BIN, "screen", "data/segments.txt", fam, os.path.relpath(tsv, HERE), f"threads={a.threads}", f"advsep={a.mode}"]
if a.streams:
    cmd.append(f"items=0:{a.streams}")
subprocess.run(cmd, cwd=HERE, check=True)
if not a.null:
    env = dict(os.environ, KSCREEN_BIN=BIN)
    subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), tsv, "--top", str(a.top), "--out", tsv.replace(".tsv", "_verify.txt")], cwd=ROOT, check=True, env=env)
