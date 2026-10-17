# Toolkit fix: an unmarked page break is a wrap inside a word (2026-10-17, laptop)

Found while comparing our one-rune words with the cicadanotebook.com inventory
(`work/log/research_cicadanotebook_2026-10-17.md`, section 4.1).

In the transcription, a word boundary at the end of a line or page is always written as '-' or '.'. A bare break is
therefore a typographic wrap, and `lp.word_spans` has treated bare line breaks that way since 2026-10-16. Page breaks
('%') still ended words. 32 of the 55 page breaks inside LP2 have runes on both sides and no mark. The page images show
no separator dot at any of the 32, and show one at all 21 marked page breaks
(`results/analysis/page_seams_2026-10-17.txt`).

**Nothing in LP2 is solved; this changes counts, not conclusions** (details below).

## Code

| File | Change |
|---|---|
| `work/lp.py` `word_spans` | '%' is treated like '\n', a wrap. All 35 or so callers inherit the fix (crib, attack, cribsolve, word-length, lag-5, family, export scripts). |
| `work/stats.py` `adjacent_pairs` | '%' ranks just above '\n', so any written mark wins. New boundary class "page break only". |
| `work/restart_columns.py` | The "word" unit no longer cuts at '%'. The coarser units still do, by design (a restart at every page as well). `test_restart_columns` checks that the word units equal `lp.word_spans`. |
| `work/wordlen_clauses.py` | Any separator token used to end a word, so line wraps split words. Line and page wraps are now joined. |
| `work/crib_matrix_check.py`, `work/crib_fluency_null.py` | These cut words at '\n' and '%'. They now use `lp.word_spans`. |
| `work/grid30.py` `gematria_search` | Word and clause units cut at '\n' and '%'. They now join wraps; lines and pages still cut there. |
| `work/tmp/hyp/probe1.py`, `probe5.py` | These cut at '%'. |
| `work/tmp/apply_crib.py` | Same old rule (Phase 4 scratch). Fixed, but not rerun (see the end of this note). |

Left alone on purpose:
- the page and line layout code (`ocr`, `word_gaps`, `separator_audit`, `red_runs`, `page_numerology`);
- the magic-square cell parsers (`keystreams.py`, `tests/test_stats.py`);
- the line and page restart test D4 in `crib.py`.

## Exports

- **`work/phpmt/data/windows.txt`, `windows_07.txt`:** only the L (word length) lines change; `dict.txt` and `english.txt`
  are identical.
  - Readers: the dictionary-scoring sweeps (phpmt, prngx stage A, hashscan).
  - The boundary-free scorers (bgsweep, the GPU ports) ignore L.
- **`work/walk/data/lp2.txt`:** the L lines change.
- **`work/walk/data/lm3.bin`:** the rune trigram model now trains on solved words kept whole across page breaks.
  `english_test.txt` is identical.
- **`work/walk/data/sur/`:** the dsearch surrogates were drawn from the old `lp2.txt`. The dsearch campaign is complete;
  regenerate them only if it is rerun.
- **`work/kscreen/data/`:** not tracked; rebuilt on the laptop. The screen itself ignores word lengths; only its plant
  files carry them. On the desktop, run `python work/kscreen/export.py` once.

## Results rerun (`results/analysis/`)

"Old" means page breaks counted as word boundaries; "new" means they are wraps. Three scripts were worse off than that,
marked †: they also cut at every line break, the convention fixed in `lp.word_spans` on 2026-10-16.

