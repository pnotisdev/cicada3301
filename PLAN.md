# Liber Primus – solve plan

Source: `LiberPrimus.pdf` (75 pages, image-only). This is a "Print to PDF" of the original page images
(`00.jpg`–`74.jpg`), not a redrawn copy as I first thought; Phase 2 showed the artwork is the same.
The 2400×3600 originals are in `work/orig/` (mirrored from rtkd/iddqd) and are the primary source.
Original order: `00` title "Liber Primus", `01` A Warning, `02` "Chapter 1 – Intus" (Latin *within*), `03`–`74` rune
pages. The PDF swaps the first two, putting Intus before A Warning. In the original, A Warning is a preface, and the
Intus chapter starts with Welcome. There are no other chapter title pages.

Working folder: `work/`
- `work/orig/NN.jpg` – original page images; `work/pages/pNN.png` – PDF pages rendered at 150 dpi
- `work/ref/lp_verified.txt` – the transcription the toolkit uses (community master plus `errata.tsv`)
- `work/ref/lp_master.txt` – community rune transcription (rtkd/iddqd), `lp_keys.txt` – known keys
- `work/lp.py` – toolkit: Gematria Primus, parser, ciphers, scoring
- `work/ocr.py` – rune OCR and transcription verification (Phase 2)
- `work/tests/` – regression tests (`python -m unittest discover -s tests -v`, run from `work/`)

```bash
python work/lp.py segments
python work/lp.py solve 0
python work/lp.py show 0 atbash+0
```

---

## Result so far: Intus page 1 (PDF p.3, segment 0.0) – SOLVED

Method: **reversed Gematria (Atbash over the 29-rune alphabet)**, plaintext index = 28 − cipher index.
The big red ᚱ (index 4) maps to ᚪ (24) = **A**; the red ᛝᚱᚪᛗᚹ maps to **WARNING**.

> A WARNING. BELIEVE NOTHING FROM THIS BOOK EXCEPT WHAT YOU KNOW TO BE TRUE. TEST THE KNOWLEDGE.
> FIND YOUR TRUTH. EXPERIENCE YOUR DEATH. DO NOT EDIT OR CHANGE THIS BOOK OR THE MESSAGE CONTAINED
> WITHIN. EITHER THE WORDS OR THEIR NUMBERS. FOR ALL IS SACRED.

I spot-checked the transcription against the scan for this page and found no differences.
Takeaway for later work: Cicada asks us to keep both the **words and their numbers** (Gematria
values/primes), so number-based keys are in scope.

## Toolkit check against the other solved sections

| Seg | Title | Method | Toolkit result |
|-----|-------|--------|----------------|
| 0.0 | A Warning | Atbash | full |
| 0.1 | Welcome | Vigenère `DIVINITY`, 11 plaintext F's literal | full |
| 0.2 | Some Wisdom | plaintext | full |
| 0.3 | A Koan | Atbash + 3 | full |
| 0.4 | The Loss of Divinity | plaintext | full |
| 0.5 | A Koan | Vigenère `FIRFUMFERENFE`, 2 plaintext F's literal | full |
| 0.6 | An Instruction | plaintext | full |
| 0.16 | An End | key φ(prime_n) = p−1, 1 plaintext F literal | full (the hash itself is not in runes) |
| 0.17 | Parable | plaintext | full |

The periodic-IoC test picks out the period-13 key in 0.5. That shows the detector works.

## What the unsolved part looks like (segments 0.7–0.15, about 12,956 runes, about 58 pages)

- **IoC ≈ 1.00** (flat, like random). English runes give about 1.8, and Vigenère with `DIVINITY` gives 1.17.
- **No period from 2 to 59.** The best periodic IoC is about 1.09, so this is not a short repeating-key Vigenère.
- **Doublet anomaly:** 86 adjacent identical runes against about 447 expected, 5× fewer than random.
  This is the strongest structural clue. The process that made the ciphertext almost never puts
  the same rune twice in a row.
- Word, clause and page boundaries are kept, so word-length patterns can be used as cribs.
- Segment 0.10 (9 runes) is a two-word caption, ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ, above the 4×4 number grid on page 30 (see Phase 3).

