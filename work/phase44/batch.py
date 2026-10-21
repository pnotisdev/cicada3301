"""Phase 44 keyless batch: T1 doublet fine structure, T2 DJU BEI + parity digraph, T4 word-length alignment, T5 recurring words.
Preregistration: work/log/phase44_keyless_batch.md.   python work/phase44/batch.py t1|t2|t4|t5 [draws]   (1 core)"""
import os, re, sys, collections
import numpy as np
import numba
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.join(HERE, ".."))
import lp
SEGS = lp.load_segments()[7:16]
assert sum(len(lp.runes_of(s)) for s in SEGS) == 12956
SEP = {" ", ".", "&", "\n", "%"}
LOG = os.path.join(HERE, "..", "log")


def layout():
    """per rune: seg, word idx, pos in word, line start, page; per adjacent same-segment pair: class."""
    X, seg, widx, wpos, lstart, page = [], [], [], [], [], []
    pair_cls = []
    w = -1; pg = 0
    for si, toks in enumerate(SEGS):
        newword = newline = first = True; between = set(); wp = 0
        for t in toks:
            if isinstance(t, int):
                if not first:
                    if " " in between: c = "gap"
                    elif "." in between: c = "clause"
                    elif "&" in between: c = "para"
                    elif "%" in between: c = "page"
                    elif "\n" in between: c = "nl"
                    else: c = "in"
                    pair_cls.append(c)
                    newword = c in ("gap", "clause", "para")
                    newline = "\n" in between or "%" in between
                if newword: w += 1; wp = 0
                else: wp += 1
                X.append(t); seg.append(si); widx.append(w); wpos.append(wp); lstart.append(newline); page.append(pg)
                first = False; between = set(); newword = False
            elif t in SEP:
                between.add(t)
                if t == "%": pg += 1
    X = np.array(X); seg = np.array(seg); widx = np.array(widx); wpos = np.array(wpos)
    lstart = np.array(lstart); page = np.array(page)
    lend = np.zeros(len(X), bool); lend[:-1] = lstart[1:] & (seg[:-1] == seg[1:])
    P = np.array([i for i in range(len(X) - 1) if seg[i] == seg[i + 1]])
    assert len(P) == len(pair_cls)
    return X, seg, widx, wpos, lstart, lend, page, P, np.array(pair_cls)


X, SEG, WIDX, WPOS, LSTART, LEND, PAGE, P, CLS = layout()
segbounds = [(int(np.where(SEG == s)[0][0]), int(np.where(SEG == s)[0][-1]) + 1) for s in range(9)]
INW = np.isin(CLS, ["in", "nl", "page"])


def shuffle(x, rng):
    y = x.copy()
    for a, b in segbounds: y[a:b] = rng.permutation(y[a:b])
    return y


def wordlens(toks):
    return [e - s for _, s, e in lp.word_spans(toks, lp.runes_of(toks))]


def words_runes(toks):
    r = lp.runes_of(toks); return [tuple(r[s:e]) for _, s, e in lp.word_spans(toks, r)]


# ------------------------------------------------------------------ T1
def t1_cells():
    cells = {}
    wl = np.bincount(WIDX)[WIDX]
    a, b = P, P + 1
    for c in ("in", "nl", "page", "gap", "clause", "para"): cells["cls_" + c] = (CLS == c)
    cells["inword_all"] = INW; cells["gap_all"] = ~INW
    cells["pair_has_line_first"] = LSTART[a] | LSTART[b]
    cells["pair_has_line_last"] = LEND[a] | LEND[b]
    cells["wordpos_first"] = INW & (WPOS[a] == 0); cells["wordpos_last"] = INW & (WPOS[b] == wl[a] - 1)
    cells["wordpos_mid"] = INW & (WPOS[a] > 0) & (WPOS[b] < wl[a] - 1)
    cells["abs_parity0"] = (a % 2 == 0); cells["abs_parity1"] = (a % 2 == 1)
    cells["inword_parity0"] = INW & (WPOS[a] % 2 == 0); cells["inword_parity1"] = INW & (WPOS[a] % 2 == 1)
    return cells


