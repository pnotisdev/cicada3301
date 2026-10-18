# lm_power — the information gap: IoC is blind to a two-layer cipher, bigram LL is not

**Hypothesis.** Every kscreen negative used IoC (about 0.4 nats/rune of English evidence).
A two-layer cipher — keyword Vigenere inside, number stream with the anti-repeat rule
outside — leaves a residual whose IoC is about 1 + 0.8/L ~ 1.1-1.2, below kscreen's 1.40
threshold, so the screen never examines it. A bigram (or better: rune-LM) score carries
1.5-2.2 nats/rune and separates it. This gate measures that gap directly and motivates
rescoring the existing library with an LM before any new family is built.

**The gate.**

1. Plants c = p + keyword + totient-stream (DIVINITY inside), anti-repeat skip.
2. Removes the outer stream with the skip-checked beam: the residual's IoC must be
   below 1.40 (this is the blindness every existing screen suffers).
3. Ranks 10 lore keywords + 30 random keywords against the residual by IoC and by bigram
   log-likelihood: the true keyword must rank #1 by LL with a large margin; report where
   it lands by IoC (the point is the LL margin per rune, not the rank).
4. Null: a random keyword's best LL must be far below the true keyword's.

**Verdict.** PASS if the residual IoC < 1.40 while the LL ranks the true keyword #1 with a
margin of at least 0.3 nats/rune over the best wrong keyword. A pass is the quantitative
case for the LM rescoring build; a fail means the gate is broken.

**Cost.** seconds on CPU.
