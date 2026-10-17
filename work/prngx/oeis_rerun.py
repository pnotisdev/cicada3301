"""OEIS lane, rerun with windows long enough for a true key to pass the gate (audit of 2026-10-17: a correct key scores +7.3 per rune on Cicada's text, so the original 36-rune windows passed the +300 gate in only 29% of cases).

The OEIS file holds only the first terms of each sequence (min 40, median 63, only 0.5% have 124 or more), so 120-rune windows are impossible. The sequences are split by length so that every one is read with the longest window it can cover:
  set A: 64 or more terms -> 60-rune windows (a true key passes +300 in 97% of windows)
  set B: 52 to 63 terms   -> 48-rune windows (81%)
(sequences with 40-51 terms keep the original 36-rune lane, 29%). Each set is swept against the 8 section windows (all 128 start offsets, 28 multipliers, both signs, skip and coin models; `prngx bgsweep seq`) and against a matched null of random
sequences of the same lengths (data/null_seqs.txt, same order).

    python work/prngx/oeis_rerun.py prep           # filtered sequence files and window files (work/prngx/data, git-ignored)
    python work/prngx/oeis_rerun.py control        # primes planted among 400 random sequences must come back at rank 1, for both window lengths
    python work/prngx/oeis_rerun.py run [threads]  # four sweeps -> results/prngx/bg_oeis_{A60,B48}_{sections,null}.tsv / .log
"""
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ROOT = os.path.dirname(WORK)
DATA = os.path.join(HERE, "data")
RES = os.path.join(ROOT, "results", "prngx")
BIGRAM = os.path.join(WORK, "phpmt", "data", "bigram.txt")
EXE = "prngx.exe" if os.name == "nt" else "prngx"
BIN = os.path.join(HERE, "target", "release", EXE)
SETS = {"A": (64, 10 ** 6, 60), "B": (52, 63, 48)}       # name: (min terms, max terms, window runes)


def lines(path):
    return open(path, encoding="utf-8").read().splitlines()


def prep():
    real, null = lines(os.path.join(DATA, "oeis_seqs.txt")), lines(os.path.join(DATA, "null_seqs.txt"))
    assert len(real) == len(null)
    for name, (lo, hi, L) in SETS.items():
        keep = [i for i, l in enumerate(real) if lo <= len(l.split()) - 1 <= hi]
        assert all(len(null[i].split()) == len(real[i].split()) for i in keep), "null lengths differ from the real ones"
        for tag, src in (("oeis", real), ("null", null)):
            with open(os.path.join(DATA, f"{tag}_{name}.txt"), "w", newline="\n", encoding="utf-8") as f:
                f.write("\n".join(src[i] for i in keep) + "\n")
        subprocess.run([sys.executable, os.path.join(HERE, "bg_windows.py"), os.path.join(WORK, "phpmt", "data", "windows.txt"), os.path.join(DATA, f"bg{L}_sections.txt"), "--runes", str(L)], check=True)
        print(f"set {name}: {len(keep)} sequences with {lo}-{hi if hi < 10 ** 6 else 'max'} terms, windows of {L} runes")


def sweep(seqfile, windows, out, threads):
    n = len(lines(seqfile))
    env = dict(os.environ, PRNGX_SEQ=seqfile)
    with open(out + ".log", "w", encoding="utf-8", newline="\n") as lg:
        subprocess.run([BIN, "bgsweep", "seq", windows, BIGRAM, "0", str(n * 128), out + ".tsv", str(threads)], cwd=HERE, env=env, stderr=lg, check=True)


def control():
    ok_all = True
    for name, (lo, hi, L) in SETS.items():
        rng = random.Random(5)
        with tempfile.TemporaryDirectory() as d:
            lib = os.path.join(d, "lib.txt")
            idx, off, mult_map = 7, 5, 3
            ps, k = [], 2
            while len(ps) < 100:
                if all(k % p for p in ps if p * p <= k):
                    ps.append(k)
                k += 1
            with open(lib, "w", newline="\n") as f:
                for i in range(400):
                    f.write(("A000040 " + " ".join(str(p % 29) for p in ps)) + "\n" if i == idx else f"R{i} " + " ".join(str(rng.randrange(29)) for _ in range(rng.randrange(max(lo, 40), min(hi, 120) + 1))) + "\n")
            env = dict(os.environ, PRNGX_SEQ=lib)
            seed = idx * 128 + off
            plainL, planted, wL, tsv = (os.path.join(d, x) for x in ("plain.txt", "p.txt", "w.txt", "o.tsv"))
            subprocess.run([sys.executable, os.path.join(HERE, "bg_windows.py"), os.path.join(WORK, "phpmt", "data", "english.txt"), plainL, "--runes", str(L)], check=True, capture_output=True)
            subprocess.run([BIN, "plant", "seq", plainL, str(seed), str(mult_map), "0", "1", "0", "0.18", planted], cwd=HERE, env=env, check=True, capture_output=True)
            subprocess.run([sys.executable, os.path.join(HERE, "bg_windows.py"), planted, wL, "--runes", str(L)], check=True, capture_output=True)
            subprocess.run([BIN, "bgsweep", "seq", wL, BIGRAM, "0", str(400 * 128), tsv, "4"], cwd=HERE, env=env, check=True, capture_output=True)
            rows = [l.split("\t") for l in lines(tsv)[1:]]
            top = rows[0]
            others = max([int(r[0]) for r in rows if r[1] != str(seed)] or [-999])
            ok = top[1] == str(seed) and top[4] == str(mult_map) and int(top[0]) > 250 and int(top[0]) > others + 100
            ok_all &= ok
            print(f"{'RECOVERED' if ok else 'MISSED'}  set {name} ({L}-rune windows): planted primes (offset {off}, map {mult_map}): top score {top[0]} at seed {top[1]} map {top[4]}; best other seed {others}")
    print("OEIS RERUN CONTROL " + ("PASSED" if ok_all else "FAILED"))
    return 0 if ok_all else 1


def run(threads):
    os.makedirs(RES, exist_ok=True)
    for name, (lo, hi, L) in SETS.items():
        for tag, label in (("oeis", "sections"), ("null", "null")):
            out = os.path.join(RES, f"bg_oeis_{name}{L}_{label}")
            print(f"sweeping {tag}_{name} at {L} runes -> {os.path.relpath(out, ROOT)}", flush=True)
            sweep(os.path.join(DATA, f"{tag}_{name}.txt"), os.path.join(DATA, f"bg{L}_sections.txt"), out, threads)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "prep":
        prep()
    elif cmd == "control":
        sys.exit(control())
    elif cmd == "run":
        run(int(sys.argv[2]) if len(sys.argv) > 2 else os.cpu_count())
    else:
        sys.exit(__doc__)
