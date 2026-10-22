"""Phase 50 item (iv): mechanism crossings. The 10 strongest of the 61 word-level sign rules (best IoC of their own screen,
results/kscreen/signs/<rule>.tsv) x nulledge=1 / nulledge=2 / advsep=1 / advsep=2 (a word-final / word-initial keyless null,
an extra key value at every word boundary / also at every line or page break).

    python work/phase50/sign_cross.py control            # planted keys under (rule, mechanism)
    python work/phase50/sign_cross.py run [--threads 12] [--third 3]

PILOT SCALE: the streams are every THIRD stream of data/library_flat.ksb (the 581 flat streams of the sign campaign), because
40 full screens are about 5 h; a hit in a stream that is not in the subset is not seen.
The planter is independent of the engine's `plant` (as sign_selftest.py's): word by word, sign from the rule before the word is
enciphered (current ciphertext length, previous ciphertext words), key pointer, skip rule as in the engine, then the mechanism:
nulledge inserts one random keyless rune at every word end / start (L = plaintext length + 1), advsep advances the key pointer by one
before every word after the first (and, for advsep=2, at synthetic line breaks listed in a B line).
"""
import argparse
import os
import random
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reorder as R  # noqa: E402
import signrules as SR  # noqa: E402

Q = 29
MECHS = [("nulledge", 1), ("nulledge", 2), ("advsep", 1), ("advsep", 2)]
CTL_RULES = ["E_cur_n4", "B5_cur_w", "A_prev_pf"]
SD = os.path.join(R.KS, "data", "signs")
TD = os.path.join(R.KS, "data", "phase50")


def read_ksb(path):
    b = open(path, "rb").read()
    assert b[:4] == b"KSB1"
    p, out = 8, []
    for _ in range(struct.unpack_from("<I", b, 4)[0]):
        ln = struct.unpack_from("<H", b, p)[0]
        name = b[p + 2:p + 2 + ln].decode("utf-8")
        p += 2 + ln
        L = struct.unpack_from("<I", b, p)[0]
        out.append((name, b[p + 4:p + 4 + L]))
        p += 4 + L
    return out


def top_rules(k=10):
    rows = []
    for name in open(os.path.join(R.KS, "sign_rules.txt")).read().split():
        t = open(os.path.join(R.ROOT, "results", "kscreen", "signs", name + ".tsv"), encoding="utf-8").read(4000)
        rows.append((-float(re.search(r"# best ([\d.]+)", t).group(1)), name))
    return [n for _, n in sorted(rows)[:k]]


def subset(third):
    path = os.path.join(TD, f"library_flat_third{third}.ksb")
    ks = read_ksb(os.path.join(R.KS, "data", "library_flat.ksb"))[::third]
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(ks)))
        for name, v in ks:
            nb = name.encode("utf-8")[:300]
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v))
    return path, [n for n, _ in ks]


def window_file_with_b(rule):
    """the rule's sign windows plus the B (line / page break) lines of data/segments.txt, for advsep=2"""
    b = {}
    cur = None
    for l in open(os.path.join(R.KS, "data", "segments.txt")).read().split(chr(10)):
        if l.startswith("W "):
            cur = l.split()[1]
        elif l.startswith("B "):
            b[cur] = l
    out, cur = [], None
    for l in open(os.path.join(SD, rule + ".txt")).read().split(chr(10)):
        out.append(l)
        if l.startswith("W "):
            cur = l.split()[1]
        elif l.startswith("S ") and cur in b:
            out.append(b[cur])
    path = os.path.join(TD, f"signs_B_{rule}.txt")
    open(path, "w", newline="\n").write(chr(10).join(out))
    return path


def plant(runes, lens, key, mult, rule, mech, rng, keep=0.18):
    """cipher, lens (ciphertext), signs, breaks. skip model (model 0)."""
    kind, v = mech
    mk = [k * mult % Q for k in key]
    c, L, signs, words, brk = [], [], [], [], []
    j, prev, pos = 0, -1, 0
    for w, n in enumerate(lens):
        cn = n + (1 if kind == "nulledge" else 0)
        s = rule(words + [dict(n=cn, w=w + 1, wp=w + 1, ws=w + 1)], w)
        if kind == "advsep" and w > 0:
            j += 1
        word = []
        if kind == "nulledge" and v == 2:
            word.append(rng.randrange(Q))
        for p in runes[pos:pos + n]:
            kv = lambda x: (Q - mk[x]) % Q if s < 0 else mk[x]
            if kind == "advsep" and v == 2 and len(c) + len(word) > 0 and (len(c) + len(word)) % 23 == 0:
                j += 1
                brk.append(len(c) + len(word))
            y = (p + kv(j)) % Q
            j += 1
            tries = 0
            while prev >= 0 and y == prev and rng.random() >= keep and tries < 5:
                y = (p + kv(j)) % Q
                j += 1
                tries += 1
            word.append(y)
            prev = y
        if kind == "nulledge" and v == 1:
            word.append(rng.randrange(Q))
        c += word
        L.append(len(word))
        signs += [s] * len(word)
        words.append(dict(n=len(word), w=w + 1, wp=w + 1, ws=w + 1, **SR.numbers(word)))
        pos += n
    return c, L, signs, brk


