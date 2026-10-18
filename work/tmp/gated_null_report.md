# Corrected gate for the lag-6 gated-null statistic — measurement report

Date: 2026-10-19. Script: `work/tmp/gated_null_gate.py` (reimplemented from scratch;
`work/independent/*` read as data only, never imported or executed). Results dump:
`work/tmp/gated_null_results.json`. Nothing in LP2 was screened. No commit made.

> **STATUS CAVEAT (read first).** This run was stopped by the delegating agent on
> budget. All numbers below were measured by the *last completed full run*, whose
> plant window was the first 300 runes of the **concatenated solved plaintext in
> section order 0.0, 0.1, ...** (A Warning + first ~150 Welcome runes, plaintext IoC
> 1.8202) — NOT the task-specified window `lp.KNOWN[1][1]` first 300 runes
> (Welcome, IoC 1.6702). The fix (section order `[1,2,3,4,5,6,16,17,0]` in
> `window_spans`) is applied in the script but was **not re-run**. Every mechanism
> measured here is structural (DP arcs, null layer, skip redraws) and will persist
> for the Welcome window, but the *exact* margins/S-values must be re-measured with
> one ~2-minute re-run of `python work/tmp/gated_null_gate.py` before any number is
> quoted for the record. Directional corroboration on the true Welcome window
> exists from the independent review (their bigram/value-gated variant: true-offset
> vs +1 neighbor margin −0.3 nats at n=300 on the totient stream), which supports
> the FAIL verdict below.

---

## 1. Model and DP derivation

**Cipher (skip rule, kscreen model 0, q = 0.81).** A plaintext letter `p` at key
pointer `j` encrypts to `y = (p + mult*k[j]) mod 29`. If `y` equals the previous
*ciphertext* rune, the draw is rejected with probability `q` (a hidden redraw: the
pointer has already advanced and the same `p` is redrawn at `j+1`); otherwise it is
accepted. One ciphertext rune therefore consumes `1 + (#rejections)` key values.

**Null layer.** At word-interior lag-6-eligible positions only
(`j - word_start >= 6` in ciphertext coordinates), with a FIXED prior
`q_null = 0.028`, the rune is a keyless null: it consumes no key value, has no
letter likelihood (scored at the prior), and two nulls are never adjacent (the
`f` flag below). Word spans follow the nulledge L-line convention — the L line is
the *ciphertext* word lengths including nulls; here it is derived from
`lp.word_spans` on the plant window, inflated by the planted nulls, and shared
between plant and decoder.

**Decoder arcs** (enumerating the skip rule exactly). From pointer `j` at
ciphertext `c` with previous rune `prev`:
* direct read: `p = c - mult*k[j]`, next pointer `j+1`, log-prob `0`, or
  `log(1-q)` when `c == prev`;
* rejected-read chain: first draw at `j` was rejected (`y == prev`, log-prob
  `log q`), which fixes `p = prev - mult*k[j]`; the same `p` is redrawn at
  `j+1, j+2, …`; each further draw equal to `prev` is a rejection (`log q` each)
  and the chain accepts where the draw equals `c` (log-prob `0`, or `log(1-q)`
  when `c == prev`, which also branches the chain). Arc `(used+1, p, Σlog q +
  accept-log)`.

**DP state** `(j, f)`: key pointer, previous-output-was-null flag. Transitions per
position `i` with `elig = (i - starts[i] >= 6)`:
* null: if `elig` and `f == 0` (and, in the gated variant, `c_i == (24 - 2*c_{i-6})
  mod 29`): weight `log(q_null)`, state `(j, 1)` — pointer unchanged;
* letter: for each arc `(nj, p, w)`: weight `log(1 - q_null·[elig]) + w + log P(p)`,
  state `(nj, 0)`, with `P = English rune unigram` in the language model and
  `P = 1/29` in the uniform model.

**Letter model (documented choice).** English rune unigram = add-one-smoothed
relative frequencies over the committed Emerson corpus converted to runes with
`lp.word_to_key` (the `work/sim.py:23-32` construction, reimplemented here);
uniform model = `1/29`. (The reviewed code used an English bigram and a
value-gated null; the task specifies unigram and an ungated prior — deviations
documented, see §7.)

## 2. The statistic

Summed-path evidence ratio (no maximizing, no beam — the anti-overfit design):

```
S(o) = ln Z_eng(o) - ln Z_unif(o),
Z_m(o) = Σ over all null/letter paths of
         Π_pos [ null:   q_null                       (eligible, f=0)
                 letter: (1 - q_null_if_eligible)·P_arc·P_m(letter) ]
```

