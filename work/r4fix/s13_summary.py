"""s13 summary: reads results/r4fix/s13_tsites/raw_*.json, writes summary.txt (called by `s13_tsites.py summary`)."""
import json
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "..", "results", "r4fix", "s13_tsites")
N = 29
SIMS = ["R0", "R0n", "R1", "R4", "R4int", "R3", "R7", "plant"]


def load(n):
    p = os.path.join(OUT, "raw_%s.json" % n)
    return json.load(open(p)) if os.path.exists(p) else None


def Z(r):
    H, E, V = np.array(r["H"]), np.array(r["E"]), np.array(r["V"])
    return np.where(V > 0, (H - E) / np.sqrt(np.maximum(V, 1e-12)), 0.0)


def arr(rs, f):
    return np.array([f(r) for r in rs], float)


def ms(x):
    return "%.2f +/- %.2f" % (np.mean(x), np.std(x, ddof=1))


def pge(x, v):
    return (np.sum(np.asarray(x) >= v - 1e-9) + 1) / (len(x) + 1)


def ple(x, v):
    return (np.sum(np.asarray(x) <= v + 1e-9) + 1) / (len(x) + 1)


def main():
    L = load("lp2")
    if L is None:
        raise SystemExit("run lp2 first")
    lp = L["lp2"]
    sets = {"within-word shuffle (2000)": L["within_word"], "word-order shuffle (300)": L["word_order"]}
    for n in SIMS:
        d = load(n)
        if d:
            sets["%s (%d reps)" % (n, d["reps"])] = d["results"]
    keys = list(sets)
    w = []
    P = w.append
    P("s13 summary: LP2 T sites (c_j = T(c_(j-6)), T(c) = 24 - 2c mod 29) and the T grid.  Keyless; nothing decrypted.")
    P("Nothing in LP2 is solved.  Sources: LP2's own runes (layout and statistics) and r4sim replicates / shuffles of them.")
    P("Replicates: LP2 section lengths, English word lengths, uniform plaintext and key (flat cipher), presets documented in s13_tsites.py PRESETS.")
    P("")
    t = lp["t"]
    z = Z(lp)
    P("== reproduction (positive control for the statistic)")
    P("LP2 in-word lag-6 cell: %d hits / %d pairs, expected %.2f, z %+.2f (07_signal_math: 80 / 1290 / 44.47 / +5.42)" % (lp["H"][6][0], lp["NP"][6][0], lp["E"][6][0], z[6][0]))
    P("LP2 (5,1): %d hits / %d pairs, expected %.1f, z %+.2f (07: 307 / 7369 / 254.2 / +3.37).  LP2 doublets in words / across gaps %d / %d (63 / 23)"
      % (lp["H"][5][1], lp["NP"][5][1], lp["E"][5][1], z[5][1], t["dbl_in"], t["dbl_gap"]))
    P("")
    P("replicate sets: mean words, mean in-word T sites (LP2 80 in %d words), in-word doublets / gap doublets (LP2 63 / 23)" % t["n_words"])
    for k in keys:
        rs = sets[k]
        P("  %-28s words %7.1f  sites %6.2f +/- %5.2f  doublets in/gap %5.1f / %5.1f  lag-6 z %+.2f" % (
            k, arr(rs, lambda r: r["t"]["n_words"]).mean(), arr(rs, lambda r: r["t"]["n_sites"]).mean(), arr(rs, lambda r: r["t"]["n_sites"]).std(ddof=1),
            arr(rs, lambda r: r["t"]["dbl_in"]).mean(), arr(rs, lambda r: r["t"]["dbl_gap"]).mean(), arr(rs, lambda r: Z(r)[6][0]).mean()))
    P("")

    # ---------------------------------------------------------------- item 21
    P("== ITEM 21: doublets at the T sites (c_j == c_(j-1))")
    P("LP2: %d T sites, %d with c_j == c_(j-1).  In-word pairs at word position >= 6: %d, doublets among them %d (rate %.4f) -> expected at 80 sites under 'T sites are ordinary pairs of LP2': %.2f"
      % (t["n_sites"], t["n_dbl"], t["n_pairs"], t["n_dbl_pos6"], t["dbl_rate_pos6"], t["n_sites"] * t["dbl_rate_pos6"]))
    P("R4 semantics: a T repair writes T(c[-6]) only when != prev, so a repair site is never a doublet; a chance T pair is a doublet only as an unrepaired collision.")
    P("%-28s %9s %10s %8s %12s %11s | %s" % ("set", "sites", "doublets", "per site", "x80 sites", "P(<=%d)" % t["n_dbl"], "of which true repair sites / doublets there / chance sites' doublets"))
    for k in keys:
        rs = sets[k]
        ns, nd = arr(rs, lambda r: r["t"]["n_sites"]), arr(rs, lambda r: r["t"]["n_dbl"])
        extra = ""
        if "n_true_repair_sites" in rs[0]["t"]:
            extra = "%.1f / %.2f / %.2f" % (arr(rs, lambda r: r["t"]["n_true_repair_sites"]).mean(), arr(rs, lambda r: r["t"]["n_dbl_true_repair"]).mean(),
                                            arr(rs, lambda r: r["t"]["n_dbl_chance"]).mean())
        # P(<= LP2) as a per-replicate share, and binomial at the pooled per-site rate over 80 sites
        rate = nd.sum() / ns.sum()
        pb = sum(math.comb(80, i) * rate ** i * (1 - rate) ** (80 - i) for i in range(t["n_dbl"] + 1))
        P("%-28s %9.2f %10.3f %8.4f %12.2f %11.3f | %s   [Bin(80, rate) P(<=obs) %.3f; replicates with 0 doublets %.3f]" % (
            k, ns.mean(), nd.mean(), rate, 80 * rate, ple(nd, t["n_dbl"]), extra, pb, np.mean(nd == 0)))
    P("")

    # ---------------------------------------------------------------- item 22
    P("== ITEM 22: source rune c_(j-6) of the T sites")
    sc = np.array(t["src_counts"])
    P("LP2 source counts by rune index (F=0 .. EA=28): %s" % " ".join(str(x) for x in sc))
    P("LP2: distinct sources %d, max count %d, chi2 vs flat (n/29 each) %.1f (28 dof; flat mean 28 +/- 7.5), sum of squares %d (flat expectation n + n(n-1)/29 = %.0f for n = %d)"
      % (t["src_distinct"], t["src_max"], t["src_chi2"], t["src_sumsq"], 80 + 80 * 79 / 29, t["n_sites"]))
    P("(phase 54's 'sum of squares 298 vs 118' compared 80 hits with a 45-hit null: 298 IS the flat expectation for 80 hits, so it is not an excess.)")
    P("%-28s %18s %18s %18s | P(set >= LP2): chi2, max, distinct<=" % ("set", "chi2 vs flat", "max count", "distinct"))
    for k in keys:
        rs = sets[k]
        c2, mx, ds = arr(rs, lambda r: r["t"]["src_chi2"]), arr(rs, lambda r: r["t"]["src_max"]), arr(rs, lambda r: r["t"]["src_distinct"])
        P("%-28s %18s %18s %18s | %.3f %.3f %.3f" % (k, ms(c2), ms(mx), ms(ds), pge(c2, t["src_chi2"]), pge(mx, t["src_max"]), ple(ds, t["src_distinct"])))
    P("")

    # ---------------------------------------------------------------- item 23
    P("== ITEM 23: distance of the T site's last rune from the word end (0 = word-final rune), bins 0 1 2 3 4 5+")
    dc = np.array(t["d_counts"]); dp = np.array(t["d_pairs"]); de = np.array(t["d_exp"])
    P("LP2 T sites by distance      : %s   (total %d; word-final share %.3f)" % (" ".join("%3d" % x for x in dc), dc.sum(), dc[0] / dc.sum()))
    P("LP2 in-word lag-6 pairs      : %s" % " ".join("%4d" % x for x in dp))
    P("LP2 chance expectation (pairs x f[T(c_src)]): %s  (sum %.1f)" % (" ".join("%5.1f" % x for x in de), de.sum()))
    for k in keys:
        rs = sets[k]
        D = np.array([r["t"]["d_counts"] for r in rs], float)
        m, s = D.mean(0), D.std(0, ddof=1)
        P("%-28s mean %s | word-final %5.1f +/- %4.1f  LP2 z %+.2f  P(>=%d) %.3f  P(<=%d) %.3f | share %.3f" % (
            k, " ".join("%5.1f" % x for x in m), m[0], s[0], (dc[0] - m[0]) / s[0], dc[0], pge(D[:, 0], dc[0]), dc[0], ple(D[:, 0], dc[0]),
            D[:, 0].sum() / D.sum()))
    # R4 split by true repair vs chance
    for k in keys:
        rs = sets[k]
        if "d_counts_repair" in rs[0]["t"] and (k.startswith("R4 ") or k.startswith("R3") or k.startswith("R7") or k.startswith("plant")):
            Dr = np.array([r["t"]["d_counts_repair"] for r in rs], float); Dc = np.array([r["t"]["d_counts_chance"] for r in rs], float)
            P("   %-26s true-repair sites by distance %s | chance sites %s" % (k, " ".join("%5.1f" % x for x in Dr.mean(0)), " ".join("%5.1f" % x for x in Dc.mean(0))))
    # other bins z
    P("LP2 minus replicate mean, in sd, per bin (0..5+):")
    for k in keys:
        D = np.array([r["t"]["d_counts"] for r in sets[k]], float)
        P("   %-28s %s" % (k, " ".join("%+.2f" % ((dc[i] - D[:, i].mean()) / D[:, i].std(ddof=1)) for i in range(len(dc)))))
    P("")

    # ---------------------------------------------------------------- grid
    P("== ITEMS 19-20: T grid.  Cell (g, k): rune lag g, k word gaps crossed (same section).  Entry = LP2 hits / expected (z).")
    P("Expected uses LP2's own unigrams f[T(c_i)] (replicates: their own).  LP2 table:")
    P("  g\\k " + "".join("%24d" % k for k in range(5)))
    cells = []
    for g in range(1, 13):
        row = "  %2d  " % g
        for k in range(5):
            if lp["NP"][g][k] > 0:
                row += "%7d/%7.1f (%+5.2f) " % (lp["H"][g][k], lp["E"][g][k], z[g][k])
            else:
                row += "%24s" % "-"
            if lp["NP"][g][k] >= 200 and not (g == 6 and k == 0):
                cells.append((g, k))
        P(row)
    P("cells with >= 200 LP2 pairs, excluding (6,0): %d (07_signal_math counted 47 by a different rule)" % len(cells))
    zl = np.array([z[g][k] for g, k in cells])
    ib = int(np.argmax(zl))
    P("LP2 largest z among those cells: %+.2f at (lag %d, gaps %d); second %+.2f" % (zl[ib], cells[ib][0], cells[ib][1], np.sort(zl)[-2]))
    P("")
    focus = [(6, 0), (5, 1), (9, 0), (3, 0), (7, 0), (5, 0), (6, 1), (4, 2)]
    P("focus cells: LP2 z vs each replicate set's z (mean +/- sd) and P(set z >= LP2 z); excess = mean(hits - expected)")
    P("%-28s " % "set" + "".join("%-30s" % ("(%d,%d) LP2 z %+.2f" % (g, k, z[g][k])) for g, k in focus))
    for k in keys:
        rs = sets[k]
        Zs = np.array([Z(r) for r in rs]); Ex = np.array([np.array(r["H"]) - np.array(r["E"]) for r in rs])
        row = "%-28s " % k
        for g, kk in focus:
            x = Zs[:, g, kk]
            row += "%-30s" % ("%+.2f+/-%.2f P%.3f ex%+.1f" % (x.mean(), x.std(ddof=1), pge(x, z[g][kk]), Ex[:, g, kk].mean()))
        P(row)
    P("")
    P("max over the %d comparison cells of the T-cell z, per set (LP2 %+.2f): mean, 95th pct, P(set max >= LP2 max), P(set max >= 3.37)" % (len(cells), zl.max()))
    for k in keys:
        Zs = np.array([Z(r) for r in sets[k]])
        mx = np.array([max(Zs[i][g][kk] for g, kk in cells) for i in range(len(Zs))])
        P("   %-28s %.2f  %.2f  %.3f  %.3f" % (k, mx.mean(), np.percentile(mx, 95), pge(mx, zl.max()), np.mean(mx >= 3.37)))
    P("")
    P("planted control and nulls on the (5,1) cell: share of replicates with z(5,1) >= LP2's %+.2f (power of the plant / null rate)" % z[5][1])
    for k in keys:
        Zs = np.array([Z(r)[5][1] for r in sets[k]])
        Ex = np.array([r["H"][5][1] - r["E"][5][1] for r in sets[k]])
        P("   %-28s share %.3f  mean z %+.2f  mean excess %+.1f (target for the plant: LP2 +%.1f)" % (k, np.mean(Zs >= z[5][1]), Zs.mean(), Ex.mean(), lp["H"][5][1] - lp["E"][5][1]))
    P("planted cross-gap repairs per replicate: %s" % ms(arr(sets[[k for k in keys if k.startswith("plant")][0]], lambda r: r["n_cross"])) if any(k.startswith("plant") for k in keys) else "")
    P("")

    # ---------------------------------------------------------------- affine maxima
    P("max z over the 812 affine forms c' = a c + b of in-word pairs, per rune lag (LP2 | set mean | P(set >= LP2)); the T form is (27, 24)")
    P("%-28s " % "set" + "".join("%12d" % g for g in range(1, 13)))
    P("%-28s " % "LP2 (z of max form)" + "".join("%12.2f" % lp["maxz"][g] for g in range(1, 13)))
    P("%-28s " % "LP2 form (a,b)" + "".join("%12s" % str(__import__("itertools").islice(((a, b) for a in range(1, 29) for b in range(29)), lp["maxform"][g], None).__next__()) for g in range(1, 13)))
    P("%-28s " % "LP2 z of the T form" + "".join("%12.2f" % lp["tz"][g] for g in range(1, 13)))
    for k in keys:
        M = np.array([r["maxz"] for r in sets[k]])
        P("%-28s " % (k + " mean") + "".join("%12.2f" % M[:, g].mean() for g in range(1, 13)))
        P("%-28s " % "   P(set >= LP2)" + "".join("%12.3f" % pge(M[:, g], lp["maxz"][g]) for g in range(1, 13)))
    P("")
    P("max over lags != 6 of the affine-form maxima: LP2 %.2f (lag %d); P(set >= LP2)" % (max(lp["maxz"][g] for g in range(1, 13) if g != 6),
      max((g for g in range(1, 13) if g != 6), key=lambda g: lp["maxz"][g])))
    ref = max(lp["maxz"][g] for g in range(1, 13) if g != 6)
    for k in keys:
        M = np.array([r["maxz"] for r in sets[k]])
        mx = np.max(np.delete(M[:, 1:], 5, axis=1), axis=1)
        P("   %-28s mean %.2f  P(>= LP2) %.3f" % (k, mx.mean(), pge(mx, ref)))

    # ---------------------------------------------------------------- addenda
    P("")
    P("== ADDENDUM A: word-final plus penultimate (distance 0 or 1) T sites: LP2 %d of 80 (share %.3f)" % (dc[0] + dc[1], (dc[0] + dc[1]) / dc.sum()))
    for k in keys:
        D = np.array([r["t"]["d_counts"] for r in sets[k]], float)
        x = D[:, 0] + D[:, 1]
        if x.std() > 0:
            P("   %-28s %.1f +/- %.1f  LP2 z %+.2f  P(>= LP2) %.3f  share %.3f" % (k, x.mean(), x.std(ddof=1), (dc[0] + dc[1] - x.mean()) / x.std(ddof=1), pge(x, dc[0] + dc[1]), x.sum() / D.sum()))
    P("")
    P("== ADDENDUM B: the whole lag-5 row (excess = hits - expected, z) for LP2 and the planted control; cells (5,k), k = 0..4")
    P("   LP2                          " + "  ".join("%+6.1f (%+.2f)" % (lp["H"][5][k] - lp["E"][5][k], z[5][k]) for k in range(5)))
    for k in keys:
        if k.startswith(("plant", "R4 ", "R3", "within")):
            Zs = np.array([Z(r) for r in sets[k]]); Ex = np.array([np.array(r["H"]) - np.array(r["E"]) for r in sets[k]])
            P("   %-28s " % k + "  ".join("%+6.1f (%+.2f)" % (Ex[:, 5, kk].mean(), Zs[:, 5, kk].mean()) for kk in range(5)))
    P("== ADDENDUM C: second-largest LP2 comparison-cell z (%+.2f at lag 9, gaps 0): P(set second-largest >= it)" % np.sort(zl)[-2])
    for k in keys:
        Zs = np.array([Z(r) for r in sets[k]])
        sec = np.array([np.sort([Zs[i][g][kk] for g, kk in cells])[-2] for i in range(len(Zs))])
        P("   %-28s mean %.2f  P %.3f" % (k, sec.mean(), pge(sec, np.sort(zl)[-2])))
    P("(lags 10-12 in-word have about 90 / 35 / 10 pairs; a z of a handful of hits is not a Gaussian, so the lag-12 form maximum of 6.35 is a small-count artefact: P(set >= LP2) 0.02-0.08 in every set.)")
    open(os.path.join(OUT, "summary.txt"), "w", encoding="utf-8").write("\n".join(w) + "\n")
    print("\n".join(w))


if __name__ == "__main__":
    main()
