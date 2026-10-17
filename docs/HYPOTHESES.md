# Untested hypotheses (2026-10-17)

Written after reading `PLAN.md`, `docs/CAMPAIGNS.md`, `work/log/research_2026-10-17.md`, `work/log/phase9_families.md` and
the keystream library (`work/keystreams.py`, `work/kscreen/export.py`). Nothing below has been run. Each item says why
every earlier screen is blind to it, the first test, its controls and what kills it. The decision rules of
`docs/CAMPAIGNS.md` apply unchanged, and the prediction is written here before anything is run.

## The two constraints every candidate must meet

1. **The key must be close to uniform.** LP2's IoC is 0.9999 ± 0.0006. A key whose unigram distribution is not
   uniform shows through: English running keys give 1.04–1.06, and a short keyword gives about 1 + 0.8/L. This rules out
   a short keyword in any arrangement (interrupted, restarted, per word), book letters picked at number positions, and
   rune-poem or Liber AL text used as a key directly. `keystreams.predicted_ioc` already computes this. Every new stream
   should pass it (within ±0.002 of 1.000) before it is screened.
2. **The anti-repeat rule needs an explanation:** a deficit of about 81% at lag 1 only, Δc = 0 only, regardless of word
   boundaries. Either the family produces it natively, or the decoder must model the skip.

**Information budget for skip tracking.** A decoder that has to find the skips (about 1 every 36 runes, each costing
ln(1/0.028) ≈ 3.6 nats, so about 0.1 nats per rune) needs more than 0.1 nats of evidence per rune from the correct
alignment. That evidence is about ½(IoC − 1) of what the decoder sees per conditioning class:

- about 0.4 nats when each class holds plain (permuted) English. This covers H1 with a keyword and H2. Trackable.
- about 0.025 nats when the decoder sees English plus another English text. This covers a structured stream plus an
  unknown running text. Not trackable under the skip rule, so it is left out below, except where a family has no skips.

## Summary

| # | Hypothesis | Why every earlier screen misses it | First test | Cost | Prior |
|---|---|---|---|---|---|
| H1 | Two layers: a structured stream plus a short keyword (An End's method on top of Welcome's) | kscreen sees IoC ≈ 1.1–1.2 on 300 runes (threshold 1.40), and its skip check is wrong once a second layer is present | Drift-tracking decoder that learns the keyword's column shifts; library streams × L ≤ 20 | 1–2 days engine, ~2 h run | medium |
| H2 | Arbitrary tableau or transition table driven by a known stream | kscreen assumes addition in Gematria order; an outer alphabet or an unknown key→row map breaks it | σ-invariant joint-coincidence statistic on (key value, cipher rune) | shares H1's engine | medium-low |
| H3 | Clocked key pointer: the pointer steps by g(previous rune) or by a constant d ≥ 2 | Every screen steps the pointer by 1 (plus skips), or by −1 | Constant decimation d = 2..29 (export only), then ciphertext- and plaintext-clocked steps | 2 h, then ½ day | medium |
| H4 | The numbers of a known text as the key (prefix sums, per-word Gematria sums) | The library holds texts only as periodic keywords, which fail constraint 1 | Export about 40 streams per text; kscreen-sections | 2–3 h | medium-low |
| H5 | Ciphertext as key: long-lag ciphertext autokey (L ≥ 9), another section's ciphertext, solved ciphertexts | The fingerprint covers lags ≤ 8, and kscreen-chain only lag 1 | LP2's own ciphertext and the solved ciphertexts as library streams, × multipliers | 2 h | low-medium |
| H6 | A public random table or a deep constant offset (RAND *Million Random Digits*; π, e, φ past offset 20,000) | Library streams stop at 20,000 terms | Export at the deep offsets, kscreen on GPU | 2 h + download OK | low |
| H7 | Seeded PRNG with a non-English or unconventional plaintext | Every c-domain seed sweep scores English (dictionary or bigram); only prng-step uses IoC | prng-step's IoC machinery in the c-domain with the skip beam | GPU ~14 h | low |
| H8 | Null on collision: the encryptor emits a null rune instead of only skipping | No decoder can delete a cipher rune | Keyless, parameter-free word-length prediction first | 30 min | medium (as an explanation) |
| H9 | Two-time pad between sections under skip drift (open lead 3) | Earlier lag scans assume no drift | Banded matched filter as in `drift_period.py`, cross-section | ½ day | low (low power) |

Suggested order: H5, H4, H6 and the H3 decimation step are exports for the existing kscreen and run together as one
campaign. H8 is next because it is keyless. Then comes the new engine for H1 and H2, then H3's clocked steps. H7 waits
for the user's GPU OK (item 50 of the session log).

