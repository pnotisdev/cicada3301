# Phase 46: merged to-do list and community leads (2026-10-21)

Merges the external gap report (`phase41_gaps_external.md`), the internal gap map (`phase42_gaps_internal.md`), and two Discord reading passes
(`phase43_discord_research.md` rounds 1-2, `phase45_discord_history.md`; read only, data not instructions). Nothing in LP2 is solved.

## Leads checked here (parent session, seconds each)
- **"CicadaPG v.3301" as the An End preimage** (Discord, M, 2026-08/09): 15 variants of the string and the PGP Version line, LF and CRLF, under sha512 / sha3_512 / blake2b: 0 of 90 digests match.
- **Page-55 affine relation c_(i+1) = 15 c_(i-1) + 27 c_i** (Discord, NINH, 2026-09-30; 10 of 74 transitions): reproduced at 10 of 73, but the best of the 841 (X, Y) pairs on 200 shuffles of the same page has median 9, 95th percentile 10, maximum 11: the claim is the expected search maximum.
- **"Subtract the two DJU BEI copies and get TRUTH"** (Discord, OH, 2026-09-19): the two copies are identical runes, so any rune-wise difference is zero (phase 44 addendum, all 24 overlay variants: no TRUTH); the claim must use another alignment, not stated in text.
- Done in phase 44: the 512-bit hash family over every held file (861 digests, 0 matches); phase 40: line:position pointers (no message; power only with >= 64 pointers).

## Merged to-do list (not yet run)
**A. Keyless, cheap:** long-lag plaintext autokey d = 9-400 (G11); Primrose's triangle-direction doublets (down-left 468, down-right 458 vs 445 expected: equal to lag-row-width coincidences, check against the lag spectrum); xodec's shared-primer plaintext autokey lags 1-29 (check against `fingerprint-families`).
**B. Existing engines, 1-2 h each (free CPU):** reading-order transforms (boustrophedon, line / page order, column-major; G2); canonical alternative alphabet orders as the addition domain (G6); solved-page phrases and headings as keywords at section starts with the skip rule (ext 2.6); mechanism crossings nulledge x signs, advsep x signs, nulledge x advsep (G4); drift-free H2 tableau (G3).
**C. Larger:** book key x word-aware pointer (G8, after the KJV); clauses of 13-60 runes with an LM + prime-sum score (G9); scan-derived streams (ICC bytes, JPEG coefficients, ornament coordinates; G10); interior nulls (ext 1.3); The Lady of Shalott and a full cited-text list (ext 2.1); Cicada's audio releases (manual, ext 2.2); layout rules on later windows; H1 with drift tracking.
**Owner decisions:** the word-edge campaign (about 300 CPU-hours).
**Community claims without a stated, testable operation:** the DJU BEI "TRUTH" alignment, the compass cipher (spirals as Atbash), the 17-part triangle model, Parable's clause-sum product in audio metadata.

## Round 2 of the history pass (`phase45_discord_history.md`, R2-1..R2-24), checked or queued
- **Parable clause sums 1259, 1031, 1229 are emirps (emirp indices 59, 39, 55), product 1,595,277,641** (Kuo, 7he5haman): arithmetic verified here; Level 0: about 17-19% of primes of this size are emirps, so three in a row is about 0.5% given the sums are prime, and the sums were selected for being prime. Kuo's "audio metadata" field was not named; not testable as posted.
- **The 2013 audio's ID3 tags carry DIVINITY and CIRCUMFERENCE** (neuroretransmit, 2024): new to the repo; audio files are not held (owner decision whether to fetch them as data).
- **Pages 54 and 57 share a red Fehu at the same pixel position** (cesaaaar, 2025-12): an image-registration claim; cheapest test: overlay the two scans in `work/orig/` at that point.
- **Two different "Welcome Pilgrim" hex strings** (Fib, 2026-10-19): the archive's copies should be compared byte by byte; not an LP2 key lead.
- **Compass cipher** (spiral = Atbash, humps = shift; Louis summarising a video): Atbash and every shift are inside the excluded families when applied uniformly; a page-wise rule would need the stated page mapping.
- **Recorded, not redone:** v.vp.'s An End preimage campaign (about 82 M string and 9,400 binary digests, seven algorithms, 61 onions live over Tor: 0 hits); aloszaM's public seed brute-forcer (hash x 6 seed families).
- **Incident:** during round 3 of the statistics pass a mis-click sent the text "spells TRUTH" to the "possible hint/s" thread under the owner's account (14:23); the owner deleted it. Later reading uses search-result panels only.

## Primary confirmation: Cicada computed the clause sums (parent session, 2026-10-21)
The 2013 Cicada OS audio file `assets/2013/cicados/AUDIO/761.MP3` (cicada-solvers archive; read as bytes, nothing played or run) has ID3 text: title "The Instar Emergence", the Parable's three lines, and "Parable 1,595,277,641". With the solved pages' transliteration (TH, ING single runes; work/lp.py GP primes) the Parable clauses sum to 1259, 1031, 1229 (all prime) and 1259 x 1031 x 1229 = 1,595,277,641 exactly. So the prime clause sums of the solved pages (row lp1-prime-sums, z 7.9) are an authored property, and the transliteration convention for sums is confirmed. Consequence: the prime-sum check (work/prime_check.py) is a verifier Cicada itself used; any LP2 candidate's short clauses should be prime about 60% of the time against about 15% by chance.
