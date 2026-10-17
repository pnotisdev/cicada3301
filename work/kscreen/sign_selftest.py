"""Controls for the word-level sign rules (signrules.py, the engine's S lines).

An independent Python planter (not the engine's `plant`) enciphers held-out English word by word with c = p + s_w * k under a sign rule, the sign of word w computed from the rule BEFORE the word is enciphered (current length and position, previous
words' ciphertext), the anti-repeat rule as in the engine (skip / coin, keep 0.18) and a library key at a known offset; the sign vector is written as the S line. For each of four rules the screen must return the planted item as the window's best hit
with IoC >= 1.40 and the re-decode at the truth must reach 1.40 (positive control); the same ciphertext WITHOUT its S line, and with the S line of another rule, must stay below 1.40 at the truth (blindness: the control is about the signs); and signrules.py
must reproduce the planter's sign vector from the planted ciphertext (consistency). Null: random keystreams under a rule's signs stay below 1.40.

    python work/kscreen/sign_selftest.py [--threads N] [--out results/kscreen/sign_selftest.txt]
"""
import argparse
import os
import random
import re
import sys

import selftest as S
import signrules as R

sys.path.insert(0, os.path.join(R.WORK, "layer2"))
from export import read_ksb  # noqa: E402

HERE = S.HERE
FAMILY = "file:data/library.ksb"
CASES = [("E_cur_n4", "primes-1 (totient)", 1, 0), ("A_prev_G", "pi digits (base 29)", 28, 1), ("B5_prev_R", "sha256-ctr reject :3301", 1, 0), ("C_prev_n", "primes-1 (totient)", 28, 1)]
Q = 29


def plain_windows():
    lines = open(S.PLAIN, encoding="utf-8").read().splitlines()
    return [([int(x) for x in lines[k + 1][2:].split()], [int(x) for x in lines[k + 2][2:].split()]) for k in range(0, len(lines), 3)]


def plant(runes, lens, key, mult, model, keep, rule, rng):
    """cipher runes and the sign vector; `rule` sees the table of the words so far (previous ciphertext) and the current word's n and position only"""
    mk = [k * mult % Q for k in key]
    c, signs, words, j, prev, pos = [], [], [], 0, -1, 0
    for w, n in enumerate(lens):
        table = words + [dict(n=n, w=w + 1, wp=w + 1, ws=w + 1)]
        s = rule(table, w)
        word = []
        for p in runes[pos:pos + n]:
            kv = lambda x: (Q - mk[x]) % Q if s < 0 else mk[x]
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
            word.append(y)
            signs.append(s)
            prev = y
        pos += n
        words.append(dict(n=n, w=w + 1, wp=w + 1, ws=w + 1, **R.numbers(word)))
    return c, signs


