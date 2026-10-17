"""Stream families proposed by an outside LLM (F1, F3, F4, F5 of 2026-10-17), built for the library-wide kscreen screens: data/sacred.ksb + data/sacred.tsv.  (F2, order-4 recurrences, is not built.)

    F1  binary combinations of two number-theoretic streams: s1 + t * s2 (t in 1, -1, 2, 1/2, 3, 1/3) and the interleave of the two, over 20 core streams (the overall multiplier is the screen's)
    F3  a number-theoretic function read at the primes: f(p_i + d), f in phi, sigma, d, Fibonacci, Lucas, Pell, triangular, d in -1, 0, 1 (phi(p) and sigma(p) are already library streams: dropped as duplicates)
    F4  base-29 digits of the reciprocals and ratios of the book's two numbers: 1/3301, 1/1033, 3301/1033, 1033/3301, 1/(3301 * 1033)  (digits in bases 10, 16 and 60 are not uniform mod 29: excluded as keys by LP2's flat IoC)
    F5  rational functions of the prime residue r = p mod 29, e.g. r / (r - 1) (primes at a pole are skipped)

    --round 2: the five families DeepSeek proposed next (G1 n^-1, G2 discrete log, G3 g^n, G4 n^3, all mod p for p = 59, 233, 349, 523, 929 reduced mod 29, whole periods so the stream is exactly uniform; G5 the sum of the two
    base-29 digits of n): data/sacred2.ksb, sacred2.tsv

Every stream is dropped when (a) LP2's flat IoC already excludes it as a key (predicted IoC under English > 1.003, as export.py's library flag) or (b) it equals a library stream up to an affine map c -> a c + b
(the screen's multiplier and the free constant offset cover those). What is left is listed in data/sacred.tsv with its family.

    python work/kscreen/sacred.py          # -> work/kscreen/data/sacred.ksb, sacred.tsv
"""
import os
import sys
from fractions import Fraction

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import keystreams  # noqa: E402
import export  # noqa: E402

N = 29
L = keystreams.LEN
OUT = os.path.join(HERE, "data")
CORE = ["primes", "prime gaps", "cumulative prime sum", "n", "n^2", "n^3", "triangular", "fibonacci", "lucas", "pell", "phi(n)", "sigma(n)", "d(n)",
        "cumulative phi(n)", "composites", "emirps", "primes^2", "primes^3", "primes digit sum", "primes reversed digits"]
TS = [(1, "1"), (28, "-1"), (2, "2"), (15, "1/2"), (3, "3"), (10, "1/3")]


def canon(v, n=400):
    """affine-invariant form of a stream: shifted and scaled so that the first two distinct values are 0 and 1 (None for a constant stream)"""
    v = np.asarray(v[:n]) % N
    nz = np.flatnonzero(v != v[0])
    if len(nz) == 0:
        return None
    inv = pow(int((v[nz[0]] - v[0]) % N), -1, N)
    return ((v - v[0]) * inv % N).astype(np.uint8).tobytes()


def arithmetic(M):
    """phi, sigma, d for n < M"""
    phi = np.arange(M, dtype=np.int64)
    sig = np.zeros(M, dtype=np.int64)
    dd = np.zeros(M, dtype=np.int64)
    for i in range(2, M):
        if phi[i] == i:                         # i is prime
            phi[i::i] -= phi[i::i] // i
    for i in range(1, M):
        sig[i::i] += i
        dd[i::i] += 1
    return phi, sig, dd


def linear_mod(a0, a1, f, M):
    """a_n mod 29 for n < M with a_(n+1) = f(a_n, a_(n-1))"""
    out = np.empty(M, dtype=np.int64)
    out[0], out[1] = a0, a1
    for n in range(2, M):
        out[n] = f(out[n - 1], out[n - 2]) % N
    return out


def f1(base):
    out = {}
    for i, a in enumerate(CORE):
        for b in CORE[i + 1:]:
            x, y = base[a][:L] % N, base[b][:L] % N
            for t, tn in TS:
                out[f"F1 {a} + {tn}*{b}"] = (x + t * y) % N
            z = x.copy()
            z[1::2] = y[1::2]
            out[f"F1 interleave {a} | {b}"] = z
    return out


