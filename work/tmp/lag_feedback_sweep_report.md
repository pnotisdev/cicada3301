# Affine lag-feedback autokey sweep over LP2 — final report

**Scope:** test whether LP2 (segments 0.7–0.15, 12,956 runes) obeys, within words,
`c_i = (p_i + a*c_{i-d} + b) mod 29` for `i >= d` inside each word (positions `0..d-1`
of each word are free heads), i.e. the residual `r_i = (c_i - a*c_{i-d} - b) mod 29`
IS the plaintext at every in-word position `i >= d`.
Swept: word scope, `d ∈ {1..8}`, `a ∈ {1..28}`, `b ∈ {0..28}` → 8·28·29 = **6496 settings**,
plus the parent-requested scope extension (4 pair scopes × `d ∈ {5,6}` × all (a,b)) and a
cheap nonlinear d=6 extension.

**Verdict:** EXCLUDED for English-plaintext autokey at lags 1–8 (see §10), with one formal
rule-trip: `(d,a,b)=(1,1,0..28)` beats the null max but is a digram artifact, not a
decryption (residual IoC 1.025 vs English ≥ ~1.7; the plant's IoC was 2.89; the signal is
dominated by LP2's adjacent-equal-rune avoidance and extends across word boundaries).

**Headline numbers:** top LP2 chi2 = **275.17** at (1,1,*) vs null max **72.28**;
plant chi2 = **164.16** (recovered 73/73 plaintext runes exactly);
next best non-artifact setting = **64.86** at (6,27,*) — the lag-6 echo itself — below the null max.

---

## 0. Lemmas (stated here because they shape every table)

- **L1 (b-invariance):** for fixed (d,a) and pair scope, incrementing b shifts the residual by
  −1 mod 29, so the 29-count histogram is a cyclic shift. Pearson chi2 and IoC are therefore
  IDENTICAL for all 29 values of b. Effective multiplicity of the sweep is 8·28 = **224**;
  the 6496 b-rows are emitted for spec compliance, and the null max over 6496 settings equals
  the null max over 224 (d,a) settings. (The null calibration therefore absorbs the
  look-elsewhere correctly: each shuffle sweeps the same 6496 settings.)
- **L2 (alphabet-permutation invariance):** chi2 uses only the count histogram of r, so any
  fixed permutation of the rune alphabet (rotation, Atbash, …) merely relabels r and leaves
  chi2 and IoC unchanged. **No alphabet search is needed for this test.**

## 1. Data and tools

- Segments from `work/lp.load_segments()` (`work/lp.py:37-68`): indices 7..15 are LP2
  (rune counts 729, 1145, 1729, 9, 1894, 1021, 1524, 1589, 3316 → 12,956; 2896 words).
- GP alphabet = 29 runes, `work/lp.py:17-24` (`lp.GP` index order: 0=ᚠ F, 15=ᛋ S, 24=ᚪ A,
  18=ᛖ E, 16=ᛏ T, …); `lp.LATIN` maps index→letter.
- Word cuts: `work/lp.word_spans(toks, plain)` (`work/lp.py:156-173`) — bare `\n`/`%` are
  typographic wraps, real boundaries at `-`, `.`, `&`, numerals. Word scope runs in this
  sweep are asserted identical to `word_spans` positions.
- IoC: `work/lp.ioc` (`work/lp.py:107-115`), normalised (random=1, English ~1.7–1.9).
- Scope extension separators: word = `' ' . & #`; clause = `.` only; linepage = `\n %` only;
  all = any consecutive pair inside a section (section `$` boundaries always hard).

## 2. Step 1 — echo replication (sanity check, PASSED)

Within-word pairs via `word_spans` on LP2 (reference: `results/analysis/echo_position.txt`):

| relation | pairs | hits | expected (n/29) | excess | z (binomial) | reference |
|---|---|---|---|---|---|---|
| lag 6, c' = 24−2c mod 29 | **1290** | **80** | 44.48 | +35.5 | +5.42 | 1290, 80, 44.9, +35.1, z +5.16 (`echo_position.txt:21-22`) |
| lag 5, c' = c | **2105** | **104** | 72.59 | +31.4 | +3.75 | 2105, 104, 72.9, z +3.65 (`echo_position.txt:3-4`) |
| lag 5, (S,S) | 2105 | **11** | 2.50 | +8.5 | +5.37 | 11, 2.4, z +5.86 (`echo_position.txt:13-14`) |

Counts match the repo exactly (the small expected-value deltas are n/29 vs their shuffle
means, e.g. 44.48 vs 44.9). Sanity check passed — no discrepancy, sweep proceeded.

## 3. Step 2 — sweep on LP2, word scope, d 1..8 (6496 settings)

Top distinct (d,a) settings (chi2 and IoC are b-invariant, L1):

| rank | d | a | chi2 | IoC of r | note |
|---|---|---|---|---|---|
| 1 | 1 | 1 | **275.17** | 1.0246 | first-difference histogram; see §8 |
| 2 | 6 | 27 | 64.86 | 1.0286 | = lag-6 echo c'=24−2c (p=0 branch), below null max |
| 3 | 4 | 24 | 47.51 | 1.0060 | |
| 4 | 4 | 16 | 44.46 | 1.0051 | |
| 5 | 7 | 2 | 43.67 | 1.0215 | |
| 6 | 7 | 16 | 43.67 | 1.0215 | |
| 7 | 8 | 13 | 43.41 | 1.0398 | |
| 8 | 4 | 14 | 42.53 | 1.0045 | |
| 9 | 6 | 4 | 41.98 | 1.0108 | |
| 10 | 2 | 20 | 41.84 | 1.0019 | |
| 11 | 5 | 16 | 40.63 | 1.0060 | |
| 12 | 1 | 19 | 39.78 | 1.0012 | |

Special hypothesis-pinned settings:
- (6,27,24) = the lag-6 echo as the enciphering equation: chi2 **64.86** (< null max 72.28).
  The echo's +35.5/1290 excess is exactly the p=0 (rune F ≈ 2.7%) branch — a real but small
  effect that this sweep correctly shows does NOT clear the bar.
- (5,28,1) = the lag-5 S-pin linear condition (1−a)·15−b ≡ 0: chi2 **28.39** (pure null).

## 4. Step 3 — null calibration (200 within-section shuffles, same word cuts, same 6496 settings)

Word scope (per-shuffle max over d 1..8 × a 1..28, = max over 6496 by L1):

- **null max = 72.28**, mean = 53.85, 99th pct = 67.74.

Per scope-lag combo (each with its own 200-shuffle null; `n` = pair count):

| scope | d | n | top chi2 | null max | null mean | null p99 |
|---|---|---|---|---|---|---|
| word | 5 | 2105 | 40.63 (a=16) | 62.17 | 44.80 | 61.24 |
| word | 6 | 1290 | 64.86 (a=27) | 67.74 | 45.01 | 65.36 |
| clause | 5 | 12120 | 40.22 (a=8) | 60.17 | 45.37 | 59.77 |
| clause | 6 | 11954 | 39.36 (a=14) | 62.34 | 45.18 | 61.48 |
| linepage | 5 | 9989 | 49.08 (a=11) | 64.31 | 45.14 | 62.43 |
| linepage | 6 | 9398 | 39.46 (a=24) | 62.29 | 45.38 | 59.88 |
| all | 5 | 12911 | 44.17 (a=11) | 61.34 | 45.49 | 59.93 |
| all | 6 | 12902 | 36.82 (a=15) | 65.48 | 45.12 | 63.02 |

**Extension verdict: no scope-lag combo beats its own null max** (all top chi2 ≤ 64.86 < 67.74),
so chains resetting at clause, line/page or never are excluded too — the echo relation is
strictly word-internal as the repo already knew.

## 5. Step 4 — positive control (plant)

Planted `(d,a,b)=(6,27,24)` on the plaintext of the KEYED solved sections 1 (Welcome),
5 (A Koan FIRFUM) and 16 (An End) via `lp.KNOWN[i][1](runes(segs[i]))` (919 runes;
no single keyed solved section has ≥ 1000 runes in this checkout, so 1+5+16 were
concatenated; words never cross section boundaries). Heads = random runes
(`random.Random(3301)`).

- planted within-word lag-6 pairs: n = 73 (English words are short).
- sweep on the plant: **top setting = (6,27,b), chi2 = 164.16, IoC = 2.89** — far above the
  null max 72.28 and the correct setting.
- residual = plaintext at in-word positions ≥ 6: **73/73 = 1.000000 exact**.
- plant echo (lag 6): hits 3 vs 2.52 expected (n=73; expected excess n·28/29·f_F = +2.9 at
  tail-F frequency 4.11% — small-n noise around it; per-pair echo rate matches the LP2
  +35-per-1290 mechanism).
- per-pair strength: chi2/n = **2.2488** (= 29·Σ(p_j−1/29)² of the English tail).

**Power statement:** with 2.2488 chi2/pair, any setting whose residual is as non-uniform as
English plaintext needs n > 72.28/2.2488 ≈ **33 pairs** to beat the null max. Every lag has
n_d ≥ 388 pairs (lag 8) and lag 6 has 1290, so an English tail at any lag 1..8 would have
yielded chi2 ≈ 870–2900 — unmissable. The family is excluded at exactly this power. (The test
cannot exclude a setting whose "plaintext" is itself uniform, i.e. a further cipher layer.)

## 6. Step 5 — real-data nulls (keyed solved sections)

Sweep on sections 1, 5, 16 with their own word cuts, plus a local 200-shuffle null each
(segment 0.6 'An Instruction' is unenciphered English — `KNOWN[6]` identity rule,
`work/lp.py:331` — and was not used):

| section | runes | max chi2 over 6496 | local null max | null-like? |
|---|---|---|---|---|
| 0.1 Welcome (Vigenère DIVINITY, `lp.py:325`) | 515 | 55.87 (d=2,a=19) | 81.79 | yes |
| 0.5 A Koan (FIRFUM, `lp.py:330`) | 319 | 55.44 (d=5,a=1) | 74.00 | yes |
| 0.16 An End (primes−1, literal F at 56, `lp.py:332`) | 85 | 54.00 (d=5,a=4) | 99.50 | yes |

All three behave null-like, as required of a valid null.

## 7. Extension — head structure probe

Pooled word heads (positions 0..d−1 per word), word-initial and word-final runes, vs
200-shuffle nulls (chi2 vs uniform; df 28):

| pool | n | IoC | chi2 vs uniform | null max | deviate? |
|---|---|---|---|---|---|
| heads d=1 (=word-initial) | 2896 | 0.998 | 22.91 | 48.66 | no |
| heads d=2 | 5709 | 0.999 | 20.23 | 50.15 | no |
| heads d=3 | 8074 | 0.999 | 23.61 | 40.99 | no |
| heads d=4 | 9719 | 1.000 | 23.73 | 38.47 | no |
| heads d=5 | 10851 | 1.000 | 22.99 | 38.03 | no |
| heads d=6 | 11666 | 1.000 | 23.60 | 34.79 | no |
| heads d=7 | 12225 | 1.000 | 25.65 | 33.02 | no |
| heads d=8 | 12568 | 1.000 | 24.32 | 31.93 | no |
| word-final | 2896 | 1.002 | 33.24 | 46.66 | no |

No evidence of non-uniform "unkeyed inserted" runes at word edges — heads are uniform at
every lag.

## 8. The (1,1,0) candidate — what it actually is

Formally, per the stated decision rule (chi2 > null max AND plant passed), **(d,a,b)=(1,1,0..28)
is a CANDIDATE**: 275.17 > 72.28. It is NOT a decryption, and here is the evidence
(`work/tmp/lag_feedback_diag_1_1_0.txt`):

- **Residual is not English:** IoC of r = 1.0246 (uniform; plant IoC = 2.89, English ~1.7–1.9).
  The decoded word tails (`work/tmp/lag_feedback_candidate_decode.txt`) are junk
  ("OEIXOPHTH", "NEIWLWMIAJN", …).
- **84% of the chi2 is one bin:** r=0 (adjacent equal runes) has 63 hits vs 346.9 expected,
  z = **−15.5**, contributing ≈ 232 of 275.17. LP2 ciphertext strongly AVOIDS equal adjacent
  runes within words (63/10060 = 0.63% vs 3.45% expected).
- **It is not word-internal:** across word boundaries the same lag-1 residual has chi2 94.94
  vs its own 200-shuffle null max 58.27 (cross doubles: 23 vs 99.6 expected — same deficit).
  The per-word chain reset that defines this hypothesis family predicts a null cross
  residual; the data violate that, so (1,1) is a global digram property, not an autokey.
- **Per-pair strength is tiny:** chi2/n = 0.027 (plant: 2.249). The remaining excess after the
  r=0 deficit is spread thinly (top bins +50, +43, +34, … each contributing ≤ 7 chi2).
- Position profile decays (p=1: 103.2 → p=7+: 36.1 chi2) and is present in all sections
  (strongest in 0.15, 95.5) — consistent with a spacing/anti-repeat rule in the ciphertext
  generation, not with per-word autokey plaintext.

**Reading:** the (1,1,b) "hit" is the first-difference histogram of LP2, dominated by the
anti-double constraint. It is a genuine new structural observation about LP2 (adjacent
repeats avoided within words, and weaker across boundaries — worth recording alongside the
lag-5 equality echo and the lag-6 24−2c echo), but the affine lag-feedback model with
per-word heads fails on it: the residual is uniform, and the effect ignores word boundaries.

## 9. Step 7 — nonlinear feedback, d=6 (word scope)

r = (c_i − f(c_{i−6}) − b) mod 29, f ∈ {x², x³, x⁻¹ (0→0), 2^x, 3^x}, b swept 0..28
(chi2 again b-invariant); null = 50 shuffles × max over the 5·29 settings:

| f | chi2 |
|---|---|
| x² | 21.70 |
| x³ | 27.45 |
| x⁻¹ | 26.64 |
| 2^x | 36.22 |
| 3^x | 25.25 |

Null: max 67.60, mean 38.38, p99 67.60. Best real chi2 36.22 < 67.60 → **excluded**.

## 10. Verdict and power statement

- **Top LP2 chi2 = 275.17** (setting (1,1,0..28)) **vs null max = 72.28** (200 shuffles,
  same 6496-setting sweep) **vs plant chi2 = 164.16** (plant n=73, recovery 73/73 = 100%,
  plant IoC 2.89 vs LP2-setting IoC 1.025).
- By the letter of the decision rule, (1,1,b) is a **CANDIDATE** and is reported as such
  (see §8); its residual is uniform, not English, and the effect crosses word boundaries,
  so it is not the hypothesised per-word autokey.
- **Excluding that artifact, the affine lag-feedback family (d 1..8, a 1..28, b 0..28) is
  EXCLUDED for English plaintext** at the plant's power: any English-like residual tail
  needs only ≈ 33 pairs to clear the null max and every lag has ≥ 388. The lag-6 echo
  setting (6,27,24) itself scores 64.86 — below the null max — exactly as expected from the
  F≈2.7% p=0 branch.
- Scope extension: clause/linepage/all chains at lags 5–6 all below their own null max —
  excluded. Nonlinear d=6 (5 functions) excluded. Word heads/edges uniform at all lags —
  no inserted-rune evidence.

## 11. Files written (all in `work/tmp/`)

- `lag_feedback_sweep_report.md` — this report.
- `lag_feedback_echo_replication.txt` — step 1 counts vs references.
- `lag_feedback_sweep_top_lp2.txt` — top-10 rows + distinct (d,a) table.
- `lag_feedback_null_shuffles.txt` — per-shuffle maxima + per-combo null stats.
- `lag_feedback_scope_extension.txt` — 4-scope × lag 5/6 sweep vs per-combo nulls.
- `lag_feedback_plant.txt` — positive control numbers and power.
- `lag_feedback_an_end.txt` — real-data nulls (sections 1, 5, 16).
- `lag_feedback_head_probe.txt` — head/edge uniformity probe.
- `lag_feedback_nonlinear.txt` — d=6 nonlinear extension + null.
- `lag_feedback_candidate_decode.txt` — (1,1,0) decoded tails (junk; for the record).
- `lag_feedback_diag_1_1_0.txt` — full characterization of the (1,1,0) signal.
- `lag_feedback_run_console.txt` — console log; `lag_sweep_main.py`, `lag_diag_1_1_0.py` — scripts.

Nothing was committed.
