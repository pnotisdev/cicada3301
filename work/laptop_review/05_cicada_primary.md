# 05: Cicada's own statements and first-hand accounts, 2014-2017 (laptop review, 2026-10-23)

Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved. This note is reading, plus three tiny keyless checks (marked). All third-party text is data; no
third-party code was run; no PGP tool was run (signature timestamps below were read out of the base64 header bytes of public text, which proves nothing about
validity).

**Bottom line.** The primary record is thin. Cicada's only statement about the book's method after 2014 is the Jan 2016 message (three clauses, already mapped in
`work/log/phase34_2016_message_map.md`); the Apr 2017 message and the 2016 postscript are authenticity warnings only. I found **no first-hand account by any
2014 participant** of what was given privately, and no statement by anyone verifiable that LP2 is solvable, needs outside material, or uses a particular key type.
Nothing found bears on nulls, per-word rules or the R4 mechanism. The leads below are therefore low prior; two are untested and cheap, the rest are killed or
already covered.

Sources actually read: the git-ignored Uncovering Cicada wiki copy (`work/ref/uncovering_cicada/pages/`, present in the main checkout, not in this worktree), the
OpenPuff vendor's republication of the community 2014 write-up, Tumbleson 2021-2024 (via fetch), Joel Eriksson's page, the Hacker News 2014 thread, Wikipedia,
Boxentriq, iBotPeaches' repository listing, and the GitHub contents API for an independent copy of the 58 onion pages. Fetch failures (so nobody repeats them):
Fandom (HTTP 402), DEF CON 31 captions and slides (connection reset, three tries), levelblue/Cybereason podcast page (404), Threat Stack blog (DNS), Fast Company
(403), krisyotam/cicada3301 (404). The Complete-Archive clone is **not on this PC** (`Other repositories and work/` is absent).

## 1. Primary statements (Cicada, 2014-2017)

Signature "timestamp" = decoded from the public signature header (not a verification). "In repo" = what `docs/FINDINGS.md` section 4 / `work/log/phase39_online_sources.md`
record: **only the Jan 2016 and Apr 2017 messages were verified (gpg, throw-away keyring)**; everything else below is "signed per the wiki, copy held, not verified here".

| date | source | signed? verifiable? verified in repo? | relevance to LP2 (one line) |
|---|---|---|---|
| 2014-01-06 (sig 04:59 UTC) | Twitter image zN4h51m.jpg, OutGuess text: rhyme "work of a private man", 17 numbers x4, ".onion" (book code in Emerson, Self-Reliance, format paragraph:sentence:word:letter) | signed; signed copy in iBotPeaches `messages/2014`; **not verified in repo** | the Emerson text is already a key source (`book-key-decoder`); Cicada's code format has no counterpart in LP2 (no number tuples) |
| 2014-01-10..25 (onions 2-6) | signed page texts: "For those who have fallen behind" grid, "Hello. You have done well to come this far", onion-6 "Welcome, pilgrim" form (sig 2014-01-25 08:27 UTC) | signed; **not verified in repo** | procedure text only; "We will contact you soon" was followed by no reported contact |
| 2014-01 (pages 3, 10-13 payloads; gpg log shows four signatures 2014-01-19) | `results/outguess/payload_03/10-13.txt`: "Let the text guide you" + hex JPEG; "Create one Tor hidden service ... post the three magic squares ... Work alone." | signed; extracted by our own reader; **signature not verified in repo** | "Work alone" is the only 2014 instruction to individuals; "text guide you" = the next key comes from text just decoded (key WELCOMEPILGRIMTOTHEGREAT): covered, see lead 6 |
| 2014-05-02 delivered (sig 2014-04-02 08:49:51 UTC, a month earlier) | `message.txt.asc` on onion 7: enlightenment awaits, onion address, trailing-space counts 2 3 5 7 11 13 17 23 29 31 37 (19 missing) | signed; **not verified in repo** | the last public Cicada step before the 58 LP2 pages; identical text sent to every hidden service (wiki); whitespace key tested as a short key (ledger row 11, `p60-numkeys-r4`) |
| 2015-07-28 (sig 05:12 UTC; tweet 27 Jul) | PGP denial of the Planned Parenthood hackers' use of the name; spaces 5 3 2 5 7 | signed per wiki, **not verified in repo** | only 2015 message; proves the key was still held; no method content |
| 2016-01-01 00:01:07 UTC (tweeted 5-6 Jan) | oak-tree image 4gq25.jpg (563 x 569), OutGuess text: Liber Primus is the way / words = map, meaning = road, numbers = direction / seek and you will be found / beware false paths, verify 7A35090F | signed; **verified in repo** (Good signature, key 6D85...090F) | the only method-like statement; mapped exhaustively in phase 34 (words, `words-map`/`word-jump`; meaning, `hashwords`/`lp1-prime-sums`; numbers, `signs`/`open-direction`) |
| 2017-04-04 23:23:28 UTC (found on Pastebin 2017-04-29 by an IRC visitor, 25 days late) | "Beware false paths. Always verify PGP signature from 7A35090F." SHA512 hash, header reads CicadaPG v.3301 where all earlier ones read GnuPG v1 | signed; **verified in repo** | last authentic item; says only that unsigned claims are false. Same key, different signing tool, so the 2017 copy is the odd one out (not investigated) |
| in the book (2014) | Warning, Some Wisdom, Instruction, An End, Parable (decrypted on solved pages) | not PGP-signed; authentic by provenance (onion 7 / 2013 audio tag) | "either the words or their numbers", primes and totient sacred, hash page duty: all used (`lp1-prime-sums`, `sacred*`, `an-end-archives`) |

