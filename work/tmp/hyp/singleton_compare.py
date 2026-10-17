"""Compare our one-rune words in LP2 with the cicadanotebook.com Session 43 inventory (83 tokens: 68 listed with page / rune offset
for their sections 0-7 = our 0.7-0.14, plus 15 in their section 8 = our 0.15 from Session 42). Their list is data copied from
their evidence file singleton43_observations.json (page, offset within the page, label); nothing of theirs is run.

    python work/tmp/hyp/singleton_compare.py
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, WORK)
import lp  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")

THEIRS = """0,176,EA 0,244,S 1,88,N 2,2,U 2,116,F 3,63,ING 4,21,H 4,79,W 4,116,TH 5,43,IO 5,109,Y 6,75,M 7,148,H 9,19,I 9,246,O
10,31,I 10,79,N 10,169,G 10,262,I 12,69,X 12,162,Y 13,28,U 13,81,W 13,153,J 15,135,Y 16,21,D 16,119,N 16,244,I 17,113,B 17,119,EA
17,147,I 17,188,T 17,204,R 18,56,T 18,172,P 19,71,W 19,137,R 19,189,TH 19,232,B 21,151,EA 21,217,AE 21,234,N 23,129,A 23,193,D
24,257,T 25,2,G 25,267,Y 27,36,P 28,32,ING 28,163,S 28,229,J 28,233,M 29,102,O 29,155,M 30,4,M 30,173,L 30,215,H 31,113,J 31,211,P
33,138,P 34,104,D 34,153,OE 35,124,R 35,243,W 37,128,E 38,74,EO 39,2,TH 39,155,H"""

LATIN_ALIASES = {"IO": "IA"}


def ours():
    """[(lp2_page, offset_in_page, latin, segment)] for every one-rune word of segments 0.7-0.15. A bare line break is a wrap;
    a page break ends a word, as lp.word_spans did until the 2026-10-17 correction, so the extras show where the two differ."""
    with open(lp.MASTER, encoding="utf-8") as f:
        body = f.read().split("\n\n", 1)[1].split("§")[0]
    page = seg = off = 0
    first_page = None
    out, cur = [], []

    def flush():
        if len(cur) == 1 and 7 <= cur[0][3] <= 15:
            out.append(cur[0])
        cur.clear()

    for ch in body:
        if ch in lp.RUNE_IDX:
            if seg == 7 and first_page is None:
                first_page = page
            cur.append((page, off, lp.LATIN[lp.RUNE_IDX[ch]], seg))
            off += 1
        elif ch in "-.&$%" or ch.isalnum():             # word, clause, paragraph, segment, page marks and inline numerals
            flush()
            if ch == "%":
                page += 1
                off = 0
            elif ch == "$":
                seg += 1
        # anything else ('/' line ends, the file's newlines) is a wrap inside a word, as in lp.word_spans
    flush()
    return [(p - first_page, o, lat, s) for p, o, lat, s in out]


def main():
    mine = ours()
    print(f"ours: {len(mine)} one-rune words in 0.7-0.15; by segment:",
          {s: sum(1 for x in mine if x[3] == s) for s in range(7, 16)})
    theirs = {}
    for tok in THEIRS.split():
        p, o, lab = tok.split(",")
        theirs[(int(p), int(o))] = LATIN_ALIASES.get(lab, lab)
    mine_0_14 = {(p, o): lat for p, o, lat, s in mine if s <= 14}
    both = set(theirs) & set(mine_0_14)
    only_ours = sorted(set(mine_0_14) - set(theirs))
    only_theirs = sorted(set(theirs) - set(mine_0_14))
    print(f"segments 0.7-0.14: ours {len(mine_0_14)}, theirs {len(theirs)}, same position {len(both)}, "
          f"label agreement {sum(theirs[k] == mine_0_14[k] for k in both)}/{len(both)}")
    print("only ours (page, offset, rune):", [(p, o, mine_0_14[(p, o)]) for p, o in only_ours])
    print("only theirs:", [(p, o, theirs[(p, o)]) for p, o in only_theirs])
    print(f"segment 0.15: ours {sum(1 for x in mine if x[3] == 15)}, theirs 15 (their Session 42)")


if __name__ == "__main__":
    main()
