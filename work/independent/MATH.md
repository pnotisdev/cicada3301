# Independent review: mathematical scope and proposed test

**Implementation status: written, NOT executed, NOT validated. Nothing in LP2 is solved.**
This review does not alter the active relabelling job or the shared engines.

## 1. The PGP → Z5 claim

Hex-to-ASCII conversion is bytewise:

| Hex byte | Decimal | ASCII |
|---|---:|---|
| `7A` | 122 | lowercase `z` |
| `35` | 53 | `5` |
| `09` | 9 | horizontal tab |
| `0F` | 15 | Shift In, a control character |

Thus `bytes.fromhex("7A35090F") == b"z5\t\x0f"`, not `b"z5z5"`.
The latter would require `7A357A35`. Uppercase `Z5` starts `5A35`.
The eight hex characters normally denote a **short OpenPGP key identifier**, not
an encoding of the signature's message. A short ID is not sufficient to authenticate
Cicada: that requires an independently trusted full fingerprint and verification of
the actual signature. These tools do neither, and do not fetch a key.

The prefix could have been intentional; byte conversion cannot settle that. But
choosing two books after finding two readable characters has a very large, undefined
selection space. The probability `1/65536` of a *predeclared* two-byte prefix is
not a p-value for a title selected after looking.

Before a cryptanalytic campaign based on the Z5 titles, establish:

1. Exact titles, author, **volumes versus editions**, publication dates and a
   source available before the relevant Cicada puzzle. Bibliography is unverified here.
2. A primary, authenticated Cicada connection, not a repost repeating this conversion.
3. An exact, bounded recipe that produces runes/key values, and a predicted observable.

A book's ordinary English text as an unwhitened additive running key is already
low priority: the repository's English-running-key simulations do not reproduce
LP2's flat unigrams. Hashing the book, a book code, a tableau inspired by it, etc.
are different hypotheses; rejecting the plain running key would not reject those.
`source_gate.py` is deliberately only a marginal preflight, not a book-code solver.
No book has been obtained, read, or bibliographically verified in this pass.

## 2. Affine OUTER alphabets are not new coverage after all multipliers

Work in the prime field F_29. Let the outer permutation be

    sigma(x) = a*x + b,   a != 0
    c_i = a*(p_i + m*k_{j_i}) + b.

The ordinary screen with key multiplier `m' = a*m` sees

    c_i - m'*k_{j_i} = a*p_i + b.

The right-hand side is a fixed bijective relabelling of plaintext. Consequently,
for every alignment, its count histogram is permuted and its IoC is identical.
Equivalently, first relabelling ciphertext and then subtracting `m*k` gives

    a^(-1)*(c_i-b) - m*k_{j_i} = p_i.

Collision feasibility is also preserved:

    p + m*k == previous_inner
      iff a*p+b + (a*m)*k == sigma(previous_inner).

Therefore the same key-pointer paths exist under the skip rule. The structural
coin decoder likewise consumes the same draws when the equality checks agree.
This says nothing about an additional, unspecified key-value-dependent coin rule.

**Consequence:** on the same windows, offsets and decoder settings, all outer
affine maps are already covered by the completed all-28-key-multiplier screen.
Atbash (`a=-1, b=28`) is covered even by the two ordinary key signs. Shifts are
likewise redundant. Affine relabelling can be an implementation cross-check, but
not an independent family requiring another long search.

This is stronger than deduplicating the 29 reflections. It does NOT say to stop or
modify the active job: the job also includes non-affine keyword alphabets, which
remain legitimate new coverage. No process was inspected, signalled or changed.

Why a genuinely non-affine sigma is different: if some fixed `m'` removed its key
for **all** plaintexts and key values, then

    sigma(p+k) - m'*k = D(p).

Setting `k=0` gives `D(p)=sigma(p)`. Setting `p=0` gives
`sigma(k)=sigma(0)+m'*k`, which is affine, a contradiction. This universal statement
does not rule out coincidences on a small or restricted data set.

`audit.py` supplies reproducible identity checks and a non-affine countercontrol.
They have not been run here. This is an algebraic correction to scope, not a new
empirical LP2 negative, and it should not be counted as a second independent test.

## 3. A narrower keyless-null hypothesis motivated by the lag-6 relation

### Why this rather than another seed/stream expansion

The reported largest 300-rune screen hit (IoC 1.415) fell to 1.073 on its full
window. None of the reported hits is a partial plaintext. The more useful leads
are structural: word-internal echoes and alignment assumptions.

The free per-word null beam's null maximum of about 1.75 does **not** prove that
all constrained or probabilistic null decoders are impossible. It establishes a
failure of that unconstrained maximum-IoC statistic. A value constraint and a
fixed prior spend less freedom. Whether that improves power must be measured,
not assumed; this code is a gate to measure it.

### Precisely bounded model

Let `w_i` be the observed word's first output position. At output position `i`,
a null opportunity exists only if

    i-w_i >= 6
    T(c_(i-6)) != c_(i-1),       T(x) = 24 - 2*x (mod 29),

and the preceding output was not itself a null. At an opportunity:

* with fixed probability `rho = 0.0272`, emit `T(c_(i-6))` and consume **no
  plaintext and no key value**;
* otherwise emit an ordinary keyed rune.

