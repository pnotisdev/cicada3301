"""Phase 4: decoding under the collision-skip rule, and keystream screening.

Encryption model (sim.make_skip_key): c_i = t_i + s*k_j with t_i = p_i (or 28 - p_i for
Atbash). If c_i would equal c_{i-1}, the encryptor (usually) skips to k_{j+1}, so the key
pointer advances by 2 instead of 1. Reading backwards, a skip at rune i is only possible
when t_i + s*k_j == c_{i-1} with t_i = c_i - s*k_{j+1}, i.e. when
    s*(k_j - k_{j+1}) == c_{i-1} - c_i   (mod 29)
which happens at about 1/29 of positions for a given key. At those "branch points" both
readings are possible, so the decoder keeps a beam of key alignments, scored by the
dictionary fitness of the words around the branch.

    python attack.py validate      # synthetic test of the decoder
    python attack.py screen        # run the keystream library over the unsolved segments
"""
import json
import os
import random
import sys
import time

import lp

N = lp.N
HERE = os.path.dirname(os.path.abspath(__file__))


class Text:
    """Ciphertext runes plus word spans taken from the token stream (word boundaries are
    visible in the ciphertext, so they do not depend on the decryption)."""

    def __init__(self, toks):
        self.toks = toks
        self.c = lp.runes_of(toks)
        self.words = [(a, b) for _, a, b in lp.word_spans(toks, self.c)]
        self.word_at = [0] * len(self.c)
        for w, (a, b) in enumerate(self.words):
            for i in range(a, b):
                self.word_at[i] = w
        self.one_rune = [a for a, b in self.words if b - a == 1]

    def score(self, plain, lo, hi):
        """Dictionary fitness of words lying fully inside runes [lo, hi) (plain must cover them)."""
        if lo >= len(self.c):
            return 0.0
        w0 = self.word_at[max(0, lo)]
        num = den = 0.0
        for a, b in self.words[w0:]:
            if a >= hi:
                break
            if a < lo or b > hi or b > len(plain):
                continue
            word = "".join(lp.LATIN[x] for x in plain[a:b])
            num += (b - a) * lp.COMMON_N.get(lp.normalize(word), 0.0)
            den += b - a
        return num / den if den else 0.0

    def ai_rate(self, plain, upto=None):
        """Share of one-rune words that decode to A or I."""
        pos = [a for a in self.one_rune if upto is None or a < upto]
        if not pos:
            return 0.0
        return sum(plain[a] in (24, 10) for a in pos) / len(pos)


def decode(text, keyfn, sign=1, atbash=False, n=None, beam=64, skip=True, max_skips=3):
    """Decode under the collision-skip rule. keyfn(j) -> key value.

    Viterbi-style search over key alignments: a state is the key pointer j (the future
    depends only on j), states with the same j are merged keeping the best, and states are
    ranked by the cumulative dictionary score of completed words. Returns
    (plain, skip_positions, score)."""
    c = text.c[:n] if n else text.c
    n = len(c)
    K = {}

    def k(j):
        if j not in K:
            K[j] = keyfn(j) % N
        return K[j]

    word_end = {}
    for a, b in text.words:
        if b <= n:
            word_end[b - 1] = a

    def bump(state, i):
        plain, j, skips, cum = state
        a = word_end.get(i)
        if a is not None:
            word = "".join(lp.LATIN[x] for x in plain[a:i + 1])
            cum += (i + 1 - a) * lp.COMMON_N.get(lp.normalize(word), 0.0)
        return (plain, j, skips, cum)

    states = [([], 0, (), 0.0)]
    for i in range(n):
        new = {}
        for plain, j, skips, cum in states:
            cands = [(plain, j, skips)]
            if skip and i > 0:
                # m skips at rune i: the true t = c_i - s*k_{j+m} collided with c_{i-1}
                # under each of k_j .. k_{j+m-1}
                for m in range(1, max_skips + 1):
                    t = (c[i] - sign * k(j + m)) % N
                    if all((t + sign * k(j + u)) % N == c[i - 1] for u in range(m)):
                        cands.append((list(plain), j + m, skips + (i,) * m))
            for pl, jj, sk in cands:
                t = (c[i] - sign * k(jj)) % N
                pl.append(N - 1 - t if atbash else t)
                st = bump((pl, jj + 1, sk, cum), i)
                old = new.get(st[1])
                if old is None or (st[3], -len(st[2])) > (old[3], -len(old[2])):
                    new[st[1]] = st
        states = sorted(new.values(), key=lambda s: (s[3], -len(s[2])), reverse=True)[:beam]
    plain, j, skips, cum = states[0]
    return plain, skips, text.score(plain, 0, n)


