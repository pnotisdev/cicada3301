"""r4sim: ONE reference simulator of the R4 encryption mechanism (phase 57), for every later plant generator and simulation.

Nothing in LP2 is solved; this module only simulates a stated rule.  Pure Python + numpy, no repository imports.

    from r4sim import encrypt_r4, invert, words_from_lengths
    res = encrypt_r4(plain_words, key, rng, q=0.81, repair='T', nu=0.45, slots='any')
    res.cipher, res.word_start, res.is_null, res.key_index, ...

The rule (R4 of work/log/phase57_mechanism.md), per word of plaintext length L, in order
-------------------------------------------------------------------------------------
Nulls.  A word with L >= min_word (default 2, "multi-rune words") gets nulls with probability nu; the number of nulls is 1,
  2, ... with the probabilities `nulls_per_word` (default (1.0,): exactly one).  Each null has a SLOT s in 0..L meaning "emitted
  just before plaintext rune s of the word" (s = L: after the last one).  Its cipher position in the word is s (+ number of
  earlier nulls of the word).  `slots` fixes the allowed s (k nulls: k independent draws, sorted, ties = adjacent nulls):
      'any'       uniform on 0..L           (L+1 values; phase 57 `ins='word'`, mech25/insert47)
      'interior'  uniform on 1..L-1         (L-1 values; phase 57 pilot make_r4, plant_mid, phase 51 decoder)
      'edge'      0 or L with prob 1/2 each (the complement of 'interior')
      'start' / 'end'  s = 0 / s = L        (plant_edge 'nulli' / 'nullf'; phase 57 `ins='edge'` (R7) is 'end')
  A null carries no key and no plaintext.  Its value is uniform on the 29 runes, minus the excluded ones:
      null_check 'none'  nothing excluded          (plant_mid, plant_edge, phase 57 R3/R5: an unchecked null)
      'left'   != its left neighbour in the OUTPUT (the previous cipher rune, null or real; none at a section start)
               (phase 57 R4 `check=True`, pilot make_r4)
      'both'   additionally != its right neighbour: the pre-repair encryption of the next plaintext rune when that is the
               next element, else (the next element is another null, or the stream is not yet known) the neighbour is
               compared after it is emitted and the null is redrawn in place.  No right neighbour at the end of the call.
Real runes.  Plaintext rune p, key k = key[j] (j = the key pointer): x = (p + sign*k) mod 29.  The ANTI-REPEAT RULE compares x
  with `prev`: if x == prev (and prev exists), with probability q the rune is REPAIRED instead:
      repair 'uniform'  x := uniform on the 28 runes != prev
      repair 'T'        x := T(c[-lag]) when the rune `lag` back is in the SAME word and T(c[-lag]) != prev, else uniform != prev
                        (T(c) = 24 - 2c mod 29; phase 57 R1/R4, pilot).
  `prev` is  null_visible=True: the previous cipher rune whatever it is (a null counts; phase 57 R4 `blind=False`, pilot)
             null_visible=False: the last REAL cipher rune (repairs are real; a null is invisible; phase 57 R3 `blind=True`,
             phase 47/51 plants, plant_edge.step `ell`).
  "Checked" = the null-value redraw above.  "Visible" = the anti-repeat rule's `prev`.  They are independent parameters.
  The plaintext rune of a repaired position is LOST (the repair rune carries no plaintext) in every mode.
Key channel.  channel 'hold': a repair does NOT advance the key pointer (the next plaintext rune reuses key[j]);
  'spend': a repair advances it.  Both: a normal real rune advances it; a null never does.  (phase 57's simulation draws a fresh
  random key at every step, which equals 'spend' with an iid key; the library plants use 'hold' (m04) or 'spend'.)
Word position / lag.  lag_basis 'cipher' (default; phase 57 R4 and the pilot): positions count every cipher rune of the word
  including nulls; "rune `lag` back in the same word" = out[-lag] with at least `lag` cipher runes before it in the word.
  lag_basis 'real' (phase 57 R3, blind): counts REAL runes only (the repair looks back in the real stream, nulls skipped).
Words / sections.  plain_words is a list of words, each a sequence of plaintext runes 0..28.  Output word flags mark the FIRST
  and LAST cipher rune of each word (a null at slot 0 carries the start flag, a null at slot L the end flag).  One call = one
  section: no anti-repeat check at its first cipher rune (prev = None), nothing carries over.  n_cipher cuts the output after
  that many cipher runes (a word may be cut; its end flag is then not set).

Entry point: encrypt_r4(plain_words, key, rng, *, q=0.81, repair='T', lag=6, T=T_MAP, nu=0.45, slots='any', nulls_per_word=(1.0,),
    min_word=2, null_check='left', null_visible=True, lag_basis='cipher', channel='hold', sign=+1, key_start=0, n_cipher=None)
rng: random.Random or numpy Generator.  Returns R4Result (numpy arrays over the cipher runes):
    cipher, word_start, word_end, is_null, is_repair, repair_is_T, key_index (-1 for a null; for a repair the pointer whose key
    collided), plain_index (-1 for a null; for a repair the lost plaintext rune), word_id (index in plain_words), word_pos
    (cipher position in its word), null_slot (slot s of a null, else -1); scalars plain_consumed (plaintext runes used, nulls
    excluded), key_end (final pointer); and `plaintext` (the flat plaintext) for invert().
"""
from dataclasses import dataclass

