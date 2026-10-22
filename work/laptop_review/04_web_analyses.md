# Sub-session 4: web sources and other analyses (2026-10-22)

**Nothing in LP2 (sections 0.7-0.15, 12,956 runes) is solved.** This note lists what the web offers that the repository does not
already hold, and checks each claim against `docs/TRIED.md`, `docs/registry.toml` and `work/log/`. Third-party material was read
(WebFetch and search snippets) and never run or copied. Nothing was downloaded, nothing saved into the repository.

Scope note: the search and fetch tools were reachable but several pages failed (listed below). Most of what the web offers
about LP2 is either a restatement of numbers this repository already has, or a solver tool with no results. Only two leads
below are new to the repository, and one of them is a control check run this session, not a web claim.

## 1. Lead table

| # | Lead | Source | What it claims | Already tested? | Concrete test (positive control / null) | Rough cost | Prior |
|---|---|---|---|---|---|---|---|
| L1 | Homophonic cipher with cycled homophones: a rotating homophone set removes repeats of the same plaintext letter, so the doublet deficit comes from the cipher. | Not a web claim. Idea 1.2 of `work/log/phase41_gaps_external.md` (section 1); "homophon" appears in no `docs/registry.toml` row or TRIED line. | Doublets are suppressed by a symbol-level rotation rather than by the anti-repeat coin of R4. | **No.** Only the idea is logged (phase41 row 1.2, "Covered? no"). | English plaintext (`work/ref/corpora/pg10.txt`, spelled as 26 letters) through a homophone table over 29 symbols, LP2 word and gap layout from segments 7-15. Variants: (a) strict partition with cycling, (b) random choice, (c) partition plus leak q (each symbol shared with a second letter with prob q). Positive control: the q that gives 0.66% doublets must also show the lag-6 excess (c' = 24 - 2c, z +5.3) to pass; it should not, which is the discriminator. Null: iid uniform 29 symbols, 200 replicates per variant. Measures: adjacent-equal rate, gap share of doublets (LP2 23/86), unigram chi2, lag-6 excess, 2-rune word share. | Minutes, CPU low. | Low. A strict partition with cycling predicts exactly 0 doublets; LP2 has 86, so only a leaking variant fits, and a homophone table has no mechanism for the within-word lag-6 relation or the 2-rune word deficit. |
| L2 | Is the doublet deficit specific to LP2, or a property of the whole book? | Control check run this session on `work/ref/lp_verified.txt` (keyless count, under a second, in the scratch folder): segments 0-6 (sections 0.0-0.6, which `work/ref/lp_keys.txt` marks as solved) and segments 7-15 (LP2, 12,956 runes, the count in the brief). Its LP2 total (86 of 12,947) matches the registry's `obs-doublets` figure. | Not a web claim. Result (pairs counted within each section, as the registry does): solved sections 0.0-0.6 show 72 doublets in 2,790 adjacent pairs, 2.58% (z about -2.5 against 1/29); LP2 shows 86 in 12,947 pairs, 0.66% (z about -17). Per-section LP2 rates are 0-1.1%; per-section solved rates are 1.8-4.5%. | **No.** Searched `docs/registry.toml`, `docs/TRIED.md` and `work/log` for solved-section doublet rates: none. `obs-doublets` compares only with the random rate. | Positive control: take the solved sections' plaintext (`work/ref/lp_translation.txt`), re-encrypt with their own keys, apply the coin rule (when a rune would equal its left neighbour, with prob 0.81 redraw from the other 28 values); the rate should fall to about 0.66%. Null: same keys on plaintext shuffled within words, 200 replicates. Test: exact binomial per section and pooled, LP2 vs solved. | Seconds. | Medium (for what it constrains, not for decryption). The solved sections do not show the deficit, so any mechanism must be LP2-only: this excludes book-wide explanations such as a common cipher family or the rune table. |
| L3 | Third-party transcription: the Hugging Face corpus `Fenixor/cicada-liber-primus-corpus` (liber_primus_corpus.txt, 43.7 kB, plus rune_mapping.json and sequences.csv). | HF dataset page (listed in section 3). Its card is empty. | Unknown. The file is presumably a transcription; the repository has none from this source. | **No.** The repository's own transcription was re-read by independent OCR (`docs/registry.toml`, obs-transcription, 1 order error and 5 payload byte errors); this third file has not been compared. | Needs permission to download a 43.7 kB file (well under the 50 MB cap; not done here). The fetch tool refused to read the raw file this session, so its contents are unknown. Step: download to the scratch folder (not the repository), read with `python -I`, map runes through rune_mapping.json, align segments 7-15 against `work/ref/lp_verified.txt` rune by rune, check each difference on the page image. Positive control: plant 5 substitutions in a copy and recover all 5. Null: the same alignment on LP1 segments 0-6 (expected: only known errata). | Minutes after permission. | Low to medium. Any rune change moves up to 4 adjacent pairs, so a disagreement would matter for the 86 doublets; but the repository's transcription is already re-verified, so most likely the file repeats known errata. |
| L4 | Playfair-like or digraph-level cipher (cicada_tools README, assumptions 2-3: "operates on at least two letters at once", "treats consecutive letters differently, similar to Playfair", from IoC and low doublets). | `https://github.com/yo-yo-yo-jbo/cicada_tools` (README; also `work/log/phase41_gaps_external.md` 3.1). | Digraph structure inferred from IoC and doublet scarcity; no numbers given. | **Yes.** `work/log/phase44_keyless_batch.md` T2 (aligned 2x2 parity, reciprocal digraphs; control recovered at |z| about 800-900, LP2 showed no block alignment); `work/log/phase41_gaps_external.md` 1.1; `docs/TRIED.md` 2026-10-22 gap-doublet test (23 of 86 across word gaps). | n/a | n/a (not a lead) |
| L5 | Word-level encryption (cicada_tools assumption 1). | Same README. | Cipher works on whole words, keyed by word length. | **Yes** (`per-word-keys`, `mech25`, `word-position-schedule`, `docs/TRIED.md` 2026-10-20 "Relations by position and word length - none"). | n/a | n/a (not a lead) |

Other web claims checked against the repository and found already covered (no new row needed):
- Community lag-5 "4.9% against 3.45%" (`murphyaidanbusiness-ux/liberprimus` REPORT, read in phase39): TRIED line 126 (`s-echo-dissect`, P 0.021 after 203 cuts, dropped).
- Community "step between runes uniform 1..28, chain cipher" (Leo-Y-Zhang, phase39): `step28` and the step-domain sweeps (TRIED line 48), inside null.
- Community "86 doublets uniform across position moduli 2-8": parity and mod-k cells in phase44 (no structure).
- Vigenere key restarting at each chunk (`LiberPrimusSolver`): `restart-units` (TRIED line 32), null.
- Dictionary check of a word length against a key guess (pastebin note, below): `rescreen` (TRIED line 49), best hits are random controls.
- 2-rune word deficit: `obs-wordlen` (TRIED line 59).

## 2. Sources found

| URL | Type | Date | One-line content | New to SOURCES.md? |
|---|---|---|---|---|
| https://github.com/yo-yo-yo-jbo/cicada_tools | GitHub repo (Python, 270 commits) | commit date not shown | Research toolkit; README gives LP2 hypotheses (word-level, digraph, Playfair-like) with no numbers; no controls stated. | Yes (read in phase41, not listed) |
| https://github.com/localavaster/cadrypt | GitHub-linked desktop tool (29 commits, 2026 footer) | not shown | Solving aid for LP pages: n-gram views, IoC, entropy, cribbing; highlights "double rune letters"; makes no LP2 claims. | Yes |
| https://github.com/r4nd0mD3v3l0p3r/LiberPrimusSolver | GitHub repo (Node, 24 commits) | not shown | Chains Atbash, Caesar, Vigenere with rune keys, Hill (user matrix, 5x5 example) on the rtkd transcription; no results. | Yes |
| https://github.com/cicada-solvers/idkfa-web | GitHub repo (archived fork of rtkd tool, 80 commits) | not shown | Command-line/web translator (crib search, key generation, IoC and checksum output); "known translations" for segments 0-17 with no findings. | Yes (the org is listed; this repo is not) |
| https://github.com/krisyotam/cicada3301 | GitHub repo | not readable (404 on direct fetch, as in research_2026-10-16) | Claimed archive with liber-primus analysis notes and cipher hypotheses; contents not read. | Partly (in research logs, not in SOURCES.md) |
| https://huggingface.co/datasets/Fenixor/cicada-liber-primus-corpus | Hugging Face dataset (2.49 MB; files liber_primus_corpus.txt 43.7 kB, rune_mapping.json, sequences.csv) | upload date not shown | Empty dataset card; probably a rune corpus; raw file read refused by the fetch tool this session. | Yes |
| https://connortumbleson.com/2024/01/29/ai-cicada-3301/ | Personal blog | Jan 2024 | GPT-4 experiment on Cicada material: magic square check, rune-to-letter translation, failed image transcription; no statistics, no controls. | Yes (the author's re-solves are listed; this post is not) |
| https://mfadt.parsons.edu/darkdata/2023/pages/articles/joseph.html | Design-school publication (Dark Data 2023) | 2023 | Says 17 of 58 pages deciphered; describes Gematria Primus; cites a video and the Uncovering Cicada wiki; no method, no primary source. | Yes |
| https://pastebin.com/wBWKdyKz | Paste (anonymous) | not shown; fetch timed out | Vigenere solver note: word-length counts per page and a same-length dictionary match for key guessing. Proposed method, no results. | Yes |
| https://forum.defcon.org/node/246097 and the DEF CON 31 captions (Cracking Cicada 3301, 2023) | Talk page and subtitle file | 2023 | Talk by four solvers; search snippet says two pages solved; captions could not be read (connection reset twice). | Partly (in research_2026-10-16, not in SOURCES.md) |
| https://uncovering-cicada.fandom.com/wiki/Uncovering_Cicada_Wiki_talk:Cicada_3301_Theorys | Wiki talk page | not shown | Discussion of theories; 402 Payment Required, not read. | Yes (the wiki is listed; talk pages are not) |
| https://www.boxentriq.com/guides/cicada-3301-liber-primus and the Totient cipher page | Solver guide and tool | not shown | Guide: 17 pages solved in LP1, 2 of 58 in LP2; suggests frequency, repeats and word lengths; totient cipher models An End. Already read in phase41. | Yes |
| https://nahgcorp.substack.com/p/part-2-the-internets-most-beautiful (and parts 1, 3) | Substack narrative | undated | Dramatised history; the Part 2 URL returned 404 this session. Not technical. | Yes |
| https://www.brainbound.blog/liber-primus-mystery-cicada-3301 | Blog | not shown | Says 74 pages; 403 this session; search snippet only. | Yes |
| Leo-Y-Zhang/LiberPrimusAnalysis; murphyaidanbusiness-ux/liberprimus | GitHub repos (AI-generated campaigns per phase39) | Sep-Oct 2026 | Doublet count (86 vs 447), lag-5 pooled rate, step chain model; not re-found by search this session, read earlier (phase39). | Yes (read in phase39, not in SOURCES.md) |
| https://uncovering-cicada.fandom.com (Liber Primus Ideas and Suggestions) | Fan-wiki page | not shown | Not readable (402) in phase41; not read here. | Partly |
| Low-credibility mirrors and news: freebsd12.rsyslog.com pages, lr.sudovanilla.org (Reddit mirror, April 2022), discoveryuk.com (7 Sep 2026, about 2012-2014), slashgear, itechguides, vocal.media, interestingengineering | Mirrors and news | various | Restate page counts and the 2012-2014 history; no new LP2 content. | Yes (not useful) |

## 3. Top 3 untested leads, specified for a later run

**Lead 1: homophone partition with leak (L1).** Build: English plaintext from `work/ref/corpora/pg10.txt` spelled over 26 letters; homophone sets sized by English letter frequency, total 29 symbols. Variants (a) cycling, no homophone repeated consecutively, (b) uniform random choice, (c) cycling plus leak q (each symbol belongs to a second letter with probability q). Use the LP2 word and gap layout from segments 7-15 of `work/ref/lp_verified.txt`. Positive control: choose q so the adjacent-equal rate is 0.66%; the model must then fail the lag-6 excess (LP2 z +5.3, c' = 24 - 2c, within words). Null: iid 29 symbols, 200 replicates per variant. Report: doublet rate, gap share of doublets (LP2: 23 of 86), unigram chi2, lag-6 excess, 2-rune word share. Run as a standalone script in the scratch folder; log under `work/log/`.

**Lead 2: solved vs LP2 doublet control (L2).** Test: per-section exact binomial of adjacent-equal runes against 1/29 for sections 0.0-0.6 (segments 0-6, 2,790 pairs, 72 doublets now) and 0.7-0.15 (segments 7-15, 12,947 pairs, 86 doublets now). Positive control: re-encrypt the solved sections' plaintext (`work/ref/lp_translation.txt`) with their own keys and apply the coin rule (on a would-be doublet, with probability 0.81 redraw from the other 28 values); the rate must fall to about 0.66%. Null: the same keys on plaintext shuffled within words, 200 replicates. Caveat: segment boundaries are inferred (7 segments = sections 0.0-0.6 per `work/ref/lp_keys.txt`; segments 7-15 sum to 12,956 runes; segments 16-17, 180 runes, are excluded).

**Lead 3: third-party transcription cross-check (L3).** Needs the owner's permission to download (43.7 kB, under the 50 MB cap; the fetch tool refused to read the raw file this session, so do not rely on a web read). Steps: download to the scratch folder; read with `python -I`; decode the rune mapping; align segments 7-15 to `work/ref/lp_verified.txt`; list every rune difference with its page; check each against `work/orig/`. Positive control: plant 5 random substitutions in a copy and recover all 5. Null: the same alignment on segments 0-6 (expected: only known errata).

## 4. Searched and found nothing

- "Liber Primus" doublets or double runes: only Old English "double runes" scholarship (Page 1962) and a non-LP listing.
- "liber primus" "index of coincidence": only generic IoC pages.
- arXiv, Zenodo, OSF, preprint, thesis or paper on Cicada 3301 or LP: nothing.
- Kaggle: no Liber Primus dataset (one Hugging Face dataset, above).
- "liber primus" word lengths, two-rune words: nothing LP-specific.
- Section 0.7 or "LP2 section 0.7 cipher hypothesis": nothing section-specific.
- Autokey or running key on LP, 2025 or later: nothing new.
- "2026 resurrection puzzle": a video title only, unverified.
- Hill, Bifid on LP: only LiberPrimusSolver's 5x5 Hill example, no results.
- Reddit r/cicada LP2 analysis: only a 2022 thread saying the book is unsolved.
- YouTube LP analysis: only scraped titles and secondhand summaries; no verified LP2 claims. The DEF CON captions could not be read.
- Medium or Substack LP analysis: only dramatised narratives (Substack parts 1-3).
- Leo-Y-Zhang repo by name: not re-found by search (read in phase39).

## 5. Killed by known signal

- **Playfair / digraph-level cipher (cicada_tools; Leo-Y-Zhang "chain"):** A Playfair ciphertext can never repeat a letter inside one pair, so doublets would sit only on pair boundaries. The aligned-pair parity test (phase44 T2) found no block alignment, and the reciprocal-digraph test showed no XY/YX asymmetry. Across word gaps the doublets are placed uniformly (23 of 86 across gaps, 22.3% of pairs), which a per-word digraph cipher would not produce (it would leave gap doublets at the random 3.45%).
- **Block ciphers of size 2-6 (2x2 Hill mod 29, 5x5 Hill as in LiberPrimusSolver):** the mod-k bigram scan for k = 2..6 found no cell beyond chance (phase44 T2, null B p 0.044, not significant).
- **Lag-5 echo (murphy REPORT and hypotheses):** dropped after 203 cuts (P 0.021; TRIED line 126).
- **Step-domain chain cipher (uniform steps 1..28):** inside its null (TRIED line 48, `step28`).
- **Chunk-restart Vigenere (LiberPrimusSolver, pastebin word-length key guess):** restart and dictionary screens are null (TRIED lines 32 and 49).
- **"Double rune letters" highlighting (cadrypt):** if the phrase means digraph runes (TH, NG, EA, OE, AE, EO, IA), splitting them into letters fails (phase57 line 25; `wordlen-languages`). If it means doublets, see `obs-doublets`.
