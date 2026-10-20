# Frontier audit: completed offline inventory and algebra

No engines, searches, simulation, new significance tests or exclusions. Input hashes and full records: `audit.json`.

## Independently scanned canonical transcription

| section | runes | words | doublets | lag5 eligible / hits / S hits | lag6 eligible / T hits |
|---|---:|---:|---:|---|---|
| 0.7 | 729 | 158 | 4 | 135 / 7 / 1 | 79 / 6 |
| 0.8 | 1145 | 255 | 6 | 183 / 5 / 1 | 106 / 6 |
| 0.9 | 1729 | 383 | 9 | 291 / 18 / 1 | 184 / 10 |
| 0.10 | 9 | 2 | 0 | 0 / 0 / 0 | 0 / 0 |
| 0.11 | 1894 | 435 | 10 | 295 / 18 / 1 | 178 / 13 |
| 0.12 | 1021 | 224 | 11 | 168 / 8 / 0 | 100 / 5 |
| 0.13 | 1524 | 349 | 13 | 241 / 9 / 0 | 152 / 11 |
| 0.14 | 1589 | 355 | 12 | 250 / 13 / 2 | 154 / 9 |
| 0.15 | 3316 | 735 | 21 | 542 / 26 / 5 | 337 / 20 |

Totals: {"runes": 12956, "words": 2896, "transitions": 12947, "doublets": 86, "lag5_pairs": 2105, "lag5_hits": 104, "lag5_S_opportunities": 74, "lag5_S_hits": 11, "lag6_pairs": 1290, "lag6_T_hits": 80}
Adjacent word pairs: 2887; repeated types: [{'words': ['DJU', 'BEI'], 'count': 2}].

## Registry and local exports

Registry statuses: {'excluded': 33, 'partial': 11, 'untestable': 3, 'explained': 1, 'open': 14, 'observed': 8}.
Local library.tsv: 1439 rows; 858 plain-additive marginal flags; 581 unflagged. This is local generated data, not new family coverage.
- `work/kscreen/data/segments.txt`: 8 windows; 0 have L sums different from R length.
- `work/kscreen/data/heads.txt`: 10 windows; 1 have L sums different from R length.
  - head0.15@2982: R=334, L sum=333. Default IoC does not use L; layout-option fallbacks are a separate scope issue.
- `work/kscreen/data/pages.txt`: 0 windows; 0 have L sums different from R length.
- `work/kscreen/data/staggered.txt`: 31 windows; 0 have L sums different from R length.

## Mechanical look menus (not independent trial counts)

- registered_rows: 70
- registered_nonobserved_rows: 62
- affine_lag_cells: 6496
- advertised_full_four_scope_menu_not_verified_as_executed: 25984
- executed_scope_extension_rows_four_scopes_two_lags: 6496
- word_all_eight_lags_plus_nonword_two_lags_unique_rows: 11368
- residual_chi_square_b_shift_classes_upper_bound_on_unique_scores: 392
- later_kernel_cells_including_guards_and_mixtures: 12995
- family_diagnostic_cells: 250
- lag_by_source_cells_logged: 232
- repeat_spectrum_lengths: 8
- wordlen_parameter_settings: 322
- corpus_spelling_rows: 34
- wordlen_two_parameter_grid: 891
- wordlen_mechanism_grid: 364
- wordlen_expansions: 8
- executed_residual_rows_plus_later_kernel_menu_not_independent: 24363
- effective_independent_looks: unknown; overlapping cells and adaptive history; do not sum as independent tests

## Exact arithmetic and explicit reference assumptions

- h5_real_cells: 353248000
- h5_campaign_null_cells: 4864000
- h5_small_control_cells: 60800
- h5_real_to_campaign_null_ratio: {'exact': '581/8', 'decimal': 72.625}
- h5_real_to_small_control_ratio: {'exact': '5810', 'decimal': 5810.0}
- source_S_gross_collision_budget_at_q_081: {'exact': '2997/1450', 'decimal': 2.0668965517241378}
- shared_lag5_lag6_excess_rounded_input: (104-36)-(72.9-27.8)+(80-44.9) = 58.0; expectations are rounded different-null outputs
- shared_collision_attempt_mean_at_q_081: {'exact': '10449/290', 'decimal': 36.03103448275862}
- global_doublet_fraction: {'exact': '86/12947', 'decimal': 0.006642465436008342}
- global_doublet_percent: {'exact': '8600/12947', 'decimal': 0.6642465436008341}
- ungated_null_one_step_mass_if_null_value_factor_omitted: {'exact': '223/125', 'decimal': 1.784}
- proper_uniform_null_one_step_mass: {'exact': '1', 'decimal': 1.0}
- prime_square_library_marginal_ioc: {'exact': '5153/5000', 'decimal': 1.0306}
- expected_ioc_after_random_keyword_L20_independent_phases: {'exact': '100153/100000', 'decimal': 1.00153}
- marginal_formula_warning: No collision rule, finite-stream clock correlations or decoder power calibrated by this calculation.
- generic_unigrams_and_bigrams_cannot_be_exactly_iid: Doublet deficit already rules out exact iid bigrams; flat means no other detected departures, not equality to iid.

## Hypothetical family-multiplicity sensitivity, NOT global p-values

Columns use the reported .001 MC floor, .008 fixed-halves adjusted p, .007 S-related calibration, .016 word-shuffle p, respectively.
- M=1: {'0.001': 0.001, '0.008': 0.008, '0.007': 0.007, '0.016': 0.016}
- M=10: {'0.001': 0.01, '0.008': 0.08, '0.007': 0.07, '0.016': 0.16}
- M=62: {'0.001': 0.062, '0.008': 0.496, '0.007': 0.434, '0.016': 0.992}
- M=95: {'0.001': 0.095, '0.008': 0.76, '0.007': 0.665, '0.016': 1.0}

Existing local corrections must not be counted twice. Historical effective independent looks and a calibrated global p remain unknown.

The registry's broad four-scope lag-1..8 phrasing is not the recorded executed grid: the non-word scope extension is only lags 5 and 6. All b shifts only relabel residual histograms, leaving chi-square unchanged: 392 b-shift classes are an upper bound on distinct numerical scores, not a measured count of unique values. Do not count the advertised 25,984-cell rectangle as executed independent tests.

## Static-audit caveats

- The un-gated prototype gives each possible null value weight rho, rather than rho/29. Summing its one-output masses yields 1+28*rho, not the stated local Bernoulli kernel. This does NOT alone invalidate the ratio: a different globally conditioned mask prior can have a common language/uniform normalizer (LIKELIHOOD_NOTE.md). The gated deterministic-null original is different and is not refuted by this identity.
- Prototype NULL_RATE=.42 is per eligible position, while the decoder uses .028; neither is the reported .42 per multi-rune WORD. Its report also retains a wrong-plaintext-window caveat. These are different experiments.
- The random-key full PLANTS in gated_null_report.md are true-key positives, not wrong-key nulls. Their 5/12 passes are not a false-positive estimate.
- No exact-offset requirement is assumed equivalent to plaintext/key-family detection. That requires a new calibrated gate, not automatic authorization to screen.

FINISHED; elapsed seconds: 0.3846. No statistical gate or search was run; invocation history is in RUN_LOG.md.
