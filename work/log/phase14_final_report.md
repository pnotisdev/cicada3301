# Final wrap-up report (2026-10-18, evening)

Scope: LP2, sections 0.7-0.15 of Cicada 3301's Liber Primus, 12,956 runes. **Nothing in LP2 is solved.**
This closes an autonomous review campaign (rounds 1-95) built on the repository's existing experiment ledger.
Every number below is cited to the file it lives in; the full logs are `work/log/phase11_review.md`,
`work/log/phase12_review2.md`, `work/log/phase13_gated_h5.md`, and the registry (`docs/registry.toml`),
which now records **70 rows: 33 excluded, 11 partial, 3 untestable, 14 open, 1 explained, 8 observed**
(the generated "Tests on record" block shows 62: it counts the test rows and omits the 8 observed
measurements; an earlier draft said 58 / 11 open - that was stale before the session's later rows landed).

## 1. The review deliverable (round 1): `work/log/phase11_review.md`

- **A. Audit - the five assumptions most likely wrong**: (1) separators = plaintext word boundaries (4 sd
  word-length correlation, planted key 33 -> 0 under LP2's cuts); (2) skip/coin with one key value per rune,
  forward-only pointer; (3) the key is a global-position stream (the echoes are strictly word-internal);
  (4) additive mod 29 in GP index order; (5) 300-rune windows at section starts (later closed for the library).
- **B. Five ranked hypotheses with controls and costs** (H1 outer keyword alphabet, H2 unkeyed
  insertions/layout advance, H3 staggered windows, H4 sign templates, H5 two-layer keyword-in-stream) - all
  five have since been built, run or closed (below).
- **C. Stop-doing list**: plain additive library screens, dictionary-scored sweeps, short-window restart
  tests, keyless echo statistics, OEIS/hash/KDF lane expansions - each with the measured reason.

## 2. What was found and excluded during the campaign (all controlled; planted keys recovered, nulls matched)

| Result | Numbers (file) |
|---|---|
| Affine lag-feedback autokey c_i = p_i + a·c_(i-d) + b (d 1-8, all a/b, 4 scopes, nonlinear maps) | excluded: plant chi2/n 2.25 vs LP2 0.05; top setting is the doublet deficit itself (`work/tmp/lag_feedback_scope_extension.txt`) |
| GP prime-domain and mixed index/prime affine feedback | excluded: plant chi2/n 1.97 vs LP2 0.44; the prime order is not the arithmetic domain (`work/tmp/prime_scan_report.md`) |
| Named lag-6 echo mechanisms (F-replacement, collision twist W3(a), word-end nulls) | F-replacement DISFAVOURED, not excluded (the 0.0056 vs 0.0272 gap used Latin-letter positions, not GP-rune positions; solved-text F at eligible positions is 3/73 = 0.041); W3(a) excluded (3/80 vs 2.8/80); word-end nulls excluded (targets word-final 32/80 vs 34.7) (`work/tmp/frate_pos6.txt`, `w3_sharp_test.txt`, `echo_word_final.txt`) |
| Lag-6 echo candidate mechanism: raw spend-key T6 collision substitution at q = 0.81 | NOT excluded: predicts 79.3 lag-6 T hits vs 80 observed with the other lags flat; full-book selected-family p_MC = .001 (floor, B = 999); fixed-halves T6 adjusted p = .008; section diagnostic own-rate expected 79.3 vs 80. Retrospective, not an untouched replication; spend vs hold has reference power 0.26 and collision causality is not identifiable from ciphertext (registry row `collision-kernel-followup`) |
| Staggered mid-page windows x library | 792 M decodes, best 1.3320 vs null 1.3184: negative (`results/kscreen/staggered.tsv`) |
| Outer keyword-mixed alphabet c = sigma(p + k) | front-end built+controlled (plant 1.6702 vs 1.0068-1.0637); 0.7 gate and all-sections keyword run negative (best 1.3895 vs null 1.3346); AFFINE sigmas proven redundant with the 28-multiplier screen (22,736 settings, |dIoC| < 1e-12) (`work/kscreen/RELABEL.md`, `work/tmp/relabel_all_summary.txt`) |
| Keyless word-edge nulls (engine option nulledge=1|2) | 0%/100% variants excluded (best 1.416/1.429 vs matched nulls; all hits fall to 1.04-1.06); the 42% mixture has no powered IoC decoder (free-beam null 1.75 = truth level) (`work/tmp/nulledge_report.md`) |
| Layout key-pointer advance (engine option advsep=1|2) | excluded: best 1.3191/1.3288 vs matched nulls, 0/10 verified (`work/tmp/advsep_report.md`) |
| Per-rune periodic sign templates (period 2-5) | campaign complete: 25/25 templates, best screen 1.400 falls to 1.04-1.13, 0 verified (`results/kscreen/signs_periodic/`) |
| Multipliers library refresh | not needed: the export is unchanged (1,439 streams); the 5.7 B-decode run is current (`docs/registry.toml` multipliers row) |
| H5 two-layer decoder (totient x keyword, drift-tracking) | built and gated: nats-scored shift-marginalized init + EM; numba init verified (48/48 + 24/24 + truth IoC 1.9856, wcol = DIVINITY, 40/40 null aborts); controls ALL PASS; LP2 first look NEGATIVE (97.3% grid, zero cells >= 1.6) (`work/h5slice/control.txt`, `lp2_look.txt`) |
| H5 Rust port (work/h5rs) | parity-clean 312/312; 3,842 dec/s single / ~17k on 8 threads (20k gate not met; scaling ~4.4x); full 880M-decode library sweep ~ 14 h, or ~6 h over the 581 flat-IoC streams (`work/h5rs/parity.txt`, `README.md`) |

## 3. New observations that any solution must explain

- **DJU->BEI**: the ONLY repeated adjacent word-pair in all 2,887 pairs of LP2 (within-section word-shuffle
  null: P = 0.016; DJU->BEI specifically 0/1000), and its second occurrence is the book's final two words
  (`work/tmp/pair_repeat.txt`; registry obs-flat row).
- **Lag-6 echo candidate mechanism survives**: the raw spend-key T6 collision substitution at q = 0.81 predicts
  79.3 lag-6 T hits against 80 observed, with the other lags flat; full-book selected-family p_MC = .001 (floor,
  B = 999); fixed-halves T6 adjusted p = .008 (registry row `collision-kernel-followup`). Caveats: retrospective
  (not an untouched replication), spend vs hold has reference power 0.26, and collision causality is not
  identifiable from the ciphertext. The echo rate (0.0272 +/- 0.0047) matches the avoided-collision rate
  (0.0269-0.0282); the section correlations use eight contributing sections (+0.329 / -0.329, opposite signs
  forced by the definitions, uncertainty unknown - the earlier "r -0.38, n = 9" report was defective and gives
  no evidence either way).
- Still unexplained: the lag-5 S echo (every candidate mechanism tested was killed, and "a mechanism has to
  contain a fixed element S" still stands), and the word-length anomaly.

## 4. Tooling built (all committed, all default-behavior-preserving)

- `work/kscreen/relabel_export.py` + RELABEL.md (outer-alphabet front-end, controlled).
- `nulledge` and `advsep` engine options in work/kscreen (+ selftests passed).
- `work/h5slice/` (Python+numba H5 decoder, gated, controls, LP2 first look).
- `work/h5rs/` (Rust H5 engine, parity-clean; CLI + sweep driver + campaign design).
- `work/tmp/` holds every analysis script and output behind the numbers above.

## 5. Handoff: what to run next (in order)

1. **H5 flat-library sweep** - tests ONE family (flat-IoC library stream + unknown keyword L <= 20, first
   300 runes of the 8 sections, both anti-repeat models): 581 streams x 8 windows x offsets 0..1999 x L 2..20
   x 2 models = 353 M decodes ~ 6 h at 8 threads. The KSB1 reader is built and 13/13 controls pass; the launch
   design and candidate rule are in `work/h5rs/CAMPAIGN.md` (do not launch until the added plant controls and
   the null-size justification land - see the review notes). Candidate rule (unchanged): IoC >= 1.6 AND >=
   matched-null max + 0.15 -> whole-window re-decode -> whole-section verification (`docs/CAMPAIGNS.md`).
   This does NOT close the family space: the M04 hold-key baseline (registry rows `m04-baseline`,
   `open-m04-decoder`) and the pointer-direction mechanism remain open.
2. **Layer2 remaining slices** (20 streams x 30 keywords bigram + core streams x L 2-14; ~3 h CPU, controls
   exist).
3. **Pointer-direction mechanism** (both orientations, 18 conventions; engine option needed).
4. Re-measure h5rs on an idle machine; if it clears 20k dec/s the full 1,447-stream sweep is ~14 h.

## Bottom line

The campaign produced no candidate for LP2. It did what the review was for: it audited the methodology,
closed families with controls (33 excluded in total), built four new decoder front-ends that were
previously missing (outer alphabet, word-edge nulls, layout advance, two-layer drift tracking), and reduced
the unexplained structure of LP2 to a short list: one surviving candidate mechanism for the lag-6 echo
(raw spend-key T6 collision substitution at q = 0.81 - 79.3 predicted vs 80 observed, fixed-halves p = .008;
retrospective, spend-vs-hold power 0.26, causality not identifiable), the lag-5 S echo and the word-length
anomaly (still unexplained), and the book-ending DJU->BEI pair. The highest-value remaining runs are the
H5 flat-library sweep (one family; launch only after the added controls) and the open M04 hold-key decoder.