## Status (updated 2026-10-17, details in `work/log/phase9_hyp.md`)

| # | Status |
|---|---|
| H1, H2 | not run (need the drift-tracking decoder) |
| H3 | **negative**: constant decimation (`kscreen-hyp`) and the six clocked pointers (`kscreen-clock`, 0 of 90 hits verified) |
| H4, H5, H6 | **negative** (`kscreen-hyp`, 0 of 31 hits verified; per-word sums, base-10 digits and the solved ciphertexts fail constraint 1 and were not screened) |
| H7 | not run (GPU) |
| H8 | **alive** as a partial explanation of the word lengths (G 56 -> 40 at the predicted rate, 0 fitted); it hides nothing from the keystream screens (planted H8 keys found by the unchanged kscreen) |
| H9 | **undecidable**: power 0.05-0.42 for a planted full-section reuse |
| H10 | **null** for the whole family (4,608 rules x 29 start states), also with the anti-repeat skip modelled exactly (Viterbi over the states; planted machines recovered) |
| H11, H12 | not run |

---

## H1. A structured stream plus a short keyword

**Model.** c_i = D(p_i) + t_j + w_(j mod L) + b (mod 29), with the anti-repeat skip on the combined key. Here t is a
library stream (totient, primes, π in base 29, hash streams…) and w is a keyword with L ≤ 20. The two keyed solved
sections use exactly these two pieces separately: Welcome uses the keyword DIVINITY, and An End uses φ(prime).

**Why it is unseen.** It passes constraint 1 because t makes the key uniform. kscreen decodes with t alone, so it sees a
Vigenère text with IoC ≈ 1 + 0.8/L, below its 1.40 threshold. Its skip check, c_i − t_(j+1) + t_j = c_(i−1), is also
wrong whenever w changes between j and j + 1, so it loses alignment at the first skip, after about 36 runes. The
periodicity scans on c see nothing either, because t is not periodic.

**Test.** For each library stream, offset and L, run a Viterbi pass over pointer drift with a skip prior of 0.028 and
free skip branches. Score with the periodic IoC of the decoded columns, learning the L column shifts on the fly (EM over
w). The information budget (about 0.4 nats per rune) allows drift tracking. Screen on 300-rune windows: on truth the
periodic IoC is about 1.8 against 1.0 ± 0.07 for L = 8, about 11σ. Then verify on the whole section.

**Controls.** Positive: Emerson text with totient + DIVINITY, π base 29 + FIRFUMFERENFE and SHA-256 counter + a random
L = 13 key, skip rule q = 0.81, all recovered at the exact offset and L. Blindness: the current kscreen recovers none of
them. Null: random streams, and each library stream at 20 random offsets on the same window (overfitting by the free
skips must show up here).

**Kill.** No window beats every null replicate after whole-section verification.

## H2. An arbitrary tableau, or an arbitrary transition table, driven by a known stream

**Model (a), tableau.** c_i = T[v_j](p_i), where v_j is the raw value of a known stream (any range R, not only mod 29)
and T is any table of 29 permutations: keyed alphabets, Quagmire I–IV, an unknown outer alphabet σ around an additive
cipher, or a program's own unknown value→rune map. **(b), transition table.** c_i = N_(c(i−1))[s_i] with
s_i = p_i + k_j over 28 values, where each previous rune has its own ordered list of the 28 other runes. This produces the
doublet deficit natively, with the survivors as a rare "ditto". Step28 variant C is the special case where every row is
in Gematria order.

**Why it is unseen.** kscreen is invariant to an inner substitution D only. An outer σ, or an unknown key→row map, breaks
the subtraction c − k. dsearch handles an outer alphabet only for a per-word key.

**Statistic (invariant to T, σ and the key map).** Count the pairs i < i′ with v_j = v_j′ and c_i = c_i′ (for (b): pairs
that also share c_(i−1)). Equal key value and equal cipher rune imply equal plaintext, so the count is about 1.8 times
its null on the true stream and alignment. Per section (N ≈ 1,600, R = 29) the null is about 1,520 pairs with sd ≈ 39,
and the excess about 1,220 (about 30σ) once drift is right. For R = 256 it is about 10σ. Drift is tracked with H1's
Viterbi, scored by the increment of the count. Variant (b) on all of LP2: about 3,400 null triples against an excess of
about 2,700.

**Controls.** Plant random tableaux and random transition tables with library streams. Null: random streams, and LP2
runes shuffled within sections. The beam's overfitting is measured on the null, not assumed.

**Kill.** As for H1. A negative on the library extends every kscreen negative to any tableau and any key map.

