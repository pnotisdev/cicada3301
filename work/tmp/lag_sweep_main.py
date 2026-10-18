#!/usr/bin/env python
"""Affine lag-feedback autokey sweep over LP2 (sections 0.7-0.15), incl. scope extension.

Hypothesis: within each LP2 word the ciphertext obeys
    c_i = (p_i + a*c_{i-d} + b) mod 29   for i >= d within the scope run,
positions 0..d-1 of each run are free heads. The residual
    r_i = (c_i - a*c_{i-d} - b) mod 29
is then the plaintext p_i at every in-scope position i >= d.

Sweeps:
  - word scope,  d in 1..8, a in 1..28, b in 0..28  -> 8*28*29 = 6496 settings
  - 4 scopes x d in {5,6} x (a,b): word, clause (no '.' crossing), line/page
    (no '\\n'/'%' crossing), all (any consecutive pair inside a section)
    -> 4*2*28*29 = 6496 settings, per scope-lag null of 200 within-section shuffles.

Lemmas (stated in the report):
  L1: for fixed (d,a) and scope, adding b shifts the residual by -b mod 29, so the
      29-count histogram is a cyclic shift: chi2 and IoC are IDENTICAL for all 29 b
      values. Effective multiplicity is 28 per (d,scope); per-b rows are emitted for
      completeness and the null max over 29*b equals the null max over a.
  L2: chi2 of the count histogram is invariant under any fixed permutation of the
      rune alphabet (rotation, Atbash, ...), so no alphabet search is needed.
"""
import math
import os
import random
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "work"))

import lp  # noqa: E402
import numpy as np  # noqa: E402

N = 29
DMIN, DMAX = 1, 8
SEED = 3301
NSHUF = 200
T0 = time.time()


def out(name):
    return os.path.join(HERE, name)


def wr(name, text):
    with open(out(name), "w", encoding="utf-8") as f:
        f.write(text)


def runes(toks):
    return [t for t in toks if isinstance(t, int)]


# ---------------------------------------------------------------- scope runs

def scope_runs(segment_toks, scope):
    """List of (start, end) rune-position runs per scope within one segment.

    word     : boundary at ' ', '.', '&', '#'numeral  (matches lp.word_spans)
    clause   : boundary at '.' only
    linepage : boundary at '\\n' and '%' only
    all      : one run per segment (segment '$' boundaries are hard for all scopes)
    """
    runs, start, pos = [], 0, 0
    for t in segment_toks + [" "]:
        if isinstance(t, int):
            pos += 1
        else:
            if scope == "word":
                is_bound = t.startswith("#") or t in (" ", ".", "&")
            elif scope == "clause":
                is_bound = t == "."
            elif scope == "linepage":
                is_bound = t in ("\n", "%")
            else:  # all
                is_bound = False
            if is_bound:
                if pos > start:
                    runs.append((start, pos))
                start = pos
    if pos > start:
        runs.append((start, pos))
    return runs


def word_runs_via_spans(segment_toks):
    return [(s, e) for _w, s, e in lp.word_spans(segment_toks, runes(segment_toks))]


# ---------------------------------------------------------------- pair plumbing

def build_pairs(seg_rune_lists, runs_list, dset):
    """(C, offsets, lens, PA) over concatenated segments.

    PA[(scope, d)] = (prev_pos, cur_pos) global positions of lag-d pairs whose
    two ends lie in the same scope run. runs_list[si] is the run list of segment si.
    """
    lens = [len(c) for c in seg_rune_lists]
    offsets = np.cumsum([0] + lens)
    per_d = {d: ([], []) for d in dset}
    for si, (c, runs) in enumerate(zip(seg_rune_lists, runs_list)):
        base = int(offsets[si])
        for s, e in runs:
            for d in dset:
                for i in range(s + d, e):
                    per_d[d][0].append(base + i - d)
                    per_d[d][1].append(base + i)
    C = np.concatenate([np.array(c, dtype=np.int16) for c in seg_rune_lists])
    PA = {d: (np.array(a, dtype=np.int32), np.array(b, dtype=np.int32))
          for d, (a, b) in per_d.items()}
    return C, offsets, lens, PA