def recip(x):
    m = np.zeros((29, 29)); ok = INW & (x[P] != x[P + 1])
    np.add.at(m, (x[P][ok], x[P + 1][ok]), 1)
    d = m - m.T; s = m + m.T; iu = np.triu_indices(29, 1)
    return float(np.sum(d[iu] ** 2 / np.maximum(s[iu], 1)))


def cellvec(x, cells):
    eq = (x[P] == x[P + 1])
    return np.array([int((eq & m).sum()) for m in cells.values()]), eq


def pagevar(eq):
    c = np.bincount(PAGE[P][eq], minlength=PAGE.max() + 1)
    return float(c.var() / max(c.mean(), 1e-9))


def repair_null(rng, p_keep=0.19):
    y = np.concatenate([rng.choice(29, size=b - a, p=np.bincount(X[a:b], minlength=29) / (b - a)) for a, b in segbounds])
    for _ in range(1):                                  # one pass: each raw doublet is repaired once
        eq = np.where(y[P] == y[P + 1])[0]
        eq = eq[rng.random(len(eq)) > p_keep]          # repaired with prob 0.81
        if len(eq) == 0: break
        idx = P[eq] + 1; y[idx] = (y[idx] + rng.integers(1, 29, len(idx))) % 29
    return y


def t1(draws):
    cells = t1_cells(); names = list(cells)
    obs, eq = cellvec(X, cells); tot = np.array([int(m.sum()) for m in cells.values()])
    obs_rec, obs_pv = recip(X), pagevar(eq)
    out = ["T1 doublets. adjacent-equal pairs, all classes: %d; contiguous within-word (in/nl/page): %d; across gap/clause/para: %d" %
           (eq.sum(), eq[INW].sum(), eq[~INW].sum()), "draws per null: %d" % draws]
    res = {}
    for nm, gen in (("A shuffle", lambda r: shuffle(X, r)), ("B repair", repair_null)):
        rng = np.random.default_rng(4401); V = []; R = []; PV = []
        for _ in range(draws):
            y = gen(rng); v, e = cellvec(y, cells); V.append(v); R.append(recip(y)); PV.append(pagevar(e))
        V = np.array(V); res[nm] = (V.mean(0), V.std(0) + 1e-9, np.mean(R), np.std(R), np.mean(PV), np.std(PV))
    out.append("%-22s %6s %6s | %8s %6s | %8s %6s | flag(|z|>3.3 both)" % ("cell", "pairs", "obs", "A mean", "A z", "B mean", "B z"))
    for i, nm in enumerate(names):
        za = (obs[i] - res["A shuffle"][0][i]) / res["A shuffle"][1][i]; zb = (obs[i] - res["B repair"][0][i]) / res["B repair"][1][i]
        out.append("%-22s %6d %6d | %8.1f %6.2f | %8.1f %6.2f | %s" % (nm, tot[i], obs[i], res["A shuffle"][0][i], za, res["B repair"][0][i], zb,
                   "FLAG" if abs(za) > 3.3 and abs(zb) > 3.3 else ""))
    for nm, r in res.items():
        out.append("null %s: reciprocal chi obs %.1f mean %.1f sd %.1f z %.2f | page var/mean obs %.2f mean %.2f sd %.2f z %.2f" %
                   (nm, obs_rec, r[2], r[3], (obs_rec - r[2]) / r[3], obs_pv, r[4], r[5], (obs_pv - r[4]) / r[5]))
    print("\n".join(out)); open(os.path.join(LOG, "phase44_t1_result.txt"), "w", encoding="utf-8").write("\n".join(out))


