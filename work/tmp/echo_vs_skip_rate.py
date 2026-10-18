# Is the lag-6 echo rate = the avoided-collision (skip) rate, section by section?
# Echo excess rate: (hits - expected)/pairs for within-word lag-6 pairs per section.
# Skip rate estimate: surviving doublets d, total adjacent pairs n: collision rate = d/(n*(1-q))
# with q = 0.81 enforcement -> avoided = collision rate - surviving = d/n * (q/(1-q)).
# Also: F-frequency at lag-6-eligible word positions in the SOLVED plaintext (F-story check).
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp

N = 29
Q = 0.81  # enforcement of the anti-repeat rule (coin model)
segs = lp.load_segments()

print("section  pairs  hits  expect  echo_excess_rate  dblts  adj_pairs  avoided_rate")
rows = []
for i in range(7, 16):
    toks = segs[i]
    runes = lp.runes_of(toks)
    spans = lp.word_spans(toks, runes)
    pairs, hits = 0, 0
    for _w, s, e in spans:
        for j in range(s, e - 6):
            pairs += 1
            if runes[j + 6] == (24 - 2 * runes[j]) % N:
                hits += 1
    dblts = sum(1 for j in range(len(runes) - 1) if runes[j] == runes[j + 1])
    avoid_rate = dblts / len(runes) * (Q / (1 - Q))
    if pairs:
        echo_rate = (hits - pairs / N) / pairs
        rows.append((echo_rate, avoid_rate))
        print(f"  {i:<4d} {pairs:5d} {hits:4d} {pairs/N:6.1f}  {echo_rate:+.4f}          {dblts:4d} {len(runes):6d}  {avoid_rate:.4f}")
    else:
        print(f"  {i:<4d} {pairs:5d} {hits:4d} {pairs/N:6.1f}  (no eligible pairs)    {dblts:4d} {len(runes):6d}  {avoid_rate:.4f}")

import statistics
er = [r[0] for r in rows]
ar = [r[1] for r in rows]
cov = sum((a - statistics.mean(er)) * (b - statistics.mean(ar)) for a, b in rows) / (len(rows) - 1)
sde = statistics.pstdev(er); sda = statistics.pstdev(ar)
print(f"\ncorr(echo_rate, avoided_rate) = {cov/(sde*sda):+.2f}  (n=9 sections)")
print(f"mean echo {statistics.mean(er):.4f} sd {sde:.4f}; mean avoided {statistics.mean(ar):.4f} sd {sda:.4f}")

# F-rate at lag-6-eligible word positions in the solved plaintext (keyed sections, decoded)
print("\nsolved plaintext F-rate at word positions >= 6 (lag-6-eligible targets):")
tot_f, tot_pos = 0, 0
for i in (1, 5, 16):  # Welcome, A Koan (FIRFUMFERENFE), An End - the keyed sections
    toks = segs[i]
    plain = lp.KNOWN[i][1](lp.runes_of(toks))
    spans = lp.word_spans(toks, plain)
    for _w, s, e in spans:
        for j in range(s + 6, e):
            tot_pos += 1
            if plain[j] == 0:
                tot_f += 1
print(f"  F at pos>=6: {tot_f}/{tot_pos} = {tot_f/tot_pos:.4f}  (overall English F ~0.022)")

# correct real-data null: An End (index 16), enciphered c = p + (prime-1) with literal F
print("\nAn End (seg 16) as real-data null:")
toks = segs[16]
runes = lp.runes_of(toks)
pairs6, hits6 = 0, 0
for _w, s, e in lp.word_spans(toks, runes):
    for j in range(s, e - 6):
        pairs6 += 1
        if runes[j + 6] == (24 - 2 * runes[j]) % N:
            hits6 += 1
r6 = [0] * N
for _w, s, e in lp.word_spans(toks, runes):
    for j in range(s, e - 6):
        r6[(runes[j + 6] + 2 * runes[j] - 24) % N] += 1
ch = sum((c - pairs6 / N) ** 2 / (pairs6 / N) for c in r6)
print(f"  within-word lag6 pairs={pairs6} hits={hits6} expected~{pairs6/N:.1f}  residual chi2={ch:.1f}")

