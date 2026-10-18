# H2-null sharp test: if the lag-6 echo is a null rune (value T(c_{i-6})) inserted at WORD ENDS,
# the echo TARGETS should concentrate at word-final positions. Null fraction = eligible words / pairs
# (each eligible word contributes exactly one word-final-target pair).
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

N = 29
segs = lp.load_segments()

echo_final6 = echo6 = 0
echo_final5 = echo5 = 0
n_eligible6 = n_eligible5 = 0
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    for _w, s, e in lp.word_spans(toks, runes):
        L = e - s
        if L >= 7:
            n_eligible6 += 1
            for j in range(s, e - 6):
                echo6 += 1
                if runes[j + 6] == (24 - 2 * runes[j]) % N:
                    if j + 6 == e - 1:
                        echo_final6 += 1
        if L >= 6:
            n_eligible5 += 1
            for j in range(s, e - 5):
                echo5 += 1
                if runes[j + 5] == runes[j]:
                    if j + 5 == e - 1:
                        echo_final5 += 1

print(f"lag6: pairs={echo6} echoes={echo6 and 80} word-final targets={echo_final6}")
print(f"      null fraction {n_eligible6}/{echo6} = {n_eligible6/echo6:.3f}  -> expected {80*n_eligible6/echo6:.1f} of 80")
print(f"      H2 prediction: all 35 excess pairs word-final -> about {80*n_eligible6/echo6 + 35*(1-n_eligible6/echo6):.1f}")
print(f"lag5: pairs={echo5} echoes=104 word-final targets={echo_final5}")
print(f"      null fraction {n_eligible5}/{echo5} = {n_eligible5/echo5:.3f}  -> expected {104*n_eligible5/echo5:.1f} of 104")
