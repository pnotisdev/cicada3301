"""s13 (R4 repair, round 2): are LP2's lag-6 T sites repairs?  Items 19-23 of work/laptop_review/11_next_100.md.  Keyless.

T(c) = 24 - 2c (mod 29).  A "T site" is an in-word pair (j-6, j) with c_j = T(c_(j-6)); LP2 has 80.
    21  how often is c_j == c_(j-1) at a T site                    (a repair never writes a doublet)
    22  is the source rune c_(j-6) uniform over the 29 values
    23  position of the T site counted from the word end
    19/20  the T grid: rune-lag 1-12 x 0-4 word gaps on LP2 and on R0/R1/R3/R4/R7 replicates, max over 812 affine forms per lag,
           plus a planted gap-crossing look-back (weight 0.26, positions 0-4, rune 5 back) as the positive control.

Only LP2's own runes (layout, statistics) and simulations (work/r4fix/r4sim.py, imported read-only) are used; nothing is decrypted.

    python -B work/r4fix/s13_tsites.py selftest                       gates (plant with w=0 == r4sim bit for bit, statistic checks)
    python -B work/r4fix/s13_tsites.py lp2   [--shuf 2000 --wshuf 300] LP2 + within-word / word-order shuffles
    python -B work/r4fix/s13_tsites.py sim <preset> [--reps 200 --workers 2]
    python -B work/r4fix/s13_tsites.py summary                         -> results/r4fix/s13_tsites/summary.txt
"""
import argparse
import json
import math
import os
import random
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "work"))
sys.path.insert(0, os.path.join(ROOT, "work", "families"))
import r4sim as S  # noqa: E402

OUT = os.path.join(ROOT, "results", "r4fix", "s13_tsites")
N = 29
LAG = 6
GMAX, KMAX = 12, 4
TARR = np.array([(24 - 2 * c) % N for c in range(N)])
# affine forms c' = a c + b (a in 1..28, b in 0..28): 812
AFF = [(a, b) for a in range(1, N) for b in range(N)]
AIDX = np.array([[(a * c + b) % N for c in range(N)] for a, b in AFF])        # (812, 29)
T_FORM = AFF.index((27, 24))                                                  # -2 = 27
DMAX = 6                                                                       # distance from word end: 0..4, 5+

# presets: r4sim.encrypt_r4 keyword settings (phase 57 table; nu = 0.448 is phase 57's tuned null rate)
PRESETS = {
    "R0":    dict(q=0.81, repair="uniform", nu=0.0),                                       # no echo, no nulls (phase 57 R0)
    "R0n":   dict(q=0.81, repair="uniform", nu=0.448, slots="any"),                         # no echo, nulls kept (word-length mix of R4)
    "R1":    dict(q=0.81, repair="T", nu=0.0),                                              # echo, no nulls (phase 57 R1)
    "R4":    dict(q=0.81, repair="T", nu=0.448, slots="any", null_check="left", null_visible=True),
    "R4int": dict(q=0.81, repair="T", nu=0.448, slots="interior", null_check="left", null_visible=True),
    "R3":    dict(q=1.0, repair="T", nu=0.448, slots="any", null_check="none", null_visible=False, lag_basis="real"),
    "R7":    dict(q=0.81, repair="T", nu=0.448, slots="end", null_check="left", null_visible=True),
    "plant": dict(q=0.81, repair="T", nu=0.448, slots="any", null_check="left", null_visible=True, w_cross=0.26),
}
PRESET_SEED = {k: 13_000_000 + 100_000 * i for i, k in enumerate(PRESETS)}


# ---------------------------------------------------------------------------------------------------------------- data
def lp2():
    import fam_data as D
    c, ws, sid = D.lp2()
    assert len(c) == 12956
    return c.astype(np.int64), ws.astype(bool), sid.astype(np.int64)


def english_length_hist():
    """pooled English word-length histogram (lengths 1..) from the project's corpora, for the plaintext word lengths"""
    import fam_data as D
    P, ST = D.english(150_000)
    s = np.flatnonzero(ST)
    L = np.diff(np.append(s, len(ST)))
    return np.bincount(L)


