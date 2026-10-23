"""Tests of work/r4fix/r4sim.py (session s07 of the R4 repair work).  Nothing here touches LP2 ciphertext.

    python -B work/r4fix/test_r4sim.py -v

Tests 4 and 5 import work/phase57_mechanism.py and work/phase57_pilot.py READ-ONLY (the latter with a recording `random` shim
patched in only for the duration of the call) and compare distributions; the numbers are printed with the [r4sim] prefix.
"""
import math
import os
import random
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, os.path.join(WORK, 'families'))
sys.path.insert(0, os.path.join(WORK, 'mech25'))
import r4sim as S  # noqa: E402

N = 29
Z_MAX = 3.0          # agreement tolerance in standard errors (tests 4, 5, 7)
CHI_Z_MAX = 3.5      # chi-square tests: Wilson-Hilferty z


def say(*a):
    print('[r4sim]', *a, flush=True)


def chi2_z(stat, dof):
    """Wilson-Hilferty normal score of a chi-square statistic (dof >= 1)"""
    return ((stat / dof) ** (1 / 3) - (1 - 2 / (9 * dof))) / math.sqrt(2 / (9 * dof))


def chi2_uniform(counts, cells):
    """chi-square of counts against uniform over the given cells; counts outside the cells make it infinite"""
    tot = sum(counts.values())
    if any(c not in cells for c in counts):
        return float('inf'), len(cells) - 1
    e = tot / len(cells)
    return sum((counts.get(c, 0) - e) ** 2 / e for c in cells), len(cells) - 1


def iid_key(rng, n):
    return [rng.randrange(N) for _ in range(n)]


def doublets(c):
    c = np.asarray(c)
    return int((c[1:] == c[:-1]).sum())


