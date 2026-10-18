# word_reversal — "numbers are the direction" as per-word plaintext reversal

**Hypothesis.** The direction hint's un-tried reading: within each word, the plaintext is
written reversed (or the key run reversed) according to the word's number. Word reversal
is invisible to IoC (it preserves letters), so every IoC screen is blind to it; only a
score that models word boundaries (bigram LL with a boundary token) can see it.

**The gate.**

1. Plants c = reverse_w(p) + totient key with the anti-repeat skip.
2. Decodes with the skip-checked beam (this yields the reversed words) and scores both
   orientations — as-is vs un-reversed per word — with a boundary-aware bigram model:
   the true orientation must win.
3. Control: plants a NOT-reversed text; the as-is orientation must win there.

**Verdict.** PASS if the correct orientation is identified in both directions. A pass
licenses the per-word-reversal variant for the sign campaign's engine; a fail means the
gate is broken.

**Cost.** seconds on CPU.
