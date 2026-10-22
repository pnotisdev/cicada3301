"""Phase 58: DJU BEI as reused key. See work/log/phase58_djubei_reuse.md.

    python -B work/phase58_djubei_reuse.py     # -> results/analysis/phase58_djubei_reuse.txt
Scans every stream of work/kscreen/data/library.ksb for equal runs (>= 6, >= 5) at key distance 5,700-6,500, against 100 shuffles per stream.
Equal runs are unchanged by key sign and by any multiplier (k -> m k, k -> -k), so one scan covers all 28 x 2 variants.
"""
import ctypes
import os
import struct
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402

ctypes.windll.kernel32.SetPriorityClass(ctypes.windll.kernel32.GetCurrentProcess(), 0x4000)  # BELOW_NORMAL

Q, LO, HI, NSH = 29, 5700, 6500, 100
OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def load_ksb(path):
    b = open(path, "rb").read()
    assert b[:4] == b"KSB1"
    n, p, out = struct.unpack_from("<I", b, 4)[0], 8, []
    for _ in range(n):
        ln = struct.unpack_from("<H", b, p)[0]
        name = b[p + 2:p + 2 + ln].decode("utf-8")
        p += 2 + ln
        kl = struct.unpack_from("<I", b, p)[0]
        out.append((name, np.frombuffer(b, np.uint8, kl, p + 4).astype(np.int64)))
        p += 4 + kl
    return out


def scan(v, m):
    """(i, j) arrays with j - i in [LO, HI] and v[i:i+m] == v[j:j+m]; streams are < 65,536 long"""
    if len(v) < m + LO:
        return np.zeros(0, np.int64), np.zeros(0, np.int64)
    h = np.zeros(len(v) - m + 1, np.int64)
    for t in range(m):
        h = h * Q + v[t:len(v) - m + 1 + t]
    pos = np.arange(len(h), dtype=np.int64)
    c = (h << 16) | pos
    comb = np.sort(c)
    a, b = np.searchsorted(comb, c + LO, 'left'), np.searchsorted(comb, c + HI, 'right')
    n = b - a
    ii = np.repeat(pos, n)
    jj = np.concatenate([comb[x:y] & 0xFFFF for x, y in zip(a[n > 0], b[n > 0])]) if n.any() else np.zeros(0, np.int64)
    return ii, jj


def count(v, m):
    return len(scan(v, m)[0])


def book():
    segs = lp.load_segments()
    words, flat = [], []
    for si in range(7, 16):
        cur, seps = [], []
        for t in segs[si] + [" "]:
            if isinstance(t, int):
                cur.append(len(flat))
                flat.append(t)
            elif t in ("\n", "%"):
                if cur:
                    seps.append((len(cur), t))
            elif cur:
                words.append((si, cur[0], len(cur), seps))
                cur, seps = [], []
    return segs, flat, words


