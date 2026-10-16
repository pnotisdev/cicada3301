"""Phase 3: which cipher generators reproduce the unsolved text's fingerprint?

Fingerprint of segments 0.7-0.15: doublets 0.66% (random 3.45%), all other adjacent
differences flat, IoC ~1.00, lag-2+ coincidences normal (~3.45%).

    python sim.py            # run every generator on English (Emerson) and print a table
"""
import math
import os
import random
import re
from collections import Counter

import lp
import stats

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))


# ---------------------------------------------------------------- English -> runes

def english_runes(path=os.path.join(HERE, "ref", "emerson_essays1.txt"), start_marker="SELF-RELIANCE"):
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = text[text.index(start_marker, text.index(start_marker) + 1):]
    text = text.split("*** END OF")[0]
    out = []
    for w in re.findall(r"[A-Za-z]+", text):
        w = w.upper().replace("IO", "IA")  # ᛡ covers IA/IO
        out += lp.word_to_key(w)
    return out


# ---------------------------------------------------------------- fingerprint

def fingerprint(c):
    n = len(c) - 1
    d = Counter((b - a) % N for a, b in zip(c, c[1:]))
    e = n / N
    chi_wo0 = sum((d[k] - e) ** 2 / e for k in range(1, N))
    lag2 = sum(c[i] == c[i + 2] for i in range(len(c) - 2)) / (len(c) - 2)
    f_share = c.count(0) / len(c)
    return dict(doublet=100 * d[0] / n, chi=chi_wo0, ioc=lp.ioc(c), lag2=100 * lag2, f=100 * f_share)


def target():
    rates = [fingerprint(lp.runes_of(stats.SEGS[i])) for i in stats.UNSOLVED if len(lp.runes_of(stats.SEGS[i])) > 100]
    c = stats.stream()
    fp = fingerprint(c)
    fp["chi"] = sum(r["chi"] for r in rates) / len(rates)  # per-segment average, comparable scale
    return fp


# ---------------------------------------------------------------- generators
# Each takes plaintext rune list p and a Random, returns ciphertext list.

def g_random(p, R):
    return [(x + R.randrange(N)) % N for x in p]


def g_random_fliteral(p, R):
    return [0 if x == 0 else (x + R.randrange(N)) % N for x in p]


def g_running_key(p, R, key=None):
    return [(x + k) % N for x, k in zip(p, key)]


def g_beaufort(p, R, key=None):
    return [(k - x) % N for x, k in zip(p, key)]


def g_totient(p, R):
    ps = lp.primes(len(p) + 5)
    return [(x + ps[i] - 1) % N for i, x in enumerate(p)]


def g_pt_autokey(p, R, primer=(23, 10, 1, 10, 9, 10, 16, 26)):
    key = list(primer) + p
    return [(x + key[i]) % N for i, x in enumerate(p)]


def g_pt_autokey1(p, R):
    return [(x + (p[i - 1] if i else 0)) % N for i, x in enumerate(p)]


def g_ct_autokey(p, R):
    c, prev = [], 0
    for x in p:
        prev = (x + prev) % N
        c.append(prev)
    return c


def g_ct_autokey_random(p, R):
    c, prev = [], 0
    for x in p:
        prev = (x + prev + R.randrange(N)) % N
        c.append(prev)
    return c


def g_prime_ct_autokey(p, R):
    c, prev = [], 0
    for x in p:
        prev = (x + lp.PRIME[prev]) % N
        c.append(prev)
    return c


def g_prime_pt_autokey(p, R):
    return [(x + (lp.PRIME[p[i - 1]] if i else 0)) % N for i, x in enumerate(p)]


def g_progressive(p, R):
    return [(x + i) % N for i, x in enumerate(p)]


def g_cumulative(p, R):
    c, s = [], 0
    for x in p:
        s = (s + x) % N
        c.append(s)
    return c


def g_key_no_repeat(p, R):
    c, k = [], -1
    for x in p:
        nk = R.randrange(N)
        while nk == k:
            nk = R.randrange(N)
        k = nk
        c.append((x + k) % N)
    return c


def make_reroll(q):
    """Random key, but when the new rune would equal the previous ciphertext rune,
    with probability q the encryptor moves on to a fresh key value."""
    def g(p, R):
        c = []
        for x in p:
            y = (x + R.randrange(N)) % N
            while c and y == c[-1] and R.random() < q:
                y = (x + R.randrange(N)) % N
            c.append(y)
        return c
    return g


