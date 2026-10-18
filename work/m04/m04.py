"""M04 hold-key repair baseline: an independent plant generator and a harness around the UNCHANGED kscreen engine.

Nothing here edits or rebuilds the engine. The encryptors below are written from the channel definitions (work/m04/README.md),
not from the decoder. Nothing in LP2 is solved: these are synthetic plants and matched wrong-key searches.
"""
import os
import random
import re
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
WORK = os.path.join(ROOT, "work")
KS = os.path.join(WORK, "kscreen")
BIN = os.path.join(KS, "target", "release", "kscreen.exe" if os.name == "nt" else "kscreen")
LIB = os.path.join(KS, "data", "library_flat.ksb")
Q = 29
N_RUNES = 300          # window length of the screen (n=300)
NEED = N_RUNES + N_RUNES // 4 + 8    # key_need(300) in work/kscreen/src/main.rs
OFFSETS = 16           # offsets 0..15 are scanned per stream
SLICE = NEED + OFFSETS - 1
TARGET_DOUBLET = 86 / 12947          # LP2: surviving doublets per transition (docs/registry.toml obs-doublets)
KEEP = 0.19            # survivors of the skip / coin models in the repository's convention
sys.path.insert(0, WORK)


# ------------------------------------------------------------------ plaintext sources

def cicada_pool(section_ids):
    """solved Cicada plaintext (GP indices) of the given sections, concatenated"""
    import lp
    segs = lp.load_segments()
    out = []
    for i in section_ids:
        out += list(lp.KNOWN[i][1](lp.runes_of(segs[i])))
    return out


_DIGRAPHS = [("ING", 21), ("TH", 2), ("NG", 21), ("EO", 12), ("OE", 22), ("AE", 25), ("IA", 27), ("IO", 27), ("EA", 28)]
_SINGLE = {"K": "C", "Q": "C", "V": "U", "Z": "S"}


def english_runes(text):
    import lp
    single = {l: i for i, l in enumerate(lp.LATIN) if len(l) == 1}
    out = []
    for word in re.findall(r"[A-Za-z]+", text):
        w = word.upper()
        i = 0
        while i < len(w):
            for dg, idx in _DIGRAPHS:
                if w.startswith(dg, i):
                    out.append(idx)
                    i += len(dg)
                    break
            else:
                ch = _SINGLE.get(w[i], w[i])
                if ch in single:
                    out.append(single[ch])
                i += 1
    return out


def english_pool(lo, hi):
    """Emerson's essays (committed reference text), body only; the fraction [lo, hi) of its runes"""
    text = open(os.path.join(WORK, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="replace").read()
    a = text.find("*** START")
    b = text.rfind("*** END")
    body = text[text.find("\n", a) + 1:b] if a >= 0 and b > a else text
    r = english_runes(body)
    return r[int(lo * len(r)):int(hi * len(r))]


# ------------------------------------------------------------------ KSB1 streams

def write_ksb(path, streams):
    with open(path, "wb") as f:
        f.write(b"KSB1")
        f.write(struct.pack("<I", len(streams)))
        for name, vals in streams:
            nb = name.encode("utf-8")
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(vals)) + bytes(vals))


def read_ksb(path):
    with open(path, "rb") as f:
        d = f.read()
    assert d[:4] == b"KSB1"
    n = struct.unpack_from("<I", d, 4)[0]
    pos, out = 8, []
    for _ in range(n):
        ln = struct.unpack_from("<H", d, pos)[0]
        pos += 2
        name = d[pos:pos + ln].decode("utf-8", "replace")
        pos += ln
        m = struct.unpack_from("<I", d, pos)[0]
        pos += 4
        out.append((name, d[pos:pos + m]))
        pos += m
    return out


_LIBCACHE = []


def library():
    if not _LIBCACHE:
        _LIBCACHE.extend(s for s in read_ksb(LIB) if len(s[1]) >= SLICE + 64)
    return _LIBCACHE


def period_of(vals, maxp=8):
    """smallest period <= maxp of a stream slice (shift-invariant streams cannot lose alignment), else 0"""
    for p in range(1, maxp + 1):
        if all(vals[i] == vals[i + p] for i in range(len(vals) - p)):
            return p
    return 0


def draw_stream(rng, kind):
    """(name, SLICE values): 'iid' uniform, or 'lib' a random slice of a random flat-library stream"""
    if kind == "iid":
        return "iid", bytes(rng.randrange(Q) for _ in range(SLICE))
    name, v = library()[rng.randrange(len(library()))]
    s = rng.randrange(len(v) - SLICE + 1)
    return name, bytes(v[s:s + SLICE])