import numpy as np

N = 29


def T_MAP(c):
    """the T relation of R4: c' = 24 - 2c (mod 29)"""
    return (24 - 2 * c) % N


class _Rng:
    """adapter: .rand() in [0,1), .below(n) uniform on 0..n-1, for random.Random and numpy Generators"""

    def __init__(self, rng):
        if hasattr(rng, 'randrange'):
            self.rand = rng.random
            self.below = lambda n: rng.randrange(n)
        else:
            self.rand = lambda: float(rng.random())
            self.below = lambda n: int(rng.integers(n))


@dataclass
class R4Result:
    cipher: np.ndarray
    word_start: np.ndarray
    word_end: np.ndarray
    is_null: np.ndarray
    is_repair: np.ndarray
    repair_is_T: np.ndarray
    key_index: np.ndarray
    plain_index: np.ndarray
    word_id: np.ndarray
    word_pos: np.ndarray
    null_slot: np.ndarray
    plaintext: np.ndarray
    plain_consumed: int
    key_end: int

    def __len__(self):
        return len(self.cipher)


def words_from_lengths(lengths, rng):
    """plain words of the given lengths with uniform random runes (for tests; real plaintext is the caller's)"""
    r = _Rng(rng)
    return [[r.below(N) for _ in range(L)] for L in lengths]


def invert(res, key, sign=1):
    """decrypt every real cipher rune with its recorded key index: plaintext runes in cipher order (nulls dropped) and the
    mask of repaired positions (where the result is not the plaintext).  Pure function of the cipher, key and ground truth."""
    real = ~res.is_null
    ki = res.key_index[real]
    return (res.cipher[real] - sign * np.asarray(key)[ki]) % N, res.is_repair[real]


