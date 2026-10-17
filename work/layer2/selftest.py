"""Positive, blindness and null controls for the two-layer screen (work/layer2). A layer2 null only counts if this passes.

    python work/layer2/selftest.py [--threads N] [--out results/layer2/selftest.txt]

Every plant is written by plant_ref.py (the two-layer cipher in Python, from the library's stream values), not by the engine.
Positive (mode=bigram): held-out English (data/plain.txt, 3 windows of ~400 runes) enciphered with a solved-page keyword
inside (with and without the literal-F rule, plain and Atbash alphabet, both inner signs) and a library number stream
outside (skip and coin models, both outer signs). The screen over offsets 0..4000 of that stream must put each window's
best hit within 2 of the true offset with the right keyword and a score of at least +2.0 per rune; the whole-window
re-decode at the truth must beat its matched null by 5 (verify.py's rule).
Positive (mode=periodic, any keyword): a keyword that is NOT in the keyword file, found through its period and the
keyword estimate of verify.py.
Blindness: kscreen at the true offset of the first plant must stay below its 1.40 threshold (so H-LAYER was invisible
to every earlier screen and this one is needed).
Null: random streams through the same bigram screen on the 8 LP2 section windows must stay below +2.0 per rune.
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ROOT = os.path.dirname(WORK)
BIN = os.path.join(HERE, "target", "release", "layer2" + (".exe" if os.name == "nt" else ""))
KS_BIN = os.path.join(WORK, "kscreen", "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
TMP = os.path.join(WORK, "tmp", "layer2")
THRESH = 2.0

# stream, offset, outer mult, model, keyword, phase, inner sign, literal F, Atbash
PLANTS = [
    ("primes-1 (totient)", 1234, 1, 0, "DIVINITY", 3, 1, 1, 0),
    ("pi digits (base 29)", 777, 28, 1, "FIRFUMFERENFE", 0, 28, 0, 1),
    ("phi(n)", 321, 1, 1, "CIRCUMFERENCE", 5, 1, 1, 1),
]
PERIODIC = ("primes", 2000, 1, 0, [7, 18, 4, 3, 16, 24], 2, 1, 0, 0)   # a keyword outside the file, period 6, litf 0


def rel(p):
    return os.path.relpath(p, HERE).replace("\\", "/")


def run(args, binary=BIN, cwd=HERE):
    r = subprocess.run([binary] + args, cwd=cwd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"{os.path.basename(binary)} {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def write_plant(path, item, off, mult, model, coin_seed, kw, phase, isign, litf, atb):
    """plant with the independent Python planter (plant_ref.py), not the engine's own plant mode"""
    import plant_ref
    text = plant_ref.plant(os.path.join(HERE, "data", "plain.txt"), os.path.join(HERE, "data", "core.ksb"), item, off, mult, model, 0.18,
                           coin_seed, kw, phase, isign, litf, atb)
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)


def keywords():
    out = {}
    for line in open(os.path.join(HERE, "data", "keywords.txt"), encoding="utf-8"):
        if line.strip() and not line.startswith("#"):
            p = line.split()
            out[p[0]] = [int(x) for x in p[1:]]
    return out


def window_bests(tsv):
    out = {}
    for line in open(tsv, encoding="utf-8"):
        m = re.match(r"# window (\S+) best (\S+) item=(.*) offset=(\d+) mult=(\d+) model=(\d+) (.*)$", line)
        if m:
            out[m.group(1)] = (float(m.group(2)), m.group(3), int(m.group(4)), m.group(7))
    return out


