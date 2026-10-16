"""Red (title) text on the unsolved pages, from the OCR colour channel.

For every transcription line whose glyph count matches the image line, the red flag of each glyph
is copied onto the transcription rune. Contiguous red runs are titles / headings; they are natural
key-restart points and crib positions.

    python red_runs.py
"""
import json
import os
import sys

import lp
import ocr
import stats

HERE = os.path.dirname(os.path.abspath(__file__))


def page_seg_offsets():
    """page -> (segment, rune index of the page's first rune within its segment)."""
    body = open(lp.MASTER, encoding="utf-8").read().split("\n\n", 1)[1].split("§")[0]
    pages = body.split("%")
    seg, pos, out = 0, 0, {}
    for p, pg in enumerate(pages):
        # a segment break ($) may sit at the start or end of the page text
        head = pg.split("$")
        if len(head) > 1 and not any(c in lp.RUNE_IDX for c in head[0]):
            seg += pg.count("$")
            pos = 0
            out[p] = (seg, pos)
            pos += sum(c in lp.RUNE_IDX for c in pg)
            continue
        out[p] = (seg, pos)
        for part_i, part in enumerate(head):
            if part_i > 0:
                seg += 1
                pos = 0
            pos += sum(c in lp.RUNE_IDX for c in part)
    return out


def red_runs(pages=range(15, 71)):
    mp = ocr.master_pages()
    offs = page_seg_offsets()
    runs, covered, total = [], 0, 0
    for p in pages:
        ml = mp[p]
        if not ml:
            continue
        dl, H, _ = ocr.segment(ocr.image_of(p))
        pairs = ocr.align_lines(ml, dl)
        seg, base = offs[p]
        line_start = base
        starts = []
        for line in ml:
            starts.append(line_start)
            line_start += len(line)
        for mi, di in pairs:
            if mi is None:
                continue
            total += len(ml[mi])
            if di is None or len(ml[mi]) != len(dl[di]):
                continue
            covered += len(ml[mi])
            flags = [g.red for g in dl[di]]
            cur = []
            for k, (r, f) in enumerate(zip(ml[mi], flags)):
                if f:
                    cur.append((starts[mi] + k, r))
                elif cur:
                    runs.append((p, seg, cur))
                    cur = []
            if cur:
                runs.append((p, seg, cur))
        print(f"page {p}", end="\r", flush=True)
    return runs, covered, total


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    runs, cov, tot = red_runs()
    print(f"\nlines with matching glyph counts cover {cov}/{tot} runes")
    out = []
    for p, seg, cur in runs:
        pos = [a for a, _ in cur]
        rs = [r for _, r in cur]
        txt = "".join(lp.GP[r][0] for r in rs)
        print(f"page {p:2d} seg 0.{seg:<2} runes {pos[0]:5d}-{pos[-1]:5d} ({len(rs):3d}): {txt}")
        out.append({"page": p, "seg": seg, "start": pos[0], "end": pos[-1], "runes": rs})
    with open(os.path.join(HERE, "tmp", "phase4", "red_runs.json"), "w", encoding="utf-8") as f:
        json.dump(out, f)
