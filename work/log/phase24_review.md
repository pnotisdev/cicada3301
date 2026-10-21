# Phase 24 review: word-edge channels in chanscreen v2 (independent, read-only)

Reviewed 2026-10-20 night: `work/chanscreen/v2/backward_edge.rs`, `engine_edge.py`, `reference_edge.py`, `bitcheck_edge.py/.json`, `test_edge.py`,
`test_edge_scale.py`, `step4/plant_edge.py`, `step4/cost.py`, `results/chanscreen/edge_summary.txt`, `results/chanscreen/edge/` (192 plant records),
`work/tmp/edge_cost.log`, `work/tmp/plant_edge_run1.log`. Nothing edited; the only things run were the two tiny exact-reference tests (24 s, 1 core).
Nothing in LP2 is solved and no LP2 ciphertext was scored by this arc.

## Answers to the four questions
1. **Default behaviour bit-identical: yes, by construction and by test, with one provenance gap.** I normalised whitespace and diffed `backward_base`
   against the body of `backward()` in `backward.rs`: identical (similarity 1.0); the helpers `add`, `rune`, `cls`, `get`, `push`, `Edge`, `NEG` are identical too.
   `backward.rs` is unmodified (git: only the new files are untracked). `bitcheck_edge.json`: 580 stored calibration/held records, every bank stream x 5 channels
   (including uncapped `skip`) x both signs x q 0.81 and the frozen q: 86,400 calls, 34,473,600 offset cells, **0 byte mismatches**. Gap: the bitcheck records the
   SHA-256 of `backward.dll` and `backward.rs` (the base) but NOT of `backward_edge.dll`/`backward_edge.rs`, the code under test (dll 19:37, bitcheck 20:04, so it
   probably ran on the current dll, but nothing pins it). Re-running after any rebuild is needed to keep the claim.
2. **Dense reference agrees: yes, incl. null-at-edge and extra-advance-at-edge.** `test_edge.py` (re-run by me): 400 random tiny cases (Q 3-4, n <= 5, key <= 8, all four
   channels, kinds 0/1/2, q in {0, .6, .8, 1}, nu in {0, .4, 1}, forced doublets, 60% candidate density, so runs of candidates), 2,022 non-zero cells, worst |log error|
   1.8e-15, support (the -inf cells) matched exactly. Four wrong-reading mutants (null visible to the anti-repeat check, null consumes a key value, null restarts the LM,
   advance ignored) each disagree in 154-265 of 300 tiny cases, so the test can tell the readings apart. `test_edge_scale.py` (re-run): Q = 29, n 10-14, key 28-36, 24 trials,
   334 non-zero cells, worst error 1.4e-14, all channels, both kinds. The reference was written from the encryptors, not from the DP (`reference_edge.py` header), and I
   compared its hold/spend/skip5/coin branches with `step()` in `plant_edge.py`: they agree. Limits: the reference and the plants share one author and one reading of the
   channels; only 24 scale cases; no case with m < n.
3. **Plants and false positives (frozen threshold T300 = 29.8 nats, nu = plant rate 0.42): detected 192/192; matched nulls 0/144 above threshold.** `edge_summary.txt`: in every
   (kind, channel) cell 12/12 plants have the true +-3 cell above T300; median band score 139-190 nats. The base engine (no edge model) detects only hold (12/12 for nullf/nulli,
   2/12 for adv) and 0/12 for spend/skip5/coin, so the edge decoder is what finds those. Matched null (iid key, same words/events/channel, searched in the same
   stream): 144 plants, global winner mean -108.8, sd 28.6, min -184.2, max **-65.4**; 0/144 reach T300 (rule of three: false-positive rate per plant-window below 2.1%
   at 95%). See finding 1 for why this does not yet license a campaign negative.
4. **What could make a later LP2 campaign meaningless:** findings 1-5 below (none invalidates the code; they limit what a negative or a hit can mean).

## Findings, ranked by severity
1. **(High, for interpretation) Plants test one operating point, 100 nats above the threshold, and there is no edge-arc null scan.** All plants use the decoder's own generative
   model: nu = rho = 0.42 exactly, events at exactly the candidate positions, 300-rune window, key present in the library, LM trained on the same pools, scores of 130-190 nats
   against T300 = 29.8. So "detected 192/192" shows the code inverts its own model, not how weak a signal it finds. Unmeasured: nu mismatch (plant 0.2 or 0.6 against decoder 0.42),
   shorter windows (60-150 runes), only some words carrying events, a different null-rune distribution, a power ladder near T300. The plan's third gate ("a null scan") is missing:
   T300 is the base engine's frozen threshold (`step2/thresholds.json`), the 144 matched nulls give only 144 maxima over about 92,000 cells each (a campaign window is about 1.3e7
   key values x 8 passes), and the edge arc adds model freedom the base null does not describe. The gap (null max -65 vs T300 +30) makes a false hit unlikely, but a campaign
   NEGATIVE may only be quoted as "no edge-arc cell above 29.8 in n = 300 windows for rho = 0.42-type plants in library streams", not for the hypothesis class. Fix before the LP2 run:
   an E3-style null scan on the edge arc (matched iid ciphertext, 1e7+ cells) and a power ladder over (n, nu mismatch, event share).
