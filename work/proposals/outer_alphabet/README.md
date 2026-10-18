# outer_alphabet — keyword-mixed outer alphabet around an additive key

**Hypothesis.** The classic hand-cipher step beyond the solved pages' Vigenere keywords: an
outer keyword-mixed alphabet sigma, so c = sigma^-1(sigma(p) + k). Every screen that
subtracts k in Gematria order then sees a flat c - k, and the anti-repeat rule is
sigma-invariant, so every existing negative is blind to this family. This is merged-plan
items [3]+[25] (the finite tiers before the general H2 screen).

**Keyword-mixed alphabet.** sigma = (keyword letters, deduplicated, in GP order) + (the
remaining runes in GP order), read as a permutation of the 29 runes. Lore keywords:
DIVINITY, FIRFUMFERENFE, CIRCUMFERENCE (the solved keys), INTUS, INSTAR, EMERGENCE,
PRIMALITY, TOTIENT, PILGRIM, WELCOME — 10 candidate alphabets.

**What this gate does.**

1. Plants c = sigma^-1(sigma(p) + k) for a randomly chosen keyword, totient stream,
   anti-repeat skip.
2. Blindness: the plain additive decode (identity alphabet) must stay flat (< 1.3) —
   this is why the existing screens cannot see the plant.
3. Recovery: applying sigma to the ciphertext and decoding additively with the same key
   must recover the text (IoC >= 1.5).
4. Enumeration: the 10 candidate alphabets are scanned; the planted one must rank #1.
5. Null: a random alphabet must stay below 1.5.

**Verdict.** PASS if blind < 1.3, sigma(c)-decode >= 1.5, planted alphabet ranks #1, and
the random alphabet fails. A pass validates the "rerun every engine on sigma(c)" trick for
the finite tier (~14 h on the GPU); a fail means the gate is broken.

**Cost.** seconds on CPU.
