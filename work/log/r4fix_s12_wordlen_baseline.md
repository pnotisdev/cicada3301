# R4 repair s12 (round 2): how strong is the word-length anomaly against honest baselines? (2026-10-24)

Nothing in LP2 is solved. Keyless: only LP2's 2,896 word LENGTHS were used (no ciphertext scored). Idea 16 of `work/laptop_review/11_next_100.md`; lead 3 / spec 4B of `work/laptop_review/08_loose_ends.md`.

## Question
`results/analysis/wordlen.txt` tests LP2 against baseline histograms as if they were exact (p 1e-28 to 1e-45). The "+1 rune in about 42-45% of multi-rune words" premise of R4's second rule rests on that. What does a test that includes the baseline's own sampling noise say, against Cicada's own solved text (739 words) and against English corpora, in two spellings, and what q does each baseline imply?

## Method
- Script `work/r4fix/s12_wordlen_baseline.py`: `python -B work/r4fix/s12_wordlen_baseline.py` (one process, numpy/scipy, below-normal priority, seed 20261024). Output `results/r4fix/s12_wordlen_baseline/summary.txt` and `results.json`; raw stdout `work/r4fix/s12_run_out.txt`. Full run: wall 1,242 s, process CPU 1,200 s. (`--quick` mode, used once, was discarded.)
- Bins: word length 1..11 and 12+ (12 bins, as `work/wordlen.py`). LP2: 2,896 words (`stats.UNSOLVED`), 83 one-rune, 448 two-rune (15.47%).
- Baselines: solved text (`lp.KNOWN`, 739 words, 2,977 runes, decrypted plaintext) and eight English corpora (Emerson, Walden, Origin of Species, KJV, Republic (Jowett), Meditations, Paradise Lost, Ethics (Elwes); `work/ref/emerson_essays1.txt`, `work/ref/corpora/*`; Gutenberg headers stripped). Spellings: `runes` = Gematria Primus, digraphs one rune, IO -> IA (as `fam_data.english`); `letters` = one rune per Latin letter.
- Two-sample test: G and Pearson chi2 of the 2 x 12 table, df 11; p by Monte Carlo from the pooled histogram (20,000 draws of both samples), so the baseline's noise counts.
- Fit: expected baseline counts B(q) = baseline histogram with a share q of eligible words lengthened by one (12+ stays 12+); G(q) = two-sample G of LP2 against B(q) (baseline size N2 enters); q = argmin on a 0.005 grid. `multi` = only words of >= 2 runes eligible (the convention of the model and the A/I oracle); `all` = every word. CI = nonparametric bootstrap, LP2 and baseline both resampled (2,000); fit p = parametric bootstrap at the fitted q (LP2* ~ Mult(2896, B(q)), baseline* ~ Mult(N2, baseline), refit, 2,000 draws).
- Extras: 8,000 contiguous English blocks of 2,896 and of 739 words per spelling (genre noise); split of the 2-rune bin by word identity in the solved text and Emerson.