2. **(Medium) Reporting artefact: "winner = true (+-3)" is 101/192 only because of periodic keyword streams.** 91 plants have a global winner other than the true cell (hold 1/12, spend
   2/12, coin 4-7/12 in several rows); I checked all 91: 85 are keyword (`kw:`) streams, every winner has the same sign and is within 2.3 nats of the true band (median 0.0), at offsets
   hundreds to thousands of runes away: exact periodic aliases of the same key sequence. The exceedance diagnostic "627,147 of 17.7M wrong-offset cells at t = 0" is the same
   effect. No false winner exists, but the column reads as a failure. An LP2 hit list must collapse key-sequence aliases (compare the key window at each hit offset) before counting
   hits or applying the whole-section verification; the summary should report "true cell within 3 nats of the global best" instead.
3. **(Medium, a trap for the campaign) The word-edge mask depends on how words are cut, and `lp_words()` in `plant_edge.py` cuts at page marks.** In LP2 sections 0.7-0.15, 32 of 55
   page marks sit inside a word (a rune on both sides), i.e. a word wraps across a page. Splitting there adds ~1% spurious edges to the plants' word lengths (harmless for plants) but
   would put false candidate positions into the LP2 mask if the campaign reuses `lp_words`. The repo convention (`CLAUDE.md`, phase 26) is that a word crossing a page stays one word.
   Build the LP2 mask from the master's word separators only, with line and page breaks transparent.
4. **(Medium) The edge model also explains data with no events, so a hit does not show that edges carry nulls.** `none` plants (no events; word-final candidates) are detected 48/48 by the edge
   decoder (median 170-190 nats), and the base engine does at least as well there (200-219). A hit in the edge arc must be read against the base engine on the same cell: only an edge
   score that clearly beats the base score for the same stream/offset/channel supports the keyless-insertion reading. Pre-register that comparison.
5. **(Low-medium) Provenance of the results.** (a) `bitcheck_edge.json` does not pin the edge sources/dll (finding under question 1). (b) `plant_edge.py` was last edited at 20:08; 18 of the 192
   result records are older than that edit, and `edge_quarantine/nulli_skip_english_05_transient_831.json` holds a record set aside for a "transient" (its numbers look normal: detected, 175.2
   nats). The records are mixed across code versions or at least their provenance is not stated; ask what changed at 20:08 and, if it touched plant generation or scoring, re-run those 18.
   (c) the summary lacks the SHA-256 of the dll and sources, which the earlier steps record.
6. **(Low) Scope limits to state in the write-up.** Uncapped `skip` is rejected for kinds 1/2 (plants for the `skip` channel are decoded with `skip5`, consistent with the encryptor's 5-redraw
   cap); the extra advance at line and page breaks listed in the registry row is NOT built (only word edges; positions i >= 1; a null or advance before the first rune of the window is not
   modelled); the three kinds (nullf, nulli, adv) triple the number of passes per window (24 instead of 8), which any family-wise threshold must count. Cost (`edge_cost.log`, m = 2000):
   null/adv at word edges 101/62 us per offset against 47 us for the base, so the edge scan is about 2.2x (null) + 1.3x (adv) the base per channel (rough total about 280 CPU-hours
   if the base four-channel n300 scan is 49 CPU-hours: nullf + nulli + adv); null at all positions (245 ms per offset) is not usable.
7. **(Info) Everything above concerns inference, not correctness of the arithmetic.** The engine agrees with an independent exact enumeration and with the base engine; the plants do what the
   header says (cand masks mark the final or first cipher position of every word and never reveal which words carry an event; I checked `make_plant` for nullf, nulli, adv and none).

## Verdict
The arc is exact on the cases tested and is unchanged in its default mode. Before an LP2 campaign: (1) null scan and power ladder for the edge arc, (2) alias collapse in the hit rule,
(3) a page-safe word mask, (4) the base-vs-edge comparison pre-registered, (5) re-pin the dll/sources. Level of the current evidence: 1 (engine gates pass; plant power measured at one
operating point only); nothing about LP2.
