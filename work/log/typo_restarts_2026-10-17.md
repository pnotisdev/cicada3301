# Key restarts at typographic marks (2026-10-17, laptop)

Idea from cicadanotebook.com, sessions 17-20 and 55-63 (`work/log/research_cicadanotebook_2026-10-17.md`): maybe LP2's key
restarts at its typographic marks. The site tried only 3 streams. **Nothing in LP2 is solved.**

Tools: `work/typo_restarts.py` and the runner campaign `kscreen-typo`. Outputs: `results/kscreen/library_typo.tsv`,
`null_typo.tsv`, `library_typo_verify.txt`, `typo_plants.txt`, `typo_known.txt`, `typo_pooled.txt`, `typo_summary.txt`.

## What was already covered

- `kscreen-restarts`: the 1,439-keystream library restarted at each red heading and each page start. Negative.
- `restart_columns.py`: a key-agnostic test of identical restarts at every segment, page, paragraph, line, clause and word.
  Negative; rerun today with the corrected word units.

## New restart points (22 windows, `work/typo_restarts.py export`)

| Group | Windows (section@first rune) | Source |
|---|---|---|
| Numbered list of 0.14 | items 1-5 alone (754, 893, 984, 1082, 1178; 91-139 runes); the whole list from its opening 10-dot mark (754-1307); the text after the closing mark (1307) | numerals #1-#5 in the transcription; the 10-dot brackets from the site's session 18 |
| Three-dot marks | 0.8@588, 0.9@1036, 0.11@1355, 0.14@1149, 0.15@1689 | images 22, 28, 37, 55, 63; checked with `work/tmp/hyp/page_seam_dots.py` |
| After a red heading | 0.7@13, 0.8@16, 0.8@122, 0.8@823, 0.12@16, 0.13@19, 0.13@1443, 0.14@1471, 0.15@8, 0.15@3017 | `work/tmp/phase4/red_runs.json`; consecutive red runs merged. The windows of `kscreen-restarts` start AT the heading |

The key offset in each window is free, so a counter that restarts from an item's label (for example key index label − 1 + j)
is covered by the same scan.

## Controls

- **Known answers** (`typo_known.txt`): the solved sections that have three-dot marks keep their key running straight
  through them.

  | Section, mark | Restart the key at the mark | Skip one key position | Continuous key |
  |---|---|---|---|
  | Second koan (0.5, FIRFUMFERENFE), before rune 110 | 209 of 209 runes wrong | 209 of 209 | 0 wrong |
  | Second koan, before rune 286 | 28 of 33 wrong | 33 of 33 | 0 wrong |
  | An End (0.16, primes − 1), before rune 19 | 61 of 66 wrong | 65 of 66 | 0 wrong |

  This matches cicadanotebook.com's session 62, so Cicada's own solved pages argue against restarts at these marks.
- **Matched null** (`null_typo.tsv`): 1,439 random keystreams of length 20,000, the library's exact size, on the same 22
  windows and settings. Under 250 runes a window must beat its own null maximum; the 1.40 rule does not apply.
- **Plants** (`typo_plants.txt`): three library keys (primes − 1, pi digits, a SHA-256 stream) planted into English twins
  of exactly each window's scored length, under the anti-repeat rule (keep 0.18), both signs and both models.

  | Windows | Recovered at the true offset | Above their window's null maximum |
  |---|---|---|
  | 282-300 runes | 44 of 45 | **45 of 45** |
  | 81-139 runes | 13 of 21 | 9 of 21 |

  The screen has full power on the long windows and little on the short ones.
- **Shared-key plants** (`typo_pooled.txt`): one key restarted at every list item, at the same offset (d = 0) or at offset
  + k (d = 1, a counter from the item label). 3 of 3 pass: the true key lands in 4, 5 and 5 of the 5 items' top-2,000
  lists, and 3 are needed.
- **A first pooled design failed its own control and was dropped.** It decoded the first 30 runes of each item directly,
  with no skip handling. The anti-repeat skips derail a direct decode after about 20 runes, so a planted key scored
  IoC 1.27, below the 1.34 that 20 random streams reach.

## Results (`results/kscreen/typo_summary.txt`)

- **Long windows** (the list as one unit from its opening mark, the text after the list, the five three-dot marks, eight
  heading tails; 282-300 runes):
  - best library IoC 1.285-1.359, against matched null bests of 1.293-1.425;
  - the library beats its null in 5 of 22 windows, by at most 0.037;
  - no window reaches 1.40.

  **Negative, with full power** (45 of 45 plants clear the null).
- **Short windows** (the five list items alone and the tails of the headings at 0.13@1443 and 0.14@1471; 81-139 runes):
  - the library best is at or below the window's null best in all 7;
  - verification (`library_typo_verify.txt`) re-decodes the top 15 hits. All are in the 81-96-rune windows, and 0 beat
    their window's null best (2.09-2.22 there).

  `verify.py`'s own "CANDIDATE" flag compares a hit with random offsets of its own keystream. A window this short passes
  that by chance, as the desktop's review noted (398d24b), so `typo_summary.txt` now judges hits against the window's null.

  **Negative but weak** (9 of 21 plants clear the null).
- **One key restarted at every list item** (`typo_pooled.txt`; the desktop's independent count in
  `results/analysis/typo_shared_key.txt` agrees): no (keystream, multiplier, model, offset) appears in 3 or more of the 5
  items' top-2,000 lists, library or null, for d = 0 or 1; chance expectation 3·10⁻⁵. **Negative, with power.**

**Verdict:** within the 1,439-keystream library, LP2's key does not restart at the numbered list, its brackets, the five
three-dot marks or right after the red headings. The single list items and the two heading tails under 140 runes remain
weakly tested. Restarts with keys outside the library (keywords, other generators) are not covered here. Nothing in LP2
is solved.
