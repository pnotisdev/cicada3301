"""Positive and blindness controls for the signed-artifact streams (work/kscreen/signed.py). A negative from `kscreen screen ... file:data/signed.ksb` only counts if this passes.

An independent Python planter (it does not call the engine's `plant`, which needs streams of 1,664 values) encrypts the first 300 runes of held-out English
(work/phpmt/data/english.txt) under the anti-repeat rule with one stream of every family: the shortest and the longest stream of the family, skip model / coin model,
key multiplier 1 / 28, plain / substituted plaintext alphabet. The unchanged engine (mults=all, as in the campaign) must return that stream at the planted offset as the
window's best hit (within 5 offsets of the plant: the skip model's alias, as in the other selftests) with IoC >= 1.40, a full re-decode at the truth must also reach 1.40 (the rules of selftest.py),
and a stream of another class (a signature value for a blob plant and vice versa; the concatenations contain the single blocks, so those cannot serve as wrong keys of their own parts) must stay below 1.40 on the same window.

    python work/kscreen/signed_selftest.py [--threads N] [--out results/kscreen/signed_selftest.txt]
"""
import argparse
import os
import random
import re
import struct
import sys

import selftest as S

HERE = S.HERE
FAMILY = "file:data/signed.ksb"
Q = 29
NEED = 383                          # key values a 300-rune window needs: n + n/4 + 8
KEEP = 0.18                         # chance that a would-be doublet survives (the fitted 81% enforcement)


def read_ksb(path):
    b = open(path, "rb").read()
    assert b[:4] == b"KSB1"
    n = struct.unpack_from("<I", b, 4)[0]
    p, out = 8, {}
    for _ in range(n):
        (ln,) = struct.unpack_from("<H", b, p)
        p += 2
        name = b[p:p + ln].decode("utf-8")
        p += ln
        (m,) = struct.unpack_from("<I", b, p)
        p += 4
        out[name] = list(b[p:p + m])
        p += m
    return out


def read_plain(path, idx=0):
    runes, lens = None, None
    cur = -1
    for line in open(path, encoding="utf-8").read().splitlines():
        if line.startswith("W "):
            cur += 1
        elif cur == idx and line.startswith("R "):
            runes = [int(x) for x in line[2:].split()]
        elif cur == idx and line.startswith("L "):
            lens = [int(x) for x in line[2:].split()]
    return runes, lens


def trim_lens(lens, n):
    out, tot = [], 0
    for x in lens:
        if tot + x >= n:
            out.append(n - tot)
            break
        out.append(x)
        tot += x
    return out


def plant(runes, key, off, mult, model, rng, subst):
    d = list(range(Q))
    if subst:
        rng.shuffle(d)
    mk = [(k * mult) % Q for k in key[off:]]
    j, prev, out = 0, -1, []
    for p in runes:
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


def klass(name):
    """which kind of block a stream was made from: the concatenations contain the single blocks, so a 'wrong key' must come from another class"""
    return "blob" if "blob" in name else "message" if "message" in name else "sig"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(S.OUT, "signed_selftest.txt"))
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    ks = read_ksb(os.path.join(HERE, "data", "signed.ksb"))
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
            pf = os.path.join(S.TMP, f"signed_plant{ci}.txt")
            tsv = os.path.join(S.TMP, f"signed_plant{ci}.tsv")
            with open(pf, "w", newline="\n", encoding="utf-8") as f:
                f.write(f"# truth plant_0 item={item} offset={off} mult={mult} model={model} keep={KEEP} subst={subst}\n"
                        f"W plant_0 -1\nR {' '.join(map(str, c))}\nL {' '.join(map(str, trim_lens(lens, 300)))}\n")
            S.run(["screen", S.rel(pf), FAMILY, S.rel(tsv), f"only={item}", "mults=all", f"threads={a.threads}"])
            ioc, bitem, boff = S.window_bests(tsv).get("plant_0", (0.0, "-", "-"))
            vout = S.run(["verify", S.rel(pf), FAMILY, item, str(off), str(mult), str(model), "plant_0"])
            vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
            wrong = max((x for x in names if klass(x) != klass(item)), key=lambda x: len(ks[x]))
            wtsv = os.path.join(S.TMP, f"signed_plant{ci}_wrong.tsv")
            S.run(["screen", S.rel(pf), FAMILY, S.rel(wtsv), f"only={wrong}", "mults=all", f"threads={a.threads}"])
            wioc = S.window_bests(wtsv).get("plant_0", (0.0, "-", "-"))[0]
            # a few offsets of difference are the skip-model alias (the decode starts a key value or two off and absorbs it in its first skips), as in the other selftests
            near = boff.lstrip("-").isdigit() and abs(int(boff) - off) <= 5
            good = bitem == item and near and ioc >= S.THRESHOLD and vioc >= S.THRESHOLD and wioc < S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  {fam} plant {item!r} (len {len(ks[item])}) model={model} mult={mult} subst={subst}: best {ioc:.3f} at offset {boff} (truth {off}); "
                         f"re-decode at truth {vioc:.3f}; wrong stream {wrong!r} best {wioc:.3f}")
            ci += 1
    lines.append("SIGNED SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
