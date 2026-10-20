"""Queue helper for the phase 36 layout sign rules: one rule as signs over the flat library (or a matched null), then verify.py on the top hits.

    python work/kscreen/layout_queue.py <rule> [--threads 14] [--null] [--streams N] [--out-dir results/kscreen/layout] [--top 15]

Runs from work/kscreen (verify.py re-reads the window and family paths from the tsv header, relative to there). A finished output is skipped (resume).
--streams N screens only the first N library streams (dry run); --null uses 581 random streams (rand:581:4242) under the same signs.
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BIN = os.environ.get("KSCREEN_BIN") or os.path.join(HERE, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))

ap = argparse.ArgumentParser()
ap.add_argument("rule")
ap.add_argument("--threads", type=int, default=14)
ap.add_argument("--null", action="store_true")
ap.add_argument("--streams", type=int, default=0)
ap.add_argument("--out-dir", default="results/kscreen/layout")
ap.add_argument("--top", type=int, default=15)
a = ap.parse_args()

out_dir = os.path.join(ROOT, a.out_dir)
os.makedirs(out_dir, exist_ok=True)
name = ("null_" if a.null else "") + a.rule
tsv = os.path.join(out_dir, name + ".tsv")
if os.path.exists(tsv):
    print("exists, skipped:", tsv)
    sys.exit(0)
fam = "rand:581:4242" if a.null else "file:data/library_flat.ksb"
cmd = [BIN, "screen", f"data/layout_signs/{a.rule}.txt", fam, os.path.relpath(tsv, HERE), f"threads={a.threads}"]
if a.streams:
    cmd.append(f"items=0:{a.streams}")
subprocess.run(cmd, cwd=HERE, check=True)
if not a.null:
    subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), tsv, "--top", str(a.top), "--out", tsv.replace(".tsv", "_verify.txt")], cwd=ROOT, check=True)