# ---------------------------------------------------------------- synthetic validation

def synthetic_tokens(n_runes=1500, start=5000):
    """English (Emerson) as a token stream with word gaps, n_runes long."""
    import re
    path = os.path.join(HERE, "ref", "emerson_essays1.txt")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    toks = []
    for w in re.findall(r"[A-Za-z]+", text)[start:]:
        r = lp.word_to_key(w.upper().replace("IO", "IA"))
        if len(lp.runes_of(toks)) + len(r) > n_runes:
            break
        toks += r + [" "]
    return toks


def encrypt_tokens(toks, keyfn, q=0.8, sign=1, atbash=False, seed=0, skips_out=None):
    R = random.Random(seed)
    out, c, j = [], [], 0
    for t in toks:
        if not isinstance(t, int):
            out.append(t)
            continue
        x = N - 1 - t if atbash else t
        y = (x + sign * keyfn(j)) % N
        j += 1
        while c and y == c[-1] and R.random() < q:
            y = (x + sign * keyfn(j)) % N
            j += 1
            if skips_out is not None:
                skips_out.append(len(c))
        c.append(y)
        out.append(y)
    return out


def validate():
    ps = lp.primes(20000)
    keys = {
        "totient primes": lambda j: ps[j] - 1,
        "DIVINITY": (lambda kw: lambda j: kw[j % len(kw)])(lp.word_to_key("DIVINITY")),
        "random": (lambda R: (lambda r: lambda j: r[j])([R.randrange(N) for _ in range(20000)]))(random.Random(5)),
    }
    plain_toks = synthetic_tokens(1500)
    truth = lp.runes_of(plain_toks)
    for name, kf in keys.items():
        for sign, atb in ((1, False), (-1, True)):
            enc = encrypt_tokens(plain_toks, kf, q=0.8, sign=sign, atbash=atb, seed=1)
            T = Text(enc)
            d = sum(a == b for a, b in zip(T.c, T.c[1:]))
            t0 = time.time()
            plain, skips, sc = decode(T, kf, sign=sign, atbash=atb)
            acc = sum(a == b for a, b in zip(plain, truth)) / len(truth)
            noskip = lp.keyed(T.c, kf) if sign == 1 and not atb else None
            base = (sum(a == b for a, b in zip(noskip, truth)) / len(truth)) if noskip else None
            print(f"{name:15s} sign={sign:+d} atbash={atb!s:5s} doublets={100 * d / len(T.c):.2f}%  "
                  f"accuracy={100 * acc:.1f}%  score={sc:.2f}  A/I={T.ai_rate(plain):.2f}  skips={len(skips)}"
                  + (f"  (plain keyed decrypt: {100 * base:.1f}%)" if base is not None else "")
                  + f"  {time.time() - t0:.1f}s")
    # wrong key must score low
    enc = encrypt_tokens(plain_toks, keys["totient primes"], q=0.8, seed=1)
    T = Text(enc)
    plain, _, sc = decode(T, lambda j: ps[j] + 1)
    print(f"wrong key (primes+1)              score={sc:.2f}  A/I={T.ai_rate(plain):.2f}")
    print("sample:", lp.render(enc, decode(T, keys["totient primes"])[0])[:160])




# ---------------------------------------------------------------- fast vectorised screen

import numpy as np  # noqa: E402

DIGRAPHS = {"TH": 2, "EO": 12, "NG": 21, "OE": 22, "AE": 25, "IA": 27, "IO": 27, "EA": 28}
SINGLE = {l: i for i, l in enumerate(lp.LATIN) if len(l) == 1}
SINGLE.update({"V": 1, "K": 5, "Q": 5, "Z": 15})
MAXLEN = 12


def rune_spellings(word, limit=16):
    """All rune spellings of a Latin word (digraphs may or may not be one rune)."""
    out = []

    def rec(i, acc):
        if len(out) >= limit or len(acc) > MAXLEN:
            return
        if i == len(word):
            out.append(tuple(acc))
            return
        if word[i:i + 3] == "ING":
            rec(i + 3, acc + [21])
        dg = DIGRAPHS.get(word[i:i + 2])
        if dg is not None:
            rec(i + 2, acc + [dg])
        if word[i] in SINGLE:
            rec(i + 1, acc + [SINGLE[word[i]]])
    rec(0, [])
    return out


_RDICT = {}