At other positions ordinary emission is forced. A null is a visible ciphertext
rune: the next ordinary rune compares its collision attempt against that null,
not against the previous non-null rune. Consecutive nulls are forbidden.

For ordinary emission, write `u=p` or `u=28-p` for the selected orientation:

    y = u + m*k_j (mod 29),       m in {1,28}.
    Consume this key value.
    If y equals the preceding OUTPUT rune:
        redraw with probability q=0.81, otherwise accept it.
    If y differs: accept it.

Repeated redraws are enumerated without a fixed skip-count cutoff. A finite key
buffer is the specified key source; real searches require ample tail for later
whole-section checks. No coin model, arbitrary alphabet, constant plaintext shift,
lag-5 null, layout clock, backward pointer, inner keyword, or unknown null value
is included.

**Rate interpretation matters.** The reported 0.0272 is an excess rate among
eligible lag-6 pairs, not among all 12,956 runes. This model therefore implies only
roughly a few dozen nulls book-wide, depending on its guard and opportunities. It
is NOT a proposed explanation of the one-extra-rune-in-42%-of-words fit, nor of
the lag-5 concentration on S. The guard also changes the exact expected rate.

This is a conditional-on-layout output-prefix model. It generates a continuing
plaintext stream while treating the observed output word layout as supplied.
It does not claim to preserve plaintext word boundaries or model word lengths.
That choice is intentional: the language score ignores separators.

### Exact forward score, not a best-alignment score

Train a normalized bigram language model `L(p | previous_p)` on the committed
Emerson reference, with 1/2 pseudocount per cell. Solved Cicada text is used for
planted tests, not for training. The competing model `U` assigns probability
`1/29` to every plaintext rune. Both use **the same cipher, layout, null prior,
key and alignment possibilities**.

Use forward states

    (next_key_pointer, previous_plaintext, previous_output_was_null).

For a candidate ordinary emission using `r` rejected draws and then key `j+r`,

    u = c_i - m*k_(j+r)
    u + m*k_(j+t) == c_(i-1) for EVERY t < r
    transition weight = q^r * (1-q if c_i==c_(i-1) else 1).

Multiply by the no-null decision probability and `L(p | previous_p)` (or `1/29`).
A matching null transition contributes its fixed prior, leaves the key and
previous plaintext unchanged, and sets the null-state flag. Sum all path masses
with log-sum-exp:

    S = log(sum_paths P_L(ciphertext, path | key, layout))
        - log(sum_paths P_U(ciphertext, path | key, layout)).

The uniform forward table can omit previous plaintext. There is no IoC-based
path cherry-picking and no beam. A separate Viterbi path is computed only when
needed for recovery checks or readable output; it never changes `S`. Exceeding
the state/time budget aborts instead of silently pruning and reporting a negative.
All equalities are exact integer arithmetic mod 29; likelihood sums use floating
point, checked against a separate tiny exhaustive forward-encryption enumerator.

This likelihood ratio is between two **specified** output-prefix models, not a
posterior probability that Cicada used this cipher. Rate, lag and map were chosen
from LP2: selection prevents treating the result as confirmatory discovery evidence.

### Controls and decision rules, fixed before the proposed search

1. Local unit tests must pass with **zero skips**, including brute-force checks.
2. Six unconditioned English plants use LP2's actual output layouts and the stated
   rates. Two more are explicitly **conditioned on at least one null** to exercise
   the new branch, not to inflate the power estimate. All must recover the correct
   key/offset/orientation with >=10 nats over wrong settings, >=98% output alignment
   accuracy, and every planted null located. Two uniform-plaintext plants undergo
   the same search and must stay below 0.20 nats per output rune.
3. A passing gate is tied to hashes of code, toolkit, transcription and corpus;
   edits invalidate it. Eight plants are not a precise power curve. Failure stops
   the campaign; it does not exclude the null hypothesis or any LP2 cipher.
4. Real screening defaults to **one stream, offsets 0..15, two signs, two
   orientations, two null rates**, on 300 runes of section 0.7: 128 hypotheses.
   At least 19 shuffled-key null searches repeat the ENTIRE same selection. The
   minimum Monte Carlo rank is then 1/20, not a discovery-level p-value. Shuffling
   preserves key marginals but not its temporal structure.
5. Flag only if `S/n >= 0.20` and `S >= max(search-null S)+20` nats. These are new
   conservative heuristics, NOT a reuse of the old clipped-bigram +300 gate.
6. A human separately starts whole-section verification: 20 random, unsearched
   offsets of the SAME stream, fixed winning variant; `S/n >= 0.20`, a >=20-nat
   margin, and conditional held-out score `(S_full-S_screen)/(n_full-n_screen)`
   >=0.20. Additionally require the Viterbi plaintext's full IoC >=1.40 and a
   >=0.15 margin above all 20 control IoCs, following CAMPAIGNS' numerical spirit.
   These thresholds alone do not authenticate a plaintext or fully correct the
   selection of the hypothesis. Report all failures too.
7. A numerical survivor still requires independent reimplementation, actual
   coherent plaintext over the full section, the same reproducible rule on
   another section, and the project's final checks. Nothing is called solved here.

Negative scope is only the selected stream prefixes/offsets, sign/orientation,
English bigram model, one section, specified null value/rate and skip convention.
It is not a negative for all nulls, all alphabets, all books, or all of LP2.
