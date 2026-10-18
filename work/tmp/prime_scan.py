"""Prime-space residual sweep -- audit: rune order / arithmetic domain (work/tmp/prime_scan.py).

Sweeps the within-word affine residual  r = (coord(c_{i+d}) - a*coord(c_i) - b) mod 29
in three coordinate domains:
    PP: coord = PRIME mod 29 for both runes      (prime -> prime)
    IP: coord(c') = PRIME[c'] mod 29, coord(c) = rune index   (index -> prime)
    PI: coord(c') = rune index,      coord(c) = PRIME[c] mod 29  (prime -> index)
chi2(a,b) is invariant under b (b just permutes the 29 bins), so the 841 (a,b)
settings per lag collapse to 29 distinct chi2 values (one per a). The null max is
therefore a max over 29*a-values per lag (8 lags -> 232 effective settings per domain).

Null: 200 within-section shuffles of the runes (same word cuts), same sweep.
Same-a z-scores (real chi2 vs the null distribution at the SAME a) cancel the marginal
structure that shuffles preserve, and isolate joint affine structure.

Positive control: plant prime(c_{i+6}) = (prime(c_i) + PRIME[p_{i+6}]) mod 29 in the
solved plaintext of sections 1, 5, 16, with uniform random heads at word positions 0..5
and lowest-index tie-breaking where PRIME mod 29 is not a bijection.
Real-data null: 'An End' ciphertext, section 16 (index 16, not 6).
"""
import json
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import lp

N = 29
P29 = [p % N for p in lp.PRIME]
SHUFFLES = 200
SEED = 0x13315C01
LAGS = (1, 2, 3, 4, 5, 6, 7, 8)
MIXED_LAGS = (5, 6)

T0 = time.time()
def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


# ---------------------------------------------------------------- machinery

def make_tmaps(domain):
    """Tmaps[a][x*29+y] = residual bin for (a, x, y) with x,y in 0..28.
    coords() already maps each rune into its domain coordinate (index or PRIME mod 29),
    so the residual table is always (y - a*x) regardless of domain."""
    return [[(y - a * x) % N for x in range(N) for y in range(N)] for a in range(N)]


def coords(runes, domain):
    if domain == "PP":
        return [P29[r] for r in runes], [P29[r] for r in runes]
    if domain == "IP":
        return runes, [P29[r] for r in runes]
    if domain == "PI":
        return [P29[r] for r in runes], runes
    raise ValueError(domain)


def make_positions(spans, lags):
    return {d: [(s + k, s + k + d) for s, e in spans for k in range(e - s - d)] for d in lags}


def lag_sweep(Xd, Yd, pos, Tmaps):
    """chi2 for every a in 0..28 from the joint (x,y) counts of the pairs in pos."""
    J = [0] * (N * N)
    Jl, Xl, Yl = J, Xd, Yd
    for i, j in pos:
        Jl[Xl[i] * N + Yl[j]] += 1
    n = len(pos)
    if n == 0:
        return None, 0
    e = n / N
    chis = {}
    for a in range(N):
        T = Tmaps[a]
        h = [0] * N
        for k in range(N * N):
            v = J[k]
            if v:
                h[T[k]] += v
        chis[a] = sum((c - e) * (c - e) for c in h) / e
    return chis, n


def chi2_for_a(Xd, Yd, pos, Tmaps, a):
    """chi2 at a single a (used by the confirmation pass)."""
    J = [0] * (N * N)
    for i, j in pos:
        J[Xd[i] * N + Yd[j]] += 1
    n = len(pos)
    if n == 0:
        return None
    e = n / N
    T = Tmaps[a]
    h = [0] * N
    for k in range(N * N):
        v = J[k]
        if v:
            h[T[k]] += v
    return sum((c - e) * (c - e) for c in h) / e


def confirm(base, bounds, pos, Tmaps, domain, lag, a, n_shuf=2000, seed=0xC0F1):
    """Fresh longer null at one (lag, a) setting: precise same-a z and empirical p."""
    Xb, Yb = coords(base, domain)
    real = chi2_for_a(Xb, Yb, pos, Tmaps, a)
    rng = random.Random(seed)
    vals = []
    for _ in range(n_shuf):
        arr = shuffle_dataset(base, bounds, rng)
        Xd, Yd = coords(arr, domain)
        vals.append(chi2_for_a(Xd, Yd, pos, Tmaps, a))
    mu = sum(vals) / len(vals)
    sd = math.sqrt(sum((x - mu) ** 2 for x in vals) / len(vals))
    z = (real - mu) / sd if sd > 0 else float("inf")
    p = (sum(1 for x in vals if x >= real) + 1) / (len(vals) + 1)
    return dict(lag=lag, a=a, real=real, null_mean=mu, null_sd=sd, null_max=max(vals),
                null_p99=sorted(vals)[int(math.ceil(0.99 * len(vals))) - 1],
                z=z, p=p, n_shuf=n_shuf)


