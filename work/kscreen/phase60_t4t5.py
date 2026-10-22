"""Phase 60 tests T4 and T5 on the plain kscreen library screen (same engine, decision rule and controls as the library campaign: both signs, mults 1 and 28, skip / coin models,
first 300 runes of the 8 section windows at every offset, IoC >= 1.40 then verify.py).

 T4  the Cicada OS binaries (2013 ISO, read as bytes only): tmp/folly (= wisdom), DATA/560.17, DATA/_560.00; bytes mod 29 and with rejection (bytes >= 232 dropped), forwards and backwards.
 T5  "do four unreasonable things": base-29 digits of the fractional parts of pi, e, phi, sqrt2 summed with every sign pattern over every subset of size 2-4 (aligned at digit 0);
     and the page-restart reading: windows = the 46 page starts (data/pages.txt), family = the four constants (any offset, so any "one constant per page" assignment is covered).
    python work/kscreen/phase60_t4t5.py build|controls|run|summary [--threads 4]
"""
import argparse
import itertools
import os
import random
import re
import sys

import numpy as np

import pdir_ref as P
import selftest as S
import signrules as R

sys.path.insert(0, R.WORK)
sys.path.insert(0, os.path.join(R.WORK, "layer2"))
from export import read_ksb  # noqa: E402

HERE = S.HERE
ROOT = S.ROOT
DATA = os.path.join(HERE, "data", "phase60_t4t5")
RES = os.path.join(ROOT, "results", "kscreen", "phase60_t4t5")
ARCH = os.path.join(ROOT, "Other repositories and work", "The-Complete-Cicada3301-Archive", "assets", "2013", "cicados")
FILES = {"folly": "tmp/folly", "560.17": "DATA/560.17", "_560.00": "DATA/_560.00"}


def rel(p):
    return os.path.relpath(p, HERE).replace("\\", "/")


def blob_streams():
    out = []
    for tag, f in FILES.items():
        b = np.frombuffer(open(os.path.join(ARCH, f), "rb").read(), np.uint8)
        for mode, v in (("mod", b % 29), ("rej", b[b < 232] % 29)):
            v = v.astype(np.uint8)
            out.append((f"{tag} {mode} fwd", v.tolist()))
            out.append((f"{tag} {mode} rev", v[::-1].tolist()))
    return out


def constants():
    import keystreams
    k = keystreams.constant_digits()
    return {n: list(k[f"{n} digits (base 29)"]) for n in ("pi", "e", "phi", "sqrt2")}


def combo_streams():
    c = constants()
    n = min(len(v) for v in c.values())
    A = {k: np.array(v[:n], np.int64) for k, v in c.items()}
    out = []
    for r in (2, 3, 4):
        for sub in itertools.combinations(("pi", "e", "phi", "sqrt2"), r):
            for signs in itertools.product((1, -1), repeat=r - 1):
                s = (1,) + signs
                v = sum(si * A[nm] for si, nm in zip(s, sub)) % 29
                out.append((" ".join(f"{'+' if si > 0 else '-'}{nm}" for si, nm in zip(s, sub)), v.astype(np.uint8).tolist()))
    singles = [(f"single {k}", v) for k, v in c.items()]
    return out, singles


def build():
    os.makedirs(DATA, exist_ok=True)
    P.write_ksb(os.path.join(DATA, "blobs.ksb"), blob_streams())
    combos, singles = combo_streams()
    P.write_ksb(os.path.join(DATA, "combos.ksb"), combos)
    P.write_ksb(os.path.join(DATA, "constants.ksb"), singles)
    rng = np.random.default_rng(60)
    P.write_ksb(os.path.join(DATA, "null_1m.ksb"), [("null 1.18M", rng.integers(0, 29, 1183811).astype(np.uint8).tolist())])
    print("blobs", len(blob_streams()), "combos", len(combos), "constants", len(singles))


