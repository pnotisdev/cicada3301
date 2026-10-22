"""Phase 60 test T1 (work/log/phase60_clue_review.md): phi, sigma, pi ... of LP2's own word Gematria sums as key material.

 A  engine screen (phase 35 convention): per-WORD values f(G_w), f(R_w) walked rune by rune as an additive key stream (whole book and 0.15, raw and prefix sums, forwards and reversed),
    all offsets, 8 section windows, both signs, skip / coin models; planted control and a shuffled-stream null (phase 35 machinery).
 B  word-aligned keys (the "number of THIS word" reading, no offset search, no skip drift):
    PT  key of a word = s*f(S(plaintext word)) + b.  Decoding must find, for every word, a shift v with v = s*f(S(c - v)) + b; for each (S, f, s, b) the share of words with such a v is
        ~64% by chance (random function) and 100% for the true rule (84% if 45% of the words carry an unkeyed extra rune). Null: runes shuffled over the positions (word lengths kept).
    CT  key of a word = s*f(S(ciphertext word)) + b: decode directly, IoC of the decoded section (invariant under b). Null: shuffled runes.
    Controls: PT and CT plants from English words (Emerson), same statistic, true configuration must be the maximum.

    python work/kscreen/phase60_t1.py build|controls|run|b|summary [--threads 3]
"""
import argparse
import os
import random
import sys
from math import sqrt

import numpy as np

import phase35 as P35
import pdir_ref as P
import selftest as S
import signrules as R

sys.path.insert(0, R.WORK)
import lp  # noqa: E402
import stats  # noqa: E402

HERE = S.HERE
DATA = os.path.join(HERE, "data", "phase60_t1")
RES = os.path.join(S.ROOT, "results", "kscreen", "phase60_t1")
Q = 29
TOP = 4000
PR = np.array(lp.PRIME)


def tables():
    """f tables over 0..TOP-1 (index = the word sum)"""
    ph = np.arange(TOP)
    for i in range(2, TOP):
        if ph[i] == i:
            ph[i::i] -= ph[i::i] // i
    sg = np.zeros(TOP, np.int64)
    for i in range(1, TOP):
        sg[i::i] += i
    isp = np.array([n > 1 and all(n % d for d in range(2, int(n ** 0.5) + 1)) for n in range(TOP + 200)])
    pi = np.cumsum(isp)[:TOP]
    nxt = np.array([next(m for m in range(n + 1, n + 200) if isp[m]) - n for n in range(TOP)])
    ar = np.arange(TOP)
    return {"phi": ph, "sigma": sg, "S-1": np.maximum(ar - 1, 0), "pi": pi, "gap": nxt, "phi(S+1)": ph[(ar + 1) % TOP], "S": ar}


F = tables()


def sections():
    return P35.sections()


# ---------------------------------------------------------------- A: engine streams
def stream_set(secs):
    scopes = {"book": [], "seg0.15": []}
    for name, s in secs.items():
        w = [(sum(s["runes"][a:b]), sum(lp.PRIME[x] for x in s["runes"][a:b])) for a, b in s["word"]]
        scopes["book"] += w
        if len(s["word"]) >= P35.MINWORDS:
            scopes[name] = w
    out = {}
    for scope, w in scopes.items():
        for st, idx in (("R", 0), ("G", 1)):
            for fn, tab in F.items():
                if st == "R" and fn in ("S", "S-1"):
                    continue
                vals = [int(tab[x[idx] % TOP]) for x in w]
                raw = [v % Q for v in vals]
                pre, acc = [], 0
                for v in vals:
                    acc += v; pre.append(acc % Q)
                for kind, s in (("raw", raw), ("prefix", pre)):
                    out[f"p60 {scope} {fn}({st}) {kind} fwd"] = s
                    out[f"p60 {scope} {fn}({st}) {kind} rev"] = s[::-1]
    return out


def build():
    os.makedirs(DATA, exist_ok=True)
    streams = stream_set(sections())
    P.write_ksb(os.path.join(DATA, "words.ksb"), list(streams.items()))
    rng = random.Random(60)
    nulls = []
    for name, v in streams.items():
        for i in range(10):
            s = v[:]; rng.shuffle(s); nulls.append((f"null{i} {name}", s))
    P.write_ksb(os.path.join(DATA, "words_null.ksb"), nulls)
    with open(os.path.join(DATA, "streams.tsv"), "w", newline="\n") as f:
        f.write("stream\tlength\tpredicted_ioc\n")
        for name, v in streams.items():
            f.write(f"{name}\t{len(v)}\t{P35.predicted_ioc(v):.4f}\n")
    print(len(streams), "streams", len(nulls), "null streams")


