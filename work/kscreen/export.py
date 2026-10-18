"""Inputs for the language-agnostic keystream screen (work/kscreen).

    python work/kscreen/export.py

data/segments.txt   LP2 segments with >= 100 runes (one continuous stream or a restart per section)
data/heads.txt      restart windows at red headings and '&' paragraph starts (ref/restart_windows.json)
data/pages.txt      a window at every LP2 page start that is not a section start
data/library.ksb    keystream library (binary "KSB1"): keystreams.number_keystreams(), solved-text keywords,
                    new number families, digits of further constants in base 29, hash streams of Cicada
                    strings and of the corrected 256-byte payload, the payload itself
data/library.tsv    per keystream: length, period, predicted ciphertext IoC under English plaintext. LP2 has
                    0.9999 +- 0.0006, so a key whose prediction exceeds ~1.003 is already excluded globally
                    (the screen still runs it).

Window format: W name prev / R runes / L word lengths / optional B line. The B line lists the window-relative
rune positions where a line or page break (the transcription's line/page separators) sits between two runes;
the engine's advsep=2 option advances the key pointer there (docs: ADVSEP.md).
"""
import hashlib
import json
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
import keystreams  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

N = lp.N
OUT = os.path.join(HERE, "data")
KEEP = 2000          # periodic keystreams are stored as one period + KEEP values (enough for windows up to ~1500)


def break_positions(toks, start, end):
    """Window-relative rune positions p where a line or page break (the transcription's '\n' / '%') sits between
    rune p-1 and rune p, i.e. after p runes of the window. Only interior positions count (a break at or after
    the window edge moves no pointer inside the window); the engine's advsep=2 advances the key pointer there."""
    out, k = [], 0
    for t in toks:
        if isinstance(t, int):
            k += 1
        elif t in ("\n", "%"):
            if start < k < end:
                out.append(k - start)
    return out


def write_windows(path, items):
    with open(path, "w", newline="\n") as f:
        for name, prev, runes, lens, breaks in items:
            f.write(f"W {name} {prev}\nR {' '.join(map(str, runes))}\nL {' '.join(map(str, lens))}\n")
            if breaks:
                f.write(f"B {' '.join(map(str, breaks))}\n")


def segment_windows():
    segs = stats.SEGS
    out = []
    for i in stats.UNSOLVED:
        c = lp.runes_of(segs[i])
        if len(c) < 100:
            continue
        prev = lp.runes_of(segs[i - 1])[-1] if i > 7 else -1
        lens = [b - a for _, a, b in lp.word_spans(segs[i], c)]
        out.append((f"seg0.{i}", prev, c, lens, break_positions(segs[i], 0, len(c))))
    return out


def sub_window(seg, start, name):
    segs = stats.SEGS
    c = lp.runes_of(segs[seg])
    spans = [(a, b) for _, a, b in lp.word_spans(segs[seg], c)]
    lens = [b - a for a, b in spans if a >= start]
    return (name, c[start - 1] if start > 0 else -1, c[start:], lens, break_positions(segs[seg], start, len(c)))


def head_windows():
    raw = json.load(open(os.path.join(WORK, "ref", "restart_windows.json")))
    seen, out = set(), []
    for seg, start, _ in raw:
        if start == 0 or any(s == seg and abs(start - k) <= 2 for s, k in seen):
            continue
        seen.add((seg, start))
        out.append(sub_window(seg, start, f"head0.{seg}@{start}"))
    return out


def page_windows():
    try:
        import red_runs
        offs = red_runs.page_seg_offsets()
    except Exception as e:  # noqa: BLE001
        print("page windows skipped:", e)
        return []
    seen, out = set(), []
    for page, (seg, pos) in sorted(offs.items()):
        if seg not in stats.UNSOLVED or pos == 0 or (seg, pos) in seen:
            continue
        if len(lp.runes_of(stats.SEGS[seg])) - pos < 100:
            continue
        seen.add((seg, pos))
        out.append(sub_window(seg, pos, f"page{page}_0.{seg}@{pos}"))
    return out


# ---------------------------------------------------------------- keystream families

def arr(seq):
    return np.array([int(x) % N for x in seq], dtype=np.int64)


