"""Verification chain for one candidate cell (PROTOCOL.md): independent re-score, Viterbi plaintext, prime-sum check.

    python verify_cell.py <set> <window index> <stream name or index> <sign> <channel> <offset>

1. The cell is re-scored with the v1 dense reference engine (cpu.forward: full state, no sparse reduction); S must agree with the
   campaign's to 1e-6 nats.
2. The Viterbi path of the dense engine gives the most likely plaintext; it is printed in Latin letters.
3. work/prime_check.py is run on the clauses that lie completely inside the window (n300 and clause sets only).
Whole-section re-decode with a matched null (docs/CAMPAIGNS.md) is the next step and is done by hand.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import campaign as K  # noqa: E402
import numpy as np  # noqa: E402

import cpu as oldcpu  # noqa: E402  (v1 dense reference through the Rust adapter)
from reconstruct import viterbi  # noqa: E402

sys.path.insert(0, str(C.ROOT / 'work'))
import prime_check  # noqa: E402


def main(kind, wi, stream, sign, ch, off):
    wins = C.windows(kind)
    lib = C.read_library()
    names = [n for n, _ in lib]
    si = int(stream) if stream.isdigit() else names.index(stream)
    name, key = lib[si]
    w = wins[wi]
    c = w['cipher']
    pi, L = C.model()
    logW = C.log_common(c, C.Q_DECODER, C.Q)
    sg, s = C.guard_scores(c, key, sign, ch, C.Q_DECODER, pi, L, logW)
    print(f'window {w["name"]} ({len(c)} runes), stream {name!r} (length {len(key)}), sign {sign}, channel {ch}, offset {off}')
    print(f'campaign engine: S = {s[off]:.6f}, S_guard = {sg[off]:.6f}')
    U = np.full(C.Q, 1 / C.Q)
    ll = oldcpu.forward(c, [int(x) for x in key], off, sign, C.Q_DECODER, ch, pi, L)
    lu = oldcpu.forward(c, [int(x) for x in key], off, sign, C.Q_DECODER, ch, U, np.full((C.Q, C.Q), 1 / C.Q))
    print(f'dense v1 engine: S = {ll - lu:.6f}  (difference {abs((ll - lu) - s[off]):.2e} nats)')
    ext = {'hold': 1, 'spend': 1, 'skip5': 6, 'coin': 3}[ch] * len(c) + 16
    sl = [int(x) for x in key[off:off + ext]]
    pp, jj, v = viterbi(c, sl, 0, sign, C.Q_DECODER, ch, pi, L)
    text = ''.join(lp_latin(x) for x in pp)
    print('Viterbi plaintext:', text)
    if w['sec'] > 0:
        segs = prime_check.lp.load_segments()
        r = prime_check.check(segs[w['sec']], w['start'], pp)
        print({k: v for k, v in r.items() if k != 'rows'})
        for a, n, ssum, p in r['rows']:
            print(f'  clause at {a} ({n} runes) sum {ssum} {"PRIME" if p else ""}')


def lp_latin(x):
    return prime_check.lp.LATIN[x]


if __name__ == '__main__':
    k, wi, st, sg, ch, off = sys.argv[1:7]
    main(k, int(wi), st, int(sg), ch, int(off))
