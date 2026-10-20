# Phase 18: what the book asks, how it is built, and three new measurements (2026-10-19)

Scope: a fresh read of the whole book (75 page scans, the solved text, the ledger) asking what Cicada 3301 built and what it wants a solver to do. **Nothing in LP2 is solved.** Everything here is scouting unless a control is named;
choices made after looking are flagged. Scripts: `work/prime_sums.py`, `work/page_scan_audit.py`, `work/book_map.py` (figure `work/figures/book_map.png`); results in `results/analysis/prime_sums.txt` and `page_scan_audit.txt`.

## 1. What the book itself asks (primary text, `work/tests/expected_solved.txt`)

| Page | Says |
|---|---|
| 0.0 A Warning | Believe nothing from this book except what you know to be true. Test the knowledge. Find your truth. Experience your death. Do not edit or change this book or the message within, **either the words or their numbers**. For all is sacred. |
| 0.2 Some Wisdom | **The primes are sacred. The totient function is sacred.** All things should be encrypted. Know this: [the 1033 square]. |
| 0.6 An Instruction | Question all things. Discover truth inside yourself. Follow your truth. Impose nothing on others. Know this: [the 3301 square]. |
| 0.16 An End | Within the deep web there exists a page that hashes to [SHA-512]. **It is the duty of every pilgrim to seek out this page.** |
| 0.17 Parable | Like the instar tunneling to the surface, we must shed our own circumferences. Find the divinity within and emerge. |

Four of the five are about verification (know, test, numbers, hash); the only concrete task is the page.

## 2. How it is built

**The solved pages are a curriculum.** Every encrypted page uses a key that is named in plain text elsewhere in the book (`work/lp.py` KNOWN):

| Section | Text | Cipher | Where the key is stated |
|---|---|---|---|
| 0.0 | Warning | Atbash | none needed |
| 0.1 | Welcome | Vigenere DIVINITY, plaintext F passes through | DIVINITY: title and body of the plain page 0.4 |
| 0.2 | Some Wisdom | plain | says: primes, totient |
| 0.3 | Koan | Atbash + 3 | none |
| 0.4 | Loss of Divinity | plain | DIVINITY, CIRCUMFERENCE |
| 0.5 | Koan | Vigenere FIRFUMFERENFE (= CIRCUMFERENCE with C -> F), literal F | CIRCUMFERENCE (0.4, 0.5) |
| 0.6 | Instruction | plain | |
| 0.16 | An End | key p_n - 1 = totient of the n-th prime, literal F | 0.2: primes, totient |
| 0.17 | Parable | plain | |

LP2 (0.7-0.15) has **no plain page**: its hints can only be in the non-text elements (grids, the cuneiform numerals 17,13 / 55,1 = 1033 / 3301 in base 60, the 256-byte base-60 payload, the dot figures, the red numerals 1-5). The solved sections' doublet rate is 1.1-4.5% (1.8-3.1% on the four of 300 or more runes; the 90-rune pages have too few pairs) against LP2's 0.5-1.1% per section, so the anti-repeat rule is LP2's own, not Cicada's habit on every page (`prime_sums.py` section 3).

