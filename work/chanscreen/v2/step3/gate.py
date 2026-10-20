"""E3b gate: the five iid-key null windows searched against the full bank must all stay below T300.

    python gate.py        # writes results/chanscreen/e3b_gate.json (status PASS or FAIL); campaign.py refuses n300 / clause without PASS
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402


def main():
    wins = C.windows('null2')
    n_chunks = len(C.chunks([len(k) for _, k in C.read_library()]))
    maxima = []
    present = 0
    for wi in range(len(wins)):
        m = -np.inf
        for ci in range(n_chunks):
            p = C.OUT / 'null2' / f'w{wi:03d}_c{ci:02d}.npz'
            if p.exists():
                present += 1
                m = max(m, float(np.max(np.load(p)['res'][:, :, 0])))
        maxima.append(m)
    ok = present == len(wins) * n_chunks and all(m < C.T300 for m in maxima)
    out = dict(status='PASS' if ok else 'FAIL', tasks_present=present, tasks_expected=len(wins) * n_chunks, T300=C.T300,
               records=list(C.NULL_RECORDS2), max_S_guard=maxima)
    (C.OUT / 'e3b_gate.json').write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