## Controls
- Reproduction: chi2 42.5 (runes) and 25.8 (letters) against the solved text, 2-rune share 24.1% / 17.9%, exactly the loose-ends numbers; the old one-sample G reproduces wordlen.txt (Emerson 242.4 / 60.4, solved letters 156.6).
- **Positive P1 (the brief's design; pseudo-LP2 of 2,896 words from the solved text, +1 rune at q 0.45 in multi-rune words, baseline = the solved text; 200 draws per spelling): PASSES.** q-hat 0.449 (runes), 0.448 (letters), sd 0.025; CI covers 0.45 in 200/200 both; model accepted (p > 0.05) 200/200 (median p 0.97). Caveat: the baseline sample is the source of the pseudo text, so this is optimistic.
- **P3 (independent halves: pseudo from a random half of the solved text, baseline the other half, 369/370 words; 200 draws): fit recovers q, with a wide spread.** q-hat 0.439 sd 0.075 both spellings; CI covers 0.45 in 171/200 (runes), 175/200 (letters); model accepted 126/200 and 130/200 (63-65%, nominal 95%: the plug-in parametric bootstrap with a 370-word baseline is too strict).
- **P2 (independent genres: Walden + q 0.45 against the Emerson baseline; 200 draws): FAILS, reported as is.** q-hat 0.482 (runes), 0.491 (letters), a bias of +0.03 / +0.04 over the truth; CI covers 0.45 in 160/200 and 137/200; the model is accepted in 0/200 (median p 0.002). Cause: Walden and Emerson differ in word-length histogram by more than the 2,896-word sampling noise, and the fit p assumes the baseline is the source's exact distribution. So every fit p against a large other-genre baseline (rows below) is not a calibrated test of the +1 model, and q-hat carries an extra genre uncertainty of about +-0.05 that the CIs omit. Nothing was tuned.
- **Null N2a (Emerson 2,896 vs an independent Emerson 739, 400 draws):** rejects at 0.05 in 0.052 (runes) and 0.052 (letters), KS uniformity p 0.54 / 0.85: the two-sample machinery is calibrated.
- **Null N2b (solved text against itself):** pseudo from the solved histogram vs a fresh 739-word resample, 400 draws: rejects 0.022 (runes), 0.045 (letters), KS p 0.49 / 0.31 (uniform). Against the very same 739-word sample p is conservative (0 rejections, KS p about 0): a shared baseline cannot give a uniform p.
- **Null N1 (the brief's: Emerson pseudo-LP2 of 2,896, no insertion, against the solved text; 200 draws): does NOT reject at the nominal rate.** Runes: 28/200 = 14% (nominal 5%); letters: 189/200 = 94.5%. Not a machinery fault (N2a): the solved text is a poor stand-in for Emerson, mainly in letters. Fitted q on the same pseudo texts: 0.006 (runes), 0.100 (letters).
- N3 (pseudo from the solved text, q = 0): q-hat mean 0.011 / 0.010, 53% exactly at 0 (the grid cannot go below 0).

## Result
Two-sample (unfitted: "LP2 has the baseline's distribution") and the fitted +1 model; `multi` unless marked. MC p floor is 5e-5.

| baseline x spelling | G (chi2), df 11 | p two-sample | fitted q [95% CI] | min G, fit p | baseline 2-rune share (LP2 15.47%) |
|---|---|---|---|---|---|
| solved text, runes (739) | 41.7 (42.5) | < 1e-4 (asym 1.8e-5; Pearson 1.3e-5) | 0.360 [0.270, 0.450] | 4.9, 0.65 | 24.1% |
| solved text, letters (739) | 28.0 (25.8) | 0.0045 (asym 0.0032; Pearson 0.0069) | 0.215 [0.130, 0.315] | 12.8, 0.077 | 17.9% |
| Emerson, runes | 234.1 (214.9) | < 1e-4 | 0.425 [0.375, 0.470] | 15.9, 0.099 | 27.1% |
| Emerson, letters | 58.2 (57.2) | < 1e-4 | 0.195 [0.135, 0.255] | 23.9, 0.005 | 20.0% |
| Walden, runes / letters | 234.5 / 73.7 | < 1e-4 | 0.390 [0.335, 0.440] / 0.135 [0.075, 0.200] | 63.4 / 57.1, < 0.001 | 24.9% / 18.5% |
| Origin of Species, runes / letters | 365.8 / 191.3 | < 1e-4 | 0.405 [0.355, 0.455] / 0.110 [0.040, 0.185] | 147.9 / 182.2, < 0.001 | 26.3% / 19.3% |
| KJV, runes / letters | 394.1 / 183.9 | < 1e-4 | 0.420 [0.375, 0.465] / 0.155 [0.100, 0.210] | 144.2 / 154.0, < 0.001 | 25.8% / 16.5% |
| Republic, runes / letters | 264.3 / 79.4 | < 1e-4 | 0.435 [0.385, 0.480] / 0.205 [0.145, 0.265] | 25.3 / 38.5, 0.008 / < 0.001 | 27.7% / 20.5% |
| Meditations, runes / letters | 192.1 / 104.5 | < 1e-4 | 0.365 [0.315, 0.415] / 0.205 [0.150, 0.265] | 26.9 / 57.8, 0.002 / < 0.001 | 24.6% / 20.2% |
| Paradise Lost, runes / letters | 123.1 / 103.3 | < 1e-4 | 0.195 [0.140, 0.260] / 0.000 [0.000, 0.010] | 84.2 / 103.3, < 0.001 | 19.1% / 14.6% |
| Ethics, runes / letters | 387.2 / 196.0 | < 1e-4 | 0.485 [0.445, 0.525] / 0.335 [0.275, 0.390] | 40.2 / 80.9, < 0.001 | 30.3% / 24.1% |

(Against the large baselines the fit p is not calibrated across genres, see P2; read q-hat, not that p, from those rows. The `all`-words variant gives q within 0.00-0.06 of `multi`, except Walden letters 0.200; on Emerson runes it fits worse, G 36.1, p 0.001.)

**Does the anomaly survive against Cicada's own text?**
- **In runes (digraphs one rune, Cicada's own spelling): yes, but at p about 1e-5, not 1e-45.** G 41.7, 2-rune share 24.1% vs 15.5% (z -5.5). The +1 model fits (p 0.65) with **q 0.36 [0.27, 0.45]**, not the 0.425 found against Emerson; 0.45 sits on the upper edge. No English block among the 8,000 (8 corpora) has a 2-rune share as low as 15.47% (Paradise Lost, the lowest, spans 17.2-21.2%), so the low 2-rune share in runes is real against English; but the whole-histogram distance is not unusual against genre variation (LP2's G to the equal-weight average English histogram is exceeded by 19.6% of English 2,896-word blocks).
- **In letters (no digraph runes): no.** Against the solved text G 28.0, p 0.0045; but (i) the same test rejects an Emerson sample with no insertion 94.5% of the time (N1), so a 739-word letter histogram is not a calibrated stand-in for English; (ii) LP2's G to the solved text (28.0) is below the median of 2,896-word English blocks against it (86% of blocks are farther away), and the solved text is nearer to LP2 than 75% of 739-word English blocks; (iii) 13.6% of English 2,896-word blocks (KJV 29%, Paradise Lost 79%) have a 2-letter share <= 15.47%. Letters-spelled q 0.215 [0.13, 0.315] (fit p 0.077) is a weak preference for any insertion.
- Baseline noise alone: with a 739-word English block as baseline, the fitted q has median 0.40 [0.155, 0.525] in runes and 0.20 [0.00, 0.40] in letters: a 739-word baseline cannot pin q to better than about +-0.19.

**One-rune accounting.** LP2's 83 one-rune words: with the multi-rune convention the baseline rate predicts 87.3 (Emerson; z -0.46, as in loose-ends) or 105.8 (solved text, whose A/I rate is 3.65%; z -2.2 with LP2's Poisson noise only, **-1.0** with the baseline's own noise). The phase 60 figure "83 vs 50.6, z +4.55" is the all-words convention at q 0.42 on Emerson (reproduced: 50.6, +4.55); under it the solved text predicts 65.6 (z +2.15) in runes. Fits using `all` do no better than `multi` (G 36.1 vs 15.9 on Emerson runes; 4.8 vs 4.9 on the solved text). No one-rune excess exists under the convention the other fits use.

**Where the 2-rune deficit sits (solved text).** The 2-rune bin is 178 of 739 words (698 per 2,896 words vs LP2's 448, a deficit of 250): THE 46 (180 per 2,896, 26% of the bin; 2 runes but 3 letters), TO 24, IS 22, WE 19, OF 9, AN 9, BE 8, HE 8, IT 7. The seven named words OF TO IN IS IT BE AN are 81 words = 11.0% of all words and 45.5% of the rune bin (61.4% of the letter bin); in Emerson 13.0% of words, with THE 25% of its rune bin. So the deficit sits where English is most frequent, trivially, because the bin consists of those words. Removing THE alone from the solved baseline gives G 18.1 (p 0.085) against LP2 in runes, removing the seven function words G 13.2 (p 0.29); in letters the shortfall is 69 words (13% of the bin; 517 expected vs 448), well inside the seven function words (317). LP2 carries no word identities, so which words are missing is not observable; these removals are post hoc and any removal of about 250 of the bin's 698 tokens would fit about as well.

## What it means for R4's second rule
The "+1 rune in about 42-45% of multi-rune words" figure is the Emerson-in-runes fit (0.425 [0.375, 0.47]), the upper part of the honest range. Against Cicada's own text in runes q is 0.36 [0.27, 0.45]; spelled letter-for-letter it is 0.2 [0.13, 0.32] and not clearly different from none. Across corpora q-hat runs 0.20-0.49 in runes (0.36-0.44 for the five prose corpora other than Ethics) and 0.00-0.34 in letters. So the second rule is supported only as "LP2 has fewer 2-rune words than English written with digraph runes (p about 1e-5 against Cicada's own text), consistent with q roughly 0.25-0.45", not as a measured 0.45 and not as evidence of a mechanism. nu 0.45 in the engine and the arc budgets sit at the upper end; 0.30-0.35 (and about 0.2 under letter spelling) are the other points to cover. This is a statistics-only statement: short words have other explanations (a plaintext register with fewer function words, or no digraph runes) that this test cannot separate from insertion.

## What this does NOT exclude
Any insertion mechanism (q summarises a histogram shift; it does not test R4); length-dependent insertion; a different language or register of LP2's plaintext (the solved text is 739 words of imperative, aphoristic prose; the corpora differ from it and from each other by more than their sampling noise, see P2); the one-rune accounting under other conventions. P2 failed, so the fit p of the large-baseline rows is not calibrated and q-hat has an unquantified genre bias of about +0.03-0.04.

## Files
`work/r4fix/s12_wordlen_baseline.py`, `results/r4fix/s12_wordlen_baseline/summary.txt`, `results/r4fix/s12_wordlen_baseline/results.json`, `work/r4fix/s12_run_out.txt` (stdout of the final run), `work/r4fix/s12_run_err.txt` (empty), this log.

## Pause and CPU
The first full run was stopped when the owner paused the work (during the P1 controls; no output kept); after the pause the same script was rerun unchanged to completion. CPU: final run 1,200 s (20 CPU-min) plus the discarded quick run (about 1 min) and the stopped run (a few minutes, not measured), so about 25-28 CPU-min in total; one worker, below-normal priority, no other process touched.
