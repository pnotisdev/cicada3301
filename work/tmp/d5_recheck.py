"""aldegonde's within-word distance-d coincidence test, on our verified data with wrapped words rejoined."""
import sys
import numpy as np
sys.path.insert(0, '.')
import lp, stats
S = stats.SEGS
rng = np.random.default_rng(0)
segs = []
for i in stats.UNSOLVED:
    c = np.array(lp.runes_of(S[i]))
    wl = [b - a for _, a, b in lp.word_spans(S[i], lp.runes_of(S[i]))]
    segs.append((c, wl))
def within(c, wl, d):
    h = p = pos = 0
    for L in wl:
        if L > d:
            w = c[pos:pos + L]
            h += int((w[:-d] == w[d:]).sum()); p += L - d
        pos += L
    return h, p
for d in range(1, 9):
    obs = sum(within(c, wl, d)[0] for c, wl in segs); pairs = sum(within(c, wl, d)[1] for c, wl in segs)
    null = np.array([sum(within(c, list(rng.permutation(wl)), d)[0] for c, wl in segs) for _ in range(1000)])
    print(f"d={d}: {obs}/{pairs} = {100*obs/pairs:.2f}%  boundary-permutation null {null.mean():.1f} ± {null.std():.1f}  P(>=obs)={np.mean(null>=obs):.4f}", flush=True)