# -------------------------------------------------------------------------------- planted gap-crossing look-back control
def encrypt_r4_plant_full(plain_words, key, rng, w_cross, cross_lag=5, cross_max_pos=4, q=0.81, nu=0.45, slots="any",
                          null_check="left", null_visible=True, lag_basis="cipher", channel="hold", lag=6, min_word=2, repair="T",
                          n_cipher=None, T=S.T_MAP):
    """copy of r4sim.encrypt_r4 (default semantics: nulls_per_word (1.0,), sign +1, key_start 0) with the cross-gap rule added.
    Returns (cipher, word_start, is_null, is_repair, repair_is_T, cross_flag) numpy arrays."""
    R = S._Rng(rng)
    words = [list(w) for w in plain_words]
    key = np.asarray(key)
    out, isnull, isrep, repT, wst, crossf, realv = [], [], [], [], [], [], []
    st = dict(j=0, lastreal=None, done=False)

    def draw_slot(L):
        if slots == "any":
            return R.below(L + 1)
        if slots == "interior":
            return 1 + R.below(L - 1)
        if slots == "edge":
            return 0 if R.rand() < 0.5 else L
        return 0 if slots == "start" else L

    def uniform_excl(excl):
        while True:
            v = R.below(N)
            if v not in excl:
                return v

    def append(x, null, first, rep=False, rT=False, cr=False):
        out.append(int(x)); isnull.append(null); isrep.append(rep); repT.append(rT); wst.append(first); crossf.append(cr)
        if not null:
            st["lastreal"] = int(x)
            realv.append(int(x))
        if n_cipher is not None and len(out) >= n_cipher:
            st["done"] = True

    for wi, w in enumerate(words):
        L = len(w)
        if L == 0 or st["done"]:
            continue
        sched = []
        if L >= min_word and R.rand() < nu:
            u, k, acc = R.rand(), 1, 0.0
            sched = sorted(draw_slot(L) for _ in range(k))
        w0, wreal = len(out), 0
        sp = 0
        for s in range(L + 1):
            while sp < len(sched) and sched[sp] == s and not st["done"]:
                sp += 1
                excl = set()
                if null_check in ("left", "both") and out:
                    excl.add(out[-1])
                m = len(out)
                append(uniform_excl(excl), True, m == w0)
            if st["done"]:
                break
            if s == L:
                break
            j = st["j"]
            p = int(w[s])
            x = (p + int(key[j])) % N
            prev = out[-1] if (null_visible and out) else (st["lastreal"] if not null_visible else None)
            rep = rT = cr = False
            if prev is not None and x == prev and R.rand() < q:
                rep = True
                src = None
                if repair == "T":
                    if lag_basis == "cipher":
                        if len(out) - w0 >= lag:
                            src = out[-lag]
                    elif wreal >= lag:
                        src = realv[-lag]
                    if src is not None:
                        tv = T(src)
                        if tv != prev:
                            x, rT = tv, True
                    elif w_cross > 0 and (len(out) - w0 <= cross_max_pos) and len(out) >= cross_lag and R.rand() < w_cross:
                        tv = T(out[-cross_lag])
                        if tv != prev:
                            x, cr = tv, True
                if not rT and not cr:
                    r = R.below(N - 1)
                    x = r + 1 if r >= prev else r
                st["j"] = j + (1 if channel == "spend" else 0)
            else:
                st["j"] = j + 1
            m = len(out)
            append(x, False, m == w0, rep=rep, rT=rT, cr=cr)
            wreal += 1
            if st["done"]:
                break
    return (np.array(out, np.int16), np.array(wst, bool), np.array(isnull, bool), np.array(isrep, bool), np.array(repT, bool),
            np.array(crossf, bool))


