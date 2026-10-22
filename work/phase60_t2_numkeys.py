"""Phase 60 test T2: Cicada's published number strings as short periodic keys under R4 (phase 59 engine and channels, unchanged).

Keys: the 2014 / 2012 / 2015 whitespace sequences, the Fibonacci-tree branch set, digit strings of Cicada's numbers, the 49 numbers of the 7 x 7 square of 761.mp3,
the 2012 P.S. digits, the two 2013 cookie values; maps value -> rune: v mod 29, (v - 1) mod 29, and (for primes <= 109) the rune whose Gematria prime is v.
    python -B work/phase60_t2_numkeys.py keys | control [--workers 3] | scan [--workers 3] | summary
"""
import argparse, concurrent.futures as cf, json, random, sys, time
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import phase59_keywords_r4 as P59  # noqa: E402

import inspect
import os
SET = os.environ.get('P60_SET', 't2')          # 't2' number strings; 'folly' = the Cicada OS file tmp/folly as four 3,368-term keys (T4 under R4)
# ctl_task samples 150 decoy keywords of a 1,940 set; this set has 50 keys, so 40 decoys
exec(inspect.getsource(P59.ctl_task).replace('range(len(keys)), 151', 'range(len(keys)), 41' if SET == 't2' else 'range(len(keys)), 4').replace('[:150]', '[:40]' if SET == 't2' else '[:3]'), P59.__dict__)
OUT = P59.C.OUT / {'t2': 'phase60_t2', 'folly': 'phase60_t4_folly', 'hex256': 'phase60_t2_hex256'}[SET]
P59.OUT = OUT            # module global read by P59.init / win_task / ctl_task (also in spawned workers: this module is imported there)

SQ7 = [7, 375, 236, 190, 27, 17, 181, 351, 223, 14, 47, 293, 98, 7, 456, 232, 121, 114, 72, 23, 15, 16, 65, 270, 331, 270, 65, 16, 15, 23, 72, 114, 121, 232, 456,
       7, 98, 293, 47, 14, 223, 351, 181, 17, 27, 190, 236, 375, 7]
PS = "1041279065891998535982789873959431895640" "442510695567564373922695237268242385295908173" "9834390370374475764863415203423499357108713631"
COOKIES = {"167": "6941f707ff39d259ff71657a79cb6b54c184d2f0455810109c1a960860bde0e6", "761": "7bc1e7805ccfa518920f0d94fc4e8f7dbd83287a03b337b89109cd2287befae5"}
SEQS = {
    "A2014 primes (19 missing)": [2, 3, 5, 7, 11, 13, 17, 23, 29, 31, 37],
    "A2014 primes + 19": [2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37],
    "2012 final message": [0, 2, 3, 5, 7, 11, 13, 1, 1, 2, 11, 0, 7, 0, 5, 0, 3, 2],
    "2012 no zeros": [2, 3, 5, 7, 11, 13, 1, 1, 2, 11, 7, 5, 3, 2],
    "2012 up and down": [2, 3, 5, 7, 11, 13, 11, 7, 5, 3, 2],
    "2015 spaces": [5, 3, 2, 5, 7],
    "fib-tree branches": [2, 3, 5, 6, 8, 10, 11, 13],
    "parable sums": [1259, 1031, 1229],
    "7x7 square (49)": SQ7,
}
DIGITS = {"3301": "3301", "1033": "1033", "33011033": "33011033", "761": "761", "parable product": "1595277641", "parable sums digits": "125910311229",
          "harmonic16": "2422826321411203", "P.S. digits (131)": PS}


def keyset():
    import phrase_keys as PK
    PRIME = PK.lp.PRIME
    keys = {}
    def add(vals, tag):
        k = P59.canon(tuple(vals))
        if len(k) >= 2 and k not in keys:
            keys[k] = tag
    for name, seq in SEQS.items():
        add([v % 29 for v in seq], f'{name} mod29')
        add([(v - 1) % 29 for v in seq], f'{name} mod29-1')
        if all(v in PRIME for v in seq):
            add([PRIME.index(v) for v in seq], f'{name} prime->rune')
    for name, d in DIGITS.items():
        add([int(c) for c in d], f'{name} digits')
        add([(int(c) - 1) % 29 for c in d], f'{name} digits-1')
        add([(int(c) + 1) % 29 for c in d], f'{name} digits+1')
    for name, h in COOKIES.items():
        b = bytes.fromhex(h)
        add([x % 29 for x in b], f'cookie {name} bytes mod29')
        add([int(c, 16) for c in h], f'cookie {name} hex digits')
    return keys


def folly_keys():
    import numpy as np
    b = np.frombuffer((HERE.parent / 'Other repositories and work' / 'The-Complete-Cicada3301-Archive' / 'assets' / '2013' / 'cicados' / 'tmp' / 'folly').read_bytes(), np.uint8)
    keys = {}
    for mode, v in (('mod', b % 29), ('rej', b[b < 232] % 29)):
        keys[tuple(int(x) for x in v)] = f'folly {mode} fwd'
        keys[tuple(int(x) for x in v[::-1])] = f'folly {mode} rev'
    return keys


