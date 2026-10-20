"""Alias-tail measurement on the laptop smoke plants (scratch, 2026-10-20). Regenerates four smoke plants from their seeds and
reports, for the decoder that reads them best, the signed distance of every cell above 10 nats from the true offset and the
slope of S_guard against distance. Also lists, for all 16 smoke records, the winners that sit at another offset.
  python -B work/tmp/laptop_e4_smoke/alias_tail.py
"""
import sys
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import json
import numpy as np
import e4_smoke as E

print('winners at another offset (record, true offset, winner offset, true G, winner G, difference)')
for f in sorted((HERE / 'records').glob('*.json')):
    r = json.loads(f.read_text())
    w = r['winner']
    if w['offset'] != r['off']:
        print(f"  {r['channel']:5} {r['index']:2} {r['off']:6} {w['offset']:6} {r['true']['G']:.6f} {w['G']:.6f} {w['G'] - r['true']['G']:+.2e}  copies {r['n_copies']}")

print('\ntail of cells >= 10 nats around the true offset (signed distance d = offset - true offset)')
for ch, idx in (('hold', 1), ('hold', 12), ('hold', 13), ('spend', 12)):
    p = E.make_plant('e4-smoke', ch, idx)
    for dec, sign, S, g in E.all_passes(p):
        if dec == 'hold' and sign == p['sign']:
            d = np.arange(len(g)) - p['off']
            m = (g >= 10) & (d != 0)
            ds = d[m]
            pos = d[(d > 0) & (d <= 40) & np.isfinite(g)]
            slope = np.polyfit(pos, g[p['off'] + pos], 1)[0] if len(pos) > 3 else float('nan')
            print(f"  {ch:5} {idx:2} sign {p['sign']:+d} m {p['m']} S_true {g[p['off']]:.1f}: {m.sum()} cells >= 10, d from {ds.min()} to {ds.max()}, "
                  f"{int((ds > 0).sum())} ahead / {int((ds < 0).sum())} behind, slope of S_guard over d = 1..40: {slope:.2f} nats per offset")
