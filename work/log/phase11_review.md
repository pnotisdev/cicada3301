# Phase 11: outside-in review of the methodology, ranked next tests, and what to stop (2026-10-18)

Scope: LP2 sections 0.7-0.15, 12,956 runes. **Nothing in LP2 is solved.** This is the deliverable of an independent
review pass (A: audit, B: at most five hypotheses with controls and costs, C: stop-doing), plus the new controlled
results produced this round (four subagents + parent checks; outputs in `work/tmp/`). Every number below is cited
file:line; "unknown" is written where something is not measured.

## New results recorded this round (details at the end)

1. **The affine lag-feedback autokey family is excluded.** `c_i = p_i + a*c_(i-d) + b` within words, d = 1..8, all
   28 x 29 (a, b), four separator scopes, plus nonlinear maps at lag 6: no setting makes the residual plaintext
   (`work/tmp/lag_feedback_scope_extension.txt:7-9`, plant power chi2/n 2.25 vs LP2's 0.05,
   `work/tmp/lag_feedback_plant.txt:4-7`).
2. **Two more lag-6 echo mechanisms are dead.** Plaintext-F replacement: English F at word positions >= 6 is 0.0056
   (n = 1,013,590, sd 0.0001, `work/tmp/frate_pos6.txt`) against the echo rate 0.0272 +/- 0.0047 -- excluded at > 4 sd.
   Collision twist W3(a) (twist the previous rune): predicts c_(i-1) = c_(i-6) at every echo site; observed 3/80 vs
   null 2.8 (`work/tmp/w3_sharp_test.txt`).
3. **The echo rate equals the avoided-collision rate but does not track it by section.** Echo excess rate
   0.0272 +/- 0.0047 (`results/analysis/echo_position.txt:21-23`); avoided collisions 0.0269-0.0282 (86 doublets at
   0.63% with q = 0.81 enforcement, `docs/registry.toml:606-613`); per-section correlation -0.38, n = 9
   (`work/tmp/echo_vs_skip_rate.txt`). The coincidence stays an open observation, not a mechanism.
4. **The keyword-mixed outer alphabet (c = sigma(p + k)) is now built and controlled**: planted sigma recovered at
   IoC 1.6702 after relabelling against 1.0068-1.0637 unrelabelled, null <= 1.052, wrong sigma <= 1.055
   (`work/kscreen/RELABEL.md:88-108`). Ready to run; it was the one family no screen covered.

---

# A. AUDIT: the five assumptions most likely to be wrong

Each with the repo evidence that it could be wrong and the cheapest test that would show it. Condensed from the full
audit in `work/tmp/methodology_audit.md` (all its citations repo-relative).

1. **Word separators = plaintext word boundaries.** Baked into the dictionary scorer
   (`work/phpmt/src/main.rs:400-403,469-475`), `lp.word_spans` (`work/lp.py:156-173`) and dsearch
   (`work/walk/src/dsearch.rs:1-5`). Evidence it is wrong: the lag-1 correlation of adjacent word lengths is -0.008
   against -0.149 +/- 0.033 for English (4 sd; `work/log/phase9_families.md:15-17`); a planted key scores 33 with its
   own word cuts and 0 with LP2's (`docs/NEGATIVE_SPACE.md:14-16`); the histogram rejects English at p about 1e-45
   (`docs/registry.toml:633-637`). Cheapest test: free -- per-section word-length correlation against the committed
   English reference; if every section sits > 2 sd from -0.149, every dictionary-scored negative is void and only
   the boundary-free lanes speak.
2. **Anti-repeat = skip/coin, exactly one key value per rune, forward-only pointer.** Baked into every decoder
   (`work/kscreen/src/main.rs:9-13`; `work/phpmt/src/main.rs:440-464`; `work/lp.py:207-216`). Evidence it is wrong:
   the repo's own blind spot 9 and review gaps 2-3 (`docs/NEGATIVE_SPACE.md:27`, `work/log/phase10_review.md:14-17`);
   the only word-length model not rejected is "+1 rune in about 42% of multi-rune words" (p 0.085,
   `docs/registry.toml:637`); and this round's finding 3 (echo rate = collision rate). Cheapest test: minutes --
   plant Emerson with a known key, add one keyless rune at 42% of word ends, decode with the aligned forward pointer;
   if the insertion plant scores < 1.40 in >= 95% of 100 replicates while the no-insertion plant scores >= 1.57
   (`results/analysis/assumption_checks.txt:14-15`), the 56 negatives say nothing about this family.