def cross_pairs(seg_rune_lists, spans_list, d):
    """Within-word positions i whose lag-d predecessor i-d sits in the PREVIOUS
    word (chain did not reset if these obey the same affine law)."""
    prev, cur = [], []
    for c, spans in zip(seg_rune_lists, spans_list):
        for _w, s, e in spans:
            for i in range(s, min(s + d, e)):
                if i - d >= 0:
                    prev.append(c[i - d])
                    cur.append(c[i])
    return np.array(prev, dtype=np.int32), np.array(cur, dtype=np.int32)


# ---------------------------------------------------------------- sweep core

def hist_scores(prev, cur):
    """For each a in 1..28: histogram of (cur - a*prev) mod 29 -> chi2, ioc."""
    n = len(prev)
    if n == 0:
        return np.zeros(N - 1), np.zeros(N - 1)
    a = np.arange(1, N, dtype=np.int16)[:, None]
    t = (cur[None, :].astype(np.int16) - a * prev[None, :].astype(np.int16)) % N
    idx = t + N * np.arange(N - 1, dtype=np.int16)[:, None]
    H = np.bincount(idx.ravel(), minlength=(N - 1) * N).reshape(N - 1, N)
    e = n / N
    chi2 = ((H - e) ** 2 / e).sum(axis=1)
    ioc = (H * (H - 1)).sum(axis=1) / (n * (n - 1) / N) if n > 1 else np.zeros(N - 1)
    return chi2, ioc


def sweep_rows(PA, C, combo):
    d = combo[1]
    p, q = PA[combo] if combo in PA else PA[d]
    if len(p) == 0:
        return []
    chi2, ioc = hist_scores(C[p], C[q])
    rows = [(d, ai + 1, b, float(chi2[ai]), float(ioc[ai]))
            for ai in range(N - 1) for b in range(N)]  # b-invariant (L1)
    rows.sort(key=lambda r: -r[3])
    return rows


def run_null(PA, offsets, lens, C, combos, head_pools, nshuf=NSHUF):
    """One 200-shuffle pass computing, per shuffle, the max chi2 for every combo
    and the chi2 of every head pool. Returns per-combo maxima and per-pool maxima."""
    rng = np.random.default_rng(SEED)
    maxima = {c: [] for c in combos}
    pool_max = {k: [] for k in head_pools}
    t0 = time.time()
    for it in range(nshuf):
        Cs = C.copy()
        for si in range(len(lens)):
            sl = slice(int(offsets[si]), int(offsets[si + 1]))
            Cs[sl] = rng.permutation(Cs[sl])
        for cname in combos:
            p, q = PA[cname]
            chi2, _ = hist_scores(Cs[p], Cs[q])
            maxima[cname].append(float(chi2.max()))
        for k, pos in head_pools.items():
            vals = Cs[pos]
            H = np.bincount(vals.astype(np.int32), minlength=N)
            e = len(vals) / N
            pool_max[k].append(float(((H - e) ** 2 / e).sum()))
        if (it + 1) % 100 == 0:
            print(f"    shuffle {it+1}/{nshuf} @ {time.time()-t0:.1f}s", flush=True)
    return maxima, pool_max


# ---------------------------------------------------------------- echo replication

def echo_check(segments):
    L = ["ECHO REPLICATION (within-word pairs via lp.word_spans, LP2 sections 0.7-0.15)"]
    for d in (5, 6):
        prev, cur = [], []
        for seg in segments:
            c = runes(seg)
            for _w, s, e in lp.word_spans(seg, c):
                for i in range(s + d, e):
                    prev.append(c[i - d])
                    cur.append(c[i])
        n = len(prev)
        exp = n / N
        if d == 6:
            hits = sum(1 for x, y in zip(prev, cur) if y == (24 - 2 * x) % N)
            L.append(f"lag 6, c' = 24-2c mod 29: pairs={n} hits={hits} expected={exp:.2f} "
                     f"excess={hits-exp:+.1f} z_binom={(hits-exp)/math.sqrt(exp*(1-1/N)):+.2f}")
            L.append("  reference (results/analysis/echo_position.txt:21-22): pairs 1290, hits 80, "
                     "expected 44.9, excess +35.1, z +5.16 (shuffle-based)")
        else:
            hits = sum(1 for x, y in zip(prev, cur) if x == y)
            ss = sum(1 for x, y in zip(prev, cur) if x == y == 15)
            exp_ss = n / (N * N)
            L.append(f"lag 5, equality: pairs={n} hits={hits} expected={exp:.2f} "
                     f"excess={hits-exp:+.1f} z_binom={(hits-exp)/math.sqrt(exp*(1-1/N)):+.2f}")
            L.append(f"lag 5, (S,S) pairs: hits={ss} expected={exp_ss:.2f} "
                     f"z_binom={(ss-exp_ss)/math.sqrt(exp_ss):+.2f}")
            L.append("  reference (echo_position.txt:3-4,13-14): pairs 2105, hits 104, expected 72.9, "
                     "z +3.65; (S,S) hits 11, expected 2.4, z +5.86")
    return "\n".join(L)


