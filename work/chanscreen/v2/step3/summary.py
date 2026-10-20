"""Merge the task files of a campaign set into a report.

    python summary.py <null|n300|clause>      # results/chanscreen/summary_<set>.txt and tier2_<set>.tsv

Tier 1: cells with S_guard >= T (candidates, not leads: re-score with the v1 dense reference, read the Viterbi text, run
work/prime_check.py, verify over the whole section). Tier 2: the top 50 (stream, sign) cells per (channel, window) by S_guard,
UNVERIFIED ranks. The counts above t are compared with the Markov bound N e^-t (an upper bound on the null expectation).
"""
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import campaign as K  # noqa: E402
import common as C  # noqa: E402


def recompute_tier1(tier1, wins, lib, names):
    """Recompute every (window, stream, sign, channel) that has tier-1 cells in a fresh call (PROTOCOL.md amendment 3): the number of
    stored cells whose S_guard comes back to 1e-6, and one line per group that does not (raised error, or values that differ)."""
    pi, Lm = C.model()
    groups = {}
    for t in tier1:
        groups.setdefault((t[0], t[8], t[3], t[4]), []).append(t)
    confirmed, faults = 0, []
    for (wi, si, sign, ch), cells in groups.items():
        c = wins[wi]['cipher']
        try:
            sg, _ = C.guard_scores(c, lib[si][1], sign, ch, C.Q_DECODER, pi, Lm, C.log_common(c, C.Q_DECODER, C.Q))
        except ValueError as e:
            faults.append(f'window {wins[wi]["name"]} stream {names[si]!r} sign {sign} {ch}: {len(cells)} cells, recomputation raised {e}')
            continue
        ok = sum(abs(float(sg[t[5]]) - t[6]) < 1e-6 for t in cells)
        confirmed += ok
        if ok < len(cells):
            faults.append(f'window {wins[wi]["name"]} stream {names[si]!r} sign {sign} {ch}: {len(cells) - ok} of {len(cells)} stored cells '
                          f'(best {max(t[6] for t in cells):.2f}) do not reproduce, recomputed best {float(np.max(sg)):.2f}')
    return confirmed, faults


def main(kind):
    wins = C.windows(kind)
    lib = C.read_library()
    names = [n for n, _ in lib]
    chunks = C.chunks([len(k) for _, k in lib])
    T = K.threshold(kind, len(wins))
    d = C.OUT / kind
    files = sorted(d.glob('w*_c*.npz'))
    expected = len(wins) * len(chunks)
    L = [f'# campaign set {kind}: {len(wins)} windows (lengths {min(len(w["cipher"]) for w in wins)}-{max(len(w["cipher"]) for w in wins)}), {len(chunks)} chunks, T = {T:.4f} nats',
         f'# tasks present {len(files)} of {expected}', '']
    by_win = {}
    for f in files:
        z = np.load(f)
        by_win.setdefault(int(z['window']), []).append((int(z['first_stream']), z['res'], z['cand']))
    chans = [(s, c) for s in C.SIGNS for c in C.CHANNELS]
    best = {ch: (-math.inf, None) for ch in C.CHANNELS}
    totals = np.zeros(6)
    npass = 0
    cells = 0
    tier1, tier2 = [], []
    window_max = []
    for wi, parts in sorted(by_win.items()):
        c_all = np.concatenate([p[1] for p in sorted(parts, key=lambda p: p[0])])  # streams x 8 x 9
        first = {p[0]: p for p in parts}
        sg = c_all[:, :, 0]
        window_max.append((wi, float(np.max(sg))))
        totals += np.array([c_all[:, :, 3 + j].sum() for j in range(5)] + [c_all[:, :, 8].sum()])
        npass += c_all.shape[0] * c_all.shape[1]
        for p in parts:
            for si in range(p[1].shape[0]):
                cells += 0
        for hi, ch in enumerate(C.CHANNELS):
            cols = [gi * len(C.CHANNELS) + hi for gi in range(len(C.SIGNS))]
            cand = [(float(sg[s, col]), s, col, int(c_all[s, col, 1]), float(c_all[s, col, 2])) for s in range(sg.shape[0]) for col in cols if np.isfinite(sg[s, col])]
            cand.sort(reverse=True)
            for v, s, col, off, sraw in cand[:50]:
                tier2.append((ch, wi, wins[wi]['name'], names[s], C.SIGNS[col // len(C.CHANNELS)], off, v, sraw))
            if cand and cand[0][0] > best[ch][0]:
                best[ch] = (cand[0][0], (wins[wi]['name'], names[cand[0][1]], C.SIGNS[cand[0][2] // len(C.CHANNELS)], cand[0][3], cand[0][4]))
        for p in parts:
            for row in p[2]:
                tier1.append((wi, wins[wi]['name'], names[int(row[0])], int(row[1]), C.CHANNELS[int(row[2])], int(row[3]), float(row[4]), float(row[5]), int(row[0])))
    L.append('1. Best S_guard per channel (window, stream, sign, offset, S)')
    for ch in C.CHANNELS:
        L.append(f'   {ch:6s} {best[ch][0]:9.3f}  {best[ch][1]}')
    L.append('')
    L.append(f'2. Windows searched {len(by_win)}; per-window maximum S_guard: min {min(v for _, v in window_max):.2f}, median {float(np.median([v for _, v in window_max])):.2f}, max {max(v for _, v in window_max):.2f}')
    L.append('')
    L.append('3. Cells (stream, sign, channel, offset) with S_guard >= t, against the Markov bound N e^-t')
    ntot = sum(len(k) + 1 for _, k in lib) * len(C.SIGNS) * len(C.CHANNELS) * len(by_win)
    for j, t in enumerate(list(C.COUNT_AT) + [T]):
        L.append(f'   t = {t:7.3f}: observed {int(totals[j]):10d}   bound {ntot*math.exp(-t):.4g}')
    L.append(f'   cells searched: {ntot:,}')
    L.append('')
    confirmed, faults = recompute_tier1(tier1, wins, lib, names)
    L.append(f'4. TIER 1 (S_guard >= T): {len(tier1)} cells, {confirmed} of them reproduced by an independent recomputation')
    for f in faults:
        L.append(f'   NOT REPRODUCED (a stored value that does not come back is a fault, not a candidate; quarantine its task file and re-run it): {f}')
    for t in sorted(tier1, key=lambda x: -x[6])[:50]:
        L.append(f'   {t}')
    L.append('')
    L.append('5. Top tier-2 cell per channel and window with the highest scores (UNVERIFIED ranks)')
    for ch in C.CHANNELS:
        rows = sorted([r for r in tier2 if r[0] == ch], key=lambda r: -r[6])[:8]
        for r in rows:
            L.append(f'   {r[0]:6s} {r[2]:18s} {r[3][:36]:36s} sign {r[4]:2d} offset {r[5]:6d}  S_guard {r[6]:8.3f}  S {r[7]:8.3f}')
    (C.OUT / f'summary_{kind}.txt').write_text('\n'.join(L) + '\n', encoding='utf-8')
    with open(C.OUT / f'tier2_{kind}.tsv', 'w', encoding='utf-8', newline='\n') as f:
        f.write('channel\twindow\tname\tstream\tsign\toffset\tS_guard\tS\n')
        for r in tier2:
            f.write('\t'.join(str(x) for x in r) + '\n')
    print('\n'.join(L))


if __name__ == '__main__':
    main(sys.argv[1])