def two_sample_z(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    return (a.mean() - b.mean()) / se if se > 0 else 0.0


class T0_Corpora(unittest.TestCase):
    def test_corpora_present(self):
        _check_corpora()
        import fam_data as D
        P, ST = D.english(150_000)
        say('T0 corpora ok: english() gives %d runes, %d words (Emerson alone: 307,290 / 74,880)' % (len(P), int(ST.sum())))
        self.assertGreaterEqual(int(ST.sum()), 150_000)


class T1_NoDoublets(unittest.TestCase):
    def test_q1_no_nulls(self):
        rng = random.Random(11)
        lengths = [rng.randint(1, 10) for _ in range(6000)]
        for repair in ('T', 'uniform'):
            for channel in ('hold', 'spend'):
                for vis in (True, False):
                    words = S.words_from_lengths(lengths, rng)
                    res = S.encrypt_r4(words, iid_key(rng, 21000), rng, q=1.0, repair=repair, nu=0.0, channel=channel,
                                       null_visible=vis, n_cipher=20000)
                    self.assertEqual(len(res), 20000)
                    self.assertEqual(doublets(res.cipher), 0, (repair, channel, vis))
        # control: with q = 0 the doublet rate is 1/29 (20,000 runes: 690 +- 26)
        res = S.encrypt_r4(S.words_from_lengths(lengths, rng), iid_key(rng, 21000), rng, q=0.0, nu=0.0, n_cipher=20000)
        d = doublets(res.cipher)
        say('T1 q=1 no nulls: 0 doublets in 8 x 20,000 runes; control q=0: %d doublets (expect %.0f +- %.0f)' % (d, 19999 / 29, math.sqrt(19999 / 29 * 28 / 29)))
        self.assertLess(abs(d - 19999 / 29), 4 * math.sqrt(19999 / 29 * 28 / 29))

    def test_q1_with_nulls(self):
        """checked + visible nulls at q 1 also leave zero doublets; an invisible or unchecked null leaves residual ones (phase 47 B)"""
        rng = random.Random(12)
        lengths = [rng.randint(2, 10) for _ in range(5000)]
        out = {}
        for vis, chk in ((True, 'left'), (True, 'both'), (False, 'left'), (True, 'none'), (False, 'none')):
            res = S.encrypt_r4(S.words_from_lengths(lengths, rng), iid_key(rng, 21000), rng, q=1.0, nu=0.45, null_check=chk,
                               null_visible=vis, n_cipher=20000)
            out[(vis, chk)] = doublets(res.cipher)
        say('T1b q=1 with nulls (nu .45): doublets by (visible, check) =', out)
        self.assertEqual(out[(True, 'left')], 0)
        self.assertEqual(out[(True, 'both')], 0)
        self.assertGreater(out[(False, 'left')], 20)       # invisible null: the next rune may repeat it
        self.assertGreater(out[(True, 'none')], 20)        # unchecked null may repeat its left neighbour
        self.assertGreater(out[(False, 'none')], 20)


class T2_Slots(unittest.TestCase):
    LENS = (2, 3, 5, 8)
    NW = 6000

    def slots_by_len(self, mode, seed, L):
        rng = random.Random(seed * 100 + L)
        words = [[0] * L for _ in range(self.NW)]
        res = S.encrypt_r4(words, iid_key(rng, self.NW * L + 5), rng, nu=1.0, slots=mode, q=0.0)
        self.assertEqual(int(res.is_null.sum()), self.NW)              # nu 1: exactly one null per word
        nz = res.is_null
        self.assertTrue(np.array_equal(res.word_pos[nz], res.null_slot[nz]))   # one null: cipher position in word == slot
        cnt = {}
        for s in res.null_slot[nz]:
            cnt[int(s)] = cnt.get(int(s), 0) + 1
        return cnt

    def test_histograms(self):
        cells = {'any': lambda L: range(0, L + 1), 'interior': lambda L: range(1, L), 'edge': lambda L: (0, L),
                 'start': lambda L: (0,), 'end': lambda L: tuple([L])}
        rows = []
        for mi, mode in enumerate(cells):
            for L in self.LENS:
                cnt = self.slots_by_len(mode, mi + 1, L)
                cs = list(cells[mode](L))
                if len(cs) == 1:
                    self.assertEqual(cnt, {cs[0]: self.NW}, (mode, L))
                    continue
                stat, dof = chi2_uniform(cnt, cs)
                z = chi2_z(stat, dof)
                rows.append((mode, L, round(stat, 1), dof, round(z, 2)))
                self.assertLess(z, CHI_Z_MAX, (mode, L, cnt))
        say('T2 slot chi-square (mode, L, chi2, dof, WH z):', rows)

    def test_detector_has_power(self):
        """positive control: 'any' slots tested against the interior rule fail at once; 'interior' against 'any' fails too"""
        cnt = self.slots_by_len('any', 9, 5)
        stat, _ = chi2_uniform(cnt, list(range(1, 5)))
        self.assertEqual(stat, float('inf'))                   # slots 0 and L occur, the interior rule forbids them
        cnt = self.slots_by_len('interior', 9, 5)
        stat, dof = chi2_uniform(cnt, list(range(0, 6)))
        self.assertGreater(chi2_z(stat, dof), 20)
        # a biased sampler: a 15% excess at slot 0 (L = 5, 6000 words) must be caught
        stat, dof = chi2_uniform({s: int(c * (1.15 if s == 0 else 1.0)) for s, c in self.slots_by_len('any', 7, 5).items()}, list(range(0, 6)))
        say('T2 power: 15%% excess at slot 0 gives WH z %.1f' % chi2_z(stat, dof))
        self.assertGreater(chi2_z(stat, dof), CHI_Z_MAX)

    def test_rates_and_counts(self):
        rng = random.Random(21)
        lengths = [rng.randint(1, 9) for _ in range(40000)]
        words = S.words_from_lengths(lengths, rng)
        res = S.encrypt_r4(words, iid_key(rng, sum(lengths) + 5), rng, nu=0.45, nulls_per_word=(0.7, 0.3), q=0.0)
        multi = sum(1 for L in lengths if L >= 2)
        nulls_by_word = np.bincount(res.word_id[res.is_null], minlength=len(words))
        with_null = int((nulls_by_word > 0).sum())
        self.assertEqual(int(nulls_by_word[[i for i, L in enumerate(lengths) if L < 2]].sum()), 0)   # one-rune words never get one
        p = with_null / multi
        se = math.sqrt(0.45 * 0.55 / multi)
        two = int((nulls_by_word == 2).sum())
        p2 = two / with_null
        se2 = math.sqrt(0.3 * 0.7 / with_null)
        say('T2 rates: words with a null %.4f of %d multi-rune words (target 0.45 +- %.4f); two-null share %.4f (target 0.30 +- %.4f)' % (p, multi, se, p2, se2))
        self.assertLess(abs(p - 0.45), 3.5 * se)
        self.assertLess(abs(p2 - 0.30), 3.5 * se2)
        self.assertEqual(int((nulls_by_word > 2).sum()), 0)


class T3_NullCheck(unittest.TestCase):
    def build(self, chk, vis, seed):
        rng = random.Random(seed)
        lengths = [rng.randint(2, 9) for _ in range(6000)]
        words = S.words_from_lengths(lengths, rng)
        return S.encrypt_r4(words, iid_key(rng, sum(lengths) + 5), rng, q=0.81, nu=0.9, nulls_per_word=(0.5, 0.5), slots='any',
                            null_check=chk, null_visible=vis)

    def counts(self, res):
        c, nl = res.cipher.astype(int), np.flatnonzero(res.is_null)
        left = int(sum(c[i] == c[i - 1] for i in nl if i > 0))
        right = int(sum(c[i] == c[i + 1] for i in nl if i + 1 < len(c)))
        return left, right, len(nl)

    def test_left_and_both(self):
        rows = {}
        for vis in (True, False):
            for chk in ('none', 'left', 'both'):
                left, right, nn = self.counts(self.build(chk, vis, 31))
                rows[(vis, chk)] = (left, right, nn)
                if chk == 'left':
                    self.assertEqual(left, 0, (vis, chk))
                if chk == 'both':
                    self.assertEqual((left, right), (0, 0), (vis, chk))
        say('T3 (null_visible, null_check): (null==left, null==right, nulls) =', rows)
        for vis in (True, False):                   # controls: without the check, equalities occur at about 1/29
            nn = rows[(vis, 'none')][2]
            self.assertGreater(rows[(vis, 'none')][0], 0.5 * nn / 29)
            self.assertGreater(rows[(vis, 'none')][1], 0.5 * nn / 29 * (0.19 if vis else 1.0))
            self.assertGreater(rows[(vis, 'left')][1], 0)          # 'left' does not check the right neighbour


def _check_corpora():
    """fam_data.english silently falls back to the corpora that exist (Emerson only gives r 0.399 instead of 0.448 in phase 57): fail loudly"""
    import fam_data as D
    missing = [f for f in D.CORPORA if not os.path.exists(os.path.join(WORK, 'ref', f))]
    if missing:
        raise AssertionError('corpora missing in work/ref (%s): phase 57 comparisons would silently use fewer texts' % ', '.join(missing))


def _phase57_ctx():
    _check_corpora()
    import fam_data as D
    c, ws, sid = D.lp2()
    P, ST = D.english(150_000)
    nxt = np.zeros(len(ST), int)
    last = len(ST) - 1
    for j in range(len(ST) - 1, -1, -1):
        last = j if ST[j] else last
        nxt[j] = last
    s = np.flatnonzero(ST)
    WL = np.zeros(len(ST), int)
    WL[s] = np.diff(np.append(s, len(ST)))
    return (P.astype(np.int16), nxt, WL, sid), s, len(c), (c, ws)


class T4_Phase57(unittest.TestCase):
    REPS = 100
    RATE = 0.448

    def test_agreement_with_phase57_R4(self):
        import phase57_mechanism as M57
        ctx, starts, n, _ = _phase57_ctx()
        P, nxt, WL, sid = ctx
        secs = [int((sid == k).sum()) for k in range(sid.max() + 1)]
        C, WS = M57.simulate(self.REPS, np.random.default_rng(5), ctx, q=0.81, rep='T', ins='word', check=True, rate=self.RATE)
        ref = [M57.measure(C[r].astype(np.int16), WS[r], sid) for r in range(self.REPS)]

        def mine(channel, seed, reps):
            rows = []
            for r in range(reps):
                rng = random.Random(seed + r)
                nprng = np.random.default_rng(seed + r)
                J = rng.randrange(len(P) - n - 5000)
                cs, wss = [], []
                for L in secs:
                    J = int(nxt[J])
                    i0 = int(np.searchsorted(starts, J))
                    words, tot, k = [], 0, 0
                    while tot < L + 30:
                        a, b = int(starts[i0 + k]), int(starts[i0 + k + 1])
                        words.append(P[a:b].tolist()); tot += b - a; k += 1
                    res = S.encrypt_r4(words, nprng.integers(0, N, L + 60), rng, q=0.81, repair='T', nu=self.RATE, slots='any',
                                       null_check='left', null_visible=True, lag_basis='cipher', channel=channel, n_cipher=L)
                    assert len(res) == L
                    cs.append(res.cipher); wss.append(res.word_start)
                    J += res.plain_consumed
                rows.append(M57.measure(np.concatenate(cs).astype(np.int16), np.concatenate(wss), sid))
            return rows

        out = {}
        for channel in ('spend', 'hold'):
            rows = mine(channel, 1000 if channel == 'spend' else 5000, self.REPS if channel == 'spend' else 40)   # hold: 40 replicates (time budget), report only
            zs = {}
            for k in ('din', 'dgap', 't6', 'nw'):
                a, b = [r[k] for r in ref], [r[k] for r in rows]
                zs[k] = (round(float(np.mean(a)), 2), round(float(np.mean(b)), 2), round(float(two_sample_z(a, b)), 2))
            out[channel] = zs
        say('T4 phase57 R4 (mean phase57, mean r4sim, z) over %d replicates (hold: 40), rate %.3f:' % (self.REPS, self.RATE))
        for channel, zs in out.items():
            say('   channel', channel, zs)
        for k, (_, _, z) in out['spend'].items():       # phase 57 draws a fresh key at every step = 'spend' with an iid key
            self.assertLess(abs(z), Z_MAX, (k, out['spend']))
        # hold with an iid key reuses the key that collided: reported, only a looser sanity bound
        for k, (_, _, z) in out['hold'].items():
            self.assertLess(abs(z), 4.0, (k, out['hold']))


class _CList(list):
    """a word-length list that counts how many multi-rune words make_r4 reads"""

    def __init__(self, *a):
        super().__init__(*a)
        self.reads = self.multi = 0

    def __getitem__(self, i):
        v = super().__getitem__(i)
        if isinstance(i, int):
            self.reads += 1
            self.multi += int(v >= 2)
        return v


class _RecRandom(random.Random):
    """random.Random that logs every two-argument randrange (in make_r4 only the interior null slot: randrange(1, L))"""
    log = []

    def randrange(self, a, b=None, *args):
        if b is None:
            return super().randrange(a)
        v = super().randrange(a, b)
        _RecRandom.log.append((a, b, v))
        return v


class _Shim:
    Random = _RecRandom


class T5_Pilot(unittest.TestCase):
    NPLANT = 400

    def test_agreement_with_make_r4(self):
        import phase57_pilot as PP
        _, _, _, (c, ws) = _phase57_ctx()
        st = np.flatnonzero(ws)
        lens = np.diff(np.append(st, len(c))).tolist()          # LP2 cipher word lengths as a realistic length supply
        shared = _CList(lens)
        words_by_sec = {s: shared for s in PP.P.SECS}
        grng = random.Random(77)
        pool = [grng.randrange(N) for _ in range(6000)]
        lib = [('synthetic', [grng.randrange(N) for _ in range(4000)])]
        _RecRandom.log = []
        old = PP.random
        PP.random = _Shim
        try:
            plants = [PP.make_r4(('m04', 'spend')[i % 2], 'cicada', i, pool, words_by_sec, lib, 0.81) for i in range(self.NPLANT)]
        finally:
            PP.random = old
        log = list(_RecRandom.log)
        # pilot side: slot histogram by word length, null rate per multi-rune word, window stats
        hist_p = {}
        for a, L, v in log:
            self.assertEqual(a, 1)
            hist_p.setdefault(L, {}).setdefault(v, 0)
            hist_p[L][v] += 1
        rate_p = len(log) / shared.multi
        nulls_p = [p['nulls_in_window'] for p in plants]
        dbl_p = [doublets(p['cipher']) for p in plants]
        # r4sim side, interior mode, same word-length supply, same windows (first non-null at >= e0, 300 runes)
        rng = random.Random(78)
        nprng = np.random.default_rng(78)
        hist_s, multi_s, nul_s, nulls_s, dbl_s = {}, 0, 0, [], []
        for i in range(self.NPLANT * 2):
            w0 = rng.randrange(len(lens) - 150)
            wl = lens[w0:w0 + 150]
            words = S.words_from_lengths(wl, rng)
            res = S.encrypt_r4(words, nprng.integers(0, N, sum(wl) + 5), rng, q=0.81, repair='T', nu=0.45, slots='interior',
                               null_check='left', null_visible=True, lag_basis='cipher', channel=('hold', 'spend')[i % 2])
            m = res.is_null
            multi_s += sum(1 for L in wl if L >= 2)
            nul_s += int(m.sum())
            for wi in np.flatnonzero(m):
                L = wl[res.word_id[wi]]
                hist_s.setdefault(L, {}).setdefault(int(res.null_slot[wi]), 0)
                hist_s[L][int(res.null_slot[wi])] += 1
            e = rng.randrange(100)
            while m[e]:
                e += 1
            sl = slice(e, e + 300)
            nulls_s.append(int(m[sl].sum())); dbl_s.append(doublets(res.cipher[sl]))
        # both histograms are keyed by the plaintext length L (make_r4 draws randrange(1, L))
        rate_s = nul_s / multi_s
        se_p = math.sqrt(0.45 * 0.55 / shared.multi)
        say('T5 null rate per multi-rune word: pilot %.4f (%d draws / %d words, target 0.45 +- %.4f), r4sim %.4f (%d / %d)'
            % (rate_p, len(log), shared.multi, se_p, rate_s, nul_s, multi_s))
        self.assertLess(abs(rate_p - 0.45), Z_MAX * se_p)
        se_s = math.sqrt(0.45 * 0.55 / multi_s)
        self.assertLess(abs(rate_s - 0.45), Z_MAX * se_s)
        self.assertLess(abs(rate_p - rate_s), Z_MAX * math.sqrt(se_p ** 2 + se_s ** 2))
        # slot histograms: every draw interior, uniform in each, and the two samples homogeneous
        rows, tot_chi, tot_dof = [], 0.0, 0
        for Lc in sorted(set(hist_p) & set(hist_s)):
            cells = list(range(1, Lc))
            self.assertTrue(set(hist_p[Lc]) <= set(cells) and set(hist_s[Lc]) <= set(cells), Lc)
            if Lc == 2:
                continue
            a = np.array([hist_p[Lc].get(s, 0) for s in cells], float)
            b = np.array([hist_s[Lc].get(s, 0) for s in cells], float)
            if min(a.sum(), b.sum()) < 20 * len(cells):
                continue
            for h in (a, b):
                stat, dof = chi2_uniform({s: h[k] for k, s in enumerate(cells)}, cells)
                self.assertLess(chi2_z(stat, dof), CHI_Z_MAX, (Lc, h))
            tot = a + b
            ea, eb = tot * a.sum() / tot.sum(), tot * b.sum() / tot.sum()
            chi = float(((a - ea) ** 2 / ea).sum() + ((b - eb) ** 2 / eb).sum())
            tot_chi += chi; tot_dof += len(cells) - 1
            rows.append((Lc, int(a.sum()), int(b.sum()), round(chi, 1), len(cells) - 1))
        zt = chi2_z(tot_chi, tot_dof)
        say('T5 slot histograms, plaintext length L: (L, pilot n, r4sim n, homogeneity chi2, dof) =', rows, ' total chi2 %.1f dof %d WH z %.2f' % (tot_chi, tot_dof, zt))
        self.assertLess(zt, CHI_Z_MAX)
        zn, zd = two_sample_z(nulls_p, nulls_s), two_sample_z(dbl_p, dbl_s)
        say('T5 300-rune windows: nulls pilot %.2f vs r4sim %.2f (z %.2f); doublets pilot %.3f vs r4sim %.3f (z %.2f); %d vs %d windows'
            % (np.mean(nulls_p), np.mean(nulls_s), zn, np.mean(dbl_p), np.mean(dbl_s), zd, len(nulls_p), len(nulls_s)))
        self.assertLess(abs(zn), Z_MAX)
        self.assertLess(abs(zd), Z_MAX)


class T6_GroundTruth(unittest.TestCase):
    CONFIGS = [dict(channel=c, sign=s, null_visible=v, lag_basis=lb, repair=rp, slots=sl, null_check=nc, nulls_per_word=npw)
               for c, s, v, lb, rp, sl, nc, npw in [
                   ('hold', 1, True, 'cipher', 'T', 'any', 'left', (1.0,)), ('spend', -1, True, 'cipher', 'T', 'interior', 'both', (0.6, 0.4)),
                   ('hold', -1, False, 'real', 'T', 'any', 'none', (1.0,)), ('spend', 1, False, 'real', 'uniform', 'edge', 'left', (0.5, 0.5)),
                   ('hold', 1, True, 'real', 'T', 'end', 'both', (1.0,)), ('spend', 1, False, 'cipher', 'T', 'start', 'none', (1.0,))]]

    def test_inversion(self):
        for ci, cfg in enumerate(self.CONFIGS):
            rng = random.Random(500 + ci)
            lengths = [rng.randint(1, 11) for _ in range(3000)]
            words = S.words_from_lengths(lengths, rng)
            key = np.array(iid_key(rng, sum(lengths) + 5))
            res = S.encrypt_r4(words, key, rng, q=0.81, nu=0.5, lag=6, **cfg)
            sign = cfg['sign']
            flat = np.array([p for w in words for p in w], np.int16)
            # (a) the recorded plaintext is the flat plaintext prefix, one rune per non-null cipher rune
            self.assertEqual(res.plain_consumed, int((~res.is_null).sum()))
            self.assertTrue(np.array_equal(res.plaintext, flat[:res.plain_consumed]))
            self.assertTrue(np.array_equal(res.plain_index[~res.is_null], np.arange(res.plain_consumed)))
            self.assertTrue(np.all(res.plain_index[res.is_null] == -1) and np.all(res.key_index[res.is_null] == -1))
            # (b) removing the nulls and inverting with the key recovers the plaintext except at repair positions
            dec, rep = S.invert(res, key, sign)
            self.assertTrue(np.array_equal(dec[~rep], flat[:res.plain_consumed][~rep]))
            self.assertGreater(rep.sum(), 50)
            # (c) key pointer accounting: hold -> a repair does not advance; spend -> it does; a null never does
            kr = res.key_index[~res.is_null]
            adv = np.diff(kr)
            steps = np.where(rep[:-1], 0 if cfg['channel'] == 'hold' else 1, 1)
            self.assertTrue(np.array_equal(adv, steps))
            self.assertEqual(res.key_end - 0, int(kr[-1]) + (1 if (cfg['channel'] == 'spend' or not rep[-1]) else 0))
            # (d) T repairs write T(c[-6]) of the right stream and sit at word position >= 6 (cipher basis) ; others differ from prev
            c = res.cipher.astype(int)
            for i in np.flatnonzero(res.repair_is_T):
                self.assertTrue(res.is_repair[i])
                self.assertTrue(res.word_id[i - 6] == res.word_id[i] if cfg['lag_basis'] == 'cipher' else True)
                if cfg['lag_basis'] == 'cipher':
                    self.assertGreaterEqual(res.word_pos[i], 6)
                    self.assertEqual(c[i], (24 - 2 * c[i - 6]) % N)
                else:
                    real = np.flatnonzero(~res.is_null[:i])
                    self.assertEqual(c[i], (24 - 2 * c[real[-6]]) % N)
                    self.assertEqual(res.word_id[real[-6]], res.word_id[i])
            # (e) word flags: starts and ends bracket every complete word; null slots only where the mode allows
            self.assertEqual(int(res.word_start.sum()), len(set(res.word_id.tolist())))
            nl = np.flatnonzero(res.is_null)
            L_of = np.array([len(w) for w in words])[res.word_id[nl]] if len(nl) else np.array([])
            sl = res.null_slot[nl]
            mode = cfg['slots']
            ok = {'any': (sl >= 0) & (sl <= L_of), 'interior': (sl >= 1) & (sl <= L_of - 1), 'edge': (sl == 0) | (sl == L_of),
                  'start': sl == 0, 'end': sl == L_of}[mode]
            self.assertTrue(ok.all(), mode)
            self.assertTrue(np.all(L_of >= 2))
        say('T6 ground truth: inversion, key accounting, T-repair values, word flags and slot ranges hold for %d configurations' % len(self.CONFIGS))

    def test_determinism(self):
        rng1, rng2 = random.Random(9), random.Random(9)
        w = S.words_from_lengths([4, 5, 6, 3, 8] * 200, random.Random(1))
        k = iid_key(random.Random(2), 6000)
        a = S.encrypt_r4(w, k, rng1)
        b = S.encrypt_r4(w, k, rng2)
        self.assertTrue(np.array_equal(a.cipher, b.cipher))
        a = S.encrypt_r4(w, np.array(k), np.random.default_rng(3))      # numpy generator accepted
        self.assertGreater(len(a), 3000)


class T7_PlantEdgeStep(unittest.TestCase):
    """extra: r4sim with no nulls and a uniform repair equals the m04 / spend encryptor of plant_edge.step (the plants' step)"""
    REPS = 100

    def test_step(self):
        import phase57_pilot as PP
        E = PP.P                                               # plant_edge, read-only
        out = {}
        for ch, channel in (('m04', 'hold'), ('spend', 'spend')):
            d_ref, j_ref, d_s, j_s = [], [], [], []
            for r in range(self.REPS):
                rng = random.Random(900 + r)
                n = 2500
                plain = [rng.randrange(N) for _ in range(n)]
                key = iid_key(rng, n + 5)
                j, ell, c = 0, None, []
                for p in plain:
                    x, u, j = E.step(ch, p, key, j, ell, 1, 0.81, rng)
                    c.append(x); ell = x
                d_ref.append(doublets(c)); j_ref.append(j)
                rng2 = random.Random(1900 + r)
                res = S.encrypt_r4([plain], key, rng2, q=0.81, repair='uniform', nu=0.0, channel=channel, null_visible=False)
                d_s.append(doublets(res.cipher)); j_s.append(res.key_end)
            out[ch] = (round(np.mean(d_ref), 2), round(np.mean(d_s), 2), round(two_sample_z(d_ref, d_s), 2),
                       round(np.mean(j_ref), 1), round(np.mean(j_s), 1), round(two_sample_z(j_ref, j_s), 2))
            self.assertLess(abs(out[ch][2]), Z_MAX)
            self.assertLess(abs(out[ch][5]), Z_MAX)
        say('T7 plant_edge.step vs r4sim (mean doublets ref/sim/z; mean key pointer ref/sim/z):', out)


if __name__ == '__main__':
    unittest.main(verbosity=2)
