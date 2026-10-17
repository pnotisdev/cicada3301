"""Controls for kscreen-hyp (docs/HYPOTHESES.md H3-H6). A negative of that campaign only counts if this passes.

    python work/kscreen/hyp_selftest.py [--threads N] [--out results/kscreen/hyp_selftest.txt]

1. Planted keys: one stream of each new family (a decimated library stream, a text prefix sum, a deep constant block,
   LP2's ciphertext read backwards under multiplier 7) planted into held-out English under the anti-repeat rule, as in
   selftest.py: each must be its window's best hit at IoC >= 1.40 and re-decode to >= 1.40 at the true offset.
2. Ciphertext autokey through the guarded self-key path: English enciphered as c_i = p_i + s_j, where s is a random
   primer of L = 500 runes followed by the ciphertext itself (skip rule, keep 0.18), must be found at offset 0 of s with
   the window's G line set.
3. The guard: LP2 section 0.8 decoded with LP2's own ciphertext 0-12 runes behind itself degenerates without the G line
   (an IoC far above 1.40, the all-zero "plaintext") and stays below 1.40 with it.
"""
import argparse
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))
import export  # noqa: E402
import selftest as st  # noqa: E402

N = 29
# family, item, offset, multiplier, model, substitution, extra screen options
CASES = [
    ("file:data/library_hyp.ksb", "dec7:primes-1 (totient)", "321", 1, 0, 0, []),
    ("file:data/library_hyp.ksb", "Self-Reliance prefix sum of prime values", "2345", 28, 1, 1, []),
    ("file:data/library_hyp.ksb", "pi digits (base 29) from position 1000000", "777", 1, 1, 0, []),
    ("file:data/library_h5.ksb", "LP2 ciphertext (reversed)", "4321", 7, 0, 1, ["mults=all"]),
]
AUTOKEY_L = 500


def ioc_of(s, used):
    return N * s / (used * (used - 1)) if used > 1 else 0.0


def planted(threads, lines):
    ok = True
    for ci, (fam, item, off, mult, model, subst, extra) in enumerate(CASES):
        plant = os.path.join(st.TMP, f"hyp_plant{ci}.txt")
        tsv = os.path.join(st.TMP, f"hyp_plant{ci}.tsv")
        st.run(["plant", st.rel(st.PLAIN), fam, item, off, str(mult), str(model), "0.18", str(300 + ci), str(subst), st.rel(plant)])
        st.run(["screen", st.rel(plant), fam, st.rel(tsv), f"only={item}", f"threads={threads}"] + extra)
        best = st.window_bests(tsv)
        for win, (_, toff) in st.truths(plant).items():
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            vout = st.run(["verify", st.rel(plant), fam, item, toff, str(mult), str(model), win])
            vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
            good = bitem == item and boff == toff and ioc >= st.THRESHOLD and vioc >= st.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  plant {item!r} mult={mult} model={model} subst={subst} {win}: "
                         f"best {ioc:.3f} at offset {boff} (truth {toff}); re-decode at truth {vioc:.3f}")
    return ok


def autokey(threads, lines):
    rng = random.Random(3301)
    plain = [int(x) for line in open(st.PLAIN, encoding="utf-8") if line.startswith("R ") for x in line.split()[1:]][:1200]
    s = [rng.randrange(N) for _ in range(AUTOKEY_L)]
    c, j, prev = [], 0, -1
    for p in plain:
        y = (p + s[j]) % N
        j += 1
        tries = 0
        while prev >= 0 and y == prev and rng.random() >= 0.18 and tries < 5:
            y = (p + s[j]) % N
            j += 1
            tries += 1
        c.append(y)
        s.append(y)                       # the ciphertext becomes key material L runes later
        prev = y
    win = os.path.join(st.TMP, "hyp_autokey.txt")
    with open(win, "w", newline="\n") as f:
        f.write(f"W autokey -1\nR {' '.join(map(str, c))}\nL {len(c)}\nG {AUTOKEY_L}\n")
    item = "autokey stream"
    export.write_ksb(os.path.join(HERE, "data", "hyp_autokey.ksb"), {item: s}, os.path.join(HERE, "data", "hyp_autokey.tsv"))
    tsv = os.path.join(st.TMP, "hyp_autokey.tsv")
    fam = "file:data/hyp_autokey.ksb"
    st.run(["screen", st.rel(win), fam, st.rel(tsv), f"threads={threads}"])
    ioc, bitem, boff = st.window_bests(tsv)["autokey"]
    vioc = float(re.search(r"ioc ([\d.]+)", st.run(["verify", st.rel(win), fam, item, "0", "1", "0", "autokey"])).group(1))
    good = bitem == item and boff == "0" and ioc >= st.THRESHOLD and vioc >= st.THRESHOLD
    lines.append(f"{'PASS' if good else 'FAIL'}  ciphertext autokey (L = {AUTOKEY_L}, guard on): best {ioc:.3f} at offset {boff} "
                 f"(truth 0); re-decode over {len(c)} runes {vioc:.3f}")
    return good


def guard(lines):
    with open(os.path.join(HERE, "data", "segments_self.txt"), encoding="utf-8") as f:
        blocks = f.read().split("W ")[1:]
    block = next(b for b in blocks if b.startswith("seg0.8 "))
    g = int(re.search(r"^G (\d+)$", block, re.M).group(1))
    res = {}
    for tag, text in (("without G", re.sub(r"^G \d+\n", "", block, flags=re.M)), ("with G", block)):
        win, out = os.path.join(st.TMP, f"hyp_guard_{tag.replace(' ', '_')}.txt"), os.path.join(st.TMP, "hyp_guard_trace.txt")
        with open(win, "w", newline="\n") as f:
            f.write("W " + text)
        st.run(["trace", st.rel(win), "file:data/library_self.ksb", st.rel(out), "mults=1", f"offs={g - 12}:{g + 1}"])
        with open(out, encoding="utf-8") as f:
            res[tag] = max(ioc_of(int(x.split()[5]), int(x.split()[6])) for x in f if x.strip())
    good = res["without G"] >= 3.0 and res["with G"] < st.THRESHOLD
    lines.append(f"{'PASS' if good else 'FAIL'}  guard: seg0.8 keyed by its own ciphertext 0-12 runes back: best IoC "
                 f"{res['without G']:.2f} without the G line (degenerate), {res['with G']:.3f} with it")
    return good


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(st.OUT, "hyp_selftest.txt"))
    args = ap.parse_args()
    os.makedirs(st.TMP, exist_ok=True)
    lines = []
    ok = planted(args.threads, lines)
    ok &= autokey(args.threads, lines)
    ok &= guard(lines)
    lines.append("HYP SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