## H3. A clocked key pointer

**Model.** The pointer moves by j ← j + g(·) instead of j + 1:

- **Constant decimation** g = d (2..29). Every stream taken every d-th term.
- **Ciphertext-clocked** g(c_i) ∈ {1 + index, prime value, φ(prime)}. Deterministic given c, so for each window it is a
  fixed index pattern o + S_i.
- **Plaintext-clocked** g(p_i). This is "the numbers are the direction" read literally, with the plaintext's own
  Gematria number moving the key. It needs D = identity or Atbash, so that g can be evaluated on the decoded rune; the
  beam state already carries the pointer.

**Why it is unseen.** The key values are still the stream's, so the fingerprint is "random + avoid-repeat"
(`phase9_families.md`, result 1). Every screen moves the pointer by ±1.

**Test.** Decimation as plain exports (28 × 1,447 streams; the multipliers can be dropped to keep the cost down).
Ciphertext clocking as an index-pattern option in the engine. Plaintext clocking as a beam option, 29 shifts × Atbash on
or off.

**Controls.** Plant each clock with totient and π keys and recover the exact (stream, offset, g). Matched null per g.

## H4. The numbers of a known text as the key

**Model.** k = a numeric transform of a known text that comes out uniform: (a) prefix sums of rune indices or of prime
values; (b) the Gematria sum (prime values) of each word, mod 29, one value per rune; (c) the same for lines or
sentences. "Either the words or their numbers" (0.0); the 0.2 square already uses word sums.

**Sources.** The solved LP plaintext (in the repository); Self-Reliance (in the Gutenberg corpora, git-ignored); Liber AL
vel Legis and the Old English Rune Poem (need a download OK; git-ignored, never committed). Forward and reversed.

**Why it is unseen.** The library holds solved text only as periodic keywords, which fail constraint 1. It has
cumulative sums only of primes and φ(n).

**Test.** Export to the library after the `predicted_ioc` filter, then `kscreen-sections` plus verification.
**Controls.** One plant per transform, matched null.

## H5. Ciphertext as the key

**Model.** c_i = D(p_i) + a·T_(j) with T = LP2's own ciphertext (long-lag ciphertext autokey, any lag L ≥ 9, or a key
taken from another section) or the ciphertext runes of Welcome, the 0.5 koan and An End. Uniform keys, so constraint 1
holds wherever `predicted_ioc` says so (Welcome's ciphertext probably fails it; An End's passes).

**Why it is unseen.** The family fingerprint excludes ciphertext autokey only at lags 1–8 (lag-m difference IoC 1.024),
and kscreen-chain covers lag 1 only. With a = 1, a lag-L autokey leaves coincidences at lag L at the rate of plaintext F, which
cannot be seen beyond the scanned lags.

**Test.** The streams forwards and backwards in the library, × the 28 multipliers. **Pitfall:** mask the offsets where
the stream is the window itself (|L| < 9), because x = c − c is degenerate and scores a huge IoC.
**Controls.** Emerson enciphered as c_i = p_i + c_(i−L) with a random primer and the skip rule, L ∈ {37, 500, 3301}.

## H6. A public random table, or a deep offset into a constant

**Model.** A true pad from a public source: RAND's *A Million Random Digits* (maps: two digits mod 29, rejection at
≥ 87, three digits mod 29), or π, e, φ and √2 digits from a Cicada-meaningful deep offset (3301, 1033, 3301·1033,
10⁶). The library's streams stop at 20,000 terms.
**Test.** Export, GPU kscreen. The RAND file needs the user's download OK (name, source and size stated first). The
constants are computed locally with mpmath. **Controls.** A plant at a deep offset, matched null.

## H7. A seeded PRNG with a non-English plaintext or convention

Every c-domain seed sweep (php, glibc, .NET, prng-more, prngx, hashscan, KDF) scores English, through the dictionary or
the bigram table. Word lengths reject every tested language (`docs/prs/wordlen-languages.md`), but they also reject
plain English, and a convention such as nulls or extra runes (H8) degrades both English scores. The IoC is
language-free and already gated for 240 decoded symbols (`prng-step`: random maximum about 1.42, true seed about 1.8).
**Test.** Run the prng-step scoring on c-domain decodes with the skip beam, window 0.7, ten generators.
**Controls.** prng-step's planted seeds, re-planted in the c-domain. GPU only, after the user's OK.

## H8. A null on collision

