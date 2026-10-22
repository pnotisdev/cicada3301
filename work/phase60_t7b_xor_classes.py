"""Phase 60 T7b: XOR-domain keys by key-class coincidences. Convention-free for every cipher c = f(p, k) in which one key value selects one substitution of the alphabet, which holds for
all three XOR conventions (X1 index XOR wrapped mod 29, X2 prime-value XOR wrapped mod 29, X3 index XOR with pass-through when p XOR k >= 29; see phase60_t7_xor.py); X4 (reject-skip)
makes the key pointer depend on the plaintext and is not covered.
Statistic: at key offset o the n window runes are grouped by the key value they would be keyed with; two runes with the SAME key value share the substitution, so c_i = c_j happens at
the English coincidence rate (about 6.4%) instead of 3.4%. z = (observed pairs with equal key and equal ciphertext - n_c f) / sqrt(n_c f (1 - f)), n_c = ciphertext-equal pairs of the
window, f = the share of equal-key pairs at that offset (exact, from the key histogram). Strict alignment: no unkeyed extra rune (R4 would break the alignment after a few words:
the plants with R4 insertion show how much power that costs). Key partitions: the stream's own values, the Gematria prime of a value (& 127); for the blobs the byte, byte & 31, byte & 127, byte mod 29.
    python work/phase60_t7b_xor_classes.py control | run [--workers N] | blobs [--workers N] | summary
"""
import argparse, json, random, re, sys, time
import concurrent.futures as cf
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / 'kscreen')); sys.path.insert(0, str(HERE / 'layer2'))
import lp  # noqa: E402
import stats  # noqa: E402
from export import read_ksb  # noqa: E402

Q = 29
PR = np.array(lp.PRIME)
OUTD = ROOT / 'results' / 'analysis'
N = 300
ARCH = ROOT / 'Other repositories and work' / 'The-Complete-Cicada3301-Archive' / 'assets' / '2013' / 'cicados' / 'DATA'


def fmap(conv, p, k):
    if conv == 'X1':
        return (p ^ k) % Q
    if conv == 'X2':
        return (int(PR[p]) ^ k) % Q
    v = p ^ k
    return v if v <= 28 else p


def windows():
    out = []
    for s in range(7, 16):
        r = lp.runes_of(stats.SEGS[s])
        if len(r) >= N:
            out.append((f'0.{s}', np.array(r[:N], np.int64)))
    return out


def pairs_of(c):
    i, j = np.triu_indices(len(c), 1)
    m = c[i] == c[j]
    return i[m], j[m]


def zscores(c, K, pairs=None):
    """z at every offset of K (non-negative integer array longer than N)"""
    I, J = pairs if pairs is not None else pairs_of(c)
    noff = len(K) - N + 1
    obs = np.zeros(noff, np.int32)
    for i, j in zip(I, J):
        obs += (K[i:i + noff] == K[j:j + noff])
    ncl = int(K.max()) + 1
    f = np.zeros(noff)
    cs = np.zeros(len(K) + 1, np.int32)
    for k in range(ncl):
        np.cumsum(K == k, out=cs[1:])
        m = (cs[N:N + noff] - cs[:noff]).astype(np.float64)
        f += m * (m - 1) / 2
    f /= N * (N - 1) / 2
    nc = len(I)
    return (obs - nc * f) / np.sqrt(np.maximum(nc * f * (1 - f), 1e-9))


def library():
    return [(n, np.frombuffer(bytes(v), np.uint8).astype(np.int32)) for n, v in read_ksb(str(HERE / 'kscreen' / 'data' / 'library.ksb'))]


def partition(K, variant):
    return (PR[K] & 127).astype(np.int32) if variant == 'P' else K


def english_words():
    txt = open(HERE / 'ref' / 'emerson_essays1.txt', encoding='utf-8').read()
    txt = txt[txt.index('SELF-RELIANCE'):].split('*** END OF')[0]
    ws = [lp.word_to_key(w.upper().replace('IO', 'IA')) for w in re.findall(r'[A-Za-z]+', txt)]
    return [[int(x) for x in w] for w in ws if w]


def plant(conv, Km, off, rng, words, extra):
    out, j = [], off
    for w in words:
        enc = []
        for p in w:
            enc.append(fmap(conv, p, int(Km[j]))); j += 1
        if rng.random() < extra and len(enc) > 1:
            enc.insert(rng.randrange(1, len(enc)), rng.randrange(Q))
        out += enc
        if len(out) >= N + 40:
            break
    return np.array(out[:N], np.int64)


