"""Phase 38: do LP2's keyless signals interact? Statistics, nulls and decision rules are fixed in work/log/phase38_signal_interactions.md section 0.

    python work/phase38/run.py iso      # 1.2 + 1.4  (slow, 2 processes)
    python work/phase38/run.py dju      # 1.3
    python work/phase38/run.py overlap  # 2
    python work/phase38/run.py wordlen  # 3
Each part writes results/analysis/phase38_<part>.txt.
"""
import os
import sys
from multiprocessing import Pool

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
for p in ("families", "mech25", ""):
    sys.path.insert(0, os.path.join(WORK, p))
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402
import lp  # noqa: E402

N = 29
LMIN, LMAX = 6, 30
OUT = os.path.join(WORK, "..", "results", "analysis")
T6 = M.T6


def emit(name, lines):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f"phase38_{name}.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def pval(obs, null, hi=True):
    null = np.asarray(null)
    return (1 + (null >= obs).sum() if hi else 1 + (null <= obs).sum()) / (1 + len(null))


# ---------------------------------------------------------------- nulls
def shuf_runes(c, sid, rng):
    out = c.copy()
    for k in np.unique(sid):
        m = np.flatnonzero(sid == k)
        out[m] = c[m][rng.permutation(len(m))]
    return out


def shuf_words_full(c, start, sid, rng):
    """word-order shuffle inside sections; returns (c, start) with the words moved whole"""
    oc, os_ = c.copy(), start.copy()
    for k in np.unique(sid):
        m = np.flatnonzero(sid == k)
        st = np.flatnonzero(start[m])
        en = np.append(st[1:], len(m))
        order = rng.permutation(len(st))
        oc[m] = np.concatenate([c[m][st[j]:en[j]] for j in order])
        os_[m] = np.concatenate([start[m][st[j]:en[j]] for j in order])
    return oc, os_


# ---------------------------------------------------------------- 1.2 isomorphs
_W = np.random.default_rng(1234).integers(1, 2 ** 62, size=LMAX, dtype=np.int64)


def patterns(c, L):
    n = len(c) - L + 1
    W = np.lib.stride_tricks.sliding_window_view(c, L)
    eq = W[:, :, None] == W[:, None, :]
    first = eq.argmax(axis=2)
    E = ((eq.sum(axis=2) - 1).sum(axis=1)) // 2
    h = (first.astype(np.int64) * _W[:L]).sum(axis=1)
    return h, E, n


def iso_stats(c, sid):
    """Emax, S3, Lbest over all matched pairs (see log 1.2)"""
    matched3 = set()
    best = (0, 0)
    for L in range(LMIN, LMAX + 1):
        h, E, n = patterns(c, L)
        ok = (sid[:n] == sid[L - 1:L - 1 + n]) & (E >= 2)
        idx = np.flatnonzero(ok)
        if len(idx) < 2:
            continue
        order = idx[np.argsort(h[idx], kind="stable")]
        hs = h[order]
        brk = np.flatnonzero(np.diff(hs)) + 1
        for g in np.split(order, brk):
            if len(g) < 2:
                continue
            g = np.sort(g)
            e = int(E[g[0]])
            if e < best[0]:
                # cannot raise Emax but may still add to S3 only if e >= 3
                if e < 3:
                    continue
            # non-overlapping pair exists iff last - first >= L
            if g[-1] - g[0] < L:
                continue
            if e > best[0]:
                best = (e, L)
            if e >= 3:
                for x in range(len(g)):
                    for y in range(x + 1, len(g)):
                        if g[y] - g[x] >= L:
                            matched3.add((int(g[x]), int(g[y]), L))
    s3 = 0
    for a, b, L in matched3:
        if L == LMAX or ((a, b, L + 1) not in matched3 and (a - 1, b - 1, L + 1) not in matched3):
            s3 += 1
    return best[0], s3, best[1]


def _null_job(args):
    kind, seed = args
    c, start, sid = D.lp2()
    rng = np.random.default_rng(seed)
    if kind == "N1":
        cc = shuf_runes(c, sid, rng)
    else:
        cc, _ = shuf_words_full(c, start, sid, rng)
    return iso_stats(cc, sid)