def shuffle_dataset(base, bounds, rng):
    arr = base[:]
    for s, e in bounds:
        seg = arr[s:e]
        rng.shuffle(seg)
        arr[s:e] = seg
    return arr


def run_sweeps(base, bounds, pos_by_lag, Tmaps, domain, n_shuf=SHUFFLES, tag=""):
    """Real sweep + null (n_shuf within-section shuffles). Returns a result dict."""
    Xb, Yb = coords(base, domain)
    real = {}
    for d, pos in pos_by_lag.items():
        chis, n = lag_sweep(Xb, Yb, pos, Tmaps)
        if chis is None:
            real[d] = {"n": 0}
            continue
        best_a = max(chis, key=chis.get)
        top = sorted(((c, a) for a, c in chis.items()), reverse=True)[:3]
        real[d] = {"n": n, "best_a": best_a, "best_chi2": chis[best_a],
                   "top3": [(a, c) for c, a in top], "chis": chis}
    rng = random.Random(SEED)
    per_lag_max = {d: [] for d in pos_by_lag}
    per_a = {d: {a: [] for a in range(N)} for d in pos_by_lag}
    combined = []
    log(f"{tag}: null {n_shuf} shuffles x {len(pos_by_lag)} lags x 29 a")
    for k in range(n_shuf):
        arr = shuffle_dataset(base, bounds, rng)
        Xd, Yd = coords(arr, domain)
        best = -1.0
        for d, pos in pos_by_lag.items():
            chis, n = lag_sweep(Xd, Yd, pos, Tmaps)
            if chis is None:
                continue
            m = max(chis.values())
            per_lag_max[d].append(m)
            if m > best:
                best = m
            for a, c in chis.items():
                per_a[d][a].append(c)
        combined.append(best)
    null = {}
    for d in pos_by_lag:
        v = sorted(per_lag_max[d])
        if not v:
            null[d] = {"max": None, "mean": None, "p99": None, "n0": True}
            continue
        null[d] = {"max": v[-1], "mean": sum(v) / len(v),
                   "p99": v[int(math.ceil(0.99 * len(v))) - 1]}
    c = sorted(combined)
    null["combined"] = {"max": c[-1], "mean": sum(c) / len(c),
                        "p99": c[int(math.ceil(0.99 * len(c))) - 1]}
    # same-a z-scores and empirical p-values
    for d, info in real.items():
        if "chis" not in info:
            continue
        zs = []
        for a, chi in info["chis"].items():
            lst = per_a[d][a]
            mu = sum(lst) / len(lst)
            var = sum((x - mu) * (x - mu) for x in lst) / len(lst)
            sd = math.sqrt(var) if var > 0 else None
            z = (chi - mu) / sd if sd else None
            p = (sum(1 for x in lst if x >= chi) + 1) / (len(lst) + 1)
            zs.append((z if z is not None else float("inf"), a, chi, mu,
                       sd if sd is not None else 0.0, p))
        zs.sort(reverse=True)
        info["top_z"] = zs[0]
        info["z5"] = [(a, z, chi, p) for z, a, chi, _, _, p in zs[:5]]
    return {"real": real, "null": null}


# ---------------------------------------------------------------- datasets

def build_dataset(segs, idx_list):
    runs, spans, bounds = [], [], []
    off = 0
    for i in idx_list:
        toks = segs[i]
        rs = lp.runes_of(toks)
        for w, s, e in lp.word_spans(toks, rs):
            spans.append((off + s, off + e))
        runs += rs
        bounds.append((off, off + len(rs)))
        off += len(rs)
    return runs, spans, bounds