# ------------------------------------------------------------------------------------------------------- replicate maker
def make_replicate(preset, seed, sec_len, lenhist):
    """one simulated LP2: per section an independent encrypt_r4 call cut at LP2's section length; uniform iid plaintext runes with
    English word lengths, iid uniform key (a flat key makes the cipher flat whatever the plaintext).  Returns
    c, ws, sid, repT(flag aligned with c), crossflag, isnull"""
    cfg = dict(PRESETS[preset])
    w_cross = cfg.pop("w_cross", None)
    rng = random.Random(seed)
    lens = np.arange(len(lenhist))
    pr = lenhist / lenhist.sum()
    cs, wss, sids, rts, crs, nls = [], [], [], [], [], []
    for k, n in enumerate(sec_len):
        nw = int(n * 0.6) + 50
        Ls = np.random.default_rng(rng.randrange(1 << 62)).choice(lens, size=nw, p=pr)
        Ls = Ls[Ls > 0]
        while Ls.sum() < n + 5:
            Ls = np.concatenate([Ls, Ls])
        words = [[rng.randrange(N) for _ in range(int(L))] for L in Ls]
        key = [rng.randrange(N) for _ in range(int(Ls.sum()) + 5)]
        if w_cross is None:
            res = S.encrypt_r4(words, key, rng, n_cipher=int(n), **cfg)
            c, ws, rt, isn = res.cipher, res.word_start, res.repair_is_T, res.is_null
            cr = np.zeros(len(c), bool)
        else:
            c, ws, isn, isrep, rt, cr = encrypt_r4_plant_full(words, key, rng, w_cross, n_cipher=int(n), **cfg)
        assert len(c) == n, (len(c), n)
        cs.append(c.astype(np.int64)); wss.append(ws); sids.append(np.full(n, k)); rts.append(rt); crs.append(cr); nls.append(isn)
    return (np.concatenate(cs), np.concatenate(wss), np.concatenate(sids), np.concatenate(rts), np.concatenate(crs),
            np.concatenate(nls))


# ---------------------------------------------------------------------------------------------------------- statistics
def layout(ws, sid):
    n = len(ws)
    widx = np.cumsum(ws) - 1
    wstart_pos = np.flatnonzero(ws)
    pos = np.arange(n) - wstart_pos[widx]
    wlen = np.diff(np.append(wstart_pos, n))[widx]
    # a word never spans a section (each section starts a word)
    return widx, pos, wlen


def grid_stats(c, ws, sid):
    """T grid and affine maxima.  Cell (g, k), g = rune lag 1..12, k = number of word gaps crossed 0..4 (same section):
    hits, expectation sum f[T(c_i)], variance sum p(1-p), pair count.  maxz[g] over the 812 affine forms for in-word pairs."""
    n = len(c)
    f = np.bincount(c, minlength=N) / n
    widx, pos, wlen = layout(ws, sid)
    H = np.zeros((GMAX + 1, KMAX + 1)); E = np.zeros_like(H); V = np.zeros_like(H); NP = np.zeros_like(H)
    maxz = np.zeros(GMAX + 1); maxform = np.zeros(GMAX + 1, int); tz = np.zeros(GMAX + 1); thits = np.zeros(GMAX + 1)
    for g in range(1, GMAX + 1):
        i = np.arange(n - g)
        ok = sid[i] == sid[i + g]
        i = i[ok]
        k = widx[i + g] - widx[i]
        sel = k <= KMAX
        i, k = i[sel], k[sel]
        p = f[TARR[c[i]]]
        hit = (c[i + g] == TARR[c[i]])
        H[g] = np.bincount(k, weights=hit, minlength=KMAX + 1)
        E[g] = np.bincount(k, weights=p, minlength=KMAX + 1)
        V[g] = np.bincount(k, weights=p * (1 - p), minlength=KMAX + 1)
        NP[g] = np.bincount(k, minlength=KMAX + 1)
        # affine forms, in-word pairs
        i0 = i[k == 0]
        M = np.bincount(c[i0] * N + c[i0 + g], minlength=N * N).reshape(N, N)
        rows = M.sum(1)
        hits = M[np.arange(N)[None, :], AIDX].sum(1)
        pe = f[AIDX]                                                     # (812, 29)
        Ef = (pe * rows[None, :]).sum(1)
        Vf = (pe * (1 - pe) * rows[None, :]).sum(1)
        zf = (hits - Ef) / np.sqrt(np.maximum(Vf, 1e-9))
        a = int(np.argmax(zf))
        maxz[g] = zf[a]; maxform[g] = a
        tz[g] = zf[T_FORM]; thits[g] = hits[T_FORM]
    return dict(H=H, E=E, V=V, NP=NP, maxz=maxz, maxform=maxform, tz=tz)


