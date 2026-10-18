# survivor_doublets — real-LP2 test: how do the 86 surviving doublets distribute?

**Hypothesis test, keyless.** The anti-repeat rule suppresses 81% of would-be repeats; the
86 that survive should distribute over words in a model-specific way: coin-flip survivors
scale with the number of adjacent pairs in a word (length - 1); a uniform/deliberate process
scales with the number of runes (length); a ditto code is text-position-dependent. The
project recorded the global rates (0.62% inside words, 0.81% across gaps) but never tested
the per-word-length distribution.

**The gate.**

1. Synthetic control: generates books with a *planted* survivor model (coin-flip 81% rule
   vs a uniform doublet process), and verifies the test statistic (G-test of doublet counts
   per word-length bin against both predictions) identifies the planted model.
2. Runs the same statistic on LP2's real words and prints which model fits.

**Verdict.** PASS if the synthetic control correctly identifies the planted model (the
statistic has power); the LP2 result is the finding, printed as data.

**Cost.** seconds on CPU.
