# Human review checklist: immutable v2/backward.rs

Nothing in LP2 is solved. This is a source/invariant review, not authorization
to launch a campaign. The E3' common-null proof failed; the v2 scoring engine
itself passed its prior exactness/parity gates. No Rust source was changed here.

## Probability semantics

- Input c,key,sign,q,channel are fixed; the code must NEVER average unknown key
  values as iid when calculating a particular cell's likelihood.
- Each output consumes one plaintext. Hold may consume zero keys; retry consumes
  more keys without drawing another plaintext. Coin spends its extra slot even
  if the initial collision is kept. Missing coin/redraw slots are failure.
- Outputs are unconditional successful-output masses. Final probabilities can
  sum to less than1; the missing mass is failure, NOT conditioned away.
- The ordinary first output has no predecessor check. This invariant is a model
  assumption, not valid automatically for windows cut at a first-rune repair.
- L and U use the SAME key/channel/end semantics. U is iid uniform plaintext,
  not automatically the same common ciphertext null at every offset.

## Sparse representation (`cls`, `get`)

- At layer i>=1 pointer j means NEXT slot; rune label is the previous plaintext.
- Slot0 ordinary label: c[i-1]-s*k[j-1] when j>0.
- Possible second label: hold c[i-2]-s*k[j]; spend c[i-2]-s*k[j-1];
  coin-kept c[i-2]-s*k[j-2]. Requires i>=2 and valid key indices.
- Skip and coin-redraw outputs use the last attempted key and hence the ordinary
  label. At most two labels per pointer, not an arbitrary two-state beam.
- Q is a missing-label sentinel, not a real rune. Labels must be distinct;
  identical labels are merged as one state. No doubled probability from labels.
- `get` returns negative infinity for an absent label. This is safe only if every
  nonzero incoming edge has class closure. E0 verifies closure and the last-event
  proof explains it. A future development build could assert this invariant;
  do not silently introduce new kernels that violate it.

## Backward boundaries and all offsets

- b and u initialize to log1 at final layer n, including j=m. Consuming the final
  available key on the final output is SUCCESS.
- In every nonterminal layer, j=m has log0: a finite key cannot emit again.
- n=0 returns log1 for every offset including m. n>0 at offset m is impossible.
- Results at o<m are log pi[p0]+B_1(o+1,p0), p0=c[0]-s*k[o]. Uniform result
  substitutes -log Q. The code must not sum or maximize different start offsets.
- Four working arrays a,b,u,v only swap after an entire output layer. Each new
  layer is cleared first. Sparse rune labels rt,rs swap at the same boundary.

## Edge generation and capacity

- For y!=previous, there is one ordinary noncollision p=y-s*k[j], j->j+1.
- Initial-collision plaintext p=previous-s*k[j] is fixed for every repair/retry.
- Hold/spend: repeat observed => keep weight1-q with advance1; nonrepeat
  observed => uniform replacement weightq/(Q-1), advance0/1 respectively.
- Coin: require coin slotj+1; kept repeat goes to j+2. Redraw requiresj+2 and
  matching emitted y, destinationj+3. A redrawn repeat is allowed.
- Six-edge stack array is sufficient: skip5 repeat has at most six accepted
  attempts; if y differs, only ordinary plus the first matching retry can occur.
  Other kernels need at most two. New kernels need a capacity review.
- Raw FFI mode is unchecked beyond branches: its catch-all implements skip5.
  The Python adapter's whitelist is therefore a required ABI precondition.
  Do not call this C ABI with unvalidated modes, lengths, dimensions or buffers.
- Additional caller preconditions: pi, cipher and key must be ONE-DIMENSIONAL;
  cipher/key values must be integers before conversion. The current adapter
  checks L.shape but lacks explicit pi/c/key dimensionality checks and casts
  rune inputs to int32. Malformed multidimensional or fractional inputs could
  therefore be silently misinterpreted. Existing gate inputs obey the contract;
  general-purpose input hardening would require a separately authorized wrapper,
  not a silent edit to immutable engine.py.

## Uncapped skip tails

- `ends[j]` is the first unequal-key position or m. It must be strictly >j.
- Nonrepeat output: collision path traverses all equal-key attempts, weight
  q**(ends[j]-j), then emits only if the first unequal key yields y. Ending at
  m contributes failure, not a fabricated output.
- Repeat output: `tail[j]` is the kept-collision suffix plus q*tail[j+1] ONLY
  within the same-key run. Iterate j right-to-left so same-layer tail[j+1] exists.
  Language transition is multiplied once outside this retry sum.
- skip5 instead enumerates attempts0..5, with attempt5 unconditional. This is
  the frozen channel cap, not an approximation to uncapped skip.

## Numeric invariants

- Float64 only; all states store logs. No beam, early abort or shared-row scale.
- `add` handles negative infinity before exp/log1p, preventing inf-inf NaNs for
  zero-mass branches. The largest local term anchors each state's addition.
- q=0 makes logq negative infinity; q=1 makes log(1-q) negative infinity.
  The uncapped run multiplier is always >=1, avoiding 0*(-infinity).
- Log LM zeros are allowed. Negative/unnormalized/nonfinite LM inputs are rejected
  by engine.py. Uniform U has one state because its next plaintext is independent
  of the preceding rune label, not because the key is fresh or random.
- S is defined only when U>0. L=0,U>0 means negative infinity; 0/0 must be rejected,
  not NaN-ranked as a hit. First/end boundary tests cover these cases.
- Cross-platform bit identity is not promised. v2 parity bound was1e-9 nats;
  decisions near a numeric threshold need a recorded ambiguity/recheck policy.

## What the engine gates do NOT prove

- A valid likelihood ratio under each U_cell does not give a union bound under
  another common null W. Key-value independence of hold/spend does not eliminate
  short-suffix exhaustion. This session supplies exact counterexamples.
- Wrong offsets of positive plants can be aliases, not null trials. An observed
  exceedance count is not deterministically bounded by its expectation.
- Searching only the planted stream cannot measure stream identification among
 1439 streams. That label must be marked conditional/provided, not recovered.
- A source mismatch (held Cicada vs Emerson training) does not measure arbitrary
  other-language power. Sanity nulls matching doublets do not fix their full law.
- A queue and candidate summary must check gate validity, not merely read T_n.
  Tier2 top50 rankings are not candidates or leads, even if displayed as text.

## Review disposition

No known DP error was demonstrated here; normalization and finite exhaustion
behave as specified. The failed invariant is the proposed INTERPRETATION of
those probabilities as a common-null, per-cell tail guarantee for all offsets.
Changing that statistic/null contract requires a new authorized protocol; do
not patch backward.rs to conceal or renormalize the failure probability.
