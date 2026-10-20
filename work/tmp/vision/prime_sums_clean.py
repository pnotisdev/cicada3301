"""Scouting (2026-10-19): Gematria sums of the solved plaintext's sentences. Clean units: split at '.' and at paragraph
breaks '&' only (a page break does not end a sentence); labels (headings such as A KOAN, SOME WISDOM, AN INSTRUCTION)
reported separately. Reports odd / prime / prime-given-odd against a shuffle null that keeps unit lengths. Own code."""
import os, sys, random
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..")); sys.path.insert(0, os.path.join(HERE, "..", ".."))
import lp
def sieve(n):
    s = bytearray([1]) * (n + 1); s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]: s[i * i::i] = bytearray(len(s[i * i::i]))
    return s
IS_P = sieve(300000)
random.seed(1033)
LABELS = {"AWARNING", "WELCOME", "WIDSOM", "SOMEWISDOM", "ACOAN", "ANINSTRUCTIAN", "THELOSSOFDIUINITY", "ANEND", "PARABLE",
          "CONSUMPTIAN", "PRESERUATIAN", "ADHERENCE", "CNOWTHIS", "DAGAIN", "WH"}
segs = lp.load_segments()
rows = []
for i, (title, fn) in lp.KNOWN.items():
    toks = segs[i]; plain = fn(lp.runes_of(toks)); it = iter(plain)
    cur, units = [], []
    for t in toks:
        if isinstance(t, int): cur.append(next(it))
        elif t in (".", "&"):
            if cur: units.append(cur); cur = []
    if cur: units.append(cur)
    for u in units:
        s = sum(lp.PRIME[j] for j in u)
        lab = "".join(lp.LATIN[j] for j in u)
        rows.append((i, len(u), s, lab, lab in LABELS, [j for j in u]))
body = [r for r in rows if not r[4] and r[1] >= 6 and r[3] != "SHADOWSAETHEREALBUFFERSUOIDCARNALOBSCURAFORMMOBIUSANALOGUOIDMOURNFULAETHEREAL"]
print("units total", len(rows), " body units (not labels, >=6 runes, not the word square):", len(body))
def stats(sel, name):
    n = len(sel); odd = sum(r[2] % 2 for r in sel); pr = sum(IS_P[r[2]] for r in sel)
    print(f"{name:34s} n={n:3d}  odd={odd:3d} ({100*odd/n:4.1f}%)  prime={pr:3d} ({100*pr/n:4.1f}%)  prime|odd={pr}/{odd}={100*pr/max(1,odd):4.1f}%")
stats(body, "all body sentences")
short = [r for r in body if r[1] <= 40]; long_ = [r for r in body if r[1] > 40]
stats(short, "short (<=40 runes)"); stats(long_, "long (>40 runes)")
for i in sorted({r[0] for r in body}):
    stats([r for r in body if r[0] == i], f"  section 0.{i}")
# null: same lengths, runes shuffled within the section
pooled_mu = pooled_var = 0.0; oddmu = oddvar = 0.0
for i in sorted({r[0] for r in body}):
    sel = [r for r in body if r[0] == i]
    plain = lp.KNOWN[i][1](lp.runes_of(segs[i]))
    lens = [r[1] for r in sel]; pool = list(plain); P = []; O = []
    for _ in range(500):
        random.shuffle(pool); p = 0; o = 0; k = 0
        for L in lens:
            s = sum(lp.PRIME[j] for j in pool[k:k + L]); k += L; p += IS_P[s]; o += s % 2
        P.append(p); O.append(o)
    mu = sum(P) / len(P); pooled_mu += mu; pooled_var += sum((x - mu) ** 2 for x in P) / len(P)
    mo = sum(O) / len(O); oddmu += mo; oddvar += sum((x - mo) ** 2 for x in O) / len(O)
n = len(body); obs = sum(IS_P[r[2]] for r in body); oo = sum(r[2] % 2 for r in body)
print(f"prime: observed {obs}/{n}, null {pooled_mu:.1f} +- {pooled_var**.5:.1f}  z = {(obs-pooled_mu)/pooled_var**.5:.1f}")
print(f"odd:   observed {oo}/{n}, null {oddmu:.1f} +- {oddvar**.5:.1f}  z = {(oo-oddmu)/oddvar**.5:.1f}")
print("labels (headings) prime rate:", sum(IS_P[r[2]] for r in rows if r[4]), "of", sum(1 for r in rows if r[4]))