def build_plant(segs, idx=(1, 5, 16)):
    """Plant  prime(c_{i+6}) = (prime(c_i) + PRIME[p_{i+6}]) mod 29  within the words
    of the solved plaintext of the given sections (uniform random heads, positions 0..5)."""
    plain, spans, bounds = [], [], []
    off = 0
    for i in idx:
        toks = segs[i]
        rs = lp.runes_of(toks)
        p = lp.KNOWN[i][1](rs)
        assert len(p) == len(rs), (i, len(p), len(rs))
        plain += p
        for w, s, e in lp.word_spans(toks, rs):
            spans.append((off + s, off + e))
        bounds.append((off, off + len(rs)))
        off += len(rs)
    n = off
    R2R, ambcnt = {}, [0] * N
    for r in range(N):
        v = P29[r]
        if v not in R2R:
            R2R[v] = r
        ambcnt[v] += 1
    # PRIME mod 29 covers only 24 of the 29 residues ({4,6,26,27,28} are absent), so a
    # planted target residue may be UNREPRESENTABLE. Deterministic completion: nearest
    # representable residue (circular distance, lower residue on a tie), then the
    # lowest-index rune with that residue.
    AVAIL = sorted(set(P29))
    NEAREST = {}
    for v in range(N):
        best, bd = None, 99
        for u in AVAIL:
            dist = min((u - v) % N, (v - u) % N)
            if dist < bd or (dist == bd and (best is None or u < best)):
                best, bd = u, dist
        NEAREST[v] = best
    c = [None] * n
    rng = random.Random(0x99A55)
    planted = []
    for s, e in spans:
        for k in range(e - s):
            pos = s + k
            if k < 6:
                c[pos] = rng.randrange(N)
            else:
                v = (P29[c[pos - 6]] + P29[plain[pos]]) % N
                planted.append((pos, v, plain[pos]))
                c[pos] = R2R[NEAREST[v]]
    assert all(x is not None for x in c)
    # encoding-side information loss: target residue v maps to >1 rune, or to none
    enc_amb = sum(1 for _, v, _ in planted if v in R2R and ambcnt[v] > 1)
    unrep = sum(1 for _, v, _ in planted if v not in R2R)
    # decoding side: the sweep residual at (d=6, a=1) equals P29[plain[pos]] mod 29
    # exactly where the target was representable (else the nearest residue, an error).
    # It maps back to a unique rune iff that residue is unambiguous; match_clean must
    # equal dec_clean by construction (sanity check).
    residual_exact = sum(1 for _, v, _ in planted if NEAREST[v] == v)
    dec_clean = sum(1 for _, _, p in planted if ambcnt[P29[p]] == 1)
    match_clean = sum(1 for _, _, p in planted
                      if ambcnt[P29[p]] == 1 and R2R[P29[p]] == p)
    # exact plaintext-rune recovery from the sweep residual over ALL planted positions
    match_residual = 0
    for pos, v, p in planted:
        r = (NEAREST[v] - P29[c[pos - 6]]) % N
        if R2R.get(r) == p:
            match_residual += 1
    return c, spans, bounds, dict(
        runes=n, words=len(spans), planted=len(planted),
        enc_ambiguous=enc_amb, unrepresentable=unrep, representable=len(planted) - unrep,
        residual_exact=residual_exact,
        dec_clean=dec_clean, match_clean=match_clean, match_residual=match_residual)


# ---------------------------------------------------------------- run