def rune_dictionary(reverse=False):
    """length -> (sorted int codes, weights) for every dictionary word spelt in runes.
    reverse=True spells every word backwards (for decoding a reversed rune stream)."""
    if reverse not in _RDICT:
        best = {}
        for w, wt in lp.COMMON_N.items():
            for sp in rune_spellings(w):
                if reverse:
                    sp = sp[::-1]
                code = 0
                for x in sp:
                    code = code * N + x
                key = (len(sp), code)
                best[key] = max(best.get(key, 0.0), wt)
        d = {}
        for L in range(1, MAXLEN + 1):
            items = sorted((code, wt) for (l, code), wt in best.items() if l == L)
            d[L] = (np.array([c for c, _ in items], dtype=np.int64), np.array([w for _, w in items]))
        _RDICT[reverse] = d
    return _RDICT[reverse]


def fast_screen(c, words, ks, sign=1, atbash=False, D=24, reverse=False):
    """Score for each constant shift b (0..28) of: key value = ks[i + d] + b, with the
    shift d non-decreasing from word to word (what the collision-skip rule does).
    c: ciphertext runes (np array); words: [(a, b)]; ks: key array of len >= len(c) + D.
    Returns np.array(29) of fitness in [0, 1]. reverse=True scores against backwards words."""
    rd = rune_dictionary(reverse)
    n = len(c)
    K = np.lib.stride_tricks.sliding_window_view(ks[:n + D], n)[:D]          # (D, n): K[d, i] = ks[i+d]
    P = (c[None, None, :] - sign * (K[None, :, :] + np.arange(N)[:, None, None])) % N  # (29, D, n)
    if atbash:
        P = N - 1 - P
    best = np.zeros((N, D))
    total = 0
    for a, b in words:
        L = b - a
        if b > n:
            break
        total += L
        if L > MAXLEN:
            best = np.maximum.accumulate(best, axis=1)
            continue
        code = np.zeros((N, D), dtype=np.int64)
        for x in range(a, b):
            code = code * N + P[:, :, x]
        codes, wts = rd[L]
        idx = np.clip(np.searchsorted(codes, code), 0, len(codes) - 1)
        W = np.where(codes[idx] == code, wts[idx], 0.0)
        best = np.maximum.accumulate(best, axis=1) + L * W
    return best.max(axis=1) / max(total, 1)


def fast_screen_batch(c, words, ks, offsets, sign=1, atbash=False, D=24, reverse=False):
    """fast_screen for many key start offsets at once. Returns array (len(offsets), 29)."""
    rd = rune_dictionary(reverse)
    n = len(c)
    offsets = np.asarray(offsets)
    idx = offsets[:, None, None] + np.arange(D)[None, :, None] + np.arange(n)[None, None, :]
    K = ks[idx]                                                    # (O, D, n)
    P = (c[None, None, None, :] - sign * (K[:, None, :, :] + np.arange(N)[None, :, None, None])) % N
    if atbash:
        P = N - 1 - P                                              # (O, 29, D, n)
    O = len(offsets)
    best = np.zeros((O, N, D))
    total = 0
    for a, b in words:
        L = b - a
        if b > n:
            break
        total += L
        if L > MAXLEN:
            best = np.maximum.accumulate(best, axis=2)
            continue
        code = np.zeros((O, N, D), dtype=np.int64)
        for x in range(a, b):
            code = code * N + P[:, :, :, x]
        codes, wts = rd[L]
        j = np.clip(np.searchsorted(codes, code), 0, len(codes) - 1)
        W = np.where(codes[j] == code, wts[j], 0.0)
        best = np.maximum.accumulate(best, axis=2) + L * W
    return best.max(axis=2) / max(total, 1)


# ---------------------------------------------------------------- screening run

SCREEN_SEGS = [7, 8, 9, 11, 12, 13, 14, 15]
SCREEN_RUNES = 300
_W = {}


def _segment_inputs():
    segs = lp.load_segments()
    before, glob, unsolved_start = 0, {}, {}
    acc_unsolved = 0
    for i, s in enumerate(segs):
        glob[i] = before
        before += len(lp.runes_of(s))
        if 7 <= i <= 15:
            unsolved_start[i] = acc_unsolved
            acc_unsolved += len(lp.runes_of(s))
    inputs = {}
    for i in SCREEN_SEGS:
        T = Text(segs[i])
        inputs[i] = (np.array(T.c[:SCREEN_RUNES]), [w for w in T.words if w[1] <= SCREEN_RUNES],
                     {"start": 0, "global": glob[i], "unsolved": unsolved_start[i]})
    return inputs


def _init_worker():
    import keystreams
    _W["ks"] = keystreams.all_keystreams()
    R = random.Random(29)
    for r in range(40):
        _W["ks"][f"CONTROL random {r}"] = np.array([R.randrange(N) for _ in range(keystreams.LEN)])
    _W["inp"] = _segment_inputs()


