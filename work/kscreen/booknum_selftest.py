"""Positive and blindness controls for the book-number streams (work/kscreen/booknum.py), phase 33. A negative from `kscreen screen ... file:data/booknum.ksb` only counts if this passes.

Same independent Python planter as signed_selftest.py (imported, not copied): 300 runes of held-out English encrypted under the anti-repeat rule with the shortest and the longest
stream of every kept family, skip / coin, multiplier 1 / 28, plain / substituted alphabet. The unchanged engine (mults=all) must return that stream at the planted offset (within 5)
as the window's best with IoC >= 1.40, a re-decode at the truth must reach 1.40, and a stream from ANOTHER BOOK must stay below 1.40 on the same window.

    python work/kscreen/booknum_selftest.py [--threads N] [--out results/kscreen/booknum_selftest.txt]
"""
import argparse
import os
import random
import re
import sys

import selftest as S
from signed_selftest import plant, read_ksb, read_plain, trim_lens, NEED, KEEP

HERE = S.HERE
FAMILY = "file:data/booknum.ksb"


def klass(name):
    return name.split()[1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(S.OUT, "booknum_selftest.txt"))
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    ks = read_ksb(os.path.join(HERE, "data", "booknum.ksb"))
    by_fam = {}
    for name, v in ks.items():
        by_fam.setdefault(name.split()[0], []).append(name)
    runes, lens = read_plain(S.PLAIN)
    runes, lens = runes[:300], trim_lens(lens, 300)
    lines, ok, ci = [], True, 0
    for fam in sorted(by_fam):
        names = sorted(by_fam[fam], key=lambda x: (len(ks[x]), x))
        pair = [names[0], names[-1]]
        for k, item in enumerate(pair):
            noff = len(ks[item]) + 1 - NEED
            off = noff // 2 if k == 0 else (2 * noff) // 3
            mult, model, subst = ((1, 0, 0), (28, 1, 1))[k]
            rng = random.Random(900 + ci)
            c = plant(runes, ks[item], off, mult, model, rng, subst)
            pf = os.path.join(S.TMP, f"booknum_plant{ci}.txt")
            tsv = os.path.join(S.TMP, f"booknum_plant{ci}.tsv")
            with open(pf, "w", newline="\n", encoding="utf-8") as f:
                f.write(f"# truth plant_0 item={item} offset={off} mult={mult} model={model} keep={KEEP} subst={subst}\n"
                        f"W plant_0 -1\nR {' '.join(map(str, c))}\nL {' '.join(map(str, trim_lens(lens, 300)))}\n")
            S.run(["screen", S.rel(pf), FAMILY, S.rel(tsv), f"only={item}", "mults=all", f"threads={a.threads}"])
            ioc, bitem, boff = S.window_bests(tsv).get("plant_0", (0.0, "-", "-"))
            vout = S.run(["verify", S.rel(pf), FAMILY, item, str(off), str(mult), str(model), "plant_0"])
            vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
            wrong = max((x for x in names if klass(x) != klass(item)), key=lambda x: len(ks[x]))
            wtsv = os.path.join(S.TMP, f"booknum_plant{ci}_wrong.tsv")
            S.run(["screen", S.rel(pf), FAMILY, S.rel(wtsv), f"only={wrong}", "mults=all", f"threads={a.threads}"])
            wioc = S.window_bests(wtsv).get("plant_0", (0.0, "-", "-"))[0]
            # a few offsets of difference are the skip-model alias (the decode starts a key value or two off and absorbs it in its first skips), as in the other selftests
            near = boff.lstrip("-").isdigit() and abs(int(boff) - off) <= 5
            good = bitem == item and near and ioc >= S.THRESHOLD and vioc >= S.THRESHOLD and wioc < S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  {fam} plant {item!r} (len {len(ks[item])}) model={model} mult={mult} subst={subst}: best {ioc:.3f} at offset {boff} (truth {off}); "
                         f"re-decode at truth {vioc:.3f}; wrong stream {wrong!r} best {wioc:.3f}")
            ci += 1
    lines.append("BOOKNUM SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
