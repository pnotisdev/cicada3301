"""H8 of docs/HYPOTHESES.md: does a null rune emitted at each avoided collision explain LP2's word lengths?

    python work/null_insertion.py            # writes results/analysis/null_insertion.txt

Prediction written before the test: an encryptor that emits a random null instead of a doublet (and re-enciphers the
rune with the next key value) inserts runes at about 360 / 12,956 = 0.028 per rune, so a word of n plaintext runes
gains Binomial(n, 0.028) runes. Base: English in runes (Emerson) with TH spelled T+H, the zero-parameter model that
removes most of the 2-rune-word deficit (G 223 -> 56, work/wordlen_languages.py). Kill: a fitted rate whose 95%
interval excludes 0.028, or no gain over TH alone at 0.028.
Control: words drawn from the same base with nulls inserted at 0.028, 2,928 per sample (LP2's count), refitted.
"""
import os
import random
import sys
from math import comb

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402
import stats  # noqa: E402
from wordlen_languages import BINS, g_test, hist, words_of  # noqa: E402

RATE = 360 / 12956
TH = lp.LATIN.index("TH")


def base_lengths(th_letters):
    ws = words_of("English (Emerson, Essays I)")[:60000]
    seqs = [s for s in (lp.word_to_key(w.replace("IO", "IA")) for w in ws) if s]
    return [len(s) + (s.count(TH) if th_letters else 0) for s in seqs]


def with_insertion(lengths, lam):
    q = np.zeros(80)
    for L, n in zip(*np.unique(lengths, return_counts=True)):
        for k in range(0, min(L, 6) + 1):
            q[min(L + k, 79)] += n * comb(int(L), k) * lam ** k * (1 - lam) ** (L - k)
    return np.concatenate([q[1:BINS], [q[BINS:].sum()]])


def fit(obs, lengths, grid=np.arange(0, 0.301, 0.001)):
    gs = np.array([g_test(obs, with_insertion(lengths, x) / 1.0, fitted=1)[0] for x in grid])
    i = gs.argmin()
    inside = grid[gs <= gs[i] + 3.84]
    return grid[i], gs[i], inside.min(), inside.max()


def kscreen_coverage(item="primes-1 (totient)", off=1234):
    """Is an H8 ciphertext visible to the existing keystream screen? English windows enciphered with a library stream,
    a null emitted at 82% of collisions (no key value spent), then screened with kscreen as is."""
    import subprocess
    import tempfile
    ks = os.path.join(HERE, "kscreen")
    exe = os.path.join(ks, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
    sys.path.insert(0, ks)
    import keystreams
    key = keystreams.number_keystreams()[item] % 29
    rng = random.Random(29)
    wins = [[int(x) for x in line.split()[1:]] for line in open(os.path.join(HERE, "phpmt", "data", "english.txt"),
                                                               encoding="utf-8") if line.startswith("R ")]
    lines, nulls, total = [], 0, 0
    with tempfile.TemporaryDirectory() as d:
        wf, tsv = os.path.join(d, "w.txt"), os.path.join(d, "o.tsv")
        with open(wf, "w", newline="\n") as f:
            for wi, p in enumerate(wins):
                j, prev, c = off + 997 * wi, -1, []
                for x in p:
                    y = (x + key[j]) % 29
                    j += 1
                    if y == prev and rng.random() >= 0.18:
                        c.append(rng.choice([r for r in range(29) if r != prev]))   # the null
                        nulls += 1
                        y = (x + key[j]) % 29
                        j += 1
                    c.append(y)
                    prev = y
                total += len(c)
                f.write(f"W h8_{wi} -1\nR {' '.join(map(str, c))}\nL {len(c)}\n")
        subprocess.run([exe, "screen", wf, "file:data/library.ksb", tsv, f"only={item}", "threads=2"], cwd=ks, check=True,
                       capture_output=True)
        for line in open(tsv, encoding="utf-8"):
            if line.startswith("# window"):
                lines.append("    " + line.strip()[2:])
    return [f"Coverage: {len(wins)} English windows enciphered with {item!r} under H8 ({nulls} nulls in {total} runes), "
            f"screened by the existing kscreen (truth: offsets {', '.join(str(off + 997 * i) for i in range(len(wins)))}):"] + lines


def main():
    obs = hist([b - a for i in stats.UNSOLVED for _, a, b in
                lp.word_spans(stats.SEGS[i], lp.runes_of(stats.SEGS[i]))])
    runes, th = base_lengths(False), base_lengths(True)
    out = [f"H8 null on collision: LP2 {int(obs.sum())} words; predicted insertion rate {RATE:.4f} per rune", ""]
    for label, L in (("English runes", runes), ("English runes, TH spelled T+H", th)):
        for lam, tag in ((0.0, "no insertion"), (RATE, f"insertion {RATE:.4f} (predicted, 0 fitted)")):
            g, df, p = g_test(obs, with_insertion(L, lam))
            out.append(f"  {label:32s} {tag:40s} G={g:6.1f} df={df} p={p:.1e}")
        lam, g, lo, hi = fit(obs, L)
        _, df, p = g_test(obs, with_insertion(L, lam), fitted=1)
        out.append(f"  {label:32s} {'insertion rate fitted':40s} G={g:6.1f} df={df} p={p:.1e}  rate {lam:.3f} (95% {lo:.3f}-{hi:.3f})")
    # control: can the fit recover 0.028 from 2,928 words?
    rng = random.Random(3301)
    fits = []
    for _ in range(100):
        sample = [L + sum(rng.random() < RATE for _ in range(L)) for L in rng.choices(th, k=int(obs.sum()))]
        lam, g, lo, hi = fit(hist(sample), th, grid=np.arange(0, 0.101, 0.002))
        fits.append((lam, lo <= RATE <= hi))
    lams = np.array([f for f, _ in fits])
    cover = sum(c for _, c in fits)
    out += ["", f"Control: 100 samples of {int(obs.sum())} words from the TH base with nulls at {RATE:.4f}: fitted rate "
                f"{lams.mean():.4f} +- {lams.std():.4f}; the 95% interval covers the truth in {cover}/100"]
    lam, g, lo, hi = fit(obs, th)
    g0 = g_test(obs, with_insertion(th, 0.0))[0]
    gp = g_test(obs, with_insertion(th, RATE))[0]
    dead = not (lo <= RATE <= hi) or gp >= g0
    out.append(f"Verdict: {'DEAD' if dead else 'ALIVE'} (TH base: G {g0:.1f} without nulls, {gp:.1f} at the predicted rate; "
               f"fitted rate {lam:.3f}, 95% {lo:.3f}-{hi:.3f})")
    out += [""] + kscreen_coverage()
    text = "\n".join(out) + "\n"
    print(text)
    with open(os.path.join(os.path.dirname(HERE), "results", "analysis", "null_insertion.txt"), "w", newline="\n",
              encoding="utf-8") as fh:
        fh.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
