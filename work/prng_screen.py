"""Phase 4 item 4: keystreams from hashes / PRNGs seeded by Cicada phrases and numbers, screened
with the collision-skip-tolerant fast screen (attack.fast_screen).

Generators (seed s as UTF-8 bytes or integer):
  sha256-ctr / sha512-ctr / md5-ctr : H(s || counter) bytes, mapped mod 29 or by rejection (< 232)
  sha256-chain                      : x_0 = H(s), x_{n+1} = H(x_n), bytes concatenated
  mt19937                           : Python random.Random(s).randrange(29)  (also numpy MT19937)
  lcg-glibc                         : x = 1103515245 x + 12345 mod 2^31, value mod 29

    python prng_screen.py
"""
import hashlib
import json
import os
import random
import sys
import time
from multiprocessing import Pool

import numpy as np

import attack
import grid60
import lp

N = lp.N
LEN = 17000
HERE = os.path.dirname(os.path.abspath(__file__))


def _bytes_stream(blocks, need):
    out = bytearray()
    for b in blocks:
        out += b
        if len(out) >= need:
            break
    return bytes(out)


def gen(name, seed):
    sb = seed.encode() if isinstance(seed, str) else str(seed).encode()
    need = LEN * 2
    if name.endswith("-ctr"):
        H = {"sha256-ctr": hashlib.sha256, "sha512-ctr": hashlib.sha512, "md5-ctr": hashlib.md5}[name.split(":")[0]] \
            if ":" in name else {"sha256-ctr": hashlib.sha256, "sha512-ctr": hashlib.sha512, "md5-ctr": hashlib.md5}[name]
        raw = _bytes_stream((H(sb + i.to_bytes(4, "big")).digest() for i in range(10 ** 6)), need)
    elif name == "sha256-chain":
        def chain():
            x = hashlib.sha256(sb).digest()
            while True:
                yield x
                x = hashlib.sha256(x).digest()
        raw = _bytes_stream(chain(), need)
    elif name == "mt19937":
        R = random.Random(seed)
        return np.array([R.randrange(N) for _ in range(LEN)], dtype=np.int64)
    elif name == "lcg-glibc":
        x = int(hashlib.md5(sb).hexdigest(), 16) % (2 ** 31) if isinstance(seed, str) else int(seed)
        out = []
        for _ in range(LEN):
            x = (1103515245 * x + 12345) % (2 ** 31)
            out.append(x % N)
        return np.array(out, dtype=np.int64)
    else:
        raise ValueError(name)
    return raw


def mappings(raw):
    b = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
    yield "mod", (b % N)[:LEN]
    rej = b[b < 232] % N
    if len(rej) >= LEN:
        yield "reject", rej[:LEN]


SEEDS_EXTRA = [3301, 1033, 29, 1729, 729, 7, 31, 2014, 20140104, 1311, 434, 3258]


def seeds():
    base = ["3301", "1033", "cicada", "cicada3301", "Cicada 3301", "liber primus", "liberprimus", "LIBER PRIMUS",
            "intus", "INTUS", "instar", "INSTAR", "divinity", "DIVINITY", "firfumferenfe", "FIRFUMFERENFE",
            "circumference", "CIRCUMFERENCE", "primes", "totient", "pilgrim", "PILGRIM", "welcome", "parable",
            "koan", "an end", "AN END", "deep web", "emergence", "INSTAR EMERGENCE", "self-reliance",
            "7A35090F", "0x7A35090F", "FULMAEAYOEA", "the primes are sacred", "THE PRIMES ARE SACRED",
            "the totient function is sacred", "all things should be encrypted", "ALL THINGS SHOULD BE ENCRYPTED",
            "a warning", "some wisdom", "an instruction", "know this", "question all things",
            "command your own self", "program your mind", "program reality", "within", "emerge",
            "shadows aethereal buffers void carnal obscura form mobius analog void mournful aethereal cabal"]
    out = []
    for s in base:
        out += [s]
    out.append(grid60.an_end_hash())
    out.append(grid60.grid_bytes().hex())
    return out + SEEDS_EXTRA


GENERATORS = ["sha256-ctr", "sha512-ctr", "md5-ctr", "sha256-chain", "mt19937", "lcg-glibc"]
_W = {}


def _init():
    _W["inp"] = attack._segment_inputs()


def _one(args):
    gname, seed = args
    rows = []
    try:
        raw = gen(gname, seed)
    except Exception as e:  # noqa: BLE001
        return [("error", str(e), gname, seed)]
    streams = [("direct", raw)] if isinstance(raw, np.ndarray) else list(mappings(raw))
    for mname, ks in streams:
        for seg, (c, words, offsets) in _W["inp"].items():
            for oname in ("start", "unsolved"):
                off = offsets[oname]
                if off + len(c) + 24 > len(ks):
                    continue
                for sign in (1, -1):
                    for atb in (False, True):
                        s = attack.fast_screen(c, words, ks[off:], sign, atb)
                        b = int(s.argmax())
                        rows.append((float(s[b]), gname, mname, str(seed)[:40], seg, oname, sign, atb, b))
    rows.sort(reverse=True)
    return rows[:5]


if __name__ == "__main__":
    tasks = [(g, s) for g in GENERATORS for s in seeds() if not (g == "lcg-glibc" and False)]
    R = random.Random(99)
    controls = [("mt19937", f"CONTROL-{R.random()}") for _ in range(8)]
    t0 = time.time()
    allrows = []
    with Pool(initializer=_init) as pool:
        for k, rows in enumerate(pool.imap_unordered(_one, tasks + controls)):
            allrows += rows
            if k % 50 == 0:
                print(f"{k}/{len(tasks) + len(controls)} {time.time() - t0:.0f}s", flush=True)
    allrows = [r for r in allrows if r[0] != "error"]
    allrows.sort(reverse=True)
    ctrl = max(r[0] for r in allrows if str(r[3]).startswith("CONTROL"))
    print(f"\n{len(tasks)} generator/seed pairs; control max {ctrl:.3f}")
    for r in [r for r in allrows if not str(r[3]).startswith("CONTROL")][:15]:
        print(f"  {r[0]:.3f} {r[1]}/{r[2]} seed={r[3]!r} seg 0.{r[4]} off={r[5]} sign={r[6]:+d} atb={r[7]} b={r[8]}")
    os.makedirs(os.path.join(HERE, "tmp", "phase4"), exist_ok=True)
    with open(os.path.join(HERE, "tmp", "phase4", "prng_screen.json"), "w", encoding="utf-8") as f:
        json.dump(allrows, f)
