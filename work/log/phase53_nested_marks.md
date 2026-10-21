# Phase 53: do LP2's marks work as paired brackets? (feasibility only)

Plan: list every non-rune mark per section (0.0-0.15, `work/ref/lp_verified.txt`), ask whether any type pair
(open, close) has equal counts, proper nesting, alternation, or is LP2-only; shuffle null (1,000 per section).
Output: `results/analysis/phase53_nested_marks.txt`; script `work/phase53_nested_marks.py`.

Numbers
- Mark types in all 16 sections: word `-`, clause `.`, line `/`, paragraph `&`, page `%` (plus numerals in 0.2, 0.6,
  0.9, 0.10, 0.14 and the 0.15 payload block, which are data, not marks). No mark type exists only in LP2.
- `&` is the section terminator: one per section in 0.0-0.6 and 0.7, 0.9-0.12 (one at the end). Extra `&` in LP2
  only in 0.8 (at rune 119, 812; 3 total), 0.13 (1433 and 1524; 2), 0.14 (1468, 1589; 2), 0.15 (2474, 3008, 3316 + 1 inside
  the payload block). `%` (page) counts: 1-7 per section, pages ~260-270 runes long in 0.7-0.15.
- Pairing '%' open / '&' close: nesting holds in 9/9 LP2 sections and 4/6 solved ones, equal counts in 1/9
  where one of each), strict alternation 1/9. Null (shuffle): nesting held in 72% of shuffles (67% solved), so
  no signal; equal counts are invariant under shuffling, so "equal" is a property of the counts alone, and counts
  differ (e.g. 0.8: 5 `%` vs 3 `&`; 0.11: 7 vs 1).
- Pairing '&' open / '%' close: never nested (a `&` comes after a `%` in every section).

Verdict: no. LP2 has no candidate open/close pairs. Its mark inventory equals the solved sections'; `&` ends a
section (plus a few mid-section ones in 0.8, 0.13-0.15) and `%` starts a page, so any key stack would have
to use the fixed-length pages (open = page start, close = next page start gives a flat restart, which earlier phases
already tested) or the 0.8/0.13/0.14/0.15 mid-section `&` as a single level-2 interval. A test would need 2 levels and
those ~7 interval positions; no further levels are marked in the text.

Not excluded: brackets carried by the ciphertext itself (rune values) or by word/clause lengths rather than by marks;
the transcription might have dropped marks.
