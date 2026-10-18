# Fact check: "Liber Primus page 12 is officially 100% solved" (r/Cipher, October 2026)

Asked by the user on 2026-10-18 (laptop, branch `factcheck/reddit-page12`). The post:
<https://www.reddit.com/r/Cipher/comments/1wy647j/update_liber_primus_page_12_is_officially_100/>.
Reddit could not be opened from this machine (both the fetch tool and the built-in browser refuse the site), so this check
works from the post's text as the user pasted it. The comments were not read. The claim is third-party material: it is
treated as data, and nothing of the author's was run (the post publishes no code anyway).

Script: `work/factcheck_page12.py`. Output: `results/analysis/factcheck_page12_2026-10-18.txt`. Every number below
comes from that output.

## Verdict

**The claim does not hold.** Page 12 is not solved, and the method as described cannot have produced the sentence from
it. Three of the findings below do not depend on how the underspecified method is read:

1. **Numbering.** In the numbering of the 2014 release's files (0.jpg-57.jpg), page 12 is unsolved, but page 56 is
   *An End*. That page has a known solution, which this project reproduces exactly; it begins AN END. WITHIN THE DEEP
   WEB THERE EXISTS A PAGE THAT HASHES TO. The post's page-56 text ("TWENTY FOUR MONTHS WAS HERE ...") contradicts it.
   In whole-book numbering (images 00-74), page 56 is unsolved, but then page 12 is a page of *The Loss of Divinity*.
   That page is written in plain runes and has been readable since the 2014 release (MOST THINGS ARE NOT WORTH
   PRESERVING ...). One of the two claims is wrong under either numbering.
2. **Length.** LP2 12.jpg has 261 runes. Every stage the post names maps one symbol to one symbol, so a decryption
   of the page has 261 symbols. The claimed sentence has 56 runes (59 letters), so 205 runes (79% of the page)
   would be left over. "Zero leftover character drift" cannot be true.
3. **Fingerprint.** The method has no step that avoids repeating a rune. Ciphertexts made with it have about 10
   doublets (the same rune twice in a row) on a 261-rune page. Page 12 has 1, and only 1 of 1,000 simulated pages
   gets that low. Over all of LP2 the method predicts about 490 doublets where there are 86 (P about 1e-112). It
   cannot be the cipher of LP2.

The other findings: the sentence's word lengths fit no 15-word run anywhere in LP2. The 5x6 "Bifid" is not a
bijection, so it is not even a well-defined cipher. And in 82,944 concrete readings of the method, with planted and
null controls, neither page 12 nor any other unsolved page gives English or the claimed sentence.

## 1. The claim

The pasted post says page 12 gives "TWENTY FOUR PAGES WERE WRITTEN FOR YOU TO FIND THE SECRET PATH TO THE END". The
method is three stages: "the standard Dynamic Multiplier 7 Mod-29 framework", a "post-multiplier SUMUS key subtractor
array", and "the 5×6 Vowel-First Polybius fractionation square (Bifid Style)". It also says there is "zero leftover
character drift". It cites two earlier results by the same author: page 56 gives "TWENTY FOUR MONTHS WAS HERE...",
and page 28 gives "108.192.168.50 GATEWAY".

There is no code, no square layout, no key values and no intermediate numbers. "Standard" is not accurate either: no
solved Liber Primus section uses a multiplier, SUMUS or a Polybius square. The solved sections use Atbash, Atbash + 3,
Vigenère with DIVINITY or FIRFUMFERENFE, the φ(prime) stream, or no cipher (`PLAN.md`, toolkit check).

## 2. Which page is "page 12"? (section A of the output)

| convention | page 12 | page 28 | page 56 |
|---|---|---|---|
| LP2 file number (0.jpg-57.jpg = images 17-74) | image 29: **unsolved** 0.9, 261 runes | image 45: unsolved 0.13 | image 73: **An End, solved** |
| whole-book image number (00-74) | image 12: **The Loss of Divinity, plain runes** | image 28: unsolved 0.9 | image 56: unsolved 0.14 |
| LiberPrimus.pdf page | image 11: The Loss of Divinity, plain runes | image 27: unsolved 0.9 | image 55: unsolved 0.14 |
| this project's transcription page index | image 14: A Koan (Vigenère) | image 30: unsolved 0.9 | image 58: unsolved 0.15 |