def truths(plant_file):
    out = {}
    for line in open(plant_file, encoding="utf-8"):
        m = re.match(r"# truth (\S+) item=(.*) offset=(\d+) ", line)
        if m:
            out[m.group(1)] = int(m.group(3))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(ROOT, "results", "layer2", "selftest.txt"))
    a = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)
    kws = keywords()
    solved = os.path.join(TMP, "kw_solved.txt")
    with open(solved, "w", newline="\n", encoding="utf-8") as f:
        for w in ("DIVINITY", "FIRFUMFERENFE", "CIRCUMFERENCE"):
            f.write(w + " " + " ".join(map(str, kws[w])) + "\n")
    lines, ok = [], True
    fam = "file:data/core.ksb"
    for pi, (item, off, mult, model, kw, ph, isign, litf, atb) in enumerate(PLANTS):
        plant = os.path.join(TMP, f"selftest_plant{pi}.txt")
        tsv = os.path.join(TMP, f"selftest_plant{pi}.tsv")
        write_plant(plant, item, off, mult, model, 10 + pi, kws[kw], ph, isign, litf, atb)
        run(["screen", rel(plant), fam, rel(tsv), "mode=bigram", f"kw={rel(solved)}", f"only={item}", "offs=0:4000",
             f"threads={a.threads}"])
        best = window_bests(tsv)
        for win, toff in truths(plant).items():
            sc, bitem, boff, inner = best[win]
            good = bitem == item and abs(boff - toff) <= 2 and f"kw={kw} " in inner + " " and sc >= THRESH
            vout = run(["verify", rel(plant), fam, item, str(toff), str(mult), str(model), win, "mode=bigram",
                        "kwvals=" + ",".join(map(str, kws[kw])), f"isign={isign}", f"phase={ph}", f"litf={litf}", f"atb={atb}",
                        "controls=20"])
            vsc = float(re.search(r"score (-?[\d.]+)", vout).group(1))
            cmax = float(re.search(r"controls \d+ random offsets: mean (-?[\d.]+) max (-?[\d.]+)", vout).group(2))
            good &= vsc >= THRESH and vsc >= cmax + 5
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  bigram plant {item!r} kw={kw} litf={litf} atb={atb} isign={isign} "
                         f"mult={mult} model={model} {win}: best {sc:+.3f} at offset {boff} (truth {toff}) [{inner}]; "
                         f"whole window at truth {vsc:+.3f}, matched null max {cmax:+.3f}")
        if pi == 0:
            # blindness: the ordinary screen at the true offset sees only the Vigenere layer
            kplant = os.path.join(TMP, "selftest_plant0_ks.txt")
            with open(plant, encoding="utf-8") as fi, open(kplant, "w", newline="\n", encoding="utf-8") as fo:
                fo.write(fi.read())
            ks_out = run(["verify", os.path.relpath(kplant, os.path.join(WORK, "kscreen")).replace("\\", "/"),
                          "file:data/library.ksb", item, str(off), str(mult), str(model), "plant_0"],
                         binary=KS_BIN, cwd=os.path.join(WORK, "kscreen"))
            kioc = float(re.search(r"ioc ([\d.]+)", ks_out).group(1))
            good = kioc < 1.40
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  blindness: kscreen re-decode of plant 0 at its true offset: IoC {kioc:.3f} "
                         f"(below its 1.40 threshold, so earlier screens could not see H-LAYER)")
    # periodic mode with a keyword outside the file
    item, off, mult, model, kwv, ph, isign, litf, atb = PERIODIC
    plant = os.path.join(TMP, "selftest_periodic.txt")
    tsv = os.path.join(TMP, "selftest_periodic.tsv")
    write_plant(plant, item, off, mult, model, 77, kwv, ph, isign, litf, atb)
    run(["screen", rel(plant), fam, rel(tsv), "mode=periodic", f"only={item}", "ms=2:12", "litf=0", f"offs={off - 300}:{off + 2300}",
         f"threads={a.threads}"])
    best = window_bests(tsv)
    vrep = subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), tsv, "--top", "3", "--controls", "10"],
                          capture_output=True, text=True, cwd=HERE)
    for win, toff in truths(plant).items():
        sc, bitem, boff, inner = best[win]
        cand = [l for l in vrep.stdout.splitlines() if l.startswith("CANDIDATE") and f" {win} " in f" {l} " and
                f"offset={boff}" in l]
        good = abs(boff - toff) <= 2 and bool(cand)
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  periodic plant (keyword not in the file, m=6) {win}: best z {sc:.2f} at offset "
                     f"{boff} (truth {toff}) [{inner}]; keyword estimate + bigram re-decode: "
                     f"{'candidate' if cand else 'not recovered'}")
    # null: random streams through the bigram screen on LP2's section windows
    null_tsv = os.path.join(TMP, "selftest_null.tsv")
    run(["screen", "../kscreen/data/segments.txt", "rand:3:4242", rel(null_tsv), "mode=bigram", f"kw={rel(solved)}",
         "offs=0:3000", f"threads={a.threads}"])
    nbest = max(v[0] for v in window_bests(null_tsv).values())
    good = nbest < THRESH
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  null: 3 random streams x 3000 offsets x the solved keywords (all phases, signs, "
                 f"literal F, Atbash) x 8 LP2 windows: best {nbest:+.3f} per rune (must stay below {THRESH})")
    lines.append("SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
