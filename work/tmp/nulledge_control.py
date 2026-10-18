"""Controls for the kscreen `nulledge=<0|1|2>` option (keyless word-edge nulls, deterministic semantics).

The option treats EVERY word-final (nulledge=1) / word-initial (nulledge=2) rune of a window's L-line words as
a keyless null: not scored, no key-pointer advance, invisible to the anti-repeat prev chain. A deterministic
decoder can stay aligned ONLY with a truth that has a null at every word edge, so the passing positive control
plants a null at 100% of the word edges (the word-length model's ~42%-of-multi-rune-words mixture is shown below
to be invisible to ANY single-window IoC decoder: a free-pattern beam variant recovers the 42% plant at IoC 1.71
but inflates the random-key null to 1.75, i.e. the null reaches the truth's level - see NULLEDGE.md).

The plant: the solved Welcome plaintext (lp.KNOWN[1][1], complete words within the first 300 runes), planted
with the engine's plant mode on the library key `primes` (offset 100, mult 1, skip model, keep 0.19, seed 12345,
no substitution). A random keyless null rune is then inserted at EVERY word edge, post-hoc (the planted
anti-repeat chain is unchanged; the decoder's null-adjusted prev chain matches), and the L line is written as
the CIPHERTEXT word lengths: every word's L entry is one longer (NULLEDGE.md convention).

Gates per variant (v = 1 word-final, v = 2 word-initial):
  (a) blindness: the default engine (nulledge=0) on the nulled window must stay <= 1.30 (it misaligns at the
      first null);
  (b) positive: nulledge=v must recover IoC >= 1.6 at the exact offset 100;
  (c) null: rand:300:300 with the same nulledge must stay <= 1.37.
Documented (not gates): the 42%-of-multi-rune-words mixture scores ~1.0 with nulledge=v (the decoder cannot
know which words carry the null, so it has no power there), and nulledge=v on the un-nulled plant also scores
~1.0 (the model does not fit null-free text).

    python work/tmp/nulledge_control.py [--threads N] [--out work/tmp/nulledge_control.txt]
"""
import argparse
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KS = os.path.join(ROOT, "work", "kscreen")
sys.path.insert(0, os.path.join(ROOT, "work"))
sys.path.insert(0, KS)
import lp  # noqa: E402

PLAIN_IO = os.path.join(ROOT, "work", "tmp", "nulledge_plain.txt")
TMP = os.path.join(ROOT, "work", "tmp", "nulledge_tmp")
SEED = 555
RECOVERY = 1.60     # positive-control threshold
NULL_MAX = 1.37     # null-control threshold
BLIND_MAX = 1.30    # blindness control: the default engine must NOT see the plant


def rel(p):
    return os.path.relpath(p, KS).replace("\\", "/")


