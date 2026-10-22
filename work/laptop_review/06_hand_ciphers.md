# 06. Hand ciphers, machines and puzzle ciphers that prevent repeats and insert nulls: mapped onto R4

Sub-session 6 of the laptop review sweep, 2026-10-22/23, machine alias `laptop`. **Nothing in LP2 is solved; nothing below is evidence that Cicada used any of these.**
Read first: `work/laptop_review/00_brief.md`, `work/log/phase57_mechanism.md`, `phase25_mechanisms.md`, `phase47_insertion_doublets.md`, `docs/TRIED.md`,
registry rows `fingerprint-families, chain, step28, state-machines, skeleton5, lag-feedback, echo-mechanisms, echo-two-tap, walk-evolving, recurrences, per-word-keys, keyless-batch, word-position-schedule, nulledge`.
Web reading only (no downloads, no third-party code run). One tiny keyless simulation was run (section 2), script kept outside the repository.

## 0. Summary

- **No classical or machine cipher I could map produces all four R4 signals.** Of 22 candidates, 0 are kept as a mechanism, 4 are kept as "design conventions" worth one cheap test each, the rest are killed by one of: ciphertext doublets not suppressed (about 3.45%), lag-6 affine relation impossible, extra rune per rune instead of per word, or non-flat unigrams / bigrams / periodic lags.
- **Structural reading (my inference, not a measurement).** Signals 1 and 2 together need a process that is *continuous across word gaps* for the anti-repeat check (23 of 86 doublets cross gaps, suppression equal) but *bounded by the word* for the look-back (zero lag-6 excess across gaps). Historical hand ciphers (Vigenere, Playfair, VIC, Nihilist, Bifid) strip word boundaries before enciphering and regroup in fives; they cannot produce a rule that looks only inside the current word. The rule reads like a program with a word loop, a persistent "previous output" variable and a per-word output buffer, or like a human nomenclator convention applied word by word. That is why the lead list below leans on implementation patterns (off-by-one, negative index, wrap) and on extending the key / feedback families, not on a named cipher.
- **Only two families natively suppress ciphertext doublets at all:** difference / relative-rank ciphers (100% by construction, so the 19% leak needs R3's later-pass nulls; row `step28`) and Playfair (about half the adjacent pairs, see the rate arithmetic below). Every key-additive, tableau, rotor and card cipher leaves doublets at the chance rate.
- **Top 3 untested leads (section 5):** (1) two- and three-tap *ciphertext* autokey, Gromark / VIC chain addition applied to the output (keyless, minutes, high power); (2) wrap-around / negative-index partner for the T repair at word positions below 6, stratified by word length (keyless, seconds); (3) sparse lagged-Fibonacci key streams of order 4-6 as library streams under the R4 channels (order 4 about 15 CPU-minutes, order 5 about 7 CPU-hours, order 6 hundreds of CPU-hours).

## 1. The four signals, as a checklist used below

| # | Signal | Test I apply to a candidate |
|---|---|---|
| S1 | doublets 0.66% (vs 3.45%), equal in words and across gaps | does the rule look at the previous OUTPUT rune, whatever the word boundary? |
| S2 | in-word lag 6: c' = 24 - 2c at about the collision rate, nothing across gaps | can the rule write a function of c(-6) alone, only inside a word, sparsely? (A key-side lag cannot: c(j) - c(j-6) then contains plaintext.) |
| S3 | one extra rune in about 45% of words, per word not per rune | is the extra symbol a per-word event with a capped count? |
| S4 | unigrams, bigrams, all other lags flat | is the output flat to IoC 1.002 with no periodic lag? |

## 2. The one simulation run (keyless, single-threaded, below-normal priority, under 1 CPU-minute)

Purpose: check two machine claims with numbers instead of memory. Script in the session scratch area, not in the repository. Seed fixed.

| Test | Setup | Result | Reading |
|---|---|---|---|
| Chaocipher generalised to 29 symbols (zenith index 0, nadir index 14 or 13; extract-shift-insert on both alphabets) | 300,000 plaintext symbols, iid uniform or iid Zipf; random start alphabets | equal-at-lag 1: 0.0342 / 0.0346 (uniform), 0.0321 / 0.0319 (Zipf); lags 2, 3, 5, 6, 7 within 0.0005 of lag 1; T6 hit rate 0.0338-0.0349 vs chance 0.0345 | no doublet suppression, no lag-6 structure: kills S1 and S2 for Chaocipher (S4 holds). Convention caveat: nadir index 13 or 14 only; other offset conventions not run. |
| Solitaire keystream (standard 54-card algorithm, 100,000 outputs) | consecutive keystream values equal | mod 26: 0.0445 (1 in 22.5); mod 52: 0.0254 (1 in 39.4); mod 29: 0.0414 | positive control: reproduces the published bias (Crowley, 1999: about 1 in 22.5). The bias goes toward MORE repeats, the opposite of S1; and a key bias would not by itself suppress ciphertext doublets. No ciphertext was computed. |

## 3. Candidate ciphers against the four signals

Entries: "yes" = native, "no" = impossible or at chance, "needs add-on" = only with an extra rule bolted on (which is then R4's own rules, not the cipher).

| Cipher | S1 doublets in/gap | S2 lag-6 affine in-word | S3 +1 per word | S4 flat | Verdict |
|---|---|---|---|---|---|
| VIC (chain addition = lagged Fibonacci mod 10 on the KEY; straddling checkerboard; two transpositions; indicator group inserted once per message) | no (additive key, chance rate) | no (key-side lag leaves plaintext in c(j) - c(j-6)) | no: checkerboard gives 1 or 2 digits per LETTER, a per-rune event (rejected, G 160 for per-rune scaling); the indicator group is once per message | yes after the key | killed S1, S2, S3 (as a cipher). Chain addition survives as a key family: lead L2. |
| Nihilist | no | no | no | output is sums of 2-digit numbers, not a 29-symbol alphabet; short keys leave structure | killed |
| Playfair (29 letters would need a 5x6 grid with a filler cell) | partial: no equal pair INSIDE a digraph (about half the adjacent positions), so about 1.7% overall against LP2 0.66%; parity of position would show it | no | pads plaintext doubles and odd lengths (per plaintext event, not 45% of words); would give even lengths if padded per word, LP2 has odd lengths | no: output keeps English digraph structure (bigram table non-uniform) | killed. Tested: aligned parity / digraph test `keyless-batch` (parity 37 vs 49, z -1.6; planted 2x2 Hill recovered), no even-length padding (commit 76be6d7, phase 60). |
| Two-square, four-square | no (a pair can have two equal letters, about 1/25) | no | no | no (digraphic) | killed |
| Hill 2x2 / Bifid / Trifid, applied per word | gap doublets would stay at 3.45% (blocks do not see the previous word): fails the brief's quick test | no | no | Bifid / Trifid keep English-shaped IoC | killed; aligned digraph blocks tested `keyless-batch` |
| Chaocipher (evolving alphabets) | no (section 2) | no (section 2) | no | yes | killed by simulation; the family row `walk-evolving` stays "untestable" for the specific length-clocked walk |
| Solitaire / Pontifex (card keystream, joker skips) | no; keystream repeats MORE than chance | no | no | yes | killed. The "skip on joker" rule is the same shape as the repo's skip / hold / spend repair channels, which already model "output suppressed or replaced". |
| Lagged-Fibonacci keystream, k_i = k_(i-1) + k_(i-6) or any two taps (Gromark / VIC chain addition on the key) | no | no | no | yes | killed as a mechanism for S1-S3; NOT excluded as a key family (keyless residual has no power for three-term forms, `phase10_keyless_power.md`; keyed screens cover order 1-3 only, row `recurrences`, gap "order >= 4; sparse taps"): lead L2 |
| Ciphertext autokey, two or three taps (the same recurrence applied to the OUTPUT) | no on its own | only as the residual cell, single tap excluded (`lag-feedback`) | no | yes | keyless residual would be plaintext itself (high power); two-tap form not run: lead L1 |
| Running key with a "never repeat the previous letter" rule | needs add-on (the rule IS the repair channel) | no | no | NOT flat for natural-language keys (excluded `book-running-key`) | killed for text keys; the repair rule is covered by `chanscreen-step3` |
| Alberti disk (capital index letters written into the ciphertext re-align the disk; numerals 1-4 hide codebook phrases) | no | no | YES in kind: indicator symbols appear every few words; but a per-segment constant shift leaves English-shaped repeats at all lags (S4 fails) | no: segments of about 2 words of a monoalphabetic shift | killed by flat lags; an indicator whose value sets a pointer jump into a long key is not testable (per-word key-phase freedom, row `nulledge` gap) |
| Jefferson wheel | no (independent discs) | no | no | periodic 36 | killed (periodic) |
| Hagelin / M-209 pin-and-lug machines | no (Beaufort-type, adjacent outputs independent) | no (key function of wheel positions, not of the output) | no | yes | killed. The six wheels have periods 17-26, which is not a lag-6 look-back. |
| Quagmire I-IV | no | no | no | periodic keyword leaves period structure | killed (`periodic`, `fingerprint-families`) |
| Gronsfeld with nulls | no | no | possible (nulls) but key is periodic | no | killed (periodic) |
| Homophonic substitution with 29 symbols | needs add-on: a homophone-avoids-repeat convention | no | no | NOT flat unless the plaintext is already flattened by a key layer; then it is R4 (a) | killed as a stand-alone; as an editorial rule it is R4 (a) |
| Nomenclator conventions (doubling signs, "repeat previous" signs, nulls) | possible by convention | no | YES in kind: nulls are scattered, but in a nomenclator they are dedicated symbols, not uniform runes | needs a flat layer | kept as the nearest historical analogue of S3 and of R3's later-pass nulls; no test beyond phases 47 / 57 |
| Anglo-Saxon / Norse cipher runes (Isruna: rune = aett number + position; Hahalruna: branch marks) | no | no | no (two numbers per rune, parity visible) | no (monoalphabetic) | killed (aligned digraph test, flatness) |
| Cicada's own: Atbash, Vigenere with literal F skips, prime / totient shifts with F skipped | solved layers do not suppress doublets by rule | no | no | solved pages not flat | killed for LP2 (`obs-flat`, `lag-feedback`, `solved-phrase-keys`) |
| Relative-rank / step-domain cipher (c_i = c_(i-1) + s_i, s_i != 0) | yes, 100% (so S1 needs the 19% leak) | no | no | yes | the only native S1; tested, `step28`, `chain`; R3 reads the leak as later-pass nulls |
| Dynamic substitution (Ritter): the table entry just used is swapped | no (output uniform and independent of the previous output) | no | no | yes | killed |
| Enigma-type "never encrypts to itself" | no (the rule relates output to plaintext, not to the previous output) | no | no | yes | killed |

## 4. Lead table

Prior: low / med / high. Costs are rough.

| ID | Lead | Source | What it claims / how it maps to R4 | Already tested? | Concrete test (planted positive control; null) | Cost | Prior |
|---|---|---|---|---|---|---|---|
| L1 | Two- and three-tap CIPHERTEXT autokey, c_j = p_j + a c_(j-s) + b c_(j-r) + d (Gromark / VIC chain addition applied to the output, Fibonacci-on-ciphertext) | https://www.cryptogram.org/downloads/aca.info/ciphers/Gromark.pdf (primer + pairwise-sum running key); https://en.wikipedia.org/wiki/VIC_cipher (chain addition) | The residual c_j - a c_(j-s) - b c_(j-r) - d is the plaintext itself, so IoC rises to the plaintext's. It would be a hidden layer under the repair / null layers; it does not explain S1-S3. | No for two taps. Single tap, d <= 8: `lag-feedback` (6,496 settings, chi2 275 only at the doublet cell). Two-tap KEY recurrences: `phase10_keyless_power.md` (residual is a mix of three letters, no power). | Section 5, lead A | minutes | low: needs a layer that leaves flat bigrams while carrying a feedback; S1-S3 stay unexplained |
| L2 | Sparse lagged-Fibonacci KEY streams, orders 4-6 (k_i = e1 k_(i-s) + e2 k_(i-r), e in {+1, -1}), as library streams scanned at every offset under the R4 channels | https://en.wikipedia.org/wiki/VIC_cipher; Gromark PDF above; page-30 Fibonacci steps and the DJU BEI distance 4 x 1597 (phase 43, row R2-2) as the only in-repo hints | A primitive characteristic polynomial gives one cycle of 29^r - 1 values containing every non-zero seed, so the existing offset screen covers the whole seed space of that recurrence. | No: `recurrences` gap says "order >= 4; sparse taps"; keyless scan has no power (three-term rank 29,640). | Section 5, lead B | order 4 about 15 CPU-min; order 5 about 7 CPU-h; order 6 about 290 CPU-h | low: no in-repo reason for a key of this form; it does not make S1-S3 |
| L3 | Wrap-around / negative-index partner for the T repair when the position in the word is below 6 | my inference from the structural reading in section 0 (a `buf[i - 6]` in a per-word buffer wraps in Python for i < 6) | If the repair source is indexed with a wrap, targets at word positions 3-5 would use a partner at lag 3, 2, 1 (Python negative index on the partial buffer: partner 2i - 6) or (j - 6) mod L. About 69% of words have 2-5 runes, so the hit count would be large but spread over lags 1-5. | Partly: pooled affine scans `lag-feedback` (d <= 8, a = 27, b = 24) dilute it over heterogeneous lags; stratified by word length it is NOT done. `word-position-schedule` tested differences, not the T map. | Section 5, lead C | seconds | low: R4 already fits S2 with in-word lag 6 only (profile by word length fits, phase 57); the wrap is a bug-pattern guess |
| L4 | Playfair-family / aligned digraph structure | https://en.wikipedia.org/wiki/Playfair_cipher; phase 41 idea 1.1 | no equal letters inside a pair would halve the doublets | YES: `keyless-batch` T2 (parity, within-word parity, planted Hill). Rate arithmetic here: Playfair predicts about 1.7% doublets vs 0.66% observed. | none new | none | low (killed) |
| L5 | Chaocipher / evolving alphabets as the doublet mechanism | https://en.wikipedia.org/wiki/Chaocipher | dynamic alphabets could in principle bias repeats | Family `walk-evolving` untestable; simulation here: no bias (section 2) | none new | none | low (killed for the plain Byrne version) |
| L6 | Solitaire / Pontifex keystream with joker skips | https://en.wikipedia.org/wiki/Solitaire_(cipher); https://arxiv.org/pdf/1909.06300 | repeat bias in the keystream | Simulated here: the bias is toward MORE repeats | none new | none | low (killed) |
| L7 | VIC-style key indicator group inserted once per section or page | https://en.wikipedia.org/wiki/VIC_cipher | an extra 5-rune block shifts the key alignment | Covered in effect: every-offset window screens (`chanscreen-step3`, mid-word arc phase 51) tolerate any change of key phase between windows; repeats of 5-6 runes: DJU BEI is the only repeated 6-gram (`obs-flat`) | none new | none | low |
| L8 | Alberti-style indicator runes whose VALUE sets the key re-alignment | https://en.wikipedia.org/wiki/Alberti_cipher | the 45% extra rune is an index letter | Edge-only insertion rejected (`insertion-doublets`); mid-word arc negative (phase 51); value-driven jump untestable (per-word null freedom = key phase freedom, `nulledge` gap) | none cheap | n/a | low |
| L9 | Per-word null presence set by a key draw with a threshold of 13 of 29 values (13/29 = 0.448; the R4 rate was tuned to 0.448) | numerical coincidence only | the per-word event would cost one key value per word | `advsep` (extra key step per word boundary) negative; the 42-45% rate is not exact to a 29th (12/29 = 0.414 and 13/29 are both inside the spread) | none (needs the key) | n/a | low: zero evidential weight, noted so nobody counts it as a finding |

## 5. Top 3 untested leads, specified to run later

### A. Two- and three-tap ciphertext autokey scan (L1)

- **Statistic.** For each tap pair (s, r), 1 <= s < r <= 12 (66 pairs) and coefficients a, b in 1..28 (784): residual vector R_j = c_j - a c_(j-s) - b c_(j-r) (mod 29) over all runes where both taps lie in the same section; chi-square of the 29-bin histogram against uniform. The constant d only cyclically shifts the histogram, so chi-square does not depend on it: 51,744 forms, d is free. Two scopes: (i) all pairs inside sections, (ii) both taps inside the same word. Optional extension: three taps (220 triples x 21,952 coefficient pairs, about 4.8 million forms, minutes with numpy).
- **Threshold.** Bonferroni over the forms, or the maximum chi-square over 1,000 shuffles of the runes inside each section (null of the maximum, same layout).
- **Positive control.** Encrypt Cicada-style English runes (the repository's English source) in LP2's section layout with a two-tap autokey (random s, r, a, b, d, primer of random runes), then apply the R4 add-ons (collision repair at q 0.81, one null in 45% of words, T repair). Required: the true (s, r, a, b) is the maximum, chi-square far above the null maximum. Power estimate: even if only 30% of residuals stay aligned, the excess chi-square is about 12,956 x 0.09 x 0.79 = about 900 against a null maximum near 80.
- **Null.** The same plants with an iid random key and no autokey: maximum chi-square within the shuffle null.
- **Also report** the single-tap results for the same sections as a regression check against `lag-feedback` (the (1, 1) doublet cell must reappear).
- **Cost** minutes of CPU, one thread. **Prior** low.

### B. Sparse lagged-Fibonacci key streams, orders 4-6 (L2)

- **Streams.** Recurrence k_i = e1 k_(i-s) + e2 k_(i-r) (mod 29), e in {+1, -1}, r in 4..6, s in 1..r-1. Keep those whose characteristic polynomial is primitive over GF(29) (test: the order of x modulo the polynomial equals 29^r - 1; expect about 1 in 5). One cycle then contains every non-zero seed: lengths 707,280 (r = 4), 20,511,148 (r = 5), 594,823,320 (r = 6; generate on the fly, not stored as 600 MB files). Non-primitive polynomials: scan one representative per cycle (list cycles; r = 4 and 5 are small enough to enumerate).
- **Scan.** The existing mid-word arc with the hold / spend / skip5 / coin channels at n 150 and n 300, both signs, every offset, on the section-start windows as in phase 57 (pilot 0.15 @ 0 cost 1.61 CPU-hours for 106.6 million cells, about 54 microseconds per cell).
- **Cost.** About 5 CPU-min per primitive polynomial for r = 4, 2.4 CPU-h for r = 5, 72 CPU-h for r = 6 (cells = offsets x 2 signs x 4 channels). Do r = 4 and 5 first (about 12 primitive polynomials, under 10 CPU-hours in total); run r = 6 only if there is a reason to.
- **Positive control.** The 12-plant R4 control of phase 57 with the key taken from one of these streams at a random offset (needs 12 of 12 within 3 nats of the best, band min above T300 = 29.8). **Null.** Matched iid-key plants (max -18.0 at n 150, -55.8 at n 300 in phase 57).
- **Do not run** before the owner decides: this is a campaign, not a check.

### C. Wrap-around / negative-index partners for the T repair (L3)

- **Partner rules for a target at position j (0-based) of a word of L runes, j < 6.** P1: partner (j - 6) mod L, excluding the target itself. P2: Python negative index on the partial buffer, partner 2j - 6 for j >= 3 (lags 3, 2, 1 at j = 3, 4, 5). P3: partner counted from the word end, L - 1 - (6 - j) when valid. Test the same relation as the main signal, c_j = 24 - 2 c_partner.
- **Statistic.** Hits over eligible pairs for each rule and each word length L = 2..10; z against 10,000 within-word shuffles that keep word lengths and sections; combine into one omnibus per rule and a Bonferroni over (3 rules x 9 lengths).
- **Positive control.** The phase 57 R4 simulation with the repair partner changed to P1 / P2 at rate 0.027 per eligible target (200 replicates each): the matching rule must be the maximum with z above 5. The main (in-word lag 6, j >= 6) hits must still be reproduced as a regression (80 vs 45.7).
- **Null.** R0 (no echo) replicates and the shuffles. **Cost** seconds. **Prior** low.

## 6. Searched and found nothing (do not repeat)

- Web, 2026-10-22: Solitaire bias (found, reproduced above); VIC cipher (components found; no definition of "sequestered digits" turned up in the search results); Alberti index letters (found: capitals mark re-alignment; numerals 1-4 hide codebook phrases); Playfair padding rule (found; ciphertext pairs cannot be equal inside a digraph follows from the rules); Chaocipher doubled-letter statistics (nothing published found; the simulation above is the only number); Isruna / Hahalruna (found: aett number + position, no Anglo-Saxon specific mapping found); homophonic "avoid repeating a homophone for double letters" convention (no source found; sources mention dedicated doubling and repeat signs instead); Gromark (found: primer plus pairwise-sum running key).
- No published hand cipher in any of these sources has a rule "write a function of the rune six back" or a per-word null with a capped count of one.
- Not searched here (other sessions cover them): Cicada community channels and repositories, and the primary 1999 Solitaire write-up (figures taken from secondary summaries and my own reproduction).

## 7. Killed by known signal

| Candidate | Signal that kills it |
|---|---|
| Any key-additive cipher with an independent key (Vigenere, Quagmire, Gronsfeld, Jefferson, M-209, lagged-Fibonacci keys used on their own) | S1: doublets would sit at the chance rate; S2: key-side lag leaves plaintext in c(j) - c(j-6) |
| Playfair, two-square, four-square, Hill, Bifid, Trifid, Nihilist | S1 (Playfair 1.7% predicted vs 0.66%; others 3.45%), S4 (English digraph structure), aligned digraph and parity tests |
| Per-word block ciphers | brief's quick test: gap doublets stay at 3.45% (LP2 has 23 of 86 across gaps) |
| Alberti disk with a per-segment constant shift | S4: English-shaped repeats at all lags inside segments |
| Straddling-checkerboard style variable-length coding, any per-rune extra unit | S3: per-rune scaling (G 160, phase 47 model E) |
| Chaocipher, dynamic substitution, Enigma-type, Solitaire | S1, S2 (simulation and stated properties above) |
| Isruna, Hahalruna and other monoalphabetic rune encodings | S4, parity, aligned digraph test |
| Cicada's own solved-page layers (Atbash, Vigenere with literal F, prime shifts) | S1 (no rule-based suppression), literal-F excess flat (`obs-flat`) |
| Per-word even-length padding (Playfair-style odd-word pad) | LP2 word lengths include 3-, 5- and 7-rune words in normal share; no padding found (commit 76be6d7, phase 60) |
