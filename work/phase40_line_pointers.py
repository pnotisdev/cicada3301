"""Phase 40: the book's own numbers read as line:position pointers into Liber Primus's own lines.
Preregistration is section 0 of work/log/phase40_line_pointers.md (written before the real run).

    python work/phase40_line_pointers.py count            # counts N readings, no scoring
    python work/phase40_line_pointers.py real             # real screen
    python work/phase40_line_pointers.py null  <runs> <seed0>   # whole-screen null (max z per run), 1 core
    python work/phase40_line_pointers.py plant            # positive control, power per pointer count
    python work/phase40_line_pointers.py selftest
Never more than 2 processes at once (CPU is shared with a long queue).
"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402
import grid30  # noqa: E402

SEGS = lp.load_segments()
REF = os.path.join(HERE, "ref")
NBOOT = 60
MIN_VALID = 0.9
MIN_TRI = 6


# ------------------------------------------------------------------ language model (same corpora as phase 31)
def gutenberg(path):
    t = open(path, encoding="utf-8", errors="ignore").read()
    a, b = t.find("*** START"), t.find("*** END")
    return t[t.find("\n", a) + 1:b] if a >= 0 and b > a else t


def _english():
    txt = ""
    for f in ("pg1497.txt", "pg2009.txt", "pg205.txt", "pg3800.txt"):
        txt += gutenberg(os.path.join(REF, "corpora", f))
    return np.array([ord(c) - 65 for c in re.sub(r"[^A-Z]", "", txt.upper())], np.int16)


ENG = _english()
C3 = np.full((26, 26, 26), 0.5)
np.add.at(C3, (ENG[:-2], ENG[1:-1], ENG[2:]), 1)
T3 = np.log(C3 / C3.sum(2, keepdims=True))


def tri_mean(s):
    """mean trigram log-likelihood over fully valid trigrams of letter array s (-1 = break); (mean, n)."""
    a, b, c = s[:-2], s[1:-1], s[2:]
    m = (a >= 0) & (b >= 0) & (c >= 0)
    n = int(m.sum())
    return (float(T3[a[m], b[m], c[m]].mean()) if n else 0.0), n


# ------------------------------------------------------------------ targets
LAT = [[ord(ch) - 65 for ch in l] for l in lp.LATIN]
E3 = np.full((30, 3), -2, np.int16)               # rune code -> up to 3 Latin letters; 29 (space) -> break
for i, ls in enumerate(LAT):
    E3[i, :len(ls)] = ls
E3[29, 0] = -1
SP = 29


def book_lines():
    """[(page, kind, tokens)] kind 'raw' (cipher as printed). Lines end at '\\n', '&', '%' or segment end; numerals skipped."""
    lines, page = [], 0
    for si, toks in enumerate(SEGS):
        cur = []
        for t in toks + ["&"]:
            if isinstance(t, int):
                cur.append(t)
            elif t in (" ", "."):
                cur.append(SP)
            elif t in ("\n", "&", "%"):
                if any(x != SP for x in cur):
                    lines.append((page, si, cur))
                cur = []
                if t == "%":
                    page += 1
    return lines


def solved_lines():
    """plaintext runes in the line layout of the ciphertext, for the solved segments."""
    out = []
    page = 0
    pg_of = {}
    for si, toks in enumerate(SEGS):
        for t in toks:
            if t == "%":
                page += 1
            pg_of.setdefault(si, page)
    lines, page = [], 0
    for si, toks in enumerate(SEGS):
        known = si in lp.KNOWN
        plain = lp.KNOWN[si][1](lp.runes_of(toks)) if known else None
        k = 0
        cur = []
        for t in toks + ["&"]:
            if isinstance(t, int):
                if known:
                    cur.append(plain[k])
                k += 1
            elif t in (" ", "."):
                cur.append(SP)
            elif t in ("\n", "&", "%"):
                if known and any(x != SP for x in cur):
                    lines.append((page, si, cur))
                cur = []
                if t == "%":
                    page += 1
    return lines


class Target:
    def __init__(self, name, lines, unit, sep):
        self.name = name
        arrs = []
        for ln in lines:
            if not sep:
                ln = [x for x in ln if x != SP]
            if unit == "latin":
                ln = [c for x in ln for c in ([26] if x == SP else LAT[x])]
            arrs.append(np.array(ln, np.int16))
        arrs = [a for a in arrs if len(a)]
        self.unit = unit
        self.lens = np.array([len(a) for a in arrs])
        self.starts = np.concatenate([[0], np.cumsum(self.lens)[:-1]])
        self.X = np.concatenate(arrs)
        self.nl = len(arrs)
        self.line_of = np.repeat(np.arange(self.nl), self.lens)

    def resolve(self, cols, flat, lineinit):
        """cols: tuple of int arrays (0-based). Returns code array, -1 where the pointer is out of range."""
        if flat:
            (i,) = cols
            ok = (i >= 0) & (i < len(self.X))
            return np.where(ok, self.X[np.clip(i, 0, len(self.X) - 1)], -1)
        if lineinit:
            (l,) = cols
            p = np.zeros_like(l)
        else:
            l, p = cols
        ok = (l >= 0) & (l < self.nl)
        lc = np.clip(l, 0, self.nl - 1)
        ok &= (p >= 0) & (p < self.lens[lc])
        return np.where(ok, self.X[np.clip(self.starts[lc] + p, 0, len(self.X) - 1)], -1)

    def letters(self, res):
        """-> Latin letter array, -1 = break."""
        if self.unit == "latin":
            return np.where((res >= 26) | (res < 0), -1, res)
        e = np.where(res[:, None] >= 0, E3[np.clip(res, 0, 29)], -1).ravel()
        return e[e != -2]


def build_targets():
    L = book_lines()
    S = solved_lines()
    groups = {}
    groups["book"] = [x[2] for x in L]
    groups["LP2"] = [x[2] for x in L if 7 <= x[1] <= 15]
    groups["solved"] = [x[2] for x in S]
    pages = {}
    for pg, si, ln in L:
        pages.setdefault(("page", pg), []).append(ln)
    spages = {}
    for pg, si, ln in S:
        spages.setdefault(("solvedpage", pg), []).append(ln)
    for k, v in sorted(pages.items()):
        if len(v) >= 8:
            groups[f"page{k[1]}"] = v
    for k, v in sorted(spages.items()):
        if len(v) >= 8:
            groups[f"solvedpage{k[1]}"] = v
    T = []
    for g, lines in groups.items():
        for unit in ("rune", "latin"):
            for sep in (True, False):
                T.append(Target(f"{g}|{unit}|{'sep' if sep else 'nosep'}", lines, unit, sep))
    return T


# ------------------------------------------------------------------ pointer sources
def nums(i):
    return [int(t[1:]) for t in SEGS[i] if isinstance(t, str) and t.startswith("#") and t[1:].isdigit()]


def payload():
    alpha = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"
    toks = [t[1:] for t in SEGS[15] if isinstance(t, str) and t.startswith("#") and len(t) == 3]
    return [alpha.index(t[0]) * 60 + alpha.index(t[1]) for t in toks]


def spiral_out(r, c):
    """clockwise from the top-left corner inwards: list of (row, col)."""
    top, bot, left, right, out = 0, r - 1, 0, c - 1, []
    while top <= bot and left <= right:
        out += [(top, j) for j in range(left, right + 1)]
        out += [(i, right) for i in range(top + 1, bot + 1)]
        if top < bot:
            out += [(bot, j) for j in range(right - 1, left - 1, -1)]
        if left < right:
            out += [(i, left) for i in range(bot - 1, top, -1)]
        top, bot, left, right = top + 1, bot - 1, left + 1, right - 1
    return out


def sources():
    g30 = grid30.grid_values()
    ks, ps, _ = grid30.reconstruct()
    src = {
        "g02 (12)": (nums(2), None),
        "sq06 (25)": (nums(6), (5, 5)),
        "g30 values (16)": (g30, (4, 4)),
        "g30 k_i (16)": (ks, None),
        "g30 p_k (16)": (ps, None),
        "payload (256)": (payload(), None),
        "LP2 numerals 9,14 (6)": (nums(9) + nums(14), None),
    }
    return src


def orders(vals, shape, name):
    """-> {order: (flat sequence, cell coordinates or None)}"""
    v = np.array(vals)
    out = {"fwd": (v, None), "rev": (v[::-1], None)}
    if shape:
        r, c = shape
        cells = [(i, j) for i in range(r) for j in range(c)]
        grid = v.reshape(r, c)
        col = [(i, j) for j in range(c) for i in range(r)]
        sp = grid30.spiral_order() if shape == (4, 4) else spiral_out(r, c)
        for nm, cl in (("fwd", cells), ("col", col), ("spiral", sp)):
            seq = np.array([grid[i, j] for i, j in cl])
            out[nm] = (seq, np.array(cl))
            out[nm + "-rev"] = (seq[::-1], np.array(cl)[::-1])
        del out["rev"]
    return out


MODES = ["consec_lp", "consec_pl", "slide_lp", "slide_pl", "div60", "flat", "lineinit"]
RC_MODES = ["rc_lp", "rc_pl"]
BASES = (1, 0)


def readings(src):
    """yield (label, columns(tuple of 1-based-or-0-based int arrays before the base shift), kind) ; kind: 'pair','flat','line'."""
    for sname, (vals, shape) in src.items():
        for oname, (v, cells) in orders(vals, shape, sname).items():
            for mode in MODES + (RC_MODES if cells is not None else []):
                if mode == "consec_lp":
                    n = len(v) // 2 * 2
                    cols, kind = (v[0:n:2], v[1:n:2]), "pair"
                elif mode == "consec_pl":
                    n = len(v) // 2 * 2
                    cols, kind = (v[1:n:2], v[0:n:2]), "pair"
                elif mode == "slide_lp":
                    cols, kind = (v[:-1], v[1:]), "pair"
                elif mode == "slide_pl":
                    cols, kind = (v[1:], v[:-1]), "pair"
                elif mode == "div60":
                    cols, kind = (v // 60, v % 60), "pair"
                elif mode == "flat":
                    cols, kind = (v,), "flat"
                elif mode == "lineinit":
                    cols, kind = (v,), "line"
                elif mode == "rc_lp":
                    cols, kind = (cells[:, 0], cells[:, 1]), "pair"
                else:
                    cols, kind = (cells[:, 1], cells[:, 0]), "pair"
                for b in ((1,) if mode.startswith("rc") else BASES):
                    # a value v is a 1-based number when b == 1 (index v - 1), a 0-based one when b == 0 (index v);
                    # rc columns are cell coordinates (index = coordinate, one base only)
                    sh = 0 if mode.startswith("rc") else b
                    c0 = tuple(np.asarray(c, np.int64) - sh for c in cols)
                    yield (f"{sname} | {oname} | {mode} | base{b}", c0, kind, mode.startswith("rc"))


# ------------------------------------------------------------------ scoring
ANCH = {
    "http": re.compile("HTTP"), "onion": re.compile("ONION"), "callus": re.compile("CALLUS"),
    "digits7": re.compile(r"(?:ZERO|OH|ONE|TWO|THREE|FOUR|FIVE|SIX|SEVEN|EIGHT|NINE|NINER){7,}"),
}


def anchors(lett):
    s = "".join(chr(65 + x) if x >= 0 else "." for x in lett)
    return [k for k, r in ANCH.items() if r.search(s)]


def valid_frac(res):
    return float((res >= 0).mean())


def z_of(T, cols, kind, rng, nboot=NBOOT):
    """-> (z, n_trigrams, mean, anchors) or None."""
    flat, li = kind == "flat", kind == "line"
    res = T.resolve(cols, flat, li)
    if len(res) < MIN_TRI or valid_frac(res) < MIN_VALID:
        return None
    lett = T.letters(res)
    obs, n = tri_mean(lett)
    if n < MIN_TRI:
        return None
    rg = [(int(c.min()), int(c.max())) for c in cols]
    m = len(res)
    nul = []
    for _ in range(nboot):
        rc = tuple(rng.integers(lo, hi + 1, m) for lo, hi in rg)
        mu, nn = tri_mean(T.letters(T.resolve(rc, flat, li)))
        if nn >= MIN_TRI:
            nul.append(mu)
    if len(nul) < nboot // 2:
        return None
    nul = np.array(nul)
    return (obs - nul.mean()) / (nul.std() + 1e-9), n, obs, anchors(lett)


def run_family(src, T, rng, skip_rc=False, collect=False):
    best, rows, anc, scored, total = (-9, ""), [], [], 0, 0
    for label, cols, kind, is_rc in readings(src):
        if skip_rc and is_rc:
            continue
        for t in T:
            total += 1
            r = z_of(t, cols, kind, rng)
            if r is None:
                continue
            scored += 1
            if r[3]:
                anc.append((label, t.name, r[3]))
            if r[0] > best[0]:
                best = (r[0], f"{label} || {t.name} (tri={r[1]})")
            if collect:
                rows.append((r[0], label, t.name, r[1]))
    return best, scored, total, anc, rows


def random_sources(src, rng):
    out = {}
    for k, (v, sh) in src.items():
        v = np.array(v)
        out[k] = (list(rng.integers(v.min(), v.max() + 1, len(v))), sh)
    return out


# ------------------------------------------------------------------ planted control
def plant(T, n, rng, vmax=None):
    """n pointers = n//2 (line,pos) pairs resolving to an English window on target T (a latin-unit or rune-unit one);
    returns cols (0-based, consec_lp) or None."""
    m = n // 2
    s = int(rng.integers(0, len(ENG) - m))
    msg = ENG[s:s + m].copy()
    for a, b in ((21, 20), (10, 2), (16, 2), (25, 18)):   # V->U, K->C, Q->C, Z->S: the rune alphabet has no V K Q Z
        msg[msg == a] = b
    X = T.X
    if T.unit == "latin":
        sym = X
    else:
        sym = np.array([ord(lp.LATIN[x][0]) - 65 if (x < 29 and len(lp.LATIN[x]) == 1) else -5 for x in X])
    lmax = T.nl if vmax is None else min(T.nl, vmax)
    ok = T.line_of < lmax
    if vmax is not None:
        ok &= (np.arange(len(X)) - T.starts[T.line_of]) < vmax
    ls, ps = [], []
    for ch in msg:
        idx = np.flatnonzero((sym == ch) & ok)
        if not len(idx):
            return None
        i = int(rng.choice(idx))
        ls.append(int(T.line_of[i]))
        ps.append(int(i - T.starts[T.line_of[i]]))
    return np.array(ls), np.array(ps)


def main():
    cmd = sys.argv[1]
    src = sources()
    T = build_targets()
    if cmd == "count":
        n_read = sum(1 for _ in readings(src))
        n_rc = sum(1 for r in readings(src) if r[3])
        print(f"targets: {len(T)} ({len(T) // 4} texts x 4 unit/separator variants)")
        print(f"readings per target: {n_read} (rc-coordinate readings: {n_rc}); N = {n_read * len(T)}")
        for k, (v, sh) in src.items():
            print(" ", k, len(v), min(v), max(v))
        print("targets:", ", ".join(t.name for t in T[::4]))
    elif cmd == "real":
        rng = np.random.default_rng(4000)
        best, scored, total, anc, rows = run_family(src, T, rng, collect=True)
        print(f"N={total} scored={scored}; best z {best[0]:.2f}: {best[1]}")
        rows.sort(reverse=True)
        for r in rows[:15]:
            print(f"  z {r[0]:+.2f} | {r[1]} || {r[2]} (tri={r[3]})")
        print("top non-rc readings (comparable to the whole-screen null):")
        for r in [r for r in rows if "rc_" not in r[1]][:12]:
            print(f"  z {r[0]:+.2f} | {r[1]} || {r[2]} (tri={r[3]})")
        print("anchored hits:", anc if anc else "none")
        print(f"MAXZ_REAL {best[0]:.4f}")
    elif cmd == "null":
        runs, seed0 = int(sys.argv[2]), int(sys.argv[3])
        for r in range(runs):
            rng = np.random.default_rng(seed0 + r)
            ns = random_sources(src, rng)
            best, scored, total, anc, _ = run_family(ns, T, rng, skip_rc=True)
            print(f"NULL seed {seed0 + r} maxz {best[0]:.4f} scored {scored}/{total} anchored {len(anc)} {sorted({a for x in anc for a in x[2]})} | {best[1]}", flush=True)
    elif cmd == "nullrc":      # post-hoc addition: rc readings with random pointers of the same per-column ranges
        runs, seed0 = int(sys.argv[2]), int(sys.argv[3])
        rc = [r for r in readings(src) if r[3]]
        for r in range(runs):
            rng = np.random.default_rng(seed0 + r)
            best = -9
            for label, cols, kind, _ in rc:
                rcols = tuple(rng.integers(int(c.min()), int(c.max()) + 1, len(c)) for c in cols)
                for t in T:
                    z = z_of(t, rcols, kind, rng)
                    if z and z[0] > best:
                        best = z[0]
            print(f"NULLRC seed {seed0 + r} maxz {best:.4f}", flush=True)
    elif cmd == "plant":
        thr = float(sys.argv[2])
        rng = np.random.default_rng(777)
        tg = {t.name: t for t in T}
        for tname in ("LP2|latin|nosep", "LP2|rune|sep", "solved|latin|nosep"):
            t = tg[tname]
            for vmax in (None, 255):
                row = []
                for n in (12, 25, 64, 128, 256):
                    hits = tot = 0
                    zs = []
                    for _ in range(100):
                        p = plant(t, n, rng, vmax)
                        if p is None:
                            continue
                        r = z_of(t, p, "pair", rng)
                        tot += 1
                        if r:
                            zs.append(r[0])
                            hits += r[0] > thr
                    row.append(f"n={n}: {hits}/{tot} (median z {np.median(zs) if zs else float('nan'):.1f})")
                print(f"plant {tname} vmax={vmax}: " + "; ".join(row), flush=True)
    elif cmd == "selftest":
        assert len(nums(2)) == 12 and len(nums(6)) == 25 and len(payload()) == 256
        t = {x.name: x for x in T}["LP2|latin|nosep"]
        rng = np.random.default_rng(1)
        p = plant(t, 160, rng)
        res = t.resolve((p[0], p[1]), False, False)
        assert (res >= 0).all()
        s = "".join(chr(65 + x) for x in res)
        r = z_of(t, p, "pair", rng)
        print("planted letters:", s[:40], "z", r[0])
        assert r[0] > 5
        r2 = z_of(t, (rng.integers(0, t.nl, 32), rng.integers(0, 5, 32)), "pair", rng)
        print("random pointers z", r2 and r2[0])
        assert "HTTP" in ANCH["http"].pattern
        assert anchors(np.array([ord(c) - 65 for c in "XXHTTPYYONIONZZONETWOTHREEFOURFIVESIXSEVEN"])) == ["http", "onion", "digits7"]
        print("selftest ok")


if __name__ == "__main__":
    main()
