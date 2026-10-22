# Laptop review 2026-10-23: what might we have missed about LP2?

**Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved.** This was a one-off research sweep on the `laptop`, run on
2026-10-22/23: ten sub-sessions (reading, web, the CicadaSolvers Discord read-only, and our own files), each writing
one file in `work/laptop_review/` (`00_brief.md` is the shared brief and its rules). No campaign, screen or queue was started;
the few keyless checks ran for seconds to about 2 CPU-minutes at below-normal priority, with scripts kept outside the
repository. Third-party text was read as data; no third-party code was run and no third-party file was copied in.
Nothing here edits `docs/registry.toml`, `PLAN.md`, `STATUS.md`, `README.md`, `docs/FINDINGS.md` or `docs/TRIED.md`:
the desktop's main session integrates these findings.

Files: `01_discord_methods.md` (Discord A), `02_discord_resources.md` (Discord B), `03_discord_signals.md` (Discord C),
`04_web_analyses.md`, `05_cicada_primary.md`, `06_hand_ciphers.md`, `07_signal_math.md`, `08_loose_ends.md`,
`09_images_hidden.md`, `10_an_end_page.md` (web + Discord D).

## (a) Merged lead table

Status: **new** = not in `docs/TRIED.md` / the registry; **tested** = already covered (row cited); **killed** = contradicts a
measured signal; **book** = bookkeeping, no new science. Prior: low / med / high. Each file has the full test spec.

### A1. Our own record and the R4 programme

| # | lead | source | status | cost | prior |
|---|---|---|---|---|---|
| 1 | **The R4 decoder never sees edge nulls.** The simulations that selected R4 draw the extra rune's slot from 0..L, edges included (`work/phase57_mechanism.py:77`, `work/mech25/insert47.py:6-7,106`); every R4 plant and the mid-word decoder use interior slots 1..L-1 only (`work/phase57_pilot.py:41`, `work/chanscreen/v2/step4/plant_mid.py:8,47`, `work/log/phase51_midword_channel.md:9`). About 41-49% of R4's fitted nulls sit at a word edge, so the 12/12, 44/44, 32/32, 24/24 plant recoveries, the library pilots and the queued `r4lib` all test the decoder against its own narrower model. Checked in the code by the orchestrator. | 08 lead 1 | new | 10-30 CPU-min | **high** (that power drops) |
| 2 | Which slot rule does LP2 prefer: 0..L (phase 47 B) or interior only (never simulated, although the decoder implements it)? | 08 lead 2 | new | 10-20 CPU-min keyless | med |
| 3 | **Word-length premise rests on Emerson-like baselines.** Against Cicada's own solved text spelled in letters, LP2's word lengths differ at chi2 25.8, df 11, p 0.007 (2-rune share 17.9% vs 15.5%, z -1.6), not p 7e-28 (`results/analysis/wordlen.txt` treats the 739-word histogram as exact). R4's second rule, nu 0.42 and the arc budgets rest on this. | 08 lead 3 (keyless check) | new | seconds | med-high |
| 4 | Only 8 of 81 excluded/partial registry rows state that they assume no unkeyed rune; FINDINGS section 2 lists the other 73 as excluded without that condition. Under R4 they are R4-free negatives. | 08 headline 2 | book (claim wording) | 0 | n/a |
| 5 | R4 x restarts (46 page starts, 82 clause starts) with ~60 Cicada-named streams; restart rows are all R4-free. | 08 lead 4 | new (after 1) | 2-5 CPU-h | low-med |
| 6 | Step-domain cipher (native no-repeat) x unkeyed nulls: R3 (q 1 + nulls) leaves 67.6/18.2 doublets vs LP2 63/23; step28 ran without nulls. | 08 lead 8 | new | engine days + 2-5 CPU-h | low-med |
| 7 | Drift-free H2 (tableau, no pointer skip) under the R3 reading. | 08 lead 9 | new | hours | low-med |
| 8 | Sign rule x mechanism crossings beyond the phase 50 pilot (1/3 of streams). | 08 lead 7 | partly tested (`phase50-block` pilot) | ~10 h | low-med |
| 9 | Clauses of 13-60 runes with a prime-sum score term. | 08 lead 10 | new | CPU-hours | low (see 13: clause marks may not be clause ends) |
| 10 | 1,447 vs 1,439 library streams: 8 streams may never have run in multipliers, chanscreen, arcs, keywords. | 08 lead 5 | book | <1 CPU-h | low |
| 11 | Night2 H5 (L 2..13) and layer2 slices have results but no registry/STATUS/TRIED row; STATUS "left" #7 and #9 and "No long runs are queued" are stale. | 08 lead 6 | book | 30 min | n/a |
| 12 | Image-dot segmentation recount (40 lines with an extra or missing dot at a line edge). | 08 lead 15 | new | seconds | low |

