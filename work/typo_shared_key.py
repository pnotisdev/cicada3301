"""Shared-key test for the five list items of 0.14 (cicadanotebook's 'the key restarts at each numbered item'; campaign kscreen-typo of research/new-hypotheses).

Each item is screened ALONE against the keystream library (kscreen; the key offset is free, so label-based counters are covered) and its 2,000 best settings are kept
(`library_item<i>.tsv`: ioc, keystream, offset, multiplier, model). If the key restarts at every item with the same stream, the TRUE setting (keystream, offset, mult, model) is in the
top list of every item (the offset is where the key starts; it is the same each time). Each item alone is too short to rank a true key first (planted keys: recovered but below the
null maximum for windows under 150 runes), but a setting that recurs in 3 or more of the 5 lists is rare by chance: with N = 2,000 kept of S settings per item, the expected number of
settings in k of 5 lists is C(5, k) * S * (N / S)^k, about 0.8 for k = 2 and 3e-5 for k = 3. The same count is made on the null (random keystreams, same screen) where it exists.

    python work/typo_shared_key.py <dir with library_item1..5.tsv [and null_item<i>.tsv]>      # prints the table
"""
import glob
import math
import os
import re
import sys
from collections import Counter


def read(path):
    """(settings, S) of one screen file: the set of (keystream, offset, mult, model) of the kept rows and the number of settings screened (the 'runs' of the header)"""
    rows, runs = set(), None
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# kscreen"):
                m = re.search(r"runs=(\d+)", line)
                runs = int(m.group(1)) if m else None
            if line.startswith("#") or line.startswith("ioc\t"):
                continue
            p = line.rstrip("\n").split("\t")
            if len(p) >= 5:
                rows.add((p[1], int(p[2]), int(p[3]), int(p[4])))
    return rows, runs


def table(files):
    sets = {i: read(p) for i, p in files.items()}
    cnt = Counter()
    for rows, _ in sets.values():
        cnt.update(rows)
    ks = len(sets)
    S = max(r for _, r in sets.values() if r)
    N = max(len(rows) for rows, _ in sets.values())
    out = {}
    for k in range(2, ks + 1):
        obs = sum(1 for v in cnt.values() if v >= k)
        exp = math.comb(ks, k) * S * (N / S) ** k          # settings expected in exactly k lists (>= k is the same to first order)
        out[k] = (obs, exp)
    return out, ks, N, S, cnt


def main():
    d = sys.argv[1]
    lib = {i: p for i in range(1, 6) for p in glob.glob(os.path.join(d, f"library_item{i}.tsv"))}
    nul = {i: p for i in range(1, 6) for p in glob.glob(os.path.join(d, f"null_item{i}.tsv"))}
    print(f"library lists: items {sorted(lib)}; null lists: items {sorted(nul)}")
    for name, files in (("library, all items", lib), ("library, items that also have a null", {i: p for i, p in lib.items() if i in nul}), ("null", nul)):
        if len(files) < 2:
            continue
        out, ks, N, S, cnt = table(files)
        print(f"\n{name} ({ks} lists of {N} settings out of {S:,} screened):")
        for k, (obs, exp) in out.items():
            print(f"   settings in at least {k} lists: {obs}   (chance expectation {exp:.2g})")
        top = [(k, v) for k, v in cnt.items() if v >= 2][:5]
        if top:
            print("   example recurring settings: " + "; ".join(f"{k[0]!r} offset {k[1]} x{k[2]} model {k[3]} in {v} lists" for k, v in sorted(top, key=lambda t: -t[1])[:5]))


if __name__ == "__main__":
    main()
