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
- **Corrected again 2026-10-17:** a page break without '-' or '.' is a wrap too. 32 of the 55 page breaks in LP2 fall
  inside a word, and the page images show no separator dot there (`results/analysis/page_seams_2026-10-17.txt`). The
  numbers below are corrected; the 2026-10-16 values were 2,928 words, a mean of 4.42 runes, 99 one-rune words (3.4%)
  and χ² = 18.5.
- Word lengths look like English: there are 2,896 words with a mean of 4.47 runes (aldegonde's 2,928 also cuts at
  page breaks; cicadanotebook.com has 2,896). So word boundaries are probably real plaintext boundaries.
- There are **83 one-rune words** (2.9% of words, a plausible rate for A and I in English), which must be ᚪ (A) or
  ᛁ (I). Their ciphertext runes are uniform (χ² = 20.8, df 28): 28 runes occur, all but ᚳ. The earlier "marginal"
  unevenness was a fragment artefact. A correct key turns most of these 83 into A or I, against 7% by chance.
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
- **Word lengths** (`work/wordlen.py`; numbers corrected 2026-10-17 for page-break wraps, earlier G = 227, p ≈ 10⁻⁴²,
  40% at p = 0.025). The LP2 histogram rejects English in GP runes (G = 242, p ≈ 10⁻⁴⁵; against the solved sections
  p ≈ 10⁻³⁷). English counted in letters, with no digraph runes, fits better but is still rejected (p = 8·10⁻⁹). The
  best simple fit is English runes with **one extra rune in about 42% of multi-rune words** (p = 0.085, no longer
  rejected at 5%). This is a lead: nulls or padding inside words, another plaintext convention, or another language.
  Dictionary screens lose power under all three; IoC screens do not.
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

- **GPU lane (00:36-04:35, `work/log/phase9_overnight_results.md`):** kscreen restarts/recurrences/multipliers and the full prng-all sweeps (PHP,
  glibc, .NET over all seeds, all 8 sections) are negative with verification. Step-domain family (research note C1/C2: plaintext enters the step
  c_i - c_{i-1} keyed mod 28, variants A additive / B log / C rank): library screen (mod-29 and native mod-28), periodic keys to lag 3000 and the
  word-index polynomial / grid key checks are negative with planted controls; seed sweeps of ten generators (`prng-step`) validated and queued
  (`work/log/phase9_step28.md`). An independent review corrected the IoC null tail (exact multinomial, random maximum ~1.42 at 240 steps).

- **Word separators (07:30, `work/log/phase9_boundaries.md`):** LP2's word-length sequence has NO serial structure (mean PMI -0.060 under an English table;
  English +0.050, the solved sections +0.006, z +4.2), and no simple distribution fits the histogram. With LP2's separators imposed on English plaintext a planted
  seed scores 0 instead of 33 in the dictionary sweeps, so every boundary-aware dictionary search (prng-all, prng-more 0.7, rescreen, dsearch) is a non-result if
  the separators are not the plaintext's word boundaries (the within-word lag-5 echo argues partly against that). Remedy: boundary-free seed sweeps
  `prng-bg` (`work/phpmt/bg.py`, bigram log-likelihood, same ten generators; gates in `work/tests/test_bgmt.py`). The Gutenberg table of
  `wordlen_languages.py` reproduces byte for byte.

- **Morning of 2026-10-17 (10:20):** boundary-free seed sweeps (window 0.7, ten generators, all seeds), the backward-key campaign (a = 0..25), the hash streams of every
  solved-text word and phrase (12,944 streams) and the step-domain screens are all negative with controls; GPU handed back at 10:00 (resume commands at the end of
  `work/log/phase9_overnight_results.md`). Nothing in LP2 is solved.

- **Midday of 2026-10-17:** community claims handed over by the user (a 27 x 27 'totient map' repo and PDF; the 'FIND YOU ARE NECESSARILY ALONE ...' crib with Fibonacci key matrices; page numerology)
  were reproduced and given selection-aware nulls (`work/log/phase9_community_claims.md`): no 27-wide structure in 0.7 (the mirror count would see about 100 hidden mirrors); the Fibonacci key of
  the crib is word-choice selection (20 / 28 / 39 alternative words fit the first three slots); matrix repeats 5 against a null mean 2.4 (P 0.05); the heading + body keys are in none of 199,088 OEIS
  sequences (exact difference lookup, planted control found); first row 563 / first column 569 of the 121-rune page is 2e-5 for the fixed lines but about 6e-3 for any row and column. Nothing decrypts.

- **Family simulations (2026-10-17, 12:20; `work/log/phase9_families.md`, `work/families/`):** 25 cipher-family rows x 100 replicates against LP2's fingerprint (IoC, doublets, within-word lag-5, repeated
  words, difference IoC, lag spectrum, word-initial IoC). Any structureless additive key (PRNG / hash / OEIS) is 'random + about 81% avoid-repeat' and cannot be told apart by statistics; plain, mono,
  plaintext / ciphertext autokeys, per-word keys and Vigenere periods up to 29 are excluded. The lag-5 effect is reproduced by period-5 alphabets per word or a 1.5% lag-5 copy; no family that otherwise fits reproduces its
  concentration on rune S (calibrated P 0.0073). Side scan: the affine relation c' = 24 - 2c at lag 6 (z +5.0, P 0.013 over lags and relations, split-half P 0.035) is an unreplicated lead.

- **Backward-key campaign complete (13:16):** `kscreen-reverse` a = 26..28 ran on the GPU in 15 minutes and is negative; over all 29 values of a the largest library IoC is 1.387 (a = 8), none reaches 1.40, 0 verified hits (`work/log/phase9_overnight_results.md`).

- **GPU, 30 minutes (13:30-13:56):** boundary-free sweeps of every section window over epoch-time seeds 2011-2015 (8 generators) and small integer seeds below 2^27 (php, glibc, py3): 0 candidates at +300 (prioritised ranges, not exhaustive). **Boundary-free OEIS lane (199,088 sequences):** negative, real best 181 / 246 against matched null bests 192 / 230; the top decodes are unreadable (`work/log/phase9_overnight_results.md`).

- **KDF lane and the laptop's new branch (14:30):** the 719,280 passphrase key streams (RC4 / AES-CTR / ChaCha20 / PBKDF2 / scrypt) are negative on the boundary-free score (best 58, whole-section -8.9 to -10.2 per rune). `research/new-hypotheses` (keyless exclusions, the two-layer screen `layer2`, millisecond-timestamp seeds) was reviewed, not merged (`docs/prs/new-hypotheses.md`): its generator vectors re-check independently (86 of 86); accept after two changes.

