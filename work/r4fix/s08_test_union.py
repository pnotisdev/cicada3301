"""Gates G1-G3 of the union null arc (R4 repair s08) and the cost probe; G4 (plants) lives in s08_power_union.py.

    python -B work/r4fix/s08_test_union.py            # G1, G2, G3  (no plants, no LP2 data)
    python -B work/r4fix/s08_test_union.py cost       # microseconds per offset, union vs mid, same input

G1  fast union engine vs the dense Fraction reference (s08_reference_union.py) on random small trials, four channels, both signs: worst |log error| < 1e-12.
G2  reductions: place 'interior' == the mid arc (backward_mid kind 3) and nu = 0 == the base engine, to 1e-12, on the real 29-rune model and random short windows.
G3  mutant witnesses: a null that consumes a key, a visible null, mid-arc weights, unnormalised weights each disagree with the engine on some cases.
"""
import json
import math
import random
import sys
import time
from fractions import Fraction as F
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
V2 = HERE.parent / 'chanscreen' / 'v2'
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(V2))
import numpy as np  # noqa: E402
from s08_engine_union import all_offsets_union  # noqa: E402
from s08_reference_union import all_offsets_ref  # noqa: E402
from engine_mid import all_offsets_mid  # noqa: E402
from engine import all_offsets  # noqa: E402
from test_edge import rmodel  # noqa: E402

TOL = 1e-12
ff = lambda x: [float(v) for v in x]
CHS = ('hold', 'spend', 'skip5', 'coin')


def case(rng, nmax, mmax, Qs=(3, 4), pws=(0.25, 0.5)):
    Q = rng.choice(Qs)
    n = rng.randint(1, nmax)
    m = rng.randint(1, mmax)
    c = [rng.randrange(Q) for _ in range(n)]
    for i in range(1, n):
        if rng.random() < .4:
            c[i] = c[i - 1]
    key = [rng.randrange(Q) for _ in range(m)]
    pw = rng.choice(pws)
    ws = [1] + [1 if rng.random() < pw else 0 for _ in range(n - 1)]
    return Q, n, m, c, key, ws


def lc_list(ws):
    st = [i for i, x in enumerate(ws) if x or i == 0]
    return [(b - a) for a, b in zip(st, st[1:] + [len(ws)])]


def compare(got, ref, tag):
    worst, nz = 0., 0
    for o, (zl, zu) in enumerate(ref):
        for col, z in ((0, zl), (1, zu)):
            g = got[o, col]
            if z == 0:
                if g != -math.inf:
                    raise AssertionError(f'support mismatch {tag} o={o} col={col} got={g}')
            else:
                nz += 1
                e = abs(g - math.log(z))
                worst = max(worst, e)
                if e > TOL:
                    raise AssertionError(f'{tag} o={o} col={col}: got {g!r} ref {math.log(z)!r} err {e}')
    return worst, nz


