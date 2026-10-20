"""Phase 27: the page-30 caption (segment 0.10) against a preregistered family of methods, with calibration.

    python grid30_caption.py count        # print the family size N (before anything is scored)
    python grid30_caption.py run [M]      # observed caption + nulls (M random captions each) + plant control

The family is defined in work/log/phase27_grid30_caption.md (section "Preregistered family"); this file is the
executable form of that text. Nothing here may be changed after `run` has been started once.
"""
import os
import sys
import time

import numpy as np

import grid30
import lp

os.environ.setdefault("OMP_NUM_THREADS", "1")
N29 = 29
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "results", "grid30_caption")
CACHE = os.environ.get("GRID30_CACHE", os.path.join(HERE, "tmp"))


# ----------------------------------------------------------------- the family
def key_sequences():
    ks, ps, _ = grid30.reconstruct()
    g = grid30.grid_values()
    spiral = [abs(3301 - p) for p in ps]
    colmajor = [g[c + 4 * r] for c in range(4) for r in range(4)]
    f = [1, 1]
    while len(f) < 15:
        f.append(f[-1] + f[-2])
    seqs = {
        "grid_rowmajor": g, "grid_colmajor": colmajor, "grid_spiral": spiral, "grid_revspiral": spiral[::-1],
        "k_index": ks, "p_k": ps, "p_k_rev": ps[::-1], "p_k_minus1": [p - 1 for p in ps],
        "fib_steps": f, "digits3301": [3, 3, 0, 1],
    }
    return {n: np.array([v % N29 for v in s], dtype=np.int64) for n, s in seqs.items()}


def family():
    """List of methods: dict(name, key (array or None), start, sign, atb, skip, b)."""
    ms = []
    ms.append(dict(name="plain", key=None, start=0, sign=1, atb="none", skip=False, b=0))
    for k in range(1, N29):
        ms.append(dict(name=f"shift{k}", key=np.array([k]), start=0, sign=1, atb="none", skip=False, b=0))
    for k in range(N29):
        # lp.atbash(c, k) = 28 - c + k : 'post' atbash of (c - 0) with additive constant, written as pre-atbash, key -k
        ms.append(dict(name=f"atbash+{k}", key=np.array([k]), start=0, sign=-1, atb="pre", skip=False, b=0))
    for kw in lp.KEYWORDS:
        key = np.array(lp.word_to_key(kw), dtype=np.int64)
        for start in range(len(key)):
            for sign in (1, -1):
                for atb in ("none", "post", "pre"):
                    for skip in (True, False):
                        ms.append(dict(name=f"vig:{kw}", key=key, start=start, sign=sign, atb=atb, skip=skip, b=0))
    pr = lp.primes(40)
    for nm, ks in (("totient_p-1", [p - 1 for p in pr]), ("prime_p", pr)):
        key = np.array([v % N29 for v in ks], dtype=np.int64)
        for start in range(16):
            for sign in (1, -1):
                for atb in ("none", "post", "pre"):
                    for skip in (True, False):
                        ms.append(dict(name=nm, key=key, start=start, sign=sign, atb=atb, skip=skip, b=0))
    for nm, key in key_sequences().items():
        for start in range(len(key)):
            for sign in (1, -1):
                for atb in ("none", "post", "pre"):
                    for skip in (True, False):
                        for b in range(N29):
                            ms.append(dict(name=f"grid:{nm}", key=key, start=start, sign=sign, atb=atb, skip=skip, b=b))
    return ms


def describe(m):
    return (f"{m['name']} start={m['start']} sign={m['sign']:+d} atbash={m['atb']} skipF={int(m['skip'])} b={m['b']}")


def decrypt(C, m):
    """C: (M, 9) int array of cipher rune indices -> plaintext indices (M, 9)."""
    Mn, L = C.shape
    nonf = (C != 0)
    if m["skip"]:
        J = np.cumsum(nonf, axis=1) - nonf
    else:
        J = np.broadcast_to(np.arange(L), C.shape)
    if m["key"] is None:
        kv = np.zeros(C.shape, dtype=np.int64)
    else:
        kv = m["key"][(m["start"] + J) % len(m["key"])]
    s = m["sign"]
    if m["atb"] == "pre":
        P = ((N29 - 1 - C) - s * (kv + m["b"])) % N29
    else:
        P = (C - s * (kv + m["b"])) % N29
        if m["atb"] == "post":
            P = N29 - 1 - P
    if m["skip"]:
        P = np.where(C == 0, 0, P)
    return P


