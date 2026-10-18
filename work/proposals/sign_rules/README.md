# sign_rules — +/- sign of the key per word, from word-level numbers (112 rules)

**Hypothesis.** "their numbers are the direction" (2016 hint) and "EITHER THE WORDS OR THEIR
NUMBERS" (0.0): the key's sign (or the pointer's direction) flips per word according to a rule
computed from word-level numbers in the transcription — word length, Gematria sum, rune-index
sum, first/last rune, word position, clause position. This is the merged plan's word-pointer
family ([2] + the 112-rule enumeration).

**The 112 rules** (exact enumeration, both orientations included):

| Template | Count |
|---|---|
| A parity of q (even -> +1) | 10 quantities x 2 = 20 |
| B (q mod p) <= (p-1)/2, p in {3,5,7} on all quantities; p=29 on G and R | 60 + 4 = 64 |
| C q_w > q_{w-1} (change from previous word) on 9 quantities | 9 x 2 = 18 |
| D first vs last rune: l > f, L > F | 2 x 2 = 4 |
| E word length n >= t, t in {3,4,5} | 3 x 2 = 6 |

Quantities: n (length), G (GP prime sum), R (rune-index sum), f/l (first/last index), F/L
(first/last GP prime), w (word index in section), wp (word index on page), ws (word index in
clause). Excluded as degenerate: w_w - w_{w-1} = 1; G >= 1033 / G >= 3301 (max LP2 word sum
is 933).

**What this gate does.**

1. Plants a text with a key whose sign flips per word by ONE randomly chosen rule
   (totient stream, anti-repeat skip), sign applied to the key value: c = p + s_w * k.
2. Decodes with the plain (un-signed) key: must fail (blindness control).
3. Scans all 112 rules: the planted rule must rank #1 by IoC of the decoded letters.
4. Null: random per-word signs (no rule) — no rule may reach IoC 1.5.
5. Informational only: the sign balance of every rule on LP2's real words (sign sequences
   should be near 50/50 for a usable rule; extreme imbalance marks degenerate rules).

**Verdict.** PASS if the blind decode stays under 1.5 (it recovers ~half the text, so it
sits around 1.35-1.45 — this partial blindness is inherent to sign families), the planted
rule ranks #1 with IoC >= 1.5 and at least +0.4 over the blind decode, and the null stays
below 1.5. A pass means the 112-rule screen has power and the full campaign (~22 h on the
GPU, 3 h for the 30-rule fast slice) is worth running; a fail means the gate itself is
broken and the campaign must not run.

**Cost.** seconds on CPU.
