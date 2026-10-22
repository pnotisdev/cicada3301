"""Phase 60 T7a (R4-tolerant unigram DP; control only, power too low to run, see phase60_t7b_xor_classes.py): XOR-domain keys. The existing engines are additive mod 29 and cannot express XOR, so this is a small numpy screen.

Conventions (exact; 29 symbols are not closed under XOR of 5-bit numbers, so each convention says what happens at values >= 29):
  X1   index XOR, wrapped:       c = (p XOR k) mod 29, p = rune index 0..28, k = key value 0..31
  X2   prime-value XOR, wrapped: c = (P[p] XOR k) mod 29, P[p] = Gematria prime of rune p (2..109), k = key value 0..127
  X3   index XOR, pass-through:  c = p XOR k if that is <= 28, else c = p (invertible)
  X4   index XOR with rejection (the encryptor skips a key value when p XOR k >= 29): the key pointer then depends on the plaintext; no LM-free decoder exists
       (a path that skips at every step is always consistent), so it is NOT screened (stated in the log).
Statistic: for a candidate key stream K at offset o, every ciphertext rune c_i keyed with k_i has the likelihood P(c|k) = sum of the English unigram weights of the plaintext runes that
the convention maps to c (a rune with no preimage gets the floor 1e-3); LLR_i = log(29 P(c_i|k_i)), against the uniform null. R4 puts an unkeyed extra rune into about 45% of the words
(about 7% of the runes): a lag DP lets any rune be unkeyed (LLR 0, probability rho = 0.07, key not consumed), at most LM of them. Score = best path (nats), the first N runes of each
n300 section-start window, all offsets. Matched null: random key streams through the same code. Controls: English plants with R4's insertion.
    python work/phase60_t7_xor.py control | run [--workers N] | blobs [--workers N] | summary
"""
import argparse, json, math, random, re, sys, time
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
NW, LM, RHO = 120, 8, 0.07
OUTD = ROOT / 'results' / 'analysis'
CONVS = {'X1': 32, 'X2': 128, 'X3': 32}
FLOOR = 1e-3
LOGK, LOGU = math.log(1 - RHO), math.log(RHO)


def fmap(conv, p, k):
    if conv == 'X1':
        return (p ^ k) % Q
    if conv == 'X2':
        return (int(PR[p]) ^ k) % Q
    v = p ^ k
    return v if v <= 28 else p


def english_pi():
    txt = open(HERE / 'ref' / 'emerson_essays1.txt', encoding='utf-8').read()
    txt = txt[txt.index('SELF-RELIANCE'):].split('*** END OF')[0]
    words = [lp.word_to_key(w.upper().replace('IO', 'IA')) for w in re.findall(r'[A-Za-z]+', txt)]
    words = [[int(x) for x in w] for w in words if w]
    flat = np.array([x for w in words for x in w])
    pi = np.bincount(flat, minlength=Q) / len(flat)
    return pi, words


PI, WORDS = english_pi()


def llr_table(conv):
    """T[c][k] = log(29 * P(c | k)), floored"""
    nk = CONVS[conv]
    P = np.zeros((Q, nk))
    for k in range(nk):
        for p in range(Q):
            P[fmap(conv, p, k), k] += PI[p]
    return np.log(np.maximum(29 * P, FLOOR)).astype(np.float32)


TAB = {c: llr_table(c) for c in CONVS}


def dp_scores(c, K, T, n=NW):
    """best path score (nats) at every offset of K for ciphertext c[:n]; K: uint8 array"""
    n = min(n, len(c))
    noff = len(K) - n - LM
    NEG = np.float32(-1e9)
    dp = [np.full(noff, NEG, np.float32) for _ in range(LM + 1)]
    dp[0][:] = 0
    for i in range(n):
        Tc = T[c[i]]
        new = []
        for l in range(LM + 1):
            r = np.full(noff, NEG, np.float32)
            if l <= i:
                r = dp[l] + Tc[K[i - l:i - l + noff]] + np.float32(LOGK)
            if l >= 1:
                np.maximum(r, dp[l - 1] + np.float32(LOGU), out=r)
            new.append(r)
        dp = new
    return np.maximum.reduce(dp)


