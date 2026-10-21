import sys, time, random
import numpy as np
sys.path.insert(0, "work/mech48"); sys.path.insert(0, "work")
from oracle_screen import *
segs, W = windows()
lib = load_ksb("work/kscreen/data/library.ksb")
long = [(n, k) for n, k in lib if len(k) >= 19000]
print("library streams", len(lib), "with >=19000 values", len(long))
rng = random.Random(4802)
def plain_of(ids):
    p, one = [], []
    for i in ids:
        c = lp.runes_of(segs[i]); q = lp.KNOWN[i][1](c)
        for w, a, b in lp.word_spans(segs[i], q):
            if b - a == 1: one.append(len(p) + a)
        p += list(q)
    isone = np.zeros(len(p), dtype=np.int64); isone[one] = 1
    return np.array(p, dtype=np.int64), isone
# timing
c, io = W[15]; key = long[0][1].astype(np.int64)
oracle_max(c, io, key, 100, 64, 10**9)           # compile
t = time.perf_counter(); R = 200
for _ in range(R): oracle_max(c, io, key, rng.randrange(0, 15000), 64, 10**9)
print("seg0.15 (%d runes, %d one-rune words): %.2f ms per stream-offset, full window" % (len(c), io.sum(), (time.perf_counter()-t)/R*1e3))
t = time.perf_counter()
for _ in range(R): oracle_max(c, io, key, rng.randrange(0, 15000), 64, 300)
print("first 300 runes: %.3f ms per stream-offset" % ((time.perf_counter()-t)/R*1e3))
# planted control + null
for label, ids in (("0.3 plaintext (13 one-rune words)", [3]), ("0.3+0.5+0.1 plaintext (25 one-rune words)", [3, 5, 1])):
    p, io = plain_of(ids); n1 = int(io.sum())
    res = {"planted": [], "off+1": [], "null": []}
    for trial in range(40):
        name, k = long[rng.randrange(len(long))]; key = k.astype(np.int64); off = rng.randrange(0, 15000)
        c = encrypt(p, key, off)
        res["planted"].append(oracle_max(c, io, key, off, 64, 10**9)[0] / n1)
        res["off+1"].append(oracle_max(c, io, key, off + 1, 64, 10**9)[0] / n1)
        for _ in range(25): res["null"].append(oracle_max(c, io, key, rng.randrange(0, 15000), 64, 10**9)[0] / n1)
    nl = np.array(res["null"]); thr = np.quantile(nl, 0.999)
    print(label, "| null mean %.4f sd %.4f q99.9 %.3f max %.3f (n=%d)" % (nl.mean(), nl.std(), thr, nl.max(), len(nl)))
    print("   planted: mean %.3f min %.3f; power(>q99.9) %.2f; true-offset+1 mean %.3f" % (np.mean(res["planted"]), np.min(res["planted"]), np.mean(np.array(res["planted"]) > thr), np.mean(res["off+1"])))