The null prior is FIXED at 0.028 (never fitted), so a random key cannot inflate it;
letters are summed (not maxed) over paths. Exact forward pass (log-sum-exp) over
`(j, f)`; a separate Viterbi pass (max + backpointers, same model) reports the best
alignment and null flags.

**Oracle check (self-validation):** with `q = 0, q_null = 0` the statistic must
equal the closed form `Σ_i log(29·P(p_i))`. Measured `113.189247` vs closed form
`113.189247` — exact to 6 decimals. The DP is correct.

**Plant (forward coins).** Welcome-style window, key offset 3, skip q = 0.81,
nulls Bernoulli(0.42) at eligible gaps (never two adjacent), value
`(24 - 2*c[j-6]) mod 29` (echo form) or uniform (second plant); a value coin is
drawn in both kinds so the coin/redraw streams are identical across null kinds.

## 3. Part 1 — does the DP recover the plant?

Plant A (totient key, echo nulls): 310 ciphertext runes (300 letters + 10 nulls),
30 eligible positions, 13 hidden redraws, first redraw at position 49.

| quantity | value |
|---|---|
| S at true offset | **+89.236 nats** |
| letter accuracy (Viterbi) | **296/300 = 98.7%** |
| planted-null recall | 6/10 = 60.0% |
| null precision | 6/9 = 66.7% |
| recovered plaintext IoC | 1.8299 |

The DP genuinely recovers the plant's alignment (98.7% letters; the review's
bigram variant got the same 98.7%). Null identification is partial: the ungated
prior costs nothing in the S-ratio, so the Viterbi trades a few false nulls for
alignment fixes.

## 4. Part 2 — the CORRECTED gate, per plant

Gate: `S(true)` must exceed **every** neighbor offset ±1..3 **and** every
matched-null decode (12 uniform random keys × the same 7 offsets on the plant's
own ciphertext — the "12 random-key plants, uniform keys, same settings" null
side; a full random-key plant cannot be a null because its own true offset
legitimately aligns English) by ≥ 10 nats.

| plant | S(true) | max neighbor | nbr margin | null-side max | gate margin | verdict |
|---|---|---|---|---|---|---|
| A echo nulls | 89.236 | 80.834 (o4) | **8.40** | −117.766 | 8.40 | **FAIL** |
| A2 uniform nulls | 90.529 | 82.200 (o4) | **8.33** | −117.802 | 8.33 | **FAIL** |
| B no nulls | 91.623 | 82.910 (o4) | **8.71** | −129.936 | 8.71 | **FAIL** |

Per-offset scores (true offset o3):
* A: o0 12.75, o1 13.66, o2 47.67, o3 89.24, o4 80.83, o5 50.52, o6 5.57
* B: o0 −148.16, o1 −146.87, o2 50.25, o3 91.62, o4 82.91, o5 52.07, o6 13.55

The null side (C2) is passed by ~+200 nats everywhere; the **binding constraint is
the +1 neighbor o4**, ~8.4 nats below the true offset — under the required 10.
All three totient plants **FAIL the corrected gate**.

**12 full random-key plants** (uniform keys, same settings — extra false-positive
probe): S(true) 90.3…96.6; neighbor margins
5.32, 8.91, 9.87, 8.95, 2.67, 4.23, **16.01, 13.94, 1.14, 10.88, 12.38, 14.53**
→ **5/12 pass the full gate, 5/12 pass the neighbor-only criterion**. The ≥10-nat
threshold is below the redraw/null valley for ~40% of random keys — the review's
"coin flip" finding reproduces with the corrected neighbor rule.

## 5. Part 3 — neighbor separation on the totient key vs n (the degeneracy)

| n | first redraw | S(true) | best neighbor | margin | o2 margin |
|---|---|---|---|---|---|
| 300 | 49 | 89.24 | o4 (+1) | **8.40** | 41.57 |
| 600 | 49 | 176.92 | o4 (+1) | **8.37** | 41.62 |
| 900 | 49 | 255.78 | o4 (+1) | **8.36** | 41.63 |

**The margin is constant in n** — it is set by the early prefix, not by window
length. Seed sweep at n=300 (first redraw pos / margin / binding neighbor):
12345 → 49 / 8.40 / o4; 31337 → 40 / 8.31 / o4; 424242 → 40 / 8.34 / o4;
20004 → 41 / 21.09 / o2; 771 → 41 / 20.71 / o2.