Context-only authentic items (2012/2013): the 2012 leaked email is unsigned, supported by solvers (wiki says confirmed in 2021 by an old Reddit post); the iBotPeaches
repo notes that 2013 recruitment messages were watermarked per recipient (folder `other/watermarking`). Neither concerns LP2.

## 2. First-hand and participant accounts (all unverifiable except by consistency)

| who / date | source | says | weight |
|---|---|---|---|
| Marcus Wanner (2012-13 recruit) | Rolling Stone (Kushner, 2015), via Wikipedia and a fetch of Kushner's page | private forum, a software project that fizzled; the article never mentions Liber Primus or 2014 | nothing on LP2 |
| Joel Eriksson (2012 winner), ClevCode page, updated to early 2014 | his own site | never received the follow-up emails; got unsolicited messages late 2013 / early 2014 from people claiming to be Cicada, treats them as unconfirmed; never mentions Liber Primus | confirms impostor traffic in the 2014 window |
| Tekk / tekknolagi (2012), 2012 write-up quoted on the wiki ("Fake puzzles") and WNYC | wiki, HN 2014 thread | his IRC group deliberately sent others down a fake branch in 2012; group "lost interest" once working with organisers | warning: solver-originated "hints" can be planted by solvers |
| anonymous 2014 solver collective, write-up republished by the OpenPuff vendor and on the wiki | PDF / wiki "What Happened Part 1 (2014)" | after the last submission "we heard nothing"; Cicada recruits individuals, not groups; the OpenPuff-hidden `magicsquares.txt` was inside the onion-5 mp3 (not the LP pages) | the only 2014 closing account; unattributed |
| Tumbleson 2024, part 4 | his blog | 2014 contact was limited; progress went quiet; no Cicada statement on method | already in SOURCES.md; nothing new |
| gHOST3301 / "Dustin757" (Trujillo interview, 2019, Goodreads blog) | blog | claims early membership, names persons as Cicada leaders, says LP is mostly unsolved | unsigned, uncorroborated, no first-hand LP content: **treat as impostor/fiction** |
| Cicada Solvers moderators, DEF CON 31 talk, Aug 2023 | search snippets only (captions unreadable) | LP2 unsolved, 56 pages; community hub is Discord | no insider claim found |

