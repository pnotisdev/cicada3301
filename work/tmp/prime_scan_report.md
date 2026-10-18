# Prime-space residual sweep — audit: rune order / arithmetic domain

**Question:** does any affine within-word lagged relation on LP2 (sections 0.7–0.15, segments 7..15,
12,956 runes) live in the Gematria-Primus **prime** domain (or a mixed index/prime domain) rather than
in the GP **index** order?

**Method.** Within-word pairs `(c_i, c_{i+d})` from `lp.word_spans(toks, runes)`. For each setting
`(a, b) ∈ 0..28 × 0..28` the residual `r = (coord(c_{i+d}) − a·coord(c_i) − b) mod 29` is pooled and
scored with Pearson chi-square of the 29 bin counts vs uniform (`e = n/29`). Domains (coordinate of the
first / second rune of the pair):

| domain | coord(c) | coord(c') | residual | lags |
|---|---|---|---|---|
| PP (prime→prime) | PRIME mod 29 | PRIME mod 29 | `P29[c'] − a·P29[c] − b` | 1..8 |
| IP (index→prime) | rune index | PRIME mod 29 | `P29[c'] − a·c − b` | 5, 6 |
| PI (prime→index) | PRIME mod 29 | rune index | `c' − a·P29[c] − b` | 5, 6 |

**Two structural facts shape the reading of every table.**
1. `chi2(a,b)` is invariant under `b` (b permutes the 29 bins), so the 841 settings collapse to **29
   distinct chi2 values per lag** (one per `a`); the reported maximum is over `(d, a)` with `b` free.
2. `a = 0` is the marginal of the second rune's coordinate, not a relation. The P29 marginal is
   non-uniform (chi2/n ≈ 0.41–0.45 pair-weighted: PRIME mod 29 has collisions — residues 2, 3, 13, 14
   are shared by 3/3/2/2 runes — and pair positions weight runes unevenly). The null (200 within-section
   shuffles, same word cuts) preserves rune multisets, so its per-lag max is the same marginal plus
   multinomial fluctuation. The real-vs-null-max comparison is therefore **insensitive by
   construction**; the decisive test is the **same-a z-score** (real chi2 vs the null distribution at
   the *same* `a`), which cancels the marginal and isolates joint (x,y) structure.

Null: 200 within-section shuffles per dataset (seed `0x13315C01`); p99 = 99th percentile of the
per-shuffle max. Confirmation pass: fresh 2000-shuffle nulls (seed `0xC0F1`) at the best-z settings.
Code: `work/tmp/prime_scan.py` (pure Python 3.12, ~5 min); machine-readable `work/tmp/prime_scan_results.json`.

---

## 1. LP2 prime domain (PP), lags 1..8 — required table

| lag | pairs | top (a, chi2) | chi2/n | null max | null mean | null p99 | real vs null max |
|---|---|---|---|---|---|---|---|
| 1 | 10060 | (0, 4152.1) | 0.413 | 4423.8 | 4253.9 | 4421.6 | below (0.94×) |
| 2 | 7247 | (0, 3051.0) | 0.421 | 3288.7 | 3068.8 | 3277.9 | below (0.93×) |
| 3 | 4882 | (0, 2002.4) | 0.410 | 2281.5 | 2077.2 | 2231.3 | below (0.88×) |
| 4 | 3237 | (0, 1354.0) | 0.418 | 1610.5 | 1385.6 | 1539.8 | below (0.84×) |
| 5 | 2105 | (0, 953.5) | 0.453 | 1106.3 | 911.4 | 1051.9 | below (0.86×) |
| 6 | 1290 | (0, 540.4) | 0.419 | 702.6 | 568.0 | 679.9 | below (0.77×) |
| 7 | 731 | (0, 328.4) | 0.449 | 434.9 | 334.9 | 429.8 | below (0.76×) |
| 8 | 388 | (0, 163.1) | 0.420 | 278.9 | 190.7 | 268.5 | below (0.58×) |

**Combined (8 lags × 29 a = 232 settings):** real max 4152.1 at (d=1, a=0) vs null max 4423.8,
mean 4253.9, p99 4421.6 → the real maximum sits *inside* the null distribution. Every lag's winner is
`a = 0`, i.e. the marginal, not a relation.

**Joint structure (a ≠ 0), same-a z-scores:**

| lag | best a≠0 | real chi2 | null mean | null sd | z | p (200 sh.) | 2000-shuffle confirm |
|---|---|---|---|---|---|---|---|
| 7 | 2 | 59.9 | 32.1 | 8.7 | 3.19 | 0.0100 | z = 3.24, p = 0.0035 |
| 5 | 1 | 91.4 | 54.6 | 13.8 | 2.67 | 0.0299 | z = 2.88, p = 0.0085 |
| 1 | 10 | 114.0 | 72.8 | 15.8 | 2.61 | 0.0149 | — |
| 4 | 3 | 68.3 | 42.8 | 10.1 | 2.53 | 0.0299 | — |
| 6 | 11 | 60.3 | 39.1 | 10.3 | 2.06 | 0.0348 | — |

Look-elsewhere over the 224 a≠0 settings: P ≈ 1 − (1−0.0035)²²⁴ ≈ **0.54** — pure chance.

## 2. Mixed domains (lags 5, 6)

| domain | lag | pairs | top (a, chi2) | null max | null mean | null p99 | best a≠0 z (2000-sh. p) |
|---|---|---|---|---|---|---|---|
| IP | 5 | 2105 | (0, 953.5) | 1106.3 | 911.4 | 1051.9 | a=24, z=2.60 (p=0.0160) |
| IP | 6 | 1290 | (0, 540.4) | 702.6 | 568.0 | 679.9 | a=14, z=2.10 (p=0.0295) |
| PI | 5 | 2105 | (6, 40.8) | 60.8 | 44.6 | 56.1 | a=6, z=1.71 (p=0.0565) |
| PI | 6 | 1290 | (26, 52.0) | 60.6 | 44.9 | 57.4 | a=26, z=3.22 (p=0.0045) |

All real maxima are below their null maxes. Look-elsewhere over the 56 settings of each mixed domain:
IP P ≈ 0.59, PI P ≈ 0.22. (PI d=6 a=26, i.e. a = −3 mod 29, is the most extreme setting anywhere in the
audit and is still within chance.) **No mixed-domain reading beats its null.**

## 3. Positive control — planted relation (power proof)

Plant: plaintext of the keyed sections 1, 5, 16 (`lp.KNOWN[i][1]`), concatenated (words never cross
sections), then within each word `prime(c_{i+6}) = (1·prime(c_i) + 0 + PRIME[p_{i+6}]) mod 29` with
uniform random rune heads at word positions 0..5; `c_{i+6}` = lowest-index rune whose PRIME has the
target residue (deterministic tie-break).

**Information loss of the prime alphabet (two channels, not one):**
- *Ambiguity* (the anticipated channel): the target residue maps to >1 rune → 10/73 = **13.7%** of
  planted positions (plant), 37/235 = 15.7% (supplementary plant).
- *Unrepresentability* (not anticipated by the task): PRIME mod 29 covers only **24 of the 29**
  residues ({4, 6, 26, 27, 28} never occur), so 12/73 = **16.4%** (plant), 39/235 = 16.6% (supplement)
  of targets cannot be written at all. Deterministic completion: nearest representable residue
  (circular distance, lower residue on ties) → these positions carry a residual error.

**Residual reproduces the plaintext primes:** exactly at 61/73 = 83.6% of planted positions (196/235 =
83.4% supplement); where the recovered residue is unambiguous, the recovered rune equals the true
plaintext rune at **57/57 = 100%** (180/180 = 100%); overall exact rune recovery 55/73 = 75.3%
(173/235 = 73.6%).

**Detection (sweep on the plant, PP domain):**

| plant | n pairs (d=6) | chi2 at true (d=6, a=1) | chi2/n | plant null max (d=6) | same-a z | null exceedances |
|---|---|---|---|---|---|---|
| sections 1, 5, 16 (as specified) | 73 | **143.5** | 1.97 | 97.4 (mean 54.3, p99 79.2) | **13.9** | 0 / 200 |
| all 9 solved sections (supplement) | 235 | **429.3** | 1.83 | 169.4 (mean 118.3, p99 166.2) | **48.1** | 0 / 200 |

At lag 6 the true setting is the top setting in both plants (next-best a=0: 46.6 and 121.0), its chi2
exceeds the plant's own lag-6 null max by 1.47× / 2.53×, and no shuffle (0/200) reaches it at the same
setting. **Power: plant chi2/n ≈ 1.8–2.0 vs the LP2 combined null max chi2/n = 4423.8/10060 = 0.44 →
~4.2–4.5×.** (The plant ciphertext's own null max is dominated by the P29 marginal of its runes — the
same a=0 artifact described above — which is why the same-a comparison is the stated power.)

## 4. Real-data null — 'An End' ciphertext (section 16, 85 runes, 25 words)

| lag | pairs | real top (a, chi2) | null max | null mean | null p99 |
|---|---|---|---|---|---|
| 1 | 60 | (1, 53.1) | 83.1 | 57.8 | 81.1 |
| 2 | 36 | (20, 62.3) | 78.4 | 49.3 | 70.3 |
| 3 | 20 | (10, 38.0) | 98.9 | 47.7 | 81.5 |
| 4 | 9 | (16, 39.3) | 84.4 | 46.6 | 65.1 |
| 5 | 4 | (0, 39.5) | 112.0 | 45.1 | 68.5 |
| 6 | 1 | (0, 28.0) | 28.0 | 28.0 | 28.0 |

Real max 62.3 vs combined null max 112.0 → **no setting beats its null.** Caveats: with 60→1 pairs the
cell expectations `e = n/29 ≤ 2` are degenerate for Pearson chi2; the null is empirical at the same n so
the comparison stays valid but low-power. The two z>3 readings (d=1 a=1 z=3.69, d=2 a=20 z=4.56) sit
inside the 232-setting look-elsewhere budget (P ≈ 0.69). This is the expected behavior of the machinery
on real ciphertext with no planted prime-space relation.

## 5. Verdict

**No prime-space or mixed-domain affine reading of LP2 beats its null.** In every domain, every lag,
the real maximum either is the a=0 marginal (PP, IP — preserved by the shuffles, real < null max) or a
df-noise-scale value below the null max (PI, An End). The joint (a≠0) same-a z-scores — the
marginal-canceling test — top out at z = 3.24 (PP d7 a2, p = 0.0035 per setting), 2.60 (IP), 3.22
(PI d6 a26); across the 336 effective settings the expected maximum |z| is ≈ 3.3 and the
look-elsewhere-corrected P is ≈ 0.22–0.85, i.e. chance. The positive control proves the detector would
have caught the planted relation: chi2/n = 1.97 / 1.83 at the true (d=6, a=1) vs 0.44 for the LP2 null
max/n (4.2–4.5×), same-a z = 13.9 / 48.1 with 0/200 null exceedances — while LP2's within-word lag-6
prime-space sweep shows nothing above the a=0 marginal (540.4 at a=0, next-best a≠0 = 64.2).

**Answer to the audit question:** the arithmetic domain is **not** the GP prime order, and the encoder
did not mix index and prime space at lags 5–6. The GP **index order remains the working arithmetic
domain** — consistent with the known index-space within-word lag-6 echo (`c' = 24 − 2c`), which has no
prime-space counterpart. The prime-domain enciphering equation is excluded with the same rigor as the
index-domain affine/nonlinear feedback was: the negative is null-calibrated (200 shuffles + 2000-shuffle
confirmations) and power-proven by the plant.

**Caveat on the plant control:** because the solved sections are short and English words rarely exceed
6 runes, the mandated plant yields only 73 planted positions; the absolute chi2 (143.5) does not exceed
the *LP2* null max (4423.8) — chi2 scales with n (10060 vs 73 pairs). Power is therefore stated per
pair (chi2/n) and via the same-a z, and a supplementary plant over all nine solved sections (235
planted positions, z = 48.1) confirms it. The plant also exposed that PRIME mod 29 is not surjective:
16.4% of planted targets are unrepresentable — a second information-loss channel of the prime alphabet
on top of the 13.7% ambiguity rate.

## Files

- `work/tmp/prime_scan.py` — sweep, null, plant, confirmation (seeds fixed: 0x13315C01 / 0x99A55 / 0xC0F1)
- `work/tmp/prime_scan_results.json` — full per-setting results (machine-readable)
- `work/tmp/prime_scan_report.md` — this report
- `work/tmp/prime_scan_probe.py`, `work/tmp/prime_scan_brute_check.py` — API/pair-count probe and independent brute-force cross-check of the sweep winners