---

## Plan

### Phase 0 – Infrastructure ✅
Render pages, get a transcription, write the Gematria toolkit, reproduce the known solutions, measure the baseline statistics.

### Phase 1 – Finish reproducing every solved section exactly ✅
Every solved section now decodes fully (`python work/lp.py known`). From `work/`, run the regression tests with
`python -m unittest discover -s tests -v`. There are 7 tests, including a golden file at `tests/expected_solved.txt`.

Findings:
- **Exact F rule:** in all three keystream sections (0.1, 0.5, 0.16), every plaintext F is left
  unencrypted and does **not** use up a key position. No other irregularities exist: the earlier break in
  Welcome was only a wrong F choice, not a transcription error.
- Ciphertext alone cannot always tell a literal ᚠ from an encrypted one. For example, "OF" became ᚠᚠ in Welcome. So
  `find_literal_f()` runs a beam search over the ᚠ positions and picks the best by dictionary score.
  It rediscovers every known position, so **it can be reused as-is when testing new keys on unsolved pages.**
- Fitness function: `word_score` measures how much of the text falls in frequency-weighted dictionary words.
  Solved English scores 0.77–0.90 (0.49 for 0.2). Unsolved ciphertext scores about 0.04, and the best wrong
  method on Welcome scores 0.15. That is a wide enough gap to use for automatic hypothesis screening in Phase 4.
- ~~Possible lead: the "SHADOWS AETHEREAL BUFFERS…" line in 0.2.~~ Resolved in Phase 3. It is interleaved with
  numbers in a 5×5 grid, and the words' Gematria sums make it a magic square with every line summing to 1033.

### Phase 2 – Transcription verification ✅
`python work/ocr.py verify` takes about 2 minutes. It segments every original image into lines and glyphs, trains a
glyph classifier from the transcription itself (cross-validated: odd pages are predicted by a model trained on even
pages and vice versa), aligns each image line with its transcription line, and writes review sheets to
`work/tmp/phase2/`.

Results:
- **The classifier agrees with the transcription on 99.96% of matched glyphs** (15,763 of 15,769). I reviewed
  every remaining flag by eye.
- **Unsolved section (pages 15–70, 12,956 runes): no transcription errors found.** 12,859 runes were
  confirmed one by one, 96 sit in ᚳ ligatures (see below) and 1 is a drop cap ᛉ checked by eye. Of the
  48 ligature partner runes, 43 were confirmed by classifying the right half and 5 ᛟ by eye.
- **1 error found, on a solved page:** page 8 (image 10), line 5. The image shows ᛒᛖᛚᛁᛖᚢᛖ (BELIEVE) but the
  master has ᛒᛖᛚᛖᛁᚢᛖ (BELEIUE). It is fixed in `lp_verified.txt` and logged in `ref/errata.tsv`. It does not
  affect any key, because that section is plaintext.
- **ᚳ ligature:** in this font ᚳ's lower stroke runs under the next rune, so the two form one connected glyph
  (68 cases). The aligner handles this with a "join" operation.
- **Non-rune symbols inside the text:** a "7"-like glyph on page 25, line 7 (unsolved section; the master records
  it as `7`), and numerals on pages 8, 9 and 51–53 (`1`…`5`). Phase 3 decided how to treat them (see below).
- Only partly checked: pages 3 (the Some Wisdom grid) and 71 (the hex hash), where digits confuse the
  segmenter, and the first rune of a few lines that touch the tablet frame on pages 4–11. All of these are
  solved pages. The rune lines on the other number pages (14, 30, 64–66) were checked.
- Limitation: the classifier learns its labels from the transcription. A rune that was misread *the same way
  everywhere* would not be caught. The solved pages decrypt to clean English, which rules this out for every
  rune that appears in them.

