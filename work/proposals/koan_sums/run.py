"""koan_sums: the pre-registered squares close-out. Segment 0.5's solved plaintext sums
against the 0.6 square's free parameters, with stated family sizes and a shuffled null.

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import PRIME, print_verdict
import lp  # noqa: E402  (imported via common's path)


def koan_words_and_clauses(segs):
    """Word spans (start,end) and clause groupings of segment 0.5's plaintext."""
    plain = lp.KNOWN[5][1](lp.runes_of(segs[5]))
    spans, cur_clause, clauses, start, pos = [], [], [], None, 0
    for t in segs[5] + [" "]:
        if isinstance(t, int):
            if start is None:
                start = pos
            pos += 1
        elif t in ("\n", "%"):
            continue
        else:
            if start is not None:
                spans.append((start, pos))
                cur_clause.append((start, pos))
                start = None
            if t == "." and cur_clause:
                clauses.append(cur_clause)
                cur_clause = []
    return plain, spans, clauses


def main():
    print("=" * 72)
    print("koan_sums: pre-registered squares close-out (0.5 plaintext vs 0.6 seeds)")
    print("=" * 72)
    segs = lp.load_segments()
    plain, spans, clauses = koan_words_and_clauses(segs)
    wsum = [sum(PRIME[plain[i]] for i in range(a, b)) for a, b in spans]
    words = [plain[a:b] for a, b in spans]

    # sanity checks (must hold for the run to count)
    sums = {tuple(w): s for w, s in zip(words, wsum)}
    def v(w):
        return sum(PRIME[x] for x in lp.runes_of_str(w)) if hasattr(lp, "runes_of_str") else None
    expect = {"UOICE": 121, "MASTER": 358, "CIRCUMFERENCE": 398, "THE": 72}
    # note: "THE" is spelled TH+E in the book's runes (5 + 67 = 72)
    ok_sanity = True
    for w, target in expect.items():
        vals = [s for word, s in sums.items() if list(word) == common.to_runes(w)]
        got = vals[0] if vals else None
        ok_sanity &= (got == target)
        print("   sanity %-14s = %s (expected %d)" % (w, got, target))

    T7 = {809, 434, 312, 966, 1311, 204, 1246}          # free parameters + t
    T13 = {204, 278, 280, 312, 434, 620, 626, 809, 812, 934, 966, 1071, 1311}
    T25 = [434, 1311, 312, 278, 966, 204, 812, 934, 280, 1071, 626, 620, 809,
           620, 626, 1071, 280, 934, 812, 204, 966, 278, 312, 1311, 434]

    w2 = [wsum[i] + wsum[i + 1] for i in range(len(wsum) - 1)]
    csum = [sum(PRIME[plain[i]] for a, b in cl for i in range(a, b)) for cl in clauses]
    print("family sizes: F1 words %d | F2 2-word sums %d | F3 clauses %d"
          % (len(wsum), len(w2), len(csum)))

    hits = []
    for name, vals in (("F1 word sums", wsum), ("F2 2-word sums", w2), ("F3 clause sums", csum)):
        h7 = sorted(set(vals) & T7)
        h13 = sorted(set(vals) & T13)
        h25 = sorted(set(vals) & set(T25))
        hits.append(len(h7))
        print("%-14s size %4d: hits vs 7 seeds %s | vs 13 values %s | vs 25 cells %s"
              % (name, len(vals), h7 or "none", h13 or "none", h25 or "none"))

    # null: 200 shuffles of the word sums, same 7-target check
    rng = random.Random(20261017)
    null_counts = []
    for _ in range(200):
        sh = wsum[:]
        rng.shuffle(sh)
        null_counts.append(len(set(sh) & T7))
    mean = sum(null_counts) / len(null_counts)
    print("null (200 shuffles, F1 vs 7 seeds): mean %.2f hits, max %d, observed %d"
          % (mean, max(null_counts), hits[0]))

    above = hits[0] > max(null_counts)
    print("CONCLUSION: %s" % ("seeds present above chance -> squares line REVIVED"
                              if above else "at chance -> squares line closed as proposed"))
    return print_verdict("koan_sums", ok_sanity,
                         "sanity %s | F1 hits %d vs null max %d -> %s" %
                         (ok_sanity, hits[0], max(null_counts),
                          "revived" if above else "closed"))


if __name__ == "__main__":
    sys.exit(main())