# ------------------------------------------------------------------ T2
def t2_forensics():
    out = []; allw = []
    for si, toks in enumerate(SEGS):
        r = lp.runes_of(toks); sp = lp.word_spans(toks, r)
        allw.append([(w, s) for w, s, e in sp])
        out.append("seg %d (LP idx %d): first 3 words %s | last 3 words %s" % (si, si + 7, " ".join(w for w, _ in allw[-1][:3]), " ".join(w for w, _ in allw[-1][-3:])))
    flat = [(si, k, w, s) for si, ws in enumerate(allw) for k, (w, s) in enumerate(ws)]
    djus = [i for i in range(len(flat) - 1) if flat[i][2] == "DJU" and flat[i + 1][2] == "BEI"]
    for i in djus:
        si, k, _, s = flat[i]
        out.append("DJU BEI at seg %d word %d rune %d (global word %d of %d); context: %s [DJU BEI] %s" % (si, k, s, i, len(flat),
                   " ".join(w for _, _, w, _ in flat[max(0, i - 6):i]), " ".join(w for _, _, w, _ in flat[i + 2:i + 8])))
    if len(djus) >= 2: out.append("distance between copies: %d words" % (djus[1] - djus[0]))
    return out


def seg_pairs(k, r):
    idx = []
    for a, b in segbounds:
        i = np.arange(a, b - 1); idx.append(i[(i - a) % k == r])
    return np.concatenate(idx)


SP = {(k, r): seg_pairs(k, r) for k in range(2, 7) for r in range(k)}


def chi_bigram(x, idx, uni):
    m = np.zeros((29, 29)); np.add.at(m, (x[idx], x[idx + 1]), 1)
    e = np.outer(uni, uni) * len(idx)
    return float(((m - e) ** 2 / np.maximum(e, 1e-9)).sum())


def dig_ioc(x, r):
    idx = SP[(2, r)]; d = x[idx] * 29 + x[idx + 1]; c = np.bincount(d, minlength=841)
    return float((c * (c - 1)).sum() / (len(d) * (len(d) - 1) / 841))


def t2stat(x):
    uni = np.bincount(x, minlength=29) / len(x)
    return np.array([chi_bigram(x, SP[(k, r)], uni) for k in range(2, 7) for r in range(k)] + [dig_ioc(x, 0), dig_ioc(x, 1)])


