# Phase 9: ciphertext-feedback ciphers (2026-10-17)

## Why a new family

LP2's one hard structural fact is that `c_i = c_{i-1}` is rare (0.66% against 3.45%), only at lag 1, with the other 28
differences `c_i - c_{i-1}` flat. Every screen so far searched for a key in `c` itself, assuming `c = p + k` and then
explained the doublets with an ad hoc "collision check on the ciphertext".

A **ciphertext-feedback cipher** produces the same fingerprint without an ad hoc rule:

    c_i = a * c_{i-1} + p_i + k_j      (mod 29)

For a = 1 this is `c_i - c_{i-1} = p_i + k_j`: the differences are an ordinary Vigenere-type ciphertext, flat for a flat key,
and a doublet occurs exactly when `p_i + k_j = 0`. If the encryptor avoids that shift (skips to the next key value, with the
same 80% effectiveness the doublet statistics need), the result is LP2's fingerprint. For general a the doublet condition
is `p_i + k_j = (1 - a) c_{i-1}`. IoC of `c` stays 1.0 whatever the plaintext, so IoC-based screens of `c` are blind to it.
(Plaintext feedback with a random key is also invisible to a screen of `c`, but its decode is only weakly non-random,
IoC ~1.05 for English, so it cannot be screened on 300-rune windows; it is not covered here.)

## The reduction (`work/kscreen/chain_windows.py`)

Rewrite each section as `c'_i = c_i - a * c_{i-1}` and give each position the reference `(1 - a) * c_{i-1}` instead of
`c_{i-1}` (a `P` line in the windows file, read by both engines). The engine's collision test - "a candidate with key
value k_j would have repeated the reference" - is then the chain model's test, and the engine, its IoC statistic, both
anti-repeat models, the key multipliers, the plaintext substitution invariance and the verification all apply unchanged.
`a = 0` is the old model. The first rune of a window is dropped when its predecessor is unknown.
The Rust engine and the CUDA port both take `P` lines; defaults are identical to before (selfcheck, 54 + tests).

## Controls (`work/kscreen/chain_selftest.py`, `work/tests/test_chain.py`)

- Algebra: for every a in 0..28 on random sequences with forced doublets, `c'_i == P_i  <=>  c_i == c_{i-1}` and
  `c'_i + a c_{i-1} = c_i` (tests).
- Positive: English enciphered with `a = 1, 7, 28`, a random plaintext substitution, a library keystream at offset 1500 and
  the skip rule; the screen returns it for all three windows at offset 1501 (the dropped first rune), IoC 1.60-2.05.
  The same ciphertext screened with the wrong multiplier peaks at 1.23-1.26.
- Null: 30 random keystreams x every offset on the LP2 chain windows, a = 1, 7, 28: best IoC 1.278 / 1.278 / 1.306
  (threshold 1.40).
- CPU and GPU engines agree decode by decode on chain windows (a = 1, 5, 28 and a = 7 in the tests).

## Preliminary check before the screens: short periodic keys (`work/chain_lag.py`)

Coincidences at lags 1..120 in `c'` for every a (3,451 tests; the largest z expected by chance is about 4.0): the largest is
+2.98 (a = 0, lag 99). No short periodic key in any chain model. (Lag 1 in `c'` for a = 1 is normal, z = -1.0: the doublet
deficit of `c` is exactly the missing zero difference.)

## The campaign

`kscreen-chain`, queued after the first two lanes: for a = 1..28, the 1,447-keystream library x 8 sections (every offset,
both models, both signs), every order-2 linear recurrence, every cubic polynomial, a matched null of 300 random keystreams,
and whole-window verification of the top 10. ~3 h on the CPU estimates, ~1.5 h on the GPU. The decision rule is the
campaign's usual one (IoC >= 1.40 on the first 300 runes, then whole-window verification against the keystream's own
random offsets); the 8 windows are all >= 300 runes, so no short-window caveat applies.

## Results

See `results/overnight/desktop/REPORT.md` (section kscreen-chain) and `results/kscreen/chain/`.