def main():
    segs, flat, words = book()
    say("== 1. DJU BEI copies ==")
    seen = {}
    for k in range(len(words) - 1):
        key = tuple(flat[words[k][1]:words[k][1] + words[k][2]]), tuple(flat[words[k + 1][1]:words[k + 1][1] + words[k + 1][2]])
        seen.setdefault(key, []).append(k)
    pairs = [(k, v) for k, v in seen.items() if len(v) > 1 and len(k[0]) + len(k[1]) == 6]
    for key, ks in pairs:
        say("repeated adjacent word pair, 6 runes: " + " ".join("".join(lp.LATIN[r] for r in w) for w in key))
        for k in ks:
            w = words[k]
            say(f"  words {k},{k + 1}: segment {w[0]}, flat start {w[1]}, word lengths {words[k][2]},{words[k + 1][2]}, line/page breaks inside first word {w[3]}")
    assert len(pairs) == 1
    ks = pairs[0][1]
    p1, p2 = words[ks[0]][1], words[ks[1]][1]
    D = p2 - p1
    starts = {si: sum(isinstance(t, int) for s in segs[7:si] for t in s) for si in range(7, 16)}
    say(f"  rune distance {D}; second copy ends at {p2 + 6} of {len(flat)} (book end: {p2 + 6 == len(flat)}); segment starts (flat): {starts}")
    s1, s2 = words[ks[0]][0], words[ks[1]][0]
    say(f"  copy 1 in segment {s1} ({p1 - starts[s1]} runes in), copy 2 in segment {s2}; sections between: {s2 - s1 - 1}; "
        f"page breaks strictly between the copies: {sum(1 for si in range(s1, s2 + 1) for t in segs[si] if t == '%')} (over whole segments {s1}..{s2})")

    lib = load_ksb(os.path.join(HERE, "kscreen", "data", "library.ksb"))
    say(f"\n== 2. scan: {len(lib)} streams, key distance {LO}-{HI}, {NSH} shuffles each ==")
    rng = np.random.default_rng(58)
    c = rng.integers(0, Q, 20000)
    c[9000:9006] = c[2900:2906]
    ii, jj = scan(c, 6)
    ok = (2900, 9000) in {(int(a), int(b)) for a, b in zip(ii, jj)}
    say(f"positive control (6-run planted at 2900 / 9000, d 6100): found {ok}, total pairs {len(ii)}")
    assert ok
    z = [count(rng.integers(0, Q, 20000), 6) for _ in range(300)]
    say(f"null control, 300 iid streams of 20,000: mean 6-pairs {np.mean(z):.4f} (expected {(20000 - 5 - LO) * (HI - LO + 1) * Q ** -6:.4f}), max {max(z)}")

    rows = []
    for name, v in lib:
        r6, r5 = count(v, 6), count(v, 5)
        s6, s5 = [], []
        for _ in range(NSH):
            w = rng.permutation(v)
            s6.append(count(w, 6))
            s5.append(count(w, 5))
        rows.append((name, len(v), r6, r5, np.mean(s6), max(s6), np.mean(s5), max(s5)))
    say(f"library total: real 6-pairs {sum(r[2] for r in rows)}, shuffle mean {sum(r[4] for r in rows):.2f}; "
        f"real 5-pairs {sum(r[3] for r in rows)}, shuffle mean {sum(r[6] for r in rows):.2f}")
    exp = lambda n, m: max(n - m + 1 - LO, 0) * (HI - LO + 1) * Q ** -m
    say(f"iid expectation over the library: 6-pairs {sum(exp(r[1], 6) for r in rows):.2f}, 5-pairs {sum(exp(r[1], 5) for r in rows):.2f}")
    ex = [r for r in rows if r[2] > r[5]]
    say(f"streams with real 6-pairs above their shuffle maximum: {len(ex)}; with any 6-pair: {sum(r[2] > 0 for r in rows)}")
    for r in sorted(ex, key=lambda r: -r[2])[:40]:
        say(f"  {r[0][:48]:48s} len {r[1]:5d} 6-pairs {r[2]:5d} (shuf mean {r[4]:.2f} max {r[5]}) 5-pairs {r[3]:5d} (shuf mean {r[6]:.1f} max {r[7]})")
    say(f"streams with 5-pairs above shuffle max but no 6-excess: {sum(1 for r in rows if r[3] > r[7] and r not in ex)}")

    say("\n== 3. decode check of 6-run repeats in streams with <= 300 pairs (not the periodic / low-entropy streams) ==")
    cip = np.array(flat)
    best = []
    for name, v in lib:
        ii, jj = scan(v, 6)
        if not 0 < len(ii) <= 300:
            continue
        for i, j in zip(ii, jj):
            o = int(i) - p1
            if o < 0 or o + len(cip) > len(v):
                continue
            for sgn in (1, -1):
                pl = (cip - sgn * v[o:o + len(cip)]) % Q
                best.append((lp.ioc(list(pl[max(p1 - 150, 0):p1 + 156])), lp.ioc(list(pl)), name, int(i), int(j), o, sgn, D - int(j - i)))
    say(f"pairs at exactly the rune distance {D} (no skips): " + (", ".join(n for n, v in lib if (lambda a, b: bool(((b - a) == D).any()))(*scan(v, 6))) or "none"))
    say(f"candidates with a usable offset (copy 1 at the first repeat): {len(best)}; best by IoC of the 306 runes around copy 1:")
    for b in sorted(best, reverse=True)[:8]:
        say(f"  window {b[0]:.3f} whole-book {b[1]:.3f} {b[2][:40]} i={b[3]} j={b[4]} offset={b[5]} sign={b[6]:+d} skipped-between={b[7]}")
    say("  (random windows ~1.05-1.35; verify.py REAL threshold 1.40; this plain no-skip decode is only a screen, verify.py not run)")

    say("\n== 4. constraint ==")
    say("DJU BEI is the same 6 ciphertext runes twice. For c' = c + s*k (mod 29) the plaintexts are equal iff k[a+t] = k[b+t], t = 0..5, "
        f"a, b the key positions of the copies. With no skipped or inserted runes b - a = {D}; otherwise b - a = {D} plus the extra key steps in between "
        f"(the scan samples {LO}-{HI}). Equal runs survive any sign or multiplier. So any screen that reports a key family and offset must also show k[a..a+5] = k[b..b+5] there; "
        "a periodic family passes only if its period divides b - a, and a non-periodic one only by chance (29^-6 = 1.7e-9 per pair). "
        "If the plaintexts differ the difference k[a+t] - k[b+t] is unconstrained, so only the equal-plaintext reading gives a test.")
    open(os.path.join(HERE, "..", "results", "analysis", "phase58_djubei_reuse.txt"), "w", encoding="utf-8").write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