def windows():
    out = []
    for s in range(7, 16):
        r = lp.runes_of(stats.SEGS[s])
        if len(r) >= 300:
            out.append((f'0.{s}', np.array(r[:300], np.int64)))
    return out


def plant(conv, K, off, rng, words, extra=0.45):
    out, j = [], off
    for w in words:
        enc = []
        for p in w:
            enc.append(fmap(conv, p, int(K[j]))); j += 1
        if rng.random() < extra and len(enc) > 1:
            enc.insert(rng.randrange(1, len(enc)), rng.randrange(Q))
        out += enc
        if len(out) >= 340:
            break
    return np.array(out[:300], np.int64)


def library():
    return [(n, np.frombuffer(bytes(v), np.uint8)) for n, v in read_ksb(str(HERE / 'kscreen' / 'data' / 'library.ksb'))]


def keymap(K, conv, variant):
    """library stream values 0..28 -> key values: 'v' as is; 'P' the Gematria prime of the value"""
    if variant == 'P':
        return PR[K.astype(np.int64)].astype(np.uint8) & (31 if CONVS[conv] == 32 else 127)
    return K


def cmd_control():
    rng = random.Random(79)
    lib = library()
    lines = []
    for conv in ('X1', 'X2', 'X3'):
        T = TAB[conv]
        ok, rows = 0, []
        nulls = []
        for t in range(10):
            name, K = lib[rng.randrange(len(lib))]
            Kc = keymap(K, conv, 'v')
            off = rng.randrange(0, len(Kc) - 600)
            w0 = rng.randrange(len(WORDS) - 300)
            c = plant(conv, Kc, off, rng, WORDS[w0:w0 + 300])
            s = dp_scores(c, Kc, T)
            at = int(np.argmax(s))
            Kr = np.frombuffer(bytes(rng.randrange(CONVS[conv]) for _ in range(20000)), np.uint8)
            nulls.append(float(dp_scores(c, Kr, T).max()))
            good = abs(at - off) <= 2
            ok += good
            rows.append(f'  plant {t}: {name!r} off {off}: best {s.max():.1f} at {at} (score at truth {s[off]:.1f}); random key stream on the same ciphertext {nulls[-1]:.1f}')
        lines.append(f'{conv}: plants recovered at the true offset {ok}/10; random-stream best max {max(nulls):.1f}')
        lines += rows
    t = chr(10).join(lines)
    (OUTD / 'phase60_t7_xor_dp_control.txt').write_text(t + chr(10)); print(t)


_W = {}


def run_task(args):
    conv, variant, lo, hi = args
    lib = _W.setdefault('lib', library())
    wins = _W.setdefault('wins', windows())
    T = TAB[conv]
    best = (-1e9, None); hist = np.zeros(8, np.int64)
    for name, K in lib[lo:hi]:
        Kc = keymap(K, conv, variant)
        for wn, c in wins:
            s = dp_scores(c, Kc, T)
            m = float(s.max())
            hist += np.histogram(s, bins=[-1e9, 0, 5, 10, 15, 20, 30, 50, 1e9])[0]
            if m > best[0]:
                best = (m, (name, wn, int(np.argmax(s))))
    return conv, variant, best, hist.tolist()


def cmd_run(w):
    lib = library()
    rng = random.Random(80)
    tasks = [(c, v, lo, min(lo + 120, len(lib))) for c, v in (('X1', 'v'), ('X1', 'P'), ('X2', 'v'), ('X2', 'P'), ('X3', 'v'), ('X3', 'P')) for lo in range(0, len(lib), 120)]
    res = {}
    t0 = time.time()
    with cf.ProcessPoolExecutor(max_workers=w) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(run_task, t) for t in tasks]), 1):
            conv, variant, best, hist = f.result()
            d = res.setdefault(f'{conv}{variant}', dict(best=(-1e9, None), hist=[0] * 8))
            if best[0] > d['best'][0]:
                d['best'] = best
            d['hist'] = [a + b for a, b in zip(d['hist'], hist)]
            print(f'[{time.time() - t0:.0f}s] {n}/{len(tasks)}', flush=True)
    # matched null: 40 random streams x 8 windows per cell
    wins = windows()
    for key in list(res):
        conv, variant = key[:2], key[2:]
        T = TAB[conv]
        nb = -1e9
        for i in range(40):
            Kr = np.frombuffer(bytes(rng.randrange(CONVS[conv]) for _ in range(20000)), np.uint8)
            for wn, c in wins:
                nb = max(nb, float(dp_scores(c, Kr, T).max()))
        res[key]['null_best'] = nb
        print(key, res[key], flush=True)
    (OUTD / 'phase60_t7_xor.json').write_text(json.dumps(res))