### Phase 3 – Characterise the cipher ✅
Tools: `work/stats.py` (`doublets`, `diffs`, residual and transition tests) and `work/sim.py` (cipher generators run
on English converted to runes, using Emerson's *Essays*, which include Self-Reliance). The facts below are guarded by
`tests/test_stats.py`.

**Doublet anomaly, in detail** (segments 0.7–0.15, 12,947 adjacent pairs):
- There are 86 doublets where about 446 would be expected. That is 0.66% against 3.45% (P ≈ 3·10⁻⁹⁹). Every
  unsolved segment shows it (0.52–1.08%). No solved section does (1.8–4.5%).
- **Only lag 1 is affected.** The coincidence rate at lags 2–100 is the normal 3.4–3.7%.
- **Only the difference d = 0 is missing.** c[i+1] − c[i] is flat over the other 28 values (χ² = 52.8, below the
  99.9% critical value of 55.5). Bins 1–28 average 459, which is exactly what you get if the suppressed repeats were
  spread evenly. A deterministic fix-up such as "+1 on collision" would inflate one bin and is ruled out.
- **It ignores text structure.** The rate is the same inside words (0.62%), across word gaps (0.81%) and across
  line breaks (0.77%), and it affects all 29 runes equally. Whatever causes it works on the continuous rune stream.
- The table of consecutive-rune pairs, excluding doublets, has no other structure (χ² 786 against 760 ± 45
  for simulated collision-avoiding text).
- Weak lead, not significant: doublets are more frequent in the first half of segments (53 vs 33, p = 0.03,
  found after looking).

**Which generators reproduce this fingerprint** (`python work/sim.py`):
- Tested and **ruled out**, because none suppresses doublets: Vigenère with a random key, the totient-prime
  stream (An End's method), English running key (forward or reversed), Beaufort, plaintext autokey (lag 1 or
  primer DIVINITY), ciphertext autokey (plain, with a random key, or prime-valued), prime-value plaintext autokey,
  progressive shift, cumulative sum, and a random key that never repeats itself.
- **Matches:** any keystream with a **collision rule**. When the next rune would equal the previous one, the
  encryptor uses a fresh key value (re-roll, or skip to the next key element) about 80% of the time. This works with
  a random key, a totient key or an English key, but see the IoC result below. What lets about 20% of
  collisions survive is still unexplained.

**Constraints that rule out whole families:**
- **No English-derived additive key.** The unsolved IoC is 0.9999 (random: 1.0000 ± 0.0006). Every English running
  key and plaintext autokey tested gives 1.039–1.057, about 65 standard deviations away. The key must be close to
  uniform, for example number-theoretic, PRNG-like or hash-like.
- **No literal-F rule** of the kind used in the solved sections, at least not with English plaintext. ᚠ is 3.54%
  of runes (random: 3.45 ± 0.17%), while literal F would give about 5.8%.
- **No simple autokey or progressive structure.** I checked residuals c_i − a·F(c_{i−1}) − b·G(i) with
  F ∈ {c, prime(c), 28−c} and G ∈ {0, i, p_i, p_i−1, Fibonacci, i²}, all a and b (about 25,000 combinations). The best
  residual IoC is 1.026, and that comes only from the missing doublets. Everything else is ≤ 1.007, which is noise.

**Structure that is preserved and can be exploited:**
- **Corrected 2026-10-16:** `lp.word_spans` used to treat every line break as a word boundary, but the
  transcription wraps words across lines (a real boundary at a line end is always written '-' or '.'). The numbers
  below are the corrected ones; the originals were 3.91 runes, 318 one-rune words and χ² = 44.8.
- Word lengths look like English: there are 2,928 words with a mean of 4.42 runes (aldegonde's count is also
  2,928). So word boundaries are probably real plaintext boundaries.
- There are **99 one-rune words** (3.4% of words, a plausible rate for A and I in English), which must be ᚪ (A) or
  ᛁ (I). Their ciphertext runes are uniform (χ² = 18.5, df 28). The earlier "marginal" unevenness was a
  fragment artefact. A correct key turns most of these 99 into A or I, against 7% by chance.
- The fix raises solved-section dictionary scores (Welcome 0.78 → 0.84) and does not change any deduction (D1–D4).
  Earlier real-data screens split wrapped words into fragments, a small handicap for a true key that the synthetic
  sensitivity tests (which have no line breaks) did not reflect.

**Numerals and the "7" glyph:**
- The numerals `1`–`5` in 0.14 begin sentences right after a clause separator. That matches the `1`/`2` list markers
  in solved section 0.4 ("…THE DECEPTION. 1 WE DO NOT HAVE ENOUGH… 2 WE HAVE…"). **Decision:** they are list
  markers. They are kept as `#n` tokens, they are not runes, and they **do not consume key positions**.
- The `7` glyph in 0.9 (rune 692) is a stand-alone word in the middle of a sentence. It is unexplained. **Decision:**
  keep it as a `#7` token that does not consume a key position by default. Phase 4 attacks on 0.9 should also try
  the variant where it does.
- `lp.numeral_positions()` gives the location of every such token for attacks that want to toggle this.

**Number grids:**
- The 0.2 word grid sums to 1033 and the page-14 square to 3301. Both are magic squares and both are explained.
- The **page-30 4×4 grid** (3258 3222 3152 3038 / 3278 3299 3298 2838 / 3288 3294 3296 2472 / 4516 1206 708 1820)
  is **not** magic and only 3299 is prime. *(Explained in Phase 4: each cell is |3301 − p_k| with
  Fibonacci-step prime indices, laid out as a spiral. The caption 0.10, ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ, is still unexplained.)*

### Phase 4 – Attack families, re-prioritised by Phase 3
Every attack must allow for the collision rule. Decryption under that rule is ambiguous in the same way
literal F was: at each rune the encryptor may have used key k_j or skipped to k_{j+1}. So the first task is to
**generalise `find_literal_f` into a beam-search decoder for the collision-skip rule**, and to test it on synthetic
text made by `sim.make_skip_key`.

**Progress so far (`work/attack.py`, `work/keystreams.py`, tests in `tests/test_attack.py`):**
- ✅ **Collision-skip decoder** (`attack.decode`). It is a Viterbi search over key alignments: states are merged on
  the key pointer and ranked by the cumulative dictionary score. It handles multiple skips at one rune, Atbash,
  and both signs. On synthetic Emerson text encrypted with `q = 0.8` it recovers 99.3–99.5% of the plaintext
  (totient, DIVINITY and random keys). A plain keyed decrypt of the same text gets 3–18%, and a wrong key
  scores about 0.09 against about 0.70.
- ✅ **Fast screen** (`attack.fast_screen`). It checks all 29 constant shifts b at once, with the key shift allowed
  to grow from word to word, and takes about 20 ms per segment and keystream. Planted keys come out at rank 1
  with the correct b, scoring about 0.6. Random keys reach at most 0.19.
- ✅ **Screen 1, negative** (`work/log/phase4_screen1.md`). I tested 1,007 keystreams: 52 integer sequences
  (primes, φ, σ, Fibonacci, Lucas, a^n mod 29, 3301·n…), 12 digit expansions (π, e, φ, √2, √3, ln 2 in bases 10
  and 29), 9 Cicada number sets (the squares, the page-30 grid, the An End hash) and 934 solved-text keywords
  and phrases. Each was run on 8 unsolved segments with 3 key offsets, ± sign, Atbash on or off and all
  29 shifts. **Nothing beat the random controls** (best 0.196 against a control maximum of 0.192). The top
  30 decode to noise under the exact decoder, and their A/I rates are at chance.

- ✅ **Screen 2, negative** (`work/log/phase4_screen2.md`). Every key start offset was tried: the 26 long
  sequences were slid over about 1,640 offsets each with `fast_screen_batch`, and the periodic ones over a full
  period. The grid- and caption-derived keys below were included. The best real keystream scored 0.205, below the
  random controls' 0.208. The top 15 decode to noise under the exact decoder (0.11–0.14, A/I at chance). A key
  planted at an arbitrary offset was found, scoring 0.73.
- **Page-30 grid structure:** explained in item 2 below. Every cell is |3301 − p_k| with Fibonacci-step prime
  indices, laid out as a spiral, and that includes the bottom row.

1. ~~**Number-theoretic keystreams with the collision rule**~~ — done (screens 1 and 2), negative at every offset.
   Still open: collision variants other than "skip to the next key element", and keys that are not added to the
   plaintext (for example multiplication or a substitution table).
2. ✅ **The page-30 4×4 grid is explained** (`work/log/phase4_grid30.md`, `work/grid30.py`). Every cell is
   |3301 − p_k|, where p_k is the k-th prime, k grows by Fibonacci steps (1, 2, 3, 4, 6, 9, 14, …, 988) and the cells
   are filled as a clockwise spiral from the centre. All 16 cells, including the "odd" bottom row, are reproduced.
   Used as key material it fails every way I tried: as keys for the caption, as a Hill matrix, as Gematria sums, as
   text positions, and as long keystreams. Its purpose and the caption ᚠᚢᛚᛗ ᚪᛠᚣᛟᚪ are still open.
3. ✅ **Crib-driven constraint solving, negative** (`work/log/phase4_crib.md`, `work/crib.py`, `work/cribsolve.py`).
   The cribs rule out four models: the same word always enciphered the same way, one key per word, a key set by
   position within the word, and a key restarting each line or page. FFT scans find no periodic key at any lag
   2–6000 and no key reused between segments. *(Corrected in Phase 7: the skip rule shifts the key, so this
   lag scan only covers periods up to about 60. The drift-aware scan extends the exclusion to about 400. Key
   reuse between segments is weakened the same way.)* The constraint solver recovers synthetic periodic keys (up to
   L = 1322) and shared-key pairs. On the real candidates it scores at control level. The apparent L = 1322 hit on
   0.15 turned out to be a time-limit artefact.
4. ✅ **Hash and random-generator keys, negative** (`work/log/phase4_items4-6.md`, `work/prng_screen.py`). I tried
   64 Cicada seeds with 6 generators (SHA-256/SHA-512/MD5 counter mode, a SHA-256 chain, MT19937, an LCG), bytes
   taken mod 29 or by rejection, under the skip-tolerant screen. Best 0.198; the top hits decode to noise. The
   Wulfic ledger also reports common PRNGs and key-derivation functions ruled out, over about 14.5 billion offsets.
5. ✅ **Transposition.** Transposition after encryption is ruled out: the doublet deficit holds in reading order
   inside words, across word gaps and across line breaks. Transposition before encryption cannot be tested
   without a key. A key running backwards from the end of each segment: `work/rev_screen.py` (result below).
6. ✅ **Steganography.** The known OutGuess payloads are the 2014 chain stages, already solved, and contain no LP
   key material. **The base-60 grid in 0.15** (pages 64–66) decodes to 256 uniform bytes. It is not the preimage
   of the An End hash under SHA-512, SHA3-512 or BLAKE2b, and none of 832,204 passphrase AES/RC4/XOR decryptions
   yields text (`work/grid60.py`).
- **Cross-check with the Wulfic/Cicada3301-Liber_Primus project** (constraints C1–C28): their results agree with
  ours, including the page-30 formula. Their C14 ("skip to the next key value" ruled out) assumes the survivors
  come from key repeats. Our skip-plus-missed-check model fits the fingerprint and is not covered by it, so our
  skip-tolerant screens add new coverage.
- **Deprioritised (ruled out by Phase 3):** additive running keys from English text (Self-Reliance, Agrippa,
  Liber AL, LP text), plaintext or ciphertext autokey, the literal-F rule with English plaintext, and short-period
  Vigenère.

### Research round (2026-10-16): other projects and online clues
Full write-up with sources: `work/log/research_2026-10-16.md`.
- **Landscape.** Dukotah/cicada3301 is the most rigorous ledger: "OTP-class", meaning either a true pad or a
  keystream derived from a short seed. Wulfic/Cicada3301-Liber_Primus keeps a constraint catalogue.
  cicada-solvers/aldegonde reports the only claimed structure besides the doublets: a within-word distance-5
  echo and the repeated phrase ᛞᛄᚢ-ᛒᛖᛁ. There is no verified solve anywhere, and the last signed Cicada message
  is from April 2017.
- **New from us:**
  - The shared transcription has BELEIUE where the image shows BELIEVE.
  - The 256-byte base-60 payload has 5 byte errors in the rtkd master: bytes 45, 50 and 246 are also wrong in
    Dukotah's canon, while bytes 165 and 172 are already right there. Their 6 "contested" bytes are confirmed
    as transcribed. Their payload-as-seed negatives (B-05 and others) are therefore conditional until rerun.
  - The haplography audit (their P-8) finds 0 merged doublets, so the anti-repeat filter is real.
  - An independent image-level re-read confirms the LP2 transcription.
- **Leads re-ranked:**
  1. A PHP `mt_rand` (`MT_RAND_PHP`) 2³² seed sweep with a skip-aware decoder. Dukotah's highest-prior open
     generator, blocked there for lack of a PHP binary; this machine has PHP 8.2.
  2. Rerun payload-as-seed tests on the corrected bytes.
  3. Verify aldegonde's d5 echo and the DJU-BEI repeat; if they hold, test word-scoped models (their
     "length-clocked walk").
  4. The unread ornament bands; the Marsaglia CD-ROM as a public pad.

