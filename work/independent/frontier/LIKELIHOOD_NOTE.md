# Audit precision: wrong stated local prior is not automatically an invalid ratio

This is algebra, not a decoder run, power measurement or LP2 result.

## 1. The declared local model

The later prototype sets `Q_NULL = .028` and plants with `NULL_RATE = .42` at
eligible positions (`work/tmp/gated_null_gate.py:78-80`). In `forward`, eligibility
sets `chance`; the ordinary log-weight is computed before inspecting the
previous-null flag, and a null gets log(chance) without a value probability
(`work/tmp/gated_null_gate.py:264-290`). Its report calls this a fixed-prior
summed-path evidence ratio (`work/tmp/gated_null_report.md:68-85`).

If the intended local process chooses a null with probability rho and its value
uniformly among Q runes, the null likelihood is rho/Q for the observed value.
The ordinary mass, when a null is allowed, is 1-rho. When the preceding-null
flag forbids another null, the ordinary mass must be one, not 1-rho.

At a fresh eligible position, summing the prototype's ungated weights over all
possible next output values gives

    (1-rho) * 1 + Q*rho = 1 + (Q-1)*rho.

For Q=29 and rho=.028 this is 1.784, not one; after a null the allowed outgoing
mass is .972. These identities refute the *declared local Bernoulli prior*, not
the possibility of using the resulting quantity as a calibrated score.

A deterministic value-gated null has emission probability one at its single
allowed value, not 1/Q. The earlier `work/independent/echo_nulls.py:118-157`
implements a different model and sets the ordinary mass from the flag-dependent
chance. Do not transfer the later ungated defect to it.

## 2. Important qualification: a common global normalizer can cancel

Fix an exogenous output layout and horizon. Suppose all ordinary cipher/letter
kernels are normalized, the key is effectively inexhaustible, and the ungated
null can emit any rune. For a particular allowed nonadjacent-null mask z, let
m(z) be its number of nulls and E the number of eligible positions. Integrating
the prototype's weights over all output and plaintext values gives

    w(z) = (Q*rho)^m(z) * (1-rho)^(E-m(z)),

with eligibility constraints on z. The sum Z_layout = sum_z w(z) depends on the
layout/horizon but not on whether plaintext has the English or uniform law.
Consequently it is possible to normalize BOTH model masses by the SAME global
Z_layout. Their log ratio is unchanged. Equivalently, the score can correspond
to a different, globally conditioned hard-core null-mask prior, rather than
the claimed online Bernoulli(rho) process. At a single fresh eligible site with
no future constraints, its normalized null chance would be

    Q*rho / (1-rho+Q*rho) = 203/446, approximately .45516,

not .028. Longer horizons and the no-adjacency constraint alter that marginal.

Thus **the one-step mass identity alone is NOT a proof that the log ratio is
mathematically invalid under every reinterpretation**. It is a proof that the
stated local prior/generative interpretation is wrong. Calibration and reported
power apply only to the actual implemented score/model. Finite-key exhaustion,
end conditions and layout generated jointly with insertions require additional
normalization checks; do not assume the common-normalizer argument covers them.

## 3. Consequence for the review

Distinguish these claims:

- wrong claimed local emission/prior: supported by code and algebra;
- no possible probabilistic interpretation of the score: NOT established;
- revised normalization necessarily rescues power: unknown;
- neighboring offset ambiguity means no family/decoded-text detection is possible:
  NOT established; it needs a different, selection-matched detection gate.

The report and audit explicitly use this narrower conclusion. The algebraic
qualification was recorded before final delivery; no statistical gate was retried.
