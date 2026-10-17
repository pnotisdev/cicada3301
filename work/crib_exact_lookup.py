"""Exact lookup of the community's crib keys in the OEIS library (work/prngx/data/oeis_seqs.txt, 199,088 sequences mod 29).

If the first 13 runes of LP2 (the red heading) say DIVINITY WITHIN, their key K = C - P (mod 29) is 13 known values; if the 141 body runes say 'FIND YOU ARE ...', 141 more.
A keystream that equals m * a(n+o) + b (mod 29) has ARITHMETIC DIFFERENCES m * (a(n+o+1) - a(n+o)), so a known key is found by matching its 12 differences against the
library's differences under each of the 28 multipliers m (the constant b drops out). The chance of an accidental 12-difference match is 29^-12 per place, so a hit would
be decisive, a miss only excludes OEIS (as a stream, with a shift and a multiplier) for THIS crib.

    python work/crib_exact_lookup.py     # -> results/analysis/crib_exact_lookup.txt
"""
import os
import sys

import numpy as np

import lp
import stats

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "prngx", "data", "oeis_seqs.txt")
N = lp.N
OUT = []
HEAD_P = [23, 10, 1, 10, 9, 10, 16, 26, 7, 10, 2, 10, 9]          # D I V I N I T Y  W I TH I N (V = U)


def say(s=""):
    print(s)
    OUT.append(s)


def library():
    ids, chunks, cut = [], [], 0
    for line in open(LIB, encoding="utf-8"):
        f = line.split()
        v = np.array(f[1:], dtype=np.int64)
        d = np.diff(v) % N
        chunks.append(d.astype(np.uint8)); chunks.append(np.array([255], np.uint8))          # 255 separates sequences
        ids.append((f[0], cut, len(d))); cut += len(d) + 1
    return ids, np.concatenate(chunks).tobytes(), np.array([i[1] for i in ids])


def search(diffs, blob, starts, ids):
    """[(sequence id, offset, multiplier)] with m * lib_diff == diffs at that offset"""
    hits = []
    pat = bytes(int(x) for x in diffs)
    for m in range(1, N):
        tr = bytes([(m * v) % N if v < N else 255 for v in range(256)])
        t = blob.translate(tr)
        p = t.find(pat)
        while p >= 0:
            j = int(np.searchsorted(starts, p, side="right")) - 1
            hits.append((ids[j][0], p - ids[j][1], m))
            p = t.find(pat, p + 1)
    return hits


def main():
    ids, blob, starts = library()
    say(f"{len(ids)} sequences, {len(blob)} differences")
    # positive control: the primes (A000040) at offset 5, multiplier 3, constant 11, over 13 terms
    pr = [p for p in range(2, 400) if all(p % q for q in range(2, int(p ** 0.5) + 1))]
    ctl = [(3 * pr[5 + i] + 11) % N for i in range(13)]
    h = search(np.diff(ctl) % N, blob, starts, ids)
    say(f"control: primes at offset 5 x 3 + 11 found {[x for x in h if x[0] == 'A000040']} (all hits: {len(h)})")
    assert any(x[0] == "A000040" for x in h), "control failed"
    c = np.array(lp.runes_of(stats.SEGS[7]))
    kh = (c[:13] - np.array(HEAD_P)) % N
    say(f"heading key C - P = {kh.tolist()}")
    h = search(np.diff(kh) % N, blob, starts, ids)
    say(f"   12 differences of the heading key found in the library: {len(h)} places {h[:5]}")
    say("   (the reversed sign P - C is covered by the multiplier m = 28)")
    from crib_matrix_check import PHRASE, LENS, spell
    P = np.array([x for w, n in zip(PHRASE, LENS) for x in spell(w, n)])
    kb = (c[13:13 + 141] - P) % N
    for a, b in ((0, 13), (0, 30), (13, 43), (43, 73), (73, 103), (103, 141)):
        h = search(np.diff(kb[a:b]) % N, blob, starts, ids)
        say(f"   body key runes {a}..{b - 1} ({b - a - 1} differences): {len(h)} places in the library")
    dest = os.path.join(HERE, "..", "results", "analysis")
    with open(os.path.join(dest, "crib_exact_lookup.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