### Phase 6 – New engines (2026-10-16)
- **PRNG pads (`work/phpmt`, Rust).** This is Dukotah's open lane P-4. The engine covers:
  - PHP < 7.1 `mt_rand` (`MT_RAND_PHP`), bit-exact against PHP 8.2 on 24 reference vectors;
  - glibc `random()`, i.e. PHP 5 `rand()` on Linux, matching the published `srand(1)` sequence;
  - .NET `System.Random`, 33/33 vectors from .NET Framework 4.x.

  Each seed is tested against 16 cipher variants (sign, Atbash, the language's own range call or `% 29`, and
  the skip or coin anti-repeat model) with an early-abort, skip-aware decoder. Planted seeds are recovered at
  rank 1 for all three generators (score 44 against at most 16 for noise). A full-segment re-decode of the
  candidates (`verify_top.py`) separates a true key at z ≈ +70. Sweeps of all 2³² seeds on segment 0.7 run
  at about 0.85 M seeds/s; results are in `results/prng/`.
- **Word-scoped families (`work/walk`, Rust).**
  - Within-word distance profile: English gives 6.3–7.5% coincidences at distance 5, LP2 4.92%, random
    3.45%. So aldegonde's echo, reproduced here, is about half of a same-alphabet leak, and distances 1 and 6
    are suppressed together.
  - The family F1(m) is c = D(Q_{j mod m}(p) + k_w), with freely designed alphabets and a per-word key.
    Direct annealing (`walk solve`) stalls because each word picks its own best key; incremental scoring
    is exact but the landscape is flat.
  - **Key-free D-search (`walk dsearch`):** within a word, x = D⁻¹(c) has differences in which the word key
    cancels. Annealing D to maximise how uneven those differences are recovers a synthetic F1(5) alphabet
    **exactly (29/29)**: true-D G 2,456 against about 300 for the null.
  - **On LP2 it finds nothing.** m = 5: 352 against surrogates 350/351/333. m = 1: 153 against 177/144/148.
  - **Ruled out: a per-word additive key behind any secret outer alphabet**, with or without period-m inner
    alphabets. aldegonde had ruled out only keyword-built alphabets in this space.

