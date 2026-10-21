# Phase 31: book codes. Is there any pointer reading of LP2 or the book's numbers that can be tested with power?

Nothing in LP2 is solved. Archive files are DATA ONLY (`Other repositories and work/`: `ARCH` = "The-Complete-Cicada3301-Archive",
`CTX` = `cicada3301_context/`). Code `work/phase31_book_codes.py`, output `work/log/phase31_book_codes_output.txt`.
Whole run: 4 min on 1 core.

## 1. Every book code Cicada used (from the archive)
| # | Year | Pointer format | Book | Produced | Archive citation |
|---|---|---|---|---|---|
| B1 | 2012 (final.jpg) | `n:k`, n = 1..76 running index, k = 1..65 (76 pairs) | Mabinogion, "The Lady of the Fountain" (Guest), text found by a Vigenere decryption | "Call us at US telephone number ..." (a phone number) | ARCH `assets/2012/1CcV1.jpg.out`; CTX `What Happened _2012_.txt` lines 7, 19, 21 |
| B2 | 2012 (second chance) | 22 pairs `a:b` (a <= 18, b <= 40) | Blake, Marriage of Heaven and Hell | 22 characters = `sq6wmgv2zcsrix6t` + `.onion` (an onion address) | ARCH `assets/2012/NHYLD.jpg.out`; CTX `The second chance _2012_.txt` line 9 |
| B3 | 2012 (QR-code messages) | riddle: "In twenty-nine volumes ... how many lines of the code remained when the Mabinogion paused? Go that far in ..." | Mabinogion | onion addresses | CTX `What Happened _2012_.txt` line 29 |
| B4 | 2013 (5 Jan) | `ROMAN:verse:number` (I:1:6, III:23:58 ...), 32 + 11 entries, groups followed by a lone number (5, 0) | Liber AL vel Legis (riddle "dictated to a beast"; sacred-texts engccxx) | a dropbox link (45 chars) to the 3301 Linux CD | ARCH `2013/additional docs/signed messages/book code pastebin.txt`, `C5G2fNPR.txt`; `CICADA 3301 2013 INFO.txt` lines 111-126 |
| B5 | 2014 (6 Jan, zN4h51m.jpg) | paragraph : sentence : word : letter (first paragraph, 2nd sentence, 3rd word, 1st letter ...) | Emerson, Self-Reliance and Other Essays | `auqgnxjtvdbll3pv` + `.onion` | CTX `What Happened Part 1 _2014_.txt` line 3; ARCH `2014/additional docs/Self-Reliance and Other Essays/`, `assets/2014/stage01/README.md` |
| B6 | 2014 (onion 5) | `chapter-code:dialogue line:word:letter` (3PI:6:1:3, LML:1:1:1 ..., 22 entries, bare digits copied literally) | Hofstadter, Goedel Escher Bach (dialogues) | `ut3qtzbrvs7dtvzp` + `.onion` | ARCH `2014/additional docs/Titanpads from time of solving/The complete story of onion 5.txt` lines 113-170; `assets/2014/stage08/README.md` |

Pattern: every Cicada book code was introduced by an outside hint to the book (a riddle, an image, a link), printed its pointers in the
clear next to the clue, and produced a short low-entropy string (URL, onion address, phone number) whose length equals the pointer count
(12-76). None was a free-floating pointer set inside a ciphertext.

Own reproduction attempts (a positive check of the harness, on local copies): B4 with the OTO text of Liber AL, rule "k-th letter of verse v,
letters only": output `ettpehsrnwo...`; characters 2-4 spell `ttp` (expected `http`), the rest and the first character do not: edition or counting
differs. **Not reproduced** (Level 0). B1 and B2 with the simple rules (first/last letter of word k, letter n of word k) did not match: **not reproduced**.
The 2012 README itself lists "the unsolved book code".

## 2. What in Liber Primus could be pointers (counted from lp_verified.txt)
| Object | Values | Count | Pointer formats from section 1 that fit |
|---|---|---|---|
| 0.2 grid, printed numbers (the other cells are words) | 18-272 | 12 (6 distinct) | B1/B2 `n:k` (value = k), single index |
| 0.6 square | 204-1311 | 25 (13 distinct) | single index into a long text (values too large for B1/B2; B5/B6 need small values) |
| page-30 / segment 0.10 grid | 708-4516 | 16 | single index into a very long text only |
| 256-byte payload (base-60) | 0-255 | 254 usable | B1/B2 style small `k`; length 256 is far above the 12-76 pointers Cicada used |
| LP2 numerals | 1-5 (list labels), 7, 1, 2 | 8 | none (too few) |
| Gematria sums of LP2 words (ciphertext) | 5-700+ | 158-300 per section | single index (B1-like) |
| LP2 word lengths | 1-13 | all | would be the word or letter coordinate of B5/B6 tuples |
B4-B6 need 3-4 coordinates per output character. None of the objects supplies a natural 3-4-tuple grouping; the only grouping the book prints is the 5 x 5 / 4 x 4 grid shape.