### A2. The signals themselves

| # | lead | source | status | cost | prior |
|---|---|---|---|---|---|
| 13 | **LP2's clause marks do not behave like plaintext clause ends.** Clause-final words: LP2 -0.26 runes vs the rest (z -1.4); solved pages +1.77 (z +7.3). Words per clause: cv 0.95 in LP2 (near geometric) vs 0.71 solved. If it holds, the prime-clause verifier and the 45-clause list are misaligned on LP2 (the A/I oracle is not affected). Community post reproduced on our transcription. | 03 S1 (Jast, general-solving, 05/10/2026, [link](https://discord.com/channels/572330844056715284/615334603049271322/1556770821866004582)) | new | minutes keyless | med |
| 14 | T relation at rune-lag 5 across exactly one word gap: 307 vs 254.2 (z +3.37), post-hoc P about 0.02 over 47 cells; T at in-word lag 9: 14 vs 7.0 (z +2.7). | 07 L1, L2 | new (weak) | seconds | low |
| 15 | Compute the whole T lag x gap grid on the existing R4/R3/R7 replicates (never computed), with a planted gap-crossing control. | 07 L3 | new | 0.5-1 CPU-h | low-med |
| 16 | The 80 T sites as a whole-section keyed verifier (lost plaintext rune at each repair). | 07 L4 | new | engine 1-2 days | low |
| 17 | Lag-6 relation is not a null-model artefact: exact tail P 6e-7 (x 6,496 = 0.004), within-word shuffle P 0.003, reverse direction at chance, constant 24 universal across sections. | 07 headline 3-4 | tested (confirms `obs-lag6`) | done | n/a |
| 18 | Doublets per rune (community: "no doublet with B"). FINDINGS already says the deficit is equal for all 29 runes; the source table was not located in the registry. | 02 L1 | probably tested; check `obs-doublets` | minutes | low |
| 19 | Solved sections 0.0-0.6 have 2.58% doublets (72/2,790) vs LP2 0.66%: the deficit is LP2-specific. | 04 L2 (keyless count) | new fact | done | n/a |
| 20 | Pages 54-55 audit: IM/MI 7 vs 0.73 in the last 308 runes is the maximum of 12,649 windows, but one pair of 406 picked after looking. One pre-registered audit would retire the 54-55 cluster. | 03 S8/T3 | new | minutes | low |
| 21 | Two 5-rune repeats end "6 runes before a quote mark": 1 of 4 sites with our 20-tick list. | 03 S2 | new | minutes | low |
| 22 | DJU BEI GP-difference overlay spells TRUTH (community). Proposed in phase 43, never run. | 02 L2 | new | seconds | low |
| 23 | Distances between repeated bigrams/trigrams (community spreadsheet). | 02 L3 | new | minutes | low |

### A3. Cipher families

| # | lead | source | status | cost | prior |
|---|---|---|---|---|---|
| 24 | Two- and three-tap ciphertext autokey (Gromark / VIC chain addition on the output): keyless residual chi-square over 51,744 two-tap forms. | 06 A | new (single tap: `lag-feedback`) | minutes | low |
| 25 | Sparse lagged-Fibonacci key streams, order 4-6, as library streams under R4 (`recurrences` gap "order >= 4; sparse taps"). | 06 B | new (campaign) | 15 CPU-min (r 4) to 290 CPU-h (r 6) | low |
| 26 | Wrap-around partners for the T repair at word positions < 6. | 06 C | new | seconds | low |
| 27 | Homophonic partition with a leak. | 04 L1 | new; no lag-6 mechanism | minutes | low |
| 28 | Alberti disk with a 31-cycle. | 01 L1 | **tested**: periodic keys to period ~400 (`periodic`, FINDINGS section 2) | - | - |
| 29 | Random-threshold skip ("if less than 78"). | 01 L2 | **tested** in substance: the coin channel (`chanscreen-step3`) and R4's q 0.81 | - | - |
| 30 | 729-matrix walk with a stop rule. | 01 L3 | new, blocked (rule text not copied); stop-at-word rules make hits by construction | days | low |
| 31 | Numerical matrices for sections 15-22; emirp ordinal chain for pages 0-2. | 02 L6, L7 | new; no rule to test | hours | low |
| 32 | No classical, machine or puzzle cipher gives all four signals (22 candidates). The look-back stopping at the word end while the anti-repeat check crosses gaps looks like a word-loop program, not a named hand cipher. | 06 | tested (survey) | done | n/a |