# ---------------------------------------------------------------- plant

PLANT_IDXS = (1, 5, 16)   # keyed solved sections: Welcome, A Koan (FIRFUM), An End


def build_plant(segs, d, a, b):
    """Encrypt the KEYED solved sections 1/5/16 (plaintext via lp.KNOWN[i][1])
    within their own words with c_i = (p_i + a*c_{i-d} + b) mod 29;
    heads (word positions 0..d-1) random. (Index 6 'An Instruction' is
    unenciphered English and is not used.)"""
    rng = random.Random(SEED)
    plain_segs = [lp.KNOWN[i][1](runes(segs[i])) for i in PLANT_IDXS]
    spans_list = [lp.word_spans(segs[i], runes(segs[i])) for i in PLANT_IDXS]
    c_segs = []
    for plain, spans in zip(plain_segs, spans_list):
        c = list(plain)
        for _w, s, e in spans:
            for j in range(s, min(s + d, e)):
                c[j] = rng.randrange(N)
            for j in range(s + d, e):
                c[j] = (plain[j] + a * c[j - d] + b) % N
        c_segs.append(c)
    return c_segs, spans_list, plain_segs


def plant_report(segs):
    d, a, b = 6, 27, 24
    c_segs, spans_list, plain_segs = build_plant(segs, d, a, b)
    runs_list = [[(s, e) for _w, s, e in sp] for sp in spans_list]
    C, offsets, lens, PA = build_pairs(c_segs, runs_list, {6})
    rows = sweep_rows(PA, C, ("word", 6))
    best = rows[0]
    top_true = [r for r in rows if r[1] == a][0]
    tot = corr = 0
    for c, plain, spans in zip(c_segs, plain_segs, spans_list):
        for _w, s, e in spans:
            for i in range(s + d, e):
                tot += 1
                r = (c[i] - a * c[i - d] - b) % N
                corr += r == plain[i]
    prev, cur = [], []
    for c, spans in zip(c_segs, spans_list):
        for _w, s, e in spans:
            for i in range(s + 6, e):
                prev.append(c[i - 6])
                cur.append(c[i])
    n6 = len(prev)
    hits = sum(1 for x, y in zip(prev, cur) if y == (24 - 2 * x) % N)
    f_frac = sum(1 for p, sp in zip(plain_segs, spans_list)
                 for _w, s, e in sp for i in range(s + d, e) if p[i] == 0) / tot
    tail = [plain[i] for plain, sp in zip(plain_segs, spans_list)
            for _w, s, e in sp for i in range(s + d, e)]
    h = np.bincount(np.array(tail, dtype=np.int32), minlength=N)
    pj = h / h.sum()
    nonunif = float(((pj - 1 / N) ** 2).sum())
    L = [f"POSITIVE CONTROL: planted (d,a,b)=({d},{a},{b}) on the plaintext of the KEYED solved "
         f"sections {PLANT_IDXS} = Welcome (0.1), A Koan FIRFUM (0.5), An End (0.16) "
         f"({sum(len(x) for x in c_segs)} runes; no single keyed solved section has >= 1000 runes, "
         f"so 1+5+16 were concatenated per parent instruction, words never cross section boundaries)",
         f"planted within-word pairs at lag 6: n={n6}",
         f"plant echo (lag 6, c'=24-2c): hits={hits} expected={n6/N:.2f} excess={hits-n6/N:+.1f} "
         f"(LP2-style +35 per ~1290 pairs; plant expectation = n6*28/29*f_F = "
         f"{n6*28/29*f_frac:.1f} at plaintext-F tail frequency {f_frac:.4f})",
         f"recovery of residual = plaintext at in-word positions >= 6: {corr}/{tot} = {corr/tot:.6f}",
         f"top sweep setting on plant: (d,a,b)=({best[0]},{best[1]},{best[2]}) chi2={best[3]:.2f} ioc={best[4]:.2f}",
         f"true setting (6,27,24): chi2={top_true[3]:.2f} ioc={top_true[4]:.2f}",
         f"plant per-pair strength: chi2/n = {top_true[3]/n6:.4f}",
         f"tail plaintext non-uniformity 29*sum(p_j-1/29)^2 = {29*nonunif:.4f}"]
    return "\n".join(L), top_true[3], n6