def run(args, bin_path):
    r = subprocess.run([bin_path] + args, cwd=KS, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"kscreen {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def window_best(tsv):
    with open(tsv, encoding="utf-8") as f:
        for line in f.read().splitlines():
            m = re.match(r"# window (\S+) best ([\d.]+) item=(.*) offset=(\S+) mult=(\d+) model=(\d+)", line)
            if m:
                return m.group(1), float(m.group(2)), m.group(3), m.group(4), m.group(5), m.group(6)
    raise RuntimeError(f"{tsv}: no window best line")


def row_for(tsv, offset):
    """the (ioc, item, mult, model) of the best hit row at a given offset, or None"""
    best = None
    with open(tsv, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.startswith("#") or not line.strip():
                continue
            p = line.split("\t")
            if p[2] == str(offset):
                v = float(p[0])
                if best is None or v > best[0]:
                    best = (v, p[1], p[3], p[4])
    return best


def make_plain():
    """Welcome (segment 1) plaintext: complete words within the first 300 runes, as a plant windows file."""
    segs = lp.load_segments()
    toks = segs[1]
    runes = lp.runes_of(toks)
    plain = lp.KNOWN[1][1](runes)
    spans = lp.word_spans(toks, plain)
    keep = []
    for _, a, b in spans:
        if b <= 300:
            keep.append((a, b))
    n = keep[-1][1]
    lens = " ".join(str(b - a) for a, b in keep)
    with open(PLAIN_IO, "w", newline="\n", encoding="utf-8") as f:
        f.write(f"W welcome -1\nR {' '.join(map(str, plain[:n]))}\nL {lens}\n")
    return plain[:n], [b - a for a, b in keep], n


def null_window(bin_path, variant, rate_pct):
    """plant with the engine, then insert a keyless null at `rate_pct`% of the word edges (100% for the passing
    control; post-hoc, so the planted anti-repeat chain is unchanged), L = ciphertext word lengths incl. nulls."""
    base = os.path.join(TMP, f"base_v{variant}.txt")
    run(["plant", rel(PLAIN_IO), "file:data/library.ksb", "primes", "100", "1", "0", "0.19", "12345", "0", rel(base)], bin_path)
    txt = open(base, encoding="utf-8").read().splitlines()
    truth = next(l for l in txt if l.startswith("# truth"))
    runes = [int(x) for x in txt[[i for i, l in enumerate(txt) if l.startswith("R ")][0]].split()[1:]]
    lens = [int(x) for x in txt[[i for i, l in enumerate(txt) if l.startswith("L ")][0]].split()[1:]]
    rng = random.Random(SEED + variant + rate_pct)
    if rate_pct == 100:
        nulled = set(range(len(lens)))
    else:
        multi = [i for i, l in enumerate(lens) if l >= 2]
        k = round(rate_pct / 100.0 * len(multi))
        nulled = set(rng.sample(multi, k))
    out_runes, out_lens = [], []
    for i, l in enumerate(lens):
        a, b = sum(lens[:i]), sum(lens[:i]) + l
        word = runes[a:b]
        if i in nulled:
            nl = rng.randrange(29)
            word = word + [nl] if variant == 1 else [nl] + word
            out_lens.append(l + 1)
        else:
            out_lens.append(l)
        out_runes.extend(word)
    out = os.path.join(ROOT, "work", "tmp", f"nulledge_window_v{variant}_p{rate_pct}.txt")
    with open(out, "w", newline="\n", encoding="utf-8") as f:
        f.write(truth + "\n")
        f.write("W plant_0 -1\n")
        f.write("R " + " ".join(map(str, out_runes)) + "\n")
        f.write("L " + " ".join(map(str, out_lens)) + "\n")
    return out, len(nulled), sum(lens), len(out_runes)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=min(8, os.cpu_count()))
    ap.add_argument("--bin", default=os.path.join(KS, "target", "release", "kscreen.exe"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "tmp", "nulledge_control.txt"))
    args = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)
    lines, ok = [], True

    plain_runes, plain_lens, n = make_plain()
    pioc = lp.ioc(plain_runes)
    lines.append(f"plaintext: Welcome (segment 1), {n} runes in {len(plain_lens)} complete words within the first 300, IoC {pioc:.4f}")

    for variant in (1, 2):
        edge = {1: "final", 2: "initial"}[variant]
        win, nnull, nrunes, total = null_window(args.bin, variant, 100)
        lines.append(f"variant {variant} ({edge} nulls): a keyless null at EVERY one of the {nnull} word edges; "
                     f"window has {total} ciphertext runes ({nrunes} planted + {nnull} nulls), L = ciphertext word lengths incl. nulls")

        # (a) blindness: the default engine on the nulled window
        tsv = os.path.join(TMP, f"a_v{variant}.tsv")
        run(["screen", rel(win), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1", f"threads={args.threads}"], args.bin)
        name, ioc, _, _, _, _ = window_best(tsv)
        vout = run(["verify", rel(win), "file:data/library.ksb", "primes", "100", "1", "0", "plant_0", "n=300"], args.bin)
        at100 = float(re.search(r"ioc ([\d.]+)", vout).group(1))
        good = ioc <= BLIND_MAX
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  (a) blindness: default engine (nulledge=0) on the nulled "
                     f"window best IoC {ioc:.3f} (<= {BLIND_MAX}); at the true offset 100: {at100:.3f}")

        # (b) positive: nulledge=variant recovers the plant at the exact offset 100
        tsv = os.path.join(TMP, f"b_v{variant}.tsv")
        run(["screen", rel(win), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
             f"nulledge={variant}", f"threads={args.threads}"], args.bin)
        name, ioc, item, off, mult, model = window_best(tsv)
        good = ioc >= RECOVERY and off == "100" and item == "primes"
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  (b) positive: nulledge={variant} best IoC {ioc:.3f} at "
                     f"item={item} offset={off} mult={mult} model={model} (must be >= {RECOVERY} at offset 100)")

        # (c) null: random keystreams under the same settings must stay low
        tsv = os.path.join(TMP, f"c_v{variant}.tsv")
        run(["screen", rel(win), f"rand:300:{300 + variant}", rel(tsv), "mults=1", "models=0,1",
             f"nulledge={variant}", f"threads={args.threads}"], args.bin)
        name, ioc, _, _, _, _ = window_best(tsv)
        good = ioc <= NULL_MAX
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  (c) null: rand:300:{300 + variant} with nulledge={variant} "
                     f"best IoC {ioc:.3f} (must be <= {NULL_MAX})")

        # documented (not a gate): the 42%-of-multi-rune-words mixture has no signature a deterministic
        # word-edge decoder can see (it misaligns at the first null-free word)
        win42, _, _, _ = null_window(args.bin, variant, 42)
        tsv = os.path.join(TMP, f"m42_v{variant}.tsv")
        run(["screen", rel(win42), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
             f"nulledge={variant}", f"threads={args.threads}"], args.bin)
        name, ioc42, _, _, _, _ = window_best(tsv)
        lines.append(f"info  42%-of-multi-rune-words mixture (word-{edge} nulls): nulledge={variant} best IoC "
                     f"{ioc42:.3f} (no power: the decoder cannot know which words carry the null; see NULLEDGE.md)")

        # documented (not a gate): nulledge on the un-nulled plant (the model does not fit null-free text)
        base = os.path.join(TMP, f"base_v{variant}.txt")
        tsv = os.path.join(TMP, f"plain_v{variant}.tsv")
        run(["screen", rel(base), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
             f"nulledge={variant}", f"threads={args.threads}"], args.bin)
        name, iocp, _, _, _, _ = window_best(tsv)
        lines.append(f"info  nulledge={variant} on the un-nulled plant: best IoC {iocp:.3f} (expected ~1.0: the model does not fit null-free text)")

    lines.append("CONTROLS " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
