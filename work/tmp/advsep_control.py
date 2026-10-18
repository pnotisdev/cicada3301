"""Controls for the kscreen `advsep=<n>` option (extra key-pointer advances at word boundaries / layout breaks).

The option advances the key pointer by ONE extra key value BETWEEN words (before the next word's first rune;
word edges from the window's L line, the nulledge convention) and, for advsep=2, also by ONE extra key value
at every line/page break (the window's B line, written by export.py). The skip/coin collision logic and the
anti-repeat prev chain are unchanged. A deterministic decoder stays aligned ONLY with a truth that consumed
the same extra values, so the passing positive control plants the solved Welcome plaintext (lp.KNOWN[1][1],
complete words within the first 300 runes) on the library key `primes` (offset 100, mult 1, skip model,
keep 0.19, seed 12345, no substitution) and RE-ENCRYPTS the planted ciphertext with one extra key value
consumed after every word: word w starting at key index j(w) consumes j(w), j(w)+1, ... and
j(w+1) = j(w) + len(w) + 1 (skip re-draws on collisions stay inside the word and move j further, exactly as
the unchanged collision rule does). The re-encryption is implemented INDEPENDENTLY in Python (the plant's
splitmix64 RNG and the first-primes key stream reproduced here); the script first checks it reproduces the
engine's own plant byte for byte with the advances off, which pins the Python key/RNG to the engine's.

Gates:
  (a) blindness: the default engine (advsep=0) on the advanced ciphertext must stay <= 1.30;
  (b) positive: advsep=1 must recover IoC >= 1.60 at the exact offset 100;
  (c) null: rand:300:301 with advsep=1 must stay <= 1.37.
Documented (not gates): advsep=1 on the un-advanced plant (the model does not fit ordinary text), and
advsep=2 on the advanced plant (the planted window has no line/page breaks, so advsep=2 == advsep=1 there).

    python work/tmp/advsep_control.py [--threads N] [--bin work/kscreen/target/release/kscreen.exe]
                                      [--out work/tmp/advsep_control.txt]
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KS = os.path.join(ROOT, "work", "kscreen")
sys.path.insert(0, os.path.join(ROOT, "work"))
sys.path.insert(0, KS)
import lp  # noqa: E402

PLAIN_IO = os.path.join(ROOT, "work", "tmp", "advsep_plain.txt")
TMP = os.path.join(ROOT, "work", "tmp", "advsep_tmp")
RECOVERY = 1.60     # positive-control threshold
NULL_MAX = 1.37     # null-control threshold
BLIND_MAX = 1.30    # blindness control: the default engine must NOT see the plant
PLANT = dict(item="primes", offset=100, mult=1, model=0, keep=0.19, seed=12345, subst=0)
MASK = 0xFFFFFFFFFFFFFFFF


# ------------------------------------------------------------------ the plant's own generators (independently)

def primes_upto(limit):
    m = bytearray(b"\x01") * (limit + 1)
    m[0:2] = b"\x00\x00"
    for i in range(2, int(limit ** 0.5) + 1):
        if m[i]:
            m[i * i::i] = b"\x00" * (((limit - i * i) // i) + 1)
    return [i for i in range(limit + 1) if m[i]]


def key_primes(offset, need):
    """The library stream `primes` at `offset`: k_j = p_(offset+j) mod 29 (p_0 = 2), as in keystreams.py."""
    ps = primes_upto(20000)
    assert offset + need <= len(ps), "sieve too small"
    return [(p % lp.N) for p in ps[offset:offset + need]]


class Splitmix64:
    """The engine's plant RNG (splitmix64 with the 0x0123_4567_89AB_CDEF xor), independently."""

    def __init__(self, seed):
        self.state = (seed ^ 0x0123456789ABCDEF) & MASK

    def next(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & MASK
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
        return z ^ (z >> 31)

    def unit(self):
        return (self.next() >> 11) / (1 << 53)


def encrypt(plain, lens, mk, keep, rng, adv):
    """The engine's skip-model plant (mult already applied to mk, no substitution, no clock), plus extra key
    values consumed between runes: adv[i] = extra values between rune i-1 and rune i (adv[0] ignored), so a
    word w starting at rune index b gets j(b) = sum over previous words of (len + skips) + sum(adv[..b]). The
    engine's advsep reads exactly such a per-position array from the L line (word boundaries) and the B line
    (breaks). Returns ciphertext."""
    j, prev, c = 0, -1, []
    for i in range(len(plain)):
        if adv and i > 0:
            j += adv[i]
        t = plain[i]
        y = (t + mk[j]) % lp.N
        j += 1
        tries = 0
        while prev >= 0 and y == prev and rng.unit() >= keep and tries < 5:
            y = (t + mk[j]) % lp.N
            j += 1
            tries += 1
        c.append(y)
        prev = y
    return c


def boundary_adv(lens):
    """adv[i] = 1 at every word boundary (cumulative L sums), 0 elsewhere: the engine's advsep=1 positions."""
    adv = [0] * (sum(lens) + 1)
    b = 0
    for l in lens:
        b += l
        if b < len(adv) - 1:
            adv[b] += 1
    return adv


# ------------------------------------------------------------------ engine plumbing (as nulledge_control.py)

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


def data_rows(tsv):
    with open(tsv, encoding="utf-8") as f:
        return sorted(l for l in f.read().splitlines() if l and not l.startswith("#"))


def make_plain():
    """Welcome (segment 1) plaintext: complete words within the first 300 runes, as a plant windows file."""
    segs = lp.load_segments()
    toks = segs[1]
    runes = lp.runes_of(toks)
    plain = lp.KNOWN[1][1](runes)
    spans = lp.word_spans(toks, plain)
    keep = [(a, b) for _, a, b in spans if b <= 300]
    n = keep[-1][1]
    lens = [b - a for a, b in keep]
    with open(PLAIN_IO, "w", newline="\n", encoding="utf-8") as f:
        f.write(f"W welcome -1\nR {' '.join(map(str, plain[:n]))}\nL {' '.join(map(str, lens))}\n")
    return plain[:n], lens, n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=min(8, os.cpu_count()))
    ap.add_argument("--bin", default=os.path.join(KS, "target", "release", "kscreen.exe"))
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "tmp", "advsep_control.txt"))
    args = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)
    lines, ok = [], True

    plain, lens, n = make_plain()
    lines.append(f"plaintext: Welcome (segment 1), {n} runes in {len(lens)} complete words within the first 300, IoC {lp.ioc(plain):.4f}")

    # the engine's own base plant, then the independent Python re-encryption with the advances off: they must agree
    base_engine = os.path.join(TMP, "base_engine.txt")
    run(["plant", rel(PLAIN_IO), "file:data/library.ksb", PLANT["item"], str(PLANT["offset"]), str(PLANT["mult"]),
         str(PLANT["model"]), str(PLANT["keep"]), str(PLANT["seed"]), str(PLANT["subst"]), rel(base_engine)], args.bin)
    base_txt = open(base_engine, encoding="utf-8").read().splitlines()
    base_runes = [int(x) for x in base_txt[[i for i, l in enumerate(base_txt) if l.startswith("R ")][0]].split()[1:]]
    truth = next(l for l in base_txt if l.startswith("# truth"))
    need = 4 * n + key_need_check(n) + 64
    mk = key_primes(PLANT["offset"], need)
    rng = Splitmix64(PLANT["seed"])
    py_base = encrypt(plain, lens, mk, PLANT["keep"], rng, None)
    match = py_base == base_runes
    ok &= match
    lines.append(f"{'PASS' if match else 'FAIL'}  self-check: independent Python re-encryption (advances off) reproduces the "
                 f"engine's plant byte for byte ({len(base_runes)} runes; pins the key stream and the splitmix64 plant RNG)")

    # the advanced plant: same stream and RNG sequence, one extra key value after every word
    rng = Splitmix64(PLANT["seed"])
    adv_runes = encrypt(plain, lens, mk, PLANT["keep"], rng, boundary_adv(lens))
    win = os.path.join(TMP, "advsep_window.txt")
    with open(win, "w", newline="\n", encoding="utf-8") as f:
        f.write(truth + "\n")
        f.write("W plant_0 -1\n")
        f.write("R " + " ".join(map(str, adv_runes)) + "\n")
        f.write("L " + " ".join(map(str, lens)) + "\n")
    lines.append(f"advanced plant: {n} ciphertext runes, L = the plain window's word lengths, {len(lens) - 1} word "
                 f"boundaries each consuming one extra key value (no line/page breaks in the window)")

    # (a) blindness: the default engine on the advanced window
    tsv = os.path.join(TMP, "a.tsv")
    run(["screen", rel(win), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
         f"threads={args.threads}"], args.bin)
    name, ioc, _, _, _, _ = window_best(tsv)
    vout = run(["verify", rel(win), "file:data/library.ksb", "primes", "100", "1", "0", "plant_0", "n=300"], args.bin)
    at100 = float(re.search(r"ioc ([\d.]+)", vout).group(1))
    good = ioc <= BLIND_MAX
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  (a) blindness: default engine (advsep=0) on the advanced window best "
                 f"IoC {ioc:.3f} (<= {BLIND_MAX}); at the true offset 100: {at100:.3f}")

    # (b) positive: advsep=1 recovers the plant at the exact offset 100
    tsv = os.path.join(TMP, "b.tsv")
    run(["screen", rel(win), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
         "advsep=1", f"threads={args.threads}"], args.bin)
    name, ioc, item, off, mult, model = window_best(tsv)
    good = ioc >= RECOVERY and off == "100" and item == "primes"
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  (b) positive: advsep=1 best IoC {ioc:.3f} at item={item} offset={off} "
                 f"mult={mult} model={model} (must be >= {RECOVERY} at offset 100)")

    # (c) null: random keystreams under the same settings must stay low
    tsv = os.path.join(TMP, "c.tsv")
    run(["screen", rel(win), "rand:300:301", rel(tsv), "mults=1", "models=0,1", "advsep=1",
         f"threads={args.threads}"], args.bin)
    name, ioc, _, _, _, _ = window_best(tsv)
    good = ioc <= NULL_MAX
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  (c) null: rand:300:301 with advsep=1 best IoC {ioc:.3f} (must be <= {NULL_MAX})")

    # documented (not a gate): advsep=1 on the un-advanced plant (the model does not fit ordinary text)
    tsv = os.path.join(TMP, "plain.tsv")
    run(["screen", rel(base_engine), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
         "advsep=1", f"threads={args.threads}"], args.bin)
    name, iocp, _, _, _, _ = window_best(tsv)
    lines.append(f"info  advsep=1 on the un-advanced plant: best IoC {iocp:.3f} (expected ~1.0: the model does not fit ordinary text)")

    # documented (not a gate): advsep=2 on the advanced plant == advsep=1 there (the window has no B line)
    tsv = os.path.join(TMP, "b2.tsv")
    run(["screen", rel(win), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
         "advsep=2", f"threads={args.threads}"], args.bin)
    same = data_rows(os.path.join(TMP, "b.tsv")) == data_rows(tsv)
    lines.append(f"{'PASS' if same else 'FAIL'}  advsep=2 on the advanced plant decodes identically to advsep=1 "
                 f"(no B line: no line/page breaks, so the option has nothing extra to advance at)")

    # the B-line positive: plant word-boundary AND line-break advances at fixed synthetic break positions, write
    # them as a B line; advsep=2 must recover at offset 100, advsep=1 (which does not know the breaks) must not.
    breaks = [17, 53, 91, 140, 199, 247, 285]
    adv2 = boundary_adv(lens)
    for p in breaks:
        adv2[p] += 1
    rng = Splitmix64(PLANT["seed"])
    b_runes = encrypt(plain, lens, mk, PLANT["keep"], rng, adv2)
    winb = os.path.join(TMP, "advsep_window_b.txt")
    with open(winb, "w", newline="\n", encoding="utf-8") as f:
        f.write(truth + "\n")
        f.write("W plant_0 -1\n")
        f.write("R " + " ".join(map(str, b_runes)) + "\n")
        f.write("L " + " ".join(map(str, lens)) + "\n")
        f.write("B " + " ".join(map(str, breaks)) + "\n")
    tsv = os.path.join(TMP, "b2b.tsv")
    run(["screen", rel(winb), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
         "advsep=2", f"threads={args.threads}"], args.bin)
    r2 = row_for(tsv, "100")
    good = r2 is not None and r2[0] >= RECOVERY
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  (b2) B-line positive: advsep=2 recovers the word-boundary + "
                 f"{len(breaks)} synthetic-break plant at offset 100 with IoC {r2[0] if r2 else float('nan'):.3f} (>= {RECOVERY})")
    tsv = os.path.join(TMP, "b2a.tsv")
    run(["screen", rel(winb), "file:data/library.ksb", rel(tsv), "only=primes", "mults=1", "models=0,1",
         "advsep=1", f"threads={args.threads}"], args.bin)
    vout = run(["verify", rel(winb), "file:data/library.ksb", "primes", "100", "1", "0", "plant_0", "n=300",
                "advsep=1"], args.bin)
    at100b = float(re.search(r"ioc ([\d.]+)", vout).group(1))
    lines.append(f"info  advsep=1 on the B-line plant: IoC {at100b:.3f} at offset 100 "
                 f"(misaligned: it does not know the breaks; expected ~1.0)")

    lines.append("CONTROLS " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


def key_need_check(n):
    """the engine's key_need with no clock: (n + n/4 + 8) * 1"""
    return n + n // 4 + 8


if __name__ == "__main__":
    sys.exit(main())