def hex256_keys():
    import re, glob
    import numpy as np
    strs = {}
    for f in sorted(glob.glob(str(HERE / 'ref' / 'uncovering_cicada' / 'pages' / '*.wiki'))):
        for m in re.finditer(r'(?<![0-9a-fA-F])[0-9a-f]{512}(?![0-9a-fA-F])', open(f, encoding='utf-8', errors='replace').read()):
            strs.setdefault(m.group(), len(strs))
    arrs = {f'hex256 #{i}': np.frombuffer(bytes.fromhex(h), np.uint8) for h, i in strs.items()}
    onion = [arrs[f'hex256 #{i}'] for i in (0, 2, 4)]            # onion 2, 3, 4 strings (order of first appearance); the others are their 'totient' strings and one more
    arrs['xor 2^3'] = onion[0] ^ onion[1]; arrs['xor 2^4'] = onion[0] ^ onion[2]; arrs['xor 3^4'] = onion[1] ^ onion[2]; arrs['xor 2^3^4'] = onion[0] ^ onion[1] ^ onion[2]
    keys = {}
    for name, b in arrs.items():
        for mode, v in (('mod', b % 29), ('rej', b[b < 232] % 29)):
            keys[P59.canon(tuple(int(x) for x in v))] = f'{name} {mode}'
    return keys


def cmd_keys():
    OUT.mkdir(parents=True, exist_ok=True)
    keys = {'t2': keyset, 'folly': folly_keys, 'hex256': hex256_keys}[SET](); kl = list(keys)
    (OUT / 'keys.json').write_text(json.dumps(dict(keys=[list(k) for k in kl], tags=[keys[k] for k in kl])))
    print(len(kl), 'keys, lengths', sorted({len(k) for k in kl}), 'windows', len(P59.windows()))


def cmd_control(w):
    d = json.loads((OUT / 'keys.json').read_text()); keys = [tuple(k) for k in d['keys']]; tags = d['tags']
    if SET == 't2':
        want = ['A2014 primes (19 missing) mod29', 'fib-tree branches mod29', '2012 final message mod29', '3301 digits']
        idx = [next(i for i, t in enumerate(tags) if t == x) for x in want]
        idx += random.Random(60).sample([i for i in range(len(keys)) if i not in idx], 2)
    elif SET == 'folly':
        idx = [0, 3]
    else:
        idx = [0, 5, 11, len(keys) - 1]
    todo = [(ki, ch, src, i) for n, ki in enumerate(idx) for ch in P59.CH for src in ('cicada', 'english') for i in range(2 if n < 2 else 1)]
    print(len(todo), 'plants', flush=True)
    with cf.ProcessPoolExecutor(max_workers=w, initializer=P59.ctl_init) as ex:
        for n, f in enumerate(cf.as_completed([ex.submit(P59.ctl_task, t) for t in todo]), 1):
            print(f'[{time.strftime("%H:%M:%S")}] {n}/{len(todo)} {f.result()}', flush=True)


def summary():
    d = json.loads((OUT / 'keys.json').read_text()); tags = d['tags']
    L = [f'# Phase 60 { {'t2': 'T2', 'folly': 'T4 (folly)', 'hex256': 'T2b (256-byte strings)'}[SET] }: {len(tags)} keys under R4 (phase 59 engine, hold / spend, both signs, T300 = {P59.C.T300:.2f})']
    cr = [json.loads(p.read_text()) for p in sorted((OUT / 'control').glob('*.json'))]
    if cr:
        srt = sorted(r['true_score'] for r in cr)
        L.append(f'control: {sum(r["true_found"] for r in cr)}/{len(cr)} planted keys recovered (score >= T300, right sign and phase); true score min / median {srt[0]:.1f} / {srt[len(srt) // 2]:.1f}; '
                 f'wrong-key max: set {max(r["decoy_set_max"] for r in cr):.1f}, random same-length {max(r["decoy_rand_max"] for r in cr):.1f}; iid-key plant with the true key: max {max(r["iid_key_plant_true_keyword_score"] for r in cr):.1f}')
        for r in cr:
            L.append(f'   {tags[r["key_index"]]} len {r["keyword_len"]} {r["channel"]} {r["src"]} {r["index"]}: true {r["true_score"]:.1f} found {r["true_found"]}')
    sr = [json.loads(p.read_text()) for p in sorted((OUT / 'scan').glob('*.json'))]
    if sr:
        b = max(sr, key=lambda r: r['best'])
        L.append(f'scan: {len(sr)}/{len(P59.windows())} windows x {len(tags)} keys, CPU {sum(r["seconds"] for r in sr) / 3600:.2f} h; max S_guard {b["best"]:.2f} (section {b["sec"]} @ {b["start"]}, {tags[b["top"][0][1]]}); '
                 f'cells >= 20: {sum(r["n_hot"] for r in sr)}; windows >= T300: {sum(r["best"] >= P59.C.T300 for r in sr)}')
        for r in sr:
            for h in r['hot'][:5]:
                L.append(f'   sec {r["sec"]} @ {r["start"]}: score {h[0]:.1f} (fresh {h[5]:.1f}) {tags[h[1]]} sign {h[2]} {h[3]} offset {h[4]}')
    t = chr(10).join(L) + chr(10)
    (HERE.parent / 'results' / 'analysis' / {'t2': 'phase60_t2_numkeys.txt', 'folly': 'phase60_t4_folly_r4.txt', 'hex256': 'phase60_t2_hex256.txt'}[SET]).write_text(t, encoding='utf-8'); print(t)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('cmd', choices=('keys', 'control', 'scan', 'summary'))
    ap.add_argument('--workers', type=int, default=3); ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    if a.cmd == 'keys':
        cmd_keys()
    elif a.cmd == 'control':
        cmd_control(a.workers)
    elif a.cmd == 'scan':
        P59.cmd_scan(a.workers, a.limit, False)
    else:
        summary()