### A4. Cicada's own material, images, sources

| # | lead | source | status | cost | prior |
|---|---|---|---|---|---|
| 33 | Trailing-space / blank-line numbers in the raw 2016 and 2017 signed messages and the 2013 hello/hint pair (gate: reproduce 2 3 5 ... 37 on May 2014 `message.txt.asc`). | 05 T1 | new | minutes | low |
| 34 | Cicada identifier strings as keys under R4 (onion addresses, 2014 RSA n/p/q, 2012 P.S. p/q, PGP fingerprint, An End hash nibbles). | 05 T2 | new | ~0.2 CPU-h | low |
| 35 | Verify the 2014-2015 signed items (only 2 of 9 signed 2014-2017 items verified in the repo). | 05 T3 | book (owner runs gpg) | 0 | n/a |
| 36 | Per-recipient watermark in the LP2 images: all 58 onion-7 pages are byte-identical to an independent crawl. | 05 lead 3 | killed (measured) | done | - |
| 37 | Container groups: the 9 OutGuess carriers (libjpeg-style JFIF, rare tables, no ICC); pages 4-16 (400 dpi, no ICC); pages 17-74 (one byte-identical 2,590-byte sRGB ICC). The ICC starts exactly at LP2's first page. No EXIF/XMP/COM/DRI on any page. | 09 | new fact | done | n/a |
| 38 | DCT pairs-of-values density on all 75 pages: LP2 inside the LP1 range (weak negative; dense sequential LSB would show). Calibrated version at 1-5% payloads; double-quantisation test. | 09 L1-L3 | new (weak negative done) | minutes | low |
| 39 | 761.mp3 identity (keyless part of the OpenPuff claim). | 09 L4 | new | 0.1 h | low |
| 40 | Hugging Face `Fenixor/cicada-liber-primus-corpus` as a third transcription cross-check (43.7 kB; the fetch tool refused the raw file). | 04 L3 | new; needs the owner's OK to download | minutes | low |
| 41 | Section counts in the community Facts post: 12,956 = the first 15 sections; 13,041 = 12,956 + 85 (An End). Explains the 13,041 / 13,136 counts in posts. | 02 note | new fact (inference; confirm boundaries) | seconds | n/a |

### A4b. An End's page (session 10, web only; its Discord part was stopped by the owner's decision)

| # | lead | source | status | cost | prior |
|---|---|---|---|---|---|
| 42 | Hash functions not in phase 52: JH, Skein, Grøstl, BLAKE-512, CubeHash, MD6, LSH, pre-FIPS Keccak (the menu of the 2021 "3301 Hash Alarm" Firefox add-on), on the 1,913 held bodies and 1,826 local files. Positive control: a planted digest of a held body under each function. | 10 L1 | new | CPU-hours | low |
| 43 | Common Crawl CDX query for onion gateway hosts (onion.to, onion.cab, onion.city, onion.link, tor2web) and the 34 phase 52 hosts, 2013-2016; counts only, then byte-range WARC records under 50 MB in total. | 10 L2 | new | minutes | low |
| 44 | archive.today, one manual lookup per phase 52 host; record snapshot dates only; positive control: a Wayback-held onion.to page must match byte for byte. | 10 L3 | new | ~1 h by hand | low |
| 45 | Gateway-rewritten copies (onion.to, tor2web) cannot byte-match the origin page, so phase 52's Wayback set tests gateway bytes, not origin bytes; academic crawls (DUTA, Biryukov 2014, Owenson-Savage 2016, Moore-Rid 2016) hold text, descriptors or classes, not raw page bytes. | 10 datasets | caveat on `an-end-archives` | 0 | n/a |

### A5. Killed by a known signal