# ------------------------------------------------------------------ channels (independent of any decoder)
# every encryptor returns (output, key index used per output, repair flags); key indices are relative to the slice start

def enc_additive(plain, key, off, mult=1):
    j, out, used = off, [], []
    for p in plain:
        out.append((p + mult * key[j]) % Q)
        used.append(j)
        j += 1
    return out, used, [False] * len(plain)


def _repair(plain, key, off, q, rng, mult, spend):
    j, out, used, rep = off, [], [], []
    for p in plain:
        x = (p + mult * key[j]) % Q
        if out and x == out[-1] and rng.random() < q:
            r = rng.randrange(Q - 1)
            out.append(r + 1 if r >= out[-1] else r)   # uniform among the 28 runes other than the previous output
            used.append(j)
            rep.append(True)
            if spend:
                j += 1
        else:
            out.append(x)
            used.append(j)
            rep.append(False)
            j += 1
    return out, used, rep


def enc_m04(plain, key, off, q, rng, mult=1):
    """M04: on a would-be repeat, with probability q emit a uniform other rune, advance the plaintext, KEEP the key position"""
    return _repair(plain, key, off, q, rng, mult, spend=False)


def enc_spend(plain, key, off, q, rng, mult=1):
    """spend-key substitution: as M04 but the colliding key value is consumed"""
    return _repair(plain, key, off, q, rng, mult, spend=True)


def enc_skip(plain, key, off, rng, keep=KEEP, mult=1):
    """the repository's skip convention (model 0): on a collision take the next key value, a missed check keeps the doublet"""
    j, out, used = off, [], []
    for p in plain:
        x = (p + mult * key[j]) % Q
        j += 1
        tries = 0
        while out and x == out[-1] and rng.random() >= keep and tries < 5:
            x = (p + mult * key[j]) % Q
            j += 1
            tries += 1
        out.append(x)
        used.append(j - 1)
    return out, used, [False] * len(plain)


def enc_coin(plain, key, off, rng, keep=KEEP, mult=1):
    """the repository's coin convention (model 1): a collision spends one key value as a coin, then the doublet is kept or a fresh value is used"""
    j, out, used = off, [], []
    for p in plain:
        x = (p + mult * key[j]) % Q
        j += 1
        if out and x == out[-1]:
            j += 1
            if rng.random() >= keep:
                x = (p + mult * key[j]) % Q
                j += 1
        out.append(x)
        used.append(j - 1)
    return out, used, [False] * len(plain)


def doublets(out):
    return sum(a == b for a, b in zip(out, out[1:]))


# ------------------------------------------------------------------ the unchanged kscreen engine

def write_window(path, name, out):
    with open(path, "w", newline="\n") as f:
        f.write(f"W {name} -1\nR {' '.join(map(str, out))}\n")


def screen(win, bank, out_tsv, extra=()):
    cmd = [BIN, "screen", win, "file:" + bank, out_tsv, "threads=1", "top=100000", f"n={N_RUNES}", "beam=16", "mults=1,28",
           "models=0,1", "abort=150:1.2", *extra]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=KS)
    if r.returncode != 0:
        raise RuntimeError("kscreen screen failed: " + r.stderr[-400:])
    rows, best = [], 0.0
    with open(out_tsv, encoding="utf-8") as f:
        for line in f:
            if line.startswith("# best"):
                best = float(line.split()[2])
            if line.startswith("#") or line.startswith("ioc\t") or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            rows.append((float(p[0]), p[1], int(p[2]), int(p[3]), int(p[4])))
    return best, rows


def verify(win, bank, item, offset, mult, model, window):
    """full decode (beam 64, no abort) at one cell -> (ioc, plain letters, key index per letter)"""
    cmd = [BIN, "verify", win, "file:" + bank, item, str(offset), str(mult), str(model), window]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=KS)
    ioc, plain, ptr = 0.0, [], []
    for line in r.stdout.splitlines():
        if line.startswith("window "):
            ioc = float(line.split()[5])      # window <name> n <n> ioc <ioc> pointer_jumps <j>
        elif line.startswith("plain "):
            plain = [int(x) for x in line[6:].split(",") if x]
        elif line.startswith("ptr "):
            ptr = [int(x) for x in line[4:].split(",") if x]
    return ioc, plain, ptr


def scratch_dir():
    d = os.environ.get("M04_SCRATCH") or os.path.join(tempfile.gettempdir(), "m04_scratch")
    os.makedirs(d, exist_ok=True)
    return d
