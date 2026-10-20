"""Bit-identity gate for the pdir engine change: the engine WITHOUT pdir= must decode exactly as the engine before the change.

    python work/kscreen/pdir_identity.py --orig <engine built from the commit before the change> [--new <engine>] [--threads 2]

Runs `trace` (one line per decode) and `screen` (whole output file, the timing field removed) with both binaries on the LP2 windows, on sign (S line), guard (G line), nulledge, advsep, dir=back and clock windows/options, and compares the output byte by byte.
"""
import argparse
import os
import re
import subprocess
import sys

import selftest as S

HERE = S.HERE
LIB = "file:data/library.ksb"


def run(exe, args):
    r = subprocess.run([exe] + args, cwd=HERE, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(r.stderr)
    return r.stdout


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--orig", required=True)
    ap.add_argument("--new", default=S.BIN)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=os.path.join(S.OUT, "pdir_identity.txt"))
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    seg = "data/segments.txt"
    g = os.path.join(S.TMP, "pdir_identity_G.txt")
    txt = open(os.path.join(HERE, seg), encoding="utf-8").read().replace("\nR ", "\nG 3\nR ", 1)
    open(g, "w", newline="\n", encoding="utf-8").write(txt)
    cases = [
        ("default", seg, []), ("sign S lines", "data/signs/E_cur_n4.txt", []), ("sign S lines, coin only", "data/signs/A_prev_G.txt", ["models=1"]), ("guard G line", S.rel(g), []),
        ("nulledge=1", seg, ["nulledge=1"]), ("nulledge=2", seg, ["nulledge=2"]), ("advsep=1", seg, ["advsep=1"]), ("advsep=2", seg, ["advsep=2"]),
        ("dir=back", seg, ["dir=back"]), ("clock=c1", seg, ["clock=c1", "n=150"]), ("clock=pp", seg, ["clock=pp", "n=100"]), ("n=100 abort=50:1.1", seg, ["n=100", "abort=50:1.1"]),
    ]
    lines, ok = [], True
    for name, win, opt in cases:
        out_o, out_n = os.path.join(S.TMP, "pdir_id_o.txt"), os.path.join(S.TMP, "pdir_id_n.txt")
        same = True
        for exe, out in ((a.orig, out_o), (a.new, out_n)):
            run(exe, ["trace", win, LIB, S.rel(out), "items=0:3", "offs=0:40", *opt])
        same &= open(out_o, "rb").read() == open(out_n, "rb").read() and os.path.getsize(out_o) > 0
        n_lines = open(out_o).read().count("\n")
        tsvs = []
        for exe, tag in ((a.orig, "o"), (a.new, "n")):
            t = os.path.join(S.TMP, f"pdir_id_{tag}.tsv")
            run(exe, ["screen", win, LIB, S.rel(t), "only=primes-1 (totient)", f"threads={a.threads}", "top=50", *opt])
            tsvs.append(re.sub(r"secs=\d+", "secs=0", open(t, encoding="utf-8").read()))
        same &= tsvs[0] == tsvs[1]
        ok &= same
        lines.append(f"{'IDENTICAL' if same else 'DIFFERENT'}  {name}: trace {n_lines} decodes and the screen file (best hits, histogram, header) {'equal' if same else 'differ'}")
    lines.append("PDIR IDENTITY " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    open(a.out, "w", newline="\n", encoding="utf-8").write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
