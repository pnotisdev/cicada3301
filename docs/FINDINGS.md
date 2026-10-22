# Findings in one page

**Nothing in LP2 (Liber Primus sections 0.7-0.15, 12,956 runes) is solved.** This page is the short version of what the repository has established; every number links to the registry row (`docs/registry.toml`) and the log that hold the details, controls and caveats. Generated pages with every row: [STATUS.md](../STATUS.md), [results/INDEX.md](../results/INDEX.md).

## 1. What LP2 shows (the only positive signals)

| Signal | Measurement | Row |
|---|---|---|
| **Doublets are suppressed.** | 0.66% of adjacent pairs (86 of 12,947; 0.63% inside words) are equal against 3.45% for random text: about 81% of would-be repeats are prevented, equally for all 29 runes, inside words and across word gaps. Every other pair is flat (chi-square 786 against 760 +- 45). | `obs-doublets` |
| **A lag-6 relation inside words: c' = 24 - 2c (mod 29).** | 80 within-word pairs against 44.5 expected (z +5.3); zero excess across word gaps; P 0.005-0.013 after correcting for every relation searched; its rate (0.027 per pair) equals the rate of suppressed collisions. Not reported by any other source we found. | `obs-lag6` |
| **A lag-5 echo inside words, carried by the rune S.** | 11 S,S pairs against 2.3 expected; P < 0.002 after correcting for 29 runes x 7 lags; the sites do not look like English S____S words. Not reported elsewhere. | `obs-lag5`, `mech25` |
| **Word lengths are not English-like.** | Too few 2-rune words (15.5% against 20-27%, p about 1e-45); best simple fit: one extra rune in about 42% of words. No spelling convention, no other language and no Old or Middle English text fits. | `obs-wordlen`, `mech25` |
| **DJU BEI.** | The only repeated adjacent word pair in LP2 (chance about 1.6%); both copies word-aligned (0.26% under shuffles, community measurement); the second copy is the book's last two words. Under 812 affine maps it matches only itself. | `obs-flat`, `signal-interactions` |
| Everything else is flat. | Unigrams, bigrams and every lag beyond 1. Any key that is not close to uniform (English text, short keywords, book letters under the rune table) is excluded by this alone. | `obs-flat`, `book-running-key` |

The four structural signals point to an encryptor that knows where words begin and end and repairs collisions. One shared collision-repair rule reproduces the doublet deficit and both echoes at about their size (phase 25), but not the S carrier or the word lengths, and the cheap tests found no coupling between the signals (phase 38).

**Update 2026-10-22 (phases 54-59).** The lag-5 S echo does not survive correction for the 203 cuts searched (P 0.021, no position or neighbour signature; `s-echo-dissect`), so it is dropped. The lag-6 relation stands (z +5.3) with no fixed word slot or repair marker (`lag6-dissect`). A mechanism search over nine rules (`mechanism-search`, `work/log/phase57_mechanism.md`) found one description that fits all remaining constraints at once (500 replicates, P 0.64): **(a)** a would-be doublet is repaired with probability 0.81 by writing 24 - 2c(-6), the rune six back in the same word, transformed; **(b)** separately, one extra rune, never equal to its left neighbour, is inserted at a random position in about 45% of words. No single rule fits the word lengths; DJU BEI is produced by none. Under this mechanism the library streams (pilot), 1,940 solved-text keywords with Cicada's spellings (44/44 plants recovered) and phi(prime) are negative (`keywords-r4`), and DJU BEI is not a reused stretch of any library stream (`djubei-reuse`).

**A quick test for proposed ciphers:** a cipher that can make a doublet only on one plaintext rune r (e.g. c[i] = c[i-1] + a(p - r)) puts almost none across word gaps; LP2 has 23 of its 86 doublets across word gaps (22.3% of adjacent pairs cross a gap), as uniform placement predicts; the solved plaintext has no word-initial NG at all (`discord-cumulative`, `work/discord_cumulative_check.py`).

