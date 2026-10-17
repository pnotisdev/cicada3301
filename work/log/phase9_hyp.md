# Phase 9: the untested hypotheses of docs/HYPOTHESES.md (2026-10-17, afternoon)

Hypotheses, predictions and kill rules were written in `docs/HYPOTHESES.md` before anything ran. Each test has a planted
(positive) control and a null. Nothing in LP2 is solved.

## Engine additions (work/kscreen/src/main.rs), both opt-in

- **G lines (self-key guard).** A windows file may give a window's index in the keystream (`G <index>`); the decoder then
  never deciphers rune i with key index g + i. Without it, LP2's own ciphertext used as its key decodes to c_i - c_i = 0
  (IoC 29.00 on seg0.8 a few runes behind itself); with it the same decodes stay at noise (1.17 at most, from decodes that
  the screen aborts at 150 runes and never counts). Unit test: `work/tests/test_hyp_exports.py`.
- **clock= (clocked key pointer, H3).** After each rune the pointer moves on by g instead of 1: 1 + index, the Gematria
  prime, or prime - 1, of the cipher rune (c1, cp, ct) or of the deciphered rune (p1, pp, pt). Default behaviour is
  unchanged: 19,200 decodes of the old and new engine compared identical (`trace`, 4 streams x 150 offsets x 8 windows x
  2 signs x 2 models). Verification now decodes as far as the key reaches when a stream is shorter than the window
  (decimated streams, prime clocks) instead of skipping it.
- Both are refused by the CUDA port (`gpu.py`), so their campaigns run on the CPU only.

## kscreen-hyp: H3 decimation, H4 text numbers, H5 ciphertext as key, H6 deep constants (desktop, CPU, 1 h 03 min)

Inputs (`work/kscreen/export_hyp.py`): every stream must keep LP2's flat IoC (predicted IoC under English plaintext at most
1.002 + 1.6/n).

| family | streams kept | screened |
|---|---|---|
| H3: the 1,447 library streams decimated by d = 2..29 (key pointer stepping d terms) | 16,071 of 40,516 | library_hyp, mults 1, 28 |
| H4: prefix sums of rune indices and of prime values, solved LP plaintext (2,977 runes) and Self-Reliance (41,235), forwards and reversed | 8 of 16 (all per-word sums fail: common words repeat the same sum) | library_hyp |
| H6: pi, e, phi, sqrt2 digits in base 29 from positions 10^6 and 3,409,933 (= 3301 x 1033), 20,000 each | 8 of 16 (base-10 digits fail: 10 values) | library_hyp |
| H5: LP2's ciphertext read backwards | 1 of 5 (Welcome's and the concatenated keyed solved ciphertexts fail) | library_h5, all 28 multipliers |
| H5: LP2's own ciphertext forwards (long-lag ciphertext autokey, keys from another section), guarded | 1 | library_self, all 28 multipliers |

Controls (`work/kscreen/hyp_selftest.py`, results/kscreen/hyp_selftest.txt): 12/12 planted windows (a decimated totient,
a Self-Reliance prefix sum, a deep pi block, LP2 backwards under multiplier 7) are their window's best hit at the exact
offset, IoC 1.60-2.06; a planted ciphertext autokey (L = 500) is found at offset 0 through the guarded self-key path (1.78;
1.87 over 1,197 runes); the guard check passes (29.00 without, 1.17 with).

| screen | decodes | best IoC (300 runes) | matched null |
|---|---|---|---|
| library_hyp (H3, H4, H6) | 895 M | 1.3747 (seg0.12, sha256-chain of "command your own self", decimated by 2) | 1,300 random streams, 816 M decodes: 1.3553 |
| library_h5 | 5.6 M (28 multipliers) | 1.3068 | (same null, 145 x more trials: conservative) |
| library_self | 5.6 M (28 multipliers) | 1.2654 | (same) |

Verification (whole section, or as far as a decimated key reaches; same keystream at 20 random offsets): **0 of 15, 0 of 8,
0 of 8** keep IoC >= 1.40; the hits fall to 1.05-1.33 (a 274-rune stretch for a d = 28 stream) and none beats its own
keystream's random offsets by 0.15. **Verdict: H3 (constant decimation), H4, H5 and H6 are negative.**

## kscreen-clock: H3 clocked key pointer (desktop, CPU, 1 h 07 min)

The 1,447-stream library at every offset on the 8 sections, both signs, both anti-repeat models, with the pointer moving on
by g after each rune. Controls (`work/kscreen/clock_selftest.py`): 18/18 planted windows (three per clock) found with
re-decode at the truth 1.71-2.02 (plaintext clocks resynchronise, so they are found within about 60 offsets of the truth),
and the unclocked screen is blind to the c1 plants (best 1.218).

| clock | window | decodes | library best | matched null (300 random streams) | verified |
|---|---|---|---|---|---|
| c1: 1 + index of the cipher rune | 300 | 236 M | 1.3171 | 1.3184 | 0 of 15 |
| p1: 1 + index of the deciphered rune | 300 | 236 M | 1.3074 | 1.3178 | 0 of 15 |
| ct: prime - 1 of the cipher rune | 150 | 172 M | 1.6115 | 1.5934 | 0 of 15 |
| cp: prime of the cipher rune | 150 | 172 M | 1.5934 | 1.5726 | 0 of 15 |
| pt: prime - 1 of the deciphered rune | 150 | 172 M | 1.5934 | 1.6038 | 0 of 15 |
| pp: prime of the deciphered rune | 150 | 172 M | 1.6868 | 1.6193 | 0 of 15 |

