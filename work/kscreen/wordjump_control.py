"""Controls for kscreen `advsep=3|4|5` (word-jump key-pointer advances; work/kscreen/WORDJUMP.md, phase 37). A screen with these options only counts if this passes.

advsep=3: the key pointer consumes n_w EXTRA key values at the end of every word (n_w = the length of the word just ended); advsep=4: a constant 2 extra values per boundary;
advsep=5: the length of the NEXT word. Word edges come from the window's L line. This planter is independent of the engine's `plant` (Python, held-out English
work/phpmt/data/english.txt, library_flat streams, the anti-repeat rule with the fitted 81% enforcement, both models, multipliers 1 and 28, plain / substituted alphabet).

Gates, per mode 3 / 4 / 5 and four plants (model x multiplier x alphabet x stream):
  (a) positive: the engine with the SAME advsep recovers the planted stream at the exact offset with IoC >= 1.60 (a re-decode with `verify` at the truth also >= 1.60);
  (b) blindness: the default engine (advsep=0) on the same ciphertext stays < 1.40, and so do advsep=1 and the two other word-jump modes (the wrong convention);
  (c) null: rand:300:<seed> with advsep=3|4|5 stays < 1.40 (the same pair count class as one stream file of 300 streams).

    python work/kscreen/wordjump_control.py [--bin <engine>] [--threads 2] [--out results/kscreen/wordjump_control.txt]
"""
import argparse
import os
import random
import re
import subprocess
import sys

import selftest as S
from signed_selftest import KEEP, NEED, read_ksb, read_plain, trim_lens

HERE = S.HERE
LIB = "file:data/library_flat.ksb"
Q = 29


def adv_of(lens, mode):
    """extra key values before rune i (the engine's adv_positions for advsep=3|4|5)"""
    adv, b = [0] * (sum(lens) + 1), 0
    for wi, l in enumerate(lens):
        b += l
        if b < sum(lens):
            adv[b] += {3: l, 4: 2, 5: lens[wi + 1]}[mode]
    return adv


def plant(runes, lens, key, off, mult, model, rng, subst, mode):
    d = list(range(Q))
    if subst:
        rng.shuffle(d)
    mk = [(k * mult) % Q for k in key[off:]]
    adv = adv_of(lens, mode)
    j, prev, out = 0, -1, []
    for i, p in enumerate(runes):
        j += adv[i] if i else 0
        t = d[p]
        y = (t + mk[j]) % Q
        j += 1
        if model == 0:                       # skip: draw the next key value
            tries = 0
            while prev >= 0 and y == prev and rng.random() >= KEEP and tries < 5:
                y = (t + mk[j]) % Q
                j += 1
                tries += 1
        elif prev >= 0 and y == prev:        # coin: spend a key value, then keep or redraw
            j += 1
            if rng.random() >= KEEP:
                y = (t + mk[j]) % Q
                j += 1
        out.append(y)
        prev = y
    return out


def best(tsv):
    return S.window_bests(tsv).get("plant_0", (0.0, "-", "-"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", default=S.BIN)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=os.path.join(S.OUT, "wordjump_control.txt"))
    a = ap.parse_args()
    S.BIN = a.bin
    os.makedirs(S.TMP, exist_ok=True)
    ks = read_ksb(os.path.join(HERE, "data", "library_flat.ksb"))
    names = sorted(ks, key=lambda x: (len(ks[x]), x))[len(ks) // 3::max(1, len(ks) // 12)]
    lines, ok, ci = [], True, 0
    for mode in (3, 4, 5):
        for k, (mult, model, subst) in enumerate(((1, 0, 0), (28, 1, 1), (28, 0, 1), (1, 1, 0))):
            item = names[(ci * 3) % len(names)]
            runes, lens = read_plain(S.PLAIN, k % 3)
            runes, lens = runes[:300], trim_lens(lens, 300)
            rng = random.Random(3700 + ci)
            need = len(ks[item]) - NEED - sum(adv_of(lens, mode)) - 40
            off = rng.randrange(50, max(51, need))
            c = plant(runes, lens, ks[item], off, mult, model, rng, subst, mode)
            pf = os.path.join(S.TMP, f"wj_plant{ci}.txt")
            tsv = os.path.join(S.TMP, f"wj_plant{ci}.tsv")
            with open(pf, "w", newline="\n", encoding="utf-8") as f:
                f.write(f"# truth plant_0 item={item} offset={off} mult={mult} model={model} keep={KEEP} subst={subst} advsep={mode}\n"
                        f"W plant_0 -1\nR {' '.join(map(str, c))}\nL {' '.join(map(str, lens))}\n")
            S.run(["screen", S.rel(pf), LIB, S.rel(tsv), f"only={item}", "mults=all", f"threads={a.threads}", f"advsep={mode}"])
            ioc, bitem, boff = best(tsv)
            vout = S.run(["verify", S.rel(pf), LIB, item, str(off), str(mult), str(model), "plant_0", f"advsep={mode}"])
            vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
            blind = {}
            for other in (0, 1, 3, 4, 5):
                if other == mode:
                    continue
                t2 = os.path.join(S.TMP, f"wj_plant{ci}_a{other}.tsv")
                S.run(["screen", S.rel(pf), LIB, t2, f"only={item}", "mults=all", f"threads={a.threads}", f"advsep={other}"])
                blind[other] = best(t2)[0]
            exact = boff.lstrip("-").isdigit() and int(boff) == off
            good = bitem == item and exact and ioc >= 1.60 and vioc >= 1.60 and max(blind.values()) < S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  advsep={mode} plant {item!r} model={model} mult={mult} subst={subst}: best {ioc:.3f} at offset {boff} (truth {off}); re-decode at truth {vioc:.3f}; "
                         f"wrong conventions: " + ", ".join(f"advsep={o} {v:.3f}" for o, v in blind.items()))
            ci += 1
    for mode in (3, 4, 5):
        tsv = os.path.join(S.TMP, f"wj_null{mode}.tsv")
        S.run(["screen", "data/segments.txt", "rand:300:%d" % (370 + mode), S.rel(tsv), "mults=1", f"threads={a.threads}", f"advsep={mode}"])
        v = float(re.search(r"# best ([\d.]+)", open(tsv, encoding="utf-8").read()).group(1))
        good = v < S.THRESHOLD
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  null advsep={mode}: rand:300:{370 + mode} on the 8 section windows, mults=1, best {v:.4f}")
    lines.append("WORDJUMP CONTROL " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
