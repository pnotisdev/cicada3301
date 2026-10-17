"""Controls for the per-rune periodic sign templates (signrules_periodic.py). Same design as sign_selftest.py: an independent Python planter (not the engine's `plant`) enciphers held-out English with c = p + s_i * k, s_i = pattern[i mod L], the anti-repeat
rule as in the engine and a library key at a known offset; the S line holds the signs. For three templates (period 2, 3 and 5) the screen must return the planted item as the window's best hit with IoC >= 1.40, the re-decode at the truth must reach 1.40; the
same ciphertext WITHOUT the S line and with another template's S line (about 50% agreement) must stay below 1.40 at the truth; the S vector must equal signrules_periodic.vector. Null: random keystreams under a template's signs stay below 1.40.

    python work/kscreen/sign_periodic_selftest.py [--threads N] [--out results/kscreen/sign_periodic_selftest.txt]
"""
import argparse
import os
import random
import re
import sys

import selftest as S
import sign_selftest as T
import signrules_periodic as P

sys.path.insert(0, os.path.join(P.R.WORK, "layer2"))
from export import read_ksb  # noqa: E402

CASES = [((1, -1), "primes-1 (totient)", 1, 0), ((1, 1, -1), "pi digits (base 29)", 28, 1), ((1, -1, -1, 1, -1), "sha256-ctr reject :3301", 1, 0)]
Q = 29


def plant(runes, key, mult, model, keep, pat, rng):
    mk = [k * mult % Q for k in key]
    c, signs, j, prev = [], P.vector(pat, len(runes)), 0, -1
    for i, p in enumerate(runes):
        kv = lambda x: (Q - mk[x]) % Q if signs[i] < 0 else mk[x]
        y = (p + kv(j)) % Q
        j += 1
        if model == 0:
            tries = 0
            while prev >= 0 and y == prev and rng.random() >= keep and tries < 5:
                y = (p + kv(j)) % Q
                j += 1
                tries += 1
        elif prev >= 0 and y == prev:
            j += 1
            if rng.random() >= keep:
                y = (p + kv(j)) % Q
                j += 1
        c.append(y)
        prev = y
    return c, signs


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(S.OUT, "sign_periodic_selftest.txt"))
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    ksb = dict(read_ksb(os.path.join(S.HERE, "data", "library.ksb")))
    wins = T.plain_windows()
    lines, ok = [], True
    for ci, (pat, item, mult, model) in enumerate(CASES):
        rng = random.Random(1700 + ci)
        key = [int(x) for x in ksb[item]]
        entries, wrong = [], []
        other = tuple(-x if i % 2 else x for i, x in enumerate((1, 1, -1, -1, 1)[:len(pat)])) if len(pat) > 2 else (1, 1)
        for wi, (runes, lens) in enumerate(wins):
            off = (1234 + 997 * wi) % (len(key) - len(runes) * 4 - 64)
            c, signs = plant(runes, key[off:], mult, model, 0.18, pat, rng)
            assert signs == P.vector(pat, len(c))
            entries.append((f"plant_{wi}", c, lens, signs, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
            wrong.append((f"plant_{wi}", c, lens, [(1, 1, -1)[i % 3] for i in range(len(c))], entries[-1][4]))
        f = os.path.join(S.TMP, f"signp_plant{ci}.txt")
        T.write(f, entries)
        T.write(os.path.join(S.TMP, f"signp_plant{ci}_nosign.txt"), [(n, c, l, None, t) for n, c, l, _, t in entries])
        T.write(os.path.join(S.TMP, f"signp_plant{ci}_wrong.txt"), wrong)
        tsv = os.path.join(S.TMP, f"signp_plant{ci}.tsv")
        S.run(["screen", S.rel(f), T.FAMILY, S.rel(tsv), f"only={item}", f"threads={a.threads}"])
        best = S.window_bests(tsv)
        for wi, (win, (_, toff)) in enumerate(S.truths(f).items()):
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            ver = lambda fn: float(re.search(r"ioc ([\d.]+)", S.run(["verify", S.rel(fn), T.FAMILY, item, toff, str(mult), str(model), win])).group(1))
            v_ok, v_no, v_wr = ver(f), ver(os.path.join(S.TMP, f"signp_plant{ci}_nosign.txt")), ver(os.path.join(S.TMP, f"signp_plant{ci}_wrong.txt"))
            agree = sum(x == y for x, y in zip(entries[wi][3], wrong[wi][3])) / len(entries[wi][3])
            blind_wr = (v_wr < S.THRESHOLD) if agree <= 0.7 else True
            good = bitem == item and ioc >= S.THRESHOLD and v_ok >= S.THRESHOLD and v_no < S.THRESHOLD and blind_wr
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  template {P.name_of(pat)} plant {item!r} model={model} mult={mult} {win}: best {ioc:.3f} at offset {boff} (truth {toff}); re-decode with its signs {v_ok:.3f}, without signs {v_no:.3f}, "
                         f"with the +,+,- template's signs {v_wr:.3f} ({100 * agree:.0f}% agreement{'' if agree <= 0.7 else ', not required to fail'})")
    nulls = os.path.join(S.TMP, "signp_null.tsv")
    S.run(["screen", S.rel(os.path.join(P.OUT, "P3_ppm.txt")), "rand:30:4242", S.rel(nulls), f"threads={a.threads}"])
    nbest = max(v[0] for v in S.window_bests(nulls).values())
    good = nbest < S.THRESHOLD
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  null: 30 random keystreams under the signs of template P3_ppm on the 8 LP2 windows: best IoC {nbest:.3f} (must stay below {S.THRESHOLD})")
    lines.append("SIGN PERIODIC SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    with open(a.out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
