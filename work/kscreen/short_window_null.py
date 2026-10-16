"""Per-window extreme-value null for short windows.

The campaign rule (IoC >= 1.40, whole-window verification) was calibrated for windows of 300 runes. In a window of 91-140 runes
chance alone gives an IoC far above 1.40 once ~10^8 decodes have been scored: the maximum is what matters, and its
distribution depends on the window length and on how many decodes were run. This script measures it directly: for each
short window of a finished screen it reruns the screen on random keystreams with the SAME number of (keystream, offset)
pairs, R times, and compares the library's best IoC for that window with the R null maxima (empirical rank, and a Gumbel fit
for the tail).

    python work/kscreen/short_window_null.py results/kscreen/library_pages.tsv [--max-len 250] [--reps 16] [--out file]

Engine: gpu.py if CUDA works, else the Rust engine (slow). Run from anywhere.
"""
import argparse
import math
import os
import re
import statistics
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
BIN = os.path.join(HERE, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))


def read_tsv(path):
    meta, bests = {}, {}
    with open(path, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.startswith("# kscreen"):
                meta = dict(kv.split("=", 1) for kv in line.split()[3:] if "=" in kv)
            m = re.match(r"# window (\S+) best ([\d.]+)", line)
            if m:
                bests[m.group(1)] = float(m.group(2))
    return meta, bests


def windows(path):
    out, cur = {}, None
    with open(path, encoding="utf-8") as f:
        block = []
        for line in f.read().splitlines():
            if line.startswith("W "):
                if cur:
                    out[cur] = block
                cur, block = line.split()[1], [line]
            elif cur:
                block.append(line)
        if cur:
            out[cur] = block
    return out


def n_pairs(family):
    """(keystream, offset) pairs of the library family at this window length (as the engine counts them)."""
    if not family.startswith("file:"):
        raise SystemExit("only file: families are supported")
    import gpu
    ks = gpu.load_ksb(os.path.join(HERE, family[5:]))
    return ks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--max-len", type=int, default=250)
    ap.add_argument("--reps", type=int, default=16)
    ap.add_argument("--out", default=None)
    ap.add_argument("--engine", choices=["cuda", "cpu"], default="cuda")
    args = ap.parse_args()
    meta, lib = read_tsv(args.tsv)
    wfile = os.path.join(HERE, meta["windows"])
    wins = windows(wfile)
    short = {}
    for name, block in wins.items():
        r = next(l for l in block if l.startswith("R "))
        n = len(r.split()) - 1
        if n < args.max_len and name in lib:
            short[name] = n
    if not short:
        print("no windows below", args.max_len)
        return 0
    n = int(meta["n"])
    need = n + n // 4 + 8
    ks = n_pairs(meta["family"])
    pairs = sum(max(0, len(v) + 1 - need) for _, v in ks)
    streams = max(1, round(pairs / (20000 + 1 - need)))
    base = ["screen"]
    extra = [f"mults={meta['mults']}", f"models={meta['models']}", f"n={meta['n']}", f"beam={meta['beam']}",
             f"abort={meta['abort']}"]
    lines = [f"{os.path.relpath(args.tsv, ROOT).replace(os.sep, '/')}: {len(short)} windows shorter than {args.max_len} runes; library has "
             f"{pairs:,} (keystream, offset) pairs = {streams} random keystreams of 20,000; {args.reps} null replicates each",
             "window                   runes  library best | null max: min   median   max   | rank (null >= lib)  Gumbel p"]
    sub = os.path.join(tempfile.mkdtemp(), "short.txt")
    with open(sub, "w", encoding="utf-8", newline="\n") as f:
        for name in short:
            f.write("\n".join(wins[name]) + "\n")
    nulls = {name: [] for name in short}
    for rep in range(args.reps):
        tsv = os.path.join(os.path.dirname(sub), f"null{rep}.tsv")
        cmd = ([sys.executable, os.path.join(HERE, "gpu.py")] if args.engine == "cuda" else [BIN]) + \
            ["screen", sub, f"rand:{streams}:{9000 + rep}", tsv, *extra]
        r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(r.stderr[-800:])
        _, b = read_tsv(tsv)
        for name in short:
            nulls[name].append(b[name])
        print(f"replicate {rep + 1}/{args.reps} done", file=sys.stderr, flush=True)
    for name, nn in sorted(short.items(), key=lambda kv: kv[1]):
        v = sorted(nulls[name])
        mu, sd = statistics.mean(v), statistics.pstdev(v) or 1e-9
        beta = sd * math.sqrt(6) / math.pi
        loc = mu - 0.5772 * beta
        p = 1 - math.exp(-math.exp(-(lib[name] - loc) / beta))
        rank = sum(x >= lib[name] for x in v)
        lines.append(f"{name:24s} {nn:5d}  {lib[name]:8.3f}      | {v[0]:6.3f}  {v[len(v) // 2]:6.3f}  {v[-1]:6.3f}  |  {rank:2d}/{len(v)}          {p:.3f}")
    lines.append("")
    lines.append("A window counts only if its library best clearly exceeds the null maxima (rank 0 and a small Gumbel p) AND the same "
                 "keystream decodes other windows; with this many windows the smallest p is expected to be about 1/windows.")
    text = "\n".join(lines)
    print(text)
    if args.out:
        with open(args.out, "w", newline="\n", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
