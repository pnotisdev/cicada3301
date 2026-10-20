"""Prime-sum check of a candidate decryption: supplementary evidence, language independent (docs/CAMPAIGNS.md).

The Gematria sum of a sentence of the solved plaintext is prime far more often than chance (work/prime_sums.py:
36 of 76 body clauses, 60% of the clauses of at most 40 runes, against 12-14% for ordinary English). If LP2's plaintext
follows the same habit, a correct decryption of a window shows the same excess on the clauses it contains.

    python prime_check.py control                      # right and wrong keys on the solved pages
    python prime_check.py window <section> <start> <plain>   # plain = comma-separated rune indices 0..28 of the decoded
                                                        # runes start .. start+len-1 of LP2 section <section>

A clause counts only if it lies completely inside the decoded window. Reported: clauses, prime sums, the binomial
probability of that many primes at the chance rate 14.7%, and the short-clause (<= 40 runes) evidence in nats using the
solved pages' 60% against 14.7% (heuristic; clauses longer than 40 runes carry none). It is NOT a gate: a window with
fewer than 6 short clauses says nothing.
"""
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402

CHANCE = 0.147       # prime share of shuffled clause sums (work/prime_sums.py); ordinary English 12-14%
SACRED = 0.60        # prime share of the solved pages' clauses of at most 40 runes
SHORT = 40


def is_prime(n):
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    i = 3
    while i * i <= n:
        if n % i == 0:
            return False
        i += 2
    return True


def clause_spans(toks):
    """[(first rune index, one past the last)] of the clauses of a segment (text between '.' marks and '&' breaks)"""
    out, idx, start = [], 0, 0
    for t in toks:
        if isinstance(t, int):
            idx += 1
        elif t in (".", "&"):
            if idx > start:
                out.append((start, idx))
            start = idx
    if idx > start:
        out.append((start, idx))
    return out


def binom_tail(n, k, p):
    return sum(math.comb(n, i) * p ** i * (1 - p) ** (n - i) for i in range(k, n + 1))


def check(toks, start, plain):
    """toks: tokens of the segment; plain: decoded rune indices for runes start .. start+len(plain)-1"""
    end = start + len(plain)
    rows = []
    for a, b in clause_spans(toks):
        if a >= start and b <= end:
            s = sum(lp.PRIME[j] for j in plain[a - start:b - start])
            rows.append((a, b - a, s, is_prime(s)))
    n = len(rows)
    k = sum(r[3] for r in rows)
    short = [r for r in rows if r[1] <= SHORT]
    ks = sum(r[3] for r in short)
    llr = ks * math.log(SACRED / CHANCE) + (len(short) - ks) * math.log((1 - SACRED) / (1 - CHANCE))
    return dict(clauses=n, prime=k, p_chance=binom_tail(n, k, CHANCE) if n else 1.0, short=len(short), short_prime=ks, short_llr=llr, rows=rows)


def control():
    segs = lp.load_segments()
    rng = random.Random(3301)
    right = [0, 0, 0.0]
    wrong = [0, 0, 0.0]
    print("section  clauses  prime | short  short prime  evidence (nats)   [right key]")
    for i in (0, 1, 2, 3, 4, 5, 6, 16, 17):
        c = lp.runes_of(segs[i])
        plain = lp.KNOWN[i][1](c)
        r = check(segs[i], 0, plain)
        print(f"0.{i:<6d} {r['clauses']:7d} {r['prime']:6d} | {r['short']:5d} {r['short_prime']:11d} {r['short_llr']:16.1f}")
        right[0] += r["short"]
        right[1] += r["short_prime"]
        right[2] += r["short_llr"]
        for _ in range(40):  # wrong key: a random constant shift of the ciphertext (the right method for another page would do the same)
            k = rng.randrange(1, 29)
            w = [(x - k) % 29 for x in c]
            r = check(segs[i], 0, w)
            wrong[0] += r["short"]
            wrong[1] += r["short_prime"]
            wrong[2] += r["short_llr"]
    print(f"right keys: {right[1]} prime of {right[0]} short clauses ({100*right[1]/right[0]:.1f}%), evidence {right[2]:.1f} nats")
    print(f"wrong keys (360 random shifts): {wrong[1]} of {wrong[0]} ({100*wrong[1]/wrong[0]:.1f}%), mean evidence per decode {wrong[2]/360:.2f} nats")


if __name__ == "__main__":
    if len(sys.argv) >= 2 and sys.argv[1] == "control":
        control()
    elif len(sys.argv) == 5 and sys.argv[1] == "window":
        segs = lp.load_segments()
        sec, start = int(sys.argv[2]), int(sys.argv[3])
        plain = [int(x) for x in sys.argv[4].split(",")]
        r = check(segs[sec], start, plain)
        print({k: v for k, v in r.items() if k != "rows"})
        for a, n, s, p in r["rows"]:
            print(f"  clause at {a:5d} ({n:3d} runes) sum {s:6d} {'PRIME' if p else ''}")
    else:
        print(__doc__)