| Analysis (output) | Old | New | Conclusion |
|---|---|---|---|
| Words; one-rune words (`crib.py`, `tests/test_crib.py`) | 2,928; 99 (3.4%), χ² 18.5 | 2,896; **83** (2.9%) over 28 runes, never ᚳ; χ² 20.8 on 28 df (p 0.83) | Unchanged: the one-rune cipher runes are uniform |
| Doublets by boundary (`stats.doublets`) | the page class mixed marked and unmarked breaks | inside a word 60/9,640 (0.62%); line wrap 3/388 (0.77%); page wrap 0/32; word gap 22/2,727 (0.81%); clause 1/148 | Unchanged: the anti-repeat rule ignores text structure |
| Within-word lag 5 (`within_word.txt`, `lag5_check.txt`, `word_internal_repeats.txt`) | 102 of 2,073 (4.92%), z +3.7; permutation p 0.0004; repeated bigrams 9 vs 1.51 | 104 of 2,105 (4.94%), z +3.75; permutation p 0.0007; 9 vs 1.54 (P 3.4e-5) | Stands |
| Lag 5 inside 10-rune words (`hypotheses_2026-10-17.txt`, probe 3) | 21 of 255, z +4.19 | 20 of 260, z +3.75 | Stands, slightly weaker |
| Family fingerprints (`families.txt`, 25 rows × 100 replicates) | z5 3.65; lag-5 concentration on S (maxz5) 4.22, calibrated P 0.0073; nearest rows: echo 1.5% (11.2), alphawalk period 5 (15.6) | z5 3.73; maxz5 4.15, P 0.010; nearest rows: echo 1.5% (9.0), alphawalk period 5 (12.9) | Ranking unchanged |
| Word lengths (`wordlen.txt`) | English in runes G 227 (p 1e-42); best simple fit +1 rune in 40% of multi-rune words, p 0.025 | G 242 (p 1e-45); +1 rune in **42%, p 0.085** | English in runes rejected more strongly; the extra-rune model is no longer rejected at 5% |
| Language comparison (`wordlen_languages.txt`) | +1 rune G 20.4 (p 0.025); 2-rune words missing G 17.1 (p 0.071) | 15.8 (p 0.10); 18.1 (p 0.054) | The extra-rune mechanism is now the best fit; no language fits |
| Parametric fits, stop lists, separator loss (`wordlen_parametric`, `wordlen_stoplist`, `seploss`) | best G 85.1 / 43.1 / 212 | 84.8 / 41.1 / 221 | All still rejected |
| Neighbouring word lengths (`wordlen_adjacency.txt`) | LP2 lag-1 r −0.008 | −0.015 (z −0.7); English −0.15 | Unchanged: no English-like length alternation |
| Clause boundaries (`wordlen_clauses.txt`) † | 19.7 words per clause, mean word 3.91, first word z +0.7 | 17.2, 4.47, z −0.3 | Unchanged: no sentence-start effect at '.' |
| Community crib for 0.7 (`crib_matrix_check.txt`) † | 4 cipher separators inside crib words (FOREVER, THINK, WORD, ANSWER) | **0**: the crib's 33 word lengths equal LP2's cipher words exactly | The crib was fitted to the true word division; its key-arithmetic evidence (selection) is unchanged |
| Crib fluency null (`crib_fluency_null.txt`) † | real location −3.39 | −3.30, +1.0 sd against LP2 windows | Unchanged: any length pattern has a fluent fit. The corpus token count also moved (2,102,767 → 2,108,966), so the laptop's corpus set differs a little from the first run's |
| Key-restart columns, word unit (`restart_columns.txt`) | Z_sum −1.48 / −0.51 | −1.42 / −0.50 | No restart |
| Per-word recurrences, key dictionary (`word_recurrence_d2/d3.txt`, `word_key_dictionary.txt`) | max hits 5 / 6, equal to the surrogates | same | Negative |
| Keyless probes (`hypotheses_2026-10-17.txt`) | multiplicative key best G 49.2 | 43.4 (4 df) | Excluded; the other probes are unchanged |
| Grid numbers as Gematria sums (`grid30.py`, printed) † | words of 2+ runes: 27 hits vs 30.0 ± 6.1 (all words 120 vs 69.9 ± 13.0, inflated by wrap fragments) | 27 vs 29.5 ± 6.1 (all words 49 vs 37.5 ± 6.5) | No excess |
| Small scans (`grid_key`, `lag5_position`, `lag_by_length`, `word_index_poly`, `lag5_len10_words`, `segment_stats`) | — | small shifts | Unchanged |

**The lag-6 affine side scan (`lag5_affine.txt`) moved the most.** The relation is c_(i+6) = 24 − 2·c_i (mod 29), counted
on within-word pairs:

| Quantity | Old | New |
|---|---|---|
| Pairs obeying | 77 | 80 |
| Expected | 43.7 | 44.5 |
| z | +5.04 | +5.32 |
| Look-elsewhere P over 8 lags × 812 relations (1,000 shuffles) | 0.013 | **0.005** |
| Split-half replication: mean held-out z (70 directed splits; shuffle null +0.01 ± 0.29) | +0.54 (P 0.035) | **+1.44, about 4.9 sd (0 of 200 shuffles)** |
| Splits in which it is the half-best relation | 20% | 44% |

The relation is positive in all eight sections. The three new obeying pairs are in 0.15, from words rejoined across page
breaks.

Caution: three pairs moved the replication statistic a lot, because the relation sits near the top in each half and small
changes decide whether it is the half-best. So this is a lead that got stronger, not a finding. A follow-up should fix the
relation in advance and test it on new splits, with planted controls and candidate mechanisms. One example: a
lag-6 ciphertext feedback c_(i+6) = p_(i+6) − 2·c_i + k makes the relation hold exactly when the plaintext rune is
A (index 24). A pure version of that model is excluded, because it would light up every constant b, not just one.

## Tests

- `tests/test_crib.py`: 83 one-rune words over 28 runes, ᚳ never alone.
- `tests/test_families.py`: 2,896 word starts, in-word doublets 63 of 10,060, z5 3.73.
- `tests/test_restart_columns.py` already checks that the word units equal `lp.word_spans`; it passes with both changes.
- Full suite after regenerating the exports: 136 tests OK. All 21 skips are GPU tests (no CuPy or CUDA on the laptop).

## Not rerun, and why

- **Campaigns that scored with word lengths:**
  - the phpmt, prngx stage-A and hashscan dictionary sweeps;
  - the dsearch m = 1 and m = 5 runs;
  - the Phase 4 crib solver, including `work/tmp/apply_crib.py` (`work/tmp/phase4/crib_apply.json`).

  The 32 seams touch about 1% of LP2's words. A true key would lose a few words' worth of score; it would not be
  excluded. In the crib solver, a word with no dictionary fit becomes a wildcard (−9 per rune). So the seam fragments
  would cost a true key about 0.3 per rune, against the 1.65 per rune that separated true from wrong keys in its
  controls. Those negatives stand.
- **Earlier logs and PR notes** (phase 3-9 logs, `docs/prs/`) keep the numbers of their time. `PLAN.md`'s fact paragraphs
  were corrected in place, with the old values noted.