def tsite_stats(c, ws, sid, repT=None):
    """items 21-23 on the in-word lag-6 T sites"""
    n = len(c)
    widx, pos, wlen = layout(ws, sid)
    d = wlen - 1 - pos                                                  # distance from word end (0 = last rune)
    j = np.flatnonzero(pos >= LAG)
    hit = c[j] == TARR[c[j - LAG]]
    sj = j[hit]
    f = np.bincount(c, minlength=N) / n
    dbl = c[sj] == c[sj - 1]
    src = c[sj - LAG]
    out = dict(n_pairs=int(len(j)), n_sites=int(len(sj)), n_dbl=int(dbl.sum()))
    out["src_counts"] = np.bincount(src, minlength=N).tolist()
    # chance expectation of the source distribution given the pair multiset: sum over pairs of f[T(c_src)]
    srcall = c[j - LAG]
    out["src_exp"] = np.bincount(srcall, weights=f[TARR[srcall]], minlength=N).tolist()
    out["d_counts"] = np.bincount(np.minimum(d[sj], DMAX - 1), minlength=DMAX).tolist()
    out["d_pairs"] = np.bincount(np.minimum(d[j], DMAX - 1), minlength=DMAX).tolist()
    out["d_exp"] = np.bincount(np.minimum(d[j], DMAX - 1), weights=f[TARR[srcall]], minlength=DMAX).tolist()
    # doublet rate among ALL in-word pairs at word position >= 6 (the depleted chance level for a doublet at a T site)
    dall = c[j] == c[j - 1]
    out["dbl_rate_pos6"] = float(dall.mean()) if len(j) else 0.0
    out["n_dbl_pos6"] = int(dall.sum())
    # all in-word adjacent doublets and across gaps (sanity: LP2 63 / 23)
    adj = (c[1:] == c[:-1]) & (sid[1:] == sid[:-1])
    inw = ~ws[1:]
    out["dbl_in"] = int((adj & inw).sum()); out["dbl_gap"] = int((adj & ~inw).sum())
    if repT is not None:
        isrep = repT[sj]
        out["n_true_repair_sites"] = int(isrep.sum())
        out["n_dbl_true_repair"] = int((dbl & isrep).sum())
        out["n_dbl_chance"] = int((dbl & ~isrep).sum())
        out["d_counts_repair"] = np.bincount(np.minimum(d[sj[isrep]], DMAX - 1), minlength=DMAX).tolist()
        out["d_counts_chance"] = np.bincount(np.minimum(d[sj[~isrep]], DMAX - 1), minlength=DMAX).tolist()
    out["n_words"] = int(ws.sum())
    return out


def src_chi2(counts):
    cnt = np.asarray(counts, float)
    n = cnt.sum()
    if n == 0:
        return 0.0
    return float(((cnt - n / N) ** 2).sum() / (n / N))


def analyse(c, ws, sid, repT=None, cross=None):
    g = grid_stats(c, ws, sid)
    t = tsite_stats(c, ws, sid, repT)
    t["src_chi2"] = src_chi2(t["src_counts"])
    t["src_max"] = int(max(t["src_counts"])); t["src_distinct"] = int(sum(1 for x in t["src_counts"] if x > 0))
    t["src_sumsq"] = int(sum(x * x for x in t["src_counts"]))
    return g, t


def pack(g, t):
    return dict(H=g["H"].tolist(), E=g["E"].tolist(), V=g["V"].tolist(), NP=g["NP"].tolist(), maxz=g["maxz"].tolist(),
                maxform=g["maxform"].tolist(), tz=g["tz"].tolist(), t=t)


# ------------------------------------------------------------------------------------------------------ shuffles on LP2
def within_word_shuffle(c, ws, rng):
    widx = np.cumsum(ws) - 1
    order = np.lexsort((rng.random(len(c)), widx))
    return c[order]


def word_order_shuffle(c, ws, sid, rng):
    out = np.empty_like(c); ws2 = np.zeros_like(ws)
    for s in np.unique(sid):
        idx = np.flatnonzero(sid == s)
        cc, ww = c[idx], ws[idx]
        st = np.flatnonzero(ww)
        ln = np.diff(np.append(st, len(cc)))
        perm = rng.permutation(len(st))
        lp_, sp_ = ln[perm], st[perm]
        offs = np.cumsum(lp_) - lp_
        gi = np.repeat(sp_ - offs, lp_) + np.arange(len(cc))
        out[idx] = cc[gi]
        w2 = np.zeros(len(cc), bool); w2[offs] = True
        ws2[idx] = w2
    return out, ws2


