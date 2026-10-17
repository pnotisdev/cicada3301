import sys
sys.path.insert(0, ".")
import attack, lp, stats
toks = stats.SEGS[7]
words, cur = [], []
for t in toks:
    if isinstance(t, int):
        cur.append(t)
    elif t in (" ", ".", "\n", "&", "%") and cur:
        words.append(cur); cur = []
if cur: words.append(cur)
print(len(words), "words;", sum(map(len, words)), "runes")
print([len(w) for w in words[:50]])
print([[lp.LATIN[x] for x in w] for w in words[:6]])
phrase = "FIND YOU ARE NECESSARILY ALONE WHEN YOU ARE BORN AND CANNOT COMMUNICATE IT IN ANY WAY FOREVER AFTER REMEMBER TO THINK OF ALL YOU VALUE IN ONE WORD JUST RECITE YOUR ANSWER NOW".split()
print(len(phrase))
print([len(attack.rune_spellings(w)) for w in phrase])
for w in phrase[:4]: print(w, attack.rune_spellings(w))
print(attack.SINGLE)
