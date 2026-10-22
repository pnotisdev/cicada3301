"""Controls for lang_checks.py (phase 50): planted true keys on solved plaintext (both checks high) and wrong
offsets / random plaintext (both at chance).

    python work/kscreen/lang_checks_selftest.py [--out results/kscreen/lang_checks_selftest.txt]
"""
import argparse
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lp  # noqa: E402
import lang_checks  # noqa: E402
import selftest  # noqa: E402  (BIN, run, truths, rel)

SECTIONS = (0, 1, 3, 4, 5, 6, 16, 17)   # all solved pages with a plaintext rule, as work/prime_check.py control
FAM, ITEM, OFF, MODEL = "file:data/library.ksb", "primes-1 (totient)", "1234", 0


def verify(plant, off, win):
    out = selftest.run(["verify", selftest.rel(plant), FAM, ITEM, off, "1", str(MODEL), win])
    return [int(x) for x in re.search(r"plain (.*)", out).group(1).split(",")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.join(selftest.OUT, "lang_checks_selftest.txt"))
    args = ap.parse_args()
    os.makedirs(selftest.TMP, exist_ok=True)
    segs = lp.load_segments()
    src, plant = (os.path.join(selftest.TMP, f"lang_checks_{x}.txt") for x in ("plain", "plant"))
    with open(src, "w", newline="\n") as f:
        for i in SECTIONS:
            f.write(f"W seg0.{i} -1\nR {' '.join(map(str, lp.KNOWN[i][1](lp.runes_of(segs[i]))))}\n")
    selftest.run(["plant", selftest.rel(src), FAM, ITEM, OFF, "1", str(MODEL), "0.18", "7", "0", selftest.rel(plant)])
    truth = selftest.truths(plant)
    rng = random.Random(50)
    lines, ok = [], True
    tot = {k: [0, 0, 0, 0] for k in ("planted", "wrong")}      # ai_k, ai_n, short_prime, short
    for wi, i in enumerate(SECTIONS):
        win, pw = f"seg0.{i}", f"plant_{wi}"          # plant renames the windows
        c = lang_checks.checks(win, verify(plant, truth[pw][1], pw))
        lines.append(f"planted {win}: {lang_checks.fmt(c)}")
        tot["planted"] = [a + b for a, b in zip(tot["planted"], (c["ai_k"], c["ai_n"], c["short_prime"], c["short"]))]
        for _ in range(20):
            c = lang_checks.checks(win, verify(plant, str(rng.randrange(1, 15000)), pw))
            tot["wrong"] = [a + b for a, b in zip(tot["wrong"], (c["ai_k"], c["ai_n"], c["short_prime"], c["short"]))]
    for k, (a, n, sp, s) in tot.items():
        lines.append(f"{k:8s} total: A/I {a}/{n} = {a/n:.2f}; prime short clauses {sp}/{s} = {sp/s:.2f}")
    p, w = tot["planted"], tot["wrong"]
    ok = p[0] / p[1] >= 0.9 and p[2] / p[3] >= 0.4 and w[0] / w[1] <= 0.25 and w[2] / w[3] <= 0.30
    # uniform random plaintext at every solved window (true chance level for both checks)
    r = [0, 0, 0, 0]
    for _ in range(200):
        for i in SECTIONS:
            n = len(lp.runes_of(segs[i]))
            c = lang_checks.checks(f"seg0.{i}", [rng.randrange(29) for _ in range(n)])
            r = [a + b for a, b in zip(r, (c["ai_k"], c["ai_n"], c["short_prime"], c["short"]))]
    lines.append(f"random plaintext (200 x {len(SECTIONS)} windows): A/I {r[0]}/{r[1]} = {r[0]/r[1]:.3f} (2/29 = 0.069); "
                 f"prime short clauses {r[2]}/{r[3]} = {r[2]/r[3]:.3f} (chance 0.147)")
    ok &= abs(r[0] / r[1] - 2 / 29) < 0.02 and abs(r[2] / r[3] - 0.147) < 0.03
    lines.append("LANG CHECKS SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