# ---------------------------------------------------------------- main

def main():
    segs = lp.load_segments()
    lp2 = segs[7:16]                       # segments 0.7 .. 0.15
    lp2_runes = [runes(s) for s in lp2]

    print("=== step 1: echo replication ===", flush=True)
    ech = echo_check(lp2)
    print(ech)
    wr("lag_feedback_echo_replication.txt", ech + "\n")

    # word runs must equal word_spans positions
    for seg in lp2:
        assert scope_runs(seg, "word") == word_runs_via_spans(seg), "word scope mismatch"

    # combo definitions: (scope, d)
    combos = [("word", d) for d in range(DMIN, DMAX + 1)]
    combos += [("clause", d) for d in (5, 6)]
    combos += [("linepage", d) for d in (5, 6)]
    combos += [("all", d) for d in (5, 6)]

    runs_by_scope = {sc: [scope_runs(seg, sc) for seg in lp2]
                     for sc in ("word", "clause", "linepage", "all")}
    C, offsets, lens, PAw = build_pairs(lp2_runes, runs_by_scope["word"], set(range(DMIN, DMAX + 1)))
    PA = {("word", d): PAw[d] for d in range(DMIN, DMAX + 1)}
    for sc in ("clause", "linepage", "all"):
        _C2, _, _, PA2 = build_pairs(lp2_runes, runs_by_scope[sc], {5, 6})
        for d in (5, 6):
            PA[(sc, d)] = PA2[d]
    print("pair counts (scope,lag):",
          {str(c): len(PA[c][0]) for c in combos}, flush=True)

    print("=== step 2: sweep on LP2 ===", flush=True)
    rows_all = {c: sweep_rows(PA, C, c) for c in combos}
    rows = rows_all[("word", 1)]  # placeholder replaced below
    word_rows = []
    for d in range(DMIN, DMAX + 1):
        word_rows.extend(rows_all[("word", d)])
    word_rows.sort(key=lambda r: -r[3])
    rows = word_rows
    wr("lag_feedback_sweep_top_lp2.txt",
       "\n".join(f"d={r[0]:d} a={r[1]:2d} b={r[2]:2d} chi2={r[3]:8.2f} ioc={r[4]:.4f}" for r in rows[:10]))
    print("top 10 on LP2 (word scope, d 1..8):")
    for r in rows[:10]:
        print(f"  d={r[0]} a={r[1]:2d} b={r[2]:2d} chi2={r[3]:8.2f} ioc={r[4]:.4f}")

    special = [(6, 27, 24, "lag-6 echo c'=24-2c (p=0 branch)"),
               (5, 28, 1, "lag-5 S-pin (1-a)*15-b=0 example")]
    for d, a, b, tag in special:
        r0 = [r for r in rows if r[0] == d and r[1] == a and r[2] == b][0]
        print(f"  special [{tag}]: chi2={r0[3]:.2f} ioc={r0[4]:.3f}")

    # head pools for the probe: pooled heads per d, word-initial, word-final
    spans_list = [lp.word_spans(seg, runes(seg)) for seg in lp2]
    head_pools = {}
    for d in range(DMIN, DMAX + 1):
        pos = []
        for si, spans in enumerate(spans_list):
            base = int(offsets[si])
            for _w, s, e in spans:
                pos.extend(range(base + s, base + min(s + d, e)))
        head_pools[f"head_d{d}"] = np.array(pos, dtype=np.int32)
    ipos, fpos = [], []
    for si, spans in enumerate(spans_list):
        base = int(offsets[si])
        for _w, s, e in spans:
            ipos.append(base + s)
            fpos.append(base + e - 1)
    head_pools["word_initial"] = np.array(ipos, dtype=np.int32)
    head_pools["word_final"] = np.array(fpos, dtype=np.int32)

    print("=== step 3: 200 within-section shuffles (all combos + head pools) ===", flush=True)
    maxima, pool_max = run_null(PA, offsets, lens, C, combos, head_pools, NSHUF)
    # word-scope original null = per-shuffle max over d in 1..8
    word_null = [max(maxima[("word", d)][i] for d in range(DMIN, DMAX + 1))
                 for i in range(NSHUF)]
    ws = sorted(word_null)
    null_max, null_mean = ws[-1], sum(ws) / len(ws)
    null_p99 = ws[min(NSHUF - 1, int(0.99 * NSHUF))]
    ntxt = ["null calibration, 200 within-section shuffles, same runs, same 6496-setting sweep",
            f"WORD scope d 1..8: null max chi2 = {null_max:.2f}, mean = {null_mean:.2f}, "
            f"p99 = {null_p99:.2f}", "per-shuffle maxima (word scope, max over d,a):"]
    ntxt += [f"{i+1:3d} {m:8.2f}" for i, m in enumerate(word_null)]
    ntxt.append("per-combo null stats (scope,lag: max / mean / p99):")
    for cname in combos:
        ms = sorted(maxima[cname])
        ntxt.append(f"  {cname[0]:8s} d={cname[1]}  n={len(PA[cname][0]):6d}  "
                    f"max={ms[-1]:7.2f}  mean={sum(ms)/len(ms):6.2f}  p99={ms[min(NSHUF-1, int(0.99*NSHUF))]:7.2f}")
    wr("lag_feedback_null_shuffles.txt", "\n".join(ntxt) + "\n")
    print(f"null word scope: max={null_max:.2f} mean={null_mean:.2f} p99={null_p99:.2f}", flush=True)

    print("=== extension: scope sweep (clause/linepage/all, d 5-6) ===", flush=True)
    ext_lines = ["SCOPE EXTENSION: same affine sweep with 4 pair scopes x d in {5,6}; "
                 "200-shuffle null per scope-lag combo.",
                 "scopes: word (boundary at ' ','.','&','#'), clause (boundary at '.'), "
                 "linepage (boundary at '\\n','%'), all (any consecutive pair inside a section).",
                 "chi2 is b-invariant (L1) so 28 distinct scores per (scope,lag); b rows kept for spec compliance."]
    for cname in combos:
        if cname[0] == "word" and cname[1] not in (5, 6):
            continue
        top = rows_all[cname][0]
        ms = sorted(maxima[cname])
        ext_lines.append(
            f"scope={cname[0]:8s} d={cname[1]}  n={len(PA[cname][0]):6d}  top chi2={top[3]:8.2f} "
            f"at (a,b)=({top[1]},{top[2]}) ioc={top[4]:.4f}   null max={ms[-1]:7.2f} "
            f"mean={sum(ms)/len(ms):6.2f} p99={ms[min(NSHUF-1, int(0.99*NSHUF))]:7.2f}")
        for r in rows_all[cname][1:3]:
            ext_lines.append(f"        next: (a,b)=({r[1]},{r[2]}) chi2={r[3]:8.2f} ioc={r[4]:.4f}")
    ext_text = "\n".join(ext_lines)
    wr("lag_feedback_scope_extension.txt", ext_text + "\n")
    print(ext_text)

    print("=== step 4: positive control plant ===", flush=True)
    ptext, pchi, pn = plant_report(segs)
    print(ptext)
    wr("lag_feedback_plant.txt", ptext + "\n")

    print("=== step 5: real-data nulls on the keyed solved sections 1, 5, 16 ===", flush=True)
    atxt = ["REAL-DATA NULLS: same sweep on the KEYED solved sections (own word cuts each).",
            "0.6 'An Instruction' is unenciphered English (KNOWN[6] = identity, work/lp.py:331) "
            "and is NOT used. Local null = 200 shuffles of the section's runes, same word cuts, "
            "same 6496 settings."]
    for i in (1, 5, 16):
        seg = segs[i]
        cr = [runes(seg)]
        runs_i = [scope_runs(seg, "word")]
        Ci, oi, li, Pi = build_pairs(cr, runs_i, set(range(DMIN, DMAX + 1)))
        arows = sorted([r for d in range(DMIN, DMAX + 1) for r in
                        sweep_rows(Pi, Ci, ("word", d))], key=lambda r: -r[3])
        rng = np.random.default_rng(SEED + i)
        ms = []
        for _it in range(200):
            Cs = rng.permutation(Ci)
            m = -1.0
            for d in range(DMIN, DMAX + 1):
                p, q = Pi[d]
                if len(p) == 0:
                    continue
                chi2, _ = hist_scores(Cs[p], Cs[q])
                m = max(m, float(chi2.max()))
            ms.append(m)
        mss = sorted(ms)
        atxt.append(
            f"\n0.{i} {lp.KNOWN[i][0]} ({len(cr[0])} runes; rule: {lp.KNOWN[i][1]!r}): "
            f"max chi2 over 6496 settings = {arows[0][3]:.2f} at "
            f"(d,a,b)=({arows[0][0]},{arows[0][1]},{arows[0][2]}); "
            f"local null max={mss[-1]:.2f} mean={sum(ms)/len(ms):.2f} p99="
            f"{mss[min(199, int(0.99*200))]:.2f}")
        atxt += [f"    top 5: " + "; ".join(
            f"(d={r[0]},a={r[1]},b={r[2]}) chi2={r[3]:.1f}" for r in arows[:5])]
    atext = "\n".join(atxt)
    wr("lag_feedback_an_end.txt", atext + "\n")
    print(atext)

    # ---- candidate logic (word scope per original decision rule + extension)
    top = rows[0]
    verdict = "excluded"
    cand_txt = None
    if top[3] > null_max:
        verdict = "CANDIDATE"
        d, a, b = top[0], top[1], top[2]
        dec = []
        wid = 0
        for c, spans in zip(lp2_runes, spans_list):
            for w, s, e in spans:
                wid += 1
                if e - s <= d:
                    continue
                r = [(c[i] - a * c[i - d] - b) % N for i in range(s + d, e)]
                dec.append(f"[w{wid} {''.join(lp.LATIN[x] for x in c[s:e])}] -> "
                           f"{''.join(lp.LATIN[x] for x in r)}")
        pv, cu = cross_pairs(lp2_runes, spans_list, d)
        rv = (cu.astype(np.int32) - a * pv.astype(np.int32) - b) % N
        Hc = np.bincount(rv, minlength=N)
        ec = len(rv) / N
        cross_chi2 = float(((Hc - ec) ** 2 / ec).sum()) if len(rv) else float("nan")
        cand_txt = (f"CANDIDATE (d,a,b)=({d},{a},{b}) chi2={top[3]:.2f} ioc={top[4]:.3f} "
                    f"(null max {null_max:.2f})\n"
                    f"cross-word-boundary residual chi2 for the same setting: {cross_chi2:.2f} "
                    f"over {len(pv)} pairs (null-like if the chain resets per word)\n\n"
                    + "\n".join(dec))
        wr("lag_feedback_candidate_decode.txt", cand_txt + "\n")
        print(cand_txt[:3000])
    else:
        d, a, b = top[0], top[1], top[2]
        pv, cu = cross_pairs(lp2_runes, spans_list, d)
        if len(pv):
            rv = (cu.astype(np.int32) - a * pv.astype(np.int32) - b) % N
            Hc = np.bincount(rv, minlength=N)
            ec = len(rv) / N
            cross_chi2 = float(((Hc - ec) ** 2 / ec).sum())
            print(f"top setting cross-word-boundary residual chi2: {cross_chi2:.2f} over {len(pv)} pairs")
    # extension combos vs their own nulls
    ext_beats = []
    for cname in combos:
        if cname[0] == "word" and cname[1] not in (5, 6):
            continue
        t = rows_all[cname][0]
        ms = sorted(maxima[cname])
        if t[3] > ms[-1]:
            ext_beats.append((cname, t[3], ms[-1]))
    print(f"extension combos beating own null max: {ext_beats}", flush=True)

    print("=== head structure probe ===", flush=True)
    hp_lines = ["WORD-HEAD / EDGE PROBE (LP2, positions fixed, 200-shuffle null for each pool):",
                "pooled head runes = word positions 0..d-1 for every word with len >= d+1 cut at word end;",
                "word_initial = first rune of each word; word_final = last rune of each word."]
    for d in range(DMIN, DMAX + 1):
        k = f"head_d{d}"
        vals = C[head_pools[k]]
        H = np.bincount(vals.astype(np.int32), minlength=N)
        e = len(vals) / N
        chi2 = float(((H - e) ** 2 / e).sum())
        iocv = lp.ioc([int(v) for v in vals])
        pm = sorted(pool_max[k])
        hp_lines.append(f"d={d}  n={len(vals):5d}  ioc={iocv:.3f}  chi2_vs_uniform={chi2:6.2f}  "
                        f"null max={pm[-1]:6.2f}  mean={sum(pm)/len(pm):5.2f}")
    for k in ("word_initial", "word_final"):
        vals = C[head_pools[k]]
        H = np.bincount(vals.astype(np.int32), minlength=N)
        e = len(vals) / N
        chi2 = float(((H - e) ** 2 / e).sum())
        iocv = lp.ioc([int(v) for v in vals])
        pm = sorted(pool_max[k])
        hp_lines.append(f"{k:13s}  n={len(vals):5d}  ioc={iocv:.3f}  chi2_vs_uniform={chi2:6.2f}  "
                        f"null max={pm[-1]:6.2f}  mean={sum(pm)/len(pm):5.2f}")
    hp_text = "\n".join(hp_lines)
    wr("lag_feedback_head_probe.txt", hp_text + "\n")
    print(hp_text)

    print("=== step 7: nonlinear feedback, d=6 (word scope) ===", flush=True)
    INV = [0] + [pow(x, N - 2, N) for x in range(1, N)]
    NF = {"x^2": np.array([(x * x) % N for x in range(N)], dtype=np.int16),
          "x^3": np.array([(x * x * x) % N for x in range(N)], dtype=np.int16),
          "x^-1": np.array(INV, dtype=np.int16),
          "2^x": np.array([pow(2, x, N) for x in range(N)], dtype=np.int16),
          "3^x": np.array([pow(3, x, N) for x in range(N)], dtype=np.int16)}
    p6, q6 = PA[("word", 6)]

    def nhist(prev, cur, tab):
        n = len(cur)
        t = (cur.astype(np.int16) - tab[prev]) % N
        H = np.bincount(t, minlength=N)
        e = n / N
        return float(((H - e) ** 2 / e).sum())

    nf_lines = ["nonlinear feedback, d=6 (word scope): r = (c_i - f(c_{i-6}) - b) mod 29, b swept 0..28",
                "(chi2 is b-invariant here too: b shifts the residual histogram cyclically)",
                f"LP2 within-word pairs at lag 6: n={len(p6)}"]
    nf_best = -1.0
    for name, tab in NF.items():
        chi2 = nhist(C[p6], C[q6], tab)
        nf_lines.append(f"  f={name:4s}  chi2={chi2:8.2f}")
        if chi2 > nf_best:
            nf_best = chi2
    rng = np.random.default_rng(SEED + 7)
    nf_maxima = []
    for it in range(50):
        Cs = C.copy()
        for si in range(len(lens)):
            sl = slice(int(offsets[si]), int(offsets[si + 1]))
            Cs[sl] = rng.permutation(Cs[sl])
        m = max(nhist(Cs[p6], Cs[q6], tab) for tab in NF.values())
        nf_maxima.append(m)
    nf_sorted = sorted(nf_maxima)
    nf_lines.append(f"null (50 shuffles, max over 5 functions x 29 b): "
                    f"max={nf_sorted[-1]:.2f} mean={sum(nf_maxima)/len(nf_maxima):.2f} "
                    f"p99={nf_sorted[min(49, int(0.99*50))]:.2f}")
    nf_lines.append(f"LP2 best nonlinear chi2 = {nf_best:.2f} vs null max {nf_sorted[-1]:.2f}")
    nf_text = "\n".join(nf_lines)
    wr("lag_feedback_nonlinear.txt", nf_text + "\n")
    print(nf_text)

    print("=== verdict ===", flush=True)
    print(f"top LP2 chi2 (word scope) = {top[3]:.2f}  null max = {null_max:.2f}  "
          f"plant chi2 = {pchi:.2f} (plant n6={pn})  ->  {verdict}", flush=True)
    print(f"elapsed {time.time()-T0:.1f}s", flush=True)
    return top, null_max, pchi, pn, verdict


if __name__ == "__main__":
    main()
