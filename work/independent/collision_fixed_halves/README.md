# Fixed T6 / I5 halves and blocked section diagnostic

Executed once on user authorization, 2026-10-18. **Nothing in LP2 is solved.**

- Same fixed A/B section split. Raw T6 and I5 kernels only, q=.81; no selection.
- 999 matched null books per half; both rules returned without maximizing.
- Both-halves claim: max(p_A,p_B), Bonferroni across two rules, scores positive.
- T6: +3.199/.004 in A, +8.803/.001 in B; adjusted p=.008; meets criterion.
- I5: +3.395/.003 in A, -.224/.016 in B; fails positive-score criterion in B.
- New controls pass the frozen coarse gate for both rules; T6 A recovered 1/2,
  other matching rule/half pairs 2/2; null did not flag. Power precision unknown.
- Eight small blocks completed the same original 199-replicate section bootstrap.
  Own-doublet-rate expected count 79.298 vs observed 80; shape upper-tail p=.990,
  overall-fit upper-tail p=.995. No proof of model correctness or homogeneity.
- All 17 invocations FINISHED; 27/27 unit tests on each; no code, protocol or
  seed edits during execution, no retries, every invocation below the 95 s cap.

Read [PROTOCOL.md](PROTOCOL.md) for frozen pre-execution decisions and commands.
Full results, source line citations, all raw artifact paths and original logs:

`results/independent/desktop/20261018-collision-fixed-summary/REPORT.md`

The rules were discovered on the entire book before this request. Freezing them
now yields retrospective consistency checks, **not untouched replication**.
Previous experiment failures/timeouts remain unchanged. No spend/hold
ciphertext discriminator or key/plaintext recovery was attempted.
