# D1 FIRST correctness-gate result

**PASS_FIRST_CORRECTNESS_GATE** (`result.json:3`). Nothing in LP2 is solved.

Elapsed seconds: 0.56956 (`result.json:2888`). One invocation; no retry.

## Completed checks

- 200 exact output laws; 4840 DP-versus-event-tree output probabilities.
- Successful output mass plus explicitly retained exhaustion mass is exactly one in each law.
- 6/6 deliberately broken transitions detected.
- Hold and insertion preserve different latent plaintext-consumption states.
- Frozen offset-prior marginalization agrees exactly with explicit enumeration; maximizing offsets is a different statistic.
- Ample-key prototype language/uniform weights share a global normalizer and preserve their ratios; finite-key success-only normalizers need not.
- Summary source: `result.json:2889-2896`.
- Full exact identities, state fixtures and normalizer values: `result.json:2480-2887`.

## Not established

No English/plaintext or key-family recovery power, real-stream offset equivalence, calibrated null tail, LP2 exclusion or decryption.
The later positive/null calibration is unapproved. Passing this first correctness gate is not permission to search LP2.
All failed/incomplete checks remain in the first result; the script refuses a second invocation.
