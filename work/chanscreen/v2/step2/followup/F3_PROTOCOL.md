# F3 analytic density correction diagnostic — frozen after F2, before F3

Post-F2 mathematical work, not a fresh power/calibration gate. No new plants,
no held-data tuning, no adopted statistic or original-code changes. Same resource
limits: <=10min/command, <=4 CPU workers (use1), no GPU. Save per-m checkpoints.

## Exact finite-hold survival factor

Let r be remaining key values, n>=2, and Dp the number of repeat transitions
among the first n-1 outputs (thus exclude the FINAL observed transition).
Bp=n-2-Dp. Given the common anti-repeat output law W, each prefix nonrepeat
independently advances with probability a=(Q-1)/(Q-1+q); otherwise it holds.
Each prefix repeat advances. First output always advances.

The key survives to the last output iff
1+Dp+Binomial(Bp,a) <= r-1. Thus

  U_hold(c;r) = W(c) * P[Binomial(Bp,a) <= r-2-Dp].

n0 has mass1; n1 has W if r>=1, else0. Nonempty at r0 has mass0. Monotonic
pointers make the final-prefix check sufficient for all earlier prefixes.
This factor is independent of key VALUES, but not of finite available length.
It gives an exact finite-end correction without any offset exclusion.

## Conservative skip5/coin factor preserving the raw S

The path that never retries/redraws and keeps each observed repeat has mass
  U_min(c) = Q^(-n) * (1-q)^D.
It consumes n slots in skip5/spend/hold; n+D in coin (extra coin slot on every
kept repeat). Therefore U_cell>=U_min whenever that particular path fits.
On W-supported observations, with A=1+q/(Q-1),
  W/U_cell <= W/U_min = A^(n-1-D).
For n0 use exponent0. Define B(c)=A^(n-1-D) and reject observations/cells not
satisfying the stated sufficient horizon. Then
  exp(S)/B(c) <= Z_L/W,
so its common-W expectation is <=1 for ANY normalized LM. This is an upper
bound, not equality; coin/skip5 with enough slots still depend on key values.
A global fixed penalty (n-1)*ln A is more conservative. Raw S is unchanged,
but threshold/cell scope WOULD change, so deployment still needs authorization.

## Fixed checks

1. Q3, keys of length0..4, offsets0..m, signs +/-1, q0,3/5,1, n0..4, all outputs.
   Independent v1 uniform-plaintext event trees for hold/spend/skip5/coin.
   Require exact finite-hold formula equality; spend W equality if n slots fit
   and zero otherwise; and the exact stated lower/density bounds for skip5/coin.
   q1 outputs with repeats are outside W support and excluded from density-ratio
   assertions, not treated as real finite scores. Record this count.
2. Float64 log-CDF implementation versus unchanged Rust U: Q29, n300/600,
   q.81, m2000, keys constant0 and cycling0..28; c cycling0..28, or the same
   sequence with each17th output replaced by its predecessor. All offsets,
   including end/failure cases; <=1e-9 nats, identical support. Save arrays.
3. Record fixed worst-case log penalties for n300/600, Q29/q.81. No inference
   about actual English power from these formula checks.

Stop on a discrepancy; preserve all partial files. F1/F2 and the original E3'
failure remain unchanged regardless of F3's outcome.
