# Phase 56: which word-level rule gives the lag-6 length profile?

Nothing in LP2 is solved. Script `work/phase56_lag6_length_rules.py`, output `results/analysis/phase56_lag6_length_rules.txt`.

## Plan
English plaintext (digraph runes, `fam_data.english`), LP2's section layout (12,956 runes), flat random key, repeat repair with probability 0.81 as in phase 25. 1,000 replicates per rule.
Rules: M0 no echo (reference); M1 phase-25 repair (a repaired collision at word position >= 6 writes T(c[-6]) = 24 - 2c[-6]); A halves (second block of 6 writes T(c[-6]) at a tuned rate, independent of collisions);
B per-word key restart every 6 (k_i = k_(i-6) in half the words; gives EQUAL runes at lag 6, so it is a control that cannot give T); D insertion gate (at word positions >= 7 an extra rune T(c[-6]) is inserted at a tuned rate; the "absent at 7" idea).
A and D tuned to LP2's 80 in-word hits. Score: chi2 of 6 numbers (hits in word-length bins 7 / 8 / 9 / 10+, in-word and gap doublet rates) against each rule's own replicate spread, P = share of replicates with chi2 >= LP2's, Poisson logL of LP2's bin counts, G of the word-length histogram vs LP2.

## Numbers
LP2 hits per bin 7 / 8 / 9 / 10+: 8 / 21 / 20 / 31 (80 of 1,290 pairs); doublets in-word 0.63%, gap 0.80%.

| rule | mean hits 7 / 8 / 9 / 10+ | total | chi2(6) | P | logL | G wordlen |
|---|---|---|---|---|---|---|
| M0 no echo | 5.8 / 7.9 / 8.9 / 16.0 | 38.6 | 42.7 | 0.001 | 148.5 | 266.7 |
| M1 phase-25 repair (untuned) | 10.4 / 14.0 / 16.1 / 28.2 | 68.7 | 5.7 | 0.48 | 164.5 | 268.0 |
| A halves, r 0.040 | 12.3 / 16.3 / 19.0 / 32.6 | 80.2 | 3.9 | 0.68 | 165.4 | 267.3 |
| B key restart (control) | 6.0 / 7.9 / 9.1 / 15.7 | 38.6 | 44.4 | 0.001 | 148.5 | 267.2 |
| D insertion gate, r 0.062 | 6.0 / 7.5 / 14.9 / 52.6 | 80.9 | 29.2 | 0.001 | 152.5 | 270.9 |

## Reading
- The length profile does not discriminate. The 7-rune bin is 8 against 10.4 (M1) or 12.3 (A): -0.8 sd and -1.2 sd, i.e. "absent at 7" is a small-number effect; the pair count is only 216. A uniform echo with the collision-repair or a block rule fits (P 0.5-0.7).
- B cannot make the T relation (confirms the period-6-key idea gives equal runes: 54.6 vs 38.6, LP2 has 32); D puts the hits into 10+ and fails (P 0.001). The "gate at position 7" idea is excluded as a fit.
- No rule changes the word-length histogram (G 267-271 for all, as in phase 25): the extra rune in ~42% of words stays unexplained, and gap doublets (LP2 0.80%) are 0.66% in every rule (not a rule difference).
- Caveats: English only, random key, Q fixed, rate tuned on the total; the profile was a post hoc cut (phase 54); A is the phase-25 repair without its collision link, so it is not a new mechanism. No rule is a fit that explains more than the plain total.

Verdict: no rule is singled out; M1 and A fit equally. A joint model for the length profile is not justified by these data.
