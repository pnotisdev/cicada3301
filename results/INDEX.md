# Results index

*Generated from [docs/registry.toml](../docs/registry.toml) by `scripts/build_overview.py`; do not edit by hand. Updated 2026-10-18. An interactive version with a chart is [index.html](index.html) (open it in a browser).*

**Nothing in LP2 is solved.** Every negative below has a positive control (a planted key the method recovers) and a null control. How to read a result file:

* `*_verify.txt`: the best hits re-decoded over their whole window. `0 of N ... (none: noise)` is a negative; `no candidate reached the sweep's floor` is a negative.
* `*_selftest.txt`: the planted-key control (`SELFTEST PASSED`). A screen without it counts for nothing.
* `*.tsv`: the top hits; header lines starting with `#` give the settings and a histogram of all decodes.

## Folders

| Folder | Content | Start with |
|---|---|---|
| [overnight/](overnight/) | Runner state, logs, REPORT.md (the verdict per campaign) and selftests, one folder per PC alias | results/overnight/desktop/REPORT.md |
| [kscreen/](kscreen/) | Keystream-library IoC screens: top hits (tsv), per-window bests, re-decoded hits (_verify.txt), controls (_selftest.txt); chain/, signs/, signs_extra/, lin3/, typo_items/ | a *_verify.txt file; '0 of N' is a negative |
| [prng/](prng/) | Seed sweeps: bg_* (boundary-free, window 0.7), bgtime_* and bgsmall_* (epoch seconds, small seeds, per-page), time_gpu/ (millisecond months), php/glibc/net_* (dictionary scores) | a *_verify.txt file; 'no candidate reached the sweep's floor' is a negative |
| [prngx/](prngx/) | OEIS lane (bg_oeis_*), KDF lane (bg_kdf*), java / msvc / drand48 / MT human-plausible seeds | bg_oeis_verify.txt, bg_kdf_verify.txt |
| [hashscan/](hashscan/) | Passphrase to hash-stream keys (dictionary and boundary-free bg_* variants) | bg_words_verify.txt |
| [layer2/](layer2/) | Two-layer screen: bigram and periodic modes, controls | combined_control.txt |
| [walk/](walk/) | Key-free secret-alphabet search (dsearch) against surrogates | dsearch_control.txt |
| [screens/](screens/) | Dictionary screens rerun with the corrected segmentation |  |
| [payload/](payload/) | Hash and passphrase-decryption tests on the corrected 256-byte payload |  |
| [analysis/](analysis/) | Statistics of the ciphertext and one-off checks (word lengths, echoes, restarts, cribs, controls); one text file per script in work/ | the file named like the script |

## Results by question

### Additive key from a known stream (c = p + m*k, skip / coin anti-repeat)

