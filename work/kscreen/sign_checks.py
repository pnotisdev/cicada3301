"""Two checks prompted by an outside audit of the sign-rule decisions (deepseek-v4-pro, 2026-10-18).

 1. FLAT-IoC SUBSET. The sign screens use only the library streams whose marginal is flat; the argument was that a sign mask cannot make a non-flat key flat. A mask that flips a share f of the runes independent of the key values turns a key marginal h into
    (1 - f) h(v) + f h(-v); for f = 0.5 that is the symmetrisation (h(v) + h(-v)) / 2, the most favourable case. Predicted ciphertext IoC under English plaintext for every EXCLUDED stream under that mixture (f = 0.25, 0.5, 0.75): any stream at or below 1.003 would be flat
    under signs and should have been screened.
 2. COVERAGE BY THE UNSIGNED SCREENS. The review claimed that a rule flipping few runes is already visible to the unsigned screens. Plant a library key into English with random word-level signs at a flip share f of the runes, and screen UNSIGNED (the S line removed): best hit and IoC at the true offset, for f = 0.1 .. 0.6. The naive mixture
    1 + (1 - f)^2 (kappa - 1) is compared with the measured IoC (the beam adds the gain of choosing paths).

    python work/kscreen/sign_checks.py [--threads N]      # -> results/analysis/sign_checks.txt
"""
import argparse
import os
import random
import re
import sys

import numpy as np

import selftest as S
import signrules as R
import sign_selftest as T

sys.path.insert(0, R.WORK)
import keystreams  # noqa: E402

sys.path.insert(0, os.path.join(R.WORK, "layer2"))
from export import read_ksb  # noqa: E402

OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def check_flat():
    P = keystreams.english_distribution()
    flat = set()
    with open(os.path.join(S.HERE, "data", "library.tsv"), encoding="utf-8") as f:
        next(f)
        for line in f:
            p = line.rstrip("\n").split("\t")
            if p[4] == "0":
                flat.add(p[0])
    ex = [(n, np.frombuffer(bytes(v), dtype=np.uint8).astype(np.int64)) for n, v in read_ksb(os.path.join(S.HERE, "data", "library.ksb")) if n not in flat]
    say(f"1. {len(ex)} library streams are excluded by the flat IoC (unsigned predicted IoC > 1.003); predicted IoC of the signed marginal (1 - f) h(v) + f h(-v):")
    for f_neg in (0.25, 0.5, 0.75):
        n_flat, best = 0, []
        for name, v in ex:
            h = np.bincount(v[:4000] % 29, minlength=29) / min(4000, len(v))
            hm = (1 - f_neg) * h + f_neg * h[(-np.arange(29)) % 29]
            q = np.zeros(29)
            for k in range(29):
                q += hm[k] * np.roll(P, k)
            ioc = float(29 * (q ** 2).sum())
            best.append((ioc, name))
            n_flat += ioc <= 1.003
        best.sort()
        say(f"   f = {f_neg}: {n_flat} of {len(ex)} would be flat (<= 1.003); lowest predicted IoC {best[0][0]:.4f} ({best[0][1][:40]!r}), 5th lowest {best[4][0]:.4f}")
    say("")


def check_coverage(threads):
    rng0 = random.Random(5)
    ksb = dict(read_ksb(os.path.join(S.HERE, "data", "library.ksb")))
    item, mult, model = "sha256-ctr reject :3301", 1, 0
    key = [int(x) for x in ksb[item]]
    wins = T.plain_windows()
    say("2. UNSIGNED screen of a plant whose key sign is flipped on a random share of WORDS (3 windows of 400 runes, one library key, rule-free random signs):")
    say(f"{'flipped runes':>14s} {'unsigned IoC at truth':>22s} {'naive mixture':>14s} {'screen best (item at truth?)':>34s}")
    for share in (0.0, 0.1, 0.2, 0.3, 0.4, 0.5):
        rule = lambda ws, w, share=share: -1 if rng0.random() < share else 1
        entries, shares, truths = [], [], []
        rng = random.Random(900)
        for wi, (runes, lens) in enumerate(wins):
            off = (1234 + 997 * wi) % (len(key) - len(runes) * 4 - 64)
            c, signs = T.plant(runes, lens, key[off:], mult, model, 0.18, rule, rng)
            entries.append((f"plant_{wi}", c, lens, None, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
            shares.append(signs.count(-1) / len(signs))
            truths.append(off)
        f = os.path.join(S.TMP, "signcheck_plant.txt")
        T.write(f, entries)
        tsv = os.path.join(S.TMP, "signcheck_plant.tsv")
        S.run(["screen", S.rel(f), T.FAMILY, S.rel(tsv), f"only={item}", f"threads={threads}"])
        best = S.window_bests(tsv)
        iocs, hits = [], 0
        for win, (_, toff) in S.truths(f).items():
            v = float(re.search(r"ioc ([\d.]+)", S.run(["verify", S.rel(f), T.FAMILY, item, toff, str(mult), str(model), win])).group(1))
            iocs.append(v)
            hits += best.get(win, (0, "-", "-"))[1] == item and best[win][0] >= S.THRESHOLD
        fr = float(np.mean(shares))
        say(f"{100 * fr:13.0f}% {np.mean(iocs):22.3f} {1 + (1 - fr) ** 2 * 0.78:14.3f} {hits} of 3 windows: best hit = the planted item with IoC >= 1.40")
    say("")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    check_flat()
    check_coverage(a.threads)
    dest = os.path.join(R.WORK, "..", "results", "analysis")
    with open(os.path.join(dest, "sign_checks.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
