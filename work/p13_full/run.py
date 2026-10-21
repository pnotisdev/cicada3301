"""Nulls and plants for the full pipeline. usage: python run.py MODEL START COUNT  (MODEL: real|perm|fresh|plant_full|plant_dil)"""
import sys, json, time, numpy as np, os
from multiprocessing import Pool
import pipe
paras, sec = pipe.load_paragraphs()
LENS = [len(x) for x in paras]; PL = 14            # the 308-rune paragraph (54+55.jpg)
Q0 = 0.19 / 29                                      # doublet rate under the 81% anti-repeat rule

def fresh_c(rng, n):
    c = np.empty(n, np.int64); c[0] = rng.integers(29)
    for i in range(1, n):
        x = rng.integers(29)
        if x == c[i - 1] and rng.random() < 0.81: x = (x + rng.integers(1, 29)) % 29
        c[i] = x
    return c

def fresh_stream(rng):
    return [fresh_c(rng, n) for n in LENS]

def perm_stream(rng):
    out = [None] * len(paras)
    for s in np.unique(sec):
        ix = np.nonzero(sec == s)[0]; ds = np.concatenate([pipe.deltas(paras[i]) for i in ix]); ds = rng.permutation(ds); o = 0
        for i in ix:
            out[i] = np.cumsum(ds[o:o + LENS[i]]) % 29; o += LENS[i]
    return out

_ENG = None
def english_runes():
    global _ENG
    if _ENG is None:
        import re
        t = re.sub('[^a-z]', '', open(os.path.join(pipe.HERE, '..', 'ref', 'emerson_essays1.txt'), encoding='utf-8', errors='ignore').read().lower())
        m = {c: pipe.lp.LATIN.index(l) for c, l in (('f','F'),('u','U'),('v','U'),('o','O'),('r','R'),('c','C'),('k','C'),('q','C'),('g','G'),('w','W'),('h','H'),('n','N'),('i','I'),('j','J'),('p','P'),('x','X'),('s','S'),('z','S'),('t','T'),('b','B'),('e','E'),('m','M'),('l','L'),('d','D'),('a','A'),('y','Y'))}
        _ENG = np.array([m[c] for c in t], np.int64)
    return _ENG

def plant(rng, q, eng=True):
    """308-rune paragraph: 303 kept deltas = English delta + period-13 offset (kept with prob q, else uniform),
    5 skipped deltas of one value inserted at random positions; returned as ciphertext runes."""
    e = english_runes(); o = rng.integers(len(e) - 400); pt = e[o:o + 303]
    ed = np.concatenate([[pt[0]], (pt[1:] - pt[:-1]) % 29]); K = rng.integers(0, 29, 13)
    if not eng: ed = np.zeros(303, np.int64)
    d = (ed + K[np.arange(303) % 13]) % 29
    rnd = rng.random(303) > q; d[rnd] = rng.integers(0, 29, rnd.sum())
    v = rng.integers(29); at = np.sort(rng.choice(np.arange(1, 308), 5, replace=False))
    full = np.empty(308, np.int64); mask = np.zeros(308, bool); mask[at] = True
    full[mask] = v; full[~mask] = d
    return np.cumsum(full) % 29

def one(args):
    model, i, q = args
    rng = np.random.default_rng([hash(model) % 2**31 if False else {'real':0,'perm':1,'fresh':2,'plant_eng':3,'plant_key':4}[model], i])
    if model == 'real': s = paras
    elif model == 'perm': s = perm_stream(rng)
    else:
        s = fresh_stream(rng)
        if model.startswith('plant'): s[PL] = plant(rng, q, model == 'plant_eng')
    t = time.time(); (v, gi, p), b0 = pipe.stream_max(s)
    d = pipe.deltas(s[PL]); pl = pipe.exact_best(d, 13); pl0 = pipe.base_ioc(d, 13)
    return dict(model=model, q=q, i=i, max=v, para=gi, period=p, base_max=b0, p14_13_skip=pl, p14_13_base=pl0, sec=time.time() - t)

if __name__ == '__main__':
    model, a, n = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]); q = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    out = open(f'out_{model}_{q}.jsonl' if model.startswith('plant') else f'out_{model}.jsonl', 'a')
    with Pool(2) as pool:
        for r in pool.imap_unordered(one, [(model, i, q) for i in range(a, a + n)]):
            out.write(json.dumps(r) + '\n'); out.flush()
