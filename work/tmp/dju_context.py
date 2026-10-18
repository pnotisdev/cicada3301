# Where are the two DJU-BEI occurrences, and what surrounds them?
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

segs = lp.load_segments()
target = [23, 11, 1, 17, 18, 10]  # D J U B E I
print("occurrences of DJU-BEI:")
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    for j in range(len(runes) - 5):
        if runes[j:j + 6] == target:
            # find the word containing it
            word_info = None
            for w, s, e in lp.word_spans(toks, runes):
                if s <= j and j + 6 <= e:
                    word_info = (w, s, e)
                    break
            ctx = "".join(lp.LATIN[x] for x in runes[max(0, j - 10):j + 16])
            word, s, e = word_info if word_info else ("?", j, j + 6)
            print(f"  sec 0.{i} rune_pos {j} word={word} (word_pos {j}-{s}..{j+6}-{s} of {e-s})")
            print(f"    context: ...{ctx}...")
# how many words in total, and any other 6-gram repeats at word starts?
print(f"\n(all LP2 words: {sum(1 for i in range(7,16) for _ in lp.word_spans(segs[i], lp.runes_of(segs[i])))})")