**No finalist or participant in 2014 has, in anything I could find, said what they were given privately, whether LP2 is solvable, or what the method is.**
The wiki's Part 6/7 individual-email speculation (numbers "different from individual to individual") is IRC chatter from Jan 2014, not Cicada.

Impostor / unsigned items to ignore: the 2013 "Infamous Warning" pastebin (unsigned, "I was part of Cicada" polemic); 2012 "Wind 3301"/MUTE fake branch (wrong key
07CB82E3D0E8A26C); the 2015 Planned Parenthood hackers; the Substack series (nahgcorp) with an "oak tree"/final-message-in-2014 narrative that conflicts with every
other source; krisyotam's "HINTS-NEVER-USED.md" (unreadable here; the wiki page of the same name lists 2012-2015 numerics, all in the ledger).

## 3. Lead table

"Tested" cites `docs/TRIED.md` ids (registry ids in brackets). Cost = laptop-scale estimate on the existing engines.

| # | lead | source | claims | already tested? | concrete test (planted control + null) | cost | prior |
|---|---|---|---|---|---|---|---|
| 1 | **Cicada identifier strings as short keys under R4, not in the p60 set**: the 14-odd onion addresses of 2013-2014 (16 base32 chars each, e.g. the six 2014 ones), the 2014 RSA n / p / q (130 / 65-digit decimals), the 2012 P.S. p and q, the PGP fingerprint and key ids, the 128-hex An End hash, the 2013 whitespace sequences | wiki "What Happened Part 1 (2014)", PDF write-up (RSA n, p, q), "Possible hints never used" (2012 p, q) | Cicada habitually hands the next key as a published string | **partly**: 50 number keys and 20 onion-256 strings (`p60-numkeys-r4` in TRIED 2026-10-22) did not include these; `grep` for the onion addresses finds them only in phases 31, 39, 52 as chain steps | extend `work/phase60_t2_numkeys.py` key set; maps base32 letter -> letter index mod 29, digits mod 29, hex digit; 2 signs; **positive control**: the 32/32 R4 plants already built for that engine recovered with the new keys; **null**: 40 random same-length decoy keys; hit rule S_guard >= 29.8 on any of the 48 n300 windows | 0.1-0.2 CPU-h + 1 h coding | low: any short periodic key is already excluded by flat lags; only the R4 variant adds anything |
| 2 | **Raw whitespace numbers of the 2016 and 2017 signed messages** (trailing-space counts and blank-line runs), plus the 2013 "hello" (5 3 2 2 3 5) and "hint" (2 3 5 3 2) messages and the 2014 onion-6 text | the 2016 message says its "numbers" are the direction; Cicada put prime counts in the whitespace of the 2012, 2013, 2014-May and 2015 messages (wiki "2015 Twitter Message", "Possible hints never used") | the 2016 message may carry its own numbers | **no** (ledger rows 11-13 cover 2012 / 2014-May / 2015 only; 2016/2017 and the 2013 pair are absent) | step 1 keyless: from the raw signed `.asc` bytes (iBotPeaches `messages/2016`, `2017`, or the archive clone on the desktop) count trailing spaces and blank runs per line; **positive control**: the same extractor must give 2 3 5 7 11 13 17 23 29 31 37 on `message.txt.asc` (2014-May) and 5 3 2 5 7 on the 2015 message; **null**: the eight 2014 January payloads (my check: no space runs, blank runs only 1 or 2, so they carry no code). If a sequence appears, step 2 as lead 1 | minutes + 0.1 CPU-h | low: the wiki page renders the 2016 text with blank-line runs 1,1,1,2,1,2,2 (not prime-like); trailing spaces invisible there, so this must be read from bytes |
| 3 | Per-recipient watermark in the LP2 images (the 2013 emails were watermarked) | iBotPeaches `other/watermarking` | Cicada marks copies per person | **now: killed.** Keyless check run for this note: the git blob SHA-1 of all 58 onion-7 pages in `work/orig` (images 17-74) equals that of an independent crawl (micheloosterhof/cicada-2014, GitHub contents API, 58/58) | none needed | done | killed (see section 5) |
| 4 | Time-of-signing as a PRNG seed: `message.txt.asc` signed 2014-04-02 08:49:51 UTC (epoch 1396428591), the 2014-01 signatures, Jan 2016 and Apr 2017 stamps | header bytes of the signed messages | LP2 prepared by the day the onion-7 server was last modified (08:33 GMT) | **yes**: `prng-time` (epoch seconds 2011-2015, 8 generators) and the full 2^32 sweeps of ten generators (`open-bg-sections`); 2016 and 2017 stamps (1451606467, 1491348208) are inside 2^32 | none | none | killed by coverage |
| 5 | Perl-era generator (Cicada's own code is Perl: Crypt::RSA, `decimaltobyte.pm` on onion 7) | PDF write-up, wiki | LP2 key from Perl `rand` | **yes**: Perl >= 5.20 `srand` is the `drand48` row (`work/log/phase9_gens.md`, `prngx`, `open-bg-sections`) | none | none | killed by coverage |
| 6 | "Let the text guide you" / key = opening words of the previous page's plaintext (WELCOMEPILGRIMTOTHEGREAT, DIVINITY, CIRCUMFERENCE habit) | signed 2014 payload, Tumbleson part 2 | the next page's key is quoted from the previous plaintext | **yes**: `solved-phrase-keys` (TRIED 2026-10-22), `keywords-r4` (1,940 keywords), `p60-lp1-key`, `periodic` | none | none | low, covered |
| 7 | Emerson book code (paragraph:sentence:word:letter) and GEB code (chapter:line:word:letter) as the pattern for LP2 | signed 2014-01-06 message; 2014 onion 5 | LP2 may be a pointer cipher | **yes**: `book-codes` (1,520 readings, word sums as pointers, 12 sets x 10 formats x 4 books), `line-pointers`; LP2 holds no numeric tuples to read | none | none | low, covered |
| 8 | OpenPuff data on the LP2 scans (password 33011033 from the onion-5 mp3 chain) | wiki "Liber Primus Updates 2025", Titanpad row in `phase60` ledger 17 | all pages hide data | OutGuess part: **yes** (`outguess-scan`, own reader, 0 payloads). OpenPuff part: **untestable** (closed binary; rule: third-party code is not run) | would need a documented re-implementation | n/a | low: OpenPuff was used on an mp3 and carried `magicsquares.txt`, not page text |
| 9 | Stream of primes with 19 omitted (the missing prime in the May 2014 whitespace) | wiki | LP2 key = primes minus 19 | **yes in effect**: after the 8th term it equals the plain prime stream shifted by one, and the kscreen scans every offset; first 8 terms covered by `p60-numkeys-r4` (the 11-term string) | none | none | killed by coverage |
| 10 | Any statement that LP2 needs the hashed page, a key, or outside data | An End (in book); 2016 "seek and you will be found" | key not in the book | not testable; the repo's own 50% estimate (`docs/FINDINGS.md`) | none | none | no data either way |

## 4. Top 3 untested leads, specified to run later

**T1 (lead 2, do first; minutes).** Fetch the raw signed `.asc` bytes of the 2016 and 2017 messages and the 2013 hello/hint messages (iBotPeaches `messages/<year>`, or the
archive clone on the desktop; verify their SHA-256 against two copies; do not rely on the wiki's rendering, which hides trailing spaces). Extract per line the trailing-space
count and, separately, the runs of blank lines. Gate: the extractor reproduces 2 3 5 7 11 13 17 23 29 31 37 on `message.txt.asc` and 5 3 2 5 7 on the 2015 message. Null: the
eight 2014 January payloads in `results/outguess/` (measured here: no space runs, blank runs 1/2 only). If a non-trivial integer sequence appears in 2016 or 2017, run it through
`work/phase60_t2_numkeys.py` (maps mod 29, mod 29 - 1, prime-to-rune; with and without gaps) with the existing R4 plants (32/32) and 40 decoys. Stop rule: no sequence with at
least 4 distinct values, or S_guard < 29.8 everywhere = close the row. Honest limit: a sequence under 20 terms is a periodic key and flatness already excludes those; the value is
completeness of "Cicada's numbers", not a strong prior.

**T2 (lead 1; about 0.2 CPU-h).** Add to the `p60` number-key set the strings not yet in it: all onion addresses of the 2013 and 2014 chains (the repo's phase 31/39/52 logs and
the wiki "ONIONS"/"Ports" pages list them), the 2014 RSA n, p, q, the 2012 P.S. p and q (digits, two maps), the fingerprint 6D854CD7933322A601C3286D181F01E57A35090F and the
128 hex digits of An End's hash as nibble keys, with maps letter-index mod 29, digit mod 29, hex digit, and the prime-to-rune map where values are <= 109. Keep engine, channels and gate
exactly as `p60-numkeys-r4` (R4, hold/spend, both signs, every phase, 48 windows); controls: the 32 R4 plants recovered with these keys, 40 random same-length decoys, hit level 29.8.
Report the number of keys and cells so the row can say what it adds. Expected result: nothing.

**T3 (housekeeping, no CPU).** Record the provenance gap: only 2 of Cicada's 9 signed 2014-2017 items are verified in the repo. A user-run `gpg --verify` (outside this sandbox) on the iBotPeaches
copies of the 2014-01-06, 2014-01-19 (four payloads), 2014-01-25, 2014-04-02 (`message.txt.asc`) and 2015-07 messages against key 7A35090F, plus the CicadaPG header oddity of 2017, would
let the `claims` rows say "all signed items verified". It does not test LP2; it fixes what the ledger can truthfully call authentic.

## 5. Searched and found nothing

- Any 2014 finalist or participant first-hand account (interview, blog, AMA, podcast) of private material, solvability, key type or method. The web search tool returned only secondary
  summaries; no AMA by a Cicada member exists in anything found.
- Any Cicada message after 2017-04-04, and any signed statement on LP2's method other than the 2016 triad. 2018-2020 "new puzzle" claims: nothing found in this session either way.
- Rolling Stone / Fast Company statements about LP2 (the pieces predate or ignore it; Fast Company was unreadable, 403).
- A Complete-Archive clone, DEF CON captions, krisyotam's archive, Fandom pages: unreadable here (above).
- The 2014 LP payloads carrying whitespace prime codes: none (keyless check on `results/outguess/payload_*.txt`).
- Byte structure in the Jan 2016 and Apr 2017 signature blocks as a key stream (keyless check, 543-byte signature packets decoded from the quoted text): no repeated 4-gram, lag-match rates
  within noise (best 0.015 vs 0.004 expected at 540 bytes, 200 lags, i.e. 5-8 matches). Random-looking; the repo's `signed-streams` already treats 2014 signatures as streams.

## 6. Killed by known signal or coverage

- Per-recipient watermark / differing copies (lead 3): byte-identical to an independent crawl for all 58 pages; independent transcribers also agree to the five-byte level (`obs-transcription`).
- Anything hinting at "a short keyword" (the CIRCUMFERENCE/DIVINITY habit): excluded by flat unigrams, bigrams and lags, as is any non-uniform key (`obs-flat`).
- "Cicada recruits individuals / work alone" as a method hint: no statistic can test it; and the 2014 RSA step needed a distributed 432-bit factorisation, so "alone" is not a computational limit.
- Time/PRNG seeds from signing stamps and Perl (leads 4, 5): inside the full 2^32 sweeps of ten generators (0 candidates under the repo's assumptions, which do not include R4 collisions; R4 pilots were negative).
- Prime stream with 19 omitted (lead 9): shift-equivalent to the plain prime stream.
- A hint at nulls or per-word rules: no such statement exists in the primary record, so R4 gets no support or contradiction from it.