## 3. Availability of the books and the preregistered test
Local (`work/ref/`): Mabinogion (Guest, PG 5160), Blake MHH (PG 45315), Liber AL (OTO text), Emerson Self-Reliance (PG essays; Cicada used the
Dover edition, so paragraph breaks may differ). Not local: Goedel Escher Bach (copyright; needed for B6). Agrippa OCR is local but noisy and unused.

Test (`work/phase31_book_codes.py`): pointer set (12 sets: 0.2 grid, 0.6 square, page-30 grid, payload, 8 LP2 sections' word sums) x format (10: letter k; word k
first/last; paragraph a letter/word b; sentence a letter/word b; paragraph:sentence:word; chapter:verse:letter; paragraph:sentence:word:letter) x book (4) x ordering
(printed, reversed, column-major for 2D grids, distinct values) = **1520 candidates counted in advance**. Score: letter-trigram log-likelihood of the resolved
string (trained on Republic, Origin of Species, Walden, Ethics: none of the four tested books), turned into a z against 100 random pointer sets with the same
per-coordinate range; a candidate needs >= 90% valid pointers. Null: the whole screen repeated 12 times with random pointer sets of the same lengths and ranges.
Positive control: a plaintext planted with random valid pointers.

## 4. Results
- 456 of 1520 candidates were scorable (the rest had pointers outside the book). Best z = +2.59 (seg 0.9 word sums | last letter of word k | Self-Reliance | distinct values); next +2.18, +2.18, +2.11, +2.02. All are LP2 word-sum sets; none is a small grid.
- **Null screens: the maximum z over a whole screen is 2.93 +- 0.37 (largest 3.80 in 12).** The real best (2.59) is below the null mean maximum: nothing.
- Positive control (plant inside the 0.6-square range, detection threshold max(null 95% max = 3.5, 4)): 12 letters 0/7, 25 letters 4/6, 64 letters 2/3. A language score has no power below about 20 letters and mediocre power at 25.
**Level 1: negative for single-index readings under a trigram score; no power for the 12-16-pointer grids.**

## 5. Candidate pairings: cost and expected power
| Pairing | Cost | Expected power (language score) | Status |
|---|---|---|---|
| 0.2 grid (12) -> any book, single index | seconds | about 0 (planted 12 letters: 0/7) | run: nothing |
| 0.6 square (25) / page-30 grid (16) -> single index in 4 books | seconds | 25 letters about 2/3; 16 letters about 0.2 | run: nothing (z <= 2.6) |
| 256-byte payload -> small-k formats | seconds | good in principle (254 characters), but values 0-255 confine it to the first 255 words/letters | run: nothing |
| LP2 word Gematria sums per section -> single index | 1 core-min per book | high (150-300 characters) | run: nothing (best 2.59 < null max 2.93) |
| LP2 word lengths / rune values as word or letter coordinates of B5/B6 tuples | needs a grouping rule and, for B6, GEB | n/a | not testable: grouping and book missing |
| Anchored test (not run): resolved string must read `HTTP`, 16 base-32 characters + `ONION`, or a 10-digit phone number (the output forms of B1-B6) | seconds | 12 pointers suffice since the target is fixed (chance 26^-4 for `HTTP`) | worth doing only after a pointer format and book are fixed |

Missing for any real test: which book, which format (Cicada always gave a riddle), and how the numbers group into tuples; nothing in the book states them.
**Verdict: no book-code reading of LP2 or its numbers is testable with power beyond the single-index screen done here, and that screen is negative.**

## Addendum 2026-10-21: book code B1 reproduced (the counting rule was line:character)
Prompted by the user (the Uncovering Cicada wiki shows the 2012 text with its fixed line breaks). Pointer list `assets/2012/1CcV1.jpg.out` (76 pairs `n:k`) and the line-wrapped "Lady of the Fountain" text in the archive (`2012/additional docs/the subreddit/the mabinogion.txt`, 68 lines; both read as data, nothing run): **n = line number, k = character position in that line, 1-based, spaces counted**. Output: `Call us at us tele phone numBer two one four three nine oh nine six o` followed by 7 pointers past the archive copy's last line (the known message ends "...oh eight"). The four leading pairs already give `Call` (1:20 C, 2:3 a, 3:5 l, 4:20 l).
Consequence for section 3: the 1,520 preregistered readings did not include a line:character format on a fixed line layout, which is the one Cicada demonstrably used in 2012. A line:position test on Liber Primus's own lines (the transcription keeps line breaks) is a new, concrete format; not run.
Context (user, 2026-10-21): in 2012 the code was the last link of a chain: a string from Mayan numerals gave an order of operations, applied to the subreddit strings it named the book, and the OutGuess payload's book code then read the phone number from that book's line layout. The reproduction fixes Cicada's counting rule (line:character, spaces counted), not a free-standing method: an LP test in this format needs a pointer list and a target text that some earlier step supplies (candidates: the 0.2 / 0.6 squares, the page-30 grid, the 256-byte payload, read as line:position pairs).