- **64-bit CUDA port for `prng-time` (14:20; `work/log/phase10_prng_time_gpu.md`, `docs/GPU_PORT.md`):** `bgmt64.cu` / `bg64.py` sweep py3, ruby and java with 64-bit (millisecond-timestamp) seeds; gate `test_bgmt64` 8/8 against independent CPython / java.util.Random references; 6.4 M (py3, ruby) and 10.8 M (java) seeds/s, so the full 2012-2014 window is about 2.9 h / 1.7 h per generator (`time_gpu.py`, not started). Demo, 2014-01-04/06 UTC, 172.8 M timestamps per generator: 0 candidates (agrees with the laptop's CPU sweep).

- **prng-time, first hour of the full window on the GPU (15:31):** py3 and java, millisecond timestamps 2013-09-01 .. 2014-02-01 UTC (13.2 billion each, 59 min of GPU time), section 0.7: 0 candidates at +300 (`work/log/phase10_prng_time_gpu.md`). py3 2012-01 .. 2013-02 (14 months) and java 2012-01 .. 2012-12 (12 months) remain: about 2.7 h; java-abs and ruby only have the 2-day demo.

- **Keyless tests and their power (19:10, `work/log/phase10_keyless_power.md`):** the laptop's final `kscreen-typo` results (f096a8c, 22 windows): strong negative for the 250-300-rune windows (planted keys clear the null 45/45; the library beats its matched null by at most 0.037 IoC, 5 of 22), weak for the 91-139-rune list items (13/21 recovered); the shared-key test on the five list items (and the laptop's pooled test) found nothing and its power control passes (6 of 6 plants seen); the summary's 'CANDIDATE - inspect' line is a verify-rule artefact (short-window maxima, 1.9-2.0, are below the null's 2.1-2.2). The branch is still not merged (conflicts in the crib files, overlap with the second session's uncommitted files). A general fixed-map scan (any permutation between runes at distance 1-12, across words) is negative but cannot see LP2's 1.5% effect size (detects 6%); a sparse-tap key-recurrence scan (55,440 forms) finds only the known doublet deficit and lag-6 relation and fails its control for three-term forms. Lesson: ciphertext-only statistics see strong effects only; the specific hypotheses worth running are those that become a finite key family for a decode screen.

- **Merged `research/new-hypotheses` (evening; `docs/prs/new-hypotheses.md`):** after committing the desktop's second session (9faf953) and the merge itself. Merged tree, CPU: 144 tests, 0 failures, the 15 errors are GPU tests with the GPU hidden; `test_prngx_time` and `test_layer2` gates pass; layer2 selftest 14/14 on the desktop. The crib reruns are identical to the laptop's apart from the corpus size of the bigram model (the PCs' `ref/corpora` differ). GPU tests of the merged tree (user's go, nothing else on the GPU): bgmt 5, bgmt64 8, stepmt 5, step28 6, kscreen_gpu 3, phpmt_gpu 3, all gates passed with 0 skips.
- **Evening runs on the user's go (20:27-20:50, GPU and CPU together):** (1) prng-time, 2013-08 and 2013-07 for py3 and java, 10.7 billion seeds in 1,422 s of GPU time: 0 candidates at +300 (`work/log/phase10_prng_time_gpu.md`); (2) layer2 variant A1 (a solved key folded into the stream, 20 streams), 1.16 billion decodes in 201 s on the CPU: best -5.63 per rune, 0 of 15 verified hits pass; its own planted control (the selftest had none for this slice) 12 of 12 recovered at +7.2 to +8.3 (`work/log/phase10_layer2_a1.md`, `work/layer2/combined_control.py`). **Both negative.**
- **Echo position test (22:00, `work/log/phase10_echo_position.md`):** an outside LLM proposed four 'ciphertext echo' mechanisms for the lag-5 S echo and the lag-6 relation. Keyless falsifier: both effects are strictly word-internal (across word boundaries +0.8 and +1.1 hits against +160 and +320 for a position-independent echo; planted control +162 / +322) and flat over the position in the word. Position-independent echo rules and the fixed-position gate are excluded; a mechanism must be word-aware.
- **Period-5 twist skeleton (22:40, `work/log/phase10_skeleton5.md`):** the outside LLM's word-aware answer (per-word affine key, in-word state T^(j mod 5), T = 24 - 2x) predicts the relation c_i = T^d(c_(i-L)) at every lag. At the strength fitted to lags 5 and 6 it predicts +44 to +62 hits at lags 3 and 4 where LP2 has +3.0 and -1.1 (about -6 sd together; the plants are its own W1 on English), and the plants give 3.1-3.6 lag-5 S-S pairs against LP2's 11. Excluded; W3 (twist at in-word collisions) is not excluded but needs the whole collision budget and derives no S.
- **Two-tap echo mechanisms A and B (23:20, `work/log/phase10_echo_values.md`):** the outside LLM's next proposals (a rare copy / T-image of the rune 5 and 6 back inside words; a rewrite of plaintext repeats) pass every keyless check by construction, the per-source-rune spread of the excess is consistent with an even echo (lag 6 P 0.25; lag 5 P 0.52 without S, 0.03 with it because of S), and three rates fit three numbers. **Not excluded, not testable on LP2 alone**, and they leave the 97% key layer untouched; the anomaly-explaining line stops here.
- **kscreen-sacred (22:15, `work/log/phase10_sacred.md`):** four of the outside LLM's five base-layer families built and screened like the library: 1,063 streams (1,052 two-stream combinations, 4 functions at the primes, 4 base-29 reciprocals, 3 prime-residue functions) after dropping streams LP2's flat IoC already excludes (the proposal's base-10/16/60 digit streams, 275 combinations, 14 of 21 functions at the primes) and affine duplicates; planted control 24/24; best IoC 1.369 against the 1.40 rule (the library's own best 1.366), 0 of 15 verified hits. **Negative.** Order-4 recurrences (F2) not built.
- **DeepSeek asked directly (22:20; `work/ask_deepseek.py`, `work/log/phase10_sacred.md` round 2):** through the pi harness with no tools and no project files, one self-contained round (2 min 51 s). Its second batch obeyed the constraints round 1 had broken and called itself 'all long shots': inverses, discrete logs, g^n and cubes modulo primes = 1 (mod 29), and a base-29 digit sum: 19 periodic streams (period 58-928). Planted control 30/30 windows; best IoC 1.249, 0 of 15 verified. **Negative.** Replies are kept in the git-ignored `work/ref/deepseek/`.
- **DeepSeek round 3 with the ledger and hypotheses documents (23:30, `work/log/phase10_deepseek_round3.md`):** its audit found one real hole: a true key scores +7.3 per rune on Cicada's solved text (not +10), so the OEIS lane's 36-rune windows pass the +300 gate in only about 29% of cases; the lane's negative is weak to partial (rerun on 120-rune windows is the remedy, not run). The 120-rune sweeps (all PRNG, hashscan, KDF) are unaffected (99.6-100% pass). Its other audit points: a wording gap in the PRNG row (unknown discard offset, now listed) and an H8 control concern that does not hold. Its five new families: two new cheap ones (g^i and i^e mod 3301, 1,599 streams), one duplicate of the KDF lane, two arbitrary; none built yet.
- **The two magic squares (23:25, `work/log/phase10_squares.md`):** an outside LLM's number leads all check out (pi(1033) = 174 = 6x29, pi(3301) = 464 = 16x29, 139+313+467+809 = 12^3, phi links), with a post-hoc chance of about 1%; the one structural fact: the 0.2 grid and the 0.6 square share the same template (magic, centrally symmetric, 13 distinct values), not noted before. No key stream follows from it yet; cheap streams (phi / sigma of 3301 i + 1033, prime decimations by 58 ... 464) are not built. Follow-up: the template is a 7-parameter linear family (rank 7, verified) reproducing both squares; the 0.2 grid's vocabulary is a word search for equal sums (SHADOWS / CABAL, BUFFERS / MOURNFUL, CARNAL / ANALOG); the 0.6 seeds' origin is not derivable (own-text sums, LP2 ciphertext word sums: chance level).
- **OEIS lane rerun (23:50, `work/log/phase10_oeis_rerun.md`):** 120-rune windows are impossible (the OEIS file has only the first terms, median 63), so each sequence is read with the longest window it covers: 98,667 sequences at 60 runes (true key passes 97%) and 46,891 at 48 runes (81%), each with a matched null, planted-prime control at both lengths: best scores 75 and 128 against the +300 gate, no better than the nulls; verification reproduces them and shows no English. **Negative**; lane power per window rises from 29% to about 75% (sequence-weighted). Pages and headings and the 53,530 sequences with 40-51 terms were not rerun.
- **kscreen-sacred3 (23:55, `work/log/phase10_sacred.md` round 3):** the cheap streams the squares suggest: phi / sigma of 3301 i + 1033 and 1033 i + 3301, primes at index multiples 58 .. 3301, base-29 digits of 1/45415 and its ratios: 15 streams after the flat-IoC filter; planted control 18/18; best IoC 1.273, 0 of 15 verified. **Negative.**
- **GPU slot on the user's go (23:09-00:20, `work/log/phase10_prng_time_gpu.md`, `phase10_pages_py3.md`):** java 2013-06 .. 2013-01 (15.6 billion seeds, 1,742 s) and py3 2013-06 .. 2013-03 (10.5 billion, 1,765 s): 0 candidates; per-page seeds (H11) for py3 over the epoch seconds 2011-2015 on 44 page windows (new `bg.make_windows("pages")` and gate `test_bgmt_pages.py`, 3 tests, 0 skips): 126 M seeds x 44 windows in 640 s, 0 candidates. **Negative.** Other generators' page sweeps and the remaining ms months not run.
- **Project review (02:00, `work/log/phase10_review.md`):** checked: the IoC rule keeps 100% of Cicada's 300-rune windows; the 120-rune boundary-free lanes keep 98-100% on Latin / German / French / Spanish / Italian; LP2 has no literal F (458 against 447 +- 21; a literal F would add about 260). Gaps: the OEIS lane's power is English-only (Latin 56% / 27% on 60 / 48-rune windows); unkeyed insertions (an extra rune per word with no key value) and layout-driven pointer advance are not decoded by any screen (new ledger blind spot 9, an engine option `stay` proposed); ledger housekeeping done.
- **DeepSeek round 4, deepseek-v4-pro with max thinking (01:30, `work/log/phase10_deepseek_round4.md`):** the audit of the sign-rule decisions found two real corrections (the unsigned screens cover only rules flipping <= about 20% of the runes, measured; 5 excluded streams are flat under sign masks, screened: best 1.293) and one rule for the unbuilt direction mechanism (both orientations needed); a 4-point audit with a test each, 18 conventions for the direction mechanism, and one cheap new family (30 per-rune periodic sign templates, about 3.2 h CPU). The 61-rule `kscreen-signs` campaign is running; GPU months continue.
- **DeepSeek proposal gates reviewed (2026-10-18, `work/log/phase10_proposals_review.md`):** all 12 pass on their toy plants; none changes a result. sign_rules / word_anchors take the word numbers from the plaintext (leak; superseded by our 61-rule campaign); the h2 coincidence statistic collapses from z 41.7 to 1.2 once the anti-repeat rule is planted (`results/analysis/proposals_h2_skip.txt`); word_reversal's premise is wrong (reversed words still decode at IoC 1.83); the only new family is the outer keyword-mixed alphabet (relabel, then the existing screen). Committed unreviewed in a360a77 / eed00eb, pushed with 00a6a75.
- **First overnight run of the detached queues (2026-10-18 01:25-08:37, `work/log/phase10_overnight_queue.md`):** the 61-rule sign campaign finished (best IoC 1.388, 0 of 5 verified hits per rule: negative); 15 more per-page seed sweeps (7 generators over the epoch seconds, 8 over the seeds < 2^27, 44 page windows): 0 candidates; java and py3 millisecond months now complete (2012-01 .. 2014-01), java-abs 23 of 25 months, ruby 14 of 25: 0 candidates. The runner-based jobs (25 periodic sign templates, layer2, prng-bg) crashed: my driver `jobs/queue.py` shadowed Python's `queue` module (renamed `jobs/jobqueue.py`); both lanes were stopped at the user's request, nothing is running.
- **Untested hypotheses (2026-10-17, `docs/HYPOTHESES.md`, details `work/log/phase9_hyp.md`):** H1-H12, each with its blind spot, controls and kill rule. Run so far:
  - `kscreen-hyp` (CPU, 1 h): 16,071 decimated library streams (H3), text prefix sums (H4), pi / e / phi / sqrt2 from positions 10^6 and 3301*1033 (H6), LP2's ciphertext as its own key forwards
    (guarded) and backwards (H5, 28 multipliers). Controls 15/15; best 1.3747 against a 1,300-stream null of 1.3553; 0 of 31 hits survive verification. **Negative.** New engine option: G lines
    (a window is never deciphered with itself).
  - H8 null on collision: alive as a partial word-length explanation (TH base G 56 -> 40 at the predicted 0.0278 per rune, 0 fitted; fitted 0.039, 95% 0.021-0.059), and it hides nothing
    from the IoC screens (planted H8 keys found at their exact offsets).
  - H9 two-time pad between sections under skip drift: power 0.05-0.42, **undecidable** (closes open lead 3).
  - H10 small 29-state machines (4,608 rules x 29 start states): **null** (1.0259, the step-stream artefact, against shuffled 1.017 / 1.015; controls 4/4), and also with the
    anti-repeat skip modelled exactly (Viterbi: LP2 -3.942 nats per rune against an avoid-repeat null of -3.944; planted machines -3.00 to -3.09, each the best).
  - Keyless: no fixed-point rune (rune x word position chi^2 74.1 / 84 df; a fixed letter would add 30-1,010), the payload is byte-random (161 distinct of 256), the S echo is not "-SELVES".
  - `kscreen-clock` (CPU, 1 h 07 min), H3 clocked pointer: new engine option `clock=` (the pointer moves on by 1 + index, the prime or prime - 1 of the cipher or deciphered
    rune; default decodes unchanged, 19,200 compared). Controls 19/19; the library on 8 sections for all six clocks, each against its own 300-stream null; 0 of 90 hits survive
    verification. **Negative.**

### Phase 10 – New hypotheses: keyless exclusions and the two-layer screen (2026-10-17, laptop)
Details: `work/log/hypotheses_2026-10-17.md`; probes `work/tmp/hyp/` (output `results/analysis/hypotheses_2026-10-17.txt`);
engine `work/layer2` (output `results/layer2/`).
- **Keyless tests with planted controls.** Excluded: a running key plus a progressive (Trithemius) shift (progressive kappa:
  LP2 +2.30 inside the null, plants +4.1 .. +5.3); multiplicative keystreams c = D(p)*k (no rune has a letter's word-position
  profile, best G = 49 on 4 df); running keys made uniform by a cumulative sum (step chi-square 130-736 against LP2's 41);
  the surviving doublets as a ditto code for one letter; a key restart after each surviving doublet (z -0.32, plants +17 .. +25).
  Disfavoured (p ~ 0.05): any prime-based key at ANY offset for the identity and Atbash alphabets (such keys never take one
  value; LP2 max z +1.89, plants median +3.55). The lag-5 echo is not concentrated in quoted speech.
- **H-LAYER, new family:** the solved pages' two methods stacked, a keyword Vigenere inside (optionally with the literal-F
  rule) and a number stream with the anti-repeat rule outside. It fits the fingerprint and explains why LP2 shows no literal-F
  excess; kscreen is blind to it (IoC 1.18 at the true offset of a plant). `work/layer2` decodes both layers in one beam and
  scores English bigrams (true key ~ +7 per rune, random ~ -15); periodic mode covers any keyword of period m. Selftest 14/14
  (plants with and without literal F, both alphabets, both models, a keyword outside the list; random streams best -4.77).
- **First slices negative:** An End's prime streams (p, p-1, p+1) x DIVINITY / FIRFUMFERENFE / CIRCUMFERENCE, every option and
  offset, 8 sections: 512 M decodes, best -4.53 per rune; 0 of 15 hits survive whole-window verification. Periodic mode, 20 Cicada
  streams x any keyword of period 2-14 (no literal F): 111 M decodes, 0 of the 100 best survive keyword estimation + re-decoding.
- **prng-time (`work/log/phase10_prng_time.md`):** generators seeded with a millisecond timestamp of 2012-2014, outside the 32-bit
  sweeps: Java `new Random(currentTimeMillis())` (48-bit seed) and CPython integer seeds above 2^32 (two-word `init_by_array`; Ruby by its documentation, unverified;
  `prngx pymt` now seeds like CPython for any integer). Vectors from CPython and the Java specification 119/119, engine keys equal
  independent keys, planted timestamp seeds at rank 1 (+988 against a random-ciphertext best of +59), whole-section check
  (`time_verify.py`). Campaign `prng-time`: one sweep per UTC month, newest first; on a validated GPU it runs the desktop's 64-bit
  port (`time_gpu.py`, about 9 h for the window), otherwise the CPU engine (about 210 h). Demo on LP2, the weekend of 2014-01-04/05 (172.8 M timestamps per
  generator): best screen +59 for both, no row near +300, 0 candidates after the whole-section check. Negative.
- **Queued:** campaign `layer2` for the desktop (115 streams x the solved keys, 20 streams x 30 keywords, periodic mode,
  folded-key variant; about 13 h on 16 threads). Proposed next: crib-filtered sweeps ("AN INSTRUCTION" fits 0.8's heading under
  letter spelling), direction-switching keys.
- **Review of this branch (desktop, 14:30) answered (15:10):** main merged in; `prng-time` gated by `run_gate.py` (fails on skipped
  tests) and pointed at the GPU port; the prngx and layer2 controls now plant with independent code (`time_verify.plant_windows`,
  `work/layer2/plant_ref.py`): `test_prngx_time` 5/5, `test_layer2` 3/3, `layer2/selftest.py` 14/14; Ruby marked unverified
  (no Ruby on either machine). Response at the end of `docs/prs/new-hypotheses.md`.
- **Correction: words across page breaks (16:00; `work/log/research_cicadanotebook_2026-10-17.md`).** Comparing our one-rune words
  with cicadanotebook.com's image-audited inventory (83) showed that `lp.word_spans` treats every page break as a word boundary.
  In fact 32 of the 55 page breaks inside LP2 fall inside a word: no '-' or '.' on either side. In the solved sections, words
  split by a page break decrypt as single words: WH|O, ADHEREN|CE, STOP|PED. **The images confirm it**
  (`work/tmp/hyp/page_seam_dots.py`, `results/analysis/page_seams_2026-10-17.txt`): none of the 32 shows a separator dot, all 21
  marked page breaks show one, and the detector finds 150 of 151 marked line ends with 4 false dots in 388 wraps. Corrected:
  2,896 words (not 2,928), **83 one-rune words (not 99)**, the site's tokens exactly, 2-rune share 15.5%, within-word lag-5
  z +3.75 (was +3.67). No conclusion changes; the toolkit fix is the next bullet.
- **Toolkit fix: an unmarked page break is a wrap (18:30; `work/log/page_seam_fix_2026-10-17.md`).**
  - **Code:** `lp.word_spans` treats '%' like '\n'. Also fixed: `stats.adjacent_pairs`, the word unit of
    `restart_columns`, and five scripts with their own splitters. Three of those (`wordlen_clauses`, the two crib checks)
    and `grid30`'s Gematria sums still cut at every line break, the pre-2026-10-16 bug.
  - **Exports:** phpmt's `windows*.txt` and walk's `lp2.txt` / `lm3.bin` regenerated; only the word lengths change.
  - **Reruns:** 23 result files. Nothing that mattered moved:
    - lag 5: 104 of 2,105 pairs, permutation p 0.0007;
    - one-rune cipher runes still uniform;
    - every family row and every exclusion keeps its verdict; the lag-5 concentration on S calibrates at P 0.010
      (was 0.0073).
  - **Three shifts worth knowing:**
    - the word-length model "+1 rune in about 42% of multi-rune words" is no longer rejected (p 0.085-0.10, was 0.025);
    - with wraps joined, the community crib for 0.7 fits LP2's word division exactly (0 cuts inside crib words, not 4);
    - **the lag-6 affine lead c' = 24 − 2c got stronger:** z +5.32, look-elsewhere P 0.005 (was 0.013), and its
      split-half replication went from P 0.035 to 0 of 200 shuffles (held-out z +1.44, about 4.9 sd). It is still a lead,
      not a finding: three pairs moved the statistic a lot. A follow-up with the relation fixed in advance is proposed.
  - **Not rerun:** the engine campaigns that scored with word lengths. About 1% of words are affected, so a true key
    loses a little score but is not excluded.
  - **Tests:** `test_crib` and `test_families` updated.
- **cicadanotebook.com read in full (17:00; `work/log/research_cicadanotebook_2026-10-17.md`).** An AI-assisted notebook of 79
  controlled sessions; **no solution claimed**. Recomputed on our data (`work/tmp/hyp/notebook_checks.py`, `keyed_floor.py`;
  `results/analysis/cicadanotebook_checks_2026-10-17.txt`):
  - **Confirmed:** doublets per section, the phrase, no rune errors, the payload bytes.
  - **Corrected the other way:** the cuneiform stamp appears 7 times, not 4.
  - **Separators:** 5 three-dot marks in the unsolved part are in our images too; our master writes each as '-'. Words are
    unaffected.
  - **Exact keyless bounds:**
    - an additive key that ignores the text needs at least 207 doublets on English in the standard order (181-226 per
      text, 121-172 in five other languages), against LP2's 86, so the encryption must look at the text (collision rule
      or feedback). A keyed alphabet gets under the floor (cheapest 29-cycle 0.15%) and a lag-1 fit cannot exclude it:
      open, low priority;
    - ciphertext feedback p = G(c_{i-1}, c_i) allows at most 5.53% for the top plaintext rune (random null 5.46%);
    - no LP2 word of 4+ runes repeats;
    - the phrase repeat has chance 4.3e-5 under independent keys, chosen after looking.
  - **Ideas not yet run:** restarts at typography with the full library, using the second koan and page 56 as controls;
    Euler-trail nulls; one-rune words as filters; a key-reuse scan anchored on the phrase.