### Phase 7 – Overnight campaigns (2026-10-16)
The runner is `jobs/overnight.py`; `docs/CAMPAIGNS.md` explains what each campaign tests, its controls and its
decision rule.

- **Correction: periodic keys.** The "no periodic key up to lag 6000" claim (Phase 4 item 3) assumed the key
  stays aligned with the runes. Under the skip rule, the key pointer gains one position at every skip
  (r ≈ 0.028 per rune, from the doublet deficit). Repeats of a period-P key therefore sit at lags P − Δd, with
  Δd ≈ Poisson(r·P), and the plain lag scan loses them beyond P ≈ 60. `work/drift_period.py` applies a matched
  filter over those drift bands and their harmonics.
  - Power on Emerson enciphered with random periodic keys under the rule: Z(true P) beats the random-text
    maximum in 8/8 trials for P ≤ 400, 7/8 at P = 800, 6/8 at P = 1600 and 0/8 at P = 3200.
  - LP2: max Z 3.03, against random-rune nulls of 2.29–3.55 (8 texts). **Periodic keys are ruled out up to about 400 runes
    only.** Longer periods remain open.
- **Word lengths** (`work/wordlen.py`). The LP2 histogram rejects English in GP runes (G = 227, p ≈ 10⁻⁴²; against
  the solved sections p ≈ 10⁻³⁵). English counted in letters, with no digraph runes, fits better but is still
  rejected (p = 7·10⁻⁸). The best simple fit is English runes with **one extra rune in about 40% of multi-rune
  words** (p = 0.025). This is a lead: nulls or padding inside words, another plaintext convention, or another
  language. Dictionary screens lose power under all three; IoC screens do not.
