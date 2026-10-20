"""Reference code for the pointer-direction option of the kscreen engine (pdir=): a plan builder, an exact emulation of the engine's beam
decoder (`ioc_beam_dir`) and an exhaustive path search for tiny cases, plus an independent PLANTER that enciphers plaintext under a
direction rule and one of the 18 conventions. Written from the specification (work/log/phase30_pointer_direction.md), not from main.rs.

Convention digits h m c:
  h  first read of a backward word: 0 read then step, 1 step back, then read
  m  pointer movement between words: 0 none, 1 one step in the OLD word's direction, 2 one step in the NEW word's direction
  c  collision comparator of a backward rune: 0 previous emitted rune, 1 previous rune of the same word (none for the first),
     2 previous rune enciphered by a backward word
The pointer is the key index the next rune reads; a rune reads key j (first try), and on a collision its retries read j+d, j+2d (skip) or
the colliding try spends the next value as a coin (coin); d is the direction of the rune's word.
"""
import struct

Q = 29


def digits(conv):
    return tuple(int(x) for x in conv)


def plan(runes, lens, dirline, prev0, conv, neg=False):
    """(dirs, mv, pv) per rune: direction, pointer movement before the rune, collision-check value (-1 = none)"""
    h, m, c = digits(conv)
    flip = -1 if neg else 1
    n = len(runes)
    dirs, mv, pv = [0] * n, [0] * n, [0] * n
    pos, old, last_back = 0, None, prev0
    for L in lens:
        d = dirline[pos] * flip
        move = 0 if old is None else (0, old, d)[m]
        if d < 0 and h == 1:
            move -= 1
        mv[pos] = move
        for i in range(pos, pos + L):
            dirs[i] = d
            before = prev0 if i == 0 else runes[i - 1]
            if d > 0 or c == 0:
                pv[i] = before
            elif c == 1:
                pv[i] = -1 if i == pos else before
            else:
                pv[i] = last_back
            if d < 0:
                last_back = runes[i]
        old = d
        pos += L
    return dirs, mv, pv


def _swap_remove(v, i):
    v[i] = v[-1]
    v.pop()


def beam_emul(c, pvs, mk, model, n, beam, abort_at, abort_s, start, dirs, mv):
    """exact emulation of ioc_beam_dir (including swap_remove order, merging and the stable sort): returns (s, used, complete)"""
    def take(st, t, nj):
        st[1] += 2 * st[2][t]
        st[2][t] += 1
        st[0] = nj

    clone = lambda st: [st[0], st[1], list(st[2])]
    cur = [[start, 0, [0] * Q]]
    klen = len(mk)
    for i in range(n):
        ci, prev, d = c[i], pvs[i], dirs[i]
        if mv[i]:
            nxt = []
            for st in cur:
                if st[0] + mv[i] >= 0:
                    st[0] += mv[i]
                    nxt.append(st)
            cur = nxt
        extra, idx = [], 0
        while idx < len(cur):
            j = cur[idx][0]
            j2 = j + 2 * d
            if min(j, j2) < 0 or max(j, j2) >= klen:
                _swap_remove(cur, idx)
                continue
            k0, k1, k2 = mk[j], mk[j + d], mk[j2]
            t0 = (ci - k0) % Q
            if prev >= 0:
                t1, t2 = (ci - k1) % Q, (ci - k2) % Q
                if model == 0:
                    if (t1 + k0) % Q == prev and j + 2 * d >= 0:
                        s2 = clone(cur[idx])
                        take(s2, t1, j + 2 * d)
                        extra.append(s2)
                    if (t2 + k0) % Q == prev and (t2 + k1) % Q == prev and j + 3 * d >= 0:
                        s3 = clone(cur[idx])
                        take(s3, t2, j + 3 * d)
                        extra.append(s3)
                elif (t2 + k0) % Q == prev and j + 3 * d >= 0:
                    s3 = clone(cur[idx])
                    take(s3, t2, j + 3 * d)
                    extra.append(s3)
            nj = j + 2 * d if model == 1 and prev == ci else j + d
            if nj < 0:
                _swap_remove(cur, idx)
            else:
                take(cur[idx], t0, nj)
                idx += 1
        cur.extend(extra)
        if not cur:
            return 0, max(i, 2), False
        if len(cur) > 1:
            a = 0
            while a < len(cur):
                b = a + 1
                while b < len(cur):
                    if cur[b][0] == cur[a][0]:
                        if cur[b][1] > cur[a][1]:
                            cur[a] = cur[b]
                        _swap_remove(cur, b)
                    else:
                        b += 1
                a += 1
            if len(cur) > beam:
                cur.sort(key=lambda s: -s[1])
                cur = cur[:beam]
        if i + 1 == abort_at:
            best = max(s[1] for s in cur)
            if best < abort_s:
                return best, abort_at, False
    return max(s[1] for s in cur), n, True