# ----------------------------------------------------------------- dictionary tables
def build_tables():
    path = os.path.join(CACHE, "grid30_caption_tables.npz")
    if os.path.exists(path):
        z = np.load(path)
        return z["t4"], z["t5"], z["s4"], z["s5"]
    vocab = open(os.path.join(HERE, "ref", "english_20k.txt"), encoding="utf-8").read().split()
    primary = set(lp.COMMON_N)                      # lp's own dictionary: COMMON + top 10,000
    strict = {lp.normalize(w) for w in vocab[:2000] if len(w) >= 3}
    lat = lp.LATIN
    nrm = lp.normalize

    def tab(length, words):
        out = np.zeros(N29 ** length, dtype=bool)
        idx = 0
        import itertools
        for combo in itertools.product(range(N29), repeat=length):
            if nrm("".join(lat[x] for x in combo)) in words:
                out[idx] = True
            idx += 1
        return out

    t4, s4 = tab(4, primary), tab(4, strict)
    # 5-rune: extend 4-prefix strings (faster than recomputing everything)
    import itertools
    t5 = np.zeros(N29 ** 5, dtype=bool)
    s5 = np.zeros(N29 ** 5, dtype=bool)
    idx = 0
    for combo in itertools.product(range(N29), repeat=4):
        pre = "".join(lat[x] for x in combo)
        for x in range(N29):
            n = nrm(pre + lat[x])
            if n in primary:
                t5[idx] = True
            if n in strict:
                s5[idx] = True
            idx += 1
    os.makedirs(CACHE, exist_ok=True)
    np.savez_compressed(path, t4=t4, t5=t5, s4=s4, s5=s5)
    return t4, t5, s4, s5


W4 = N29 ** np.arange(3, -1, -1)
W5 = N29 ** np.arange(4, -1, -1)
PRIME_TAB = np.array(lp.PRIME)


def isprime(n):
    return n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1))


PRIMEFLAG = np.array([isprime(n) for n in range(0, 700)])


def sets():
    ks, ps, _ = grid30.reconstruct()
    g = grid30.grid_values()
    seq16 = np.zeros(700, dtype=bool)
    seq48 = np.zeros(700, dtype=bool)
    for v in ps:
        if v < 700:
            seq16[v] = seq48[v] = True
    for v in list(g) + list(ks):
        if v < 700:
            seq48[v] = True
    return seq16, seq48


STATS = ["d2", "d2s", "d1", "sa16", "sb16", "sab16", "sa48", "sb48", "sab48", "pp"]


def score(P, tabs, seqs):
    t4, t5, s4, s5 = tabs
    seq16, seq48 = seqs
    i4 = P[:, :4] @ W4
    i5 = P[:, 4:] @ W5
    a, b = t4[i4], t5[i5]
    sa, sb = PRIME_TAB[P[:, :4]].sum(1), PRIME_TAB[P[:, 4:]].sum(1)
    f = {
        "d2": a & b, "d2s": s4[i4] & s5[i5], "d1": a | b,
        "sa16": seq16[sa], "sb16": seq16[sb], "sab16": seq16[sa] & seq16[sb],
        "sa48": seq48[sa], "sb48": seq48[sb], "sab48": seq48[sa] & seq48[sb],
        "pp": PRIMEFLAG[sa] & PRIMEFLAG[sb],
    }
    return f


