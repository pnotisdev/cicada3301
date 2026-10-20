"""Phase 25, part 2: (a) the repair budget: excess hits per eligible pair for lag 6 and lag 5 against the collision rate, for M2 at several splits a;
(b) a prediction of M1 (collision repair T(c_(i-6))) that was not measured on LP2: the lag-6 hits are independent Bernoulli over the eligible
positions, so multi-hit words and hits at consecutive positions follow the shuffle-null count plus ONE rate, nothing more.  Measured on LP2,
on M1 plants (the mechanism's own spread) and on shuffled LP2 (no echo).

    python work/mech25/fit_and_predict.py [--reps 60]   -> results/analysis/mech25_fit.txt
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "families"))
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402
import sim25 as S  # noqa: E402


def hits6(c, start, sid):
    """boolean hit vector for within-word lag-6 pairs (indexed by the later rune)"""
    wid, _ = M.wordinfo(start)
    h = np.zeros(len(c), bool)
    i = np.arange(6, len(c))
    ok = (sid[i] == sid[i - 6]) & (wid[i] == wid[i - 6])
    h[i] = ok & (c[i] == M.T6[c[i - 6]])
    return h, wid


def multi(c, start, sid):
    h, wid = hits6(c, start, sid)
    cnt = np.bincount(wid[h], minlength=wid.max() + 1)
    adj = int((h[1:] & h[:-1]).sum())
    return int((cnt >= 2).sum()), adj, int(h.sum())


def shuffled(c, sid, rng):
    c = c.copy()
    for k in np.unique(sid):
        m = sid == k
        c[m] = rng.permutation(c[m])
    return c


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=60)
    args = ap.parse_args()
    out = []

    def say(x=""):
        print(x, flush=True); out.append(x)

    ref, (c, start, sid) = M.lp2_stats()
    n = len(c)
    rng = np.random.default_rng(2511)
    P0, st0 = S.english(False)
    say("(a) repair budget. LP2: lag 6 excess/pair %.4f (%d pairs), lag 5 excess/pair %.4f (%d pairs); collision budget q/29 = %.4f"
        % ((ref["l6_in"][1] - ref["l6_in"][2]) / ref["l6_in"][0], ref["l6_in"][0], (ref["l5_in"][1] - ref["l5_in"][2]) / ref["l5_in"][0], ref["l5_in"][0], 0.81 / 29))
    say("M2 split a (share of repairs writing T(c-6); the rest copy c-5), digraph plaintext, mean +- sd over replicates:")
    for a in (1.0, 0.9, 0.8, 0.7, 0.5):
        r6, r5 = [], []
        for _ in range(args.reps):
            s0 = int(rng.integers(0, len(P0) - n - 5000)); s0 += int(np.flatnonzero(st0[s0:])[0])
            cc, ss, sd = S.run("M2", P0[s0:s0 + n + 5000], st0[s0:s0 + n + 5000], sid, rng, a=a)
            st = M.all_stats(cc, ss, sd)
            r6.append((st["l6_in"][1] - st["l6_in"][2]) / st["l6_in"][0]); r5.append((st["l5_in"][1] - st["l5_in"][2]) / st["l5_in"][0])
        say(f"  a={a:.1f}: lag6 excess/pair {np.mean(r6):.4f} +- {np.std(r6):.4f}   lag5 excess/pair {np.mean(r5):.4f} +- {np.std(r5):.4f}")
    say("")
    say("(b) prediction: lag-6 hits are independent over eligible positions. Statistics: words with >= 2 hits, hits at consecutive positions (i, i+1), total hits")
    m_lp = multi(c, start, sid)
    say(f"  LP2: words>=2 hits {m_lp[0]}, consecutive {m_lp[1]}, hits {m_lp[2]}")
    sh = np.array([multi(shuffled(c, sid, rng), start, sid) for _ in range(300)])
    say(f"  shuffled LP2 (300, no echo):   words>=2 {sh[:, 0].mean():.2f} +- {sh[:, 0].std():.2f}, consecutive {sh[:, 1].mean():.2f} +- {sh[:, 1].std():.2f}, hits {sh[:, 2].mean():.1f}")
    pl = []
    for _ in range(args.reps * 3):
        s0 = int(rng.integers(0, len(P0) - n - 5000)); s0 += int(np.flatnonzero(st0[s0:])[0])
        cc, ss, sd = S.run("M1", P0[s0:s0 + n + 5000], st0[s0:s0 + n + 5000], sid, rng)
        pl.append(multi(cc, ss, sd))
    pl = np.array(pl)
    say(f"  M1 plants ({len(pl)}):           words>=2 {pl[:, 0].mean():.2f} +- {pl[:, 0].std():.2f}, consecutive {pl[:, 1].mean():.2f} +- {pl[:, 1].std():.2f}, hits {pl[:, 2].mean():.1f}")
    # rate-matched: M1 plants with similar hit totals
    k = np.abs(pl[:, 2] - m_lp[2]) <= 12
    if k.sum() > 5:
        say(f"  M1 plants with hits within 12 of LP2's ({int(k.sum())}): words>=2 {pl[k, 0].mean():.2f} +- {pl[k, 0].std():.2f}")
    say(f"  P(M1 words>=2 >= LP2) = {(pl[:, 0] >= m_lp[0]).mean():.3f}; P(M1 words>=2 <= LP2) = {(pl[:, 0] <= m_lp[0]).mean():.3f};  consecutive: P(>=) = {(pl[:, 1] >= m_lp[1]).mean():.3f}")
    with open(os.path.join(HERE, "..", "..", "results", "analysis", "mech25_fit.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