**Mechanism (measured, two distinct realignments):**
1. **+1 shift (o4):** the ungated null is a *free* re-synchronization tool — the
   `log(q_null)` weight cancels in the S-ratio, so the decoder places one null at
   the first eligible position (~6–8) and erases the +1 error, paying only the
   early garbage positions ≈ 8.4 nats, n-independent. The review's value gate was
   load-bearing: it blocked exactly this realignment (a null could only fire where
   `c_i == 24−2c_{i−6}`, p ≈ 1/29).
2. **−1 shift (o2):** cannot be fixed by nulls (nulls move the pointer backward);
   it realigns at the first hidden redraw via the rejection-chain arcs —
   the review's mechanism, confirmed: margin ≈ 0.5 nats × first-redraw position
   (21.1/20.7 nats at first-redraw 41; the review's bigram factor was ~2 nats).
   Also n-independent once n > first redraw.
3. Far shifts on the null-bearing plant recover partially because each planted
   null advances the ciphertext without the key (lagging decoders gain +1 shift
   per null); on the no-null plant the −3/−2 shifts never realign (−148 nats).

**Explicit statement required by the task: at no n ≤ 900 does the statistic
separate the true offset from its +1 neighbor by the required 10 nats on the
totient-structured key (8.40/8.37/8.36). The method is BLIND for ±1 offsets on
structured keys; more window does not help — the valley is a prefix property
(first eligible position / first redraw), not an n-scaling property.** (Numbers
from the wrong-prefix window; re-run pending for the exact Welcome-window values —
see the status caveat.)

## 6. Part 4 — null-side strength and z-scores

16 uniform random keys on the totient echo ciphertext (n=300); max statistic per
key over the settings grid:

| grid | mean | sd | min | max | z(S_true = +89.24) |
|---|---|---|---|---|---|
| A: 64 settings (8 offsets × mult{1,28} × atbash{F,T} × rho{0,0.028}, ungated) | −121.49 | 11.64 | −138.79 | −98.30 | **+18.11** |
| B: 16 settings (4 offsets × 2 rho × 2 value-gate) | −145.30 | 14.97 | −165.87 | −117.77 | **+15.67** |

**The statistic has real power against random keys: z ≈ +15.7…+18.1**
(margin S(true) − null mean ≈ +210 nats). The review's bigram variant reached
z = +45.9; the unigram model is weaker but still far beyond any null threshold.
The null layer's own contribution is NOT detectable as an S-increase
(A +89.24 vs no-null B +91.62 — the ungated prior is symmetric), consistent with
the review's +205.50 vs +205.70.

## 7. Verdict and power statement for screening LP2

* **Corrected gate: FAIL on all three totient plants** (margins 8.33–8.71 < 10,
  at every n ≤ 900); **PASS on 5/12 random-key plants** (seed-dependent). The
  corrected gate therefore refuses to authorize an LP2 screen on the totient
  stream — which is the correct, conservative outcome, but it means the gate
  cannot certify power for the screen's actual key family.
* **At n = 300 the statistic would detect** (5σ) any alignment whose S exceeds
  the random-key null max by ~58 nats; the true plant clears this by +210 nats.
  Its effective detection power is **offset-resolution-limited, not
  null-limited**: it can tell "some alignment of this structured key" from random
  keys at z ≈ 18, but cannot tell the true offset from its +1 neighbor
  (valley ≈ 8.4 nats < 10 required), so a screen flag would land at a
  mis-identified offset — exactly the failure mode the independent review warned
  about. **No LP2 screening with this statistic is authorized by these
  measurements.**
* Deviations from the reviewed model, documented: unigram (task) vs bigram;
  q_null = 0.028 (task) vs 0.0272; ungated null prior (task: "scored as a fixed
  prior, no letter likelihood") vs value-gated — the ungated prior re-opens the
  free +1-shift realignment that the value gate had been suppressing, which is a
  measured consequence of the task's own specification.

## 8. Files

* `work/tmp/gated_null_gate.py` — full reimplementation (streams, plant, DP,
  forward/Viterbi, gate, n-sweep, seed sweep, null-side grids).
* `work/tmp/gated_null_debug.py` — far-offset mechanism diagnostics (null-free
  decoder, direct-only decoder, Viterbi inspection).
* `work/tmp/gated_null_results.json` — all measured numbers from the last full run.
* This report: `work/tmp/gated_null_report.md`.

**Pending re-run** (one command, ~2 min, when budget allows):
`python work/tmp/gated_null_gate.py` after the `window_spans` section-order fix —
reports the same tables for the task-specified Welcome first-300 window
(IoC 1.6702).
