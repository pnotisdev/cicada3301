# Phase 54: where does the within-word lag-6 relation live? (2026-10-22)

Scope: LP2 sections 0.7-0.15 (12,956 runes). **Nothing in LP2 is solved.** Goal: pin down the encryptor's repair rule behind c' = 24 - 2c (mod 29) at lag 6 (`obs-lag6`).

Plan: reuse the word segmentation of `work/families/fam_data.py` (`lp.word_spans`); reproduce the 80 sites; then cut them by (1) word length / position, (2) source rune c, (3) neighbours of the site, (4) section / page,
(5) doublets and S in the window, (6) the solved sections 0.0-0.6 as negative control. Null = 10,000 within-word rune shuffles (word lengths and memberships kept); exact independence expectation alongside.
Script `work/phase54_lag6_dissect.py` -> `results/analysis/phase54_lag6_dissect.txt`. One-sided p; 33 cuts looked at, Bonferroni p < 0.0015 (floor of the null: 0.0001).

Numbers
- Reproduced: 1,290 within-word pairs at lag 6, **80 hits**; independence expectation 44.49, shuffle null 45.68 +/- 6.48, z +5.30, p 0.0001.
- Word length (pairs: hits vs null): 7: 8 vs 8.0 (no excess); 8: 21 vs 11.0 (p 0.003); 9: 20 vs 8.3 (p 0.0002); 10-11: 21 vs 12.8 (p 0.018); 12+: 10 vs 5.5 (p 0.05). Words of exactly 7 runes (pair = first and last rune) carry no excess; longer words carry about 1.6-2.4x.
- Start position in the word: 0: 33 vs 20.1 (p 0.0035); 1: 19 vs 12.0; 2: 12 vs 6.6; 3: 6 vs 3.8; 4+: 8 vs 2.0 (p 0.0014). Every position is elevated by a similar factor (1.5-4): no single fixed slot. Pair ending on the word's last rune: 32 vs 20.1 (p 0.008), the same as position 0 because both counts are one pair per word of 7+ runes.
- Source rune c: 27 different c occur, max 7 (W->I), null max 4.6 (p 0.04, not significant over 33 cuts). Sum of squares 298 vs 118 (p 0.0002) is the "few pairs repeat" effect: the same (c, c') pair recurs (e.g. TH->L 5, O->E 5, T->ING 5), c = S 3 (null 1.5), c' = S 3 (null 1.3). No single c dominates.
- Neighbours (14 cuts, hit sites only): c[i+1] == c' 6 vs 1.6 (p 0.006; not significant over 33 cuts), c[i+2] == c 4 vs 1.25 (p 0.04), c[i+2] == c' 5 vs 1.6 (p 0.02), c[i+4] == c 4 vs 1.25 (p 0.04). c[i+5] == c' (the rune before c') is 1 vs 1.6 and c[i-1], c[i+3], c[i+7] show nothing. No neighbour relation survives the correction, and the one that marks c' as a repaired collision (c[i+5] == c') is absent.
- Sections: hits/sites 0.7 6/79, 0.8 6/106, 0.9 10/184, 0.10 0/0 (9 runes), 0.11 13/178, 0.12 5/100, 0.13 11/152, 0.14 9/154, 0.15 20/337: chi2 28.8 vs 7.4 (p 0.0005, passes the correction); per-pair rates run from 0 (0.10, no pairs) and 3-5% (0.8, 0.12, 0.9, 0.7) to 6-7% (0.11, 0.13, 0.15), so the rate is not uniform across sections. Pages: chi2 117 vs 51 (p 0.0005, 55 units, mostly small counts); pages with >= 4 hits: 0.7 p1 (4), 0.13 p3 (4), 0.15 p6 (6). Mild clustering; the section/page null is the within-word shuffle, which keeps each word, so this is not a consequence of word length mix.
- Doublet and S overlap: 2 hits in the 49 windows holding a doublet (null 1.8, as expected); 18 hits in the 294 windows holding an S (null 10.2, p 0.0125, not significant over 33 cuts).
- **Negative control** 0.0-0.6 (2,797 runes, 221 pairs): 11 hits vs null 7.45 +/- 2.61 (independence 7.71), z +1.36, p 0.13: no excess.

Verdict
- The relation is not tied to one fixed position: every start position 0-4 shows 1.5-4x, both ends of the word alike. It looks like a lookback (c' relates to the rune 6 back), a per-pair event at rate about 0.027 / pair, in words of 8+ runes.
- Two things stand out: 7-rune words (pair = first and last rune) carry no excess (8 vs 8.0, 216 pairs) while 8-9-rune words carry about 2x (p 0.003, 0.0002, both pass the correction); and nothing marks c' as a repaired collision (c[i+5] = c' is 1 vs 1.6).
- Simulation spec for a later session: for every in-word position j >= 6 (0-based) with probability q = 0.027 set c[j] = 24 - 2c[j-6] (mod 29); the check is that this yields the 2x in 8-9-rune words AND the null in 7-rune words. The unconstrained rule gives 7-rune words their share too, so it already fails that check on the numbers above: a rule needs to treat the (first, 7th) pair of a 7-rune word differently, or 7 vs 8-9 is chance (p of 8 vs 8.0 given 2x expected 16: about 0.02, one cut). Hypothesis only, not a result.
- Not tested: whether the excess depends on the encrypted (plaintext-side) word, since LP2's word boundaries are ciphertext separators.