def encrypt(P, sid, rng, key, Q=0.81, skip=True):
    """c = p + key[ptr]; skip rule: a would-be repeat with prob Q moves the pointer on and recomputes"""
    out = np.empty(len(P), dtype=np.int64)
    last = -1
    ptr = 0
    prev_sec = -1
    for j in range(len(P)):
        if sid[j] != prev_sec:
            last = -1; prev_sec = sid[j]
        while True:
            x = (int(P[j]) + int(key[ptr])) % N
            ptr += 1
            if skip and x == last and rng.random() < Q:
                continue
            break
        out[j] = x
        last = x
    return out


def make_key(kind, P, s, n, rng):
    if kind == "R0":
        return rng.integers(N, size=n)
    base = rng.integers(N, size=P)
    i = np.arange(n)
    if kind == "per":
        return base[i % P]
    return (base[i % P] + s * (i // P)) % N


def _ctl_job(args):
    kind, P, skip, seed = args
    c, start, sid = D.lp2()
    rng = np.random.default_rng(seed)
    runes, _ = ENG[0]
    a = rng.integers(0, len(runes) - len(c) - 1)
    Pl = runes[a:a + len(c)]
    key = make_key(kind, P, 3, 6 * len(c), rng)
    cc = encrypt(Pl, sid, rng, key, skip=skip)
    return iso_stats(cc, sid)


ENG = None


def _init():
    global ENG
    ENG = (D.english(150_000),)


def run_iso(n_null=300, n_ctl=100):
    c, start, sid = D.lp2()
    L = []
    obs = iso_stats(c, sid)
    L.append(f"LP2: Emax {obs[0]}, S3 {obs[1]}, Lbest {obs[2]}")
    with Pool(2, initializer=_init) as pool:
        res = {}
        for kind in ("N1", "N2"):
            res[kind] = np.array(pool.map(_null_job, [(kind, 1000 + i) for i in range(n_null)], chunksize=5))
            r = res[kind]
            L.append(f"{kind}: n {n_null}; Emax mean {r[:,0].mean():.2f} 99th {np.percentile(r[:,0],99):.0f} max {r[:,0].max()}; "
                     f"p(Emax) {pval(obs[0], r[:,0]):.4f}; S3 mean {r[:,1].mean():.1f} 99th {np.percentile(r[:,1],99):.0f}; p(S3) {pval(obs[1], r[:,1]):.4f}")
            print(L[-1], flush=True)
        L.append("Emax distribution N1: " + str(np.bincount(res['N1'][:, 0]).tolist()))
        L.append("Emax distribution N2: " + str(np.bincount(res['N2'][:, 0]).tolist()))
        thr = {k: np.percentile(res[k][:, 0], 99) for k in res}
        L.append("controls (English plaintext, skip rule 0.81), Emax / S3 means and the share of runs with Emax > the 99th percentile of the R0 run:")
        cells = [("R0", 0, True), ("per", 13, True), ("per", 47, True), ("prog", 13, True), ("prog", 47, True),
                 ("per", 13, False), ("per", 47, False), ("prog", 13, False), ("prog", 47, False)]
        r0 = None
        rows = []
        for kind, P, skip in cells:
            r = np.array(pool.map(_ctl_job, [(kind, P, skip, 5000 + i) for i in range(n_ctl)], chunksize=5))
            rows.append((kind, P, skip, r))
            if kind == "R0":
                r0 = r
        t99 = np.percentile(r0[:, 0], 99)
        for kind, P, skip, r in rows:
            L.append(f"  {kind:5s} P={P:3d} skip={skip!s:5s}: Emax mean {r[:,0].mean():.2f} max {r[:,0].max()}, S3 mean {r[:,1].mean():.1f}, "
                     f"share Emax > R0-99th ({t99:.0f}): {(r[:,0] > t99).mean():.2f}")
            print(L[-1], flush=True)
    emit("iso", L)


# ---------------------------------------------------------------- 1.3 DJU BEI affine
def run_dju(n=2000):
    c, start, sid = D.lp2()
    t = np.array([23, 11, 1, 17, 18, 10])
    maps = [(a, b) for a in range(1, 29) for b in range(29)]
    POW = np.array([29 ** (5 - k) for k in range(6)])
    code6 = {(a, b): int(np.dot((a * t + b) % N, POW)) for a, b in maps}

    def word_counts(c, start, sid):
        st = np.flatnonzero(start)
        ln = np.diff(np.append(st, len(c)))
        pairs = {}
        for j in range(len(st) - 1):
            if ln[j] == 3 and ln[j + 1] == 3 and sid[st[j]] == sid[st[j + 1]]:
                k = int(np.dot(c[st[j]:st[j] + 6], POW))
                pairs[k] = pairs.get(k, 0) + 1
        return {m: pairs.get(v, 0) for m, v in code6.items()}

    def cr_counts(c, sid):
        i = np.arange(len(c) - 5)
        ok = sid[i] == sid[i + 5]
        w = np.zeros(len(i), dtype=np.int64)
        for k in range(6):
            w = w * N + c[i + k]
        u, cnt = np.unique(w[ok], return_counts=True)
        d = dict(zip(u.tolist(), cnt.tolist()))
        return {m: d.get(v, 0) for m, v in code6.items()}

    def stat(c, start, sid):
        cr, cw = cr_counts(c, sid), word_counts(c, start, sid)
        non = [m for m in cr if m != (1, 0)]
        return max(cr[m] for m in non), max(cw[m] for m in non), cr, cw

    o_cr, o_cw, cr, cw = stat(c, start, sid)
    L = [f"identity: Cr {cr[(1,0)]}, Cw {cw[(1,0)]} (known 2 word-aligned copies)",
         f"LP2 non-identity maps: max Cr {o_cr}, max Cw {o_cw}; maps with Cr>=1: {[m for m in cr if m!=(1,0) and cr[m]>=1]}; maps with Cw>=1: {[m for m in cw if m!=(1,0) and cw[m]>=1]}"]
    rng = np.random.default_rng(38)
    for kind in ("N1", "N2"):
        s = []
        for _ in range(n):
            if kind == "N1":
                cc, ss = shuf_runes(c, sid, rng), start
            else:
                cc, ss = shuf_words_full(c, start, sid, rng)
            r = stat(cc, ss, sid)
            s.append((r[0], r[1]))
        s = np.array(s)
        L.append(f"{kind} ({n} runs): max-over-maps Cr: P(>=1) {np.mean(s[:,0] >= 1):.4f}, mean {s[:,0].mean():.4f}; Cw: P(>=1) {np.mean(s[:,1] >= 1):.4f}; "
                 f"p(Cr obs {o_cr}) {pval(o_cr, s[:,0]):.4f}, p(Cw obs {o_cw}) {pval(o_cw, s[:,1]):.4f}")
        print(L[-1], flush=True)
    # share of 6-windows with the all-different pattern
    W = np.lib.stride_tricks.sliding_window_view(c, 6)
    alld = np.mean([len(set(w)) == 6 for w in W])
    L.append(f"share of LP2 6-windows with the all-different pattern (DJU BEI's equality pattern): {alld:.3f}")
    emit("dju", L)


# ---------------------------------------------------------------- 2 overlap
def sites(c, start, sid):
    wid, loc = M.wordinfo(start)
    out = {}
    for name, L, rel, S_only in (("L6", 6, T6, False), ("S5", 5, M.EQ, True)):
        i = np.arange(L, len(c))
        ok = (sid[i] == sid[i - L]) & (wid[i] == wid[i - L]) & (c[i] == rel[c[i - L]])
        if S_only:
            ok &= c[i] == M.S
        out[name] = i[ok]
    return out, wid, loc


def counts_AB(X, Y, wid):
    """for sites X, number with a Y-site in the same word (A), within +-1 (B), at the same position (C)"""
    Ys = np.sort(Y)
    wy = set(wid[Y].tolist())
    A = sum(wid[x] in wy for x in X)
    B = C = 0
    for x in X:
        k = np.searchsorted(Ys, x - 1)
        near = Ys[k:k + 3]
        near = near[(near >= x - 1) & (near <= x + 1) & (wid[near] == wid[x])]
        B += len(near) > 0
        C += bool((Ys == x).any())
    return A, B, C


def word_patterns(X, wid, loc, wlen_of_word):
    """dict word -> list of in-word positions"""
    d = {}
    for x in X:
        d.setdefault(int(wid[x]), []).append(int(loc[x]))
    return d


def perm_sites(pat, words_by_len, rng):
    """move each word's pattern to a random word of the same length (permutation inside each length class)"""
    newpat = {}
    for L, ws in words_by_len.items():
        have = [w for w in ws if w in pat]
        if not have:
            continue
        tgt = rng.permutation(ws)[:len(have)]
        for w, t in zip(have, tgt):
            newpat[int(t)] = pat[w]
    return newpat


def run_overlap(nperm=20000, nctl=200):
    c, start, sid = D.lp2()
    s, wid, loc = sites(c, start, sid)
    st = np.flatnonzero(start)
    wl = np.diff(np.append(st, len(c)))
    first = st
    words_by_len = {}
    for w, l in enumerate(wl):
        words_by_len.setdefault(int(l), []).append(w)
    # wid from wordinfo is cumsum(start) = 1-based; convert
    widz = wid - 1
    S5, L6 = s["S5"], s["L6"]
    patS = word_patterns(S5, widz, loc, wl)
    patL = word_patterns(L6, widz, loc, wl)

    def to_sites(pat):
        return np.array(sorted(first[w] + p for w, p in pat.items() for p in pat[w]), dtype=np.int64)

    def three(X, Y):
        return counts_AB(X, Y, widz)

    L = [f"S-sites {len(S5)} in {len(patS)} words; L6-sites {len(L6)} in {len(patL)} words; words with both: {len(set(patS) & set(patL))}"]
    rng = np.random.default_rng(3838)

    def test(Xpat, Ypat, nperm, rng):
        """move X's patterns; returns obs (A,B,C), null array (nperm,3)"""
        X, Y = to_sites(Xpat), to_sites(Ypat)
        obs = np.array(three(X, Y))
        nul = np.array([three(to_sites(perm_sites(Xpat, words_by_len, rng)), Y) for _ in range(nperm)])
        return obs, nul

    def report(tag, obs, nul):
        for j, nm in enumerate("ABC"):
            L.append(f"  {tag} {nm}: obs {obs[j]}, null mean {nul[:,j].mean():.2f} (sd {nul[:,j].std():.2f}); P(null>=obs, co-location) {pval(obs[j], nul[:,j]):.4f}; "
                     f"P(null<=obs, avoidance) {pval(obs[j], nul[:,j], hi=False):.4f}")
            print(L[-1], flush=True)

    obs, nul = test(patS, patL, nperm, rng)
    L.append("S-sites moved, L6 fixed (statistics counted over the 11 S-sites):")
    report("S->L6", obs, nul)
    obs2, nul2 = test(patL, patS, nperm, rng)
    L.append("L6-sites moved, S fixed (statistics counted over the L6-sites w.r.t. S-sites; direction check):")
    # note: statistic here counts moved class's sites near fixed class
    report("L6->S", obs2, nul2)
    cohere = lambda ob, nu: (pval(ob[0], nu[:, 0]) <= .025 and pval(ob[1], nu[:, 1]) <= .025, pval(ob[0], nu[:, 0], False) <= .025 and pval(ob[1], nu[:, 1], False) <= .025)
    L.append(f"decision rule (A and B both P<=0.025; (co-location, avoidance)): S side {cohere(obs, nul)}, L6 side {cohere(obs2, nul2)}")
    # controls: 200 pseudo-datasets, 1000 perms each for speed
    npc = 1000
    Lsites = to_sites(patL)
    det_pos = det_null = det_null_av = 0
    for r in range(nctl):
        # planted: each S site with prob .5 moved to the position of a random L6 site
        newS = []
        for x in S5:
            if rng.random() < .5:
                newS.append(int(rng.choice(Lsites)))
            else:
                newS.append(int(x))
        newS = np.array(sorted(set(newS)))
        pat = word_patterns(newS, widz, loc, wl)
        ob, nu = test(pat, patL, npc, rng)
        det_pos += cohere(ob, nu)[0]
        # null pseudo-data
        pat0 = perm_sites(patS, words_by_len, rng)
        ob, nu = test(pat0, patL, npc, rng)
        c0 = cohere(ob, nu)
        det_null += c0[0]; det_null_av += c0[1]
    L.append(f"controls ({nctl} pseudo-datasets, {npc} permutations each): planted co-location detected {det_pos / nctl:.2f}; null pseudo-data flagged co-location {det_null / nctl:.3f}, avoidance {det_null_av / nctl:.3f}")
    print(L[-1], flush=True)
    emit("overlap", L)


# ---------------------------------------------------------------- 3 word lengths
def wl_hist(lengths):
    h = np.bincount(np.minimum(lengths, M.BINS), minlength=M.BINS + 1)[1:].astype(float)
    return h


def model_hist(base, r, multi_only):
    q = base / base.sum()
    ins = q.copy()
    if multi_only:
        ins[0] = 0
    m = q - r * ins
    m[1:] += r * ins[:-1]
    m[-1] += r * ins[-1]
    return m


RGRID = np.linspace(0, 0.8, 161)


def fit_r(h, base):
    best = None
    for mo in (True, False):
        for r in RGRID:
            g = M.g_test(h, model_hist(base, r, mo))
            if best is None or g < best[0]:
                best = (g, r, mo)
    return best


def fit_r_fixed(h, base, mo):
    g = [M.g_test(h, model_hist(base, r, mo)) for r in RGRID]
    k = int(np.argmin(g))
    return g[k], RGRID[k]


def run_wordlen(nshuf=1000, nboot=1000):
    c, start, sid = D.lp2()
    s, wid, loc = sites(c, start, sid)
    widz = wid - 1
    st = np.flatnonzero(start)
    wl = np.diff(np.append(st, len(c)))
    nw = len(wl)
    ems = [len(lp.word_to_key(w.replace("IO", "IA"))) for w in __import__("wordlen").emerson_words()]
    base = wl_hist([x for x in ems if x])
    h_all = wl_hist(wl)
    g, r, mo = fit_r(h_all, base)
    L = [f"all words {nw}: fitted +1 model r {r:.3f} (multi-rune only: {mo}), G {g:.1f} (df 10)"]
    rng = np.random.default_rng(3838)
    rb = []
    for _ in range(nboot):
        hb = wl_hist(wl[rng.integers(nw, size=nw)])
        rb.append(fit_r_fixed(hb, base, mo)[1])
    L.append(f"  r bootstrap 95% interval {np.percentile(rb, 2.5):.3f}-{np.percentile(rb, 97.5):.3f}")
    qm = model_hist(base, r, mo); q = qm / qm.sum()
    L.append("  length histogram (%) 1..11,12+: LP2 " + " ".join(f"{x:5.1f}" for x in 100 * h_all / h_all.sum()) + " | model " + " ".join(f"{x:5.1f}" for x in 100 * q))

    def groups(cc):
        ss, w2, _ = sites(cc, start, sid)
        w2 = w2 - 1
        i5 = np.arange(5, len(cc))
        ok5 = (sid[i5] == sid[i5 - 5]) & (w2[i5] == w2[i5 - 5]) & (cc[i5] == cc[i5 - 5])
        e6 = np.zeros(nw, bool); e6[w2[ss["L6"]]] = True
        e5 = np.zeros(nw, bool); e5[w2[i5[ok5]]] = True
        return {"E6": e6, "E5": e5, "EU": e6 | e5, "non": ~(e6 | e5)}, ss["L6"], w2

    def gstat(mask):
        h = wl_hist(wl[mask])
        return wl[mask].mean(), fit_r_fixed(h, base, mo)[1], M.g_test(h, q)

    obsg, L6s, _ = groups(c)
    nulls = {k: [] for k in obsg}
    nl_profile = []
    for _ in range(nshuf):
        cc = shuf_runes(c, sid, rng)
        gg, l6, w2 = groups(cc)
        for k in gg:
            nulls[k].append(gstat(gg[k]) if gg[k].sum() > 5 else (np.nan,) * 3)
        nl_profile.append(wl_hist(wl[w2[l6]]))
    L.append(f"groups (L6-bearing E6 / lag-5-bearing E5 / either EU / none): sizes " + ", ".join(f"{k} {int(v.sum())}" for k, v in obsg.items()))
    for k, m in obsg.items():
        o = gstat(m)
        nu = np.array(nulls[k])
        bo = []
        idx = np.flatnonzero(m)
        for _ in range(300):
            mm = np.zeros(nw, bool); mm[rng.choice(idx, len(idx))] = True
            bo.append(gstat(mm))
        bo = np.array(bo)
        for j, nm in enumerate(("mean length", "fitted r", "G vs global model")):
            if j and k != "non":
                continue   # deviation from the pre-registration: r and G are degenerate for groups selected to be >= 7 runes (r hits the 0.8 bound)
            lo, hi = np.nanpercentile(nu[:, j], [2.5, 97.5])
            blo, bhi = np.percentile(bo[:, j], [2.5, 97.5])
            L.append(f"  {k:3s} {nm:18s}: obs {o[j]:.3f} [boot {blo:.3f}-{bhi:.3f}]; selection null mean {np.nanmean(nu[:,j]):.3f} [{lo:.3f}-{hi:.3f}]; "
                     f"obs-null {o[j]-np.nanmean(nu[:,j]):+.3f}")
    # site-length profile
    obs_prof = wl_hist(wl[widz[L6s]])
    bg = np.mean(nl_profile, axis=0); bgp = bg / bg.sum()
    n6 = obs_prof.sum()
    gprof = M.g_test(obs_prof, bgp)
    gnull = np.array([M.g_test(np.random.default_rng(i).multinomial(int(n6), bgp).astype(float), bgp) for i in range(2000)])
    L.append(f"L6-site word-length profile (80 sites; 1..11,12+): obs {obs_prof.astype(int).tolist()}, null mean {np.round(bg,1).tolist()}")
    L.append(f"  G(obs vs null profile) {gprof:.1f}, multinomial null P {pval(gprof, gnull):.4f}")
    # mixture with inserted-rune words
    b = base / base.sum()
    inn = b.copy()
    if mo:
        inn[0] = 0
    mod = np.zeros(M.BINS)
    mod[1:] = r * inn[:-1]; mod[-1] += r * inn[-1]   # share of all words that are +1 words, by length (one echo per word at most)
    mod[:6] = 0   # an echo needs >= 7 runes
    mod = mod / mod.sum()

    def ll(sitehist, pi):
        p = (1 - pi) * bgp + pi * mod
        return float((sitehist[p > 0] * np.log(p[p > 0])).sum())
    grid = np.linspace(0, 1, 201)
    def fitpi(h):
        v = [ll(h, p) for p in grid]
        k = int(np.argmax(v)); return grid[k], v[k] - v[0]
    pi, gain = fitpi(obs_prof)
    sl = wl[widz[L6s]]
    pis = []
    for _ in range(1000):
        pis.append(fitpi(wl_hist(sl[rng.integers(len(sl), size=len(sl))]))[0])
    # null of the gain under background only
    gain0 = np.array([fitpi(np.random.default_rng(10 ** 6 + i).multinomial(int(n6), bgp).astype(float))[1] for i in range(1000)])
    L.append(f"mixture with +1-inserted words: pi {pi:.3f} (boot 95% {np.percentile(pis,2.5):.3f}-{np.percentile(pis,97.5):.3f}), loglik gain {gain:.2f}, null P(gain>=obs) {pval(gain, gain0):.4f}")
    exp_tot = bg.sum()
    pi_ex = (n6 - exp_tot) / n6
    L.append(f"supplementary (not pre-registered): chance L6-sites per shuffle {exp_tot:.1f} vs observed {int(n6)}; excess profile by length (obs - chance) "
             f"{np.round(obs_prof - bg, 1).tolist()}; log-lik gain of pi fixed at the excess share {pi_ex:.2f}: {ll(obs_prof, pi_ex) - ll(obs_prof, 0):+.2f} (negative: the +1-word profile fits the excess worse than the chance profile)")
    L.append("  model profile (inserted-word share by length, L>=7): " + str(np.round(mod, 3).tolist()))
    # power: plant pi=.3
    det = 0
    for i in range(300):
        pp = 0.7 * bgp + 0.3 * mod
        h = np.random.default_rng(2 * 10 ** 6 + i).multinomial(int(n6), pp).astype(float)
        det += pval(fitpi(h)[1], gain0) <= 0.01
    L.append(f"  power to detect pi=0.3 at P<=0.01: {det / 300:.2f}")
    for ln in L:
        print(ln)
    emit("wordlen", L)


if __name__ == "__main__":
    part = sys.argv[1]
    {"iso": run_iso, "dju": run_dju, "overlap": run_overlap, "wordlen": run_wordlen}[part]()