def main():
    segs = lp.load_segments()
    log("segments loaded")

    # LP2 = sections 7..15
    lp2_runs, lp2_spans, lp2_bounds = build_dataset(segs, range(7, 16))
    log(f"LP2: runes={len(lp2_runs)} words={len(lp2_spans)} sections={len(lp2_bounds)}")
    pos_lp2 = make_positions(lp2_spans, LAGS)
    log("LP2 pairs per lag:", {d: len(v) for d, v in pos_lp2.items()})

    results = {}
    for domain, lags in (("PP", LAGS), ("IP", MIXED_LAGS), ("PI", MIXED_LAGS)):
        log(f"--- LP2 domain {domain} lags {lags} ---")
        results[f"lp2_{domain}"] = run_sweeps(
            lp2_runs, lp2_bounds, {d: pos_lp2[d] for d in lags},
            make_tmaps(domain), domain, tag=f"LP2/{domain}")
        rr = results[f"lp2_{domain}"]
        log(f"LP2/{domain} real max per lag:",
            {d: round(v['best_chi2'], 1) for d, v in rr["real"].items() if 'best_chi2' in v})
        for d, v in rr["real"].items():
            if "top_z" in v:
                z, a, chi, mu, sd, p = v["top_z"]
                log(f"  LP2/{domain} d={d} best-z: a={a} chi2={chi:.1f} "
                    f"null(mu={mu:.1f},sd={sd:.1f}) z={z:.2f} p={p:.4f}")

    # positive control: planted relation in solved plaintext of sections 1, 5, 16
    log("--- plant 1,5,16 (positive control, as specified) ---")
    plant, plant_spans, plant_bounds, plant_info = build_plant(segs)
    log("plant:", plant_info)
    pos_plant = make_positions(plant_spans, LAGS)
    results["plant"] = run_sweeps(plant, plant_bounds, pos_plant, make_tmaps("PP"),
                                  "PP", tag="plant/PP")
    results["plant"]["info"] = plant_info
    chis_d6 = results["plant"]["real"][6]["chis"]
    log(f"plant chi2 at (d=6, a=1): {chis_d6[1]:.1f}   (n={results['plant']['real'][6]['n']})")
    log(f"plant per-lag max:",
        {d: (v['best_a'], round(v['best_chi2'], 1)) for d, v in results['plant']['real'].items()
         if 'best_chi2' in v})
    log(f"plant top-z d=6: a={results['plant']['real'][6]['top_z'][1]} "
        f"z={results['plant']['real'][6]['top_z'][0]:.2f}")
    # chi2/n of the plaintext prime residues (power reference)
    plain_runs = []
    for i in (1, 5, 16):
        plain_runs += lp.KNOWN[i][1](lp.runes_of(segs[i]))
    from collections import Counter
    pc = Counter(P29[r] for r in plain_runs)
    pn = len(plain_runs)
    pchi = sum((v - pn / N) ** 2 for v in pc.values()) / (pn / N)
    results["plant"]["plaintext"] = dict(runes=pn, p29_chi2=pchi, p29_chi2_per_n=pchi / pn)

    # supplementary plant: all solved sections, same rule -> larger n power calibration
    log("--- plant ALL solved sections (supplementary power calibration) ---")
    pall, pall_spans, pall_bounds, pall_info = build_plant(segs, sorted(lp.KNOWN))
    log("plant_all:", pall_info)
    pos_pall = make_positions(pall_spans, LAGS)
    results["plant_all"] = run_sweeps(pall, pall_bounds, pos_pall, make_tmaps("PP"),
                                      "PP", tag="plant_all/PP")
    results["plant_all"]["info"] = pall_info
    log(f"plant_all chi2 at (d=6, a=1): {results['plant_all']['real'][6]['chis'][1]:.1f}")
    log(f"plant_all top-z d=6: a={results['plant_all']['real'][6]['top_z'][1]} "
        f"z={results['plant_all']['real'][6]['top_z'][0]:.2f}")

    # real-data null: 'An End' ciphertext, section 16
    log("--- An End (section 16 ciphertext) ---")
    anend_runs, anend_spans, anend_bounds = build_dataset(segs, [16])
    log(f"An End: runes={len(anend_runs)} words={len(anend_spans)}")
    pos_an = make_positions(anend_spans, LAGS)
    results["anend"] = run_sweeps(anend_runs, anend_bounds, pos_an, make_tmaps("PP"),
                                  "PP", tag="AnEnd/PP")

    # confirmation pass: fresh 2000-shuffle null at the best-z (lag, a) per LP2 domain
    log("--- confirmation pass (2000 fresh shuffles at best-z settings) ---")
    confirms = {}
    for domain, lags in (("PP", LAGS), ("IP", MIXED_LAGS), ("PI", MIXED_LAGS)):
        rr = results[f"lp2_{domain}"]["real"]
        cand = []
        for d, v in rr.items():
            if "top_z" in v:
                z, a, chi, mu, sd, p = v["top_z"]
                cand.append((z, d, a))
        cand.sort(reverse=True)
        for z, d, a in cand[:2]:
            key = f"lp2_{domain}_d{d}_a{a}"
            confirms[key] = confirm(lp2_runs, lp2_bounds, pos_lp2[d], make_tmaps(domain),
                                    domain, d, a)
            log(f"confirm {key}: real={confirms[key]['real']:.1f} "
                f"null(mu={confirms[key]['null_mean']:.1f}, sd={confirms[key]['null_sd']:.1f}, "
                f"max={confirms[key]['null_max']:.1f}) z={confirms[key]['z']:.2f} "
                f"p={confirms[key]['p']:.5f}")
    results["confirms"] = confirms

    with open(os.path.join(HERE, "prime_scan_results.json"), "w", encoding="utf-8") as f:
        json.dump(results, f, indent=1, default=float)
    log("wrote prime_scan_results.json")
    return results


if __name__ == "__main__":
    R = main()
