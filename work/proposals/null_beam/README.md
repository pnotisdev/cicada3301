# null_beam — unkeyed per-word null runes (the '+1 rune in 42% of words' mechanism)

**Hypothesis.** About 42% of multi-rune words carry one extra rune that uses **no** key value
(the solved pages' literal-F mechanism with a uniform rune in place of F). It is the leading
explanation of the word-length histogram, and it silently desynchronises every existing
decoder after the first null. This is merged-plan items [0],[7],[23] (the unkeyed half).

**The gate.**

1. Plants a text with nulls: each multi-rune word gets one uniform null rune at a random
   inner position with probability 0.42; the expanded sequence is encrypted with a totient
   key and the anti-repeat skip. Nulls do not consume key values.
2. Null-blind decode (the current `decode_beam`): must fail (IoC < 1.3) — this is the
   blindness every existing engine suffers.
3. Null-aware decode (a beam with a 'null' transition: cipher rune, key pointer stays,
   at most one per word at an inner slot): must recover (IoC >= 1.5 on the non-null
   letters) and must find about the planted number of nulls.
4. Self-consistency: ciphertext word lengths must show the planted +1-in-42% signature.
5. Null: no nulls planted, null-aware decoder must NOT hallucinate nulls (its recovered
   null count must stay near zero and its IoC near the blind decoder's).

**Verdict.** PASS if blind < 1.3, null-aware >= 1.5 with null count within +/- 20% of the
plant, and the no-null control stays clean. A pass means the null-aware beam is correct and
the GPU port (bgmt null branch, ~2.4 h per generator on window 0.7) is worth building; a
fail means the beam is broken and the campaign must not run.

**Cost.** seconds on CPU.