def encrypt_r4(plain_words, key, rng, *, q=0.81, repair='T', lag=6, T=T_MAP, nu=0.45, slots='any', nulls_per_word=(1.0,),
               min_word=2, null_check='left', null_visible=True, lag_basis='cipher', channel='hold', sign=1, key_start=0,
               n_cipher=None):
    """Encrypt plain_words with the R4 mechanism; see the module docstring for every semantic."""
    if repair not in ('T', 'uniform'):
        raise ValueError('repair')
    if slots not in ('any', 'interior', 'edge', 'start', 'end'):
        raise ValueError('slots')
    if null_check not in ('none', 'left', 'both'):
        raise ValueError('null_check')
    if lag_basis not in ('cipher', 'real'):
        raise ValueError('lag_basis')
    if channel not in ('hold', 'spend'):
        raise ValueError('channel')
    if sign not in (1, -1):
        raise ValueError('sign')
    if slots == 'interior' and min_word < 2:
        raise ValueError("slots='interior' needs min_word >= 2")
    if abs(sum(nulls_per_word) - 1.0) > 1e-9:
        raise ValueError('nulls_per_word must sum to 1')
    R = _Rng(rng)
    words = [list(w) for w in plain_words]
    key = np.asarray(key)
    out, isnull, isrep, repT, kidx, pidx, wid, wpos, nslot, wst, wen, realv = [], [], [], [], [], [], [], [], [], [], [], []
    st = dict(j=key_start, pi=0, lastreal=None, done=False)
    plain = []

    def draw_slot(L):
        if slots == 'any':
            return R.below(L + 1)
        if slots == 'interior':
            return 1 + R.below(L - 1)
        if slots == 'edge':
            return 0 if R.rand() < 0.5 else L
        return 0 if slots == 'start' else L

    def uniform_excl(excl):
        while True:
            v = R.below(N)
            if v not in excl:
                return v

    def append(x, null, wi, w0, first, slot=-1, rep=False, rT=False, k=-1, pi=-1):
        out.append(int(x)); isnull.append(null); isrep.append(rep); repT.append(rT); kidx.append(k); pidx.append(pi)
        wid.append(wi); wpos.append(len(out) - 1 - w0); nslot.append(slot); wst.append(first); wen.append(False)
        if not null:
            st['lastreal'] = int(x)
            realv.append(int(x))
        if n_cipher is not None and len(out) >= n_cipher:
            st['done'] = True

    def fix_right(m):
        """null_check 'both': the null at m-1 must differ from the rune just appended at m (redraw it in place)"""
        if null_check == 'both' and m >= 1 and isnull[m - 1] and out[m - 1] == out[m]:
            excl = {out[m]}
            if m >= 2:
                excl.add(out[m - 2])
            out[m - 1] = uniform_excl(excl)

    nw = len(words)
    for wi, w in enumerate(words):
        L = len(w)
        if L == 0 or st['done']:
            continue
        sched = []
        if L >= min_word and R.rand() < nu:
            u, k, acc = R.rand(), len(nulls_per_word), 0.0
            for i, pr in enumerate(nulls_per_word):
                acc += pr
                if u < acc:
                    k = i + 1
                    break
            sched = sorted(draw_slot(L) for _ in range(k))
        w0, wreal = len(out), 0
        sp = 0                                     # next scheduled null
        for s in range(L + 1):
            while sp < len(sched) and sched[sp] == s and not st['done']:
                sp += 1
                left = out[-1] if out else None
                excl = set()
                if null_check in ('left', 'both') and left is not None:
                    excl.add(out[-1])
                if null_check == 'both':
                    nxt = None
                    if s < L and not (sp < len(sched) and sched[sp] == s):
                        nxt = w[s]
                    elif s == L and sp >= len(sched):
                        for w2 in words[wi + 1:]:
                            if len(w2):
                                nxt = w2[0]
                                break
                    if nxt is not None and st['j'] < len(key):
                        excl.add((nxt + sign * int(key[st['j']])) % N)
                m = len(out)
                append(uniform_excl(excl), True, wi, w0, m == w0, slot=s)
                fix_right(m) if m else None
            if st['done']:
                break
            if s == L:
                break
            j = st['j']
            if j >= len(key):
                raise IndexError('key exhausted at pointer %d' % j)
            p = int(w[s])
            plain.append(p)
            x = (p + sign * int(key[j])) % N
            prev = out[-1] if (null_visible and out) else (st['lastreal'] if not null_visible else None)
            rep = rT = False
            if prev is not None and x == prev and R.rand() < q:
                rep = True
                src = None
                if repair == 'T':
                    if lag_basis == 'cipher':
                        if len(out) - w0 >= lag:
                            src = out[-lag]
                    elif wreal >= lag:
                        src = realv[-lag]
                    if src is not None:
                        tv = T(src)
                        if tv != prev:
                            x, rT = tv, True
                if not rT:
                    r = R.below(N - 1)
                    x = r + 1 if r >= prev else r
                st['j'] = j + (1 if channel == 'spend' else 0)
            else:
                st['j'] = j + 1
            m = len(out)
            append(x, False, wi, w0, m == w0, rep=rep, rT=rT, k=j, pi=st['pi'])
            st['pi'] += 1
            wreal += 1
            fix_right(m) if m else None
            if st['done']:
                break
        if not st['done'] and out and wid[-1] == wi:
            wen[-1] = True
    # the flat plaintext index of every real rune is its position in `plain`
    return R4Result(cipher=np.array(out, np.int16), word_start=np.array(wst, bool), word_end=np.array(wen, bool),
                    is_null=np.array(isnull, bool), is_repair=np.array(isrep, bool), repair_is_T=np.array(repT, bool),
                    key_index=np.array(kidx, np.int64), plain_index=np.array(pidx, np.int64), word_id=np.array(wid, np.int64),
                    word_pos=np.array(wpos, np.int64), null_slot=np.array(nslot, np.int64), plaintext=np.array(plain, np.int16),
                    plain_consumed=st['pi'], key_end=st['j'])