def g1(seed=7, trials=400, nmax=7, mmax=8, place='any', pws=(0.25, 0.5), Qs=(3, 4)):
    rng = random.Random(seed)
    worst, nz, byc, bys = 0., 0, {}, {1: 0, -1: 0}
    adj = null0 = lc1 = 0
    for t in range(trials):
        Q, n, m, c, key, ws = case(rng, nmax, mmax, Qs, pws)
        ch = CHS[t % 4]
        s = 1 if (t // 4) % 2 == 0 else -1
        q = rng.choice((F(0), F(3, 5), F(1), F(4, 5)))
        nu = rng.choice((F(0), F(2, 5), F(1), F(2, 5), F(1, 3)))
        pi, L = rmodel(rng, Q)
        ref = all_offsets_ref(c, key, s, q, ch, pi, L, ws, nu, place)
        got = all_offsets_union(c, key, s, float(q), ch, ff(pi), [ff(r) for r in L], float(nu), ws, place)
        w, k = compare(got, ref, f'G1 trial {t} {ch} s={s} q={q} nu={nu} place={place} c={c} key={key} ws={ws}')
        worst = max(worst, w)
        nz += k
        byc[ch] = byc.get(ch, 0) + 1
        bys[s] += 1
        lcs = lc_list(ws)
        adj += any(a >= 2 and b >= 2 for a, b in zip(lcs, lcs[1:]))
        null0 += lcs[0] >= 2
        lc1 += any(x == 1 for x in lcs)
    return dict(place=place, trials=trials, nonzero_cells=nz, worst_abs_err=worst, by_channel=byc, by_sign=bys,
                trials_with_adjacent_nullable_words=adj, trials_with_first_word_Lc_ge_2=null0, trials_with_a_one_rune_word=lc1)


def model29():
    m = np.load(V2.parent / 'model.npz')
    return m['pi'], m['L']


def g2(seed=21, trials=240, nmax=40, mmax=30):
    pi, L = model29()
    rng = random.Random(seed)
    worst_i = worst_0 = 0.
    ncell_i = ncell_0 = 0
    bysc = {}
    for t in range(trials):
        n = rng.randint(1, nmax)
        m = rng.randint(2, mmax)
        c = [rng.randrange(29) for _ in range(n)]
        for i in range(1, n):
            if rng.random() < .05:
                c[i] = c[i - 1]
        key = [rng.randrange(29) for _ in range(m)]
        pw = rng.choice((0.1, 0.25, 0.5))
        ws = [1] + [1 if rng.random() < pw else 0 for _ in range(n - 1)]
        ch = CHS[t % 4]
        s = 1 if (t // 4) % 2 == 0 else -1
        q = rng.choice((0.0, 0.6, 0.81, 1.0))
        nu = rng.choice((0.1, 0.42, 0.9))
        # (a) interior == mid arc (kind 3)
        a = all_offsets_union(c, key, s, q, ch, pi, L, nu, ws, 'interior')
        b = all_offsets_mid(c, key, s, q, ch, pi, L, 3, None, nu, ws)
        fin = np.isfinite(a) & np.isfinite(b)
        assert (np.isfinite(a) == np.isfinite(b)).all() and (a[~np.isfinite(a)] == b[~np.isfinite(b)]).all(), f'G2a support mismatch trial {t}'
        if fin.any():
            e = float(np.max(np.abs(a[fin] - b[fin])))
            worst_i = max(worst_i, e)
            ncell_i += int(fin.sum())
            assert e < TOL, f'G2a trial {t} {ch} s={s} q={q} nu={nu}: {e}'
        # (b) nu = 0 == base engine, for place any / interior / edge
        base = all_offsets(c, key, s, q, ch, pi, L)
        for place in ('any', 'interior', 'edge'):
            u0 = all_offsets_union(c, key, s, q, ch, pi, L, 0.0, ws, place)
            fin = np.isfinite(u0) & np.isfinite(base)
            assert (np.isfinite(u0) == np.isfinite(base)).all(), f'G2b support mismatch trial {t} {place}'
            if fin.any():
                e = float(np.max(np.abs(u0[fin] - base[fin])))
                worst_0 = max(worst_0, e)
                ncell_0 += int(fin.sum())
                assert e < TOL, f'G2b trial {t} {ch} s={s} q={q} place={place}: {e}'
        bysc[ch] = bysc.get(ch, 0) + 1
    return dict(trials=trials, interior_vs_mid_kind3=dict(finite_cells=ncell_i, worst_abs_diff=worst_i),
                nu0_vs_base_all_places=dict(finite_cells=ncell_0, worst_abs_diff=worst_0), by_channel=bysc)


def g3(seed=11, trials=250):
    rng = random.Random(seed)
    found = {m: 0 for m in ('null_visible', 'null_keyed', 'mid_weights', 'unnormalised')}
    for t in range(trials):
        Q, n, m, c, key, ws = case(rng, 6, 7, (3,))
        ch = CHS[t % 4]
        s = 1 if (t // 4) % 2 == 0 else -1
        q = F(4, 5)
        nu = F(2, 5)
        pi, L = rmodel(rng, Q)
        got = all_offsets_union(c, key, s, float(q), ch, ff(pi), [ff(r) for r in L], float(nu), ws, 'any')
        for mu in found:
            ref = all_offsets_ref(c, key, s, q, ch, pi, L, ws, nu, 'any', mutant=mu)
            for o, (zl, zu) in enumerate(ref):
                g = got[o, 0]
                if (zl == 0) != (g == -math.inf) or (zl != 0 and abs(g - math.log(zl)) > 1e-9):
                    found[mu] += 1
                    break
    return dict(trials=trials, witnesses=found)


def cost(n=300, m=20000, reps=1, seed=5):
    """process CPU time per offset per sign, summed over the four channels, union ('any'), interior-only union and mid arc, on the same random window"""
    pi, L = model29()
    rng = random.Random(seed)
    c = [rng.randrange(29) for _ in range(n)]
    key = [rng.randrange(29) for _ in range(m)]
    ws = [1] + [1 if rng.random() < 0.18 else 0 for _ in range(n - 1)]
    out = {}
    for name, fn in (('base', lambda ch: all_offsets(c, key, 1, .81, ch, pi, L)),
                     ('mid_kind3', lambda ch: all_offsets_mid(c, key, 1, .81, ch, pi, L, 3, None, .42, ws)),
                     ('union_interior', lambda ch: all_offsets_union(c, key, 1, .81, ch, pi, L, .42, ws, 'interior')),
                     ('union_any', lambda ch: all_offsets_union(c, key, 1, .81, ch, pi, L, .42, ws, 'any'))):
        per = {}
        for ch in CHS:
            t0 = time.process_time()
            for _ in range(reps):
                fn(ch)
            per[ch] = (time.process_time() - t0) / reps / m * 1e6
        out[name] = dict(us_per_offset_per_channel=per, us_per_offset_sum_4ch=sum(per.values()))
    out['ratio_union_any_over_mid'] = out['union_any']['us_per_offset_sum_4ch'] / out['mid_kind3']['us_per_offset_sum_4ch']
    out['n'], out['m'] = n, m
    return out


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'cost':
        r = cost()
        print(json.dumps(r, indent=1))
        sys.exit(0)
    t0 = time.process_time()
    res = {}
    res['G1_any'] = g1(7, 400, place='any')
    res['G1_any_dense_words'] = g1(10, 300, nmax=8, place='any', pws=(0.4, 0.5))   # words of 2-3 runes: runs of adjacent nulls, nulls at window start
    res['G1_any_Q6'] = g1(12, 80, nmax=6, mmax=6, place='any', Qs=(6,))
    res['G1_interior'] = g1(8, 200, place='interior')
    res['G1_edge'] = g1(9, 200, place='edge')
    res['G2'] = g2()
    res['G3'] = g3()
    res['cpu_seconds'] = time.process_time() - t0
    print(json.dumps(res, indent=1))