def rel(p):
    return os.path.relpath(p, HERE).replace("\\", "/")


def controls(threads):
    ksb = dict(P35.read_ksb(os.path.join(DATA, "words.ksb")))
    preds = {l.split("\t")[0]: float(l.split("\t")[2]) for l in open(os.path.join(DATA, "streams.tsv")).read().splitlines()[1:]}
    flat = [n for n, p in preds.items() if p <= 1.003]
    import sign_selftest as SS
    plains = SS.plain_windows()
    fam = "file:" + rel(os.path.join(DATA, "words.ksb"))
    lines, ok = [f"INFO  {len(flat)} of {len(preds)} streams predicted flat under English"], True
    pick = [n for n in flat if " book " in n]
    cases = [(pick[i * (len(pick) // 4)], m, mo) for i, (m, mo) in enumerate([(1, 0), (28, 1), (1, 1), (28, 0)])]
    one = lambda t, w: 1
    for ci, (item, mult, model) in enumerate(cases):
        key = list(ksb[item]); rng = random.Random(6000 + ci); entries = []
        for wi, (runes, lens) in enumerate(plains):
            off = (400 + 211 * wi) % max(1, len(key) - len(runes) * 2 - 60)
            c, _, _ = P.plant(runes, lens, key, off, mult, model, 0.19, one, "000", False, rng, R.numbers)
            entries.append((f"plant_{wi}", -1, c, lens, None, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
        pf = os.path.join(S.TMP, f"p60t1_plant{ci}.txt"); P.write_windows(pf, entries)
        tsv = os.path.join(S.TMP, f"p60t1_plant{ci}.tsv")
        S.run(["screen", S.rel(pf), fam, S.rel(tsv), f"only={item}", f"threads={threads}"])
        best = S.window_bests(tsv)
        other = [n for n in pick if n.split()[3] != item.split()[3]][0]
        tsvo = os.path.join(S.TMP, f"p60t1_plant{ci}_o.tsv")
        S.run(["screen", S.rel(pf), fam, S.rel(tsvo), f"only={other}", f"threads={threads}"])
        besto = S.window_bests(tsvo)
        for win, (_, toff) in S.truths(pf).items():
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            good = bitem == item and abs(int(boff) - int(toff)) <= 2 and ioc >= S.THRESHOLD and besto.get(win, (9,))[0] < S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  A plant {item!r} model={model} mult={mult} {win}: best {ioc:.3f} at offset {boff} (truth {toff}); other stream {other!r}: {besto.get(win, (0,))[0]:.3f}")
    lines.append("PHASE60 T1 ENGINE CONTROLS " + ("PASSED" if ok else "FAILED"))
    os.makedirs(RES, exist_ok=True)
    open(os.path.join(RES, "controls_engine.txt"), "w", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def run(threads):
    segs = "data/segments.txt"
    P35.screen.__globals__["RES"] = RES
    P35.screen("A_real", segs, "file:" + rel(os.path.join(DATA, "words.ksb")), threads)
    P35.screen("A_null", segs, "file:" + rel(os.path.join(DATA, "words_null.ksb")), threads)


# ---------------------------------------------------------------- B: word-aligned keys
def padded(words, maxl=24):
    M = np.full((len(words), maxl), -1, np.int64)
    for i, w in enumerate(words):
        M[i, :len(w)] = w
    return M


def sums(M, v):
    """(R, G) of every word with the shift v removed: runes (c - v) mod 29"""
    idx = (M - v) % Q
    m = M >= 0
    return (np.where(m, idx, 0).sum(1)), (np.where(m, PR[idx], 0).sum(1))


CONFIGS = [(st, fn, s) for st in ("R", "G") for fn in F for s in (1, -1) if not (st == "R" and fn in ("S", "S-1"))]   # key linear in R: always solvable mod 29


def pt_prevalence(M):
    """-> {(S, f, s): share of words with a consistent shift, per b (length 29)}"""
    RG = [sums(M, v) for v in range(Q)]
    out = {}
    for st, fn, s in CONFIGS:
        tab = F[fn]
        pres = np.zeros((len(M), Q), bool)
        for v in range(Q):
            S_ = RG[v][0 if st == "R" else 1] % TOP
            d = (v - s * tab[S_]) % Q
            pres[np.arange(len(M)), d] = True
        out[(st, fn, s)] = pres.mean(0)
    return out


def ct_ioc(M, flat_c):
    """IoC (random = 1) of c - s f(S(c word)) over all runes, per config"""
    R_, G_ = sums(M, 0)
    m = M >= 0
    out = {}
    for st, fn, s in CONFIGS:
        v = (s * F[fn][(R_ if st == "R" else G_) % TOP]) % Q
        dec = (M - v[:, None]) % Q
        h = np.bincount(dec[m], minlength=Q)
        n = h.sum()
        out[(st, fn, s)] = Q * float((h * (h - 1)).sum()) / (n * (n - 1))
    return out


def words_of(secs, names):
    ws = []
    for n in names:
        s = secs[n]
        ws += [s["runes"][a:b] for a, b in s["word"]]
    return ws


def shuffled(ws, rng):
    flat = np.array([x for w in ws for x in w]); rng.shuffle(flat)
    out, k = [], 0
    for w in ws:
        out.append(list(flat[k:k + len(w)])); k += len(w)
    return out


def english_words(n, rng):
    import re
    txt = open(os.path.join(R.WORK, "ref", "emerson_essays1.txt"), encoding="utf-8").read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    allw = [lp.word_to_key(w.upper().replace("IO", "IA")) for w in re.findall(r"[A-Za-z]+", txt)]
    allw = [w for w in allw if w]
    i = rng.randrange(len(allw) - n)
    return [list(w) for w in allw[i:i + n]]


def plant_pt(words, st, fn, s, b, extra=0.0, rng=None):
    out = []
    for w in words:
        a = np.array(w)
        S_ = int(a.sum()) if st == "R" else int(PR[a].sum())
        v = (s * int(F[fn][S_ % TOP]) + b) % Q
        c = [(x + v) % Q for x in w]
        if rng and rng.random() < extra:
            c.insert(rng.randrange(len(c) + 1), rng.randrange(Q))
        out.append(c)
    return out


def plant_ct(words, st, fn, s, b, rng):
    """words with a consistent v: v = s f(S(p + v)) + b; others are dropped (63% survive)"""
    out = []
    for w in words:
        a = np.array(w)
        for v in range(Q):
            c = (a + v) % Q
            S_ = int(c.sum()) if st == "R" else int(PR[c].sum())
            if v == (s * int(F[fn][S_ % TOP]) + b) % Q:
                out.append([int(x) for x in c]); break
    return out


def summarize_pt(real, nulls, tag, lines, top=6):
    keys = list(real)
    rb = {k: (real[k].max(), int(real[k].argmax())) for k in keys}
    nm = np.array([[n[k].max() for k in keys] for n in nulls])           # null max-over-b per config
    nmax = nm.max(1)
    best = sorted(keys, key=lambda k: -rb[k][0])[:top]
    pmax = ((nmax >= max(v[0] for v in rb.values())).sum() + 1) / (len(nulls) + 1)
    lines.append(f"{tag}: best share of words with a consistent shift {max(v[0] for v in rb.values()):.4f}; null max-over-all-configs median {np.median(nmax):.4f}, max {nmax.max():.4f}; P(max) = {pmax:.3f}")
    for k in best:
        lines.append(f"      {k[0]} {k[1]} s={k[2]:+d}: share {rb[k][0]:.4f} at b={rb[k][1]}  (null mean max-over-b {nm[:, keys.index(k)].mean():.4f})")
    return max(v[0] for v in rb.values()), nmax


def summarize_ct(real, nulls, tag, lines, top=6):
    keys = list(real)
    nmax = np.array([max(n.values()) for n in nulls])
    pmax = ((nmax >= max(real.values())).sum() + 1) / (len(nulls) + 1)
    lines.append(f"{tag}: best IoC {max(real.values()):.4f}; null max-over-configs median {np.median(nmax):.4f}, max {nmax.max():.4f}; P(max) = {pmax:.3f}")
    for k in sorted(keys, key=lambda k: -real[k])[:top]:
        lines.append(f"      {k[0]} {k[1]} s={k[2]:+d}: IoC {real[k]:.4f}")


def partb(reps):
    secs = sections()
    rng = random.Random(61)
    lines = []
    scopes = {"LP2 all (8 windows' sections)": list(secs), "seg0.15": ["seg0.15"]}
    for sname, names in scopes.items():
        ws = words_of(secs, names)
        M = padded(ws)
        lines.append(f"== {sname}: {len(ws)} words")
        real = pt_prevalence(M)
        nulls = [pt_prevalence(padded(shuffled(ws, rng))) for _ in range(reps)]
        summarize_pt(real, nulls, "B-PT real", lines)
        rc = ct_ioc(M, None)
        ncs = [ct_ioc(padded(shuffled(ws, rng)), None) for _ in range(reps)]
        summarize_ct(rc, ncs, "B-CT real", lines)
        if sname.startswith("LP2"):
            ncs_pt = nulls
    # controls
    lines.append("== controls (English words from Emerson; same statistic, same null size)")
    n = 2000
    for label, cfg, b, extra in (("PT plant (G, phi, +, b=5)", ("G", "phi", 1), 5, 0.0), ("PT plant (R, sigma, -, b=17)", ("R", "sigma", -1, ), 17, 0.0),
                                 ("PT plant (G, pi, +, b=3) + 45% extra unkeyed rune", ("G", "pi", 1), 3, 0.45)):
        pl = plant_pt(english_words(n, rng), cfg[0], cfg[1], cfg[2], b, extra, rng)
        Mp = padded(pl)
        real = pt_prevalence(Mp)
        nul = [pt_prevalence(padded(shuffled(pl, rng))) for _ in range(max(10, reps // 4))]
        k = (cfg[0], cfg[1], cfg[2])
        top, nmax = summarize_pt(real, nul, label, lines, top=3)
        lines.append(f"      planted config share {real[k].max():.4f} at b={int(real[k].argmax())} (want b={b}); is the maximum: {real[k].max() >= top - 1e-12}")
    for label, cfg, b in (("CT plant (G, phi, +, b=5)", ("G", "phi", 1), 5), ("CT plant (R, phi(S+1), -, b=2)", ("R", "phi(S+1)", -1), 2)):
        pl = plant_ct(english_words(8000, rng), cfg[0], cfg[1], cfg[2], b, rng)
        Mp = padded(pl)
        real = ct_ioc(Mp, None)
        nul = [ct_ioc(padded(shuffled(pl, rng)), None) for _ in range(max(10, reps // 4))]
        summarize_ct(real, nul, f"{label} ({len(pl)} words survive)", lines, top=3)
        lines.append(f"      planted config IoC {real[cfg]:.4f}")
    txt = "\n".join(lines)
    os.makedirs(RES, exist_ok=True)
    open(os.path.join(RES, "partB.txt"), "w", newline="\n").write(txt + "\n")
    print(txt)


def partb_sections(reps):
    """the PT test per section (b may differ between sections); P(max over configs and b) per section against its own shuffles"""
    secs = sections()
    rng = random.Random(62)
    lines = []
    for name in secs:
        ws = words_of(secs, [name])
        real = pt_prevalence(padded(ws))
        nulls = [pt_prevalence(padded(shuffled(ws, rng))) for _ in range(reps)]
        keys = list(real)
        top = max(keys, key=lambda k: real[k].max())
        nmax = np.array([max(n[k].max() for k in keys) for n in nulls])
        lines.append(f"{name}: {len(ws)} words; best share {real[top].max():.4f} ({top[0]} {top[1]} s={top[2]:+d} b={int(real[top].argmax())}); null max median {np.median(nmax):.4f}, max {nmax.max():.4f}; P = {((nmax >= real[top].max()).sum() + 1) / (reps + 1):.3f}")
    txt = chr(10).join(lines)
    open(os.path.join(RES, "partB_sections.txt"), "w", newline=chr(10)).write(txt + chr(10))


def summary():
    import re
    for n in ("A_real", "A_null"):
        p = os.path.join(RES, n + ".tsv")
        if os.path.exists(p):
            hd = open(p, encoding="utf-8", errors="replace").readline()
            print(n, "best IoC", P35.best_of(p), re.search(r"runs=(\d+)", hd).group(1), "decodes")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd"); ap.add_argument("--threads", type=int, default=3); ap.add_argument("--reps", type=int, default=100)
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    {"c": lambda: None, "build": build, "controls": lambda: controls(a.threads), "run": lambda: run(a.threads), "b": lambda: partb(a.reps), "bsec": lambda: partb_sections(a.reps), "summary": summary}[a.cmd]()


# ---------------------------------------------------------------- C: key from the PREVIOUS word's sum (word-level feedback)
def ioc_counts(h):
    n = h.sum(-1)
    return Q * (h * (h - 1)).sum(-1) / (n * (n - 1))


def feedback_chains(words, st, fn, s, mode):
    """mode 'PT': v_w = s f(S(plain word w-1)) + b; 'CT': v_w = s f(S(cipher word w-1)) + b. 29 x 29 chains (first-word shift v0, constant b) run in parallel; returns the IoC of every chain"""
    tab = F[fn]
    v0, b = np.meshgrid(np.arange(Q), np.arange(Q), indexing="ij")
    v0, b = v0.ravel(), b.ravel()
    counts = np.zeros((len(v0), Q), np.int64)
    v = v0.copy()
    prev_c = None
    for w in words:
        c = np.array(w)[None, :]
        p = (c - v[:, None]) % Q
        counts += np.bincount((np.arange(len(v))[:, None] * Q + p).ravel(), minlength=len(v) * Q).reshape(len(v), Q)
        if mode == "PT":
            S_ = p.sum(1) if st == "R" else PR[p].sum(1)
        else:
            S_ = np.full(len(v), int(c.sum()) if st == "R" else int(PR[c[0]].sum()))
        v = (s * tab[S_ % TOP] + b) % Q
    return ioc_counts(counts)


def partc(reps):
    secs = sections()
    rng = random.Random(63)
    ws = words_of(secs, ["seg0.15"])            # the biggest section: 735 words, keeps the run short
    allws = words_of(secs, list(secs))
    lines = []
    cfgs = list(CONFIGS)

    def best(words):
        out = {}
        for st, fn, s in cfgs:
            for mode in ("PT", "CT"):
                out[(st, fn, s, mode)] = float(feedback_chains(words, st, fn, s, mode).max())
        return out
    real = best(allws)
    nulls = [best(shuffled(allws, rng)) for _ in range(reps)]
    nmax = np.array([max(n.values()) for n in nulls])
    top = sorted(real, key=lambda k: -real[k])[:5]
    lines.append(f"C real (LP2, {len(allws)} words; {len(cfgs)} configs x PT/CT x 841 chains): best chain IoC {real[top[0]]:.4f}; null max-over-all median {np.median(nmax):.4f}, max {nmax.max():.4f}; P = {((nmax >= real[top[0]]).sum() + 1) / (reps + 1):.3f}")
    for k in top:
        lines.append(f"      {k}: {real[k]:.4f}")
    for label, cfg, mode in (("PT plant (G, phi, +)", ("G", "phi", 1), "PT"), ("CT plant (R, sigma, -)", ("R", "sigma", -1), "CT")):
        words = english_words(1500, rng)
        # encipher with the chain: first-word shift 7, constant b 11
        tab = F[cfg[1]]; v = 7; out = []; bconst = 11
        for w in words:
            a = np.array(w); c = (a + v) % Q
            S_ = int((a if mode == "PT" else c).sum() if cfg[0] == "R" else PR[a if mode == "PT" else c].sum())
            v = (cfg[2] * int(tab[S_ % TOP]) + bconst) % Q
            out.append([int(x) for x in c])
        r2 = best(out)
        n2 = np.array([max(best(shuffled(out, rng)).values()) for _ in range(max(5, reps // 10))])
        k = (cfg[0], cfg[1], cfg[2], mode)
        lines.append(f"C control {label}: planted config chain IoC {r2[k]:.4f}, best of all {max(r2.values()):.4f} ({'planted' if r2[k] >= max(r2.values()) - 1e-12 else 'other'}); null max {n2.max():.4f}")
    txt = chr(10).join(lines)
    open(os.path.join(RES, "partC.txt"), "w", newline=chr(10)).write(txt + chr(10))
    print(txt)


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "c":
    partc(int(sys.argv[sys.argv.index("--reps") + 1]) if "--reps" in sys.argv else 30)
