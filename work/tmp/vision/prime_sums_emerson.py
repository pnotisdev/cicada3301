"""External null: prime rate of Gematria sentence sums for ordinary English (Emerson, Essays I) in GP runes (scouting)."""
import os, re, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import lp
def sieve(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]: s[i * i::i] = bytearray(len(s[i * i::i]))
    return s
IS_P = sieve(400000)
txt = open(os.path.join(HERE, "..", "..", "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
txt = re.sub(r"\s+", " ", txt)
sents = re.split(r"(?<=[.!?])\s+", txt)
order = sorted(range(lp.N), key=lambda i: -len(lp.LATIN[i]))
def to_runes(s):
    w = re.sub(r"[^A-Za-z ]", "", s).upper().replace("QU", "CW")
    out = []
    for word in w.split():
        while word:
            for i in order:
                if word.startswith(lp.LATIN[i]) and not (lp.LATIN[i] in ("EO", "OE", "AE", "IA", "EA", "ING")):
                    out.append(i); word = word[len(lp.LATIN[i]):]; break
            else:
                a = {"V": 1, "K": 5, "Z": 15, "Q": 5}
                out.append(a.get(word[0], 0)); word = word[1:]
    return out
bins = {}
for s in sents:
    r = to_runes(s)
    n = len(r)
    if n < 6 or n > 200: continue
    S = sum(lp.PRIME[j] for j in r)
    b = "<=25" if n <= 25 else "26-40" if n <= 40 else "41-80" if n <= 80 else ">80"
    t = bins.setdefault(b, [0, 0, 0]); t[0] += 1; t[1] += IS_P[S]; t[2] += S % 2
print("Emerson sentences (GP letters, TH as T+H not merged... digraph runes TH only):")
for b in ("<=25", "26-40", "41-80", ">80"):
    n, p, o = bins[b]
    print(f"  length {b:6s} n={n:5d}  prime {100*p/n:5.1f}%  odd {100*o/n:5.1f}%")
