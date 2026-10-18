# section_depth — shared pad at section starts: power of the difference statistic

**Hypothesis.** Every keyed solved section starts its key at j=0 at the section start. If LP2
does the same with one unknown pad, the sections are in depth: d_i = c1_i - c2_i = p1_i - p2_i.
This is merged-plan items [1],[10],[15],[21],[26] (the reuse family). The ledger calls
section reuse "undecidable" — this gate measures *why* and *where power remains*.

**The statistic.** Not unigram IoC — the difference of two English streams has IoC only
about 1.02 (the 4th moment of the letter distribution), which is why the plain depth test is
near-powerless. The working statistic is the **bigram log-likelihood of the difference
stream** under the difference-bigram model (the convolution of English bigrams): shared pads
give a positive excess per rune, independent pads none.

**The gate.**

1. Builds the difference-bigram model empirically from two long corpus-consistent streams
   (Markov from the embedded corpus).
2. Plants two 4,000-rune sections with the SAME totient pad from j=0 — first without the
   anti-repeat rule, then with it.
3. Null: ten draws of two sections with independent pads (same code path).
4. Reports: the LL excess (nats per rune) and z for the no-skip case (must be strong), the
   unigram IoC for honesty (about 1.02 — near-powerless), and the with-skip case (the excess
   must collapse to the aligned first-window share — this is the documented reason the real
   campaign needs the LM drift-tracking beam).

**Verdict.** PASS if the no-skip shared excess clears z >= 5 over the independent nulls AND
the with-skip excess falls to at most 25% of the no-skip excess. A pass documents the power
curve and justifies building the LM stage; a fail means the statistic is misimplemented.

**Cost.** seconds on CPU (two 4,000-rune sections, ten null draws).