def control(third, threads):
    lib, names = subset(third)
    rules = SR.build_rules()
    ksb = dict(read_ksb(lib))
    lines = open(os.path.join(R.WORK, "phpmt", "data", "english.txt")).read().split(chr(10))
    wins = [([int(x) for x in lines[k + 1][2:].split()], [int(x) for x in lines[k + 2][2:].split()]) for k in range(0, len(lines) - 2, 3)]
    res, ok = [], True
    for rname in CTL_RULES:
        for mi, mech in enumerate(MECHS):
            rng = random.Random(900 + mi)
            item = [n for n in names if len(ksb[n]) >= 15000][3 + mi]      # aperiodic streams only: a short period has no offset
            key = [int(x) for x in ksb[item]]
            f = os.path.join(TD, f"cross_ctl_{rname}_{mech[0]}{mech[1]}.txt")
            ents, truth = [], []
            for wi, (runes, lens) in enumerate(wins):
                off = (1234 + 997 * wi) % (len(key) - len(runes) * 4 - 64)
                c, L, s, brk = plant(runes, lens, key[off:], 1, rules[rname], mech, rng)
                ents.append(f"W plant_{wi} -1\nR {' '.join(map(str, c))}\nL {' '.join(map(str, L))}\nS {' '.join(map(str, s))}"
                            + (f"\nB {' '.join(map(str, brk))}" if brk else ""))
                truth.append(off)
            open(f, "w", newline="\n").write(chr(10).join(ents) + chr(10))
            tsv = f.replace(".txt", ".tsv").replace(TD, R.OUT)
            R.kscreen(["screen", R.rel(f), "file:" + R.rel(lib), R.rel(tsv), f"only={item}", "mults=1", "models=0", f"threads={threads}",
                       f"{mech[0]}={mech[1]}"])
            b = R.best(tsv)
            for wi, t in enumerate(truth):
                ioc, bi, bo = b[f"plant_{wi}"]
                good = bi == item and abs(int(bo) - t) <= 10 and ioc >= 1.40
                ok &= good
                res.append(f"{'PASS' if good else 'FAIL'} plant {rname} x {mech[0]}={mech[1]} {item[:30]!r} plant_{wi}: best {ioc:.3f} at {bo} (truth {t})")
    return ok, res


def run(third, threads):
    lib, names = subset(third)
    ok, ctl = control(third, threads)
    print(f"control {'PASS' if ok else 'FAIL'} {sum('PASS' in x for x in ctl)}/{len(ctl)}", flush=True)
    out = [f"sign crossings (pilot: every {third}rd flat stream = {len(names)} streams): control {'PASS' if ok else 'FAIL'} "
           f"{sum('PASS' in x for x in ctl)}/{len(ctl)}"] + ctl
    for rule in top_rules():
        for kind, v in MECHS:
            win = window_file_with_b(rule) if (kind, v) == ("advsep", 2) else os.path.join(SD, rule + ".txt")
            tag = f"{rule}_{kind}{v}"
            nul, hit = os.path.join(R.OUT, f"cross_{tag}_null.tsv"), os.path.join(R.OUT, f"cross_{tag}.tsv")
            flag = f"{kind}={v}"
            if not os.path.exists(nul):
                R.kscreen(["screen", R.rel(win), "rand:60:6060", R.rel(nul), f"threads={threads}", flag])
            if not os.path.exists(hit):
                R.kscreen(["screen", R.rel(win), "file:" + R.rel(lib), R.rel(hit), "mults=1,28", "models=0,1", f"threads={threads}", flag])
            bn, bh = R.best(nul), R.best(hit)
            v_ = subprocess.run([sys.executable, os.path.join(R.KS, "verify.py"), hit, "--top", "5", "--controls", "20", "--out",
                                 os.path.join(R.OUT, f"cross_{tag}_verify.txt")], capture_output=True, text=True)
            line = (f"{rule:12s} x {flag:11s}: best {max(x[0] for x in bh.values()):.4f}, null best {max(x[0] for x in bn.values()):.4f}; "
                    f"{v_.stdout.strip().splitlines()[-1][:60]}")
            print(line, flush=True)
            out.append(line)
            open(os.path.join(R.OUT, "summary_cross.txt"), "w", encoding="utf-8", newline="\n").write(chr(10).join(out) + chr(10))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--threads", type=int, default=12)
    ap.add_argument("--third", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(R.OUT, exist_ok=True)
    os.makedirs(TD, exist_ok=True)
    if a.cmd == "control":
        ok, res = control(a.third, a.threads)
        print("\n".join(res), "\nCONTROL", "PASS" if ok else "FAIL")
    else:
        run(a.third, a.threads)