| lead | source | why |
|---|---|---|
| avaster's "circumference" / cumulative prime cipher | 01, 03 | doublets only on plaintext NG; LP2 has 23 of 86 across word gaps and the solved text has no word-initial NG (`discord-cumulative`) |
| ozon's in-word-only filler insertion (Playfair-style) | 03 S4 | gap doublets would stay at 3.45% (about 100); LP2 has 23 |
| tz18 / Garrodactyl ciphertext or cumulative autokey | 03 | doublets only where p = 0; also `step28`, `chain` |
| Collision-triggered key reset ("interruptor") | 03 S7 | short keys: periodic between resets, all lags flat (`periodic`); long keys: invisible, untestable |
| AZdecrypt-style homophonic / monoalphabetic solving | 03 S10 | 29 symbols cannot flatten English unigrams |
| Digraph / Playfair | 03, 04 L4, 06 L4 | bigrams flat; gap doublets would be 3.45%; Playfair predicts ~1.7% doublets; `keyless-batch` T2 |
| Atbash / Caesar layers | 01 | a fixed bijection cannot change doublets |
| **Shared-primer plaintext autokey, lags 9-29** (xodec, 02 L4) | 02, 08 G11 | c = p + p(-L) is a sum of two English-shaped streams: IoC 1.04-1.06 against LP2's 1.002 |
| Pervasive key recurrence k_j = -2 k_(j-6) + b (lagged Fibonacci, period-6 key, order-6 LFSR) | 07 | best rate gives 66 hits (LP2 80), and its other 28 residual cells would have chi2 89.9 +- 14.2; LP2 36.5 |
| LCG / affine-step keys making T | 07 | -2 is a non-residue mod 29; six affine steps give a square multiplier |
| T anchor/ring repairs at word positions 1-5 | 07 | z -1.6 to +2.1, planted control >= 2.5 |
| T161 triangle doublets | 02 L5 | diagonal counts at the random rate; only reading order is suppressed |
| Chaocipher, Solitaire | 06 | no doublet suppression (Solitaire repeats MORE often) |
| Scan-derived byte streams, base-10 digit streams as additive keys | 08 | non-flat key histograms break the flat unigrams |
| R5 (per-word null = T(c-6)) | 08 | 1.5x too many T hits in 7-rune words |
| Mokzy's "no plaintext" generator (partly) | 03 S5 | it cannot give 15.5% 2-rune words or the lag-6 excess; it does fit lead 13, so it stays as a hypothesis with nothing to decrypt |

## (b) Top 5 new leads (prior x cheapness)

1. **Edge-slot R4 plants (leads 1-2). Run this before any more R4 CPU, the queued `r4lib` included.**
   Plants: `make_r4` from `work/phase57_pilot.py` (hold and spend x Cicada / English plaintext x 3 seeds = 12 per mode, n 150 and 300, library key at a random offset, both signs, repair T(c-6) at q 0.81, null in 45% of multi-rune words, checked against the previous rune), in a new file, with a second mode that draws the slot from 0..L as in `phase57_mechanism.py:77`. Decoder: the unchanged mid arc, true stream only, every offset. Detected = true cell S_guard >= 29.8. **Positive control**: interior mode must give 12/12 (reproduces phase 57). **Null**: matched iid-key plants (max near -18 at n 150, -56 at n 300). **Decision**: under about 90% detection in the 0..L mode, the R4 negatives cover only the interior share; then build a union arc (null at any cipher position, weight nu/Lc), gate it as phase 51 did, and rerun the pilots. Same session: rerun `insert47.py` with interior-only slots to see which slot rule LP2 wants (doublet split 63/23, edge-pair share 0.48, doublet-word length 6.08). Cost 20-50 CPU-min.
2. **Rebuild the word-length baseline from Cicada's own text (lead 3).** Fit "+1 rune in a share q of multi-rune words" against the solved plaintext (739 words, letters and digraph runes), Emerson and Walden, with a parametric bootstrap that includes the baseline's sampling noise; settle the one-rune accounting (83 observed vs 87 under the multi-rune convention); split the 2-rune bin by function-word frequency. **Positive control**: pseudo-LP2 from the solved text with +1 at q 0.45 recovers q inside its CI. **Null**: pseudo-LP2 from Emerson with no insertion is rejected at the nominal rate; the solved text against itself gives uniform p. Seconds.
3. **Do LP2's clause marks sit at plaintext clause ends? (lead 13).** Statistics fixed in advance: D = mean clause-final word length minus the rest; the same for first and penultimate words; cv of words per clause; D by clause-length bin. **Positive control**: English (Emerson) in runes cut at its own sentence marks and passed through R4 must keep D at +1.2 to +1.8 and cv 0.6-0.8; LP1 with its dots moved to random gaps must fall to D about 0, cv about 1. **Null**: 2,000 shuffles of LP2's 168 marks over its word gaps; a Bernoulli placement fit to the clause-length histogram. If LP2 sits in the shuffle null and far below the R4-on-English control, record that LP2's dots are not plaintext clause ends; then the prime-clause verifier cannot use LP2's dots as clause units. Minutes.
4. **The full T grid under R4 (leads 14-15).** On the 500 existing R4 (and R3, R7) replicates of `work/phase57_mechanism.py`, compute T hits for rune-lag 1-12 x 0-4 word gaps and the max over 812 affine forms per lag. **Positive control**: R4 with a planted gap-crossing look-back of weight 0.26 must show the (lag 5, 1 gap) excess. **Null**: R4 as specified; report P of a non-lag-6 cell >= z 3.37 among the 46 others, and whether lags 3 and 9 are R4-typical. Sharpens the lag-7 and word-final side predictions that separate R3/R4/R7. 0.5-1 CPU-h.
5. **Two-tap ciphertext autokey residual scan (lead 24).** For every tap pair 1 <= s < r <= 12 and a, b in 1..28 (51,744 forms; the constant only rotates the histogram), chi-square of R_j = c_j - a c_(j-s) - b c_(j-r) mod 29, in-section and in-word scopes. **Positive control**: English runes enciphered with a random two-tap autokey, then R4's repair and nulls, must put the true (s, r, a, b) at the maximum far above the null. **Null**: max chi-square over 1,000 within-section shuffles. Minutes; regression check: the single-tap (1, 1) doublet cell must reappear.

