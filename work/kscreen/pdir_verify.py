"""Whole-window verification of a pdir screen (docs/CAMPAIGNS.md): verify.py (top 5 hits per vector, 20 random-offset controls) over every real tsv of a convention.

    python work/kscreen/pdir_verify.py --conv 000 [--tag stage1]      # -> results/kscreen/pdir/<tag>/<conv>/verify/*.txt and verify_summary.txt
A line `N of M re-decoded hits keep IoC >= 1.4 ...` with N > 0 is a candidate: read the decoded text, then the whole-section verification of docs/CAMPAIGNS.md. 0 everywhere is a negative.
"""
import argparse
import glob
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(os.path.dirname(HERE)), "results", "kscreen", "pdir")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conv", required=True)
    ap.add_argument("--tag", default="stage1")
    a = ap.parse_args()
    base = os.path.join(OUT, a.tag, a.conv)
    os.makedirs(os.path.join(base, "verify"), exist_ok=True)
    lines, cand = [], 0
    for tsv in sorted(glob.glob(os.path.join(base, "real", "*.tsv"))):
        name = os.path.basename(tsv)[:-4]
        out = os.path.join(base, "verify", name + ".txt")
        r = subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), tsv, "--top", "5", "--out", out], capture_output=True, text=True)
        m = re.search(r"(\d+) of (\d+) re-decoded hits", open(out, encoding="utf-8").read()) if os.path.exists(out) else None
        n = int(m.group(1)) if m else -1
        cand += max(n, 0)
        lines.append(f"{name}: {m.group(0) if m else 'verify failed ' + r.stderr[-200:]}")
    text = f"pdir verify {a.tag} conv {a.conv}: {len(lines)} vectors, candidates {cand}\n" + "\n".join(lines) + "\n"
    open(os.path.join(base, "verify_summary.txt"), "w", newline="\n", encoding="utf-8").write(text)
    print(text.splitlines()[0])


if __name__ == "__main__":
    main()