def f3():
    ps = np.array(keystreams._PRIMES[:L + 5], dtype=np.int64)
    M = int(ps.max()) + 3
    phi, sig, dd = arithmetic(M)
    fib = linear_mod(0, 1, lambda a, b: a + b, M)
    luc = linear_mod(2, 1, lambda a, b: a + b, M)
    pell = linear_mod(0, 1, lambda a, b: 2 * a + b, M)
    tri = (np.arange(M, dtype=np.int64) * (np.arange(M, dtype=np.int64) + 1) // 2) % N
    fs = {"phi": phi, "sigma": sig, "d": dd, "Fibonacci": fib, "Lucas": luc, "Pell": pell, "triangular": tri}
    out = {}
    for name, f in fs.items():
        for d in (-1, 0, 1):
            out[f"F3 {name}(p+{d})".replace("+-", "-")] = f[ps[:L] + d] % N
    return out


def digits(num, den, base, n):
    out, r = [], num % den
    for _ in range(n):
        r *= base
        out.append(r // den)
        r %= den
    return np.array(out, dtype=np.int64) % N


def f4():
    out = {}
    for num, den, tag in ((1, 3301, "1/3301"), (1, 1033, "1/1033"), (3301, 1033, "3301/1033"), (1033, 3301, "1033/3301"), (1, 3301 * 1033, "1/(3301*1033)")):
        out[f"F4 {tag} base 29"] = digits(num, den, N, L)
    return out


def f5():
    ps = np.array(keystreams._PRIMES[:L + 400], dtype=np.int64)
    r = ps % N
    inv = {x: pow(x, -1, N) for x in range(1, N)}
    funcs = {
        "r/(r-1)": (lambda x: x * inv[(x - 1) % N], (0, 1)),
        "(r-1)/r": (lambda x: (x - 1) * inv[x], (0,)),
        "(r+1)/(r-1)": (lambda x: (x + 1) * inv[(x - 1) % N], (0, 1)),
        "(r-1)/(r+1)": (lambda x: (x - 1) * inv[(x + 1) % N], (0, 28)),
        "r^2/(r-1)": (lambda x: x * x * inv[(x - 1) % N], (0, 1)),
        "1/(r-1)": (lambda x: inv[(x - 1) % N], (0, 1)),
        "r^2": (lambda x: x * x, ()),
        "r + 1/r": (lambda x: x + inv[x], (0,)),
    }
    out = {}
    for name, (f, bad) in funcs.items():
        keep = r[~np.isin(r, bad)][:L]
        out[f"F5 {name}"] = np.array([f(int(x)) % N for x in keep], dtype=np.int64)
    return out


P2 = [59, 233, 349, 523, 929]


def n_for(period):
    return period * ((L + period - 1) // period)


def primroot(p):
    fs = [q for q in range(2, p) if (p - 1) % q == 0 and all(q % r for r in range(2, int(q ** 0.5) + 1))]
    return next(g for g in range(2, p) if all(pow(g, (p - 1) // q, p) != 1 for q in fs))


def g_families():
    out = {}
    for p in P2:
        per = p - 1
        n = n_for(per)
        g = primroot(p)
        out[f"G1 inverse mod {p}"] = np.array([pow(i % per + 1, p - 2, p) % N for i in range(n)], dtype=np.int64)
        log, x = [0] * p, 1
        for e in range(per):
            log[x] = e
            x = x * g % p
        out[f"G2 discrete log mod {p}"] = np.array([log[i % per + 1] % N for i in range(n)], dtype=np.int64)
        x, v = 1, []
        for _ in range(n):
            v.append(x % N)
            x = x * g % p
        out[f"G3 g^n mod {p}"] = np.array(v, dtype=np.int64)
        if p in (59, 233, 929):                  # gcd(3, p - 1) = 1: the cube is a permutation
            out[f"G4 n^3 mod {p}"] = np.array([pow(i % per + 1, 3, p) % N for i in range(n)], dtype=np.int64)
    out["G5 base-29 digit sum"] = np.array([(i % 841 // N + i % 841 % N) % N for i in range(24 * 841)], dtype=np.int64)
    return out


def main(rnd=1):
    os.makedirs(OUT, exist_ok=True)
    print("building the library for the duplicate check ...")
    lib = export.library()
    seen = {}
    for name, v in lib.items():
        c = canon(v)
        if c is not None:
            seen.setdefault(c, name)
    P = keystreams.english_distribution()
    cand = {}
    if rnd == 1:
        base = {}
        base.update(keystreams.number_keystreams())
        base.update(export.new_number_families())
        missing = [c for c in CORE if c not in base]
        assert not missing, f"core streams missing from the library: {missing}"
        for fn in (lambda: f1(base), f3, f4, f5):
            cand.update(fn())
    else:
        cand.update(g_families())
    kept, stats = {}, {}
    for name, v in cand.items():
        fam = name.split()[0]
        s = stats.setdefault(fam, {"built": 0, "constant": 0, "flat-IoC excluded": 0, "duplicate": 0, "kept": 0})
        s["built"] += 1
        c = canon(v)
        if c is None:
            s["constant"] += 1
            continue
        n = min(4000, len(v))
        pi = max(keystreams.predicted_ioc(v, P, 1, n=n), keystreams.predicted_ioc(v, P, -1, n=n))
        if pi > 1.003:
            s["flat-IoC excluded"] += 1
            continue
        if c in seen:
            s["duplicate"] += 1
            continue
        seen[c] = name
        kept[name] = v
        s["kept"] += 1
    tag = "sacred" if rnd == 1 else "sacred2"
    rows = export.write_ksb(os.path.join(OUT, tag + ".ksb"), kept, os.path.join(OUT, tag + ".tsv"))
    for fam, s in sorted(stats.items()):
        print(fam, s)
    print(f"{tag}.ksb: {len(rows)} streams")
    return stats


if __name__ == "__main__":
    main(2 if "--round" in sys.argv and sys.argv[sys.argv.index("--round") + 1] == "2" else 1)
