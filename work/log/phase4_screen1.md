# Phase 4 screen 1 – number-theoretic, Cicada-number and keyword keystreams (2026-10-16)

**Result: negative.** No keystream scored above the random-key controls.

## Setup
- Cipher model: c = t + s*(k_j + b) mod 29, where t = p or 28−p (Atbash), s = ±1, b = 0..28, with the
  collision-skip rule from Phase 3. The fast screen (`attack.fast_screen`) lets the key shift grow by
  0–23 positions from word to word.
- Segments 0.7, 0.8, 0.9, 0.11–0.15, using the first 300 runes of each. Key offsets tried: 0, the segment's
  rune position in the whole book, and its position within the unsolved block.
- 1007 keystreams (73 numeric or Cicada, 934 keywords or phrases from the solved
  text) plus 40 random controls. That is 100512 screens, each covering all 29 values of b.
- Sensitivity was checked on synthetic text: keys planted with φ(n), π in base 29, DIVINITY and totient (with
  offsets, b, sign and Atbash all varied) all came out at rank 1 with the correct b, scoring 0.59–0.65.

## Scores (fast screen, max over b; real keys score about 0.6)
- Random controls: max 0.192, 99.9th percentile 0.185
- Highest per family: a^n mod 29 0.196 · keywords/phrases 0.194 · digits of constants 0.183 ·
  number-theoretic/Cicada 0.182
- I re-decoded the top 30 (keystream, segment) pairs with the exact decoder. Scores were 0.10–0.13
  (wrong-key level is about 0.09, a real key about 0.7). A/I rates were 0.00–0.27 on about 11 one-rune
  words each, which is chance level (0.07).

## Keystreams covered
Numeric / Cicada: 1033 digits, 1033 square rows, 1033*n, 10^n mod 29, 11^n mod 29, 12^n mod 29, 13^n mod 29, 14^n mod 29, 15^n mod 29, 16^n mod 29, 17^n mod 29, 18^n mod 29, 19^n mod 29, 20^n mod 29, 21^n mod 29, 22^n mod 29, 23^n mod 29, 24^n mod 29, 25^n mod 29, 26^n mod 29, 27^n mod 29, 28^n mod 29, 2^n mod 29, 3301 digits, 3301*n, 3301^n, 3^n mod 29, 4^n mod 29, 5^n mod 29, 6^n mod 29, 7^n mod 29, 8^n mod 29, 9^n mod 29, An End hash bytes, An End hash nibbles, composites, cumulative phi(n), cumulative prime sum, d(n), e digits (base 10), e digits (base 29), emirps, fibonacci, gematria primes cycle, ln2 digits (base 10), ln2 digits (base 29), lucas, n, n^2, n^3, page-14 square cols, page-14 square rows, page-30 grid cols, page-30 grid rows, pell, phi digits (base 10), phi digits (base 29), phi(n), pi digits (base 10), pi digits (base 29), prime gaps, prime index of primes, primes, primes from 3301, primes+1, primes-1 (totient), primes^2, sigma(n), sqrt2 digits (base 10), sqrt2 digits (base 29), sqrt3 digits (base 10), sqrt3 digits (base 29), triangular

Keywords / phrases: 934 entries. These are every solved-text word of 4 or more letters, every adjacent
word pair, and: DIVINITY, FIRFUMFERENFE, CIRCUMFERENCE, INSTAR, EMERGENCE, PRIMALITY, TOTIENT, PILGRIM, CICADA,
LIBERPRIMUS, INTUS, PARABLE, KOAN, WELCOME, DEEPWEB, SELFRELIANCE, AGRIPPA, THELEMA, the 1033-square words,
and FULMAEAYOEA (caption 0.10 read as plain runes).

## Not covered by this screen
- Keys that start at an arbitrary offset other than the three above. A keyword key covers every offset
  through b and its period; number sequences do not.
- Plaintext-dependent keys, keys from texts outside the solved LP, and PRNG or hash keys.
- Variants where the collision rule is not "skip to the next key element", for example a fresh
  random re-roll. Those cannot be decoded with a deterministic key at all.

Raw results: `work/tmp/phase4/screen.json` (score, keystream, segment, offset, sign, atbash, b).