# --------------------------------------------------------------------------------------------------------------- jobs
def sim_job(args):
    preset, rep, sec_len, lenhist = args
    try:
        os.nice(0)
    except Exception:
        pass
    t0 = time.process_time()
    c, ws, sid, repT, crs, isn = make_replicate(preset, PRESET_SEED[preset] + rep, sec_len, lenhist)
    g, t = analyse(c, ws, sid, repT)
    r = pack(g, t)
    r["n_null"] = int(isn.sum()); r["n_cross"] = int(crs.sum()); r["cpu"] = time.process_time() - t0
    return r


def set_low_priority():
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    except Exception:
        try:
            import ctypes
            ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)
        except Exception:
            pass


def cmd_sim(a):
    from multiprocessing import Pool
    set_low_priority()
    c, ws, sid = lp2()
    sec_len = [int((sid == s).sum()) for s in np.unique(sid)]
    lenhist = english_length_hist()
    os.makedirs(OUT, exist_ok=True)
    t0 = time.time()
    jobs = [(a.preset, r, sec_len, lenhist) for r in range(a.reps)]
    res = []
    with Pool(a.workers, initializer=set_low_priority) as pool:
        for r in pool.imap(sim_job, jobs, chunksize=4):
            res.append(r)
    cpu = sum(r["cpu"] for r in res)
    json.dump(dict(preset=a.preset, cfg=PRESETS[a.preset], reps=a.reps, seed0=PRESET_SEED[a.preset], cpu=cpu, sec_len=sec_len,
                   results=res), open(os.path.join(OUT, "raw_%s.json" % a.preset), "w"))
    print("preset %s: %d reps, wall %.0fs, worker cpu %.0fs, mean cpu/rep %.2fs" % (a.preset, a.reps, time.time() - t0, cpu, cpu / a.reps))


def cmd_lp2(a):
    set_low_priority()
    c, ws, sid = lp2()
    g, t = analyse(c, ws, sid)
    os.makedirs(OUT, exist_ok=True)
    rng = np.random.default_rng(13)
    sh = []
    t0 = time.process_time()
    for _ in range(a.shuf):
        sh.append(pack(*analyse(within_word_shuffle(c, ws, rng), ws, sid)))
    wsh = []
    for _ in range(a.wshuf):
        c2, ws2 = word_order_shuffle(c, ws, sid, rng)
        wsh.append(pack(*analyse(c2, ws2, sid)))
    json.dump(dict(lp2=pack(g, t), within_word=sh, word_order=wsh, cpu=time.process_time() - t0),
              open(os.path.join(OUT, "raw_lp2.json"), "w"))
    print("lp2: cell (6,0) hits %d, (5,1) hits %d; shuffles %d / %d; cpu %.0fs" % (g["H"][6, 0], g["H"][5, 1], a.shuf, a.wshuf,
                                                                                     time.process_time() - t0))


