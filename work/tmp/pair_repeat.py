# Are repeated ADJACENT word-pairs rare in LP2? DJU-BEI is one such pair (twice: 0.13:28, 0.15:3310 = book end).
import sys, os, random
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

segs = lp.load_segments()
sections = []
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    sections.append([w for w, s, e in lp.word_spans(toks, runes)])

def pair_counts(secs):
    pairs = {}
    for si, words in enumerate(secs):
        for n in range(len(words) - 1):
            p = (words[n], words[n + 1])
            pairs.setdefault(p, []).append((si, n))
    return pairs

pairs = pair_counts(sections)
rep = {p: v for p, v in pairs.items() if len(v) >= 2}
print(f"total words {sum(len(s) for s in sections)}, adjacent pairs {sum(len(s)-1 for s in sections)}")
print(f"repeated adjacent pairs (>= 2 occurrences): {len(rep)}")
for p, v in sorted(rep.items(), key=lambda kv: -len(kv[1])):
    print(f"  {p[0]}->{p[1]} x{len(v)} at {v}")

# null: shuffle words within sections, 1000 replicates
rng = random.Random(42)
n_rep = []
max_m = []
max_len_word = []
dju_pair_counts = []
for _ in range(1000):
    sh = [rng.sample(w, len(w)) for w in sections]
    pc = pair_counts(sh)
    rp = [v for p, v in pc.items() if len(v) >= 2]
    n_rep.append(len(rp))
    max_m.append(max((len(v) for v in rp), default=0))
    max_len_word.append(max((len(p[0]) for p, v in pc.items() if len(v) >= 2), default=0))
    dju_pair_counts.append(len(pc.get(("DJU", "BEI"), [])))
obs_rep = len(rep)
obs_max = max((len(v) for v in rep.values()), default=0)
print(f"\nnull (1000 word shuffles within sections):")
print(f"  number of repeated pairs: mean {sum(n_rep)/1000:.1f}, P(>= {obs_rep}) = {sum(1 for x in n_rep if x >= obs_rep)/1000:.3f}")
print(f"  max occurrences per pair: mean {sum(max_m)/1000:.2f}, P(>= {obs_max}) = {sum(1 for x in max_m if x >= obs_max)/1000:.3f}")
print(f"  P(any pair has both words >= 5 letters): {sum(1 for x in max_len_word if x >= 5)/1000:.3f}  (observed: {max((len(p[0]) for p in rep), default=0)})")
print(f"  DJU->BEI pairs in shuffled books: mean {sum(dju_pair_counts)/1000:.3f}, P(>= 2) = {sum(1 for x in dju_pair_counts if x >= 2)/1000:.3f}")