The post says page 12 had "0% progress", so it must mean the LP2 file numbering, in which 56.jpg is An End, the page
with the hash. Under that numbering, the page-56 text is false: An End decrypts exactly with the key φ(p_n) = p_n − 1
and one literal F (`lp.KNOWN[16]`, golden file `work/tests/expected_solved.txt`). The rest of this check uses LP2
12.jpg (image 29, section 0.9, runes 1059-1319).

## 3. Length and word pattern (section B)

- LP2 12.jpg has 261 runes and 65 words. Its first word lengths are 2 3 3 4 3 3 3 5 9 9 6 10 5 2 2.
- The sentence has 15 words and 56 runes in the Gematria Primus spelling. Its word lengths are 6 4 5 4 7 3 3 2 4 2 6
  3 2 2 3 in runes, or 6 4 5 4 7 3 3 2 4 3 6 4 2 3 3 in letters.
- A one-to-one cipher gives 261 plaintext symbols for 261 runes, which leaves 205 runes unexplained.
- Neither length pattern occurs in any of the 2,782 runs of 15 consecutive LP2 words. The best partial fit anywhere
  is 9 of 15 word lengths. In every solved section the word separators are the plaintext's word boundaries, so a
  true plaintext of a page would have the page's word lengths.

## 4. The 5x6 Bifid is not a bijection (section C)

A Bifid writes each symbol as a (row, column) pair, re-pairs the coordinates and reads the new pairs off the square.
With 5 rows and 6 columns, a column index of 6 can land where a row index is read, and the 30th cell is empty (29
runes). The 6 x 5 orientation has the same problem with row 6. So the map is not a bijection. (The script's Bifid code
reproduces the textbook example FLEEATONCE -> UAEOLWRINS; `work/tests/test_factcheck_page12.py`.)

- 958 of 960 English windows of 261 runes cannot be encrypted at all with the rune squares. With the letter squares
  the figure is 480 of 960; the 6 x 5 letter squares fail only on Z.
- Decrypting page 12 with the rune squares (strict rule) leaves 3.1-10.7% of its positions without a plaintext symbol.
- Only some placements of the sentence can come out of such a decryption at all: 22,539 of 98,880 for runes and
  67,862 of 131,040 for letters (8 squares, periods 0 and 2-60, every offset). This is a constraint on the claim, not a
  refutation.

## 5. The method in every reading we could define (section D)

We cannot know the author's private implementation, so the grid tries every reading we could define. Per text it
runs 82,944 decodes:

- **multiplier** (9): none, ×7, ×25 (= ÷7), ×7^(i+1), ×25^(i+1), ×7(i+1), ×(7+i), −7i, +7i;
- **SUMUS stage** (8): none; the runes S U M U S subtracted, added or as Beaufort; the Gematria primes of SUMUS mod 29
  subtracted or added; A = 0 letter values subtracted or added;
