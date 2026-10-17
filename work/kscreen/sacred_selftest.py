"""Positive control for the kscreen-sacred streams (work/kscreen/sacred.py): one planted key from each family (F1, F3, F4, F5) into held-out English under the anti-repeat rule, screened through
`file:data/sacred.ksb` with the same engine and options as the campaign. Each must come back as its window's best hit with IoC >= 1.40 at the true offset, and a full re-decode at the truth must also reach 1.40
(the rules of selftest.py). Two plants per family: skip model / coin model, key sign +1 / multiplier 28.

    python work/kscreen/sacred_selftest.py [--threads N] [--out results/kscreen/sacred_selftest.txt]
"""
import argparse
import os
import re
import sys

import selftest as S

HERE = S.HERE
FAMILY = "file:data/sacred.ksb"


def items():
    out = {}
    with open(os.path.join(HERE, "data", "sacred.tsv"), encoding="utf-8") as f:
        next(f)
        for line in f:
            name = line.split("\t")[0]
            out.setdefault(name.split()[0], []).append(name)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(S.OUT, "sacred_selftest.txt"))
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    by_fam = items()
    lines, ok, ci = [], True, 0
    for fam in ("F1", "F3", "F4", "F5"):
        names = by_fam[fam]
        for k, (idx, off, mult, model, subst) in enumerate(((0, "1234", 1, 0, 0), (len(names) // 2, "5321", 28, 1, 1))):
            item = names[idx]
            plant = os.path.join(S.TMP, f"sacred_plant{ci}.txt")
            tsv = os.path.join(S.TMP, f"sacred_plant{ci}.tsv")
            S.run(["plant", S.rel(S.PLAIN), FAMILY, item, off, str(mult), str(model), "0.18", str(200 + ci), str(subst), S.rel(plant)])
            S.run(["screen", S.rel(plant), FAMILY, S.rel(tsv), f"only={item}", f"threads={a.threads}"])
            best = S.window_bests(tsv)
            for win, (titem, toff) in S.truths(plant).items():
                ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
                vout = S.run(["verify", S.rel(plant), FAMILY, item, toff, str(mult), str(model), win])
                vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
                good = bitem == item and ioc >= S.THRESHOLD and vioc >= S.THRESHOLD
                ok &= good
                lines.append(f"{'PASS' if good else 'FAIL'}  {fam} plant {item!r} model={model} mult={mult} subst={subst} {win}: best {ioc:.3f} at offset {boff} (truth {toff}); re-decode at truth {vioc:.3f}")
            ci += 1
    lines.append("SACRED SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
