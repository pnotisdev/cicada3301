"""Phase 61: un-repair via lag-6 sites. See work/log/phase61_unrepair.md.

    python work/phase61_unrepair.py sim    [--reps 250]                 # detector D on phase 57's R4 simulator -> results/analysis/phase61_sim.txt
    python work/phase61_unrepair.py test                                # controls of the Python decoder and the plant generator
    python work/phase61_unrepair.py rust   [--per 40] [--workers 4]     # (a) un-repair, mid engine S_guard + oracle IoC -> results/analysis/phase61_rust/
    python work/phase61_unrepair.py py     [--per 40] [--workers 4]     # (a) + (b) with the Python decoder (no nulls) -> results/analysis/phase61_py/
    python work/phase61_unrepair.py summary                             # -> results/analysis/phase61_plants.txt

D = within-word sites i (word position >= 6, the window start counts as a word start) with c_i = T(c_{i-6}), T(x) = 24 - 2x mod 29.
Plants are phase 51's (plant_mid.make_plant) except that the anti-repeat repair writes T(c_{i-6}) in-word (R4) and every repair is recorded. Streams are the library
streams of length <= 2100 (a single-stream null; the whole-library null tail is higher for raw and un-repaired alike). Windows without a D site are unchanged by either use and
are not searched (their difference is 0 by identity).
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import random
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE / "chanscreen" / "v2" / "step4"))
import phase57_mechanism as P57  # noqa: E402
import plant_mid as X  # noqa: E402

P, C = X.P, X.C
Q = 29
OUT = HERE.parent / "results" / "analysis"
PCH = {"m04": "hold", "spend": "spend"}      # plant channel -> decoder channel
SRCS = ("english", "cicada")
RHO = 0.45                                   # plant rate of the interior null (phase 57 R4: 0.448 of multi-rune words)
QPL = 0.81
MAXLEN = 2100
ALIAS = C.ALIAS_K


def lower():
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)


def Tm(x):
    return (24 - 2 * x) % Q


def dsites(c, ws):
    """indices i >= 6 in the same word as i-6 (ws[0] is a word start) with c_i = T(c_{i-6})"""
    c = np.asarray(c, int)
    wid = np.cumsum(np.r_[1, np.asarray(ws, int)[1:]]) - 1
    i = np.arange(6, len(c))
    return i[(wid[i] == wid[i - 6]) & (c[i] == Tm(c[i - 6]))]


def unrepair(c, sites):
    c2 = np.array(c, int)
    c2[sites] = np.asarray(c, int)[sites - 1]
    return [int(v) for v in c2]


# ------------------------------------------------------------------ step 1: detector on the R4 simulator
def sim(reps, rate=0.448, chunk=50):
    out = []
    ctxs = P57.D.lp2()
    c_lp, ws_lp, sid = ctxs
    P_, ST = P57.D.english(150_000)
    nxt = np.zeros(len(ST), int)
    last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    s = np.flatnonzero(ST)
    WL = np.zeros(len(ST), int)
    WL[s] = np.diff(np.append(s, len(ST)))
    ctx = (P_.astype(np.int16), nxt, WL, sid)
    n = len(sid)
    wid_lp = np.cumsum(ws_lp) - 1
    i = np.arange(6, n)
    lp_d = int(((wid_lp[i] == wid_lp[i - 6]) & (c_lp[i] == Tm(c_lp[i - 6]))).sum())
    out.append(f"LP2: {lp_d} D sites (within-word c_i = 24 - 2 c_(i-6)), {n} runes. R4 simulator: rate {rate}, q 0.81, T repair, checked word null, {reps} texts of {n} runes")
    rng = np.random.default_rng(6101)
    rows = []
    for k in range(0, reps, chunk):
        Cc, WS, RT, RA = P57.simulate(min(chunk, reps - k), rng, ctx, q=0.81, rep="T", ins="word", check=True, rate=rate, want=True)
        for r in range(len(Cc)):
            c, ws = Cc[r].astype(int), WS[r]
            wid = np.cumsum(ws) - 1
            d = np.zeros(n, bool)
            d[6:] = (wid[6:] == wid[:-6]) & (c[6:] == Tm(c[:-6]))
            # positions in a 300 window: D sites per 300 runes
            rows.append((int(d.sum()), int((d & RT[r]).sum()), int(RT[r].sum()), int(RA[r].sum()), int(((c[1:] == c[:-1]) & (~ws[1:])).sum())))
    a = np.array(rows, float)
    D_, TP, RTn, RAn = a[:, 0], a[:, 1], a[:, 2], a[:, 3]
    out.append(f"D sites per text: mean {D_.mean():.1f} sd {D_.std():.1f} (LP2 {lp_d}, z {(lp_d - D_.mean()) / D_.std():+.2f}); true T repairs among them {TP.mean():.1f} sd {TP.std():.1f}")
    out.append(f"precision (pooled) {TP.sum() / D_.sum():.3f}  (per-text mean {np.mean(TP / D_):.3f}, 5-95% {np.percentile(TP / D_, 5):.2f}-{np.percentile(TP / D_, 95):.2f})")
    out.append(f"recall of T-valued repairs {TP.sum() / RTn.sum():.3f} ({RTn.mean():.1f} per text; all of them are D sites by construction)")
    out.append(f"recall of ALL repairs {TP.sum() / RAn.sum():.3f} ({RAn.mean():.1f} repairs per text, {RAn.mean() / n:.4f} per rune); only {RTn.sum() / RAn.sum():.3f} of repairs are T-valued (word position >= 6)")
    out.append(f"false D sites (chance matches c_i = T(c_(i-6)) on a genuine rune): {np.mean(D_ - TP):.1f} per text; expected per 300 / 150 runes: D {D_.mean() * 300 / n:.2f} / {D_.mean() * 150 / n:.2f}, true {TP.mean() * 300 / n:.2f} / {TP.mean() * 150 / n:.2f}")
    out.append(f"share of 300-rune windows with >= 1 D site (Poisson, mean {D_.mean() * 300 / n:.2f}): {1 - math.exp(-D_.mean() * 300 / n):.2f}; with >= 1 true site {1 - math.exp(-TP.mean() * 300 / n):.2f}")
    txt = "\n".join(out) + "\n"
    print(txt)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "phase61_sim.txt").write_text(txt, newline="\n", encoding="utf-8")


# ------------------------------------------------------------------ plants with T repairs
def make_plant(ch, src, i, rho, iid_key=False):
    G = P._G
    rng = random.Random(int.from_bytes(hashlib.sha256(f"phase61-plant|{ch}|{src}|{i}".encode()).digest()[:8], "big"))
    e0 = rng.randrange(100)
    sec = P.SECS[rng.randrange(len(P.SECS))]
    wl = G["words"][sec]
    w0 = rng.randrange(len(wl) - 150)
    items, plain_len, w = [], 0, w0
    while len(items) < e0 + 320 + 40:
        L = wl[w]
        slot = rng.randrange(1, L) if (L >= 2 and rng.random() < rho) else 0
        for t in range(L):
            items.append(("r", plain_len, t == 0, t == L - 1))
            plain_len += 1
            if slot and t + 1 == slot:
                items.append(("n", False, False, False))
        w += 1
    pool = G["pool"][src]
    s0 = rng.randrange(len(pool) - plain_len + 1)
    plain = pool[s0:s0 + plain_len]
    need = len(items) + 16
    eligible = [k for k, (_, v) in enumerate(G["lib"]) if need + 1 <= len(v) <= MAXLEN]
    si = eligible[rng.randrange(len(eligible))]
    name, key = G["lib"][si]
    keyl = [int(x) for x in key]
    off = rng.randrange(len(key) - need + 1)
    mult = 1 if i % 4 < 2 else 28
    if iid_key:
        keyl = [rng.randrange(Q) for _ in range(len(keyl))]
    out, used, isnull, rep, repT, pre, ptx, wstart = [], [], [], [], [], [], [], []
    j, ell, wst = off, None, 0
    for it in items:
        if it[0] == "n":
            out.append(rng.randrange(Q)); used.append(-1); isnull.append(True); rep.append(False); repT.append(False); pre.append(-1); ptx.append(-1); wstart.append(False)
            continue
        if it[2]:
            wst = len(out)
        p = plain[it[1]]
        x = (p + mult * keyl[j]) % Q
        u, isrep, ist = j, False, False
        if ell is not None and x == ell and rng.random() < QPL:
            tb = Tm(out[-6]) if len(out) - wst >= 6 else None
            if tb is not None and tb != ell:
                y, ist = tb, True
            else:
                r = rng.randrange(Q - 1)
                y = r + 1 if r >= ell else r
            isrep = True
            nj = j + 1 if ch == "spend" else j
        else:
            y, nj = x, j + 1
        out.append(y); used.append(u); isnull.append(False); rep.append(isrep); repT.append(ist); pre.append(x); ptx.append(p); wstart.append(it[2])
        ell, j = y, nj
    e = e0
    while isnull[e]:
        e += 1
    sl = slice(e, e + 300)
    ws = [1] + [int(v) for v in wstart[sl][1:]]
    return dict(name=name, stream_index=si, keyl=keyl, offset=off, e=e, mult=mult, true_sign=1 if mult == 1 else -1, cipher=out[sl], ws=ws, we=ws,
                used=used[sl], isnull=isnull[sl], rep=rep[sl], repT=repT[sl], pre=pre[sl], plain=ptx[sl], o_true=int(used[e]), nulls=int(sum(isnull[sl])))


def ioc(x):
    x = np.asarray(x, int)
    f = np.bincount(x, minlength=Q).astype(float)
    return float((f * (f - 1)).sum() / (len(x) * (len(x) - 1)))


def oracle_dec(pl, c):
    sgn = pl["true_sign"]
    return [(c[k] - sgn * pl["keyl"][u]) % Q for k, u in enumerate(pl["used"]) if u >= 0]


def ioc_block(pl, rng, n=300, nnull=1000):
    """oracle-key IoC of the planted window raw / un-repaired at D sites / un-repaired at every true repair vs random (offset, sign) decryptions of the same ciphertext"""
    c = pl["cipher"][:n]
    ds = dsites(c, pl["ws"][:n])
    pl_n = dict(pl, used=pl["used"][:n])
    allfix = [pl["pre"][k] if pl["rep"][k] else c[k] for k in range(n)]
    variants = dict(raw=c, unrep=unrepair(c, ds) if len(ds) else c, allfix=allfix)
    key = np.array(pl["keyl"])
    m = len(key)
    res = {}
    offs = rng.integers(0, m - n, nnull)
    sg = rng.choice([1, -1], nnull)
    for nm, cc in variants.items():
        t = ioc(oracle_dec(pl_n, cc))
        cc = np.array(cc)
        nl = np.array([ioc((cc - s * key[o:o + n]) % Q) for o, s in zip(offs, sg)])
        res[nm] = dict(true=t, null_mean=float(nl.mean()), null_sd=float(nl.std()), null_max=float(nl.max()))
    res["plain"] = ioc([v for v in pl["plain"][:n] if v >= 0])
    return res


def rust_one(args):
    ch, src, i = args
    dest = OUT / "phase61_rust" / f"r_{ch}_{src}_{i:03d}.json"
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    lower()
    pi, L = P._G["pi"], P._G["L"]
    pl = make_plant(ch, src, i, RHO)
    npl = make_plant(ch, src, i + 1000, RHO, iid_key=True)
    npl["keyl"], npl["o_true"] = pl["keyl"], -10 ** 6
    dec = PCH[ch]
    rec = dict(channel=ch, src=src, index=i, stream=pl["name"], nulls=pl["nulls"], true_sign=pl["true_sign"])
    rng = np.random.default_rng(i * 7 + 1)
    for n in (300, 150):
        dt, dn = dsites(pl["cipher"][:n], pl["ws"][:n]), dsites(npl["cipher"][:n], npl["ws"][:n])
        r = dict(nD=len(dt), nTP=int(sum(pl["repT"][k] for k in dt)), nD_null=len(dn), nrep=int(sum(pl["rep"][:n])), nrepT=int(sum(pl["repT"][:n])),
                 literal_ok=int(sum(pl["pre"][k] == pl["cipher"][k - 1] for k in dt)))
        if len(dt) or len(dn):
            raw_t = X.search(dict(pl), n, dec, "mid", pi, L) if len(dt) else None
            raw_n = X.search(dict(npl), n, dec, "mid", pi, L) if len(dn) else None
            if len(dt):
                un_t = X.search(dict(pl, cipher=unrepair(pl["cipher"][:n], dt) + pl["cipher"][n:]), n, dec, "mid", pi, L)
                r["true"] = dict(raw=_pick(raw_t), unrep=_pick(un_t))
            if len(dn):
                un_n = X.search(dict(npl, cipher=unrepair(npl["cipher"][:n], dn) + npl["cipher"][n:]), n, dec, "mid", pi, L)
                r["null"] = dict(raw=_pick(raw_n), unrep=_pick(un_n))
        rec[str(n)] = r
    if rec["300"]["nD"]:
        rec["ioc300"] = ioc_block(pl, rng)
    rec["seconds"] = time.perf_counter() - t0
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rec, indent=1), newline="\n", encoding="utf-8")
    return dest.name, rec["seconds"]


def _pick(s):
    return dict(band=s["band_best"], winner=s["winner_score"], wrong_max=s["null_max"])


# ------------------------------------------------------------------ Python decoder (exact hold / spend semantics, no nulls), all offsets and signs at once
class Dec:
    def __init__(self, pi, L, q=C.Q_DECODER):
        self.pi, self.L, self.q = np.asarray(pi), np.asarray(L), q

    def weights(self, c, ws, variant):
        """per position: genuine-path weight g_i, repair emission r_i(y_i) (None -> position has no repair path), as arrays; shared by L and U"""
        n = len(c)
        c = np.asarray(c, int)
        g = np.ones(n)
        rep = np.full(n, 1.0 / (Q - 1))
        if variant in ("hard", "aware"):
            wid = np.cumsum(np.r_[1, np.asarray(ws, int)[1:]]) - 1
            for i in range(6, n):
                if wid[i] != wid[i - 6]:
                    continue
                tb = Tm(c[i - 6])
                if variant == "hard":
                    if c[i] == tb:
                        g[i] = 0.0                      # forced repair at a D site (the repair emission stays uniform)
                elif tb != c[i - 1]:
                    rep[i] = 1.0 if c[i] == tb else 0.0      # R4: the repair rune is T(c_(i-6))
        return g, rep

    def lnU(self, c, g, rep):
        c = np.asarray(c, int)
        q = self.q
        tot = 0.0
        for i in range(len(c)):
            if i and c[i] == c[i - 1]:
                tot += math.log((1 - q) / Q)
            else:
                tot += math.log((g[i] + (q * rep[i] if i else 0.0)) / Q)
        return tot

    def lnL(self, c, key, signs, offs, g, rep, mode, H):
        """log P(c | cell) for every (sign, offset); cells = signs x offs. hold keeps h = number of repairs so far (<= H); spend has a deterministic pointer"""
        q, pi, L = self.q, self.pi, self.L
        n, m = len(c), len(key)
        oo = np.tile(np.asarray(offs), len(signs))
        ss = np.repeat(np.asarray(signs), len(offs))
        K = len(oo)
        H1 = H + 1 if mode == "hold" else 1
        hs = np.arange(H1)
        kk = np.arange(K)[:, None] * np.ones((1, H1), int)
        hh = np.ones((K, 1), int) * hs[None, :]
        alpha = np.zeros((K, H1, Q))
        logs = np.zeros(K)
        for i in range(n):
            y = c[i]
            ell = c[i - 1] if i else None
            idx = oo[:, None] + i - (hs[None, :] if mode == "hold" else 0)
            k = key[np.clip(idx, 0, m - 1)]
            if i == 0:
                M = np.zeros((K, H1, Q)); M[:, 0, :] = pi
            else:
                M = (alpha.reshape(-1, Q) @ L).reshape(K, H1, Q)
            b1 = (y - ss[:, None] * k) % Q
            new = np.zeros((K, H1, Q))
            if i and y == ell:
                new[kk, hh, b1] = M[kk, hh, b1] * (1 - q)
            else:
                new[kk, hh, b1] = M[kk, hh, b1] * g[i]
                if i and rep[i] > 0:
                    b2 = (ell - ss[:, None] * k) % Q
                    w = q * rep[i]
                    if mode == "hold":
                        new2 = np.zeros((K, H1, Q))
                        new2[kk[:, :-1], hh[:, :-1] + 1, b2[:, :-1]] = M[kk[:, :-1], hh[:, :-1], b2[:, :-1]] * w
                        new += new2
                    else:
                        new[kk, hh, b2] += M[kk, hh, b2] * w
            tot = new.sum((1, 2))
            with np.errstate(divide="ignore"):
                logs += np.log(tot)
            alpha = new / np.where(tot > 0, tot, 1)[:, None, None]
        return logs


def py_one(args):
    ch, src, i = args
    dest = OUT / "phase61_py" / f"p_{ch}_{src}_{i:03d}.json"
    if dest.exists():
        return dest.name, 0.0
    t0 = time.perf_counter()
    lower()
    dec = Dec(P._G["pi"], P._G["L"])
    mode = PCH[ch]
    pl = make_plant(ch, src, i, 0.0)
    npl = make_plant(ch, src, i + 1000, 0.0, iid_key=True)
    key = np.array(pl["keyl"])
    rec = dict(channel=ch, src=src, index=i, stream=pl["name"], true_sign=pl["true_sign"])
    for n in (300, 150):
        H = 14 if n == 300 else 10
        dt, dn = dsites(pl["cipher"][:n], pl["ws"][:n]), dsites(npl["cipher"][:n], npl["ws"][:n])
        r = dict(nD=len(dt), nTP=int(sum(pl["repT"][k] for k in dt)), nD_null=len(dn), nrep=int(sum(pl["rep"][:n])), nrepT=int(sum(pl["repT"][:n])))
        offs = np.arange(0, len(key) - n + 1)
        nO = len(offs)
        ot, ts = pl["o_true"], pl["true_sign"]
        base = 0 if ts == 1 else nO
        alias = np.zeros(2 * nO, bool); alias[base + max(0, ot - ALIAS):base + min(nO, ot + ALIAS + 1)] = True
        band = np.zeros(2 * nO, bool); band[base + max(0, ot - 3):base + min(nO, ot + 4)] = True
        res = {}
        for nm, who, dd in (("true", pl, dt), ("null", npl, dn)):
            cc = who["cipher"][:n]
            for var in ("raw", "unrep", "hard", "aware"):
                c2 = unrepair(cc, dd) if var == "unrep" and len(dd) else cc
                g, rep = dec.weights(c2, who["ws"][:n], var if var in ("hard", "aware") else "raw")
                s = dec.lnL(np.array(c2), key, [1, -1], offs, g, rep, mode, H) - dec.lnU(c2, g, rep)
                res[f"{nm}_{var}"] = dict(band=float(s[band].max()), wrong_max=float(s[~alias].max()), winner=float(s.max())) if nm == "true" else dict(winner=float(s.max()))
        r["res"] = res
        rec[str(n)] = r
    rec["seconds"] = time.perf_counter() - t0
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(rec, indent=1), newline="\n", encoding="utf-8")
    return dest.name, rec["seconds"]


def test():
    """controls: (1) the Python decoder reproduces the Rust base engine on a null-free plant, (2) D recovers planted T repairs, (3) un-repair restores the pre-repair rune at true sites"""
    P._init()
    pi, L = P._G["pi"], P._G["L"]
    dec = Dec(pi, L)
    from engine_mid import all_offsets_mid
    for ch in ("m04", "spend"):
        pl = make_plant(ch, "english", 3, 0.0)
        key = np.array(pl["keyl"])
        n = 60
        c = pl["cipher"][:n]
        offs = np.array([pl["o_true"], pl["o_true"] + 1, 5, 17, 300])
        for sign in (1, -1):
            g, rep = dec.weights(c, pl["ws"][:n], "raw")
            lnl = dec.lnL(np.array(c), key, [sign], offs, g, rep, PCH[ch], 40)
            out = all_offsets_mid(c, key, sign, C.Q_DECODER, PCH[ch], pi, L, 0, nu=0.0)
            d = np.abs(lnl - out[offs, 0]).max()
            print(f"control 1 {ch} sign {sign}: max |python - rust| lnL = {d:.2e}; U python {dec.lnU(c, g, rep):.6f} rust {out[offs[0], 1]:.6f}")
            assert d < 1e-6 and abs(dec.lnU(c, g, rep) - out[offs[0], 1]) < 1e-6
    ntp = nD = nrt = 0
    for i in range(40):
        pl = make_plant("spend", "english", i, 0.45)
        d = dsites(pl["cipher"], pl["ws"])
        nD += len(d); ntp += sum(pl["repT"][k] for k in d); nrt += sum(pl["repT"])
        assert all(pl["pre"][k] == pl["cipher"][k - 1] for k in d if pl["repT"][k] and not pl["isnull"][k - 1])
        assert sum(pl["repT"][k] for k in range(300)) == sum(1 for k in d if pl["repT"][k])    # every T-valued repair is a D site
    print(f"control 2/3 (40 plants, n 300): D {nD}, true {ntp}, T-valued repairs {nrt}: all T-valued repairs are D sites, literal un-repair restores the pre-repair rune")
    print("tests passed")


def summary():
    L = []

    def paired(name, a, b):
        a, b = np.array(a, float), np.array(b, float)
        d = b - a
        if not len(d):
            return f"{name}: no windows"
        return f"{name}: n {len(d)}, mean change {d.mean():+.2f} nats (se {d.std(ddof=1) / math.sqrt(len(d)) if len(d) > 1 else float('nan'):.2f}), median {np.median(d):+.2f}, up {int((d > 0.05).sum())} / down {int((d < -0.05).sum())}"

    recs = [json.loads(p.read_text()) for p in sorted((OUT / "phase61_rust").glob("*.json"))]
    nall = len(recs)
    L.append(f"(a) mid engine S_guard, plants with R4 nulls (rate {RHO}, decoder nu {X.RHO}), T repairs, streams <= {MAXLEN} runes, {nall} plants x (true, matched iid-key null); T300 = {C.T300:.2f}")
    for n in ("300", "150"):
        rs = [r[n] for r in recs]
        w = [r for r in rs if r["nD"]]
        L.append(f"  n {n}: plants with >= 1 D site {len(w)}/{len(rs)}; D sites {sum(r['nD'] for r in rs)}, true T repairs among them {sum(r['nTP'] for r in rs)} (precision {sum(r['nTP'] for r in rs) / max(1, sum(r['nD'] for r in rs)):.2f}); "
                 f"all repairs in the windows {sum(r['nrep'] for r in rs)}, T-valued {sum(r['nrepT'] for r in rs)}; literal c_i := c_(i-1) restores the pre-repair rune at {sum(r['literal_ok'] for r in rs)}/{sum(r['nD'] for r in rs)} D sites")
        t = [r["true"] for r in rs if "true" in r]
        L.append("    " + paired("true-key band", [x["raw"]["band"] for x in t], [x["unrep"]["band"] for x in t]))
        L.append("    " + paired("true-key band, windows with a TRUE site", [x["raw"]["band"] for x, r in zip(t, [r for r in rs if 'true' in r]) if r["nTP"]], [x["unrep"]["band"] for x, r in zip(t, [r for r in rs if 'true' in r]) if r["nTP"]]))
        nn = [r["null"] for r in rs if "null" in r]
        L.append("    " + paired("matched-null winner (random key)", [x["raw"]["winner"] for x in nn], [x["unrep"]["winner"] for x in nn]))
        gap = [(r["true"]["unrep"]["band"] - r["true"]["raw"]["band"]) for r in rs if "true" in r]
        L.append(f"    raw band median over the searched windows {np.median([x['raw']['band'] for x in t]):.1f}, raw matched-null winner median {np.median([x['raw']['winner'] for x in nn]) if nn else float('nan'):.1f}")
    iocs = [r["ioc300"] for r in recs if "ioc300" in r]
    if iocs:
        L.append(f"  oracle-key IoC of the n 300 window (only windows with a D site, {len(iocs)}), mean over windows: plaintext {np.mean([x['plain'] for x in iocs]):.4f}; "
                 + "; ".join(f"{nm} {np.mean([x[nm]['true'] for x in iocs]):.4f} (null mean {np.mean([x[nm]['null_mean'] for x in iocs]):.4f}, null max {np.mean([x[nm]['null_max'] for x in iocs]):.4f})" for nm in ("raw", "unrep", "allfix")))
        for nm in ("unrep", "allfix"):
            d = [x[nm]["true"] - x["raw"]["true"] for x in iocs]
            L.append(f"    IoC change {nm} - raw: mean {np.mean(d):+.5f} (se {np.std(d, ddof=1) / math.sqrt(len(d)):.5f}); in null-sd units {np.mean(d) / np.mean([x['raw']['null_sd'] for x in iocs]):+.2f}; true minus null max: raw {np.mean([x['raw']['true'] - x['raw']['null_max'] for x in iocs]):.4f}, {nm} {np.mean([x[nm]['true'] - x[nm]['null_max'] for x in iocs]):.4f}")
    precs = [json.loads(p.read_text()) for p in sorted((OUT / "phase61_py").glob("*.json"))]
    L.append("")
    L.append(f"(b) Python decoder, plants WITHOUT nulls (exact hold / spend semantics), S = ln L - ln U, {len(precs)} plants; variants raw | unrep (a) | hard (D sites forced to be repairs) | aware (R4 likelihood)")
    for n in ("300", "150"):
        rs = [r[n] for r in precs]
        L.append(f"  n {n}: {len(rs)} plants; true-cipher D sites {sum(r['nD'] for r in rs)} (true {sum(r['nTP'] for r in rs)}), repairs {sum(r['nrep'] for r in rs)} of which T-valued {sum(r['nrepT'] for r in rs)}")
        for sel, tag in ((lambda r: True, "all windows"), (lambda r: r["nD"] > 0, "windows with a D site in the TRUE cipher"), (lambda r: r["nTP"] > 0, "windows with a TRUE T repair")):
            q_ = [r for r in rs if sel(r)]
            if not q_:
                continue
            L.append(f"    {tag} ({len(q_)}):")
            for var in ("unrep", "hard", "aware"):
                L.append("      " + paired(f"{var:6s} band", [r["res"]["true_raw"]["band"] for r in q_], [r["res"][f"true_{var}"]["band"] for r in q_]))
                L.append("      " + paired(f"{var:6s} null winner", [r["res"]["null_raw"]["winner"] for r in q_], [r["res"][f"null_{var}"]["winner"] for r in q_]))
                L.append("      " + paired(f"{var:6s} band - null winner", [r["res"]["true_raw"]["band"] - r["res"]["null_raw"]["winner"] for r in q_], [r["res"][f"true_{var}"]["band"] - r["res"][f"null_{var}"]["winner"] for r in q_]))
            L.append(f"      raw: band median {np.median([r['res']['true_raw']['band'] for r in q_]):.1f}, null winner median {np.median([r['res']['null_raw']['winner'] for r in q_]):.1f}")
    txt = "\n".join(L) + "\n"
    print(txt)
    (OUT / "phase61_plants.txt").write_text(txt, newline="\n", encoding="utf-8")


def pool_run(fn, todo, workers):
    print(len(todo), "to do", flush=True)
    with cf.ProcessPoolExecutor(max_workers=workers, initializer=P._init) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(fn, a) for a in todo]), 1):
            nm, dt = f.result()
            print(f"[{time.strftime('%H:%M:%S')}] {n}/{len(todo)} {nm} {dt:.0f}s", flush=True)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("sim", "test", "rust", "py", "summary"))
    ap.add_argument("--reps", type=int, default=250)
    ap.add_argument("--per", type=int, default=24)
    ap.add_argument("--workers", type=int, default=4)
    a = ap.parse_args()
    lower()
    if a.cmd == "sim":
        sim(a.reps)
    elif a.cmd == "test":
        test()
    elif a.cmd == "summary":
        summary()
    else:
        fn, sub = (rust_one, "phase61_rust") if a.cmd == "rust" else (py_one, "phase61_py")
        todo = [(ch, s, i) for ch in PCH for s in SRCS for i in range(a.per)]
        pool_run(fn, todo, a.workers)