**Numbers as checksums (new, measured; `results/analysis/prime_sums.txt`).** The Gematria sum of a *sentence* of the solved plaintext is prime far more often than chance: **36 of 76 body clauses against 11.2 +- 3.1 expected (z 7.9)**, with a shuffle null per section and
ordinary English as an outside control (Emerson, Essays I, in GP runes: 12-14% of sentence sums prime, 47-52% odd). Per page: A Warning **9 of 9**, An Instruction 4 of 4, Parable 3 of 3, Some Wisdom 3 of 3. Clauses of at most 40 runes: 32 of 53 (60%); longer ones: 4 of 23 (17%, chance level);
the narrative Koans are at chance (3 of 20). Words, lines and the displayed ciphertext of the encrypted pages are at chance, so it is the *plaintext sentence* that carries it. A Warning's closing sentence is cut into three fragments ("DO NOT EDIT OR CHANGE THIS BOOK." / "OR THE MESSAGE CONTAINED WITHIN." / "EITHER THE WORDS OR THEIR NUMBERS."), each with a prime sum (911, 1051, 859): the awkward breaks look
chosen for it. LP2's ciphertext units show no enrichment (clauses 31 of 167 = 18.6% against 13.0%, z 2.2; words, lines, pages, paragraphs at chance), as expected for scrambled text.
Status: exploratory (the clause marks are the transcription's; the short/long split was made after looking, the pooled effect does not need it). A weak outside source (a Substack deep dive) asserts "each decoded line resolved to a prime sum" without method; no controlled number was found.
Reading: "their numbers" is a check on the plaintext, which makes a decryption verifiable in any language. LP2 has 45 clauses of 13-40 runes, the length where the solved pages are prime 60% of the time: about 27 would be prime in a correct decryption against about 6 by chance.

**Visual structure (`work/figures/book_map.png`).** Art changes exactly at section boundaries (title/chapter pages, tablets, women, a recurring reclining corpse on 14-16 and 39, three-bar crosses on 17-19, spirals, bare trees, mirrored insects, vines, the white ghost tree on 72).
The five-dot figure (one rigid shape, flipped on 40, rotated on 73) closes 0.8 (image 24), opens 0.12 (image 40) and sits under the hash (73); it cuts LP2 into three parts of 1,874 / 3,632 / 7,450 runes (ratio 1 : 1.94 : 3.98, probably chance).
Correction to `phase9_art.md`: the three-dot rows (images 50 and 56) separate two red-headed paragraphs inside 0.13 and 0.14; they are not section boundaries. The last page is a cicada made of 574 irregular stipple dots (no lattice, nothing to decode).

## 3. Scan audit (`results/analysis/page_scan_audit.txt`)

- The scans sort into four JPEG quantisation families (43 / 23 / 5 / 4). The five scans of the rare family (03, 08, 10, 11, 12) are among the pages the research note names as 2014 OutGuess carriers (13 is named too but sits with the title pages); none of the 66 scans of the two common families, which hold every LP2 page, has it (an inference about encoder history, not a proof).
- `10.jpg` is a four-in-one container (pages 10-13 end to end). `05.jpg` is [page][360-byte hex text][the page byte-reversed]; the text decodes to the page's own 25 magic-square cells (digits least significant first): rows, columns and diagonals sum to 1033. It restates the grid, no new key material.
- No scan hashes to the An End SHA-512. Control for the faint-mark scan: a planted level 252-254 mark is found at JPEG quality 85 and 95 (about 160,000 pixels), the 22 clean text pages show 0; off-white pixels elsewhere are soft shading in the art. Negative: no hidden faint marks in the text pages.

## 4. What Cicada may want (inference, labelled; subjective weights, not measurements)

1. **The page.** The only explicit duty is to find the hashed page. It is the book's verification oracle in the way sums are for sentences. Offline we cannot reach it (the 2014 hidden service pages are gone); what it contains (plaintext, key, commitment) is unknown.
2. **Understand the machine, then repeat it.** The curriculum shows hints in plain pages and escalating ciphers, and the plaintext is numerically constructed. For LP2 the hints moved to numbers; the numbers themselves (1033, 3301, pi(1033) = 6 x 29, pi(3301) = 16 x 29, base 60, 256 bytes) are all in the ledger as streams; what is missing is the *recipe*.
3. **The journey is the point** ("Liber Primus is the way", impose nothing on others): some of it may be unsolvable by design.
Rough split of my belief: solvable offline from the book alone about 30%, needs data never published (the page, a key) about 50%, not meant to be decrypted about 20%.

## 5. Ranked next steps

1. **Prime-sum check on every future hit** (free): a decrypted clause of 13-40 runes whose sum is not prime counts against it; proposed for `docs/CAMPAIGNS.md` (not edited, a decision rule).
2. **Clause-aligned library scan** (new coverage): every earlier screen assumes one key alignment per 300-rune window or a restart at a window start. A key that restarts or jumps at each '.' (the 167 clause marks) is blind spot for the IoC screen (windows of 60-250 runes have a heavy-tailed null) but not for the likelihood score of chanscreen v2 (expected +30 to +60 nats for 60-120 true runes against a threshold near +30; an estimate). Needs the chanscreen v2 contract adopted.
3. **The pending hold-key campaign** (82 section windows, about 49 CPU-hours extrapolated) stays the top compute item.
4. **Not worth more compute:** more seed lists or number-theory streams (the ledger), more image searches (this audit).

Curiosities, probably chance (post hoc): the 9-rune caption of the grid has Gematria sum 638 = 22 x 29 = pi(1033) + pi(3301); section 0.7's sum 36,781 is prime and 0.8's is 75 x 809 (809 is the centre of the 0.6 square).

| Doublet rate of adjacent runes | solved sections (0.0-0.6, 0.16, 0.17) | LP2 sections |
|---|---|---|
| per section | 1.1-4.5% (Welcome 3.1%, An End 2.4%; 1.8-3.1% on the four of 300+ runes) | 0.5-1.1% |
| mean clause length (runes) | 31 | 77 |
