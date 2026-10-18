# Sharp test of the collision-twist mechanism W3(a): "at a would-be doublet, write T(previous rune)".
# Then a lag-6 echo pair (i-6, i) with c_i = T(c_{i-6}) implies T(c_{i-1}) = T(c_{i-6})
# i.e. c_{i-1} = c_{i-6} (T is a bijection). So the rune right before an echo equals the rune 6 back.
# Null: 1/29 of pairs. W3(a): ~all.
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

N = 29
segs = lp.load_segments()
runes_all = []
spans_all = []
sec_of = []
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    off = len(runes_all)
    runes_all += runes
    for _w, s, e in lp.word_spans(toks, runes):
        spans_all.append((s + off, e + off, i))
    sec_of += [i] * len(runes)

# all within-word lag-6 pairs
lag6 = []
for s, e, i in spans_all:
    for j in range(s, e - 6):
        lag6.append(j)
echo = [j for j in lag6 if runes_all[j + 6] == (24 - 2 * runes_all[j]) % N]
pre_eq = [j for j in echo if runes_all[j + 5] == runes_all[j]]
print(f"lag6 pairs={len(lag6)} echoes={len(echo)}")
print(f"echoes with c[i-1] == c[i-6]: {len(pre_eq)}/{len(echo)}  (null ~ {len(echo)/N:.1f}, W3(a) ~ {len(echo)})")
p = sum(1 for j in lag6 if runes_all[j + 5] == runes_all[j])
print(f"all pairs with c[i-1]==c[i-6]: {p}/{len(lag6)} = {p/len(lag6):.4f} (null 1/29 = 0.0345)")

# converse: for lag-5 equality pairs (j, j+5), how many have c[j+6] == T(c[j])? (null 1/29; W3(a) ~ collision rate 2.8%)
lag5 = []
for s, e, i in spans_all:
    for j in range(s, e - 5):
        lag5.append(j)
eq5 = [j for j in lag5 if runes_all[j + 5] == runes_all[j]]
echo_after = [j for j in eq5 if j + 6 < len(runes_all) and runes_all[j + 6] == (24 - 2 * runes_all[j]) % N and sec_of[j + 6] == sec_of[j] and any(s <= j + 6 < e for s, e, _ in spans_all)]
print(f"\nlag5 equality pairs={len(eq5)}; of these, c[j+6]==T(c[j]) in-word: {len(echo_after)} ({len(echo_after)/max(len(eq5),1):.4f}; null 1/29=0.0345, W3(a) ~0.028)")

# the S pairs: how many S,S lag-5 pairs have a lag-6 echo following? and do S pairs sit before echoes?
ss = [j for j in eq5 if runes_all[j] == 15]
ss_echo = [j for j in ss if j + 6 < len(runes_all) and runes_all[j + 6] == (24 - 2 * runes_all[j]) % N and sec_of[j + 6] == sec_of[j] and any(s <= j + 6 < e for s, e, _ in spans_all)]
print(f"S,S lag5 pairs={len(ss)}; with following lag-6 echo: {len(ss_echo)}")

# where are echo targets: distance to the nearest surviving doublet?
dblts = [j for j in range(len(runes_all) - 1) if runes_all[j] == runes_all[j + 1]]
import bisect
near = 0
for j in echo:
    pos = bisect.bisect_left(dblts, j)
    d = min(abs(dblts[pos] - j) if pos < len(dblts) else 10**9,
            abs(dblts[pos - 1] - j) if pos > 0 else 10**9)
    if d <= 3:
        near += 1
print(f"\necho targets within 3 runes of a surviving doublet: {near}/{len(echo)}")