def write(path, entries):
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        for name, c, lens, signs, truth in entries:
            if truth:
                f.write(truth + "\n")
            f.write(f"W {name} -1\nR {' '.join(map(str, c))}\nL {' '.join(map(str, lens))}\n")
            if signs is not None:
                f.write(f"S {' '.join(map(str, signs))}\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(S.OUT, "sign_selftest.txt"))
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    rules = R.build_rules()
    ksb = dict(read_ksb(os.path.join(HERE, "data", "library.ksb")))
    wins = plain_windows()
    lines, ok = [], True
    for ci, (rname, item, mult, model) in enumerate(CASES):
        rng = random.Random(700 + ci)
        key = [int(x) for x in ksb[item]]
        entries, truths = [], []
        for wi, (runes, lens) in enumerate(wins):
            off = (1234 + 997 * wi) % (len(key) - len(runes) * 4 - 64)
            c, signs = plant(runes, lens, key[off:], mult, model, 0.18, rules[rname], rng)
            # consistency: signrules.py recomputes the planter's signs from the planted ciphertext
            spans, a0 = [], 0
            for n in lens:
                spans.append((a0, a0 + n))
                a0 += n
            again = R.sign_vector(rules[rname], R.word_table(c, spans), spans, len(c))
            assert again == signs, f"{rname}: signrules.py and the planter disagree"
            entries.append((f"plant_{wi}", c, lens, signs, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
            truths.append(off)
        plant_f = os.path.join(S.TMP, f"sign_plant{ci}.txt")
        write(plant_f, entries)
        write(os.path.join(S.TMP, f"sign_plant{ci}_nosign.txt"), [(n, c, l, None, t) for n, c, l, _, t in entries])
        def sv(rule, c, lens):
            spans, a0 = [], 0
            for n in lens:
                spans.append((a0, a0 + n))
                a0 += n
            return R.sign_vector(rule, R.word_table(c, spans), spans, len(c))
        c0, l0, true0 = entries[0][1], entries[0][2], entries[0][3]
        other_name = min((n for n in rules if n != rname), key=lambda n: abs(sum(x == y for x, y in zip(sv(rules[n], c0, l0), true0)) / len(true0) - 0.5))
        other = rules[other_name]
        wrong = []
        for (n, c, l, _, t), (runes, lens) in zip(entries, wins):
            spans, a0 = [], 0
            for ln in lens:
                spans.append((a0, a0 + ln))
                a0 += ln
            wrong.append((n, c, l, R.sign_vector(other, R.word_table(c, spans), spans, len(c)), t))
        write(os.path.join(S.TMP, f"sign_plant{ci}_wrong.txt"), wrong)
        tsv = os.path.join(S.TMP, f"sign_plant{ci}.tsv")
        S.run(["screen", S.rel(plant_f), FAMILY, S.rel(tsv), f"only={item}", f"threads={a.threads}"])
        best = S.window_bests(tsv)
        for wi, (win, (titem, toff)) in enumerate(S.truths(plant_f).items()):
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            ver = lambda f: float(re.search(r"ioc ([\d.]+)", S.run(["verify", S.rel(f), FAMILY, item, toff, str(mult), str(model), win])).group(1))
            v_ok, v_no, v_wr = ver(plant_f), ver(os.path.join(S.TMP, f"sign_plant{ci}_nosign.txt")), ver(os.path.join(S.TMP, f"sign_plant{ci}_wrong.txt"))
            true_s = entries[wi][3]
            share = true_s.count(-1) / len(true_s)
            agree = sum(x == y for x, y in zip(wrong[wi][3], true_s)) / len(true_s)
            blind_no = (v_no < S.THRESHOLD) if 0.3 <= share <= 0.7 else True         # an unsigned decode is only expected to fail when 30-70% of the runes are flipped
            blind_wr = (v_wr < S.THRESHOLD) if agree <= 0.7 else True
            good = bitem == item and ioc >= S.THRESHOLD and v_ok >= S.THRESHOLD and blind_no and blind_wr
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  rule {rname} plant {item!r} model={model} mult={mult} {win}: best {ioc:.3f} at offset {boff} (truth {toff}); re-decode with its signs {v_ok:.3f}; "
                         f"without signs {v_no:.3f} ({100 * share:.0f}% of the runes flipped{'' if 0.3 <= share <= 0.7 else ', not required to fail'}); with {other_name}'s signs {v_wr:.3f} "
                         f"({100 * agree:.0f}% agreement{'' if agree <= 0.7 else ', not required to fail'})")
    nulls = os.path.join(S.TMP, "sign_null.tsv")
    S.run(["screen", S.rel(os.path.join(R.OUT, "E_cur_n4.txt")), "rand:30:4242", S.rel(nulls), f"threads={a.threads}"])
    nbest = max(v[0] for v in S.window_bests(nulls).values())
    good = nbest < S.THRESHOLD
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  null: 30 random keystreams under the signs of rule E_cur_n4 on the 8 LP2 windows: best IoC {nbest:.3f} (must stay below {S.THRESHOLD})")
    lines.append("SIGN SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