def cmd_blobs(w):
    """560.17 / _560.00 bytes as XOR keys: byte & 31 (X1, X3) and byte & 127 (X2), forwards and backwards, all offsets, the 8 section windows (chunks of 400,000 offsets)"""
    arch = ROOT / 'Other repositories and work' / 'The-Complete-Cicada3301-Archive' / 'assets' / '2013' / 'cicados' / 'DATA'
    tasks = []
    for f in ('560.17', '_560.00'):
        b = np.frombuffer((arch / f).read_bytes(), np.uint8)
        for d in ('fwd', 'rev'):
            tasks += [(f, d, conv, lo) for conv in ('X1', 'X2', 'X3') for lo in range(0, len(b), 400000)]
    res, t0 = {}, time.time()
    with cf.ProcessPoolExecutor(max_workers=w) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(blob_task, t) for t in tasks]), 1):
            key, best = f.result()
            if best[0] > res.get(key, (-1e9, None))[0]:
                res[key] = best
            print(f'[{time.time() - t0:.0f}s] {n}/{len(tasks)}', flush=True)
    (OUTD / 'phase60_t7_xor_blobs.json').write_text(json.dumps(res))
    print(res)


def blob_task(args):
    f, d, conv, lo = args
    arch = ROOT / 'Other repositories and work' / 'The-Complete-Cicada3301-Archive' / 'assets' / '2013' / 'cicados' / 'DATA'
    b = np.frombuffer((arch / f).read_bytes(), np.uint8)
    b = b[::-1] if d == 'rev' else b
    K = (b & (31 if CONVS[conv] == 32 else 127)).astype(np.uint8)
    seg = K[lo:lo + 400000 + NW + LM]
    best = (-1e9, None)
    if len(seg) < NW + LM + 10:
        return f'{f} {d} {conv}', best
    for wn, c in windows():
        s = dp_scores(c, seg, TAB[conv])
        if s.max() > best[0]:
            best = (float(s.max()), (wn, lo + int(np.argmax(s))))
    return f'{f} {d} {conv}', best


def cmd_summary():
    L = ['# Phase 60 T7: XOR-domain keys (conventions X1 / X2 / X3; X4 not screened), first %d runes of the section-start n300 windows, lag DP with <= %d unkeyed runes (rho %.2f)' % (NW, LM, RHO)]
    r = json.loads((OUTD / 'phase60_t7_xor.json').read_text())
    for k, d in r.items():
        L.append(f'library {k}: best {d["best"][0]:.1f} nats ({d["best"][1]}); random-stream null best {d["null_best"]:.1f}; cells >= 20: {sum(d["hist"][4:])}; histogram [<0,0-5,5-10,10-15,15-20,20-30,30-50,>50] {d["hist"]}')
    p = OUTD / 'phase60_t7_xor_blobs.json'
    if p.exists():
        for k, v in json.loads(p.read_text()).items():
            L.append(f'blob {k}: best {v[0]:.1f} nats ({v[1]})')
    t = chr(10).join(L) + chr(10)
    (OUTD / 'phase60_t7_xor.txt').write_text(t); print(t)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('control', 'run', 'blobs', 'summary')); ap.add_argument('--workers', type=int, default=2)
    a = ap.parse_args()
    {'control': cmd_control, 'run': lambda: cmd_run(a.workers), 'blobs': lambda: cmd_blobs(a.workers), 'summary': cmd_summary}[a.cmd]()