## Addendum 2026-10-21 (2): the 2012 Agrippa code reproduced; B2 corrected
The archive image `assets/2012/everywhere.jpg` (2012 QR-poster stage) holds a signed OutGuess message (extracted with the repo's own `work/ogscan` reader, default key; nothing third-party run): "A poem of fading death, named for a king / Meant to be read only once and vanish", then 22 pointers `1:5, 152:24, [the product of the first two primes], 14:13, 7:36, 12:10, 7:16, 24:3, 271:22, 10:7, 13:28, 12:7, 86:17, 93:14, [the product of the first two primes], 16:7, 96:4, 19:13, 47:2, 71:22, 75:9, 77:4`. On William Gibson's *Agrippa (a book of the dead)* as published on the author's site (Wayback 2019-03-22, owner's copy `work/ref/user_downloads/agrippa_gibson_wayback_20190322.txt`, 344 lines), line n : character k, 1-based, **blank lines counted**, spaces counted, the two phrases read as the digit 6, it decodes to **`sq6wmgv2zcsrix6t.onion`** exactly (the poem's own letters spell ".onion"); counting only non-blank lines gives garbage. Positive control for the edition and the counting rule, and a second confirmation of Cicada's line:character convention.
**Correction to B2:** `sq6wmgv2zcsrix6t.onion` is the output of this Agrippa code, not of the Blake code. The Blake "second chance" code (`assets/2012/NHYLD.jpg.out`, "Miss round 1? Care for a second chance?", 19 pairs from 1:22 to 3:11) is a separate code whose output is not reproduced here.

## Addendum 2026-10-21 (3): the Blake "second chance" code identified, not reproduced
`assets/2012/NHYLD.jpg.out` holds 22 pointers (1:22 ... 18:18, lines <= 18, characters <= 40); the archive's account (`cicada3301_context/The second chance _2012_.txt`) gives its output as **cginiziglyaobyph.onion** (served from the same server as sq6wmgv2zcsrix6t.onion). The message's image link `hkdgl.png` (in the archive) is the illustration of **plate 3** of The Marriage of Heaven and Hell, so the pointers index the text of plate 3 ("As a new heaven is begun ..."), lines of Blake's plate (<= 40 characters), not the Gutenberg line wrap (about 70). Re-wrapping the Gutenberg text of plate 3 at every width 30-50 matches at most 3 of 22 characters (chance). Reproducing it needs Cicada's plate-3 line layout (a transcription that keeps the plate lines, e.g. the William Blake Archive or Erdman); a book-key negative on our Blake copy says nothing about that layout.
Follow-up the same day: the William Blake Archive's transcription of copy A (its public API, `/api/object/mhh.a.illbk.02` and `.03`, read in the app's browser; certificate checks fail for plain fetches) gives plate 3 only 13 plate lines (the pointers reach line 18) and plate 2, The Argument, 24 short lines; line:character on plate 2 (archive and Gutenberg wording) gives 0 of 22 characters of cginiziglyaobyph.onion. Not reproduced; the code counts another text, layout or unit. Needed: what Cicada's 2012 message pointed to (the 'second chance' page's full text or a solver's worked decode).

## Addendum 2026-10-21 (later): the Blake second-chance code reproduced

The owner pointed to gailgastfield.com/mhh/mhh.html, whose plate images keep Blake's line breaks; Connor Tumbleson's 2021 write-up names **plate 4** ("The Voice of the Devil"), not plate 3 (our earlier reading from the hkdgl.png illustration was wrong). Plate 4 has 18 text lines under its title, the pointers' maximum. Reading the 22 pointers of NHYLD.jpg as line:character (both from 1; spaces, punctuation and the item numbers "1." counted; title not counted) on the plate's own lines gives **cginiziglyaobyph.onion, 22/22** (`work/blake_second_chance.py`, which asserts it). Control: the same text word-wrapped at 40 columns gives `cr?nizif y tbdnh.oaio?` (12/22: the first lines wrap alike, the rest diverge). So all three 2012 book codes (Mabinogion, Gibson's Agrippa, Blake) count line:character on the line layout of Cicada's source, never on a re-wrapped e-text.