def cmd_control():
    rng = random.Random(81)
    lib = library(); words = english_words()
    lines = []
    for conv, mask in (('X1', 31), ('X2', 127), ('X3', 31)):
        for extra in (0.0, 0.45):
            ok, zs, nz = 0, [], []
            for t in range(8):
                name, K = lib[rng.randrange(len(lib))]
                Km = (K & mask)
                off = rng.randrange(0, len(Km) - 800)
                c = plant(conv, Km, off, rng, words[rng.randrange(len(words) - 400):][:400], extra)
                z = zscores(c, Km)
                at = int(np.argmax(z))
                Kr = np.array([rng.randrange(mask + 1) for _ in range(20000)], np.int32)
                nz.append(float(zscores(c, Kr).max()))
                ok += float(z[off]) >= 6.5
                zs.append(float(z[off]))
            lines.append(f'{conv} extra-rune rate {extra}: plants detected (z at the true offset >= 6.5, above every random-stream value) {ok}/8; z at truth median {np.median(zs):.1f} (min {min(zs):.1f}); random key stream best z max {max(nz):.1f}')
    t = chr(10).join(lines)
    (OUTD / 'phase60_t7b_control.txt').write_text(t + chr(10)); print(t)


_W = {}


def run_task(args):
    variant, lo, hi = args
    lib = _W.setdefault('lib', library())
    wins = _W.setdefault('wins', [(n, c, pairs_of(c)) for n, c in windows()])
    best, hist = (-99, None), np.zeros(6, np.int64)
    for name, K in lib[lo:hi]:
        Kp = partition(K, variant)
        for wn, c, pr in wins:
            z = zscores(c, Kp, pr)
            hist += np.histogram(z, bins=[-99, 3, 4, 5, 6, 7, 99])[0]
            if z.max() > best[0]:
                best = (float(z.max()), (name, wn, int(np.argmax(z))))
    return variant, best, hist.tolist()


def cmd_run(w):
    lib = library()
    rng = random.Random(82)
    tasks = [(v, lo, min(lo + 60, len(lib))) for v in ('v', 'P') for lo in range(0, len(lib), 60)]
    res, t0 = {}, time.time()
    with cf.ProcessPoolExecutor(max_workers=w) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(run_task, t) for t in tasks]), 1):
            v, best, hist = f.result()
            d = res.setdefault(v, dict(best=(-99, None), hist=[0] * 6))
            if best[0] > d['best'][0]:
                d['best'] = best
            d['hist'] = [a + b for a, b in zip(d['hist'], hist)]
            print(f'[{time.time() - t0:.0f}s] {n}/{len(tasks)}', flush=True)
    wins = [(n, c, pairs_of(c)) for n, c in windows()]
    for v in res:
        nb = -99
        for i in range(40):
            Kr = np.array([rng.randrange(128 if v == 'P' else 29) for _ in range(20000)], np.int32)
            for wn, c, pr in wins:
                nb = max(nb, float(zscores(c, Kr, pr).max()))
        res[v]['null_best'] = nb
    (OUTD / 'phase60_t7b_run.json').write_text(json.dumps(res)); print(res)


def blob_task(args):
    f, d, part, lo = args
    b = np.frombuffer((ARCH / f).read_bytes(), np.uint8)
    b = b[::-1] if d == 'rev' else b
    K = {'byte': b, 'and31': b & 31, 'and127': b & 127, 'mod29': b % 29}[part].astype(np.int32)[lo:lo + 300000 + N]
    best = (-99, None)
    if len(K) <= N:
        return f'{f} {d} {part}', best
    for wn, c in windows():
        z = zscores(c, K)
        if z.max() > best[0]:
            best = (float(z.max()), (wn, lo + int(np.argmax(z))))
    return f'{f} {d} {part}', best


def cmd_blobs(w):
    tasks = []
    for f in ('560.17', '_560.00'):
        n = (ARCH / f).stat().st_size
        for d in ('fwd', 'rev'):
            for part in ('and31', 'and127'):
                tasks += [(f, d, part, lo) for lo in range(0, n, 300000)]
    res, t0 = {}, time.time()
    with cf.ProcessPoolExecutor(max_workers=w) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(blob_task, t) for t in tasks]), 1):
            key, best = f.result()
            if best[0] > res.get(key, (-99, None))[0]:
                res[key] = best
            if n % 20 == 0:
                print(f'[{time.time() - t0:.0f}s] {n}/{len(tasks)}', flush=True)
    (OUTD / 'phase60_t7b_blobs.json').write_text(json.dumps(res)); print(res)


