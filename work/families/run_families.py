"""Which cipher families can produce LP2's statistical fingerprint? Simulate each family on English plaintext with LP2's own section and word structure, compute the same
fingerprint (fam_fingerprint.py) on R replicates, and report, per statistic, whether the real LP2 lies inside the replicates (|z| <= 2.5).

Two segmentation readings: 'lp2' imposes LP2's word cuts on the English rune stream (the separators are not the plaintext's words), 'natural' keeps the English words
(the separators are the plaintext's word boundaries). Also: a nearest-centroid classifier on the fingerprints (can the fingerprint tell the families apart at all?), the
calibrated chance of the lag-5 statistics under a random text, and the size of a lag-5 echo the fingerprint can see.

    python work/families/run_families.py [--reps 60] [--seed 1]       # -> results/analysis/families.txt
"""
import argparse
import os
import sys

import numpy as np

import fam_data as D
import fam_fingerprint as F
import fam_sims as S

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = []
Z_OK = 2.5


def say(s=""):
    print(s)
    OUT.append(s)


def sd_of(x):
    return np.maximum(x.std(0), 0.01 * np.abs(x.mean(0)) + 0.02)


def wl_r1(start, sid):
    """lag-1 Pearson correlation of adjacent word lengths inside sections"""
    a, b = [], []
    for k in np.unique(sid):
        pos = np.flatnonzero(sid == k)
        w = np.diff(np.append(np.flatnonzero(start & (sid == k)), pos[-1] + 1))
        a += w[:-1].tolist(); b += w[1:].tolist()
    return float(np.corrcoef(a, b)[0, 1])


