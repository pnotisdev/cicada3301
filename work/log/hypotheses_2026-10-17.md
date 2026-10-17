# New hypotheses and algorithms (2026-10-17, laptop session)

Scope: LP2 (segments 0.7-0.15, 12,956 runes). **Nothing in LP2 is solved.** This note starts from `PLAN.md`,
`docs/CAMPAIGNS.md`, the desktop report and `work/log/research_2026-10-17.md`, and lists only what is new. Every test
has a positive control (a planted key the method finds) and a null control.
- Keyless probes: `work/tmp/hyp/probe1.py` .. `probe5.py`, all run by `work/tmp/hyp/run_all.py`, output
  `results/analysis/hypotheses_2026-10-17.txt`.
- New engine for the two-layer hypothesis: `work/layer2` (Rust; `export.py`, `selftest.py`, `verify.py`), outputs in
  `results/layer2/`, campaign `layer2` in `jobs/overnight.py`.

## 0. Summary

| id | hypothesis (why it was a candidate) | test | result |
|---|---|---|---|
| H-PROG | English-like running key plus a progressive (Trithemius) shift, k_j = t_j + s*j, under the skip rule. Flat unigrams, no lag coincidences, and the Phase-3 residual sweep loses it because skips move j away from the rune index | "progressive kappa": count c[i+d] - c[i] = s*d over d = 2..30 for each s (the drift is usually zero over short d) | **excluded at moderate power**: LP2 max z +2.30, inside the null (40 replicates: median +1.95, 90% +2.78, max +3.83); four plants found at rank 1 with z +4.1 .. +5.3 |
| H-MULT | multiplicative keystream c = D(p) * k (mod 29), any key, any plaintext alphabet (not covered by the additive screens) | the cipher fixes one plaintext letter on one rune; that rune would need a letter's word-position profile | **excluded**: no rune matches any English letter (best G = 49.2 on 4 df over 29 x 29 pairs; rune F itself is flat, G = 8.2) |
| H-CUM | running key made uniform by a cumulative sum (k = cumsum of an English text), or c = cumsum(p + t) | step histogram c[i+1] - c[i], bins 1..28 | **excluded**: simulated chi-square 130-144 and 569-736 against LP2's 41.2 (27 df) |
| H-DITTO | the 86 surviving doublets are a "ditto" code for one plaintext letter | doublet positions in words against every letter of about 0.66% frequency | **excluded**: ING (0.48%), IA (0.64%), EA (0.72%) sit in the wrong positions (G = 95-338, 3 df) |
| H-DRST | the key restarts after each surviving doublet (a doublet as a visible "reset" mark) | coincidences of the runes following each pair of doublets, t = 1..30 | **excluded**: LP2 z -0.32 (random restart points: median +0.28, max +2.48); three plants z +17 .. +25 |
| H-MISS | any prime-based key at ANY offset (p_n + b, phi(p_n) = p_n - 1): such a key never takes one value, which dents the unigrams in the shape of the English frequencies | matched filter over the 29 rune counts, 29 shifts x {identity, Atbash} | **disfavoured (p ~ 0.05)**: LP2 max z +1.89; 40 planted prime keys (n ~ 10^7): median +3.55, 38 of 40 above +1.89. Extends the prime/totient coverage far beyond the 20,000 values of the kscreen library, for Cicada's two alphabets |
| - | the within-word lag-5 echo is concentrated in quoted speech (tick-mark spans) | lag-5 coincidences inside the 6 quote spans | no: 2 inside, 1.9 expected |
| **H-LAYER** | **the solved pages' two methods stacked**: a keyword Vigenere inside (Welcome / Koan 2, optionally their literal-F rule), a number stream with the anti-repeat rule outside | new engine `work/layer2`: beam over the outer stream's re-draws, inner keyword decoded per state, English-bigram score | engine validated (selftest 14/14); **first slice negative**: An End's prime streams x the three solved keys, 512 M decodes, best -4.53 per rune against about +7 for a true key; 0 of 15 hits survive whole-window verification. Full campaign queued for the desktop |