| Test | Status | Best (null) | Files |
|---|---|---|---|
| Keystream library: 1,447 streams (number theory, constants, Cicada numbers, hashes of Cicada strings) | excluded | 1.366 (null 1.318) | [library_segments.tsv](kscreen/library_segments.tsv), [library_segments_verify.txt](kscreen/library_segments_verify.txt), [null_segments.tsv](kscreen/null_segments.tsv) |
| Library x all 28 key multipliers (c = p + m*k, for example 3301*k = 24*k mod 29) | excluded | 1.381 (null 1.318) | [library_segments_allmults.tsv](kscreen/library_segments_allmults.tsv), [library_segments_allmults_verify.txt](kscreen/library_segments_allmults_verify.txt) |
| Every linear recurrence of order 1-3 and every polynomial up to degree 3, mod 29, every start state | excluded | 1.368 (null 1.318) | [lin2_segments.tsv](kscreen/lin2_segments.tsv), [lin3_segments.tsv](kscreen/lin3_segments.tsv), [poly3_segments.tsv](kscreen/poly3_segments.tsv), [lin3_segments_verify.txt](kscreen/lin3_segments_verify.txt) |
| Hash streams of the 12,944 words and phrases of the solved text (sha256 / sha512 / md5 counter streams and chains) | excluded | 1.371 (null 1.364) | [library_hashwords.tsv](kscreen/library_hashwords.tsv), [library_hashwords_verify.txt](kscreen/library_hashwords_verify.txt) |
| Decimated library (d = 2..29), prefix / word sums of the solved plaintext and Self-Reliance, pi / e / phi / sqrt2 at 10^6 and 3301 x 1033 | excluded | 1.375 (null 1.355) | [library_hyp.tsv](kscreen/library_hyp.tsv), [library_hyp_verify.txt](kscreen/library_hyp_verify.txt), [hyp_selftest.txt](kscreen/hyp_selftest.txt) |
| Ciphertext as the key: solved ciphertexts and LP2 backwards (28 multipliers), LP2 forwards with the self-key guard | excluded | 1.307 (null 1.355) | [library_h5.tsv](kscreen/library_h5.tsv), [library_self.tsv](kscreen/library_self.tsv), [library_self_verify.txt](kscreen/library_self_verify.txt) |
| Combinations of number-theoretic streams, functions at the primes, reciprocals, prime residues (1,063 streams) | excluded | 1.369 (null 1.318) | [sacred_segments.tsv](kscreen/sacred_segments.tsv), [sacred_segments_verify.txt](kscreen/sacred_segments_verify.txt), [sacred_selftest.txt](kscreen/sacred_selftest.txt) |
| Inverses, discrete logs, g^n and cubes modulo primes = 1 (mod 29), base-29 digit sum (19 periodic streams) | excluded | 1.249 (null 1.318) | [sacred2_segments.tsv](kscreen/sacred2_segments.tsv), [sacred2_segments_verify.txt](kscreen/sacred2_segments_verify.txt), [sacred2_selftest.txt](kscreen/sacred2_selftest.txt) |
| Book-derived streams: phi / sigma of 3301 i + 1033 and 1033 i + 3301, primes at index multiples 58..3301, base-29 digits of 1/45415 (15 streams) | excluded | 1.273 (null 1.318) | [sacred3_segments.tsv](kscreen/sacred3_segments.tsv), [sacred3_segments_verify.txt](kscreen/sacred3_segments_verify.txt), [sacred3_selftest.txt](kscreen/sacred3_selftest.txt) |
| Word-level key-sign rules ('their numbers are the direction'): 61 non-circular rules over 581 flat-IoC library streams | excluded | 1.388 (null 1.370) | [signs](kscreen/signs), [signs_extra](kscreen/signs_extra), [sign_selftest.txt](kscreen/sign_selftest.txt) |
| Ciphertext feedback c_i = a*c_(i-1) + p_i + k, a = 1..28 (library, order-2 recurrences, cubic polynomials) | excluded | 1.415 (null 1.320) | [chain](kscreen/chain), [library_a17_verify.txt](kscreen/chain/library_a17_verify.txt) |
| Key running backward through the text, with and without ciphertext feedback (a = 0..28) | excluded | 1.387 (null 1.335) | [chain](kscreen/chain) |
| Step-domain cipher: the plaintext enters c_i - c_(i-1), keyed mod 28 (variants A, B, C) | excluded | 1.297 (null 1.320) | [step_periodicity.txt](analysis/step_periodicity.txt) |
| Clocked key pointer: after each rune the pointer advances by 1 + index, prime or prime - 1 (six clocks) | excluded |  | [clock_c1_library.tsv](kscreen/clock_c1_library.tsv), [clock_pp_library_verify.txt](kscreen/clock_pp_library_verify.txt) |
| Per-rune periodic sign templates (period 2-5: the Beaufort / Vigenere alternation) | open |  | [sign_periodic_selftest.txt](kscreen/sign_periodic_selftest.txt) |

### Seeded generators, passphrases and sequences as keys

