"""Phase 4: library of candidate keystreams (each a numpy int array mod 29).

Families: number-theoretic integer sequences, digits of constants (base 10 and 29),
geometric sequences mod 29, Cicada numbers (3301, 1033, the magic squares, page-30 grid,
An End hash), and keywords / phrases from the solved text (repeated).
"""
import re

import numpy as np

import lp

N = lp.N
LEN = 20000


def sieve(limit):
    m = np.ones(limit + 1, dtype=bool)
    m[:2] = False
    for i in range(2, int(limit ** 0.5) + 1):
        if m[i]:
            m[i * i::i] = False
    return np.nonzero(m)[0].tolist()


_PRIMES = sieve(3_500_000)  # 250k primes: enough for p_(p_n) and offsets


def _arr(seq):
    return np.array([int(x) % N for x in seq[:LEN]], dtype=np.int64)


def _cycle(vals):
    vals = list(vals)
    return _arr((vals * (LEN // len(vals) + 1))[:LEN])


def integer_sequences():
    out = {}
    ps = _PRIMES[:LEN + 10]
    pset = set(_PRIMES[:LEN * 4])
    n = np.arange(LEN, dtype=object)
    out["primes"] = _arr(ps)
    out["primes-1 (totient)"] = _arr([p - 1 for p in ps])
    out["primes+1"] = _arr([p + 1 for p in ps])
    out["primes^2"] = _arr([p * p for p in ps])
    out["prime gaps"] = _arr([b - a for a, b in zip(ps, ps[1:])])
    out["prime index of primes"] = _arr([_PRIMES[p - 1] for p in ps[:LEN] if p - 1 < len(_PRIMES)])
    out["primes from 3301"] = _arr([p for p in _PRIMES[:LEN + 500] if p >= 3301])
    out["cumulative prime sum"] = _arr(np.cumsum(np.array(ps, dtype=object)))
    out["n"] = _arr(range(1, LEN + 1))
    out["n^2"] = _arr([i * i for i in range(1, LEN + 1)])
    out["n^3"] = _arr([i ** 3 for i in range(1, LEN + 1)])
    out["triangular"] = _arr([i * (i + 1) // 2 for i in range(1, LEN + 1)])
    fib, luc, pell = [0, 1], [2, 1], [0, 1]
    while len(fib) < LEN:
        fib.append((fib[-1] + fib[-2]) % N)
        luc.append((luc[-1] + luc[-2]) % N)
        pell.append((2 * pell[-1] + pell[-2]) % N)
    out["fibonacci"] = _arr(fib)
    out["lucas"] = _arr(luc)
    out["pell"] = _arr(pell)
    # arithmetic functions
    M = LEN + 2
    phi = list(range(M))
    for i in range(2, M):
        if phi[i] == i:
            for j in range(i, M, i):
                phi[j] -= phi[j] // i
    sigma = [0] * M
    divs = [0] * M
    for i in range(1, M):
        for j in range(i, M, i):
            sigma[j] += i
            divs[j] += 1
    out["phi(n)"] = _arr(phi[1:])
    out["sigma(n)"] = _arr(sigma[1:])
    out["d(n)"] = _arr(divs[1:])
    out["cumulative phi(n)"] = _arr(np.cumsum(np.array(phi[1:], dtype=object)))
    out["composites"] = _arr([i for i in range(4, 3 * LEN) if i not in pset])
    big = set(_PRIMES)
    out["emirps"] = _arr([p for p in _PRIMES if p > 10 and str(p) != str(p)[::-1] and int(str(p)[::-1]) in big])
    out["gematria primes cycle"] = _cycle(lp.PRIME)
    for a in range(2, N):
        out[f"{a}^n mod 29"] = _arr([pow(a, i, N) for i in range(LEN)])
    out["3301*n"] = _arr([3301 * i for i in range(1, LEN + 1)])
    out["1033*n"] = _arr([1033 * i for i in range(1, LEN + 1)])
    out["3301^n"] = _arr([pow(3301, i, N) for i in range(1, LEN + 1)])
    return out


def constant_digits():
    import mpmath
    out = {}
    mpmath.mp.dps = 32000
    consts = {"pi": mpmath.pi, "e": mpmath.e, "phi": (1 + mpmath.sqrt(5)) / 2, "sqrt2": mpmath.sqrt(2),
              "sqrt3": mpmath.sqrt(3), "ln2": mpmath.log(2)}
    for name, v in consts.items():
        s = mpmath.nstr(v, 25000, strip_zeros=False).replace(".", "")
        out[f"{name} digits (base 10)"] = _arr([int(ch) for ch in s])
    for name, v in consts.items():
        # base-29 digits of the fractional part via one big-integer conversion
        x = int(mpmath.floor((v - mpmath.floor(v)) * mpmath.mpf(N) ** LEN))
        dig = []
        while x:
            x, d = divmod(x, N)
            dig.append(d)
        dig = (dig + [0] * (LEN - len(dig)))[::-1]
        out[f"{name} digits (base 29)"] = _arr(dig)
    return out


def cicada_numbers():
    segs = lp.load_segments()
    out = {}

    def nums(seg):
        return [int(t[1:]) for t in segs[seg] if isinstance(t, str) and t.startswith("#") and t[1:].isdigit()]

    sq14 = nums(6)[:25]
    out["page-14 square rows"] = _cycle(sq14)
    out["page-14 square cols"] = _cycle([sq14[r * 5 + c] for c in range(5) for r in range(5)])
    g30 = nums(10)[:16]
    out["page-30 grid rows"] = _cycle(g30)
    out["page-30 grid cols"] = _cycle([g30[r * 4 + c] for c in range(4) for r in range(4)])
    # 0.2 word grid with Gematria sums
    vals, cur = [], []
    for t in segs[2] + [" "]:
        if isinstance(t, int):
            cur.append(t)
        else:
            if cur:
                vals.append(sum(lp.PRIME[x] for x in cur))
                cur = []
            if t.startswith("#"):
                vals.append(int(t[1:]))
    out["1033 square rows"] = _cycle(vals[-25:])
    h = "".join(t[1:] for t in segs[16] if isinstance(t, str) and t.startswith("#"))
    out["An End hash bytes"] = _cycle(bytes.fromhex(h))
    out["An End hash nibbles"] = _cycle([int(ch, 16) for ch in h])
    grid_primes = [3301 - x for x in g30[:12]]           # 43 79 149 263 23 2 3 463 13 7 5 829, all prime
    out["page-30 grid primes (3301-x)"] = _cycle(grid_primes)
    out["page-30 grid primes sorted"] = _cycle(sorted(grid_primes))
    out["page-30 grid first 12"] = _cycle(g30[:12])
    out["page-30 last row"] = _cycle(g30[12:])
    out["caption 0.10 gematria sums"] = _cycle([149, 489])
    out["caption 0.10 runes"] = _cycle(lp.runes_of(segs[10]))
    out["caption 0.10 prime values"] = _cycle([lp.PRIME[x] for x in lp.runes_of(segs[10])])
    out["3301 digits"] = _cycle([3, 3, 0, 1])
    out["1033 digits"] = _cycle([1, 0, 3, 3])
    return out


def keywords():
    """Repeating keys from words and short phrases of the solved plaintext."""
    segs = lp.load_segments()
    words, phrases = set(), set()
    for i, (title, f) in lp.KNOWN.items():
        plain = f(lp.runes_of(segs[i]))
        ws = [w for w, _, _ in lp.word_spans(segs[i], plain)]
        words.update(w for w in ws if len(w) >= 4)
        for a in range(len(ws) - 1):
            phrases.add(" ".join(ws[a:a + 2]))
    extra = ["DIVINITY", "FIRFUMFERENFE", "CIRCUMFERENCE", "INSTAR", "EMERGENCE", "PRIMALITY", "TOTIENT",
             "PILGRIM", "CICADA", "LIBERPRIMUS", "INTUS", "PARABLE", "KOAN", "WELCOME", "DEEPWEB", "SELFRELIANCE",
             "AGRIPPA", "THELEMA", "MOBIUS", "AETHEREAL", "OBSCURA", "CABAL", "ANALOG", "MOURNFUL", "SHADOWS",
             "BUFFERS", "CARNAL", "VOID", "FULMAEAYOEA"]
    out = {}
    for w in sorted(words | set(extra)) + sorted(phrases):
        key = lp.word_to_key(re.sub(r"[^A-Z]", "", w))
        if key:
            out[f"kw:{w}"] = _cycle(key)
    return out


def all_keystreams():
    ks = {}
    ks.update(integer_sequences())
    ks.update(constant_digits())
    ks.update(cicada_numbers())
    ks.update(keywords())
    return ks


def english_distribution():
    import sim
    p = sim.english_runes()
    return np.bincount(p, minlength=N) / len(p)


def predicted_ioc(ks, P, sign=1, atbash=False, n=4000):
    """IoC the ciphertext would have (infinite sample) for English plaintext under this key."""
    h = np.bincount(ks[:n] % N, minlength=N) / n
    if atbash:
        P = P[::-1]
    Q = np.zeros(N)
    for k in range(N):
        if h[k]:
            Q += h[k] * np.roll(P, sign * k)
    return float(N * (Q ** 2).sum())


def period(ks, max_p=5000, probe=3000):
    """Smallest period p <= max_p (exact repetition over `probe` values), else None."""
    for p in np.flatnonzero(ks[1:max_p + 1] == ks[0]) + 1:   # only shifts that repeat the first value can match
        if np.array_equal(ks[p:p + probe], ks[:probe]):
            return int(p)
    return None


def number_keystreams():
    """Everything except keywords: the sequences that need sliding offsets."""
    ks = {}
    ks.update(integer_sequences())
    ks.update(constant_digits())
    ks.update(cicada_numbers())
    return ks