def exhaustive(c, pvs, mk, model, n, start, dirs, mv):
    """the best coincidence sum over EVERY consistent pointer path (no merging, no beam); tiny n only"""
    klen = len(mk)
    best = [0]

    def go(i, j, cnt, s):
        if i == n:
            best[0] = max(best[0], s)
            return
        j += mv[i]
        d = dirs[i]
        if j < 0 or min(j, j + 2 * d) < 0 or max(j, j + 2 * d) >= klen:
            return
        ci, prev = c[i], pvs[i]
        k = [mk[j], mk[j + d], mk[j + 2 * d]]
        opts = []
        t0 = (ci - k[0]) % Q
        opts.append((t0, j + 2 * d if model == 1 and prev == ci else j + d))
        if prev >= 0:
            t1, t2 = (ci - k[1]) % Q, (ci - k[2]) % Q
            if model == 0:
                if (t1 + k[0]) % Q == prev:
                    opts.append((t1, j + 2 * d))
                if (t2 + k[0]) % Q == prev and (t2 + k[1]) % Q == prev:
                    opts.append((t2, j + 3 * d))
            elif (t2 + k[0]) % Q == prev:
                opts.append((t2, j + 3 * d))
        for t, nj in opts:
            if nj < 0:
                continue
            cnt[t] += 1
            go(i + 1, nj, cnt, s + 2 * (cnt[t] - 1))
            cnt[t] -= 1

    go(0, start, [0] * Q, 0)
    return best[0]


def plant(runes, lens, key, start, mult, model, keep, rule_dir, conv, neg, rng, numbers):
    """Independent planter. Enciphers `runes` word by word with key (a list, `start` = pointer before the first rune, key values before
    `start` are read by backward words); the native direction of word w comes from rule_dir(table, w) BEFORE the word is enciphered
    (table: current n and position plus the previous words' ciphertext numbers). Returns (cipher, native D line, the plan it used)."""
    h, m, cmp_ = digits(conv)
    mk = [k * mult % Q for k in key]
    P, old, prev_emitted, last_back = start, None, -1, -1
    c, native, words, used_pv, used_mv, pos = [], [], [], [], [], 0
    for w, n in enumerate(lens):
        table = words + [dict(n=n, w=w + 1, wp=w + 1, ws=w + 1)]
        nat = rule_dir(table, w)
        d = nat * (-1 if neg else 1)
        move = 0 if old is None else (0, old, d)[m]
        if d < 0 and h == 1:
            move -= 1
        P += move
        assert P >= 0, "pointer ran off the key start"
        word = []
        for r, p in enumerate(runes[pos:pos + n]):
            if d > 0 or cmp_ == 0:
                chk = prev_emitted
            elif cmp_ == 1:
                chk = -1 if r == 0 else prev_emitted
            else:
                chk = last_back
            used_pv.append(chk)
            used_mv.append(move if r == 0 else 0)
            y = (p + mk[P]) % Q
            P += d
            if model == 0:
                tries = 0
                while chk >= 0 and y == chk and rng.random() >= keep and tries < 5:
                    y = (p + mk[P]) % Q
                    P += d
                    tries += 1
            elif chk >= 0 and y == chk:
                P += d                                                   # the coin
                if rng.random() >= keep:
                    y = (p + mk[P]) % Q
                    P += d
            assert P >= 0, "pointer ran off the key start"
            c.append(y)
            native.append(nat)
            word.append(y)
            prev_emitted = y
            if d < 0:
                last_back = y
        old = d
        pos += n
        words.append(dict(n=n, w=w + 1, wp=w + 1, ws=w + 1, **numbers(word)))
    return c, native, (used_mv, used_pv)


def write_ksb(path, streams):
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(streams)))
        for name, v in streams:
            nb = name.encode("utf-8")
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v))


def write_windows(path, entries):
    """entries: (name, prev, runes, lens, dirline | None, truth comment | None)"""
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        for name, prev, runes, lens, dirline, truth in entries:
            if truth:
                f.write(truth + "\n")
            f.write(f"W {name} {prev}\nR {' '.join(map(str, runes))}\nL {' '.join(map(str, lens))}\n")
            if dirline is not None:
                f.write(f"D {' '.join(map(str, dirline))}\n")