def t2(draws):
    out = t2_forensics()
    names = ["chi k%d r%d" % (k, r) for k in range(2, 7) for r in range(k)] + ["dIOC even", "dIOC odd"]
    obs = t2stat(X); rng = np.random.default_rng(4402)
    N = np.array([t2stat(shuffle(X, rng)) for _ in range(draws)]); mu, sd = N.mean(0), N.std(0) + 1e-9
    z = (obs - mu) / sd; mx = np.abs((N - mu) / sd).max(1); thr = np.quantile(mx, 0.999 if draws >= 1000 else 0.99)
    out.append("T2 digraph cells (draws %d): observed max|z| %.2f; null max|z| %s quantile %.2f; empirical p(max) %.3f" %
               (draws, np.abs(z).max(), "99.9%" if draws >= 1000 else "99%", thr, (mx >= np.abs(z).max()).mean()))
    for n, o, zz in zip(names, obs, z): out.append("  %-12s obs %.3f z %.2f" % (n, o, zz))
    # deviation (documented in the log): the shuffle null does not contain the doublet deficit, which inflates every cell's chi2;
    # second null = repair model B (deficit kept, no parity structure), plus a within-k contrast (spread of chi2 over residues)
    NB = np.array([t2stat(repair_null(rng)) for _ in range(draws)]); mb, sb = NB.mean(0), NB.std(0) + 1e-9
    zb = (obs - mb) / sb; mxb = np.abs((NB - mb) / sb).max(1)
    out.append("null B (repair, deficit kept): observed max|z| %.2f at %s; null B 99.9%% quantile %.2f; empirical p(max) %.3f" %
               (np.abs(zb).max(), names[int(np.abs(zb).argmax())], np.quantile(mxb, 0.999 if draws >= 1000 else 0.99), (mxb >= np.abs(zb).max()).mean()))
    for n, o, zz in zip(names, obs, zb): out.append("  B %-12s z %.2f" % (n, zz))
    i0 = 0
    for k in range(2, 7):
        sp = lambda v: v[i0:i0 + k].max() - v[i0:i0 + k].min()
        sn = np.array([sp(v) for v in NB]); out.append("  spread over residues k=%d: obs %.1f null B mean %.1f sd %.1f z %.2f" % (k, sp(obs), sn.mean(), sn.std(), (sp(obs) - sn.mean()) / (sn.std() + 1e-9))); i0 += k
    L2R = dict(A=24, B=17, C=5, D=23, E=18, F=0, G=6, H=8, I=10, J=11, K=5, L=20, M=19, N=9, O=3, P=13, Q=5, R=4, S=15, T=16, U=1, V=1, W=7, X=14, Y=26, Z=15)
    t = open(os.path.join(HERE, "..", "ref", "corpora", "pg1497.txt"), encoding="utf-8", errors="ignore").read()
    t = re.sub("[^A-Z]", "", t[200000:].upper())[:12956]; pt = np.array([L2R[c] for c in t])
    while True:
        K = rng.integers(0, 29, (2, 2))
        if int(K[0, 0] * K[1, 1] - K[0, 1] * K[1, 0]) % 29: break
    ct = pt.copy()
    for a, b in segbounds:
        n = (b - a) // 2 * 2; pr = pt[a:a + n].reshape(-1, 2).T; ct[a:a + n] = ((K @ pr) % 29).T.reshape(-1)
    oc = t2stat(ct); Nc = np.array([t2stat(shuffle(ct, rng)) for _ in range(min(draws, 150))]); mc, sc = Nc.mean(0), Nc.std(0) + 1e-9
    zc = (oc - mc) / sc; mxc = np.abs((Nc - mc) / sc).max(1); q = np.quantile(mxc, 0.99)
    out.append("positive control (Hill 2x2 mod 29, English): max|z| %.2f at %s; control null 99%% quantile %.2f -> %s" %
               (np.abs(zc).max(), names[int(np.abs(zc).argmax())], q, "recovered" if np.abs(zc).max() > q else "NOT recovered"))
    print("\n".join(out)); open(os.path.join(LOG, "phase44_t2_result.txt"), "w", encoding="utf-8").write("\n".join(out))


# ------------------------------------------------------------------ T5
def t5(draws):
    ws = [w for toks in SEGS for w in words_runes(toks)]
    segw = [[len(w) for w in words_runes(toks)] for toks in SEGS]

    def stat(wlist):
        c = collections.Counter(w for w in wlist if len(w) >= 3); rec = {w: n for w, n in c.items() if n >= 2}
        return len(rec), sum(rec.values()), sum(1 for w in rec if len(w) >= 5)
    obs = stat(ws); rng = np.random.default_rng(4405); N = []
    for _ in range(draws):
        y = shuffle(X, rng); wl = []
        for si, (a, b) in enumerate(segbounds):
            p = a
            for L in segw[si]: wl.append(tuple(y[p:p + L])); p += L
        N.append(stat(wl))
    N = np.array(N); out = ["T5 recurring words (>=3 runes): distinct recurring %d, tokens %d, distinct len>=5 %d (null draws %d)" % (obs + (draws,))]
    for i, nm in enumerate(["distinct", "tokens", "len>=5"]):
        out.append("  %-9s obs %d null mean %.2f sd %.2f z %.2f  p_two_sided(emp) %.4f" % (nm, obs[i], N[:, i].mean(), N[:, i].std(), (obs[i] - N[:, i].mean()) / (N[:, i].std() + 1e-9), min(1, 2 * min((N[:, i] >= obs[i]).mean(), (N[:, i] <= obs[i]).mean()))))
    pos = collections.defaultdict(list)
    for i, w in enumerate(ws):
        if len(w) >= 3: pos[w].append(i)
    out.append("recurring words (word, count, word indices, gaps):")
    for w, p in sorted(pos.items(), key=lambda kv: -len(kv[1])):
        if len(p) >= 2: out.append("  %s %d: %s gaps %s" % ("".join(lp.LATIN[x] + "." for x in w), len(p), p, [b - a for a, b in zip(p, p[1:])]))
    print("\n".join(out)); open(os.path.join(LOG, "phase44_t5_result.txt"), "w", encoding="utf-8").write("\n".join(out))


