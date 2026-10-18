# crib_filter — decode filters from the book's own marks (apostrophes, n't, one-rune words)

**Hypothesis.** The marks layer gives hard plaintext constraints no campaign currently
consumes: the four lone ticks (work/ref/tick_marks.tsv, ticks=1) are apostrophes, so the
rune after each must be S, D or T; two of them are 3-rune stems ("n't"), so N then T at two
known offsets; the 83 one-rune words must be A or I. Any candidate decode that fails these
positions is wrong regardless of score.

**The gate.**

1. Planted control: encrypts a koan-style text (it contains "the I" one-rune words and
   designated apostrophe/n't sites) and shows the filter passes the true decode 100% and
   kills a wrong-key decode on most of the checks.
2. LP2 wiring: reads the real tick table and computes the real constraint positions
   (4 apostrophe tails, 2 n't sites, 83 one-rune words) with their segment rune offsets,
   ready to be plugged into any verifier.

**Verdict.** PASS if the true decode passes all checks and the wrong decode fails at least
60% of them. The LP2 part is informational (no decode of LP2 exists); its output is the
constraint table for the campaigns.

**Cost.** seconds on CPU.
