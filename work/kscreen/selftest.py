"""Positive and null controls for the keystream screen. A kscreen null result only counts if this passes.

    python work/kscreen/selftest.py [--threads N]

Positive: keys from five different families are planted into held-out English (work/phpmt/data/english.txt,
3 windows of 400 runes) under the anti-repeat rule: skip and coin models, both key signs, with and without a
random substitution of the plaintext alphabet. Each must come back as its window's best hit with IoC >= 1.40,
and a full re-decode at the true offset must also reach 1.40.
Null: random keystreams over every offset of the LP2 section windows must stay below 1.40.
Writes results/kscreen/selftest.txt (or --out) and exits non-zero on any failure.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
BIN = os.path.join(HERE, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
PLAIN = os.path.join(ROOT, "work", "phpmt", "data", "english.txt")
TMP = os.path.join(ROOT, "work", "tmp", "kscreen")
OUT = os.path.join(ROOT, "results", "kscreen")
THRESHOLD = 1.40

# family, item, offset, multiplier, model, substitution, extra screen options
CASES = [
    ("file:data/library.ksb", "primes-1 (totient)", "1234", 1, 0, 0, []),
    ("file:data/library.ksb", "pi digits (base 29)", "777", 28, 1, 1, []),
    ("file:data/library.ksb", "sha256-ctr reject :3301", "4321", 1, 0, 1, []),
    ("lin:2", "lin2:1,1", "state=1,1", 1, 1, 1, ["mults=1"]),
    ("poly:2", "poly2:3,5", "7", 1, 0, 0, ["mults=1"]),
]


def rel(p):
    return os.path.relpath(p, HERE).replace("\\", "/")


def run(args, **kw):
    r = subprocess.run([BIN] + args, cwd=HERE, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"kscreen {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def window_bests(tsv):
    out = {}
    with open(tsv, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        m = re.match(r"# window (\S+) best ([\d.]+) item=(.*) offset=(\S+) mult=(\d+) model=(\d+)", line)
        if m:
            out[m.group(1)] = (float(m.group(2)), m.group(3), m.group(4))
    return out


def truths(plant_file):
    out = {}
    with open(plant_file, encoding="utf-8") as f:
        lines = f.read().splitlines()
    for line in lines:
        m = re.match(r"# truth (\S+) item=(.*) offset=(\S+) mult=", line)
        if m:
            out[m.group(1)] = (m.group(2), m.group(3))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--null-keystreams", type=int, default=30)
    ap.add_argument("--out", default=os.path.join(OUT, "selftest.txt"), help="where to write the summary")
    args = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)
    os.makedirs(OUT, exist_ok=True)
    lines, ok = [], True
    for ci, (fam, item, off, mult, model, subst, extra) in enumerate(CASES):
        plant = os.path.join(TMP, f"selftest_plant{ci}.txt")
        tsv = os.path.join(TMP, f"selftest_plant{ci}.tsv")
        # relative paths: they end up in the result headers, which must not show this PC's folders
        run(["plant", rel(PLAIN), fam, item, off, str(mult), str(model), "0.18", str(100 + ci), str(subst), rel(plant)])
        run(["screen", rel(plant), fam, rel(tsv), f"only={item}", f"threads={args.threads}"] + extra)
        best = window_bests(tsv)
        for win, (titem, toff) in truths(plant).items():
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            vout = run(["verify", rel(plant), fam, item, toff, str(mult), str(model), win])
            vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
            good = bitem == item and ioc >= THRESHOLD and vioc >= THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  plant {item!r} model={model} mult={mult} subst={subst} {win}: "
                         f"best {ioc:.3f} at offset {boff} (truth {toff}); re-decode at truth {vioc:.3f}")
    null_tsv = os.path.join(TMP, "selftest_null.tsv")
    run(["screen", "data/segments.txt", f"rand:{args.null_keystreams}:4242", rel(null_tsv), f"threads={args.threads}"])
    nbest = max(v[0] for v in window_bests(null_tsv).values())
    good = nbest < THRESHOLD
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  null: {args.null_keystreams} random keystreams x every offset x "
                 f"8 LP2 windows x 2 signs x 2 models: best IoC {nbest:.3f} (must stay below {THRESHOLD})")
    lines.append("SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
