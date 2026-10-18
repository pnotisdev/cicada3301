"""lm_power gate: two-layer cipher is IoC-blind (below 1.40) but LL-separable.

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, LATIN, ioc, decode_beam, totient_key, words_of, bigram_table, \
    print_verdict

KW = ["DIVINITY", "FIRFUMFERENFE", "CIRCUMFERENCE", "INTUS", "INSTAR", "EMERGENCE",
      "PRIMALITY", "TOTIENT", "PILGRIM", "WELCOME"]


def kw_vals(kw):
    return [LATIN.index(ch) for ch in kw.upper() if ch in LATIN]


def ll(letters, bg=None):
    bg = bg if bg is not None else bigram_table()
    return sum(bg[a][b] for a, b in zip(letters, letters[1:]))


def main():
    print("=" * 72)
    print("lm_power gate: IoC blindness vs LL separation for a two-layer cipher")
    print("=" * 72)
    rng = random.Random(20261017)
    words = words_of(common.CORPUS_B)
    plain = [x for w, _ in words for x in w]
    t = totient_key(len(plain) * 2)
    kw = kw_vals("DIVINITY")
    L = len(kw)

    # Plant: c = p + kw + t with the anti-repeat skip on the total; record the pointer.
    c, j, prev, ptr = [], 0, -1, []
    for i, p in enumerate(plain):
        x = (p + kw[i % L] + t[j % len(t)]) % N
        j += 1
        if x == prev and rng.random() < 0.81:
            x = (p + kw[i % L] + t[j % len(t)]) % N
            j += 1
        c.append(x)
        prev = x
        ptr.append(j - 1)

    # 1. ideal outer-stream removal (the plant's own pointer path): the residual is
    #    Vigenere text whose IoC stays far below kscreen's 1.40 threshold.
    r = [(c[i] - t[ptr[i] % len(t)]) % N for i in range(len(c))]
    ioc_r = ioc(r)
    print("residual after ideal outer-stream removal: IoC %.3f (kscreen threshold 1.40)"
          % ioc_r)

    # 2. keyword ranking by IoC and by LL over 40 candidates.
    cands = [kw_vals(k) for k in KW]
    for _ in range(30):
        cands.append([rng.randrange(N) for _ in range(rng.randrange(6, 11))])
    rows = []
    for i, v in enumerate(cands):
        inner = [(r[k] - v[k % len(v)]) % N for k in range(len(r))]
        rows.append((ll(inner), ioc(inner), i))
    rows.sort(reverse=True)
    true_i = 0
    ll_true, ioc_true, _ = rows[[i for _, _, i in rows].index(0)]
    best_wrong_ll = max(v for v, _, i in rows if i != 0)
    ioc_rank = [i for _, _, i in rows].index(0) + 1
    print("true keyword by LL:  rank 1 of %d, LL %.1f nats" % (len(cands), ll_true))
    print("best wrong keyword:  LL %.1f nats -> margin %.3f nats/rune" %
          (best_wrong_ll, (ll_true - best_wrong_ll) / max(1, len(r))))
    print("true keyword by IoC: rank %d of %d (IoC %.3f)" % (ioc_rank, len(cands), ioc_true))

    ok = (ioc_r < 1.40) and (ll_true > best_wrong_ll) and \
        ((ll_true - best_wrong_ll) / max(1, len(r)) >= 0.3)
    return print_verdict("lm_power", ok,
                         "residual IoC %.2f (< 1.40: blind) | LL margin %.3f nats/rune "
                         "(>= 0.3: separable) | IoC rank of true keyword %d" %
                         (ioc_r, (ll_true - best_wrong_ll) / max(1, len(r)), ioc_rank))


if __name__ == "__main__":
    sys.exit(main())
