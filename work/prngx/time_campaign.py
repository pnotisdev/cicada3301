#!/usr/bin/env python3
"""prng-time: generators seeded with a MILLISECOND timestamp of 2012-01-01 .. 2014-02-01 (UTC), on LP2 section 0.7.

    python work/prngx/time_campaign.py list
    python work/prngx/time_campaign.py run <java|pymt> <YYYY-MM | YYYY-MM-DD:YYYY-MM-DD> [--threads N]

The 32-bit seed sweeps cover every second-resolution time(NULL) seed, but not these:
  java  java.util.Random(long): 48-bit seed, e.g. new Random(System.currentTimeMillis()); maps 0 nextInt(29),
        1 (int)(nextDouble()*29), 2 Math.abs(nextInt()) % 29
  pymt  CPython random.seed(int) with an integer >= 2^32, e.g. int(time.time() * 1000): MT19937 init_by_array with two 32-bit
        words; maps 2 randrange / randint / choice, 5 random() * 29, and 3 (low 5 bits with rejection), which is Ruby's
        documented rand(n) for a Random.new(int) seeded the same way: NOT checked against a Ruby (none on either machine)
        (the maps of the other languages, 0 / 1 / 4, cannot come with a two-word seed and are left out: PRNGX_MAPS)
Each run is one boundary-free sweep (`prngx bgsweep`, English rune-bigram score of the first 120 runes, skip and coin
anti-repeat models, both signs, plain and Atbash) followed by the whole-section check of its best rows (time_verify.py).
Outputs: results/prngx/time/<gen>_<label>.tsv, .log, _verify.txt. Months run newest first (the book appeared in
January 2014). Full window: about 6.6e10 seeds per generator, i.e. GPU work (see work/log/phase10_prng_time.md);
on a CPU this is a tool for narrow windows (Java about 12,000 and Python about 10,000 seeds/s per thread).
"""
import argparse
import datetime as dt
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ROOT = os.path.dirname(WORK)
OUT = os.path.join(ROOT, "results", "prngx", "time")
DATA = os.path.join(WORK, "phpmt", "data")
EXE = "prngx.exe" if os.name == "nt" else "prngx"
MAPS = {"java": "0,1,2", "pymt": "2,3,5"}
FIRST, END = (2012, 1), (2014, 2)          # months [FIRST, END)


def binary():
    """the newest prngx build (target/ is the usual one; target_time/ is a side build next to a running sweep)"""
    cands = [os.path.join(HERE, d, "release", EXE) for d in ("target", "target_time")]
    cands = [p for p in cands if os.path.exists(p)]
    if not cands:
        sys.exit("build prngx first: cargo build --release (in work/prngx)")
    return max(cands, key=os.path.getmtime)


def ms(y, m, d=1):
    return int(dt.datetime(y, m, d, tzinfo=dt.timezone.utc).timestamp() * 1000)


def months():
    """[(label, lo, hi)] newest first"""
    out, (y, m) = [], FIRST
    while (y, m) < END:
        ny, nm = (y + (m == 12), m % 12 + 1)
        out.append((f"{y}-{m:02d}", ms(y, m), ms(ny, nm)))
        y, m = ny, nm
    return out[::-1]


def parse_label(label):
    if ":" in label:
        a, b = label.split(":")
        (ya, ma, da), (yb, mb, db) = (map(int, a.split("-")), map(int, b.split("-")))
        return label.replace(":", "_"), ms(ya, ma, da), ms(yb, mb, db)
    for lab, lo, hi in months():
        if lab == label:
            return lab, lo, hi
    sys.exit(f"unknown month {label}: use YYYY-MM between 2012-01 and 2014-01, or YYYY-MM-DD:YYYY-MM-DD")


def paths(gen, label):
    base = os.path.join(OUT, f"{gen}_{label}")
    return base + ".tsv", base + ".log", base + "_verify.txt"


def run(gen, label, threads):
    lab, lo, hi = parse_label(label)
    tsv, log, ver = paths(gen, lab)
    os.makedirs(OUT, exist_ok=True)
    env = dict(os.environ, PRNGX_MAPS=MAPS[gen])
    cmd = [binary(), "bgsweep", gen, os.path.join(DATA, "windows_07.txt"), os.path.join(DATA, "bigram.txt"), str(lo), str(hi),
           tsv + ".part", str(threads)]
    print(f"prng-time: {gen} {lab}: seeds [{lo}, {hi}) = {(hi - lo) / 1e9:.2f} e9, maps {MAPS[gen]}, {threads} threads", flush=True)
    with open(log, "w", encoding="utf-8") as lf:
        lf.write(f"# prngx bgsweep {gen} windows_07 bigram {lo} {hi} PRNGX_MAPS={MAPS[gen]} threads={threads}\n")
        lf.flush()
        p = subprocess.Popen(cmd, cwd=HERE, env=env, stderr=subprocess.PIPE, text=True)
        for line in p.stderr:
            sys.stderr.write(line)
            lf.write(line)
        if p.wait() != 0:
            sys.exit(f"prngx bgsweep failed (log {log})")
    os.replace(tsv + ".part", tsv)
    sys.path.insert(0, HERE)
    import time_verify
    lines = []

    def out(s):
        print(s, flush=True)
        lines.append(s)

    time_verify.verify(tsv, gen, top=10, controls=8, out=out)
    with open(ver, "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["list", "run"])
    ap.add_argument("gen", nargs="?", choices=["java", "pymt"])
    ap.add_argument("label", nargs="?")
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    a = ap.parse_args()
    if a.action == "list":
        for gen in ("java", "pymt"):
            for lab, lo, hi in months():
                done = os.path.exists(paths(gen, lab)[2])
                print(f"{'done' if done else 'todo'}  {gen:5s} {lab}  [{lo}, {hi})  {(hi - lo) / 1e9:.2f} e9 seeds")
        return 0
    if not (a.gen and a.label):
        ap.error("run needs a generator and a month")
    return run(a.gen, a.label, a.threads)


if __name__ == "__main__":
    sys.exit(main())