def simulate(name, fn, params, eng, seg, real, R, rng):
    runes, start, sid = real
    T = len(runes)
    sec_start = np.append(True, sid[1:] != sid[:-1])
    P, st = D.windows(eng, T, R, rng, seg == "natural", start, sec_start)
    C = fn(P, st, rng, **params)
    return F.many(C, st, sid)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=60)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args()
    rng = np.random.default_rng(a.seed)
    real = D.lp2()
    runes, start, sid = real
    eng = D.english()
    fp = F.fingerprint(runes, start, sid)
    rv = np.array([fp[k] for k in F.NAMES])
    say(f"LP2 (sections 0.7-0.15): {len(runes)} runes, {int(start.sum())} words; English plaintext: {len(eng[0])} runes from {len(D.CORPORA)} texts; {a.reps} replicates per row")
    say("real fingerprint: " + ", ".join(f"{k} {v:.3g}" for k, v in fp.items()))
    sec_start = np.append(True, sid[1:] != sid[:-1])
    P, st = D.windows(eng, len(runes), 20, rng, True, start, sec_start)
    r_nat = np.array([wl_r1(st[i], sid) for i in range(20)])
    say(f"word-length lag-1 correlation: LP2 {wl_r1(start, sid):+.3f}; English words in the same sections {r_nat.mean():+.3f} +- {r_nat.std():.3f} "
        f"(LP2 is {(wl_r1(start, sid) - r_nat.mean()) / r_nat.std():+.0f} sd from English words: the cuts of LP2 are not English word boundaries, so the 'lp2' reading below is the one to use)")
    results = {}
    for seg in ("lp2", "natural"):
        say("")
        say(f"== segmentation '{seg}': " + ("LP2's word cuts on the English rune stream" if seg == "lp2" else "English words as the cipher words"))
        say(f"{'family':26s}" + "".join(f"{k:>9s}" for k in F.NAMES) + "   reproduced")
        for name, fn, plist in S.FAMILIES:
            for label, params in plist:
                X = simulate(name, fn, params, eng, seg, real, a.reps, rng)
                results[(seg, name, label)] = X
                z = (rv - X.mean(0)) / sd_of(X)
                ok = np.abs(z) <= Z_OK
                say(f"{(name + ' ' + label).strip():26s}" + "".join(f"{m:>8.3g}{' ' if o else '*'}" for m, o in zip(X.mean(0), ok))
                    + f"   {int(ok.sum())}/{len(ok)}" + ("" if ok.all() else "  (* = real LP2 outside: " + ", ".join(f"{k} z{zz:+.1f}" for k, zz, o in zip(F.NAMES, z, ok) if not o) + ")"))
    # ---- classifier: can the fingerprint tell the rows apart? (first half of the replicates trains, second half tests)
    say("")
    say("== nearest-centroid classification of simulated replicates by their fingerprint (segmentation lp2; train on half, test on the other half)")
    keys = [k for k in results if k[0] == "lp2"]
    mats = {k: results[k] for k in keys}
    sd = np.sqrt(np.mean([m.var(0) for m in mats.values()], axis=0)) + 1e-9
    h = a.reps // 2
    cent = {k: m[:h].mean(0) / sd for k, m in mats.items()}
    names = list(cent)
    C = np.array([cent[k] for k in names])
    conf = {}
    for k, m in mats.items():
        pred = [names[int(np.argmin(((C - x / sd) ** 2).sum(1)))] for x in m[h:]]
        conf[k] = pred
    acc = {k: np.mean([p == k for p in v]) for k, v in conf.items()}
    say(f"overall accuracy {np.mean(list(acc.values())):.2f} over {len(names)} rows; rows below 0.7: " +
        "; ".join(f"{(k[1] + ' ' + k[2]).strip()} {v:.2f} (mistaken for {max(set(conf[k]), key=conf[k].count)[1:]})" for k, v in acc.items() if v < 0.7))
    # where is the real LP2?
    dist = {k: float((((rv / sd) - cent[k]) ** 2).sum()) for k in names}
    best = sorted(dist, key=dist.get)[:5]
    say("real LP2, nearest rows (squared standardised distance): " + "; ".join(f"{(k[1] + ' ' + k[2]).strip()} {dist[k]:.1f}" for k in best))
    # ---- calibration of the lag-5 statistics under a random text, and the size of echo the fingerprint can see
    rng2 = np.random.default_rng(a.seed + 1)
    big = np.array([[F.fingerprint(S.random_(np.zeros((1, len(runes)), int), None, rng2)[0], start, sid)[k] for k in ("z5", "maxz5")] for _ in range(1500)])
    say("")
    say(f"random text, 1500 draws with LP2's word structure: P(z5 >= {fp['z5']:.2f}) = {(big[:, 0] >= fp['z5']).mean():.4f}; P(maxz5 >= {fp['maxz5']:.2f}) = {(big[:, 1] >= fp['maxz5']).mean():.4f};"
        f" P(both) = {((big[:, 0] >= fp['z5']) & (big[:, 1] >= fp['maxz5'])).mean():.4f}")
    perm = []
    for _ in range(1500):                                           # LP2's own runes shuffled inside each section: keeps rune frequencies and word structure
        Cp = runes.copy()
        for k in np.unique(sid):
            m = sid == k
            Cp[m] = rng2.permutation(Cp[m])
        f2 = F.fingerprint(Cp, start, sid)
        perm.append((f2["z5"], f2["maxz5"]))
    perm = np.array(perm)
    say(f"LP2's runes shuffled inside sections, 1500 draws: P(z5 >= {fp['z5']:.2f}) = {(perm[:, 0] >= fp['z5']).mean():.4f}; P(maxz5 >= {fp['maxz5']:.2f}) = {(perm[:, 1] >= fp['maxz5']).mean():.4f};"
        f" P(both) = {((perm[:, 0] >= fp['z5']) & (perm[:, 1] >= fp['maxz5'])).mean():.4f}")
    for eps in (0.005, 0.015, 0.03):
        X = results[("lp2", "echo", f"q=0.81,eps={eps}")]
        say(f"lag-5 copy probability {eps}: z5 mean {X[:, 3].mean():+.1f} (sd {X[:, 3].std():.1f}); share of replicates with z5 >= 3: {(X[:, 3] >= 3).mean():.2f}")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    os.makedirs(dest, exist_ok=True)
    with open(os.path.join(dest, "families.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    sys.exit(main())