- **New engine `work/kscreen`.** It is a language- and alphabet-agnostic keystream screen. For each keystream,
  start offset, key multiplier and anti-repeat model (skip or coin), it runs a beam decode over key pointers
  and scores the decoded letters by IoC. The IoC is unchanged by Atbash, by any substitution of the plaintext
  alphabet, by a constant shift and by the language. So one pass covers c = D(p) ± m·k + b for every D and b,
  in any language.
  - **Families:** a 1,447-keystream library (`work/kscreen/export.py`). It has the earlier number streams and
    the 809 solved-text keyword keys, plus:
    - new prime and multiplicative functions;
    - 13 more constants in base 29;
    - SHA-256/SHA-512/MD5 counter and chain streams (520) of 65 seeds: Cicada strings and numbers, the An End
      hash, and the corrected payload forwards and reversed;
    - the payload bytes themselves.

    Beyond the library, every linear recurrence of order ≤ 3 mod 29 from every start state, and every
    polynomial key up to degree 3.
  - **Controls** (`work/kscreen/selftest.py`, `tests/test_kscreen.py`): 15/15 planted windows are recovered at
    their exact offset (IoC 1.61–2.06). The plants cover totient, π base-29, SHA-256 stream, Fibonacci and
    polynomial keys, both models, both signs, with and without a random plaintext alphabet. Random keys stay
    below 1.31 over 10⁷ decodes. The decision threshold is 1.40, followed by whole-window verification.
    Verification includes a keystream-matched null: the same keystream at 20 random offsets on the same
    window. It is needed because structured keystreams can let the beam overfit (plain English decoded with a
    period-3 recurrence key reached 2.29).
  - **Result on LP2, library × the 8 sections** (409 M decodes, 19 min on the laptop):
    - best 1.366, against 1.318 for the matched null of 300 random keystreams;
    - all 15 top hits fall to 1.05–1.13 over their whole section (their own keystream at random offsets:
      1.05–1.09);
    - **negative.** This extends the screen 1/2 negatives to **any plaintext language and any substituted
      plaintext alphabet**, under both anti-repeat models.
  - The other kscreen campaigns (restarts, recurrences, multipliers) are queued in `jobs/overnight.py`.