**Relation to the desktop's family simulations of the same day** (`work/log/phase9_families.md`, written in parallel):
that study shows that every structureless additive key looks like "random + 81% avoid-repeat" to any statistic, so only
decryption tests can tell keystream sources apart; `layer2` is such a test. Its 25 families do not include the six tested
here (progressive running key, multiplicative key, cumulative running key, ditto letter, doublet restarts, missing key
value). It also finds that LP2's separators are not English word boundaries (no serial correlation of word lengths): the
bigram score of `layer2` ignores the separators, so H-LAYER is unaffected. Its open leads (the lag-5 echo concentrated on
rune S, the lag-6 relation c' = 24 - 2c inside words) are not explained by any family here either.

## 1. What any hypothesis has to explain

From `PLAN.md`, reproduced by `probe1.py`:
- runes uniform (IoC 0.9999); the step c[i+1] - c[i] uniform on 1..28 (chi-square 41.2 on 27 df), bin 0 at 86 against
  446; every lag-d difference stream flat for d = 2..400 (largest chi-square 53.9 at d = 11, what 400 lags give), so
  there is no ciphertext autokey at any lag up to 400;
- separators authentic; word lengths: too few 2-rune words, slightly too many 7-8-rune words;
- inside words, coincidences at lag 5 (4.92% against 3.45%, z +3.7; lag 4 z +2.0, lag 6 z -1.95), strongest in
  10-rune words (21 against 8.8); none across word gaps (the global lag-5 excess equals the within-word excess);
- rune F is an ordinary cipher symbol (3.54%, flat over word positions; 10 of 465 2-rune words end in F, where a fixed
  F would give about 77 from OF and IF).

## 2. The keyless tests (details)

### H-PROG: running key plus a progressive shift (`probe2.py`)
Model: c_i = p_i + t_j + s*j (mod 29), t an English text, s a constant step, j the key pointer (skip rule, q = 0.8).
Statistic T(s) = sum over d = 2..W of #{i : c[i+d] - c[i] = s*d}. With no re-draw between i and i+d the key difference is
exactly s*d, and the rest, (p+t)[i+d] - (p+t)[i], is 0 with probability IoC(p+t)/29, about 1.05/29.
- Controls: Emerson (LP2's section lengths) under four Gutenberg running keys and random s: z +5.25, +5.32, +4.22,
  +4.08, true s at rank 1 each time. Null (random key, same rule), max over the 28 steps, 40 replicates: median +1.95,
  90% +2.78, max +3.83.
- LP2: W = 10: +1.69; W = 30: +2.30; W = 60: +1.73; W = 30 including d = 1: +2.44. All inside the null.

### H-MULT: multiplicative keystream (`probe3.py`)
With k never 0, c = 0 exactly where D(p) = 0: one plaintext letter X always lands on one rune. Every rune was compared
with every English letter on the four position classes (1-rune word, word-initial, word-final, medial): best G = 49.2
(rune EO against letter M), then 54.6 and 56.4. Letters are never or very often 1-rune words and differ strongly
between initial and final position; every LP2 rune is flat. Holds for any key, with or without the anti-repeat rule,
and for any numbering of the runes.

### H-CUM: cumulative running keys (`probe3.py`)
Emerson as plaintext, three Gutenberg texts as t, skip rule: the step keeps the plaintext's shape (Delta p + t, or
p + t), chi-square 130-736 against LP2's 41.2. The same holds for any non-uniform map of the key text.

### H-DITTO and H-DRST: the surviving doublets (`probe5.py`)
Doublets by the position of their second rune: initial 23, final 19, medial 44, 1-rune 0. Positional shares fit common
letters (O, M, H: G 4.6-9.0), but those occur at 2.6-7.6%, not 0.66%; the letters of the right frequency do not fit.
A key restarting after every doublet would line up the runes that follow: 3,721 coincidences in 108,460 aligned pairs
(3.43%), z -0.32; planted restarts give z +17 .. +25.

### H-MISS: missing key value (`probe4.py`)
P(c) = (1 - f(D^-1(c - u))) / 28 when the key avoids one value v (u = sign * v). Prime-based keys avoid one value at every
offset (p_n mod 29 is never 0 for p_n > 29). LP2's best (u, D) is +1.89 (Atbash, u = 23), below the null median (+2.00;
95% +2.94 over 200 replicates). With letter-by-letter English frequencies: +1.91. 40 plants of p_n + b at n ~ 10^7
(random offset, shift, sign and alphabet): true cell median +3.55, 10% quantile +1.97, rank 1 in 33 of 40; 2 of 40 fall
below LP2's maximum. Limits: identity and Atbash only, modest power; evidence, not proof.