# ------------------------------------------------------------------ T4
@numba.njit(cache=True)
def runs2(L, T, cnt):
    """cnt[0]: exact runs >= 20/30/40; cnt[1]: +-1 runs >= 20/30/40 (start in L, offset in T)."""
    n_t = len(T)
    for s in range(len(L) - 1):
        if L[s] < 0: continue
        for o in range(n_t - 41):
            n = 0
            while n < 40 and L[s + n] >= 0 and abs(L[s + n] - T[o + n]) <= 1: n += 1
            if n >= 20:
                m = 0
                while m < n and L[s + m] == T[o + m]: m += 1
                if m >= 20: cnt[0, 0] += 1
                if m >= 30: cnt[0, 1] += 1
                if m >= 40: cnt[0, 2] += 1
                cnt[1, 0] += 1
                if n >= 30: cnt[1, 1] += 1
                if n >= 40: cnt[1, 2] += 1
    return cnt


def targets():
    import glob
    T = {}
    t = open(os.path.join(HERE, "..", "ref", "lp_translation.txt"), encoding="utf-8", errors="ignore").read()
    T["LP1"] = "\n".join(l.split(None, 1)[1] if re.match(r"^\d+\.\d+", l) and len(l.split(None, 1)) > 1 else "" for l in t.splitlines())
    for f in sorted(glob.glob(os.path.join(HERE, "..", "ref", "corpora", "cited", "*"))):
        if not f.endswith(".html"): T[os.path.basename(f)] = open(f, encoding="utf-8", errors="ignore").read()
    T["emerson"] = open(os.path.join(HERE, "..", "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    return {k: np.array([len(w) for w in re.findall(r"[A-Za-z]+", v)][:200000], np.int64) for k, v in T.items()}


def t4(draws):
    TG = targets(); segw = [wordlens(toks) for toks in SEGS]

    def tot(sw):
        L = np.array([x for w in sw for x in list(w) + [-100] * 41], np.int64)
        return {k: runs2(L, T, np.zeros((2, 3), np.int64)) for k, T in TG.items()}
    obs = tot(segw); rng = np.random.default_rng(4404)
    N = [tot([list(rng.permutation(w)) for w in segw]) for _ in range(draws)]
    out = ["T4 word-length alignment (LP2 rune-lengths, %d words; target letter-lengths, first 200k words); counts of (LP2 start, target offset) with run >= 20/30/40" % sum(map(len, segw)),
           "null = %d within-segment word-length shuffles" % draws,
           "%-36s exact obs | +-1 obs | null max exact | null max +-1 | null mean +-1@20" % "target (n words)"]
    for k in TG:
        nm = np.array([n[k] for n in N])
        out.append("%-36s %s | %s | %s | %s | %.1f" % ("%s (%d)" % (k, len(TG[k])), obs[k][0].tolist(), obs[k][1].tolist(), nm[:, 0].max(0).tolist(), nm[:, 1].max(0).tolist(), nm[:, 1, 0].mean()))
    print("\n".join(out)); open(os.path.join(LOG, "phase44_t4_result.txt"), "w", encoding="utf-8").write("\n".join(out))


if __name__ == "__main__":
    f = {"t1": t1, "t2": t2, "t4": t4, "t5": t5}[sys.argv[1]]
    f(int(sys.argv[2]) if len(sys.argv) > 2 else 200)