def ctrl_plant(fam_file, item, off, mult, model, seed, threads, tag):
    plant = os.path.join(S.TMP, f"p60t45_{tag}.txt")
    tsv = os.path.join(S.TMP, f"p60t45_{tag}.tsv")
    S.run(["plant", rel(S.PLAIN), "file:" + rel(fam_file), item, str(off), str(mult), str(model), "0.18", str(seed), "0", rel(plant)])
    S.run(["screen", rel(plant), "file:" + rel(fam_file), rel(tsv), f"only={item}", f"threads={threads}"])
    best = S.window_bests(tsv)
    lines, ok = [], True
    for win, (titem, toff) in S.truths(plant).items():
        ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
        good = bitem == item and abs(int(boff) - int(toff)) <= 2 and ioc >= S.THRESHOLD
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  {tag}: plant {item!r} mult={mult} model={model} {win}: best {ioc:.3f} at offset {boff} (truth {toff})")
    return lines, ok


def controls(threads):
    lines, ok = [], True
    for tag, f, item, off, mult, model in (("T4 folly", "blobs.ksb", "folly rej fwd", 1200, 1, 0), ("T4 560.17", "blobs.ksb", "560.17 mod fwd", 700000, 28, 1),
                                           ("T4 _560.00", "blobs.ksb", "_560.00 rej fwd", 2500000, 1, 1),
                                           ("T5 pair", "combos.ksb", "+pi -e", 5000, 1, 0), ("T5 quad", "combos.ksb", "+pi +e -phi +sqrt2", 9000, 28, 1)):
        l, o = ctrl_plant(os.path.join(DATA, f), item, off, mult, model, 600 + len(lines), threads, tag)
        lines += l; ok &= o
    lines.append("PHASE60 T4/T5 CONTROLS " + ("PASSED" if ok else "FAILED"))
    os.makedirs(RES, exist_ok=True)
    open(os.path.join(RES, "controls.txt"), "w", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def screen(name, windows, family, threads, extra=()):
    tsv = os.path.join(RES, name + ".tsv")
    if not os.path.exists(tsv):
        os.makedirs(RES, exist_ok=True)
        S.run(["screen", windows, family, rel(tsv), f"threads={threads}", "top=200", *extra])
        print("done", name, flush=True)
    return tsv


def run(threads):
    screen("T4_blobs", "data/segments.txt", "file:" + rel(os.path.join(DATA, "blobs.ksb")), threads)
    screen("T4_null_1m", "data/segments.txt", "file:" + rel(os.path.join(DATA, "null_1m.ksb")), threads)
    screen("T5_combos", "data/segments.txt", "file:" + rel(os.path.join(DATA, "combos.ksb")), threads)
    screen("T5_combos_null", "data/segments.txt", "rand:72:60", threads)
    screen("T5_pages_constants", "data/pages.txt", "file:" + rel(os.path.join(DATA, "constants.ksb")), threads)
    screen("T5_pages_combos", "data/pages.txt", "file:" + rel(os.path.join(DATA, "combos.ksb")), threads)
    screen("T5_pages_null", "data/pages.txt", "rand:76:61", threads)


def run5(threads):
    for name, w, fam in (("T5_combos", "data/segments.txt", "file:" + rel(os.path.join(DATA, "combos.ksb"))), ("T5_combos_null", "data/segments.txt", "rand:72:60"),
                         ("T5_pages_constants", "data/pages.txt", "file:" + rel(os.path.join(DATA, "constants.ksb"))), ("T5_pages_combos", "data/pages.txt", "file:" + rel(os.path.join(DATA, "combos.ksb"))),
                         ("T5_pages_null", "data/pages.txt", "rand:76:61")):
        screen(name, w, fam, threads)


def best_of(tsv):
    for l in open(tsv, encoding="utf-8", errors="replace").read().split("\n"):
        if l.startswith("# best"):
            return l
    return ""


def summary():
    lines = []
    for f in sorted(os.listdir(RES)):
        if f.endswith(".tsv"):
            hd = open(os.path.join(RES, f), encoding="utf-8", errors="replace").readline()
            lines.append(f"{f[:-4]}: {best_of(os.path.join(RES, f))}  runs={re.search(r'runs=(\d+)', hd).group(1) if re.search(r'runs=(\d+)', hd) else '?'}")
    t = "\n".join(lines) + "\n"
    open(os.path.join(RES, "summary.txt"), "w", newline="\n").write(t)
    print(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd"); ap.add_argument("--threads", type=int, default=4)
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    {"run5": lambda: run5(a.threads), "build": build, "controls": lambda: controls(a.threads), "run": lambda: run(a.threads), "summary": summary}[a.cmd]()