| Test | Status | Best (null) | Files |
|---|---|---|---|
| Ten seeded generators over all 2^32 seeds (net: 2^31), boundary-free bigram score, window 0.7 | excluded |  | [bg_py3_07_verify.txt](prng/bg_py3_07_verify.txt), [bg_php_07_verify.txt](prng/bg_php_07_verify.txt), [bg_net_07_verify.txt](prng/bg_net_07_verify.txt) |
| Epoch-second seeds 2011-2015 (8 generators) and small seeds below 2^27, on every section | excluded |  | [bgsmall_glibc_all_verify.txt](prng/bgsmall_glibc_all_verify.txt) |
| Per-page seeds: 8 generators x (epoch seconds 2011-2015, seeds below 2^27) on the 44 page windows | excluded |  | [bgsmall_drand48_pages_verify.txt](prng/bgsmall_drand48_pages_verify.txt), [bgsmall_glibc_pages_verify.txt](prng/bgsmall_glibc_pages_verify.txt) |
| Millisecond timestamps 2012-01 .. 2014-01 as seeds (Java 48-bit, CPython two-word seeds, Java abs() map, Ruby), window 0.7 | partial |  | [time_gpu](prng/time_gpu) |
| Dictionary-scored seed sweeps: PHP, glibc, .NET on all 8 sections; seven more generators on window 0.7 | partial |  | [php_all.tsv](prng/php_all.tsv), [glibc_all.tsv](prng/glibc_all.tsv) |
| Human-plausible seeds (334 M per generator) for MT init_by_array, MSVC, Java, drand48; 3-6 key maps each | partial |  | [java_b_negative.tsv](prngx/java_b_negative.tsv) |
| 199,088 OEIS integer sequences as keys (mod 29), boundary-free score | partial |  | [true_key_score.txt](analysis/true_key_score.txt), [bg_oeis_verify.txt](prngx/bg_oeis_verify.txt), [bg_oeis_A60_verify.txt](prngx/bg_oeis_A60_verify.txt), [bg_oeis_B48_verify.txt](prngx/bg_oeis_B48_verify.txt) |
| Passphrases to hash streams (19.2 M candidates, MD5 / SHA-1 / SHA-256 / SHA-512) and KDF streams (719,280) | partial |  | [bg_words_verify.txt](hashscan/bg_words_verify.txt), [bg_kdf_verify.txt](prngx/bg_kdf_verify.txt) |
| Dictionary screens (screen 1, screen 2, reverse direction, heading restarts) with the corrected word segmentation | partial |  | [screens](screens) |

### Cipher structure beyond c = p + k