def run_family(C, fam, tabs, seqs, collect=False):
    T = {s: np.zeros(len(C), dtype=np.int64) for s in STATS}
    hits = {s: [] for s in ("d2", "d2s", "sab16", "sab48", "pp")}
    outs = set()
    for m in fam:
        P = decrypt(C, m)
        f = score(P, tabs, seqs)
        for s in STATS:
            T[s] += f[s]
        if collect:
            for s in hits:
                if f[s][0]:
                    hits[s].append((describe(m), "".join(lp.LATIN[x] for x in P[0, :4]) + " " + "".join(lp.LATIN[x] for x in P[0, 4:])))
            outs.add(tuple(P[0]))
    return T, hits, len(outs)


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "count"
    fam = family()
    if cmd == "count":
        print("N decryptions (nominal, per 9-rune caption):", len(fam))
        return
    M = int(sys.argv[2]) if len(sys.argv) > 2 else 4000
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    tabs = build_tables()
    seqs = sets()
    print("tables", int(tabs[0].sum()), int(tabs[1].sum()), int(tabs[2].sum()), int(tabs[3].sum()), f"{time.time()-t0:.0f}s")
    S = grid30.S
    cap = np.array(lp.runes_of(S[10]), dtype=np.int64)[None, :]
    assert cap.shape == (1, 9) and list(cap[0]) == [0, 1, 20, 19, 24, 28, 26, 22, 24]
    res = {}
    T, hits, ndist = run_family(cap, fam, tabs, seqs, collect=True)
    res["observed"] = {s: int(T[s][0]) for s in STATS}
    print("N =", len(fam), "distinct outputs on the caption:", ndist)
    print("observed:", res["observed"])
    rng = np.random.default_rng(27)
    nulls = {}
    nulls["uniform"] = rng.integers(0, N29, (M, 9))
    uns = [i for i in range(7, 16) if i < len(S)]
    stream = np.concatenate([np.array(lp.runes_of(S[i])) for i in uns])
    st = rng.integers(0, len(stream) - 9, M)
    nulls["lp2_slices"] = np.stack([stream[i:i + 9] for i in st])
    capv = cap[0]
    nulls["caption_perm"] = np.stack([rng.permutation(capv) for _ in range(M)])
    out = {"observed": res["observed"], "N": len(fam), "distinct": ndist, "M": M}
    for name, C in nulls.items():
        t1 = time.time()
        Tn, _, _ = run_family(C, fam, tabs, seqs)
        out[name] = {}
        for s in STATS:
            v = Tn[s]
            obs = res["observed"][s]
            out[name][s] = dict(mean=float(v.mean()), p_ge=float((1 + (v >= obs).sum()) / (M + 1)),
                                p_any=float((v > 0).mean()), q99=float(np.quantile(v, 0.99)), max=int(v.max()))
        print(name, f"{time.time()-t1:.0f}s", {s: (round(out[name][s]['mean'], 2), out[name][s]['p_ge']) for s in STATS})
    # fraction of random 4-rune words with sum in the sets (exact)
    all4 = np.array(np.meshgrid(*[np.arange(N29)] * 4, indexing="ij")).reshape(4, -1).T
    sm = PRIME_TAB[all4].sum(1)
    out["sum_in_seq16"] = float(seqs[0][sm].mean())
    out["sum_in_seq48"] = float(seqs[1][sm].mean())
    out["sum_prime"] = float(PRIMEFLAG[sm].mean())
    out["sum_eq_149"] = float((sm == 149).mean())
    all5 = None
    out["hits"] = hits
    import json
    json.dump(out, open(os.path.join(OUT, "results.json"), "w"), indent=1)
    with open(os.path.join(OUT, "observed_hits.txt"), "w", encoding="utf-8") as f:
        for s, h in hits.items():
            f.write(f"== {s}: {len(h)}\n")
            for r in h:
                f.write(f"{r[1]}\t{r[0]}\n")
    # plant control
    t4, t5 = tabs[0], tabs[1]
    ok4, ok5 = np.flatnonzero(t4), np.flatnonzero(t5)
    found, tried, plants = 0, 0, []
    pr = np.random.default_rng(5)
    while tried < 300:
        i4, i5 = int(pr.choice(ok4)), int(pr.choice(ok5))
        pt = np.array([(i4 // 29 ** (3 - j)) % 29 for j in range(4)] + [(i5 // 29 ** (4 - j)) % 29 for j in range(5)])
        if (pt == 0).any():
            continue
        m = fam[int(pr.integers(0, len(fam)))]
        if m["key"] is None:
            kv = np.zeros(9, dtype=np.int64)
        else:
            kv = m["key"][(m["start"] + np.arange(9)) % len(m["key"])]
        s = m["sign"]
        base = (pt + s * (kv + m["b"])) % N29
        if m["atb"] == "pre":
            c = N29 - 1 - base
        elif m["atb"] == "post":
            c = (N29 - 1 - pt + s * (kv + m["b"])) % N29
        else:
            c = base
        if (c == 0).any():
            continue
        tried += 1
        assert (decrypt(c[None, :], m)[0] == pt).all(), describe(m)
        plants.append(c)
    Tp, _, _ = run_family(np.stack(plants), fam, tabs, seqs)
    found = int((Tp["d2"] >= 1).sum())
    print(f"plant control: {found}/{tried} planted two-word captions flagged d2 by the family")
    out["plants"] = [found, tried]
    json.dump(out, open(os.path.join(OUT, "results.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
