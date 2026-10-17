"""Positive control of the boundary-free OEIS lane: English enciphered with the primes (A000040, 60 terms) taken at offset 5 with multiplier m, hidden among 400 random
sequences of OEIS-like lengths; a `bgsweep seq` over 36-rune windows must return the primes plant at rank 1.

    python work/prngx/oeis_bg_control.py        # prints the result, exit 0 if recovered
"""
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
EXE = "prngx.exe" if os.name == "nt" else "prngx"
BIN = os.path.join(HERE, "target", "release", EXE)
DATA = os.path.join(WORK, "phpmt", "data")


def primes(n):
    out, k = [], 2
    while len(out) < n:
        if all(k % p for p in out if p * p <= k):
            out.append(k)
        k += 1
    return out


def run(*args, **env):
    return subprocess.run([BIN, *args], cwd=HERE, capture_output=True, text=True, check=True, env=dict(os.environ, **env), encoding="utf-8")


def main():
    rng = random.Random(5)
    with tempfile.TemporaryDirectory() as d:
        lib = os.path.join(d, "lib.txt")
        idx = 7
        with open(lib, "w", newline="\n") as f:
            for i in range(400):
                if i == idx:
                    f.write("A000040 " + " ".join(str(p % 29) for p in primes(60)) + "\n")
                else:
                    f.write(f"R{i} " + " ".join(str(rng.randrange(29)) for _ in range(rng.randrange(40, 100))) + "\n")
        off, mult_map = 5, 3                      # map = multiplier - 1 (28 maps)
        seed = idx * 128 + off
        env = dict(PRNGX_SEQ=lib)
        planted, w36, tsv = os.path.join(d, "p.txt"), os.path.join(d, "p36.txt"), os.path.join(d, "o.tsv")
        plain36 = os.path.join(d, "plain36.txt")      # the key has 60 terms: plant a 36-rune plaintext (the 400-rune ones would run past its end)
        subprocess.run([sys.executable, os.path.join(HERE, "bg_windows.py"), os.path.join(DATA, "english.txt"), plain36, "--runes", "36"],
                       check=True, capture_output=True)
        run("plant", "seq", plain36, str(seed), str(mult_map), "0", "1", "0", "0.18", planted, **env)
        subprocess.run([sys.executable, os.path.join(HERE, "bg_windows.py"), planted, w36, "--runes", "36"], check=True, capture_output=True)
        run("bgsweep", "seq", w36, os.path.join(DATA, "bigram.txt"), "0", str(400 * 128), tsv, "4", **env)
        rows = [l.split("\t") for l in open(tsv, encoding="utf-8").read().splitlines()[1:]]
        top = rows[0]
        others = max([int(r[0]) for r in rows if r[1] != str(seed)] or [-999])
        ok = top[1] == str(seed) and top[4] == str(mult_map) and int(top[0]) > 250 and int(top[0]) > others + 100
        print(f"planted primes (offset {off}, map {mult_map}): top score {top[0]} at seed {top[1]} map {top[4]}; best other seed {others}; {'RECOVERED' if ok else 'MISSED'}")
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
