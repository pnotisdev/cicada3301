"""E4-letters: the E4 plants with the plaintext spelled letter by letter (TH -> T+H, ING -> I+N+G, EA -> E+A, ...).

    python e4_letters.py run [--workers N]     # one JSON per plant in results/chanscreen/e4_letters/ (resumable)
    python e4_letters.py summary               # results/chanscreen/e4_letters_summary/e4_summary.txt

Same plants, seeds, streams, offsets, frozen decoder / LM / thresholds as e4.py (PROTOCOL.md section E4); only the
held plaintext pools are expanded. Question (registry row open-e4-letters, phase 20 plan): does the frozen contract keep
its power when LP2's plaintext is letter-spelled, as its word lengths suggest (G 60 vs 242 for digraph spelling)?
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common as C  # noqa: E402
import e4  # noqa: E402

# GP index -> letter runes: TH, EO, ING, OE, AE, IA, EA (NG has no rune of its own in GP; ING does)
EXPAND = {2: (16, 8), 12: (18, 3), 21: (10, 9, 6), 22: (3, 18), 25: (24, 18), 27: (10, 24), 28: (18, 24)}


def letters(runes):
    out = []
    for r in runes:
        out.extend(EXPAND.get(int(r), (int(r),)))
    return out


_init_digraph = e4._init


def _init():
    _init_digraph()
    e4._G['pool'] = {s: letters(p) for s, p in e4._G['pool'].items()}


e4._init = _init
e4.DEST = C.OUT / 'e4_letters'
C.OUT = C.OUT / 'e4_letters_summary'   # summary files go here, never over the digraph E4 summary
C.OUT.mkdir(parents=True, exist_ok=True)
assert letters([2, 21, 5]) == [16, 8, 10, 9, 6, 5]

if __name__ == '__main__':
    if sys.argv[1] == 'run':
        w = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 4
        e4.run(w, False)
    else:
        e4.summary()
