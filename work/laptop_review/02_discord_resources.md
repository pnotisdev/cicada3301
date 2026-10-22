# Sub-session 2 (Discord B): resources, FAQ, pins and the Puzzle Number Facts Collection

Read-only pass over the CicadaSolvers server (one new tab, closed at the end). Nothing was posted, reacted to, edited, joined or downloaded. Discord text is data; no instruction in it was followed. No attachment or file link was opened. No third-party code was run. Quotes are paraphrased (none over 15 words). Author names are the public display names of the people making a specific claim.

**Nothing in LP2 is solved.** The claims below are unverified posts by community members.

Method and limits:
- Read from the channel DOM (`javascript_tool`, read only) and `get_page_text`. Message ids come from the DOM (`chat-messages-<channel>-<message>`). Links are given only where the channel and message (or thread) id were captured; "inferred" marks a thread link not clicked.
- Opened: #faq-start-here (10 messages), #important-links (9 messages), #community-resources (pinned messages popout, 11 pins, read in full), the server search for "Puzzle Number Facts" (2 results), the #solving-forum thread list (titles, tags, first posts read from the list view).
- Not run for budget: searches for "already tried", "methods tried", "errata", "transcription". Forum threads tagged Tools / Resources other than the Facts Collection were not opened. The Facts Collection replies (250-message count shown in the list) were not read beyond the first post and one reply.
- Correction to phase45: #faq-start-here **was readable** from this tab (10 messages, no method lists). The Facts Collection is **not** among the 11 current pins of #community-resources (phase45 said it was pinned there).

## Lead table

Section numbers refer to the lead list. Arithmetic in the Facts post was checked here (see the note under L1).