- **glibc `random()` sweep (segment 0.7, all 2³² seeds): negative.** Best screening score 21. The top-20
  full-segment scores are 0.088–0.112 against 0.077 for random seeds, the same selection-bias pattern as PHP
  (`work/log/phase6_prng.md`).
- **.NET `System.Random` sweep (segment 0.7, all 2³¹ seeds): negative.** Best screening score 19. The top-20
  full-segment scores are 0.086–0.110 against 0.077 for random seeds. All three generators are now negative for
  a whole-book pad starting on LP2 page 0. A fresh seed per section is the `prng-all` campaign.

### Phase 8 – The desktop PC: live console, CUDA ports, concurrent lanes (2026-10-17)
Details: `work/log/phase8_gpu.md`, `docs/GPU_PORT.md`.
- **Setup.** `desktop` (Ryzen 7 2700X 16 threads, 32 GB, RTX 2080 Ti): Rust 1.99 installed, venv in `.venv`, selftest
  passed (54 tests with the new ones, 15/15 planted windows, null 1.306).
- **Runner.** Live timestamped console with step counter, device, progress/eta, heartbeat and summary; throttled
  logs; `--device auto|cuda|cpu` with validation and CPU fallback; `--lane` for concurrent runs.
- **CUDA ports** of the kscreen screen and of the PHP / glibc / .NET seed sweeps, bit-identical to the Rust
  engines (decode by decode, full histograms, planted keys and seeds). Speed against the 16-thread CPU: screen
  2.3-4x (1.8x on the 46 page windows), seed sweep 6.8x.