### Phase 11 – Outside-in review: audit, ranked next tests, stop-doing (2026-10-18, `work/log/phase11_review.md`)

- **Methodology audit** (`work/tmp/methodology_audit.md`): the five assumptions most likely wrong, ranked, each with
  evidence and a minutes-level falsifier: (1) separators = plaintext words (4 sd word-length correlation, 33 -> 0
  plant); (2) skip/coin with one key value per rune, forward-only (repo's blind spot 9; +1-rune fit p 0.085);
  (3) key = global-position stream (echoes strictly word-internal; planted echoes spread +162/+321 across
  boundaries); (4) additive mod 29 in GP indices (lag-6 relation is multiplicative; W3 alive); (5) 300-rune windows
  at starts (45/45 vs 13/21 power curve; staggered-window test is about 2.8 M decodes, minutes).
- **New controlled negatives (all in the registry):** the affine lag-feedback autokey family
  c_i = p_i + a*c_(i-d) + b (d 1..8, all a,b, four separator scopes, nonlinear maps at lag 6) is excluded: LP2 best
  chi2 64.86 = the known echo, below the 200-shuffle null max 67.74; plant 73/73 recovered at chi2/n 2.25. Two more
  named echo mechanisms dead: plaintext-F replacement (English F at word positions >= 6 is 0.0056 vs the echo rate
  0.0272 +/- 0.0047) and the collision twist W3(a) (3/80 vs null 2.8). The echo rate equals the avoided-collision
  rate but does not track it by section (r -0.38, n = 9): open observation. Echo pairs spread over sections and
  vocabulary (0 repeated hit-bearing words); the lag-6 residual is not plaintext (IoC 1.029 vs shuffle max 1.018).
- **Outer-alphabet front-end built and controlled** (`work/kscreen/relabel_export.py`, `RELABEL.md`): the one family
  no screen covers; plant recovered at 1.6702 after relabelling vs 1.0068-1.0637 unrelabelled, null <= 1.052, wrong
  sigma <= 1.055. Real run: 72 sigmas (29 reflections, 26 affine, 17 keyword alphabets), about 1 h GPU / 6 h CPU.
- **Staggered mid-page windows (audit assumption 5) run:** 31 windows of 300 runes at mid-section offsets x the
  library at every offset, both models: 792,182,494 decodes in 19 min, best IoC 1.3320 vs the rand:300:300 null
  1.3184 (+0.014; rule 1.40 and +0.15): negative, a library key starting mid-page is excluded
  (`results/kscreen/staggered.tsv`, plant control 1.6779).
- **Stop-doing list** in `work/log/phase11_review.md` section C: no more plain additive library screens, no
  dictionary-scored leftovers, no short-window restart tests, no new keyless echo statistics, no OEIS/hash/KDF
  lane expansions.

### Phase 12 – Outer-alphabet gate, prime domain, and the unkeyed-insertion decoder (2026-10-18, `work/log/phase12_review2.md`)

- **Outer-alphabet gate (H1): 72 sigma settings (44 distinct: 26 affine multipliers, 1 reflection family, 17
  keyword alphabets) x the library on window 0.7, both key signs and models: best 1.3811 (aff:8:0/aff:21:0,
  sha256-ctr:1311 offset 14398), null 1.2874: negative. Sections 0.8-0.15 with these sigmas remain open
  (about 5 h CPU / 1.5-2 h GPU).
- **Prime domain excluded** (registry row `prime-domain`): prime->prime affine feedback at lags 1-8 and the
  mixed index/prime domains at lags 5-6 never beat their nulls (plant chi2/n 1.97 vs LP2 0.44): the GP prime
  order is not the arithmetic domain; index order remains the working domain.
- **Keyless word-edge nulls** (engine option `nulledge=1|2`, built and controlled, selftest passed): the
  0%/100% deterministic variants are excluded (best 1.4163/1.4294 vs matched nulls 1.3901/1.3849; every hit
  falls to 1.04-1.06 over the whole window); the 42% mixture has no powered IoC decoder (free beam null 1.75 =
  the truth's level). Word-end nulls are also excluded as the echo source (targets word-final 32/80 vs 34.7
  expected).

- **Affine outer sigmas closed by algebra (2026-10-18).** sigma(x) = a*x + b: the ordinary screen with key
  multiplier a decodes c - a*k = a*p + b (an IoC-invariant permutation of the plaintext), so the completed
  28-multiplier campaign (5.7 B decodes, negative) covers every affine sigma - verified over all 22,736
  (a, b, m') settings with |dIoC| < 1e-12. The keyword-alphabet run (17 + Atbash, all sections, best 1.3895 vs
  null 1.3346) is negative; only arbitrary non-affine permutations remain open (not sweepable). A current-library
  multipliers rerun (1,439 -> 1,447 streams) is a library refresh, queued.
- **Second model's work/independent reviewed** (`work/tmp/independent_review.md`): PGP 7A35090F bytes correct
  but already in-repo as keystream seeds; its lag-6 gated-null statistic fixes the free-beam overfit (z +45.9 vs
  random keys) but its gate fails (offset valley on structured keys, 3/6 random plants); the corrected gate and
  the H5 drift-decoder slice are being built with the review's required fixes.
- **Sign-template campaign running** (`kscreen-signs-periodic`, 25 templates, control 9/9): every template so
  far negative (best 1.32-1.36 falling to 1.05-1.15 whole-window).

### Collision follow-up – authorized single-pass gates (2026-10-18)

Details: `work/log/collision_followup_2026-10-18.md`; all artifact paths and failures:
`results/independent/desktop/20261018-collision-followup-summary/REPORT.md`.
21/21 local tests passed on every invocation; frozen code/protocol/seeds unchanged.
- Exact reference spend/hold count-test power: **26.07%** at size .05 with 35 hidden
  repairs among 80 independent sites (nonrandom power 20.63% at size 3.40%): HOLD
  discriminator. Actual-site power remains unknown; no discriminator run.
- Section bootstrap timed out at 96.1 s under the 95 s cooperative cap; last
  progress 81/199. No completed section artifact, no retry, not an LP2 negative.
- B=999 controls: full-book plants .001/.001/.001/.344, null .492; gate PASSED.
  Split plants .292/.595/.718/.221, null .433; 0/4, gate FAILED; LP2 split NOT RUN.
- Permitted full test: **15.895269 nats**, mix_I5_T6_w=1/4; 0/999 exceedances,
  **p_MC=.001 (floor)**; null max 11.373414. Selected-hypothesis re-test, not replication.
- Pure-null optimism: selected lag-6 affine maps +26.54 counts (190 cases; MC SE
  .51), but zero fixed-T6 selections and zero observed-score tail matches. True
  inflation of the observed 80 remains unknown; no subtraction is justified.
- Source-S-only gross predictable repair capacity: .614 first-target, 1.452 shared,
  2.067 total; not a realized ceiling or controlled exclusion. Smallest successful
  second mechanism remains unknown. Nothing in LP2 is solved.

### Fixed-rule halves and section blocks – authorized follow-up (2026-10-18)

Frozen new protocol: `work/independent/collision_fixed_halves/PROTOCOL.md`.
Details: `work/log/collision_fixed_halves_2026-10-18.md`; all artifacts/logs:
`results/independent/desktop/20261018-collision-fixed-summary/REPORT.md`.
17/17 invocations FINISHED, each once under 95 s; 27/27 unit tests each, zero skips.
- NO selection: raw T6/I5, q=.81, same halves. T6 A +3.198569 nats (p=.004),
  B +8.803375 (p=.001); meets positive-in-both criterion, adjusted p=.008.
  I5 A +3.394918 (p=.003), B -.224223 (p=.016); fails required positive score
  in B despite adjusted conjunction tail p=.032. Not an exclusion of lag5 echoes.
- New coarse per-rule controls pass: I5 2/2 per half; T6 1/2 in A, 2/2 in B;
  no null flag. Rules fixed before these runs, not before whole-LP2 discovery:
  retrospective consistency, NOT untouched replication or collision causality.
- Section diagnostic now completed in eight blocks (20.6-33.6 s each), same
  199 original seeds and refit procedure; prior timeout preserved. Expected
  79.298359 vs observed 80; shape statistic 1.336559, upper-tail p=.990;
  overall discrepancy 1.354594, p=.995. Observed residuals unusually small;
  high upper-tail p does not validate the model. Plug-in selected-family
  diagnostic, heterogeneity-sized power unknown. Nothing in LP2 is solved.

### Echo-site dispersion – three frozen scales, matched controls (2026-10-18)

Details: `work/log/echo_dispersion_2026-10-18.md`; protocol:
`work/independent/echo_dispersion/PROTOCOL.md`; raw artifacts and full report:
`results/independent/desktop/20261018-echo-dispersion-summary/REPORT.md`.
- Fixed lower-tail T6-HIT dispersion: section counts, per-section disjoint bins
  of 100 eligible pairs, internal gap CV in eligible exposure. No scale/offset/
  rule/tail tuning. Independent inhomogeneous Bernoulli before conditioning on
  total 80; prior own-doublet q_s frozen, exact conditional finite sampling.
- Controls PASSED: 0/4 Bernoulli flags, 4/4 evenly spaced flags. Same total and
  one-site inclusion marginals; positive plants differ in joint regularity.
  Fully regular 80-hit controls do not measure partial/35-repair power.
- LP2 B=999 raw lower p=.024/.030/.687; three-scale Bonferroni .072/.090/1.000;
  omnibus **.072, no flag**. Counts somewhat smooth; internal gaps not unusually
  regular. Not an exclusion of weak regularity or proof of randomness.
- Both invocations FINISHED, once each, 11.6/7.2 s, 28/28 tests each. Site-process
  null is NOT an exact forward-cipher null; shared-position dependence and q_s
  uncertainty omitted. Motivated by prior same-data smoothness, not independent
  replication. No retuning, new exclusion or decryption; nothing in LP2 solved.

### Phase 5 – Validation and reporting
- A plaintext counts as solved only if it scores well across a whole segment (word hits and IoC about 1.8)
  and the same rule works on the next page.
- Log every hypothesis tested, with its parameters and score, in `work/log/` so nothing is re-run blindly.
- Record negative results too. The unsolved section has resisted public effort since 2014, so
  ruling hypotheses out with clear reasons is useful progress.

### M04 hold-key baseline (2026-10-18, `work/log/phase15_m04_baseline.md`, `work/m04/`)

Synthetic crossed gate, no LP2 search; design frozen first. Independent plants (hold-key repair M04, spend-key substitution, and the repository's skip / coin conventions) through the UNCHANGED kscreen engine
(bank 8 streams x 16 offsets, 512 cells). Regression skip 40/40 and coin 40/40 detected; matched nulls 2/100 flagged (T = 1.1969). **M04: 14/100 above T, 0/100 reach 1.40, 0/100 plaintext accuracy >= 0.95
(mean 0.154 = the prefix before the first held repair): the old screens are blind to a hold-key repair at this scope. Spend-key substitution: 100/100 detected, accuracy 0.969: visible.** Not evidence that Cicada used M04;
a matching decoder is a separate decision (registry `open-m04-decoder`).

### H5 sweep power map (2026-10-19, `work/log/phase16_h5_power_map.md`, `work/h5power/`)

6,000 independent stream + keyword plants through the real `h5rs sweep` path: recall of the true cell falls from 84% (L = 2) to 7% (L = 20) at IoC 1.6 and from 48% to 4% at 1.8 (skip 58% / 36%, coin 34% / 21%); no dependence on offset or key kind.
**A negative H5 sweep excludes little** (the 1.8 floor rejects about half of even perfect 300-rune decodes; the engine truncates windows to 300). The overnight queue was re-cut to L = 2..13 (flat library) and L = 2..8 (the 858 streams the flat filter excluded).

### chanscreen: hold-key matching decoder (2026-10-19, `work/log/phase17_chanscreen.md`, `work/chanscreen/`)

GPT built it, Claude reviewed and finished the follow-up. No LP2 ciphertext scored. v1 dense summed-path DP: G0-G2 PASS (M04 plants 100/100, nulls 4/100), G3 GPU port FAIL.
v2 sparse all-offsets Rust engine: E0-E2 PASS (exact on the Q3 grid, all 693,940 stored cells to 1.3e-11 nats); full 82-window campaign projected at about 15 wall hours on 4 workers.
**E3' FAIL:** the union bound at T300 = 29.80 nats does not hold under one common null (exact finite-key counterexamples, 2.07x the bound at Q29/n300). **F4 guard min(S, S_W) >= T PASS:** exact tails under both nulls on the
full Q3 grid (48,708 bounds), and on the 380 saved held records 280/280 plants kept, 0/100 nulls (max -132.15). The literal wrong-offset count fails on +-15 alias cells (403 of 2,240 passes at t = 10). E3-E5 wait for adoption of the guard.

**2026-10-20, laptop: independent full-library null (`work/chanscreen/v2/step3/REPORT.md`):** under the same rule (S_guard >= T300 = 29.80), five regenerated v1 calibration windows (cal records 0-4, Cicada/iid keys; they reproduce the stored maxima to 3.6e-12 nats) were scored against all 1,439 library streams, 4 channels x 2 signs x every offset (533,130,960 cells): best S_guard -97.29 to -102.37, zero cells >= 0 (best plain S -17.2 to -26.6). Record 0 equals the desktop's E3 maximum (-102.37), so with the desktop's E3 / E3b there are 11 distinct iid-key nulls, all below -96.7; five laptop windows cannot certify a .001 rate. The E4 plants, the 82-window campaign and the clause scan ran on the desktop (below) and are not repeated here. A 16-plant smoke run on non-protocol seeds (`work/tmp/laptop_e4_smoke/`, not a result) found the same alias structure as the desktop's amendment 2: 854 of the 1,439 streams are exactly periodic (period <= 64), and hold aliases above 10 nats lie almost entirely ahead of the truth, up to about (S - 10) / 4.2 offsets, so alias radii of 15 or 20 are too small.

### What the book asks, how it is built (2026-10-19, `work/log/phase18_cicada_intent.md`, `work/prime_sums.py`, `work/page_scan_audit.py`, `work/book_map.py`)

Sentence sums of the solved plaintext are prime far more often than chance (36 of 76 body clauses against 11.2 expected, z 7.9; A Warning 9 of 9, An Instruction 4 of 4, Parable 3 of 3; long narrative clauses at chance; ordinary English 12-14%); LP2's ciphertext units are not enriched.
Reading: the plaintext carries a number check ("either the words or their numbers"), so a decryption would be verifiable in any language; proposed for the campaign rules, not edited. Scan audit: 10.jpg is a four-in-one container, 05.jpg holds a hex copy of its own magic square and a byte-reversed copy of itself;
no hash match, no hidden faint marks (planted control found). New open row: key restart or jump at every clause mark, to be run with chanscreen v2.

### "Try all four" (2026-10-19, `work/log/phase19_try_all_four.md`)

(1) `work/prime_check.py` + the CAMPAIGNS.md addendum (right keys 56% prime on short clauses, random shifts 16%). (4) OutGuess re-implemented (`work/ogscan/`, no third-party code run): the default key opens 9 pages (0, 1, 2, 3, 8, 10-13: the 2014 payloads, pages 0-2 new to the notes); a key-free screen shows no OutGuess-style payload in any of the 56 LP2 pages
(9 of 9 controls show 14-258 deviations, LP2 pages 0); page 4: 53,227 solved-text keys, 0 hits, planted control found. Seed lists: `prng-bg` on sections 0.8-0.15 for all ten generators queued on the GPU (py3: 0 candidates). (2) and (3): chanscreen v2 step3 protocol adopted on the user's instruction; E4 200/200 detected (194/200 at 60 runes, 200/200 from 80);
E3 as frozen failed by my choice of records (three library-keyed records were found: a 3-of-3 library-scale control), E3b gate pending; the n300 campaign (about 49 CPU-hours) and the clause scan (21) run in the detached queue `jobs/queues/chanscreen.txt` and have not been read.

### Segmentation plan (2026-10-19, `work/log/phase20_segmentation_plan.md`, `work/word_structure.py`)

An outside analysis proposed treating "segmentation preserved, symbols destroyed" as the central clue. Against the record: adjacent word lengths are independent (lag-1 mutual-information z +0.4; English +8.8 to +27), clause marks are not sentence-like (first word 4.42 runes against 3.14), the anti-repeat rule ignores word boundaries (0.63% inside words, 0.80% across)
while the lag-5 and lag-6 echoes stop at them: the separators belong to the cipher layer, not to the language layer. Its top experiments were already done (restart at words Z -1.4 against 237 for planted restarts; per-word keys). New keyless tests with planted controls: the boundaries do not depend on the neighbouring runes (16 of 16 detections down to 12% of the boundaries;
LP2 combined P 0.57 and 0.72), and there is no schedule by position in the word or by (length, position), with or without a per-word offset (LP2 P 0.81 and 0.80; plants found 8 of 8 on at least half or a quarter of the words). Order of work: read the running queues, E4-letters (power of the frozen contract under letter spelling), word-edge null / advance channels in chanscreen v2 (row `open-unkeyed`, engine work, needs a go-ahead).

### Queue results (2026-10-19 / 20, `work/log/phase19_try_all_four.md` section 5, `work/chanscreen/v2/step3/PROTOCOL.md` amendment 3)

**Nothing in LP2 is solved.** chanscreen v2, 82 LP2 windows of 300 runes against the 1,439-stream library (hold, spend, skip5, coin; both signs; every offset; 8.74e9 cells): 0 tier-1 cells, no cell reaches S_guard 0 (best -75.7 hold). Clause-aligned scan (82 clauses of 61-559 runes): 0 tier-1 cells (best 7.5).
Seed sweeps of sections 0.8-0.15, ten generators over their full seed space: 0 candidates. Nine isolated computation faults in the 2,296 campaign tasks (7 raised `invalid log likelihood`, 2 stored false tier-1 cells of 132.6 and 335.1 nats that do not reproduce) were re-run clean; `summary.py` now recomputes every tier-1 group.
What the negatives exclude: those streams, channels, q = 0.81 and an English-like plaintext; not other streams, languages, restarts inside a window, or a fault that hides a hit (about 1e-5 per call). Next (phase 20): E4-letters (power under letter spelling), word-edge channels in chanscreen v2.

### Signed page-scan material as key streams, art checks, hypotheses review (2026-10-20, `work/log/phase21_signed_streams.md`, `work/kscreen/signed.py`)

The eight PGP-signed payloads in the page scans (issuer 181F01E57A35090F, created 2014-01-07 / 10 / 19, signatures not verified) and the three 991-byte hex blobs, read as flat streams (bytes, base-29 digits, hash counters: 272 streams, 714,912 stream-offset pairs), screened against the eight LP2 section windows (skip and coin, multipliers +-1): best IoC 1.297 against matched nulls 1.302 and 1.336 and the 1.40 rule, 0 of 15 hits verified; controls 18 of 18 planted keys recovered (IoC 1.74-1.79), wrong streams <= 1.29. Negative; other multipliers not run. Art checks of the mayfly / spiral / 4x4 / 40x40 ideas: red digits exist only on image 32 (one red cell, 3299) and images 53-55 (numerals 1-5), none on the mayfly or spiral pages, and no unit of the book holds 1,600 runes. Registry row and STATUS rebuild still to do.

### A book as the running key, "OTP-class" from a referenced text (2026-10-20, `work/log/phase22_book_keys.md`, `work/book_key_flatness.py`)

**Nothing in LP2 is solved.** Keyless: the ciphertext's unigrams are the convolution of the plaintext's and the key's, so LP2's IoC (0.99987 over 12,956 runes; uniform-key + skip null 0.99986 +- 0.00051) tests every book at once through its letter frequencies. 16 Gutenberg texts in six languages plus Emerson, digraph or letter spelling:
under the GP table every plant (680, skip rule, multipliers 1 / 28 / 3 / 17) is >= +31.7 sd; under 20,000 random tables per book the 0.01% quantile is +11.3 to +21.9 sd: **excluded** for any untuned table, LP2 +0.02. A table searched to flatten the key against the plaintext's frequencies leaves only +1.9 to +6.3 sd (40 plants at the flattest: 6 of 40 above the null max; pairs at lags 2-8 +1.3 to +2.2 sd): **not excluded**.
Next (not run): a table-invariant, drift-tracking decoder for candidate books (group the ciphertext by key letter; within-group IoC about 1.8 at the right book and offset).

### Table-invariant book-key decoder, gate only (2026-10-20, `work/log/phase23_book_key_decoder.md`, `work/book_key_decoder.py`)

**Nothing in LP2 is solved; LP2 was not decoded.** Closes the method gap of phase 22, the table tuned to flatten the key. It groups the ciphertext by the key letter under it, integrates each group's shift out (a table-free beam with up to 8 histories per pointer, skip cost ln(0.81/29)), and then runs a hard EM with an exact skip-rule Viterbi for decryption.
Controls with a flattening table per plant, skip q = 0.81 and the grid offset 0-7 below the truth (612 nulls, 0 above the family threshold at p = 5e-10, from an exponential tail fit). Power: 300 runes 21/40 and 27/40 (digraph / letter key spelling), 729 runes 24/30 and 28/30, 1,524 runes 19/20 and 17/20, 3,316 runes 12/12 and 12/12. Cost about 0.033 ms per rune per book-offset.
The decision rule is frozen: 729-rune windows at the 8 section starts, every offset in steps of 8, then whole-section verification. Cost about 310 core-hours for the KJV and about 480 for the six cited books (Liber AL, Agrippa, Mabinogion and Blake downloaded 2026-10-20 to the git-ignored `work/ref/corpora/cited/`; the Agrippa copy is a raw 1651 OCR). Waiting for a go-ahead.

E4-letters (same evening, addendum in `phase22_book_keys.md`): the 200 E4 plants with letter-spelled plaintext are detected 200 of 200 at 300 runes (180 of 200 at 60, 200 of 200 from 80): the chanscreen v2 negatives hold if LP2's plaintext is spelled letter by letter.
Registry row `signed-streams` added for phase 21 (it had none).
Phase 25 (side session, `work/log/phase25_mechanisms.md`): eight simulated collision-repair mechanisms; none reproduces every anomaly (no Level 2 lead). One shared repair budget writing T(c_-6) or copying c_-5 inside words reproduces the doublet deficit and both echoes at about their size; the S carrier and the word lengths stay unexplained.
Phase 25 follow-ups: the lag-5 S carrier holds after calibration (P < 0.002 over 29 sources x lags 2-8) and its rate equals English plaintext's own S..S rate at lag 5 (-SELVES, SENSES), but no simulated cipher keeps such a coincidence on cipher S; no plaintext spelling or language reproduces the word-length histogram (letter-spelled English G 63-233 depending on the text).
Phase 25 section 9: the 11 S,S sites do not look like English S____S words (the plaintext reading is disfavoured); the S excess stays an unexplained Level 0 observation.
Phase 26 (`work/log/phase26_464_table.md`): the community "464-word table" reproduces exactly; its column balance (R 0.2515, permutation P 1.4e-3) does not survive the choice of sections and width (an equally good cell in 22-77% of selection nulls); the 928-word two-panel carrier shows no balance and no pairing (planted copies at 5% of cells detected 100/100); the grille is not specified well enough to test.
Phase 27 (`work/log/phase27_grid30_caption.md`): the page-30 caption against 53,014 preregistered decryptions from the solved rules and the grid's numbers: 0 two-word hits (null 0.008), controls 300/300; not decoded.
Phase 25 section 10: Old English (Beowulf) and Middle English (Chaucer) plaintext models do not fit LP2's word lengths (G 242-1057).
GPU (gpunight queue, 2026-10-20): the remaining millisecond-timestamp months (java-abs 2012-01/02, ruby 2012-01..11) gave 0 candidates; row prng-ms is complete. prng-step (step-domain seed sweeps) is running.
Phase 28 (`work/log/phase28_square_seeds.md`): no rule in a 5.3-million-rule family generates the 0.6 square's seeds and t (best 3 of 7, chance P 0.14), nor the 0.2 grid's own seeds: the seeds look like free choices; row square-06 closed for that family.
Phase 23 review (`work/log/phase23_review.md`): nothing invalidates the overnight book-key negative; the offset step of 8 is safe; per-window power 80-93%; the sentinel at the last grid offset corrupts the summary's mean / own z only (fix in scan() and rerun the last chunk per book after the queue).
Phase 31 (`work/log/phase31_book_codes.md`): Cicada's six known book codes catalogued; 1,520 preregistered pointer readings of the book's numbers into four local books: best z +2.59 against null maxima 2.93 +- 0.37, negative; grids too short for a language score; multi-coordinate formats need a grouping nothing in the book gives.
Phase 23 stage 2 (`work/log/phase23_stage2.md`): whole-section verifier for book-key hits, quick gate 13 of 16 plants verified (plaintext accuracy 0.99-1.00 when the path is found), 0 of 32 matched nulls.
Phase 30 (`work/log/phase30_pointer_direction.md`): the pointer-direction mechanism ("their numbers are the direction") is built into kscreen (default bit-identical; plants 11/12 recovered); a 1% pilot on window 0.7 is null-like (1.295 vs 1.306). The campaign (about 3.4 h per convention for stage 1) waits for a free CPU.
Phase 32 (`work/log/phase32_h2_drift.md`): a drift-aware H2 tableau statistic has 0-6 / 24 power at 300-1,524 runes under the skip rule: no campaign; H2 stays open.
GPU prng-step: py3 swept all 2^32 seeds (4,790 s): 0 candidates at the floor.
Phase 30 queue: the pointer-direction stage 1 waits detached for the book screen (review `phase30_review.md`: WAIT cap raised to 48 h per line, wrong-engine guard added). Phase 34 (`phase34_2016_message_map.md`): the 2016 message clause by clause against the registry; cheapest untested readings: LP2's own word lengths / sums as key streams, a word-length pointer jump, ciphertext reversed per word / clause / line, direction from page / line numbers.
Phase 29 (`phase29_signed_mults.md`): the signed streams with all 28 multipliers: best 1.3404 against nulls 1.3326 / 1.3359, 0 of 15 verified: negative. Phase 36 (`phase36_layout_rules.md`): 23 sign / direction rules from page, line and position numbers built and gated (15/15 plants); page rules barely differ from the default engine in a 300-rune window; the 13 line / position rules (about 2-3 h on 14 threads) wait for a free CPU. GPU prng-step: php and glibc swept, 0 candidates.
Phase 33 (`phase33_book_number_streams.md`): 80 flat number streams computed from six cited books: best 1.3462 against nulls 1.3191 / 1.3417, 0 of 15 verified: negative. GPU prng-step: java swept, 0 candidates. Book screen: the Mabinogion done, 0 stage-1 hits.
Phase 24 (`phase24_word_edge_channels.md`): the word-edge null / extra-advance arc of chanscreen v2 is built and gated (plants 192/192, power 24/24 at n >= 150, null scan of 320 M cells: best -60.3 vs T300 29.8); the LP2 scan (about 285-400 CPU-hours) waits for a free CPU. GPU prng-step: mt32 and net swept, 0 candidates.
Phase 35 (`phase35_words_map.md`): LP2's own word-length / word-sum sequences as keys (best 1.256 vs null 1.304) and the ciphertext reversed per word / clause / line (1.339 / 1.374 / 1.367 vs nulls 1.321 / 1.304 / 1.379): negative, 0 verified. Phase 37 (`phase37_word_jump.md`): word-length pointer jump built (advsep=3-5, bit-identical default); plant gate failed as defined on two low-IoC plants (1.584 / 1.589 < 1.60, both at the exact offset); screen not run.
2026-10-21 07:30: the PC restarted; all queues relaunched (booknight resumed at Agrippa). The GPU validation failed once because work/kscreen/data/pages.txt was empty (written by an export without OpenCV, "page windows skipped"); re-exported with the .venv interpreter (46 page windows; library, segments and heads byte-identical) and validation passed.
Phase 24 LP2 pilot: window 0.7 under the word-edge arc, 320 M cells, no cell reaches 0 nats (null-like); the 82-window campaign is written, not launched (about 20-29 h on 14 workers). GPU prng-step: msvc swept, 0 candidates; drand48 gave one window candidate (IoC 1.481) that falls to 1.000 beyond its window: not verified (8 of 10 done).
GPU prng-step complete (2026-10-21 10:38): all ten generators over 2^32 seeds; three window candidates (drand48, mt31 x2) fall to 0.99-1.02 beyond their windows: negative.
Phase 38 (`phase38_signal_interactions.md`): no coupling between LP2's signals (isomorphs, DJU BEI under 812 affine maps, S lag-5 x lag-6 overlap, echo-word lengths); verdict independent quirks, with low power for weak couplings.
Phase 39 (`phase39_online_sources.md`, web + archives, data only): the payload's five corrected bytes are confirmed by iddqd's own hex byte string; scream314's sexagesimal.bin is a derived community file (the 10 bytes a community member reported). The signed Jan 2016 and Apr 2017 messages verify (gpg, key 7A35090F); neither holds a key. No online source reports the lag-6 relation or the S lag-5 echo; better page images and the cuneiform signs' meaning were not found.
Book-key screen: Agrippa done, 0 stage-1 hits (six of seven books); the KJV running.
Phases 40-46 (2026-10-21): line:position pointers from the book's numbers (no message; power only for the payload), a keyless batch (doublet fine structure, digraph blocks, 512-bit hashes of every held file, word-length alignment: all null), gap research inside and outside the repo, two read-only Discord passes; three community leads checked and not reproduced ('CicadaPG v.3301' hash, the page-55 affine relation, the DJU BEI 'TRUTH' overlay). Merged to-do list: `work/log/phase46_todo_and_leads.md`.
Phase 47 (`phase47_insertion_doublets.md`): insertion after a 100% anti-repeat rule explains the doublet count only with mid-word insertions (joint p 0.08); edge-only insertion is rejected (p 0.000), so the 300-CPU-hour word-edge campaign is not justified by the +1-rune length fit.
Phase 48 (`phase48_ai_oracle.md`): the A/I oracle calibrates at 27/27 on the solved plaintext (one-rune words are A or I); no hit any campaign kept reaches 0.5 (best 0.40, null 0.22); as a full screen it costs about 330x an IoC decode, so it serves as a verifier and post-filter.
2026-10-21 queue now1: Gibson's Agrippa as a table-free book key 0 hits; word-length pointer jump (advsep 3/4/5) negative (best 1.365 vs null 1.348); 4 layout sign rules negative (best 1.345 vs 1.322).
Phase 49 (`phase49_p13_1033.md`): Mike's skip-optimised period 13 on 54+55.jpg reproduces (1.7155) but does not survive its selection (P 0.26 over the searched cells, 0.04 for the pipeline maximum at p = 39); the 1033.jpg blob is a two-line added mark, not a shrunken logo, but rectangles fit as well as Roman numerals.
2026-10-21: the 2012 Blake second-chance code reproduces 22/22 as line:character on plate 4 of MHH with the plate's line breaks (`work/blake_second_chance.py`; plate 3 was a misreading); all three 2012 book codes follow the same rule.
Phase 53 (`phase53_nested_marks.md`): LP2 has the same five marks as the solved sections (word, clause, line, paragraph `&`, page `%`), no LP2-only mark and no open/close pair (`&` ends sections, nesting holds in 72% of shuffles); a key stack would have no marked levels to use.
2026-10-22: Discord proposals checked: avaster's cumulative prime-multiplier cipher puts every doublet on a plaintext NG (LP2 has 26 doublets across word gaps; the solved text has 2 word-initial NG in 2,977 runes) and decrypts to best IoC 1.236 at prime offsets 0-19,999 (control recovered 1.820): negative; DCPH's book key + random skip is the excluded skip/coin + book-key model.
Phase 55 (`phase55_s_echo_dissect.md`): the 11 lag-5 S,S pairs reproduce (null 1.8-2.4); corrected over 203 cuts P 0.021 against the conservative across-word null; S has no favoured word position (p 0.70) or length (p 0.48), the 11 words are as long as lag-5 windows predict, neighbours are not fixed, S is no more frequent than in the solved text: no marker/filler rule follows.
Phase 54 (`phase54_lag6_dissect.md`): the 80 lag-6 sites reproduce (null 45.7 +/- 6.5, z +5.3); all word positions 0-4 are elevated 1.5-4x (no fixed slot), words of exactly 7 runes show none (8 vs 8.0) while 8-9-rune words show 2x (p 0.003/0.0002, 33 cuts), no single c dominates, no neighbour marks c' as a repaired collision (c[i+5] = c' is 1 vs 1.6), doublet-window overlap as expected, solved 0.0-0.6 shows no excess (z +1.4): a per-pair lookback event in words of 8+ runes; nothing pins the repair rule.
Phase 52 (`phase52_an_end_archives.md`): An End's SHA-512 against 3,739 archived capture files (Wayback, Ahmia; 124,017 digests): no match; 24 spam-injected captures blocked by the antivirus, not hashed. Phase 50 (`phase50_verifier_and_block.md`): verifier checks in verify.py, alphabet orders incl. 15 OEIS prime orders (Mayfly lead) and solved-phrase keys with Cicada's spelling habits: 0 verified hits.
Phase 56 (`phase56_lag6_length_rules.md`): four word-level rules simulated (1,000 replicates, English, random key): phase-25 repair and a block rule fit LP2's lag-6 length bins (chi2(6) 5.7 / 3.9, P 0.48 / 0.68), an insertion gate at position 7 and a period-6 key restart do not (P 0.001); the 7-rune 'gap' is 8 vs 10-12 expected, i.e. noise; no rule touches the word-length histogram. No mechanism singled out.
Phase 57 (`phase57_mechanism.md`): nine encryption rules scored on all LP2 anomalies at once (500 replicates, English, random key). Best: R4 = collision repair writing T(c-6) inside words (q 0.81) plus one checked null in ~45% of multi-rune words (chi2 6.7 over 9 statistics, P 0.64; the later-pass and end-rune variants miss a side prediction by 1.6-1.8 sd). Every rule without a per-word extra rune fails the word lengths (G z +8 to +9), a per-rune null too (+6.3); no single trigger gives both the T relation and the lengths. DJU BEI is made by no rule (P <= 0.002). The implied search (chanscreen mid arc) recovers 12/12 R4 plants; LP2 pilot 0.15 @ 0, n 150, full library: max -4.9 vs T300 29.8 (negative). Nothing solved.
Phase 58 (`phase58_djubei_reuse.md`): DJU BEI as reused key. 1,439 library streams scanned for equal 6-runs at key distance 5,700-6,500 (100 shuffles each; planted control found): 31 structured number families exceed their shuffle maxima (arithmetic regularity, not tied to 6,395), none decodes (best window IoC 1.088 of 686 offsets). Constraint recorded: any key must repeat the 6-run at the copies' key positions. Nothing solved.
Phase 59 (`phase59_keywords_r4.md`): keyword keys under R4. 1,940 periodic keywords (solved pages, 2014 messages, variants; lengths 3-30) through the mid-word arc (hold/spend, both signs, all phases) on all 48 n300 windows of 0.7-0.15, plus phi(prime) on 4 channels: max S_guard -64.0 / -62.5, 0 cells >= 20. Control 44/44 R4 keyword plants recovered (113.8+ nats). Excluded for this keyword set and these channels only.
Reproduce (`scripts/reproduce_signals.py`, registry `reproduce-signals`): one command recomputes the FINDINGS section 1 numbers with PASS/FAIL (1-4 min, below-normal priority). Result: everything reproduces except one wording error, now fixed: the doublet rate is 0.66% of all adjacent pairs (86 of 12,947); 0.63% is the in-word rate (63 of 10,060). The phase 54 (28.75) vs phase 57 (1.4) per-section lag-6 statistics differ only by their expectation (section-composition shuffle mean vs equal rate per site); notes appended to both logs.
Phase 60 (`phase60_clue_review.md`): clue review of page art, archives, wiki and solved-text phrases against the registry (30-row ledger, top 5 untested clues specified). Images: the black glyph ending 0.11 (image 39) is the 0.7 Russian cross rotated 90 degrees; art is page-invariant inside a part and LP1 shows no art -> method rule. New clue never used: Cicada's 2013 "The key is all around you" (Cicada OS message). Extra rune as a function of the other runes, previous word, index or length (45 tests, planted 15-45% recovered, 2,000 shuffles): max z +2.08, P(max) 0.58, no prime-length padding: negative. Top 5 to run: phi/sigma/pi of word sums, Cicada number strings under R4, solved LP1 text as running key, Cicada OS blobs, four irrationals. Nothing solved.
Phase 60 follow-up (`phase60_clue_review.md` section 7): the five ranked tests run, each with a planted control and a matched null, all negative. T1 phi/sigma/pi of word sums: engine screen best IoC 1.2738 (null 1.2951), word-aligned fixed-point share 0.714 (P 0.92), direct decode IoC 1.006 (P 0.48), word-level feedback P 0.32. T2 Cicada number strings (50 keys) and 256-byte onion strings (20) under R4: max S_guard -56.8 / -57.4, 0 cells >= 20, controls 32/32 and 24/24. T3 solved LP1 text as table-invariant running key (forwards, reversed, wrapped): 0 stage-1 hits, best gate z +3.7, plant power about 2/3. T4 Cicada OS binaries: 632 M decodes best IoC 1.3268, folly under R4 max -65.9. T5 four irrationals: section windows best 1.3094 (null 1.3436); page-start windows 1.488 / 1.594 are short-window artefacts (random null 1.689). New archive findings: 'The key is all around you' (Cicada OS, 2013), the black glyph of image 39 is the rotated 0.7 cross, red runes are not plain English. Nothing solved.
Phase 60 second follow-up (`phase60_clue_review.md` section 8): XOR-domain keys defined exactly (index XOR wrapped, prime-value XOR wrapped, index XOR with pass-through; reject-skip not screenable) and screened by key-class coincidences: library best z 6.82 in 103 M trials (chance expectation 0.1), number / onion strings 4.95 (null 6.76), megabyte files 6.21-6.93, nothing at the preset 7.5; controls detect R4-free XOR plants (5-8 of 8) but 0 of 8 under R4's extra runes, so only R4-free XOR is excluded. The megabyte Cicada OS files under R4: every offset (19.7 M) of one window, 3.56 CPU-h, max S_guard -52.3, 0 cells >= 20, 8/8 plants. Remaining untested Cicada-material families: the 118 MB object behind 560.13 and the audio (not held / OpenPuff), XOR under R4 and reject-skip, the P.S. number and cookies as integers, the An End page. Nothing solved.
2026-10-22 correction: word segmentation in work/discord_cumulative_check.py now merges bare line / page wraps (as lp.word_spans): LP2 has 23 (not 26) of its 86 doublets across word gaps, gap share 22.3% (not 25.5%); the solved text has 0 (not 2) word-initial NG; the gap-doublet test is stronger, the verdict unchanged. Also checked (pasted AI analysis): LP2 doublets are not confined to word boundaries (63 inside words, 0.63%; 23 across gaps, 0.80%: suppressed equally), word lengths are not padded to even (50.1% odd vs 47.5% on the solved pages), and no compression or file header starts LP2 read as base-29 or 5-bit packed (60 conversions x 12 signatures).
Phase 60 third follow-up (`phase60_clue_review.md` section 9): DATA/560.13 of the 2013 Cicada OS (118.8 MB, uniformly random: entropy 8.0, no anti-repeat) as a key, and the 2013/2014 audio payloads (MP3 frames stripped of ID3 and headers) as byte streams. 560.13: additive plain screen on the section windows (start region of all four maps complete, 16 M of 118.8 M offsets sampled per map about 7%, 515 M decodes) best IoC 1.3249; R4 (start region against all 48 windows, 5.8 M sampled offsets of one window) max S_guard -45.4, 0 cells >= 20; XOR (9 M sampled offsets) best z 6.84 against a preset 7.5. Audio (21 M offsets, 339 M decodes, model 0): best IoC 1.3165; audio payload is compressed, not random. All with planted controls recovered. About 5.7 CPU-h. Remaining: arbitrary offsets of the pad (about 93%), XOR under R4 / reject-skip, audio as PCM or notes, the P.S. number and cookies as integers, the An End page. Nothing solved.
2026-10-22: queued r4lib (`docs/QUEUE.md`): the full library under R4 (phase 51 engine, hold / spend) on the section-start n300 windows of 0.8, 0.9, 0.11-0.15, about 20 CPU-h, after the current queues.
2026-10-22: Zipf / word-frequency check (`zipf-words`): LP2's words repeat exactly as random runes would (2,731 distinct of 2,896; nothing above 3 runes repeats) and its 83 one-rune words are uniform (P 0.85): no word-level code; a 2021 'Zipf' claim came from mixing in the solved pages and numerals.
Phase 61 (`work/log/phase61_unrepair.md`, `work/phase61_unrepair.py`, registry `unrepair-lag6`): un-repair via lag-6 sites tested on simulation and plants, negative. Detector D (within-word c_i = 24 - 2 c_(i-6)) on 250 R4 simulations: 75.4 +- 11.6 sites per text (LP2 80), precision 0.433, recall of ALL repairs 0.100 (only repairs at word position >= 6 can be T-valued). Un-repair c_i := c_(i-1) with the TRUE key LOSES: mid-engine true band -2.2 nats (n 300, se 0.4), matched-null winner +0.6 (separation -2.8; n 150 -2.5), IoC unchanged (-0.00003 +- 0.00004); D sites forced as repairs -9.8 / -3.8. Only the full R4 likelihood (repair rune must equal T(c_(i-6)) at word position >= 6, not D itself) helps: separation +6.5 nats at n 300, +2.8 at n 150 (93/96, 84/96 plants up; no nulls, an upper bound) against raw margins of 215 / 108 nats; needs a Rust change and R4 to be true. LP2 windows not run.
Phase 62 (`work/log/phase62_shared_keys.md`, `work/phase62_shared_keys.py`, registry `shared-keys`): shared keys between LP2 sections (same / sign-flipped / reversed key, all offsets, 28 pairs): nothing beyond the max-statistic null (global z 6.59 vs 95th pct 7.94; 0.7 vs 0.11 best 5.71); power is low (0.7-0.11 plain 0.00-0.06, 0.14-0.15 0.56-0.69, R4 with drifting key 0), so only long pairs under the plain model are excluded.
Phase 63 (`work/log/phase63_change_points.md`, `work/phase63_change_points.py`, registry `change-points`): change points of LP2's doublet / lag-6 / word-length rates per page (57 pages, 0-2 change points, permutation and R4 nulls): none significant (smallest P 0.08, 0.41 after correction; control power only 0.14); one R4 setting (q 0.81) gives 0.58% / 0.60% for the two groups vs LP2 0.53% / 0.77% (P 0.05 one-sided, 0.11 two-sided); lag-6 ratio does not move.
Phase 64 (`work/log/phase64_clause_structure.md`, `work/phase64_clause_structure.py`, registry `clause-structure`): LP2's clause structure is not LP1's: mean clause 77.5 vs 31.8 runes (P 0.0002), LP2 like prose sentences, LP1 comma-sized; the word before a clause mark is 1.4 runes longer than average in English and LP1 (+1.5) but not in LP2 (-0.25; z -3.7 / -6.6); no length trace of prime sums in either (odd counts 0.56 / 0.49).