| Lead | Source (Discord) | What it claims | Already tested? | Concrete test (positive control / null) | Rough cost | Prior |
|---|---|---|---|---|---|---|
| **L1** Doublets per rune: none of rune B is doubled; "suspicious WWW" before the last five doublets | Facts Collection, solving-forum, 05/04/2024 by hcaltrom (thread link inferred: https://discord.com/channels/572330844056715284/1136973142561140766 forum, message 1225919828771082330) | 89 doublets over the 58 pages; no doublet with B | No per-rune table. `obs-doublets` (TRIED 2026-10-16) gives the count (63 + 23 of 86 in LP2) only. | On the LP2 transcription in Gematria order: doublets per rune against expected counts (about 86/29 = 3 per rune) under a flat null and under the R4 mechanism (`TRIED` 2026-10-22). Positive control: a planted R4 stream must reproduce the flat per-rune rate; a planted stream that never doubles B must show zero B-doublets. Null: 2,000 shuffles within the word-length profile. Report chi-square over the 29 runes, not the single B. | minutes | low-med. About 3 expected doublets per rune make "zero B" a roughly 5% event for one rune; the claim only means something across all 29 runes. A rune-specific rule would separate R4 (rune-blind repair) from letter-dependent rules, so the test is cheap and useful either way. |
| **L2** DJU BEI overlay: GP value of copy 1 minus GP value of copy 2, mod 29, spells TRUTH | OH (OP), thread "possible hint/s", 19/09/2026 16:46: https://discord.com/channels/572330844056715284/1549444826653659156 (thread id captured from DOM). tz18 asked about word breaks on 21/09 (no answer in thread). | Difference of the two DJU BEI copies in Gematria values gives TRUTH (image) | No. `djubei-reuse`, the isomorph and 812-affine rows do not use GP differences. | Copies at the repo positions (6555 and 12950, from Mike's post, 0-based index in `work/ref/lp_verified.txt` to be confirmed), six differences mod 29 in Gematria order, decoded with the 29-letter table, both sign conventions. Control: the same difference for every other six-rune pair at spacing 6395, and at random spacings; count pairs that decode to a 20k-list word. Positive control: plant TRUTH into one copy by inverting the difference; recover it. | seconds | low-med. A single six-rune output: with about 29^6 strings and 20k words, a chance hit somewhere in the control is likely, so only the exact spelling at these positions, against the control count, counts. |
| **L3** Repeat-distance table: runes until the next repeated pair (spreadsheet "Repeated Rune Data") | Facts Collection, sheet link (not opened): https://docs.google.com/spreadsheets/d/1-Tqf9SuLXv75YQfpAr7zIm7s1oF4ZWO_jqU-sg9PuN0 | Counts for 58 pages, pair and word distances | No row for distances between repeated pairs (`obs-flat` covers lags of single runes; phase 38 isomorphs cover DJU BEI only). | LP2 transcription: histogram of distances between repeated bigrams and trigrams; 2,000 shuffles within the word profile as null. Positive control: a planted period-13 Vigenere on a solved page must show excess at multiples of 13. | minutes | low. Standard repeat test; `obs-flat` already points to a null. Use as a cross-check of L1. |
| **L4** Shared-primer plaintext autokey, lags 9 to 29 | xodec, #math-and-cryptanalysis, 21/07/2026 22:17 and 22:21 (channel 787683923383156796; message ids not captured). Posted: lags 1-29, 128 best primers per lag, page-reset and continuous; real LP2 -4.611 and -4.616 vs -2.377 for solved text | Excludes a compact shared-primer plaintext autokey through lag 29 | Partly. Autokey row covers lag <= 8 only (`TRIED` 2026-10-17). | Plant c_i = p_i + p_(i-L) with one primer shared by all pages, L = 9..29, on a solved page; for each L the best of 128 primers by bigram likelihood on LP2 and on shuffled LP2 (21 lags, look-elsewhere). Positive control: planted L = 17 primer must rank first. | hours | low. The poster's own run is a negative with a control. Worth reproducing in our framework because the record does not cover lags 9-29. |
| **L5** Triangle (T161) doublets in three directions: horizontal 84, down-left 468, down-right 458, expected 445.01 | Primrose (OP), thread "LP2 as a Recursive T161 Triangle", root 21/06/2026 https://discord.com/channels/572330844056715284/1518040630927032390 (thread id captured); doublet follow-up 09/07/2026 inside the thread | Horizontal suppressed; diagonals not suppressed; LP1 cut shows the same | No. `obs-doublets` uses reading order only. | Count equal adjacent pairs on the triangle geometry; expected from 2,000 shuffles within the word profile (445.01 is not derived in the post). Positive control: a planted reading-order-only deficit (R4 stream) must show a horizontal deficit and no diagonal one. | minutes once the geometry is written down | low. The diagonal counts are at the random rate (see killed list); the only deficit is in reading order, which `obs-doublets` already reports. |
| **L6** Numerical matrices for sections 15-22 (GP values, prime digits, index mixes) | CC (OP), solving-forum, "Lp2 as a series of numerical grids with a focus on 15-22 v2.0", posted 22/10/2026 16:20 (thread id not captured); a stage-1 file is attached (not opened) | Sections are matrices; the reading is a traversal rule still to be found | Partly. Grid rows cover the page-30 grid, the 1033 and 3301 squares (`grids`) and 12 pointer sets (phase 31). The 15-22 matrix walks are not in TRIED. | A matrix reading of 15-22 (row-major, column-major, zig-zag) with each of the four encodings the post lists; score with the IoC 1.40 line and the prime-clause verifier. Positive control: solved page 1 laid into the same geometry must be recovered. Null: shuffled 15-22 and random matrices of the same shape. | hours | low. The post names no rule to test. |
| **L7** Pages 0-2 emirp chain: infinity sign to 8734, inverted to 7649, emirp ordinals, product 3,012,828,529, prime-sequence addition, "CRYING" header on page 15 | Zaveon Carlio (OP), solving-forum, "Pages 0-2 /15", 20/10/2026 14:13 (thread id not captured) | Ordinals of emirps give a key; the first step produces a word | No row for ordinal-chain keys. | Apply the chain as written to LP2 0-2 and page 15, with the step "0 for 7" fixed as posted. Null: the same map with 1,000 random seeds. Positive control: plant the chain's key on a solved page; it must be recovered. | minutes | low. The step "0 for 7" is chosen because it makes a word (the post says so), and one header reading is the only evidence. |

Carried from sub-session 1 without re-reading: the 729-matrix walk with a stop rule (`01_discord_methods.md`, L3). Still blocked on the rule text.

Note on the Facts Collection arithmetic (checked here, no measurement): the post's section character counts are 729, 119, 693, 319, 14, 1729, 9, 1894, 1021, 1433, 91, 1468, 121, 3008, 308, 85, 95. They sum to 13,136. The first 15 of them sum to 12,956, the repo's LP2 count, and the last two sum to 180. So 13,041 = 12,956 + 85 (the "LP2 through An End" figure of Primrose). This is an inference from section order, not checked against the transcription; the registry should not cite it until the boundaries are confirmed. The 85 and 106 differences noted in sub-session 1 may be the same fact.

## Links collected

Status column: "yes" means the host or repository is named in `docs/SOURCES.md`. "no" means not there.

| URL (host and path, query strings stripped) | Where posted | What it is | In SOURCES.md |
|---|---|---|---|
| dropbox.com/sh/lkta4q921vliyuw (shared folder) | #important-links, 26/01/2020 (msg 671062177108459531) | "Liber Primus Files" folder | no |
| github.com/cicada-solvers/iddqd | #important-links (same msg) | transcription and original files (a mirror of rtkd/iddqd) | partly: rtkd/iddqd is listed (section 1); the cicada-solvers copy is not |
| pastebin.com/vGMK330j | #important-links (same msg) | the 58 pages in runes with prime values | no |
| docs.google.com/spreadsheets/d/1QsoYQ-NkJcwEuyOgMrD6DkHU2AUktwsfnQGnTURf1bU | #important-links (same msg) | runes as numbers and letters in plaintext and ciphertext | no |
| colab.research.google.com/drive/1Hd9fNYXHTke3uEvHdi4XPmaM1W67Abdz | #important-links (same msg) | Colab notebook that solves the solved pages | no |
| uncovering-cicada wiki (fandom/wikia) | #important-links, 671062198352871455 | wiki | yes (uncovering-cicada.fandom.com; the wikia address is older) |
| youtube.com/c/noxpopuli and a 2019 documentary (youtube) | #important-links (same msg) | solution tutorials; documentary | no |
| cicada3301.boards.net | #important-links (same msg) | old forum | no |
| khanacademy.org cryptography; gamedetectives.net/academy | #important-links, 671062313800826881 | learning material | no |
| Google Drive folder of crypto PDFs | #important-links, 671062341747736618 | book collection | no |
| pastebin.com/u/SpiderPuck | #important-links, 671062395388690444 | 2020 voice-session recaps | no |
| opensource.taiiwo.dev | #important-links, 671062282993926164 | gematria web tools | no |
| isitcicada.meme.tips | #important-links (same msg) | PGP checker | no |
| cicada-solvers.github.io/joutguess-rebirth | #important-links (same msg) | OutGuess in JavaScript | no |
| ether8unny.shinyapps.io/cickada | #important-links (same msg) | rune frequency tool | no |
| github.com/mortlach/RuneDecrypterPrime | #important-links (same msg) | LP decrypter | no |
| github.com/Taiiwo/cicada | #important-links (same msg) | Python wrapper | no |
| github.com/tweqx/dwh-hashkit | #important-links (same msg) | multi 512-bit hasher | no |
| github.com/tweqx/3301-hash-alarm | #important-links (same msg); #community-resources pin 09/02/2021 | hash alarm source | no (named in work/log/research_2026-10-16.md, not in SOURCES) |
| cicada-solvers.github.io/GPPrimeView | #important-links (same msg) | GP prime viewer | no |
| github.com/cicada-solvers/The-Complete-Cicada3301-Archive | #community-resources, 20/10/2026 (CicadasKoan) | archive | yes (section 7) |
| github.com/tweqx/solving_cicada | #community-resources pin, 23/07/2023 | repository documenting failed solving attempts | no |
| pastebin.com/u/geomatria | #community-resources pin, 18/04/2022 | paste account (a 49 KB paste) | no |
| github.com/scream314/cicada3301 | #community-resources pin | repository (scream314's sexagesimal file is cited in registry `payload`) | no |
| github.com/micheloosterhof/cicada-2014 | #community-resources pin, 10/04/2021 | 2014 puzzle repository | no |
| imgur.com/ke78n | #community-resources pin, 2021 | image | no |
| 3301archive.com/2012-4chan-archives | #community-resources pin | 2012 4chan archive | no |
| addons.mozilla.org ... /3301-hash-alarm/ | #community-resources pin, 09/02/2021 | Firefox add-on | no |
| numbersaplenty.com/13136 and /676334 | Facts Collection (solving-forum), 05/04/2024 and reply 06/04/2024 | number property pages | no |
| docs.google.com/spreadsheets/d/1-Tqf9SuLXv75YQfpAr7zIm7s1oF4ZWO_jqU-sg9PuN0 | Facts Collection | "Repeated Rune Data" sheet (see L3) | no |
| Attachments, not opened: englishwordsgematria.txt (892 KB, pin 09/02/2021); sentences.csv (49 KB, pin 2022); a pinned Python snippet with LP data strings (pin 01/08/2023, third-party code, not run) | #community-resources pins | word list by gematria sum; a paragraph/sentence table of runes; a decoder | no |

FAQ (#faq-start-here): no external links; the FAQ entries point to threads (original files, who is 3301, the DWH, PGP, IRC). The threads were not opened.

## Methods others list as tried that are not in docs/TRIED.md

| Method (as claimed) | Who, where | In TRIED? |
|---|---|---|
| Plaintext autokey with a shared primer, lags 9-29 | xodec, #math-and-cryptanalysis, 21/07/2026 | no (TRIED: lag <= 8) |
| Affine triples C_i = a P_i + b C_(i-1) + g mod 29 (23,548 triples) on the 86 equal-rune transitions, with a synthetic control at rank 1 | xodec, 21/07/2026 22:12 | partly (`chain`: a c_(i-1) + p_i + k, best 1.07; `lag-feedback`: within words, d <= 8) |
| Page-allocation p-values for equal-rune transitions (page .293, previous rune .525, spacing .607) | xodec, 21/07/2026 | no |
| A_i = 15 C_(i-1) + 27 C_i mod 29 over 841 pairs on page 55 | NINH, 30/09/2026 | partly (feedback rows); killed below by look-elsewhere |
| phi(p) - 1 and k_i = phi(p_i) mod 29 keystreams | v.vp. (29/09/2026), NINH (30/09/2026) | partly (`totient walk`, 27 x 27 layout) |
| Hill keys from the book's three matrices, with transposes, inverses and phi variants | v.vp., An End thread (29/09/2026) | partly (Hill is in the repo per phase 22, 42, 44; no TRIED line) |
| 6 hashes x 3 chain modes x 4 reductions x 3 bases x 2 signs x 16 offsets (6,912 variants) scored by fraction of one-rune words | aloszaM, "Liber Primus - Bruteforcer", 01/08/2026 | partly (`hashwords`, `hashscan-kdf`; the variant grid and the one-rune score are not named) |
| Running key against a 30.2 M external list (text cut off) | v.vp., 29/09/2026 | no (list not named) |
| Pages 31-32 as 11 x 11 squares, GP row sums 563 and 569 | heck, 15/09 and 11/10/2026; OH, 16-17/09/2026 | no (TRIED has 27 x 27 only) |
| GP sums of rows of page 31 against an 11-rune LP2 null | OH / ThirdLateralEye, 10/10 and 14/10/2026 | no |
| Cuneiform base-60 navigation to 1033.jpg; "two areas" for base 60 | CicadasKoan, 17/10 and 08/10/2026 | partly (HANDOFF item 7, open) |
| Welcome Pilgrim hex string: 65532 removed, 57 appended, byte count prime (2,116,097) | Fib, #general-solving, 19/10/2026 | no (killed below on arithmetic) |
| Parable clause product 1,595,277,641 as an audio-metadata value and as a seed | Kuo, 08/10/2026; aloszaM, 01/08/2026 | no |
| DJU BEI copies 4 x 1597 apart | hcaltrom, 21/09/2026 | no |
| Doublet counts along the three triangle directions | Primrose, 09/07/2026 | no (L5) |
| Atbash and index shift 3 or 4 from spirals ("compass") | Louis, 19/10/2026 | yes, covered: `open-outer-alphabet` (Atbash plus 17 keyword alphabets, all below 1.40; affine sigma covered by the multipliers row) |

Errata claims seen: image 10, line 6 ("BELIEVE" read as a different rune run; Elleandria, #solved-pages, 05/09/2026) is already a PLAN correction (line numbering 5 vs 6 to check against the image). No new transcription errata were seen in these channels. FINDINGS section 4 was not read in this pass.

## Top 3 untested leads, specified to run later

1. **L2, DJU BEI GP-difference overlay.** Input: the two DJU BEI copies in `work/ref/lp_verified.txt` (six runes each; take the start indices from Mike's post and check them against the file). Transform: d_i = (GP(c1_i) - GP(c2_i)) mod 29, with GP in the Gematria Primus order (F=0 ... EA=28); also the reverse subtraction. Score: decode d through the 29-letter table; success = the spelling TRUTH at both sign conventions. Positive control: plant TRUTH into copy 2 (invert the difference), recover it. Null: every other six-rune pair at spacing 6395, and 10,000 random spacings; count dictionary words (20k list) per null pair. Report: the exact output for both conventions and the fraction of null pairs that decode to any word. Stop rule: if the true copies do not decode to TRUTH, record as negative under a new row.

2. **L1, per-rune doublet table.** Input: LP2 transcription (runes 0-12,955), counts of adjacent equal pairs per rune value. Expected count per rune: flat null (uniform runes) and R4 (`docs/registry.toml` mechanism; the repair removes the doublet with probability 0.81). Score: chi-square over 29 runes and the single rune B. Positive control: a planted R4 stream and a planted stream that never doubles B. Null: 2,000 shuffles within the word-length profile. Report: chi-square, p, and each rune's observed/expected counts. Stop rule: a rune-specific deficit under R4 is a finding only if it survives the 29-rune look-elsewhere.

3. **L4, shared-primer plaintext autokey, lags 9 to 29.** Input: LP2 under the Gematria map. Model: c_i = p_i + p_(i-L) mod 29 with one primer of length L shared by all pages; the primer is chosen per lag by bigram log-likelihood over 128 candidates (xodec's design). Positive control: a planted L = 17 primer on a solved page must rank first with the same code. Null: the same scan on shuffled LP2 and on random text; report the best (L, primer) and its rank among the 21 lags. Stop rule: record as negative under `autokey` (extend to lag 29) if no lag beats the null maximum.

## Searched and found nothing

- #faq-start-here (10 messages): no method list, no errata, no "already tried" list.
- #important-links (9 messages): resource lists only.
- Pinned messages of #community-resources (11 pins, 2020-2023): tools, a code snippet (not run), attachments. No tried-methods list. The Facts Collection is not among them.
- Server search "Puzzle Number Facts": two results, the Facts Collection and the T161 thread. No other Facts-type list found.
- Not searched (budget): "already tried", "methods tried", "errata", "transcription" as server-wide terms.

## Killed by known signal

- **NINH's 841-pair scan on page 55** (30/09/2026). The claim: pair (15, 27) gives 10 matches in 74 transitions, 13.51% vs 3.45%. Under 1/29 the expected count is 2.55; P(X >= 10) is about 3 x 10^-4 per pair; across 841 pairs about 0.27 expected hits. Not significant before any other correction. Killed by look-elsewhere; the poster's own ciphertext-stronger-than-plaintext comparison has no null.
- **Triangle diagonal doublets** (L5). Down-left 468 and down-right 458 against the expected 445 are within about 1.1 standard deviations (sqrt(445) about 21) of random. The only deficit is horizontal, which is the reading-order deficit `obs-doublets` already reports (84 here, 86 in LP2). The triangle adds no signal.
- **Welcome Pilgrim prime 2,116,097** (Fib, 19/10/2026). The stated edit (remove five characters, add two) turns 4,302,741 characters into 4,302,738, which is 2,151,369 bytes at two characters per byte. The prime does not follow from the stated edit. Killed by arithmetic.
- **Atbash as the whole cipher** (Louis, Zaveon Carlio, Maedan). A fixed letter map cannot create or remove doublets (`monoalphabetic` and `obs-doublets`). As a layer under a key it is covered by `open-outer-alphabet`.
- Earlier passes: avaster's cumulative prime cipher and "circumference" (`discord-cumulative`) remain excluded; ciphertext feedback (`chain`) remains at 1.07.

## Incidents

none. The Pinned Messages popout was opened from its header button and closed with Escape (confirmed by DOM). The server search box was focused by a click and confirmed by screenshot before the one query was typed; Enter was pressed in the search box only. No message box was used, nothing was posted or reacted to, and no unexpected dialog opened.