- **position origin** (2): the page start or the section start (rune 1059);
- **two paths**. The rune path uses 8 rune squares (AEIOUY first, the 11 vowel runes in GP order, AEIOU first, and a
  column-filled square; each 5x6 and 6x5) in two stage orders (the post's order, or the Bifid first). The letter path
  writes the runes as letters and uses 8 letter squares (AEIOUY or AEIOU first, row- or column-filled, 5x6 and 6x5);
- **Bifid period** (12): the whole text as one block, or periods 2-12;
- **overflow rule** (2): strict or wrap.

Scores: the mean English bigram score per adjacent pair, using the project's rune table and a letter table built the
same way (Cicada's solved text scores +7.40). "Claim match" is the largest number of positions that any placement of
the sentence shares with an output: 56 for runes, 59 for letters.

- **Page 12:** the best rune output scores −8.37 and the best letter output −4.46. Both are noise
  (FAELTHOBRUCEANEO..., QTJCJIFAWVUOEBEK...). The best claim match is 12 of 56 runes and 15 of 59 letters.
- **Null control** (200 texts of 261 runes: half uniform random, half shuffles of page 12). Page 12 is inside the null
  on all four statistics:

  | statistic | null median | null 95% | null max | page 12 | nulls at or above page 12 |
  |---|---|---|---|---|---|
  | rune best score | −8.33 | −7.55 | −7.03 | −8.37 | 105 of 200 |
  | rune claim match (of 56) | 12 | 13 | 15 | 12 | 190 of 200 |
  | letter best score | −4.34 | −3.66 | −3.23 | −4.46 | 139 of 200 |
  | letter claim match (of 59) | 14 | 15 | 15 | 15 | 28 of 200 |
- **Positive control** (PLANTN planted pages): each plant is 261 runes of Cicada's solved text with the claimed
  sentence spliced in, under a random reading with an invertible multiplier and a strict square. Plaintext symbols
  that no 5x6 Bifid can produce are replaced first (4-31 of the 261 runes). **24 of 24 recovered:** in every plant
  the top decode of the grid is the planted text, 100% of it, and no decode scores higher (10 plants in the post's
  stage order, 14 with the Bifid first). The top scores are +3.83 to +7.81, against a null maximum of −7.03. The claim
  match is 47-56 of 56; it is below 56 only where sentence runes had to be replaced. A second control plants
  Cicada's text in letters straight into the letter Bifid (the rune -> letter step has no inverse, because no rune
  is written K, Q, V or Z): 24 of 24 recovered, top scores +3.81 to +8.37.
- **Every unsolved page** (the post: "the mathematical master key is holding up flawlessly"). The grid ran on 53 of
  the 56 LP2 pages; the 3 that straddle two sections were skipped. Each page was set against 20 null texts of its own
  length, 92,316,672 decodes in all. If the method carried no signal, about 2.5 pages would beat all 20 of their nulls
  on each statistic, a little fewer where integer ties occur. The counts are at chance:

  | statistic | pages above all 20 of their nulls | median nulls at or above the page |
  |---|---|---|
  | rune best score | 2 of 53 | 9 of 20 |
  | rune claim match | 1 of 53 | 18 of 20 |
  | letter best score | 1 of 53 | 11 of 20 |
  | letter claim match | 0 of 53 | 17 of 20 |

  The claim match never exceeds 14 of 56 runes or 15 of 59 letters on any page. The largest excess over a page's own
  null median is LP2 55.jpg, the 76-rune last page: −3.07 against a null median of −4.63 and a null maximum of −2.67.
  On the letter path the largest is LP2 13.jpg: −3.64 against −4.64 and −3.78. That page is the one of 53 above its
  20 nulls, and its output is noise (EPACAQBBBEONHENANNOFOAUG...).

## 6. The fingerprint the method would leave (section E)

- **Doublets.** Page 12 has 1 doublet (the same rune twice in a row) in 260 adjacent pairs. The claimed method has no
  step that avoids repeats. Ciphertexts made with it from Cicada's solved text (1,000 random readings, with the
  plaintext made reachable first) have 9.85 doublets per 261-rune page (sd 3.26); only 1 of the 1,000 has 1 or fewer.
  Over all of LP2, the method's rate (3.79%) predicts 490 doublets in 12,947 pairs, where LP2 has 86: P(≤ 86) =
  1.2e-112. Every LP2 page shows the deficit (`PLAN.md`, Phase 3). The method cannot be the cipher of page 12 or of LP2.
- **IoC** (×29): page 12 has 0.985; the method's ciphertexts have 1.075 ± 0.089 (1.128 ± 0.099 with a constant
  multiplier). This is not decisive at 261 runes.

## 7. The two other "blueprints"

- **Page 56** (see section 2): in LP2 numbering this is An End. Its plaintext is known, reproduces exactly here, and
  does not match.
- **Page 28, "108.192.168.50 GATEWAY"**: LP2 28.jpg (image 45) has no numerals among its runes, and the Gematria
  Primus has no digits. Python's `ipaddress` gives `is_private=False` for 108.192.168.50, which is outside
  192.168.0.0/16 (RFC 1918 needs 192.168 as the first two octets). It is a public address, not a "local mesh gateway".

## 8. Limits, and what would change the verdict

- We could not read the thread or its comments. The author's implementation is private, so their method may differ
  from all 82,944 of our readings. Findings 1-3 of the verdict do not depend on the reading.
- To change the verdict, the author would need to publish the code, the square, the key values and the intermediate
  arrays for all 261 runes of 12.jpg, so that anyone can get the sentence back from the ciphertext. The method would
  also need to decrypt a second page chosen in advance, and to explain LP2's doublet deficit.