## 3. H-LAYER: the solved pages' methods stacked (`work/layer2`)

**Why.** The keyed solved sections use two building blocks, a keyword Vigenere (Welcome: DIVINITY; Koan 2:
FIRFUMFERENFE, i.e. CIRCUMFERENCE with C -> F) and a number stream (An End: phi of the primes), all with the literal-F
rule. LP2 adds one feature, the anti-repeat rule. The simplest stronger cipher made of these parts is the stack

    q_i = p_i + K[phi mod m]     (literal F: q_i = F and phi does not advance)
    c_i = q_i + S_j              (anti-repeat: when c_i would repeat c_{i-1}, the encryptor moves on to S_{j+1})

It fits the whole fingerprint: flat unigrams and steps (outer stream), the doublet deficit (outer rule), word structure
kept, and **no F excess**: the inner layer's literal F's are enciphered again by the outer layer, which explains why
the solved pages' literal-F rule is invisible in LP2.

**Why every earlier screen misses it.** kscreen decodes the outer stream correctly and then scores q, a Vigenere text:
IoC 1.18 on the selftest plant, below its 1.40 threshold. The dictionary screens see no words; the step-domain and chain
screens model other ciphers.

**Engine.** The outer collision check depends only on c and S (the encryptor compares q_i + S_j with c_{i-1}), so the
outer branch points are kscreen's. `layer2` keeps a beam over (outer pointer, inner phase) and decodes the inner layer
in each state:
- `mode=bigram` (main screen): keywords from a file, every phase, both inner signs, literal F on/off, identity or Atbash
  alphabet; score = English rune-bigram log-odds per rune (x10). True key about +7, random decodes about -15. IoC scoring
  (`mode=known`) overfits the literal-F branch, which lets a decode re-phase the keyword at every decoded F: chance
  decodes reached IoC 1.46-1.57 after only 54,000 tries, against 1.70 for the planted key.
- `mode=periodic`: any keyword of period m, scored by a z-score of coincidences within the m columns (comparable across
  m). Hits are turned into a keyword (best English shift per column) and rescored in bigram mode (`verify.py`).
- `verify.py`: whole-window re-decode (beam 64) and the same setting at 20 random offsets of the same stream (offsets
  within 50 of the hit excluded); a candidate needs +2.0 per rune and a margin of 5 over that matched null.

**Controls** (`work/layer2/selftest.py`, `results/layer2/selftest.txt`): SELFTEST PASSED, 14 of 14.
- Three bigram plants (DIVINITY in phi(p_n) with literal F, skip; FIRFUMFERENFE in pi base 29, Atbash, inner and
  outer sign -1, coin; CIRCUMFERENCE in phi(n), literal F, Atbash, coin), 3 windows each: all 9 found at the true
  offset (one at -1) with the right keyword, +7.2 .. +8.2 per rune; whole-window re-decode +7.3 .. +8.2 against matched
  nulls of -7.4 .. -9.8.
- Blindness: kscreen at the true offset of the first plant gives IoC 1.182.
- Periodic mode, a keyword not in the file (period 6): all 3 windows found, keyword recovered (as a rotation),
  decoded text readable (+6.8 .. +8.1 per rune against -9 .. -10).