3. **The key is a stream indexed by global position.** The beam state is the pointer only
   (`work/kscreen/src/main.rs:14-15`). Evidence it is wrong: both echoes are strictly word-internal
   (`results/analysis/echo_position.txt:3-9,22-27`) and the S concentration needs a fixed element
   (`work/log/phase9_families.md:60-62`). Cheapest test: free -- the committed plants spread a position-independent
   echo across boundaries (+162.1 / +321.5) where LP2 has +0.8 / +1.1 (`results/analysis/echo_position.txt:34-37`);
   a global-position mechanism cannot confine an echo to words, so this assumption is falsified for LP2's mechanism
   and any decoder must carry word-aware state.
4. **The cipher is additive mod 29 in GP-order indices (c = D(p) + m*k + b).** The engine's header
   (`work/kscreen/src/main.rs:3-7`). Evidence it is wrong: the lag-6 relation is multiplicative
   (c' = 24 - 2c, 24 = 3301 mod 29; `docs/registry.toml:624-630,68-70`); W3 is not excluded
   (`work/log/phase10_skeleton5.md:24-26`); a two-layer cipher scores IoC 1.1-1.2 and is blind
   (`docs/NEGATIVE_SPACE.md:23`). Cheapest test: minutes -- plant c = pi^-1(pi(p) + k) with 5 random permutations and
   a non-constant library key; if all pi-plants stay < 1.40 while the identity plant recovers >= 1.6, the additive
   coverage claim is falsified for non-affine arithmetic (with a constant key it collapses into the covered D).
5. **300-rune windows at section/page/heading starts.** `work/kscreen/export.py:41-51,62-88`. Evidence it is wrong:
   planted recovery 45/45 at 250-300 runes but 13/21 at 0-149 (`docs/NEGATIVE_SPACE.md:18-19`); mid-page starts are
   untested (priority 11, `docs/registry.toml:759-767`). Cheapest test: minutes -- about 12 staggered 300-rune
   windows x the 1,447-stream library is about 2.8 M decodes on the built `kscreen` (about 1-2 min), with a planted
   staggered control (>= 1.6) and the rand:300 null (<= 1.37); the ordinary CAMPAIGNS rule then decides.

Deprioritized: the scoring/outer-alphabet assumption (E) -- a real blind spot, but now built and controlled
(finding 4), and GP rotations are exactly the covered shift b. Section-independence (G) is covered by the exhaustive
per-section offset sweeps, and key reuse is proven untestable (power 0.05-0.42, `docs/registry.toml:510-517`).

---

# B. HYPOTHESES, ranked by probability x information / cost (at most five)

Decision rule and verification for every screen hit: IoC >= 1.40 on the first 300 runes, then whole-window
re-decode beating 20 random offsets by 0.15, then whole-section verification with a positive and a null control
(`docs/CAMPAIGNS.md:97-107,128-133`). Nothing below is a long run; each control runs in minutes.

## H1 (rank 1): keyword-mixed OUTER alphabet -- c_i = sigma(p_i + m*k_j + b) mod 29

1. **Model.** The ciphertext is relabelled by a permutation sigma before it reaches the page; inside there is an
   ordinary additive key with the skip/coin anti-repeat rule. sigma is derived from a keyword (Vigenere-tableau
   convention, see `work/kscreen/RELABEL.md:36-46`), is Atbash, or is affine sigma(x) = a*x + b (the 29 reflections
   and 26 proper multipliers). In-book precedent: the A Warning page is Atbash over the GP.
2. **Fingerprint.** IoC is invariant under sigma, so every screen saw flat text -- this family explains the total
   absence of candidates without touching any observation. It does NOT explain the doublet deficit, the echoes or the
   word lengths by itself (the inner program still needs the anti-repeat rule and whatever makes the echoes).
3. **Registry rows.** `open-outer-alphabet` (`docs/registry.toml:652-662`); blind spot in `docs/NEGATIVE_SPACE.md`
   section 6 line 1; the family is the "only one no screen covers".
4. **Control (built and run, minutes).** Plant c = sigma(p + k) on the solved Welcome text: unrelabelled screen
   1.0068-1.0637 (noise); sigma_inv-relabelled 1.6702 == plaintext; null (uniform plaintext) <= 1.052; wrong sigma
   <= 1.055; end-to-end through the Rust engine 1.6702 at the true offset only vs null 1.1348
   (`work/kscreen/RELABEL.md:88-108`). Null: the same run on random ciphertext.
5. **Decision rule.** Any relabelled window reaching IoC >= 1.40 with the ordinary CAMPAIGNS verification is a
   candidate for the whole-section check.
6. **Cost.** 72 settings (29 reflections + 26 affine + 17 keyword alphabets from `lp.KEYWORDS`), each one relabel
   plus one library screen: about 1 h on the 2080 Ti, about 6 h on 14 CPU threads (`work/kscreen/RELABEL.md:110-121`;
   per-window cost from `docs/registry.toml:53-66`).

## H2 (rank 2): unkeyed insertions / collision-conditional nulls and layout key advance

1. **Model.** (a) At a would-be doublet (rate about 0.028 per rune) the encoder writes a null rune that consumes NO
   key value and re-enciphers the plaintext rune with the next key value; (b) or an extra keyless rune is inserted
   at about 42% of word ends; (c) or the key pointer advances an extra step at word separators / line / page breaks.
   The null value may be the echo itself: null = T(c_(i-6)), T(x) = 24 - 2x.
2. **Fingerprint.** Explains the word-length anomaly (one extra rune in 42% of words, p 0.085, and the +1-rune
   direction of the residual after the TH correction); explains the doublet deficit (the rule IS the anti-repeat
   rule); the null value T(c_(i-6)) explains the lag-6 echo at exactly its observed rate (0.0272 +/- 0.0047 vs
   0.0269-0.0282 avoided collisions, finding 3) and word-internal-only scope if the rule is word-scoped. It does NOT
   explain the lag-5 S concentration (a mechanism needs a fixed element S, `work/log/phase9_families.md:60-62`).
3. **Registry rows.** `open-unkeyed` (priority 2, `docs/registry.toml:664-674`); `obs-wordlen`
   (`docs/registry.toml:633-637`); blind spot 9 (`docs/NEGATIVE_SPACE.md:27`); H8
   (`docs/HYPOTHESES.md:172-182`).
4. **Control (minutes, ~50 lines of Python).** Plant Emerson with a known library key, no skips; add one keyless
   rune at 42% of word ends; decode with the aligned forward pointer: the insertion plant must score < 1.40 in
   >= 95% of 100 replicates (proving the current screens are blind to it) while the no-insertion plant scores
   >= 1.57; null = random keys, same settings. Engine option after that: pointer-stay at word-final runes and a
   per-rune extra-advance line.
5. **Decision rule.** Once the option exists: planted null-T keys recovered at the exact setting (IoC >= 1.6);
   random-null max <= 1.37; an LP2 decode reaching 1.40 + whole-window verification is a candidate.
6. **Cost.** 3-4 h of engine work, then about 7 min of CPU per variant (registry estimate, `docs/registry.toml:671`).

## H3 (rank 3): staggered mid-page windows x the library (tests audit assumption 5 on real data)

1. **Model.** The key starts at a mid-page position (a fresh key at an unknown place), not at a section/page start.
2. **Fingerprint.** Explains nothing by itself, but if true it voids the scope of every IoC negative ("a key that is
   right only somewhere else is not tested", `docs/NEGATIVE_SPACE.md:20-21`). Does not explain the echoes.
3. **Registry rows.** `open-sliding` (`docs/registry.toml:759-767`); blind spot 3.
4. **Control (minutes).** Plant a library key at a staggered start: the screen must recover it >= 1.6; rand:300 null
   <= 1.37.
5. **Decision rule.** A stream with IoC >= 1.40, +0.15 over its matched null, surviving whole-window verification.
6. **Cost.** About 12 windows x 1,447 streams x offsets ~ 2.8 M decodes ~ 1-2 min on 14 CPU threads per sign/model
   combination (about 10 min for all four). **RUN 2026-10-18** (both models, 31 windows, every offset):
   792,182,494 decodes in 19 min, best IoC 1.3320 against the rand:300:300 null's 1.3184 -- 0.014 over the null,
   far below the 1.40 rule and the +0.15 verification margin: **negative, the library at mid-page starts is
   excluded** (plant control 1.6779 at the exact offset; `results/kscreen/staggered.tsv`, `staggered_null.tsv`).

## H4 (rank 4): per-rune periodic sign templates (Beaufort / Vigenere alternation, period 2-5)

1. **Model.** c_i = s_(i mod P) * (p_i + k_j) or c_i = s_(i mod P) * p_i + k_j with s a period-2..5 sign pattern
   (25 templates already built).
2. **Fingerprint.** Sign flips are affine multipliers of the plaintext term, so they keep the flat IoC and the
   doublet fingerprint; they do not produce the lag-6 relation or the S echo -- this is a coverage gap, not an
   explanation.
3. **Registry rows.** `open-sign-periodic` (priority 5, `docs/registry.toml:696-705`); the 61 word-level sign rules
   ran negative (`docs/registry.toml:187-200`) but the per-rune templates never ran (queued, `docs/QUEUE.md`).
4. **Control.** Already built: 9/9 planted windows recovered (`results/kscreen/sign_periodic_selftest.txt`); matched
   null per template.
5. **Decision rule.** As for every kscreen hit: 1.40 + whole-window verification.
6. **Cost.** About 2.7 h CPU, nothing to build (`docs/registry.toml:702`).

## H5 (rank 5): two layers -- a keyword inside a stream, with drift tracking (H1 of docs/HYPOTHESES.md)

1. **Model.** c_i = D(p_i) + t_(j) + w_(j mod L) + b mod 29 with the skip rule on the combined key: the solved pages'
   two methods stacked (Welcome's keyword DIVINITY / FIRFUMFERENFE inside An End's totient-style stream).
2. **Fingerprint.** The outer stream keeps the key uniform (flat IoC), the keyword layer hides the literal-F
   convention (no F excess), the skip rule gives the doublet deficit. Does not explain the echoes or word lengths.
3. **Registry rows.** `layer2` (partial: A1 and the periodic slices negative, `docs/registry.toml:428-438`);
   `open-h1` (priority 9, `docs/registry.toml:738-745`).
4. **Control (minutes once the decoder exists).** Emerson + totient + DIVINITY with the skip rule recovered at the
   exact offset and L; the current kscreen blind to the same plant (specified in `docs/HYPOTHESES.md:70-80`).
5. **Decision rule.** Periodic IoC of the decoded columns about 1.8 vs 1.0 +- 0.07 for L = 8, then whole-section
   verification.
6. **Cost.** 1-2 days of engine work, then CPU/GPU runs (`docs/registry.toml:743`).

---

# C. WHAT WE SHOULD STOP DOING

1. **More plain additive library-stream screening** (c = D(p) +/- m*k + b on the 1,447 streams and their decimations
   / multipliers / feedback variants). Coverage is saturated: 409 M + 5.7 B + 8.1 B + 9.2 B decodes at matched-null
   power, 26 families excluded (`docs/registry.toml:53-259`); each additional stream has near-zero prior and the
   same power profile. New stream ideas should only be screened behind a new structural front-end (H1's relabel, the
   H2 decoder, the H5 drift tracker).
2. **Dictionary-scored sweeps and their leftovers** (prngx stage B, rescreen-style reruns, any word-scored lane).
   They are separator-blind: a planted key scores 33 with its own word cuts and 0 with LP2's
   (`docs/NEGATIVE_SPACE.md:14-16`), and the boundary-free lanes supersede them wherever they exist. Do not spend
   cycles finishing the rand48/msvc/java stage-B chunks.
3. **Short-window restart/heading tests** (windows below about 250 runes). Power is 13/21 recovered at 91-139 runes
   (`docs/NEGATIVE_SPACE.md:18-19`), the maxima are heavy-tailed, and the heading/page windows already produced
   three noise candidates that cost a day to dismiss (`docs/registry.toml:486-495`). Only run short windows behind a
   new decoder with measured power.
4. **New keyless echo statistics.** The two-tap family is untestable by construction: three free rates fit three
   numbers (`docs/registry.toml:449-457`), and this round shows three more named mechanisms dead while the general
   scan still has no power at 1.5% (`docs/registry.toml:459-469`). The only formulations with power are decode-based
   ones (H2's engine option; the sweep in finding 1 is the template: a keyless statistic plus a planted control that
   shows the true setting's score).
5. **Expanding the OEIS / hashscan / KDF lanes** (more sequences, more passphrase lists, 36-48-rune windows). The
   lanes' best scores are indistinguishable from their matched nulls (OEIS real best 181/246 vs null 192/230,
   `PLAN.md:426`), and the short-window lanes have 29% power for anything but English
   (`work/log/phase10_review.md:13`). Wait for a structural engine before spending more candidates.

---

## Details of this round's new results (all controlled; all files committed)

- **Affine lag-feedback autokey excluded.** Sweep of c_i = p_i + a*c_(i-d) + b (mod 29) over d = 1..8, a = 1..28,
  b = 0..28 (6,496 settings), residual scored by chi-square against uniform (invariant to any plaintext-alphabet
  permutation), 200-shuffle null per scope-lag; scopes: word / clause / line-page / all. LP2's formal top is
  chi2 275.17 at (d, a) = (1, 1) -- the doublet deficit itself (the r = 0 cell holds 63 within-word equal pairs
  against 346.9 expected, z -15.5, 84% of the chi2; it also crosses word boundaries, 23 vs 99.6, so it is a global
  digram property, not an autokey; residual IoC 1.025, tails junk). The echo setting (6, 27, 24) scores 64.86, below
  the null max 67.74 (p99 65.36), and its whole excess is the residual cell r = 0 (F); clause/line/all scopes
  36.8-49.1 vs null max 60.2-65.5; nonlinear maps (x^2, x^3, x^-1, 2^x, 3^x) at lag 6: 36.2 vs 67.6; word heads /
  initials / finals are uniform (`work/tmp/lag_feedback_scope_extension.txt`, `_nonlinear.txt`, `_head_probe.txt`,
  `_diag_1_1_0.txt`). Plant control: (d,a,b) = (6,27,24) on the keyed solved sections recovers 73/73 residual
  positions, chi2 164.16 (chi2/n = 2.25; the true model on n = 1290 pairs would give about 2900; an English-like
  tail needs only about 33 pairs to beat the null max, so lags 1..8 are excluded at the plant's power)
  (`work/tmp/lag_feedback_plant.txt`). The solved keyed sections are null-like on the same sweep
  (`work/tmp/lag_feedback_an_end.txt`).
- **Echo sources:** plaintext-F replacement excluded (0.0056 vs 0.0272 +/- 0.0047, `work/tmp/frate_pos6.txt`),
  collision twist W3(a) excluded (3/80 vs 2.8 expected, `work/tmp/w3_sharp_test.txt`), echo rate vs avoided-collision
  rate per section: r = -0.38, n = 9 (`work/tmp/echo_vs_skip_rate.txt`). Echo pairs are spread over sections and
  vocabulary: no hit-bearing word repeats (0/74 and 0/93), multi-hit words 6 vs 1.64 (Poisson p 0.007) and 9 vs 3.05
  (p 0.004) confounded with the source concentrations, the 11 S,S pairs: 3 word-final, 4 at position 0
  (`work/tmp/echo_pairs_report.md:57-126`). The lag-6 residual is not plaintext: pooled IoC 1.029 vs shuffle range
  0.986-1.018, the F cell alone carries the excess (`work/tmp/echo_pairs_report.md:170-225`).
- **Outer-alphabet front-end built and controlled** (`work/kscreen/relabel_export.py`, `work/kscreen/RELABEL.md`,
  `work/tmp/relabel_control.txt`): see H1.
- **Staggered mid-page windows (audit assumption 5, run to completion).** 31 windows of 300 runes at mid-section
  offsets across 0.7-0.15 x the 1,447-stream library at every offset, both models: 792,182,494 decodes in 19 min,
  best IoC 1.3320 vs the rand:300:300 null's 1.3184 (+0.014, rule needs +0.15 and 1.40): negative; a library key
  starting mid-page is excluded. Plant control recovered at 1.6779 at the exact offset
  (`results/kscreen/staggered.tsv`, `staggered_null.tsv`, `work/tmp/stag_plant_screen.tsv`).
- **Methodology audit** with per-assumption tests: `work/tmp/methodology_audit.md`.
