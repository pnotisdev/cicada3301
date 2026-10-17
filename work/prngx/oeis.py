"""OEIS integer sequences as keystream candidates for prngx's `seq` generator.

    python work/prngx/oeis.py fetch          # downloads https://oeis.org/stripped.gz (34 MB) to work/ref/oeis/ (git-ignored)
    python work/prngx/oeis.py build [--min-terms 40]   # -> work/prngx/data/oeis_seqs.txt: "<id> v0 v1 ..." values mod 29
    python work/prngx/oeis.py null [--n N]   # random sequences with the same lengths (null control) -> data/null_seqs.txt

The OEIS terms file is CC BY-NC 4.0 data from oeis.org and is not committed. Each line of stripped.gz holds the first
terms of one sequence (as many as fit in about 260 characters), so most sequences have 20-100 terms; sequences with
fewer than --min-terms terms cannot cover a 30-rune decoding window and are dropped.
"""
import argparse
import gzip
import os
import random
import sys
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REF = os.path.join(ROOT, "work", "ref", "oeis")
GZ = os.path.join(REF, "stripped.gz")
DATA = os.path.join(HERE, "data")
OUT = os.path.join(DATA, "oeis_seqs.txt")


def fetch():
    os.makedirs(REF, exist_ok=True)
    with open(os.path.join(REF, ".gitignore"), "w", newline="\n") as f:
        f.write("*\n!.gitignore\n")
    if not os.path.exists(GZ):
        print("downloading https://oeis.org/stripped.gz ...")
        import shutil
        import subprocess
        if shutil.which("curl"):          # oeis.org's CDN rejects the default Python user agent
            subprocess.run(["curl", "-sSL", "--fail", "-o", GZ, "https://oeis.org/stripped.gz"], check=True)
        else:
            req = urllib.request.Request("https://oeis.org/stripped.gz", headers={"User-Agent": "curl/8"})
            with urllib.request.urlopen(req) as r, open(GZ, "wb") as out:
                shutil.copyfileobj(r, out)
    print("ok:", GZ, os.path.getsize(GZ), "bytes")


def parse(min_terms):
    seqs = []
    with gzip.open(GZ, "rt", encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            ident, _, rest = line.strip().partition(" ")
            try:
                terms = [int(x) for x in rest.strip(",").split(",") if x != ""]
            except ValueError:
                continue
            if len(terms) >= min_terms:
                seqs.append((ident, [t % 29 for t in terms]))
    return seqs


def build(min_terms):
    os.makedirs(DATA, exist_ok=True)
    seqs = parse(min_terms)
    with open(OUT, "w", newline="\n", encoding="utf-8") as f:
        for ident, v in seqs:
            f.write(ident + " " + " ".join(map(str, v)) + "\n")
    import statistics
    print(f"{len(seqs)} sequences with >= {min_terms} terms; median length {statistics.median(len(v) for _, v in seqs):.0f}"
          f" -> {OUT}")


def null(n):
    seqs = parse(40)
    rng = random.Random(29)
    with open(os.path.join(DATA, "null_seqs.txt"), "w", newline="\n") as f:
        for k in range(n or len(seqs)):
            L = len(seqs[k % len(seqs)][1])
            f.write(f"N{k:06d} " + " ".join(str(rng.randrange(29)) for _ in range(L)) + "\n")
    print("wrote null_seqs.txt")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("action", choices=["fetch", "build", "null"])
    ap.add_argument("--min-terms", type=int, default=40)
    ap.add_argument("--n", type=int, default=0)
    a = ap.parse_args()
    if a.action == "fetch":
        fetch()
    elif a.action == "build":
        build(a.min_terms)
    else:
        null(a.n)
