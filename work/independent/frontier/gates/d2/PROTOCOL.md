# D2 — first, bounded composition-feasibility gate

Authorization: user approved GPT's D2 gate, then D1's first gate, each at most
2 minutes, each in its own folder. This directory is D2 only. Preparation is not
an experimental invocation. Run the frozen gate ONCE; do not overwrite its result,
replace failed seeds, enlarge the bank or retry after a timeout.

## Budget and scope

- One foreground driver invocation; external timeout 120 seconds, cooperative
  wall deadline 90 seconds including input loading and sequential engine calls.
- One computing worker: no GPU, multiprocessing, background jobs, builds, installs,
  network, campaign launcher or LP2 search. Existing h5rs is called sequentially
  as a child while the controller waits; its parity/decode commands are single-threaded.
- All new code, plants, logs and results stay in this directory. No repository
  module imports. Existing source is read as data; the tests/planter here are new.
- A passing first gate does NOT authorize the later 20-positive/199-null calibration
  or a real-data look. It is not a six-hour approval.

## Frozen choices, before seeing any gate output

1. Independently parse KSB1 and select exactly `primes^2`. Recreate the first
   20,000 primes by a fresh sieve and compare every exported key value.
   Reproduce the recorded plain-additive prefilter from the first 4,000 key values,
   both signs, and the full local Emerson rune-frequency vector; cutoff 1.003.
2. Exact small-alphabet checks of the convolution identity
   E[J_after] = 1 + (J_before-1)/L: alphabet 3, h=(1/2,1/3,1/6), all 9 length-2
   keywords. A balanced 3-letter keyword must flatten; a length-1 shift must not.
3. Eight independent frozen keyword/coin streams: periods {13,20}, anti-repeat
   models {0=skip,1=coin}, keyword clocks {attempt j, emitted-rune i}, in that
   nested order. Case index k=0..7: keyword RNG seed 78101+k, coin seed 78201+k.
   Each keyword is uniform over 29 letters; no outcome-dependent selection.
   Corpus slice starts at 6500+400*k, length 12,956, stream offset 317; prefix
   300 is the decoder test. Literal-F disabled, b=0, keep=.19, initial prev=-1.
   Long forward IoC is a measured finite-sample diagnostic, not the population formula.
4. Independent forward planter records every used key index. Oracle-alignment
   subtraction must round-trip exactly. A new key-known/keyword-known unigram
   Viterbi decoder must reach accuracy >=.95 on each 300-rune prefix, without
   being supplied the planted alignment. This is not evidence of unknown-key power.
5. Existing h5rs parity path (same decode function, not the file-reader test)
   learns an UNKNOWN keyword, at known period. No engine edits. Fixed fast engine,
   beam24/max_em5/beam_a12, abort(120,.9), first300. For EACH synthetic window:
   real bank = the one planted stream; iid null bank = one seed-78300 stream;
   structure-preserving null bank = one cyclic rotation of primes^2 by 7001 values.
   Each bank searches offsets {316,317,318} x BOTH anti-repeat models: 6 cells.
   Thus 18 cells/window, 144 new synthetic cells total. Same lengths and effort.
   The two null banks are separate sensitivities, not replicated significance tests.
6. A known-cell composition witness requires: standalone stream rejected;
   attempt-clock composite marginal prediction <=1.003; long forward IoC within
   [.997,1.003]; native true-cell keyword recovered up to a single constant shift;
   native IoC >=1.6 AND >= each same-sized null-bank max +.15; independently
   decoded native keyword (all 29 global shifts selected by language likelihood,
   NOT by planted truth) reaches rune accuracy >=.95. No exact-offset requirement
   is imposed on the best family cell. All eight outcomes are retained; finding
   a witness is existential, NOT an 8-case power estimate.
7. The native engine implements the attempt clock only. Emission-clock cases
   are explicitly unsupported diagnostics, not false negatives for that model.
   Nulls use the same native selection as their corresponding positive.
8. Mandatory retained deep-offset regression: copy the existing synthetic c1500
   window and decode exactly once at (1500,L8,model0), fast, campaign abort.
   Report its recovery failure as a coverage limitation even if ABORT matches
   the historical record. Do not replace it by offset1422 or turn it into a
   successful planted-key control. No other old plant or null sweep is repeated.

## Decision

- Algebra, stream identity and oracle round trips must all pass; failures mean
  FAILED_CORRECTNESS and no scientific inference.
- The keyword-known and canonical (attempt-clock) unknown-keyword recovery
  requirements are reported separately. Any failed required canonical positive
  is FAILED_RECOVERY_GATE. An empty witness set is NOT an LP2 exclusion.
- Even if new witnesses and all new canonical cases pass, the retained c1500
  failure blocks a campaign-wide power claim: LIMITED_FEASIBILITY_ONLY.
- Timeout/unfinished work is INCOMPLETE. No automatic retry or seed replacement.
- No Monte Carlo p-value, global false-positive rate, LP2 negative or decryption
  is inferred. Later calibration needs a new explicit approval.

Reference design: `work/independent/frontier/REPORT.md`, D2 and A0. Source semantics:
`work/h5slice/h5slice.py:690-716`, `work/kscreen/export.py:264-283`,
`work/keystreams.py:185-200`, `work/h5rs/src/main.rs:1591-1740,1746-1831`.
The parity command's supplied-stream interface is a reviewed harness interface;
this gate does not independently retest file: KSB reader parity.
