"""Controls for the ciphertext-feedback screen: a planted key must be recovered, random keys must stay below 1.40.

    python work/kscreen/chain_selftest.py [--engine cpu|cuda] [--out file]

Positive: English (work/phpmt/data/english.txt, 3 windows of 400 runes) is enciphered with
c_i = a*c_{i-1} + D(p_i) + k_j (mod 29), D a random substitution, k a library keystream at a known offset, and the
anti-repeat rule on c (a repeated rune is re-drawn from the next key value with probability 0.82; model 0), for
a = 1, 7, 28. The ciphertext goes through chain_windows.chain_window(a) and the unchanged screen; the planted item must
be each window's best hit at the planted offset with IoC >= 1.40. A screen with the wrong a must NOT find it.
Backward key: the same with the key pointer running down from the planted offset; found by reversed windows + dir=back (offset = the
key index at the text's last rune), not by the forward screen. Null: random keystreams over every offset of the LP2 chain windows
(a = 1, 7, 28) stay below 1.40.
"""
import argparse
import os
import random
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import chain_windows as cw  # noqa: E402

BIN = os.path.join(HERE, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
PLAIN = os.path.join(os.path.dirname(HERE), "phpmt", "data", "english.txt")
ITEM, OFFSET = "primes-1 (totient)", 1500
THRESHOLD = 1.40
Q = 29


def load_ksb(path, name):
    import struct
    b = open(path, "rb").read()
    n = struct.unpack_from("<I", b, 4)[0]
    p = 8
    for _ in range(n):
        ln = struct.unpack_from("<H", b, p)[0]
        nm = b[p + 2:p + 2 + ln].decode("utf-8")
        p += 2 + ln
        kl = struct.unpack_from("<I", b, p)[0]
        if nm == name:
            return list(b[p + 4:p + 4 + kl])
        p += 4 + kl
    raise KeyError(name)


def plant(a, seed, keep=0.18, backward=False, last_used=None):
    """Planted windows. backward=True: the key pointer RUNS DOWN from OFFSET (a key read from the end); last_used, if a
    dict, receives each window's key index at its last rune (where a reversed-window screen finds the key)."""
    rng = random.Random(seed)
    d = list(range(Q))
    rng.shuffle(d)
    key = load_ksb(os.path.join(HERE, "data", "library.ksb"), ITEM)
    step = -1 if backward else 1
    out = []
    for w in cw.read_windows(PLAIN):
        j, prev, c, used = OFFSET, -1, [], OFFSET
        for p in w["R"]:
            t = d[p]
            used = j
            y = (t + key[j] + a * (prev if prev >= 0 else 0)) % Q
            j += step
            tries = 0
            while prev >= 0 and y == prev and rng.random() >= keep and tries < 5:
                used = j
                y = (t + key[j] + a * prev) % Q
                j += step
                tries += 1
            c.append(y)
            prev = y
        out.append({"name": "plant_" + w["name"], "prev": -1, "R": c, "P": None})
        if last_used is not None:
            last_used[out[-1]["name"]] = used
    return out


def screen(windows, family, extra, engine):
    tsv = tempfile.mktemp(suffix=".tsv", dir=tempfile.gettempdir())
    cmd = ([sys.executable, os.path.join(HERE, "gpu.py")] if engine == "cuda" else [BIN]) + ["screen", windows, family, tsv, *extra]
    r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    best = {}
    with open(tsv, encoding="utf-8") as fh:
        text = fh.read()
    for line in text.splitlines():
        m = re.match(r"# window (\S+) best ([\d.]+) item=(.*) offset=(\S+) mult=(\d+) model=(\d+)", line)
        if m:
            best[m.group(1)] = (float(m.group(2)), m.group(3), int(m.group(4)) if m.group(4).isdigit() else m.group(4))
    os.unlink(tsv)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", choices=["cpu", "cuda"], default="cpu")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    lines, ok = [], True
    with tempfile.TemporaryDirectory() as d:
        for a in (1, 7, 28):
            win = plant(a, 40 + a)
            f = os.path.join(d, f"plant_a{a}.txt")
            cw.write_windows([cw.chain_window(w, a) for w in win], f)
            best = screen(f, "file:data/library.ksb", [f"only={ITEM}"], args.engine)
            for name, (ioc, item, off) in best.items():
                good = item == ITEM and ioc >= THRESHOLD and abs(off - OFFSET) <= 6      # drift: the rule shifts the pointer
                ok &= good
                lines.append(f"{'PASS' if good else 'FAIL'}  chain a={a} planted {name}: best {ioc:.3f} item {item!r} offset {off} (planted {OFFSET})")
            # the same ciphertext read with the wrong feedback multiplier must not be found
            f2 = os.path.join(d, f"wrong_a{a}.txt")
            wrong = 2 if a != 2 else 3
            cw.write_windows([cw.chain_window(w, wrong) for w in win], f2)
            best = screen(f2, "file:data/library.ksb", [f"only={ITEM}"], args.engine)
            top = max(v[0] for v in best.values())
            good = top < THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  chain a={a} planted but screened with a={wrong}: best IoC {top:.3f} (must stay below {THRESHOLD})")
        # a key that runs BACKWARD through the text: found by the reversed windows with dir=back, not by the forward screen
        for a in (0, 7):
            used = {}
            win = plant(a, 70 + a, backward=True, last_used=used)
            f = os.path.join(d, f"back_a{a}.txt")
            cw.write_windows([cw.reverse_window(cw.chain_window(w, a)) for w in win], f)
            for name, (ioc, item, off) in screen(f, "file:data/library.ksb", [f"only={ITEM}", "dir=back"], args.engine).items():
                good = item == ITEM and ioc >= THRESHOLD and abs(off - used[name]) <= 6
                ok &= good
                lines.append(f"{'PASS' if good else 'FAIL'}  backward key, chain a={a}, reversed windows {name}: best {ioc:.3f} item {item!r} offset {off} (key index at the last rune {used[name]})")
            f2 = os.path.join(d, f"back_fwd_a{a}.txt")
            cw.write_windows([cw.chain_window(w, a) for w in win], f2)
            top = max(v[0] for v in screen(f2, "file:data/library.ksb", [f"only={ITEM}"], args.engine).values())
            good = top < THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  backward key, chain a={a}, read FORWARD: best IoC {top:.3f} (must stay below {THRESHOLD})")
        for a in (1, 7, 28):
            f = os.path.join(HERE, "data", "chain", f"segments_a{a}.txt")
            if not os.path.exists(f):
                cw.make(a, "segments")
            best = screen(f, "rand:30:4242", [], args.engine)
            top = max(v[0] for v in best.values())
            good = top < THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  null a={a}: 30 random keystreams x every offset x 8 LP2 chain windows x 2 signs x 2 models: best IoC {top:.3f} (must stay below {THRESHOLD})")
    lines.append("CHAIN SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    if args.out:
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        with open(args.out, "w", newline="\n", encoding="utf-8") as fh:
            fh.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
