"""Phase 25: word-aware stateful encryption mechanisms on English plaintext at LP2's size and section layout, random key, measured with measure.py.

All mechanisms: c_i = p_i + k_i (mod 29), k iid uniform (any unstructured keystream is this). A 'would-be repeat' is a raw c_i equal to c_(i-1) inside a
section; with probability Q (0.81) the repair acts. Words start where the English word starts (sections start a word).

  M0 base     repair = uniform other rune (the skip/coin rule; the existing null for the doublet deficit)
  M1 t6       repair = T(c_(i-6)) = 24 - 2 c_(i-6) when the rune 6 back is in the same word, else M0
  M2 t6c5     repair = T(c_(i-6)) with prob a, c_(i-5) with prob b (a+b=1, a=0.7), in-word, else M0  (one repair budget for both echoes)
  M3 t6+cp5   M1 plus an independent rate-eps copy c_i = c_(i-5) inside words (the echo-two-tap family; two rules, two budgets)
  M4 rewind6  repair = redo with the key value of 6 back (k_i := k_(i-6), in-word): c_i = p_i + k_(i-6)  (key-pointer rewind)
  M5 ins      repair = INSERT T(c_(i-6)) as an extra rune (plaintext not advanced, key advanced), in-word, else M0 (changes word lengths)
  M6 ctr      word-scoped counter: a repair counter n (reset at every word start) selects the map applied to c_(i-6): n=0 -> T, n=1 -> identity, then uniform
  M7 xr6      repair = the plaintext-independent function 2*c_(i-1)-c_(i-6)... (unrelated affine of both neighbours), a negative control for the lag-6 relation

    python work/mech25/sim25.py [--reps 40]  -> results/analysis/mech25.txt
"""
import argparse
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, ".."))
sys.path.insert(0, os.path.join(HERE, "..", "families"))
import fam_data as D  # noqa: E402
import measure as M  # noqa: E402
import lp  # noqa: E402

N = 29
Q = 0.81


