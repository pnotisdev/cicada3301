"""Gate runner: immutable artifacts, no held-out work here."""
import os
for name in ('OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'NUMEXPR_NUM_THREADS'):
    os.environ[name] = '1'
import hashlib
import itertools as it
import json
import math
from fractions import Fraction as F
from pathlib import Path
import sys
import time
import numpy as np
from reference import rational_forward, event_tree, forward, score

HERE = Path(__file__).resolve().parent
CHANNELS = ('hold', 'spend', 'skip', 'skip5', 'coin')


def tiny_cases():
    pi = [F(1,6), F(2,6), F(3,6)]
    L = [pi, [F(3,6), F(1,6), F(2,6)], [F(2,6), F(3,6), F(1,6)]]
    u = [F(1,3)]*3
    for m in range(4):
        for key in it.product(range(3), repeat=m):
            for off, sign, q, ch, model in it.product(range(m+1), (-1,1), (F(0),F(3,5),F(1)), CHANNELS, (0,1)):
                yield key, off, sign, q, ch, (pi if model else u), (L if model else [u]*3)


def g0():
    count, trees = 0, 0
    witnesses = {}
    mutations = {'hold_spends':'hold', 'coin_missing_slot':'coin',
                 'skip_drops_tail':'skip', 'replacement_denominator':'spend'}
    for key, off, sign, q, ch, pi, L in tiny_cases():
        for n in range(4):
            outputs, fail = event_tree(key, off, sign, q, ch, pi, L, n)
            assert sum(outputs.values()) + sum(fail.values()) == 1, ('normalization', key, ch, n)
            trees += 1
            for c in it.product(range(3), repeat=n):
                p = rational_forward(c, key, off, sign, q, ch, pi, L)
                assert p == outputs.get(c, F(0)), ('tree-DP', key, ch, c)
                count += 1
            for mutation, target in mutations.items():
                if ch == target and mutation not in witnesses:
                    bad = event_tree(key, off, sign, q, ch, pi, L, n, mutant=mutation)
                    if bad != (outputs, fail):
                        witnesses[mutation] = dict(key=key, off=off, sign=sign, q=str(q), n=n)
    assert set(witnesses) == set(mutations), ('uncaught mutations', witnesses)
    # Explicit long-run tail and skip5 cap beyond the exhaustive key bound.
    u = [F(1,3)]*3
    for ch in CHANNELS:
        key = (0,)*8
        outputs, fail = event_tree(key, 0, 1, F(3,5), ch, u, [u]*3, 2)
        assert sum(outputs.values()) + sum(fail.values()) == 1
        for c in it.product(range(3), repeat=2):
            assert rational_forward(c,key,0,1,F(3,5),ch,u,[u]*3) == outputs.get(c,0)
    return dict(status='PASS', exact_probability_comparisons=count,
                normalized_trees=trees, mutations=witnesses, extra_tail_cases=45)


def g1():
    # All tiny combinations at n=3: also tests every shorter prefix via their
    # corresponding stream-end cases; G0 itself covers all lengths explicitly.
    count, maxerr = 0, 0.0
    for key, off, sign, q, ch, pi, L in tiny_cases():
        outputs, _ = event_tree(key, off, sign, q, ch, pi, L, 3)
        fp, fl = np.array(pi,float), np.array(L,float)
        for c in it.product(range(3), repeat=3):
            logp = forward(c,key,off,sign,float(q),ch,fp,fl)
            exact = float(outputs.get(c,0))
            err = abs((math.exp(logp) if math.isfinite(logp) else 0) - exact)
            assert err <= 2e-13, ('probability',err)
            if exact:
                assert abs(logp-math.log(exact)) <= 2e-11
            else:
                assert logp == -math.inf
            maxerr = max(maxerr,err)
            count += 1
    rng = np.random.default_rng(1701)
    for idx in range(50):
        Q, n, m = 29, int(rng.integers(0,7)), int(rng.integers(0,10))
        key = rng.integers(Q,size=m).tolist()
        c = rng.integers(Q,size=n).tolist()
        off, sign = int(rng.integers(m+1)), (-1 if idx%2 else 1)
        q = (0., .81, 1.)[idx%3]
        pi = np.full(Q,1/Q); L = np.full((Q,Q),1/Q)
        ch = CHANNELS[idx%5]
        x = forward(c,key,off,sign,q,ch,pi,L)
        y = forward(c,key,off,sign,q,ch,pi,L)
        assert x.hex() == y.hex()
        exact = rational_forward(c,key,off,sign,F(str(q)),ch,[F(1,Q)]*Q,[[F(1,Q)]*Q]*Q)
        assert abs((math.exp(x) if math.isfinite(x) else 0)-float(exact)) < 2e-13
    return dict(status='PASS', tiny_comparisons=count, random_edge_cells=50,
                max_probability_error=maxerr, reproducibility='identical float.hex on repeated calls')


def main():
    gate = sys.argv[1]
    dest = HERE / (gate+'.json')
    if dest.exists():
        raise SystemExit('Refusing to overwrite existing gate artifact')
    if gate == 'g1' and json.loads((HERE/'g0.json').read_text())['status'] != 'PASS':
        raise SystemExit('G0 must pass first')
    start = time.perf_counter()
    try:
        res = {'g0':g0, 'g1':g1}[gate]()
    except Exception as exc:
        res = dict(status='FAIL', error=type(exc).__name__, detail=str(exc))
    res['elapsed_seconds'] = time.perf_counter()-start
    res['hashes'] = {p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
                     (HERE/'README.md', HERE/'reference.py', HERE/'gates.py', HERE/'channels.json')}
    dest.write_text(json.dumps(res,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(res,indent=2),flush=True)
    if res['status'] != 'PASS':
        raise SystemExit(1)

if __name__ == '__main__':
    main()