def _screen_one(name):
    ks = _W["ks"][name]
    rows = []
    for seg, (c, words, offsets) in _W["inp"].items():
        for oname, off in offsets.items():
            if off + len(c) + 24 > len(ks):
                continue
            k = ks[off:]
            for sign in (1, -1):
                for atb in (False, True):
                    s = fast_screen(c, words, k, sign, atb)
                    b = int(s.argmax())
                    rows.append((float(s[b]), name, seg, oname, sign, atb, b))
    return rows


def screen(out_path=os.path.join(HERE, "tmp", "phase4", "screen.json")):
    from multiprocessing import Pool
    import keystreams
    names = list(keystreams.all_keystreams()) + [f"CONTROL random {r}" for r in range(40)]
    t0 = time.time()
    rows = []
    with Pool(initializer=_init_worker) as pool:
        for k, res in enumerate(pool.imap_unordered(_screen_one, names, chunksize=4)):
            rows += res
            if k % 100 == 0:
                print(f"{k}/{len(names)} keystreams, {time.time() - t0:.0f}s", flush=True)
    rows.sort(reverse=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(rows, f)
    ctrl = [r[0] for r in rows if r[1].startswith("CONTROL")]
    print(f"\n{len(rows)} screens in {time.time() - t0:.0f}s. Controls: max {max(ctrl):.3f}, "
          f"p99.9 {np.percentile(ctrl, 99.9):.3f}")
    print("top 25:")
    for r in rows[:25]:
        print(f"  {r[0]:.3f}  {r[1][:40]:40s} seg 0.{r[2]:<2} off={r[3]:8s} sign={r[4]:+d} atbash={r[5]!s:5s} b={r[6]}")
    return rows


# ---------------------------------------------------------------- sliding-offset screen

STEP = 12


def _init_sliding():
    import keystreams
    _W["ks"] = keystreams.number_keystreams()
    R = random.Random(1033)
    for r in range(4):
        _W["ks"][f"CONTROL random {r}"] = np.array([R.randrange(N) for _ in range(keystreams.LEN)])
    _W["inp"] = _segment_inputs()


def _slide_one(name):
    import keystreams
    ks = _W["ks"][name]
    p = keystreams.period(ks)
    limit = (p + STEP) if p else len(ks) - SCREEN_RUNES - 30
    offsets = np.arange(0, limit, STEP)
    rows = []
    for seg, (c, words, _) in _W["inp"].items():
        for sign in (1, -1):
            for atb in (False, True):
                for o0 in range(0, len(offsets), 128):
                    offs = offsets[o0:o0 + 128]
                    S = attack_batch(c, words, ks, offs, sign, atb)
                    flat = S.max(axis=1)
                    for k in np.argsort(flat)[-3:]:
                        rows.append((float(flat[k]), name, seg, int(offs[k]), sign, atb, int(S[k].argmax())))
    rows.sort(reverse=True)
    return name, len(offsets), rows[:40]


def attack_batch(*a, **k):
    return fast_screen_batch(*a, **k)


def screen_sliding(out_path=os.path.join(HERE, "tmp", "phase4", "screen_sliding.json")):
    from multiprocessing import Pool
    import keystreams
    names = list(keystreams.number_keystreams()) + [f"CONTROL random {r}" for r in range(4)]
    t0 = time.time()
    result = {}
    with Pool(initializer=_init_sliding) as pool:
        for k, (name, n_off, rows) in enumerate(pool.imap_unordered(_slide_one, names)):
            result[name] = {"offsets": n_off, "top": rows}
            print(f"{k + 1}/{len(names)} {name[:34]:34s} offsets={n_off:5d} best={rows[0][0]:.3f} "
                  f"(seg 0.{rows[0][2]} off {rows[0][3]} sign {rows[0][4]:+d} atb {rows[0][5]} b {rows[0][6]})  "
                  f"{time.time() - t0:.0f}s", flush=True)
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f)
    allrows = sorted((r for v in result.values() for r in v["top"]), reverse=True)
    ctrl = [r[0] for r in allrows if r[1].startswith("CONTROL")]
    print(f"\ncontrols (full offset range): max {max(ctrl):.3f}")
    print("top 20 non-control:")
    for r in [r for r in allrows if not r[1].startswith("CONTROL")][:20]:
        print(f"  {r[0]:.3f}  {r[1][:36]:36s} seg 0.{r[2]:<2} off={r[3]:6d} sign={r[4]:+d} atbash={r[5]!s:5s} b={r[6]}")
    return result


if __name__ == "__main__":
    {"validate": validate, "screen": screen, "slide": screen_sliding}[sys.argv[1]]()