On 150-rune windows the 1.40 rule does not apply: the random-stream null itself reaches 1.57-1.62, and the library tails
match the null's (all the top hits are hash streams). Verification decides: the best pp hit falls from 1.687 to 1.260 over
294 runes (as far as a 20,000-value stream reaches at about 44 values per rune; a true key keeps about 1.8), against 1.156
for the same keystream at random offsets. **Verdict: negative for all six clocks.** Limit: with the prime clocks a
20,000-value stream covers only the first ~450 runes of a key, so only keys starting within the first ~9,000 terms of a
library stream are screened, on the first 150 runes of each section.

## H8 null on collision (`work/null_insertion.py`, `results/analysis/null_insertion.txt`)

Prediction: an encryptor that emits a random null instead of a doublet inserts 360 / 12,956 = 0.0278 runes per rune.

| base | no nulls | nulls at 0.0278 (0 fitted) | rate fitted |
|---|---|---|---|
| English in runes | G 222.7 | G 182.3 | 0.100 (0.076-0.124), G 144.0 |
| English in runes, TH as T+H | G 56.0 | **G 40.1** | **0.039 (0.021-0.059)**, G 38.7 |

Control: 100 samples of 2,928 words with nulls at 0.0278 refit to 0.0271 +- 0.0088; the 95% interval covers the truth
in 94/100. **Verdict: alive** by its kill rule (the predicted rate is inside the fitted interval and improves the fit
from G 56 to 40 with no free parameter), but still not a fit (p = 3e-5).
**It hides nothing from the keystream screens:** a decoder that never skips stays aligned (it reads the null with key j,
one garbage rune, and the real rune with key j + 1). Three English windows enciphered with the totient stream under H8
(39 nulls in 1,236 runes) are found by the unchanged kscreen at their exact offsets, IoC 1.71 / 2.02 / 1.58. Every
earlier kscreen negative therefore also holds under H8.

## H9 two-time pad between sections (`work/pad_reuse_power.py`, `results/analysis/pad_reuse_power.txt`)

Two English sections enciphered with the same random pad from the same start, each with its own skips, against pairs
whose second section used another pad, 40 replicates per size:

| runes per section | band statistic: power at 5% | Viterbi path statistic: power at 5% |
|---|---|---|
| 400 | 0.38 | 0.15 |
| 1,500 | 0.05 | 0.10 |
| 3,000 | 0.42 | 0.12 |

**Verdict: undecidable.** Reuse gives 6.2% coincidences against 3.45%, about 0.025 nats per rune, while each skip costs
about 3.6 nats and comes every ~36 runes, so the alignment cannot be followed. A negative from either test would mean
nothing; open lead 3 (drift-aware key reuse between sections) is closed as not decidable from the ciphertext.

## H10 small 29-state machines (`work/state_machines.py`, `results/analysis/state_machines.txt`)

c_i = E(x_i, S_i), S' = F(S, x, c): 512 updates F (linear a*u(S) + b*x + g*c + d with u in {S, prime(S), prime(S)-1, S^2},
coefficients in {0, 1, 2, 28}, plus four product forms) x 9 rules E (x = c - t, c + t, t - c, t in {S, prime(S),
prime(S)-1}) x 29 start states, decoded on every section with a free start state (so a machine running across sections is
included), scored by IoC (blind to any substitution of the plaintext).

- LP2: best mean IoC over the 8 sections 1.0259 (best single section 1.0516). Shuffled LP2 (two replicates): 1.0169 and
  1.0152. The top LP2 rows are all one machine, S' = +-c, which decodes to the step c_i - c_(i-1); its IoC of about 1.024 is
  the known missing doublets (`phase9_families.md`), which shuffling destroys. Nothing else stands out. **Verdict: null.**
- Controls: three random machines without skips and one ciphertext-driven machine (S' = g*c + d) with the anti-repeat skip
  are recovered as the best of all 4,608 (F, E) pairs at mean IoC 1.76. A machine with memory under the skip rule decodes
  to 1.21 only: the first pass has no skip model.
- **Second pass with the skip modelled** (`work/state_machines.py --viterbi`, `results/analysis/state_machines_skip.txt`): the
  3,528 machines with memory, a Viterbi over the 29 states per machine with the skip transition taken exactly where it is
  consistent (the first try equalled c_(i-1)), scored by English rune log-likelihood (English text -2.954 nats per rune,
  uniform runes -4.233). LP2's best path -3.9417 per rune; random runes with LP2's avoid-repeat rate -3.9435; three planted
  machines with memory under the skip rule are each the best of all 3,528, at -3.00, -3.08 and -3.09. **Verdict: null for
  the whole family, with and without the anti-repeat rule.**

## Keyless checks prompted by the outside lists (2026-10-17)

- **Fixed-point rune** (multiplicative keys, prime algebras with an absorbing element, literal pass-through): rune x
  position in word (initial, medial, final, one-rune word) over LP2, chi^2 74.1 on 84 df, p 0.77, largest |z| 2.13.
  Control: a 1.5-6% English letter (Self-Reliance) on one 458-count row adds chi^2 30 (L) to 1,010 (TH). Excluded.
- **The 256-byte payload as a permutation or S-box:** 161 distinct values (random bytes: 161.8); rows / columns of the
  16 x 16 layout all-distinct 10 / 12 (random: about 10). Byte-random.
- **The S echo as "-SELVES":** 3 of the 11 within-word lag-5 S-S pairs end on a word-final S, against 4.4 expected. Dead.