# ---------------------------------------------------------------------------------------------------------------- tests
def cmd_selftest(a):
    ok = True
    # 1. plant with w=0 reproduces r4sim bit for bit (same seed) for several configs
    words = S.words_from_lengths([random.Random(5).randrange(1, 12) for _ in range(400)], random.Random(6))
    key = [random.Random(7).randrange(N) for _ in range(5000)]
    for cfg in (dict(q=0.81, nu=0.448, slots="any"), dict(q=0.81, nu=0.448, slots="interior"), dict(q=1.0, nu=0.448, slots="any",
                null_check="none", null_visible=False, lag_basis="real"), dict(q=0.81, nu=0.448, slots="end")):
        a_ = S.encrypt_r4(words, key, random.Random(99), n_cipher=2500, **cfg)
        b_ = encrypt_r4_plant_full(words, key, random.Random(99), 0.0, n_cipher=2500, **cfg)
        same = (np.array_equal(a_.cipher, b_[0]) and np.array_equal(a_.word_start, b_[1]) and np.array_equal(a_.is_null, b_[2])
                and np.array_equal(a_.is_repair, b_[3]) and np.array_equal(a_.repair_is_T, b_[4]))
        print("selftest 1 plant(w=0) == r4sim", cfg.get("slots"), cfg.get("lag_basis", "cipher"), ":", same)
        ok &= same
    # 2. planted cross-gap repairs are T relations at lag 5 across the gap
    rr = random.Random(11)
    words = [[rr.randrange(N) for _ in range(rr.randrange(1, 12))] for _ in range(3000)]
    key = [rr.randrange(N) for _ in range(40000)]
    c, ws, isn, isrep, rt, cr = encrypt_r4_plant_full(words, key, random.Random(3), 1.0, q=1.0, nu=0.0, n_cipher=8000)
    idx = np.flatnonzero(cr)
    good = all(c[i] == TARR[c[i - 5]] for i in idx)
    print("selftest 2 cross repairs: %d, all c_j == T(c_(j-5)): %s" % (len(idx), good))
    ok &= good and len(idx) > 50
    # 3. grid statistic on a hand-built case: a stream where every position j >= 6 of one long word is T of the one 6 back
    c0 = np.zeros(60, np.int64); rs = np.random.default_rng(1)
    c0[:6] = rs.integers(0, N, 6)
    for j in range(6, 60):
        c0[j] = TARR[c0[j - 6]]
    ws0 = np.zeros(60, bool); ws0[0] = True
    g = grid_stats(c0, ws0, np.zeros(60, int))
    print("selftest 3 hand stream: lag-6 in-word hits %d of %d pairs; max-form lag 6 = form %s" % (g["H"][6, 0], g["NP"][6, 0], AFF[int(g["maxform"][6])]))
    ok &= g["H"][6, 0] == 54 and g["NP"][6, 0] == 54 and AFF[int(g["maxform"][6])] == (27, 24)
    # 4. LP2 lag-6 in-word cell reproduces the published 80 / 1290 / 44.47 and (5,1) 307 / 7369 / 254.2
    c, ws, sid = lp2()
    g, t = analyse(c, ws, sid)
    z = lambda gg, k: (g["H"][gg, k] - g["E"][gg, k]) / math.sqrt(g["V"][gg, k])
    print("selftest 4 LP2 (6,0): hits %d pairs %d E %.2f z %+.2f | (5,1): hits %d pairs %d E %.1f z %+.2f | lag-6 max form %s z %+.2f | T sites %d, doublets in/gap %d/%d"
          % (g["H"][6, 0], g["NP"][6, 0], g["E"][6, 0], z(6, 0), g["H"][5, 1], g["NP"][5, 1], g["E"][5, 1], z(5, 1), AFF[int(g["maxform"][6])],
             g["maxz"][6], t["n_sites"], t["dbl_in"], t["dbl_gap"]))
    ok &= g["H"][6, 0] == 80 and g["NP"][6, 0] == 1290 and abs(g["E"][6, 0] - 44.47) < 0.05
    ok &= g["H"][5, 1] == 307 and abs(g["E"][5, 1] - 254.2) < 0.2 and t["dbl_in"] == 63 and t["dbl_gap"] == 23
    # 5. within-word shuffle keeps word structure; its lag-6 cell hits ~45.7
    rng = np.random.default_rng(2)
    h = [analyse(within_word_shuffle(c, ws, rng), ws, sid)[0]["H"][6, 0] for _ in range(40)]
    print("selftest 5 within-word shuffle (6,0) mean hits %.1f (publ. 45.7)" % np.mean(h))
    ok &= abs(np.mean(h) - 45.7) < 4
    print("SELFTEST", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    sp.add_parser("selftest")
    p = sp.add_parser("lp2"); p.add_argument("--shuf", type=int, default=2000); p.add_argument("--wshuf", type=int, default=300)
    p = sp.add_parser("sim"); p.add_argument("preset"); p.add_argument("--reps", type=int, default=200); p.add_argument("--workers", type=int, default=2)
    sp.add_parser("summary")
    a = ap.parse_args()
    if a.cmd == "selftest":
        sys.exit(cmd_selftest(a))
    if a.cmd == "lp2":
        cmd_lp2(a)
    elif a.cmd == "sim":
        cmd_sim(a)
    else:
        import s13_summary
        s13_summary.main()


if __name__ == "__main__":
    main()
