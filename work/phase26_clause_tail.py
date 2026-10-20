"""Phase 26 addendum: tail of the single-clause contribution to the Welcome x man/master residual dot (null: koan lengths shuffled)."""
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp, phase26_words as pw
segs = lp.load_segments()
W = np.array([len(w) for w in pw.seg_words(segs, 1)], float)
K = np.array([len(w) for w in pw.seg_words(segs, 3)], float)
colW = (45 + np.arange(len(W))) % 16
colK = (169 + np.arange(len(K))) % 16
Wr = np.bincount(colW, W, 16) - np.bincount(colW, minlength=16) * W.mean()
sizes = [2,10,8,11,7,13,11,12,12,8,6,8,9,12,16,10,8,5,18,14,2,6]
b = np.cumsum([0] + sizes)
rng = np.random.default_rng(5)
def clauses(k):
    c = (k - k.mean()) * Wr[colK]
    return np.array([c[b[i]:b[i+1]].sum() for i in range(22)])
obs = clauses(K)
mx = np.array([np.abs(clauses(rng.permutation(K))).max() for _ in range(100000)])
c14 = np.array([clauses(rng.permutation(K))[14] for _ in range(100000)])
print("observed clause contributions: min", obs.min().round(1), "idx", obs.argmin(), "; sd of clause 14 under null", c14.std().round(1))
print("P(clause 14 contribution <= -187.9, pre-chosen) =", (c14 <= obs[14]).mean())
print("P(max |contribution| over 22 clauses >= 187.9) =", (mx >= abs(obs[14])).mean())
print("Welcome residual vector sd", Wr.std().round(2))

# sliding 16-word windows (every start inside the koan): this removes the "chosen among 22 clauses" freedom
def win(k):
    c = (k - k.mean()) * Wr[colK]
    cs = np.concatenate([[0], np.cumsum(c)])
    return cs[16:] - cs[:-16]
wo = win(K)
print("real koan: 193 sliding 16-word windows, min", wo.min().round(1), "at word", int(wo.argmin()) + 170, "; windows <= -150:", int((wo <= -150).sum()))
mn = np.array([win(rng.permutation(K)).min() for _ in range(100000)])
print("P(min over 193 windows <= %.1f) under shuffled koan = %.5f" % (wo.min(), (mn <= wo.min()).mean()))
# also shuffle with the Welcome column pattern re-randomised (Welcome lengths shuffled too, i.e. no structure at all)
W0 = W.copy()
def Wres(w):
    return np.bincount(colW, w, 16) - np.bincount(colW, minlength=16) * w.mean()
mn2 = []
for _ in range(20000):
    Wr_ = Wres(rng.permutation(W0)); k = rng.permutation(K)
    c = (k - k.mean()) * Wr_[colK]; cs = np.concatenate([[0], np.cumsum(c)])
    mn2.append((cs[16:] - cs[:-16]).min())
mn2 = np.array(mn2)
print("both Welcome and koan shuffled: P(min over 193 windows <= %.1f) = %.5f" % (wo.min(), (mn2 <= wo.min()).mean()))

# structure-preserving null: keep the koan's own word order, change only which column it starts in (16 offsets)
print("koan start-column offset -> (min sliding-window dot, net dot, R of the 464 table with the koan shifted)")
for o in range(16):
    ck = (o + np.arange(len(K))) % 16
    c = (K - K.mean()) * Wr[ck]; cs = np.concatenate([[0], np.cumsum(c)])
    print(o, round((cs[16:] - cs[:-16]).min(), 1), round(c.sum(), 1), "<- real" if o == 169 % 16 else "")
