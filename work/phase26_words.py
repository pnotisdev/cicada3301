"""Phase 26 helpers: rune-word lengths of LP segments (words split at word/clause/paragraph marks; line and page breaks do not split)."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp

def words(toks):
    out, cur = [], []
    for t in toks:
        if isinstance(t, int):
            cur.append(t)
        elif t in (" ", ".", "&") or t.startswith("#"):
            if cur: out.append(cur); cur = []
    if cur: out.append(cur)
    return out

def seg_words(segs, i):
    return words(segs[i])