- **Two CPU-engine problems fixed:** the kscreen top-hit list could drop good hits (per-window bests and
  histograms were never affected), and the beam cut now uses a stable sort. No earlier conclusion depends on either.
- **Queue started** as two lanes: GPU (kscreen restarts / recurrences / multipliers, prng-all) and CPU (rescreen,
  dsearch, payload). Results go to the usual `PLAN.md` / `results/` places as they finish.

### Phase 9 – Page art, section statistics, ciphertext feedback (2026-10-17, overnight)
Details: `work/log/phase9_overnight_results.md`, `phase9_art.md`, `phase9_chain.md`.
- **Queue.** Two lanes (GPU: kscreen restarts / recurrences / multipliers, prng-all; CPU: rescreen, dsearch, payload). The
  short heading windows (91 and 121 runes) need their own null: head0.13@1433 peaks at 2.12 against a null of 1.90-2.08
  over 24 replicates (p ~ 0.01 for that window, not significant overall; its best offset is unrelated to the other
  windows'); head0.14@1468 equals the null median.
- **Other AI's branch `research/restart-columns`** merged after review: no key restart at any unit type (a word-unit bug
  fixed, tests rewritten).
- **Section statistics:** all eight unsolved sections share the doublet deficit, flat IoC and word-length shape; the
  within-word distance-5 excess is +3.7 sigma pooled (about p = 0.002 after looking at 9 distances), spread over sections
  and word lengths.
- **Page art:** mirror-symmetric borders; the five-dot figure (pages 24, 40, 73) is one rigid shape reused; three-dot rows on
  pages 50 and 56 share a shape; pages 50-56 carry a six-sign cuneiform-style cluster (unidentified).
- **New hypothesis family, ciphertext feedback c_i = a c_{i-1} + p_i + k_j:** it reproduces the doublet fingerprint natively
  and no earlier screen could see it. Reduction to the existing engine (P lines), positive and null controls, CPU/GPU
  agreement; no short periodic key in any of the 28 transforms. Campaign `kscreen-chain` queued behind the GPU lane.

- **Seven more generators for the seed sweeps** (py3, mt32, mt31, java, msvc, drand48, ruby; `work/log/phase9_gens.md`):
  validated against CPython, NumPy and published vectors, bit-identical on the GPU, planted seeds recovered; campaign
  `prng-more` queued (window 0.7 first, then every section).
- **Image-level audits:** the transcription's separators are right (9,828 gaps, none missing, none extra); the images carry a
  tick glyph the transcription lacks (4 apostrophes, quote marks): `work/ref/tick_marks.tsv`, `phase9_separators.md`.

- **Second pass (early morning, `work/log/phase9_overnight_results.md`):** the six short page windows the library screen
  flagged are chance (Gumbel p 0.19-0.85); backward-key screening added to both engines with planted-key controls;
  branches `restart-columns`, `word-internal-lag5` and `wordlen-languages` reviewed and merged (tests rewritten).
  The lag-5 repeated-bigram excess replicates independently (P < 1e-4 after the look-elsewhere over lags, 4e-4 to 5e-3
  with conditioning), sits in 10-rune words (lag 5 = half the word, +4.2 sigma, post hoc), and has no mechanism yet.
  Word lengths: the TH digraph explains most of the 2-rune-word deficit (G 223 -> 56); a residual remains.

### Phase 5 – Validation and reporting
- A plaintext counts as solved only if it scores well across a whole segment (word hits and IoC about 1.8)
  and the same rule works on the next page.
- Log every hypothesis tested, with its parameters and score, in `work/log/` so nothing is re-run blindly.
- Record negative results too. The unsolved section has resisted public effort since 2014, so
  ruling hypotheses out with clear reasons is useful progress.
