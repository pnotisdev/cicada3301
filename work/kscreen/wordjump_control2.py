"""Phase 37 gate, restated (work/log/phase37_word_jump.md, 'Restated gate'): fresh plants on NEW plaintext windows (Walden, digraph runes, word lengths from the text), advsep=3|4|5.

A plant passes if the engine with the same advsep returns the planted stream at the EXACT planted offset, its IoC is >= 0.9 x the plaintext window's own IoC (before encryption),
the re-decode at the truth gives the same IoC, and the default engine (advsep=0) and advsep=1 on the same ciphertext stay < 1.40. Four plants per mode, twelve in all, twelve distinct windows.

    python work/kscreen/wordjump_control2.py [--bin <engine>] [--threads 2] [--out results/kscreen/wordjump_control2.txt]
"""
import argparse
import os
import random
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import selftest as S
import lp
from signed_selftest import KEEP, NEED, read_ksb, trim_lens
from wordjump_control import adv_of, best, plant

HERE = S.HERE
LIB = "file:data/library_flat.ksb"


def walden_words():
    t = open(os.path.join(HERE, "..", "ref", "corpora", "pg205.txt"), encoding="utf-8", errors="ignore").read()
    a, b = t.find("*** START"), t.find("*** END")
    t = t[t.find("\n", a) + 1:b]
    ws = []
    for w in re.findall(r"[A-Za-z]+", t):
        r = lp.word_to_key(w.upper().replace("IO", "IA"))
        if r:
            ws.append(r)
    return ws


def window(ws, rng):
    """300 runes of consecutive Walden words, the last word cut to land on 300: (runes, lens)"""
    i = rng.randrange(1000, len(ws) - 200)
    runes, lens = [], []
    while len(runes) < 300:
        runes += ws[i]
        lens.append(len(ws[i]))
        i += 1
    return runes[:300], trim_lens(lens, 300)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", default=S.BIN)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--out", default=os.path.join(S.OUT, "wordjump_control2.txt"))
    a = ap.parse_args()
    S.BIN = a.bin
    os.makedirs(S.TMP, exist_ok=True)
    ks = read_ksb(os.path.join(HERE, "data", "library_flat.ksb"))
    names = sorted(ks, key=lambda x: (len(ks[x]), x))[len(ks) // 4::max(1, len(ks) // 17)]
    ws = walden_words()
    lines, ok, ci = [], True, 0
    for mode in (3, 4, 5):
        for k, (mult, model, subst) in enumerate(((1, 0, 0), (28, 1, 1), (28, 0, 1), (1, 1, 0))):
            item = names[(ci * 5 + 1) % len(names)]
            rng = random.Random(3800 + ci)
            runes, lens = window(ws, rng)
            own = lp.ioc(runes)
            need = len(ks[item]) - NEED - sum(adv_of(lens, mode)) - 40
            off = rng.randrange(50, max(51, need))
            c = plant(runes, lens, ks[item], off, mult, model, rng, subst, mode)
            pf = os.path.join(S.TMP, f"wj2_plant{ci}.txt")
            tsv = os.path.join(S.TMP, f"wj2_plant{ci}.tsv")
            with open(pf, "w", newline="\n", encoding="utf-8") as f:
                f.write(f"# truth plant_0 item={item} offset={off} mult={mult} model={model} keep={KEEP} subst={subst} advsep={mode}\n"
                        f"W plant_0 -1\nR {' '.join(map(str, c))}\nL {' '.join(map(str, lens))}\n")
            S.run(["screen", S.rel(pf), LIB, S.rel(tsv), f"only={item}", "mults=all", f"threads={a.threads}", f"advsep={mode}"])
            ioc, bitem, boff = best(tsv)
            vout = S.run(["verify", S.rel(pf), LIB, item, str(off), str(mult), str(model), "plant_0", f"advsep={mode}"])
            vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
            blind = {}
            for other in (0, 1):
                t2 = os.path.join(S.TMP, f"wj2_plant{ci}_a{other}.tsv")
                S.run(["screen", S.rel(pf), LIB, t2, f"only={item}", "mults=all", f"threads={a.threads}", f"advsep={other}"])
                blind[other] = best(t2)[0]
            exact = boff.lstrip("-").isdigit() and int(boff) == off
            good = bitem == item and exact and ioc >= 0.9 * own and abs(vioc - ioc) < 0.02 and max(blind.values()) < S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  advsep={mode} plant {item!r} model={model} mult={mult} subst={subst}: plaintext IoC {own:.3f} (need {0.9 * own:.3f}); best {ioc:.3f} at offset {boff} (truth {off}); "
                         f"re-decode at truth {vioc:.3f}; blind: advsep=0 {blind[0]:.3f}, advsep=1 {blind[1]:.3f}")
            ci += 1
    lines.append("WORDJUMP CONTROL2 " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