def english(letters):
    """English as runes with natural word starts; letters=True spells TH, NG, EA... letter by letter (the word-length fit G 60)"""
    if not letters:
        return D.english(150_000)
    import re
    runes, start = [], []
    order = [i for i in range(N) if len(lp.LATIN[i]) == 1]
    idx = {lp.LATIN[i]: i for i in order}
    alias = {"V": 1, "K": 5, "Z": 15, "Q": 5}
    txt = open(os.path.join(D.WORK, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    txt = txt[txt.index("SELF-RELIANCE"):].split("*** END OF")[0]
    for w in re.findall(r"[A-Za-z]+", txt):
        r = [idx.get(ch, None) if ch in idx else alias.get(ch, 0) for ch in w.upper()]
        runes += r; start += [True] + [False] * (len(r) - 1)
    return np.array(runes), np.array(start)


def layout():
    c, start, sid = D.lp2()
    return len(c), sid


def run(mech, P0, st0, sid, rng, eps=0.015, a=0.7):
    """encrypt the plaintext stream (P0, st0) section by section; returns (c, start, sid) of the cipher text"""
    out_c, out_s, out_id = [], [], []
    pos = 0
    for k in np.unique(sid):
        n = int((sid == k).sum())
        p = P0[pos:pos + n]; st = st0[pos:pos + n].copy(); st[0] = True
        pos += n
        c, s = [], []
        key = []
        w0 = 0   # index in c of the word's first rune
        cnt = 0
        j = 0
        outlen = 0
        while j < n and len(c) < n + 40:
            if st[j]:
                w0 = len(c); cnt = 0
            kk = int(rng.integers(N))
            x = (int(p[j]) + kk) % N
            i = len(c)
            ins = False
            if i and x == c[-1] and rng.random() < Q:
                inw = i - 6 >= w0
                inw5 = i - 5 >= w0
                if mech == "M0" or (not inw and mech != "M2"):
                    x = (c[-1] + 1 + int(rng.integers(N - 1))) % N
                elif mech == "M1":
                    x = (24 - 2 * c[i - 6]) % N
                elif mech == "M2":
                    if rng.random() < a and inw:
                        x = (24 - 2 * c[i - 6]) % N
                    elif inw5:
                        x = c[i - 5]
                    else:
                        x = (c[-1] + 1 + int(rng.integers(N - 1))) % N
                elif mech == "M3":
                    x = (24 - 2 * c[i - 6]) % N
                elif mech == "M4":
                    x = (int(p[j]) + key[i - 6]) % N
                elif mech == "M5":
                    ins = True
                    x = (24 - 2 * c[i - 6]) % N
                elif mech == "M6":
                    if cnt == 0:
                        x = (24 - 2 * c[i - 6]) % N
                    elif cnt == 1:
                        x = c[i - 6]
                    else:
                        x = (c[-1] + 1 + int(rng.integers(N - 1))) % N
                    cnt += 1
                elif mech == "M7":
                    x = (2 * c[-1] - c[i - 6]) % N
                if x == c[-1]:   # a repair must not repeat
                    x = (c[-1] + 1 + int(rng.integers(N - 1))) % N
            elif mech == "M3" and i - 5 >= w0 and rng.random() < eps:
                x = c[i - 5]
            c.append(x); key.append(kk); s.append(bool(st[j]) and not ins)
            if ins:
                s[-1] = False
            else:
                j += 1
        c = c[:n] if len(c) > n else c   # insertion mechanism: cut the section to the observed length (LP2 sections are fixed)
        s = s[:len(c)]
        s[0] = True
        out_c += c; out_s += s; out_id += [int(k)] * len(c)
    return np.array(out_c), np.array(out_s), np.array(out_id)


def stats_of(c, s, sid, lp2hist):
    st = M.all_stats(c, s, sid)
    st["Gown"] = M.g_test(st["hist"], np.array(ENG_HIST))
    st["Glp2"] = M.g_test(lp2hist, st["hist"])
    return st


ENG_HIST = None


def main():
    global ENG_HIST
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=40)
    ap.add_argument("--mechs", default="M0,M1,M2,M3,M4,M5,M6,M7")
    args = ap.parse_args()
    ref, _ = M.lp2_stats()
    n, sid = layout()
    out = []

    def say(x=""):
        print(x, flush=True); out.append(x)

    say(f"LP2: doublets {100 * ref['dbl']:.2f}% (in {100 * ref['dbl_in']:.2f}%, gap {100 * ref['dbl_gap']:.2f}%); lag6 in {ref['l6_in'][1]}/{ref['l6_in'][2]:.1f} z {ref['l6_in'][3]:+.2f}, "
        f"across {ref['l6_x'][3]:+.2f}; lag5 in {ref['l5_in'][1]}/{ref['l5_in'][2]:.1f} z {ref['l5_in'][3]:+.2f}, across {ref['l5_x'][3]:+.2f}, S5 {ref['S5']}; uni chi2 {ref['uni']:.1f}, bi chi2 {ref['bi']:.0f}, "
        f"max lag z {ref['lagz']:+.2f}")
    lp2hist = ref["hist"]
    rng = np.random.default_rng(2510)
    for letters in (False, True):
        P0, st0 = english(letters)
        ENG_HIST = M.hist(st0[:400000])
        say(f"\n== plaintext spelling: {'letters' if letters else 'digraph runes'} ==")
        say("mech  rep  dbl%  dblIn%  dblGap%  l6in hits/exp (z)   l6 across z  l5in hits/exp (z)  l5 across z  S5   uni   bi   lagz  Glp2 words")
        for mech in args.mechs.split(","):
            rows = []
            for r in range(args.reps):
                a = int(rng.integers(0, len(P0) - n - 5000))
                a = int(np.flatnonzero(st0[a:])[0]) + a
                c, s, sd = run(mech, P0[a:a + n + 5000], st0[a:a + n + 5000], sid, rng)
                if len(c) != n:
                    c = np.resize(c, n); s = np.resize(s, n); sd = sid.copy()
                rows.append(stats_of(c, s, sd, lp2hist))
            g = lambda f: np.array([f(x) for x in rows])
            m = lambda f: f"{g(f).mean():.2f}"
            say(f"{mech:4s} {args.reps:3d}  {100 * g(lambda x: x['dbl']).mean():.2f}  {100 * g(lambda x: x['dbl_in']).mean():.2f}  {100 * g(lambda x: x['dbl_gap']).mean():.2f}   "
                f"{g(lambda x: x['l6_in'][1]).mean():5.1f}/{g(lambda x: x['l6_in'][2]).mean():.1f} ({m(lambda x: x['l6_in'][3])})  {m(lambda x: x['l6_x'][3])}   "
                f"{g(lambda x: x['l5_in'][1]).mean():5.1f}/{g(lambda x: x['l5_in'][2]).mean():.1f} ({m(lambda x: x['l5_in'][3])})  {m(lambda x: x['l5_x'][3])}  {m(lambda x: x['S5'])}  "
                f"{m(lambda x: x['uni'])}  {m(lambda x: x['bi'])}  {m(lambda x: abs(x['lagz']))}  {m(lambda x: x['Glp2'])}")
    dest = os.path.join(HERE, "..", "..", "results", "analysis")
    with open(os.path.join(dest, "mech25.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


if __name__ == "__main__":
    main()
