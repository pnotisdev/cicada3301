# sliding_window — a key that starts anywhere in the book is found at its position

**Hypothesis.** Every kscreen campaign so far placed its 300-rune windows at fixed positions
(8 section starts, 46 page starts, 10 headings, 22 typographic marks). The key offset was
swept exhaustively, the ciphertext position was not. A key that starts mid-section, or runs
continuously across the whole book (no restart convention — `restart_llr`'s Z 0.96 vs a
planted 2.7 mildly argues against restarts), is invisible to all of it.

**The gate.**

1. Builds a synthetic "book" (8 concatenated sections of corpus-consistent English).
2. Plants a totient-key alignment at a random mid-book position and a random key offset:
   300 runes are encrypted there; everything else is uniform.
3. Screens 120 random (position, offset) pairs plus the planted one with the skip-checked
   beam and IoC: the planted pair must rank #1 with IoC >= 1.5, and the best of the 10
   neighbouring positions at the true offset must not beat the planted position.

**Verdict.** PASS if the planted (position, offset) clears IoC 1.5 and beats every null by
+0.3. A pass licenses the full-book sliding export (staggered windows, 581 flat streams,
~3-8 h on the GPU); a fail means the gate is broken.

**Cost.** seconds on CPU.