def make_skip_key(q, key_fn=None):
    """Keystream (default random) where a collision makes the encryptor skip to the next
    key element with probability q — i.e. key index advances by more than one."""
    def g(p, R):
        c, j = [], 0
        ks = key_fn(len(p) * 3) if key_fn else [R.randrange(N) for _ in range(len(p) * 3)]
        for x in p:
            y = (x + ks[j]) % N
            j += 1
            while c and y == c[-1] and R.random() < q:
                y = (x + ks[j]) % N
                j += 1
            c.append(y)
        return c
    return g


def make_plus_one(q):
    """On collision, add 1 to the ciphertext rune (deterministic fix-up) with probability q."""
    def g(p, R):
        c = []
        for x in p:
            y = (x + R.randrange(N)) % N
            if c and y == c[-1] and R.random() < q:
                y = (y + 1) % N
            c.append(y)
        return c
    return g


def run():
    eng = english_runes()
    half = len(eng) // 2
    p, other = eng[:13000], eng[half:half + 13000]
    rev_other = other[::-1]
    R = random.Random(3301)
    ps = lp.primes(13000 * 3 + 10)
    gens = [
        ("plaintext (English, no cipher)", lambda p, R: p),
        ("Vigenere, random key", g_random),
        ("random key + literal F", g_random_fliteral),
        ("running key: English (c=p+k)", lambda p, R: g_running_key(p, R, other)),
        ("running key: English reversed", lambda p, R: g_running_key(p, R, rev_other)),
        ("Beaufort, English key (c=k-p)", lambda p, R: g_beaufort(p, R, other)),
        ("totient-prime stream (An End)", g_totient),
        ("plaintext autokey, primer DIVINITY", g_pt_autokey),
        ("plaintext autokey lag 1", g_pt_autokey1),
        ("ciphertext autokey", g_ct_autokey),
        ("ciphertext autokey + random", g_ct_autokey_random),
        ("prime-value ciphertext autokey", g_prime_ct_autokey),
        ("prime-value plaintext autokey", g_prime_pt_autokey),
        ("progressive shift k=i", g_progressive),
        ("cumulative sum (k = sum of previous p)", g_cumulative),
        ("random key, key never repeats", g_key_no_repeat),
        ("collision re-roll q=1.0", make_reroll(1.0)),
        ("collision re-roll q=0.8", make_reroll(0.8)),
        ("collision skip-key q=0.8 (random key)", make_skip_key(0.8)),
        ("collision skip-key q=0.8 (totient key)", make_skip_key(0.8, lambda n: [x - 1 for x in ps[:n]])),
        ("collision skip-key q=0.8 (English key)", make_skip_key(0.8, lambda n: (other * 3)[:n])),
        ("collision +1 fix-up q=0.8", make_plus_one(0.8)),
    ]
    t = target()
    print(f"{'generator':42s} {'doublet%':>8s} {'chi2(d!=0)':>10s} {'IoC':>6s} {'lag2%':>6s} {'F%':>5s}  match")
    print(f"{'TARGET: unsolved 0.7-0.15':42s} {t['doublet']:8.2f} {t['chi']:10.1f} {t['ioc']:6.3f} {t['lag2']:6.2f} {t['f']:5.2f}")
    print("-" * 92)
    results = []
    for name, g in gens:
        # chi2 is computed on 1,500-rune chunks to match the per-segment target scale
        c = g(p, R)
        fp = fingerprint(c)
        chunks = [fingerprint(c[i:i + 1500])["chi"] for i in range(0, len(c) - 1499, 1500)]
        fp["chi"] = sum(chunks) / len(chunks)
        ok = (abs(fp["doublet"] - t["doublet"]) < 0.35 and fp["chi"] < 2 * t["chi"]
              and abs(fp["ioc"] - 1.0) < 0.05 and abs(fp["lag2"] - t["lag2"]) < 0.5)
        results.append((name, fp, ok))
        print(f"{name:42s} {fp['doublet']:8.2f} {fp['chi']:10.1f} {fp['ioc']:6.3f} {fp['lag2']:6.2f} {fp['f']:5.2f}  {'YES' if ok else ''}")
    return t, results


if __name__ == "__main__":
    run()