- Null: 3 random streams x 3,000 offsets x the solved keys (every phase, sign, literal F, alphabet) x 8 LP2 windows:
  best -4.77 per rune.
- A first selftest run failed one check for a design reason, not a method failure: the matched null drew an offset one
  step from the true one (it decodes most of the text). Offsets within 50 of the hit are now excluded from the null.

**First LP2 slice** (`results/layer2/bigram_solved_primes.tsv`, `_verify.txt`): the outer stream as in An End (primes,
primes - 1 = phi(p_n), primes + 1), the inner key DIVINITY, FIRFUMFERENFE or CIRCUMFERENCE, every phase, both inner and
outer signs, literal F on/off, identity and Atbash, skip and coin, every offset up to about 19,700, each of the 8
sections as its own window (a fresh start per section or one pad through LP2): 512 M decodes in 14 min (6 threads).
Best -4.53 per rune (all sections -5.10 .. -4.53, the null's range); the 15 best re-decoded over their whole windows give
-6.7 .. -7.9 per rune (IoC 1.05-1.10), level with their matched nulls; **0 of 15 pass. Negative.**

**Queued for the desktop** (`python jobs/overnight.py run layer2`, about 13 h on 16 CPU threads; no GPU port):
the 115 core number streams x the three solved keys; 20 Cicada streams x 30 Cicada keywords; any keyword of period
2-14 (periodic mode); variant A1 (the keyword folded into the stream with one pointer), each with verification.

## 4. Proposed next (not run yet), ranked

1. **The `layer2` campaign** on the desktop (above).
2. **Time-seeded generators.** All 32-bit seeds are swept, but Java's `Random` takes a 48-bit seed and Python's
   `random.seed(int)` any integer. A program run in 2012-2014 that seeded with a millisecond timestamp
   (1.3254e12 .. 1.3889e12, about 6.4 x 10^10 seeds) is not covered. On the desktop GPU the existing kernels take 165 s
   (Java) and 425 s (Python) per 2^32 seeds, so about 40 min and 1.8 h. Controls as in `prng-more`.
3. **Crib-filtered seed sweeps.** With letter-by-letter spelling (the TH finding of `wordlen-languages`) the red heading
   of 0.8, word lengths (2, 11, 3), fits "AN INSTRUCTION" (the title of solved section 0.6), and 0.13's (3, 12, 4) fits
   "THE INSTRUCTIONS". A crib turns a sweep into a filter: generate the first 13-16 key values of each seed and compare
   them with the crib, allowing re-draws. No scoring is needed, so it is much faster than the dictionary sweeps, and one
   full match is decisive (29^-13 per seed). Works for any generator and also for the library at every offset.
4. **H-SIGN: direction switching** ("their numbers are the direction", January 2016 message): c = p + s_i*k with s_i = +-1
   set by a known rule (parity of the key value, of the word index, of the previous ciphertext rune). Rules on key values
   are just new library streams (k' = k or -k); rules on positions need a per-position sign in the decoder.
5. **H-LAYER with seeded generators outside.** The solved keys x 2^32 seeds of the ten generators is about 10^12
   decodes: a GPU kernel with the layer2 decoder (the generators of phpmt.cu plus the bigram beam of bgmt.cu).
6. **Single-layer English-scored rescreen of short restart windows.** `layer2` with the trivial keyword
   (`data/keyword_none.txt`) is kscreen with a bigram score for the identity and Atbash alphabets; it separates a true
   key from chance even on 91-137-rune windows, where kscreen's IoC peaks (2.12 on head0.13) needed an extreme-value null.
7. **H-STALL: the key pointer stalls on one plaintext letter** (An End's "F uses no key position" without the literal
   F). Low prior: two letters would share a key value. Covered by 29 decoder variants.
8. **Steganography with solved-text passphrases** (OutGuess on the LP2 page images with each of the 12,944 solved-text
   words and phrases): needs the OutGuess tool installed; the user's decision.
