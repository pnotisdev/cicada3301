"""Page-safe LP2 word-edge masks for the edge arc (phase 24). Word separators of the master are ' ' (word), '.' (clause) and '&' (paragraph);
line breaks '\n' and page marks '%' are TRANSPARENT: a word that wraps over a line or a page stays one word (32 of the 55 page marks of sections
0.7-0.15 sit inside a word). Numeral tokens ('#...') are transparent too. No ciphertext is scored here.

    python -B lp_mask.py        # self-check + counts, writes results/chanscreen/edge/lp_mask_check.json
"""
import json
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'step3'))
import common as C  # noqa: E402

SECS = (7, 8, 9, 11, 12, 13, 14, 15)
SEP = (' ', '.', '&')


def section_edges(sec):
    """returns (runes, brk) with brk[r] True iff a word separator lies between rune r-1 and rune r (brk[0] False)"""
    toks = C.lp.load_segments()[sec]
    runes, brk, sep = [], [], False
    for t in toks:
        if isinstance(t, int):
            brk.append(bool(runes) and sep)
            runes.append(t)
            sep = False
        elif t in SEP:
            sep = True
    return runes, brk


def window_masks(sec, start, n):
    """(cand_nullf, cand_initial) for the window runes[start:start+n]: word-final positions (a separator follows the rune, including the rune
    n-1 when the next rune starts a new word) and word-initial positions i >= 1"""
    runes, brk = section_edges(sec)
    nxt = brk + [True]          # a separator after the section's last rune
    final = [1 if nxt[start + i + 1] else 0 for i in range(n)]
    initial = [1 if (i >= 1 and brk[start + i]) else 0 for i in range(n)]
    return final, initial


def check():
    out = {}
    segs = C.lp.load_segments()
    for sec in SECS:
        runes, brk = section_edges(sec)
        toks = segs[sec]
        pages_inside = pages = 0
        last_rune = False
        # page marks with a rune on both sides and no separator between
        idx = [i for i, t in enumerate(toks) if t == '%']
        for i in idx:
            pages += 1
            left = next((j for j in range(i - 1, -1, -1) if isinstance(toks[j], int) or toks[j] in SEP), None)
            right = next((j for j in range(i + 1, len(toks)) if isinstance(toks[j], int) or toks[j] in SEP), None)
            if left is not None and right is not None and isinstance(toks[left], int) and isinstance(toks[right], int):
                pages_inside += 1
        out[sec] = dict(runes=len(runes), words=sum(brk) + 1, page_marks=pages, page_marks_inside_words=pages_inside)
    return out


if __name__ == '__main__':
    o = check()
    for s, d in o.items():
        print(s, d)
    print('total page marks', sum(d['page_marks'] for d in o.values()), 'inside words', sum(d['page_marks_inside_words'] for d in o.values()))
    f, i = window_masks(9, 0, 300)
    print('window 0.9@0: word-final', sum(f), 'word-initial', sum(i))
    outd = C.OUT / 'edge'; outd.mkdir(parents=True, exist_ok=True)
    (outd / 'lp_mask_check.json').write_text(json.dumps(o, indent=1))
