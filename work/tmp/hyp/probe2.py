"""Probe 2 (2026-10-17, laptop): progressive kappa.

Hypothesis family H-PROG: a non-uniform running key t (English text, the book's own plaintext, ...) plus a
progressive (Trithemius) shift, k_j = t_j + s*j (mod 29), under the skip rule. Its ciphertext has a flat
unigram distribution (IoC 1.000) and no lag coincidences, so the IoC and lag scans cannot see it, and the
residual sweep of Phase 3 loses it because skips move the key pointer j away from the rune index i.
Over short distances d the drift is usually zero, and then c[i+d] - c[i] = (p+t)[i+d] - (p+t)[i] + s*d, which
equals s*d with probability IoC(p+t)/29 (about 1.05/29 for English plus English) instead of 1/29.

Statistic: T(s) = sum over d = dmin..W of #{i : c[i+d] - c[i] = s*d (mod 29)}, within sections, with a
z-score against the uniform expectation. s = 0 is the ordinary kappa test.
Controls: Emerson enciphered with an English running key (another Gutenberg text) plus s*j under the skip rule
(q = 0.8); the same with a random key (null).
"""
import os
import random
import re
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WORK)
import lp  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
N = lp.N
LP2 = list(range(7, 16))


def text_runes(path, skip_chars=20000, limit=None):
    with open(path, encoding="utf-8", errors="ignore") as f:
        text = f.read()
    text = text[skip_chars:]
    text = text.split("*** END OF")[0]
    out = []
    for w in re.findall(r"[A-Za-z]+", text):
        out += lp.word_to_key(w.upper().replace("IO", "IA"))
        if limit and len(out) >= limit:
            break
    return out


def prog_kappa(streams, W=30, dmin=2):
    """{s: (observed, expected, z)}"""
    obs = Counter()
    exp = 0.0
    for c in streams:
        n = len(c)
        for d in range(dmin, W + 1):
            m = n - d
            if m <= 0 or d % N == 0:
                continue
            exp += m / N
            for i in range(m):
                obs[((c[i + d] - c[i]) * pow(d, -1, N)) % N] += 1
    return {s: (obs[s], exp, (obs[s] - exp) / (exp * (1 - 1 / N)) ** 0.5) for s in range(N)}


def encrypt_prog(p, t, s, q, R, key=None):
    c, j = [], 0
    ks = key if key is not None else [(t[x] + s * x) % N for x in range(len(t))]
    for x in p:
        y = (x + ks[j]) % N
        j += 1
        while c and y == c[-1] and R.random() < q:
            y = (x + ks[j]) % N
            j += 1
        c.append(y)
    return c


def show(name, res, top=4):
    zs = sorted(res.items(), key=lambda kv: -kv[1][2])
    line = ", ".join(f"s={s}:{z:+.1f}" for s, (_, _, z) in zs[:top])
    print(f"  {name:38s} max z {zs[0][1][2]:+5.2f} ({line})")
    return zs


def main():
    segs = lp.load_segments()
    streams = [lp.runes_of(segs[i]) for i in LP2]

    # step histogram (lag 1)
    st = Counter()
    for c in streams:
        for a, b in zip(c, c[1:]):
            st[(b - a) % N] += 1
    n1 = sum(st.values()) - st[0]
    e = n1 / 28
    print("LP2 step histogram c[i+1]-c[i], bins 1..28 (expected %.1f each; z):" % e)
    print("  " + " ".join(f"{b}:{(st[b] - e) / e ** 0.5:+.1f}" for b in range(1, N)))
    chi = sum((st[b] - e) ** 2 / e for b in range(1, N))
    print(f"  chi-square {chi:.1f} on 27 df; bin 0 = {st[0]}")

    print("\nprogressive kappa on LP2 (z per step s; 28 tests, look-elsewhere max of 28 normals ~ +2.4):")
    for W, dmin in ((10, 2), (30, 2), (60, 2), (30, 1)):
        show(f"LP2 W={W} dmin={dmin}", prog_kappa(streams, W, dmin))

    # controls
    R = random.Random(3301)
    corp = os.path.join(WORK, "ref", "corpora")
    emer = text_runes(os.path.join(WORK, "ref", "emerson_essays1.txt"))
    key_texts = [f for f in sorted(os.listdir(corp)) if f.endswith(".txt")]
    lens = [len(c) for c in streams]
    print("\ncontrols (section lengths as LP2, q = 0.8):")
    done = 0
    for kt in key_texts:
        t = text_runes(os.path.join(corp, kt), limit=60000)
        if len(t) < 3 * sum(lens) or done == 4:
            continue
        done += 1
        s = R.randrange(1, N)
        off = R.randrange(0, len(emer) - 20000)
        tst, pos, toff = [], off, 0
        for L in lens:
            p = emer[pos:pos + L]
            pos += L
            tt = t[toff:toff + 3 * L]
            toff += 3 * L
            tst.append(encrypt_prog(p, tt, s, 0.8, R))
        res = prog_kappa(tst, 30, 2)
        zs = show(f"plant s={s} key text {kt}", res)
        print(f"      true s rank {[k for k, _ in zs].index(s) + 1}, z {res[s][2]:+.2f}")
    mx = []
    for trial in range(40):
        tst = []
        for L in lens:
            p = emer[R.randrange(0, len(emer) - L):][:L]
            key = [R.randrange(N) for _ in range(3 * L)]
            tst.append(encrypt_prog(p, None, 0, 0.8, R, key=key))
        mx.append(max(z for _, _, z in prog_kappa(tst, 30, 2).values()))
    mx.sort()
    print(f"  null (random key, same rule), max z over the 28 steps, 40 replicates: median {mx[20]:+.2f}, "
          f"90% {mx[36]:+.2f}, max {mx[-1]:+.2f}")


if __name__ == "__main__":
    main()
