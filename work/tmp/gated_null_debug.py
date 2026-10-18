"""Quick diagnostic: why do far offsets differ between plant A (with nulls) and
plant B (no nulls)?  Reads the gate module's functions (my own code)."""
import sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "work"))
import gated_null_gate as G

k = G.totient_key(G.KEY_LEN)
UNI = G.emerson_unigram_logs()
plain300, spans300 = G.window_spans(300)
A = G.plant(plain300, spans300, k, G.TRUE_OFFSET, G.NULL_RATE, "echo", G.SEED_PLANT)
B = G.plant(plain300, spans300, k, G.TRUE_OFFSET, 0.0, "echo", G.SEED_PLANT)

print("plant A: n=%d, nulls at %s, redraws at %s" % (len(A["c"]), A["nulls"][:14], A["redraws"][:14]))
print("plant B: n=%d, redraws at %s" % (len(B["c"]), B["redraws"][:14]))

def S(pl, o, qn, q=G.SKIP_Q):
    return G.forward(pl["c"], pl["starts"], k, o, 1, False, qn, False, q=q,
                     logs=UNI)["score_nats"]

for o in (0, 1, 2, 3):
    print("B o%d: qn=0.028 -> %.2f | qn=0 -> %.2f | qn=0.028,decoder-q=0 -> %.2f"
          % (o, S(B, o, 0.028), S(B, o, 0.0), S(B, o, 0.028, q=0.0)))
for o in (0, 1):
    print("A o%d: qn=0.028 -> %.2f | qn=0 -> %.2f" % (o, S(A, o, 0.028), S(A, o, 0.0)))

# Viterbi letters for B at o0 with null freedom vs true plaintext
v = G.viterbi(B["c"], B["starts"], k, 0, 1, False, 0.028, False, logs=UNI)
print("B@o0 viterbi letters (first 60): " + "".join(G.lp.LATIN[p] if p is not None else "." for p in v["aligned"][:60]))
print("B true plaintext (first 60):      " + "".join(G.lp.LATIN[p] for p in plain300[:60]))
# expected shifted reading for B@o0: p_i + k[i]-k[3+i]
shifted = [(p + k[i] - k[G.TRUE_OFFSET + i]) % 29 for i, p in enumerate(plain300[:60])]
print("B@o0 3-gap reading (first 60):    " + "".join(G.lp.LATIN[p] for p in shifted))
# compare viterbi vs shifted
agree = sum(a == s for a, s in zip(v["aligned"][:60], shifted))
print("viterbi letters equal 3-gap reading in first 60: %d/60" % agree)
# does the viterbi place nulls?
print("B@o0 viterbi nulls:", [i for i, e in enumerate(v["aligned"]) if e is None][:20])