| Test | Status | Best (null) | Files |
|---|---|---|---|
| Periodic keys (drift-aware matched filter that allows for the skip rule's key drift) | excluded |  | [drift_period.txt](analysis/drift_period.txt), [step_periodicity.txt](analysis/step_periodicity.txt) |
| Plaintext / ciphertext autokey (lag <= 8), monoalphabetic, Vigenere (period <= 29), per-word key, progressive, multiplicative and cumulative keys | excluded |  | [families.txt](analysis/families.txt) |
| Small state machines: 4,608 rules x 29 start states, with and without the skip modelled | excluded |  | [state_machines.txt](analysis/state_machines.txt), [state_machines_skip.txt](analysis/state_machines_skip.txt) |
| Per-word keys: constant, linear, quadratic, periodic (<= 7), recurrences of order <= 3; same word -> same cipher | excluded |  | [word_recurrence_d2.txt](analysis/word_recurrence_d2.txt), [word_recurrence_d3.txt](analysis/word_recurrence_d3.txt), [word_key_dictionary.txt](analysis/word_key_dictionary.txt) |
| Key-free search for a secret outer alphabet behind a per-word additive key (walk dsearch, m = 1..8 position phases) | partial |  | [dsearch_control.txt](walk/dsearch_control.txt), [dsearch.txt](walk/dsearch.txt) |
| Two layers: a keyword Vigenere inside a number stream with the anti-repeat rule outside (H1, the laptop's layer2) | partial |  | [bigram_combined.tsv](layer2/bigram_combined.tsv), [combined_control.txt](layer2/combined_control.txt), [selftest.txt](layer2/selftest.txt) |
| Per-word period-5 twist skeleton (key state T^(j mod 5), T(x) = 24 - 2x) | excluded |  | [skeleton5.txt](analysis/skeleton5.txt) |
| Two-tap echo rules (copy or affine image of the rune 5 and 6 back, inside words) and rewrites of plaintext repeats | untestable |  | [echo_values.txt](analysis/echo_values.txt) |
| Affine lag-feedback autokey: c_i = p_i + a*c_(i-d) + b within words, d = 1..8, all a, b (6496 settings), four separator scopes, plus nonlinear maps (x^2, x^3, x^-1, 2^x, 3^x) at lag 6 | excluded |  | [lag_feedback_scope_extension.txt](../work/tmp/lag_feedback_scope_extension.txt), [lag_feedback_plant.txt](../work/tmp/lag_feedback_plant.txt), [lag_feedback_nonlinear.txt](../work/tmp/lag_feedback_nonlinear.txt), [lag_feedback_head_probe.txt](../work/tmp/lag_feedback_head_probe.txt), [lag_feedback_null_shuffles.txt](../work/tmp/lag_feedback_null_shuffles.txt), [lag_feedback_an_end.txt](../work/tmp/lag_feedback_an_end.txt) |
| Named lag-6 echo source mechanisms: plaintext-F replacement, collision twist W3(a), autokey chain | excluded |  | [w3_sharp_test.txt](../work/tmp/w3_sharp_test.txt), [echo_vs_skip_rate.txt](../work/tmp/echo_vs_skip_rate.txt), [frate_pos6.txt](../work/tmp/frate_pos6.txt), [lag6_residual_quick.py](../work/tmp/lag6_residual_quick.py), [echo_pairs_report.md](../work/tmp/echo_pairs_report.md), [echo_word_final.txt](../work/tmp/echo_word_final.txt) |
| Affine feedback in the GP prime domain and mixed index/prime domains: r = PRIME[c_(i+d)] - a*PRIME[c_i] - b (mod 29), d = 1..8, all a, b, within words | excluded |  | [prime_scan_report.md](../work/tmp/prime_scan_report.md), [prime_scan_results.json](../work/tmp/prime_scan_results.json) |
| Keyless word-edge nulls: every word-final or word-initial rune consumes no key value and is not scored (nulledge=1\|2) | excluded | 1.429 (null 1.385) | [NULLEDGE.md](../work/kscreen/NULLEDGE.md), [nulledge_control.txt](../work/tmp/nulledge_control.txt), [nulledge_report.md](../work/tmp/nulledge_report.md), [nulledge1_segments.tsv](kscreen/nulledge1_segments.tsv), [nulledge2_segments.tsv](kscreen/nulledge2_segments.tsv), [nulledge1_segments_verify.txt](kscreen/nulledge1_segments_verify.txt), [nulledge2_segments_verify.txt](kscreen/nulledge2_segments_verify.txt) |
| Layout key-pointer advance: one extra key value per word boundary, with and without one extra per line / page break (advsep=1\|2) | excluded | 1.329 (null 1.368) | [ADVSEP.md](../work/kscreen/ADVSEP.md), [advsep_control.txt](../work/tmp/advsep_control.txt), [advsep_report.md](../work/tmp/advsep_report.md), [advsep1_segments.tsv](kscreen/advsep1_segments.tsv), [advsep2_segments.tsv](kscreen/advsep2_segments.tsv), [advsep1_segments_verify.txt](kscreen/advsep1_segments_verify.txt), [advsep2_segments_verify.txt](kscreen/advsep2_segments_verify.txt) |
| Evolving-alphabet walk (period-5 alphabets per word, alphabet changes per word, skip on repeat; aldegonde's length-clocked walk) | untestable |  | [perm_relations.txt](analysis/perm_relations.txt) |
| Keyword-mixed outer alphabet around an additive key: relabel the ciphertext by sigma, then the ordinary screen | open |  | [relabel_export.py](../work/kscreen/relabel_export.py), [RELABEL.md](../work/kscreen/RELABEL.md), [relabel_control.txt](../work/tmp/relabel_control.txt), [summary.txt](../work/tmp/relabel_gate/summary.txt), [relabel_all_summary.txt](../work/tmp/relabel_all_summary.txt), [relabel_all_kw_KOAN.tsv](kscreen/relabel_all_kw_KOAN.tsv), [relabel_all_kw_PRIMES.tsv](kscreen/relabel_all_kw_PRIMES.tsv), [relabel_all_atbash.tsv](kscreen/relabel_all_atbash.tsv), [relabel_all_null.tsv](kscreen/relabel_all_null.tsv) |
| Unkeyed insertions (an extra rune per word that consumes no key value) and extra key advance at word separators / line / page breaks | open |  | [README.md](../work/proposals/null_beam/README.md), [null_insertion.txt](analysis/null_insertion.txt) |
| H1: library x keyword (L <= 20) with a drift-tracking decoder | open |  | [README.md](../work/h5slice/README.md), [h5slice.py](../work/h5slice/h5slice.py) |
| H2: tableau / transition-table ciphers (a statistic invariant to the table) | open |  | [proposals_h2_skip.txt](analysis/proposals_h2_skip.txt) |

### Restarts, reuse and layout

| Test | Status | Best (null) | Files |
|---|---|---|---|
| Key restart at every page, paragraph, line, sentence or word | excluded |  | [restart_columns.txt](analysis/restart_columns.txt), [restart_llr.txt](analysis/restart_llr.txt) |
| Library restarted at the 10 red headings and the 46 page starts | partial |  | [library_heads_verify.txt](kscreen/library_heads_verify.txt), [library_pages_verify.txt](kscreen/library_pages_verify.txt), [short_window_null_pages.txt](analysis/short_window_null_pages.txt) |
| Restart at typographic marks: list items of 0.14, three-dot marks, after red headings (22 windows) | partial |  | [library_typo_verify.txt](kscreen/library_typo_verify.txt), [typo_shared_key.txt](analysis/typo_shared_key.txt) |
| Key reuse between sections (two-time pad under skip drift) | untestable |  | [pad_reuse_power.txt](analysis/pad_reuse_power.txt) |
| Transposition | partial |  | [page_seams_2026-10-17.txt](analysis/page_seams_2026-10-17.txt) |
| Key that starts mid-page: windows of 300 runes at staggered positions across the book | excluded | 1.332 (null 1.318) | [staggered.tsv](kscreen/staggered.tsv), [staggered_null.tsv](kscreen/staggered_null.tsv), [staggered_windows.py](../work/tmp/staggered_windows.py), [stag_plant_screen.tsv](../work/tmp/stag_plant_screen.tsv) |

### Cribs, puzzle furniture and outside claims

| Test | Status | Best (null) | Files |
|---|---|---|---|
| Heading = DIVINITY WITHIN; body = 'FIND YOU ARE ...'; title cribs | excluded |  | [crib_exact_lookup.txt](analysis/crib_exact_lookup.txt), [crib_matrix_check.txt](analysis/crib_matrix_check.txt), [crib_fluency_null.txt](analysis/crib_fluency_null.txt) |
| 27 x 27 layout, page numerology, totient walk | excluded |  | [page_numerology.txt](analysis/page_numerology.txt), [grid729_check.txt](analysis/grid729_check.txt) |
| The 256-byte base-60 payload (pages 64-66), corrected bytes | excluded |  | [hashes.txt](payload/hashes.txt), [decrypt.txt](payload/decrypt.txt) |
| Page-30 grid, the Some Wisdom word square (1033), the page-14 square (3301) | explained |  | [grid_key.txt](analysis/grid_key.txt) |
| Origin of the 0.6 square's seeds {809, 434, 312, 966, 1311, 204} and t = 1246 | open |  | [squares_check.txt](analysis/squares_check.txt) |

### What LP2 shows (any solution has to explain it)

| Test | Status | Best (null) | Files |
|---|---|---|---|
| Doublet deficit: 0.63% of adjacent pairs against 3.45% expected | observed |  | [seploss.txt](analysis/seploss.txt) |
| Within-word lag-5 echo | observed |  | [echo_position.txt](analysis/echo_position.txt), [lag5_check.txt](analysis/lag5_check.txt), [echo_pairs_report.md](../work/tmp/echo_pairs_report.md) |
| Within-word lag-6 relation c' = 24 - 2c | observed |  | [echo_values.txt](analysis/echo_values.txt), [lag5_affine.txt](analysis/lag5_affine.txt), [lag_feedback_scope_extension.txt](../work/tmp/lag_feedback_scope_extension.txt), [w3_sharp_test.txt](../work/tmp/w3_sharp_test.txt) |
| Word lengths: no serial structure, fewer 2-rune words than English | observed |  | [wordlen.txt](analysis/wordlen.txt), [wordlen_adjacency.txt](analysis/wordlen_adjacency.txt), [wordlen_parametric.txt](analysis/wordlen_parametric.txt) |
| Flat unigrams and bigrams, no coincidence peak at any lag, no literal-F excess, repeated 6-gram DJU-BEI | observed |  | [segment_stats.txt](analysis/segment_stats.txt), [assumption_checks.txt](analysis/assumption_checks.txt), [pair_repeat.txt](../work/tmp/pair_repeat.txt), [dju_context.txt](../work/tmp/dju_context.txt), [dju_counts.txt](../work/tmp/dju_counts.txt) |
