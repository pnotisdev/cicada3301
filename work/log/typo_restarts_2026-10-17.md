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

PENDING_CONTROLS

## Results

PENDING_RESULTS