Cheap runners-up (seconds each, low prior): the DJU BEI GP-difference overlay (lead 22), the 54-55 pre-registered audit (lead 20), wrap-around T partners (lead 26), the 2016/2017 whitespace numbers (lead 33).

**For the desktop's main session (bookkeeping, no CPU):** the number mismatches in `08_loose_ends.md` section 2 (lag-6 expected 44.5 vs 45.7 are two valid nulls, say which; lag-6 z +5.0 stale in STATUS and the registry; lag-5 P < 0.002 vs P 0.021 are different statistics; the phase 60 "one-rune excess" z +4.6 is an artefact; PLAN.md:759 still says 26 gap doublets; README/STATUS book-key and "no long runs queued" lines stale), the over-strong claims in section 3 there (README "fits every statistic" while DJU BEI is P <= 0.002 under R4; FINDINGS "no other language fits" rests on one Old and one Middle English text), lead 4 (R4-free wording) and lead 11 (missing rows).

## (c) Searched and found nothing

- **Discord** (CicadaSolvers, read-only): "partial", "IoC", "readable", "decrypted", "729 Matrix" (01); pins of #community-resources, #faq-start-here (readable now: 10 messages, no method lists), #important-links (02); "doublet", "doublets across word", "double letters", "lag 6" (2 hits, nothing), "anti-repeat", "word length", "two letter words", "djubei", "totient", "prime sums", "skip", "null runes", "insert", "Playfair", "autokey", "running key", "interrupter", "already tried" (no tried-methods list exists on the server), "errata" (none), "repeat doublet", "AZdecrypt" (03). Nobody else has reported a lag-6 or any affine lag relation; two community counts of the in-word/gap doublet split agree with ours (_Neophile_ 2025: 59/20; hcaltrom 2022).
- **Web**: arXiv, Zenodo, OSF, theses, Kaggle, two-rune word analyses (04); no first-hand 2014 finalist account of private material, solvability or method; the 2015 and April 2017 messages are authenticity warnings only (05); no web source for DCT statistics on LP pages (09).
- **Unreachable**: krisyotam archive (404), DEF CON captions, brainbound (403), the Uncovering Cicada talk page (402), Substack part 2 (404), pastebin (timeout), Fandom, Fast Company, the Threat Stack blog. The Complete Cicada3301 Archive clone is not on the laptop (it is on the desktop).
- **An End**: no hunt or dataset beyond phase 45's R2-17..R2-21 was found on the web; no 2014-2016 onion dataset with raw page bytes is publicly downloadable (10). Discord D was stopped by the owner before its results were read.
- **Not done (budget)**: Discord result pages beyond the first for every query; heck's announced forum post on "doublet collision skips" (20/10/2026, not yet posted); the full ozon thread; the 2re 729-matrix rules (image only).

## (d) Risky or odd events

- **No post, reply, reaction, DM, join or setting change happened in any Discord session.** Every query was typed only after a screenshot or zoom confirmed the top-right search box.
- The Discord renderer froze on screenshots twice (sessions 1 and 3, CDP timeouts). Session 1 stopped after 5 terms; session 3 typed nothing after the freeze. Its last read-only DOM check showed the search box focused. Both tabs were closed.
- In session 3 one query was concatenated with the previous one inside the search box (Ctrl+A did not select). It was caught by a zoom and fixed by a triple-click; it never left the search box.
- The owner stopped the Discord work during session 10 (Discord D). By then four searches had been typed in the search box; the "page 56" results were not read. One ordinary search-suggestion popout opened and closed; the tab was closed.
- Session 1 noted a screenshot in #general-solving (22/10/2026) whose poster it took to be the owner's account. It is not identified in any file.
- No instruction found in third-party text was followed; none was reported as an injection attempt.
- Session 4 asked for the owner's permission to download a 43.7 kB Hugging Face file (lead 40). It was not downloaded.