The solved pages also carry a check any future decryption can use: 36 of 76 of their sentence clauses have a prime Gematria sum (z 7.9) (`lp1-prime-sums`). **This is authored:** the ID3 tags of Cicada's own 2013 audio file (Cicada OS, a year before Liber Primus) carry the Parable's text and 1,595,277,641, exactly the product of its three prime clause sums (1259 x 1031 x 1229).

A second verifier: in the solved pages every one-rune word decrypts to A or I (27 of 27), against 2 in 29 by chance; LP2 has 83 one-rune words (`ai-oracle`). No hit any campaign kept comes near it.

## 2. What is excluded (with planted keys the tests recover, and random-key nulls)

- **Additive keys from number streams:** a 1,447-stream library (number theory, constants, Cicada numbers, hashes of Cicada strings) at every offset, x all 28 multipliers, backward, with ciphertext feedback, decimated; every linear recurrence of order <= 3 and polynomial of degree <= 3; number streams from the solved text, the magic squares, the signed 2014 payloads and Cicada's cited books; LP2's own word lengths and sums.
- **Seeded generators:** ten generators over all 2^32 seeds (boundary-free score), epoch-second and millisecond timestamps 2011-2015, per-page seeds, the step-domain cipher's seeds; partly: OEIS, 19 M passphrases, KDFs.
- **Cipher structures:** periodic keys to period about 400, autokeys, Vigenere, progressive / multiplicative / cumulative keys, small state machines, per-word keys, ciphertext feedback, the step-domain cipher, clocked pointers, sign rules from the words' numbers, keyless nulls and extra key steps at word edges, a whole-book repair-channel likelihood campaign (8.7e9 cells), ciphertext reversed per word / clause / line.
- **Restarts:** at every page, paragraph, line, sentence, word and clause mark; windows starting mid-page.
- **Books:** a book's letters as a running key under the rune table or any untuned letter table (17 texts, 6 languages); six cited books (Liber AL, Blake x2, Self-Reliance, the Mabinogion, Agrippa) under ANY letter table with a table-free decoder (stage 1, 0 hits; the KJV running).
- **Puzzle pieces:** cribs, the 256-byte payload (random bytes), OutGuess payloads in the LP2 scans (none), the page-30 caption, the 0.6 square's seeds, book-code pointer readings of the book's numbers.

What each negative does **not** exclude is listed per row; the common limits are: keys outside every list, windows other than the section starts, plaintexts that are not English-like, and a key whose source is not in the book at all.

## 3. Open

- Queued (detached, `docs/QUEUE.md`): the KJV as a table-free book key; key-pointer direction by the words' numbers ("their numbers are the direction"); the remaining page / line sign rules. Done since: the word-length pointer jump and four layout rules (negative).
- Built, not run: the word-edge campaign over all 82 windows (about 300 CPU-hours; one-window pilot null). A simulation (`insertion-doublets`) rejects edge-only insertion as the source of the word-length excess, so the campaign would need a mid-word variant.
- Not testable at LP2's size: two-tap echo rules, an evolving-alphabet walk, key reuse between sections.
- The page that hashes to An End's SHA-512 has never been found; the repository's own estimate is about 50% that LP2's key cannot be recovered from the book alone.

## 4. Facts settled along the way

- The transcription (rtkd/iddqd master plus our errata) is confirmed by an independent re-read; the payload's five corrected bytes agree with iddqd's own hex byte string (`payload`).
- The signed January 2016 and April 2017 messages verify against Cicada's key 7A35090F; neither contains a key.
- Cicada's book codes count line:character, spaces and blank lines included, on Cicada's own line-wrapped copy of the text: the 2012 Mabinogion code and the 2012 Agrippa code both reproduce that way (`book-codes`). Cicada's "Agrippa" is William Gibson's 1992 poem, not the 1651 occult text (screened too: 0 hits). The 2012 Blake "second chance" code also reproduces (22/22, plate 4 with its own line breaks).
- The 1.40 IoC rule is a screening threshold between the random-key maximum (about 1.37 at 1e10 decodes) and real plaintext (>= 1.45 on 300 runes); hits are decided by whole-section verification, which no candidate has ever passed.

Sources of every text and image: [SOURCES.md](SOURCES.md).
