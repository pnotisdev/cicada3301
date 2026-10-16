# Phase 4 screen 2 – every key start offset, number keystreams, page-30 grid and caption (2026-10-16)

**Result: negative.** No keystream scored above the random controls at any start offset.

## Setup
- Same cipher model as screen 1: c = t + s*(k_j + b), t = p or 28−p, s = ±1, b = 0..28, collision-skip rule.
- `attack.fast_screen_batch` slides the key start in steps of 12 over the whole sequence (offsets 0 to about 19,670).
  The fast screen's 24-position shift window covers the positions between steps and leaves room for skips.
  Periodic sequences were slid over one period.
- First 300 runes of segments 0.7, 0.8, 0.9 and 0.11–0.15, with sign ±1, Atbash on or off, and all 29 values of b.
- 26 long sequences × 1,640 offsets and 54 periodic sequences, plus 4 random controls given the same
  full slide.
- New key material from the page-30 grid. Its first 12 numbers are 3301 − p for the primes
  43, 79, 149, 263, 23, 2, 3, 463, 13, 7, 5, 829. The caption ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ has word Gematria sums 149 and 489, and
  149 is one of those primes. Keys tried: the grid primes in grid order and sorted, the grid's first 12 numbers,
  its last row, the caption's sums, the caption's runes and the caption's prime values.
- Sensitivity: φ(n) planted at offset 17,001 with b = 19 and sign −1 was found at the right offset and b,
  scoring 0.73. The next-best offset scored 0.199.

## Scores
- Random controls (full slide): max 0.208
- Best real keystream: 0.205 (pi digits base 29). The top 15 under the exact decoder scored
  0.106–0.139, which is wrong-key level (a real key scores about 0.7). Their A/I rates were 0.00–0.25, which is chance.
- Per keystream (best fast-screen score over all offsets, segments and variants):
  - pi digits (base 29): 0.205 (1640 offsets)
  - ln2 digits (base 29): 0.204 (1640 offsets)
  - e digits (base 29): 0.203 (1640 offsets)
  - prime index of primes: 0.202 (1640 offsets)
  - composites: 0.202 (1640 offsets)
  - sigma(n): 0.200 (1640 offsets)
  - pi digits (base 10): 0.199 (1640 offsets)
  - primes: 0.199 (1640 offsets)
  - primes-1 (totient): 0.199 (1640 offsets)
  - primes+1: 0.199 (1640 offsets)
  - emirps: 0.199 (1640 offsets)
  - prime gaps: 0.198 (1640 offsets)
  - primes from 3301: 0.198 (1640 offsets)
  - sqrt3 digits (base 10): 0.198 (1640 offsets)
  - phi digits (base 29): 0.197 (1640 offsets)
  - phi(n): 0.197 (1640 offsets)
  - cumulative phi(n): 0.196 (1640 offsets)
  - d(n): 0.196 (1640 offsets)
  - primes^2: 0.196 (1640 offsets)
  - sqrt2 digits (base 29): 0.195 (1640 offsets)
  - ln2 digits (base 10): 0.194 (1640 offsets)
  - sqrt3 digits (base 29): 0.194 (1640 offsets)
  - e digits (base 10): 0.193 (1640 offsets)
  - 21^n mod 29: 0.193 (4 offsets)
  - sqrt2 digits (base 10): 0.193 (1640 offsets)
  - cumulative prime sum: 0.192 (1640 offsets)
  - phi digits (base 10): 0.191 (1640 offsets)
  - 19^n mod 29: 0.189 (4 offsets)
  - 11^n mod 29: 0.183 (4 offsets)
  - page-14 square cols: 0.182 (4 offsets)
  - 3301^n: 0.180 (2 offsets)
  - An End hash nibbles: 0.179 (12 offsets)
  - 23^n mod 29: 0.179 (2 offsets)
  - 15^n mod 29: 0.178 (4 offsets)
  - 8^n mod 29: 0.178 (4 offsets)
  - page-30 grid primes sorted: 0.177 (2 offsets)
  - 13^n mod 29: 0.177 (3 offsets)
  - page-30 grid rows: 0.177 (3 offsets)
  - 1033*n: 0.177 (4 offsets)
  - 27^n mod 29: 0.176 (4 offsets)
  - 3^n mod 29: 0.176 (4 offsets)
  - 14^n mod 29: 0.174 (4 offsets)
  - 16^n mod 29: 0.174 (2 offsets)
  - 24^n mod 29: 0.174 (2 offsets)
  - triangular: 0.174 (4 offsets)
  - page-30 grid cols: 0.174 (3 offsets)
  - 18^n mod 29: 0.174 (4 offsets)
  - 20^n mod 29: 0.173 (2 offsets)
  - page-30 grid primes (3301-x): 0.173 (2 offsets)
  - page-30 grid first 12: 0.173 (2 offsets)
  - 10^n mod 29: 0.173 (4 offsets)
  - 17^n mod 29: 0.173 (2 offsets)
  - 2^n mod 29: 0.173 (4 offsets)
  - 4^n mod 29: 0.172 (3 offsets)
  - 25^n mod 29: 0.172 (2 offsets)
  - 9^n mod 29: 0.172 (3 offsets)
  - gematria primes cycle: 0.172 (4 offsets)
  - page-14 square rows: 0.172 (4 offsets)
  - n^3: 0.172 (4 offsets)
  - An End hash bytes: 0.171 (7 offsets)
  - 22^n mod 29: 0.171 (3 offsets)
  - n^2: 0.170 (4 offsets)
  - lucas: 0.170 (3 offsets)
  - fibonacci: 0.169 (3 offsets)
  - 5^n mod 29: 0.169 (3 offsets)
  - pell: 0.168 (3 offsets)
  - 26^n mod 29: 0.168 (4 offsets)
  - 1033 square rows: 0.167 (4 offsets)
  - caption 0.10 prime values: 0.167 (2 offsets)
  - 6^n mod 29: 0.167 (3 offsets)
  - 7^n mod 29: 0.165 (2 offsets)
  - caption 0.10 runes: 0.165 (2 offsets)
  - 3301 digits: 0.162 (2 offsets)
  - n: 0.161 (4 offsets)
  - page-30 last row: 0.161 (2 offsets)
  - 12^n mod 29: 0.158 (2 offsets)
  - 3301*n: 0.156 (4 offsets)
  - 1033 digits: 0.154 (2 offsets)
  - caption 0.10 gematria sums: 0.126 (2 offsets)
  - 28^n mod 29: 0.122 (2 offsets)

## Conclusion
None of these number sequences, at any start position, combined with any constant shift, sign or Atbash and the
collision-skip rule, produces English in the first 300 runes of any unsolved segment. The page-30 grid numbers and
the caption do not work as direct keystreams either. The grid's 3301 − prime structure is real, but its role is
still unknown.

Raw results: `work/tmp/phase4/screen_sliding.json` (top 40 per keystream).