def cmd_summary():
    L = [f'# Phase 60 T7b: XOR-domain keys by key-class coincidences (n {N}, strict alignment), first window of each of the 8 sections']
    r = json.loads((OUTD / 'phase60_t7b_run.json').read_text())
    for k, d in r.items():
        L.append(f'library partition {k}: best z {d["best"][0]:.2f} ({d["best"][1]}); random-stream null best {d["null_best"]:.2f}; trials {sum(d["hist"]):,}; histogram z [<3,3-4,4-5,5-6,6-7,>7] {d["hist"]}')
    p = OUTD / 'phase60_t7b_blobs.json'
    if p.exists():
        for k, v in sorted(json.loads(p.read_text()).items()):
            L.append(f'blob {k}: best z {v[0]:.2f} ({v[1]})')
    t = chr(10).join(L) + chr(10)
    (OUTD / 'phase60_t7b_xor_classes.txt').write_text(t); print(t)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('control', 'run', 'blobs', 'summary', 'strings')); ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    {'strings': lambda: None, 'control': cmd_control, 'run': lambda: cmd_run(a.workers), 'blobs': lambda: cmd_blobs(a.workers), 'summary': cmd_summary}[a.cmd]()


def cmd_strings():
    """Cicada's number strings (raw values) and the seven 256-byte onion strings (+ XOR combinations) as periodic key streams of 20,000 values, five partitions each"""
    import os
    os.environ.setdefault('P60_SET', 'hex256')
    import phase60_t2_numkeys as T2
    rng = random.Random(83)
    wins = [(n, c, pairs_of(c)) for n, c in windows()]
    keys = []
    for name, seq in T2.SEQS.items():
        keys.append((name, np.array(seq, np.int64)))
    for name, d in T2.DIGITS.items():
        keys.append((name + ' digits', np.array([int(ch) for ch in d], np.int64)))
    for name, h in T2.COOKIES.items():
        keys.append((f'cookie {name} bytes', np.frombuffer(bytes.fromhex(h), np.uint8).astype(np.int64)))
    # the onion strings: the same extraction as T2's hex256 set, as raw bytes
    import re, glob
    strs = {}
    for f in sorted(glob.glob(str(HERE / 'ref' / 'uncovering_cicada' / 'pages' / '*.wiki'))):
        for m in re.finditer(r'(?<![0-9a-fA-F])[0-9a-f]{512}(?![0-9a-fA-F])', open(f, encoding='utf-8', errors='replace').read()):
            strs.setdefault(m.group(), len(strs))
    arrs = [np.frombuffer(bytes.fromhex(h), np.uint8).astype(np.int64) for h in strs]
    for i, a in enumerate(arrs):
        keys.append((f'onion-hex #{i}', a))
    o = [arrs[0], arrs[2], arrs[4]]
    keys += [('xor 2^3', o[0] ^ o[1]), ('xor 2^4', o[0] ^ o[2]), ('xor 3^4', o[1] ^ o[2]), ('xor 2^3^4', o[0] ^ o[1] ^ o[2])]
    res, null = [], -99
    for name, a in keys:
        for part, fn in (('value', lambda x: x), ('mod29', lambda x: x % 29), ('and31', lambda x: x & 31), ('and127', lambda x: x & 127), ('high5', lambda x: x >> 3)):
            base = fn(a).astype(np.int32)
            K = np.resize(base, 20000)
            best = max((float(zscores(c, K, pr).max()), wn) for wn, c, pr in wins)
            res.append((name, part, len(base), best[0], best[1]))
    for i in range(40):
        Kr = np.array([rng.randrange(256) for _ in range(20000)], np.int32)
        null = max(null, max(float(zscores(c, Kr, pr).max()) for wn, c, pr in wins))
    top = sorted(res, key=lambda r: -r[3])[:8]
    L = [f'# Phase 60 T7b strings: {len(keys)} number / onion / XOR-combination keys x 5 partitions as periodic streams, 8 windows (n {N}, strict alignment); random-stream null best z {null:.2f}']
    L += [f'{r[0]} / {r[1]} (period {r[2]}): best z {r[3]:.2f} in {r[4]}' for r in top]
    t = chr(10).join(L) + chr(10)
    (OUTD / 'phase60_t7b_strings.txt').write_text(t); print(t)


if __name__ == '__main__' and len(sys.argv) > 1 and sys.argv[1] == 'strings':
    cmd_strings()