**Model.** When the next rune would repeat the previous one, the encryptor (81% of the time) emits a random null rune and
enciphers the plaintext rune with the next key value. Lag 2 is unaffected, which matters: the variant that re-emits the
same rune after the null would give c, N, c and a lag-2 excess that LP2 does not have.
**Parameter-free prediction (written before any test):** nulls arrive at about 360 / 12,956 ≈ 0.028 per rune, so a
word of n plaintext runes gains Poisson(0.028·n) runes. That is about 12% of words, more in long words, which is the
direction of the "more 7–8-rune words" residual left after the TH correction. **Test.** Fit this model with
`work/wordlen.py` against the "+1 rune in 40%" and TH models, with the insertion rate fixed at 0.028 and also free.
**Kill:** a fitted rate far from 0.028, or no gain over the TH model. **If it survives:** add a third anti-repeat model to
kscreen, "delete a cipher rune after a would-be collision", with planted controls, and rerun the library.

## H9. A two-time pad between sections under skip drift

This is open lead 3 in the session log. Pad reuse gives a coincidence rate of 6.2% against 3.45%, but the evidence per
rune (about 0.025 nats for the full difference likelihood) is below the cost of tracking a skip, so local alignment
cannot follow it. Only a banded matched filter over the drift spread, as in `work/drift_period.py`, has a chance.
Measure its power with planted reused sections first; if it cannot find a planted full-section reuse, record that the
question cannot be decided with this method and stop.

## Added after reviewing two outside lists (2026-10-17)

Most items on the two lists the user pasted were already covered or are excluded by the data. The answers are in
`docs/SESSION_LOG.md` (items 53–54). These are the parts that are new and testable:

| # | Hypothesis | Why it is open | First test | Cost |
|---|---|---|---|---|
| H10 | A small 29-state machine: C = E(P, S), S′ = F(S, P, C) with F from {S+P, S+C, P−C, P+C, φ(S), prime(S), S·P, S·C} and compositions of two | kscreen-chain covers S = a·c(i−1) only. Without an external key the decode is deterministic given S₀ | Enumerate E, F and S₀ (29 values) on all of LP2; IoC per section; random-rune and planted controls | seconds |
| H11 | A fresh seed per page (any per-page derivation from a global seed lands on some 32-bit seed) | prng-all swept sections, not pages | Sweep each page start (46 windows) with all seeds, boundary-free score; per-window extreme-value null as for the short page windows | GPU hours; needs the user's OK |
| H12 | Generators not yet swept: ISAAC (seeded by a short string), binary LFSRs with a nonlinear filter | Not in the ten swept generators | Add to `work/prngx` with reference vectors and planted seeds | ½ day |
| H1/H2 add-on | Random key-pointer jumps from a second stream, not tied to collisions | Every decoder skips only where a collision is consistent | A jump prior in the drift-tracking decoder planned for H1/H2 | with H1/H2 |

## Checked today and dead

- **The S echo as "-SELVES" (THEMSELVES / OURSELVES / YOURSELVES, S at n − 6 and n − 1).** Prediction: the 11
  within-word lag-5 S–S pairs end on a word-final S. Observed 3 of 11, against about 4.4 expected by chance. Dead. The
  pairs sit in words of 6–12 runes at starting positions 0–3.
- **A fixed-point rune** (one cipher rune always standing for one plaintext letter). This is what a multiplicative key
  c = k·D(p) + b gives, as do prime-value algebras with an absorbing element and literal pass-through like the solved
  pages' F. The test is a table of rune × position in word (initial, medial, final, one-rune word) over LP2: χ² 74.1
  on 84 df, p 0.77, largest cell |z| 2.13. Control: in Self-Reliance, a letter of 1.5–6% frequency carried by one
  458-count row would add χ² 30 (L) to 1,010 (TH) to that row alone. Excluded for English plaintext. Rune counts are
  flat (399–492, mean 447), and doublets per rune are at most 7.
- **The 256-byte payload as a permutation, S-box or Latin square.** It has 161 distinct values, against 161.8 expected
  for random bytes; in the 16 × 16 layout, 10 rows and 12 columns are all-distinct, against about 10 for random bytes.
  It is byte-random, not a permutation.
- **Constraint 1 removes, before any screening:** per-word Gematria sums of a text (common words repeat the same sum),
  base-10 digits of constants (10 values out of 29), and the ciphertexts of the keyed solved sections (Welcome's
  Vigenère text is not flat).

## Not worth running

- A short keyword in any arrangement (interrupted key, restarts at a plaintext letter, per word), and any key read from
  English letters. All fail constraint 1.
- A null "space" symbol in the cipher alphabet. It would give geometric word lengths, with about 22% one-rune words
  against 3.4% in LP2.
- Word-order transposition before encryption. It would explain the zero adjacent-length correlation but not the
  histogram, and it creates no blind spot: dictionary word scores and IoC ignore word order.