def new_number_families(L=keystreams.LEN):
    ps = keystreams._PRIMES[:L + 10]
    out = {}
    n = range(1, L + 1)
    out["primes^3"] = arr(p ** 3 for p in ps[:L])
    out["(p-1)/2"] = arr((p - 1) // 2 for p in ps[1:L + 1])
    out["(p+1)/2"] = arr((p + 1) // 2 for p in ps[1:L + 1])
    out["p_n + n"] = arr(p + i for i, p in enumerate(ps[:L], 1))
    out["p_n - n"] = arr(p - i for i, p in enumerate(ps[:L], 1))
    out["n * p_n"] = arr(p * i for i, p in enumerate(ps[:L], 1))
    out["primes digit sum"] = arr(sum(map(int, str(p))) for p in ps[:L])
    out["primes reversed digits"] = arr(int(str(p)[::-1]) for p in ps[:L])
    out["primes popcount"] = arr(bin(p).count("1") for p in ps[:L])
    out["primes base-29 digit sum"] = arr(sum(np.base_repr(p, 29).encode()) for p in ps[:L])
    out["3301 * p_n"] = arr(3301 * p for p in ps[:L])
    out["p_n mod 3301"] = arr(p % 3301 for p in ps[:L])
    out["3301 - p_n"] = arr(3301 - p for p in ps[:L])
    out["p_(n+1) * p_n"] = arr(a * b for a, b in zip(ps, ps[1:L + 1]))
    out["p_n^2 - 1"] = arr(p * p - 1 for p in ps[:L])
    # multiplicative functions
    M = L + 2
    spf = list(range(M))
    for i in range(2, int(M ** 0.5) + 1):
        if spf[i] == i:
            for j in range(i * i, M, i):
                if spf[j] == j:
                    spf[j] = i

    def factor(x):
        f = {}
        while x > 1:
            p = spf[x]
            f[p] = f.get(p, 0) + 1
            x //= p
        return f
    fs = [factor(i) for i in range(1, L + 1)]
    out["mobius mu(n)"] = arr(0 if any(e > 1 for e in f.values()) else (-1) ** len(f) for f in fs)
    out["omega(n)"] = arr(len(f) for f in fs)
    out["Omega(n)"] = arr(sum(f.values()) for f in fs)
    out["rad(n)"] = arr(int(np.prod([p for p in f], dtype=object)) if f else 1 for f in fs)

    def carmichael(f):
        from math import lcm
        v = 1
        for p, e in f.items():
            lam = (p - 1) * p ** (e - 1)
            if p == 2 and e >= 3:
                lam //= 2
            v = lcm(v, lam)
        return v
    out["carmichael lambda(n)"] = arr(carmichael(f) for f in fs)
    pi_n, cnt, pset = [], 0, set(keystreams._PRIMES[:L])
    for i in n:
        cnt += i in pset
        pi_n.append(cnt)
    out["prime counting pi(n)"] = arr(pi_n)
    # partition numbers mod 29 (Euler's pentagonal recurrence)
    part = [1] + [0] * L
    pent = []
    k = 1
    while True:
        g1, g2 = k * (3 * k - 1) // 2, k * (3 * k + 1) // 2
        if g1 > L:
            break
        pent.append((g1, 1 if k % 2 else -1))
        pent.append((g2, 1 if k % 2 else -1))
        k += 1
    for m in range(1, L + 1):
        s = 0
        for g, sg in pent:
            if g > m:
                break
            s += sg * part[m - g]
        part[m] = s % N
    out["partitions p(n)"] = arr(part[1:])
    return out


def more_constants():
    import mpmath
    mpmath.mp.dps = 32000
    consts = {"euler gamma": mpmath.euler, "zeta(3)": mpmath.zeta(3), "catalan G": mpmath.catalan,
              "sqrt5": mpmath.sqrt(5), "ln3": mpmath.log(3), "pi^2": mpmath.pi ** 2, "e^pi": mpmath.e ** mpmath.pi,
              "cbrt2": mpmath.cbrt(2), "ln10": mpmath.log(10), "sqrt3301": mpmath.sqrt(3301),
              "ln3301": mpmath.log(3301), "sqrt29": mpmath.sqrt(29), "1/3301": mpmath.mpf(1) / 3301}
    out = {}
    L = keystreams.LEN
    for name, v in consts.items():
        x = int(mpmath.floor((v - mpmath.floor(v)) * mpmath.mpf(N) ** L))
        dig = []
        while x:
            x, d = divmod(x, N)
            dig.append(d)
        dig = (dig + [0] * (L - len(dig)))[::-1]
        out[f"{name} digits (base 29)"] = arr(dig)
    return out


def hash_streams():
    """Hash counter / chain streams of Cicada strings, the An End hash and the corrected payload."""
    import grid60
    import prng_screen
    seeds = [s.encode() if isinstance(s, str) else str(s).encode() for s in prng_screen.seeds()]
    payload = grid60.grid_bytes()
    seeds += [payload, bytes.fromhex(grid60.an_end_hash()), payload[::-1]]
    labels = [s.decode("latin-1")[:40] if len(s) < 120 else f"<{len(s)} bytes {s[:4].hex()}>" for s in seeds]
    L = keystreams.LEN
    need = L * 2
    out = {}
    for sb, lab in zip(seeds, labels):
        streams = {}
        for hn, H in (("sha256", hashlib.sha256), ("sha512", hashlib.sha512), ("md5", hashlib.md5)):
            raw, i = bytearray(), 0
            while len(raw) < need:
                raw += H(sb + i.to_bytes(4, "big")).digest()
                i += 1
            streams[f"{hn}-ctr"] = bytes(raw)
        raw, x = bytearray(), hashlib.sha256(sb).digest()
        while len(raw) < need:
            raw += x
            x = hashlib.sha256(x).digest()
        streams["sha256-chain"] = bytes(raw)
        for gname, raw in streams.items():
            b = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
            out[f"{gname} mod :{lab}"] = (b % N)[:L]
            rej = b[b < 232] % N
            out[f"{gname} reject :{lab}"] = rej[:L]
    # the payload itself as key material (cycled)
    pb = np.frombuffer(payload, dtype=np.uint8).astype(np.int64)
    out["payload bytes mod 29 (cycled)"] = np.resize(pb % N, L)
    out["payload bytes reversed mod 29 (cycled)"] = np.resize(pb[::-1] % N, L)
    toks = grid60.grid_tokens()
    digs = [grid60.DIGITS.index(ch) for t in toks for ch in t]
    out["payload base-60 digits mod 29 (cycled)"] = np.resize(np.array(digs) % N, L)
    return out


def library():
    ks = {}
    ks.update(keystreams.number_keystreams())
    ks.update(new_number_families())
    ks.update(more_constants())
    ks.update(hash_streams())
    ks.update(keystreams.keywords())
    return ks


def write_ksb(path, ks, info_path):
    P = keystreams.english_distribution()
    rows = []
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(ks)))
        for name, v in ks.items():
            v = np.asarray(v, dtype=np.int64) % N
            # predicted ciphertext IoC from the full-length stream (before a periodic one is truncated)
            n = min(4000, len(v))
            pi = max(keystreams.predicted_ioc(v, P, 1, n=n), keystreams.predicted_ioc(v, P, -1, n=n))
            p = keystreams.period(v, max_p=5000, probe=min(3000, len(v) // 2))
            if p:
                v = v[:p + KEEP]
            nb = name.encode("utf-8")[:300]
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v.astype(np.uint8)))
            rows.append((name, len(v), p or 0, pi))
    with open(info_path, "w", newline="\n", encoding="utf-8") as f:
        f.write("name\tlength\tperiod\tpredicted_ioc_english\texcluded_by_global_ioc\n")
        for name, n, p, pi in rows:
            f.write(f"{name}\t{n}\t{p}\t{pi:.4f}\t{int(pi > 1.003)}\n")
    return rows


def main():
    os.makedirs(OUT, exist_ok=True)
    segw = segment_windows()
    headw = head_windows()
    pagew = page_windows()
    write_windows(os.path.join(OUT, "segments.txt"), segw)
    write_windows(os.path.join(OUT, "heads.txt"), headw)
    write_windows(os.path.join(OUT, "pages.txt"), pagew)
    ks = library()
    rows = write_ksb(os.path.join(OUT, "library.ksb"), ks, os.path.join(OUT, "library.tsv"))
    excl = sum(pi > 1.003 for _, _, _, pi in rows)
    print(f"windows: {len(segw)} segments, {len(headw)} headings, {len(pagew)} pages; "
          f"library: {len(rows)} keystreams ({excl} already excluded by LP2's flat IoC under English plaintext)")


if __name__ == "__main__":
    main()
