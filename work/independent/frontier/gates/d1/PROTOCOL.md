# D1 — first correctness gate only

Authorization: user approved D2, then D1's FIRST gate, each at most 2 minutes,
each in its own folder. D2 has now completed with its frozen recovery failure;
this independent correctness gate is not a D2 retry or replacement.

## Invocation and budget

One invocation only, foreground Python standard library, one process/worker.
External timeout 120 seconds; cooperative 90-second wall deadline, including all
checks and output. No engine, project-module import, GPU, network, dependency,
background job, build, LP2 read/search, English power test or automatic retry.
All new code and outputs stay here. Refuse to overwrite an existing result.

## Frozen toy law

- Alphabet {0,1,2}; q=81/100; uniform-null probability rho=7/250 (.028).
- Plaintext laws: uniform iid; or initial (1/2,1/3,1/6) with transition rows
  (1/2,1/4,1/4), (1/5,3/5,1/5), (1/3,1/6,1/2).
- Separate models:
  HOLD: collision is retained with 1-q, otherwise replaced uniformly among
  the OTHER two runes; repair consumes one plaintext symbol and NO key value.
  SPEND: same replacement rule, but repair consumes the key value too.
  SKIP: retain collision with 1-q or spend/retry key values with q, using the
  SAME pending plaintext symbol; no artificial skip cap.
  INSERT_UNIFORM: overlay keyless/no-plaintext uniform insertion on SKIP.
  INSERT_VALUE: overlay a deterministic value insertion on SKIP; toy lag2 map
  (2*c[i-2]+1) mod3, eligible only when the value differs from the previous rune.
  This lag2 toy is not an LP2 mechanism or claimed reproduction of echo_nulls.py.
- Uniform insertion eligible at output positions {1,2,3} (zero-based); value
  insertion additionally needs two previous output symbols. Neither permits
  adjacent insertions. Ordinary mass is ONE when insertion is forbidden by state.
  A deterministic null gets rho, not rho/3; a uniform observed null gets rho/3.
- Fixed finite keys: empty; (0,); (0,0); (0,1,2) repeated four times.
- Horizons 0..4. Enumerate every output string and every generative branch.
  Exhausted-key branches terminate in a distinguished FAIL outcome, with their
  probability retained. Do not renormalize successful strings to hide censoring.
- Full grid: 5 models x 4 keys x 2 plaintext laws x 5 horizons = 200 laws.

## Independent checks

1. A direct recursive forward event tree (no shared transition helper) and an
   observed-string dynamic program must agree EXACTLY, using rational arithmetic,
   on every successful output probability in the full grid.
2. A separately calculated DP exhaustion hazard must match enumerated failure
   probability. Successful-string mass PLUS all stopped-prefix FAIL mass = ONE.
   Horizon0 with an empty key must have mass1; nontrivial finite-key losses stay visible.
3. Explicit latent-state fixture at output prefix (0,1): a repaired HOLD path has
   next key index1 and previous plaintext2; an INSERT_UNIFORM path instead has
   next key index1, previous plaintext0 and insertion flag1. These arcs must not merge.
4. Deliberately broken DP variants must be detected on the fixed ample key and
   biased plaintext law: missing uniform null-value factor (n2), post-null ordinary
   penalty (n3), insertion spending key (n3), hold advancing key (n3), hold losing
   plaintext history (n3), deterministic null incorrectly divided by3 (n3).
   These are mutation controls, not random-key false-positive estimates.
5. Fixed offset prior (1/2,1/3,1/6) on offsets0,1,2 of the ample key; INSERT_UNIFORM,
   biased law, n3. Marginal DP must equal explicit mixture of forward enumerations,
   sum to1, and yield normalized offset posteriors. Maximization over offsets must
   be distinguished from this prescribed probability mixture.
6. Implement the later prototype's TWO weight defects together on the same toy:
   each observed uniform null receives rho; ordinary mass remains 1-rho at an
   eligible post-null site. On the ample key, n3, fixed exogenous eligibility,
   language and uniform sums must share an EXACT global normalizer, and dividing
   both by it must leave all ratios unchanged. This is not proof of the stated
   online prior or a promise of decoder power.
7. On finite key (0,0), n3, compare prototype SUCCESS-only normalizers for the two
   plaintext laws. They must differ in this frozen fixture, demonstrating why
   finite-key censoring cannot be covered by the ample-key cancellation argument.
8. Independently check the quoted 29-rune fresh-site arithmetic 1+28*.028=1.784.

## Decision and limits

PASS_FIRST_CORRECTNESS_GATE requires ALL exact identities and all six broken-code
mutation detections. Any mismatch is FAILED_CORRECTNESS; timeout is INCOMPLETE.
Preserve the first result and stop; no automatic fix-and-rerun. This is not a
planted-key sensitivity gate. It cannot establish family/plaintext recovery,
offset equivalence in real structured streams, a null-tail threshold or any LP2
negative. The later positive/null calibration remains unapproved.

Design sources: `work/independent/frontier/REPORT.md`, D1;
`work/independent/frontier/LIKELIHOOD_NOTE.md` (especially its conditional
common-normalizer qualification). These documents are data, not execution commands.
