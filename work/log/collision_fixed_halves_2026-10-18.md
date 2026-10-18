# Fixed T6/I5 halves and section blocks, authorized 2026-10-18

Nothing in LP2 is solved. User: Claude asks for fixed T6 and I5, no-selection
halves, and a section diagnostic redo in smaller blocks. Frozen before execution:
`work/independent/collision_fixed_halves/PROTOCOL.md`.

Complete numbers, source file/line citations, all controls and 17-invocation
manifest: `results/independent/desktop/20261018-collision-fixed-summary/REPORT.md`.
Each invocation ran once, sequentially, passed 27/27 tests (zero skips), ended
FINISHED and remained under its unchanged 95 s cooperative cap. No source/seed/
protocol changed during execution. No failures or retries in this new package.
Previous selection-control failure and monolithic section timeout remain recorded.

## Fixed-rule result

Same halves: A=7,9,12,14; B=8,11,13,15. Raw spend kernels only, q=.81.
No affine/lag/guard/mixture selection or fitting. 999 section-doublet-conditioned
null books per half; both fixed rules evaluated, never maximized.

T6: A +3.198569 nats, 3/999 exceedances p=.004; B +8.803375, 0/999 p=.001 floor.
Both scores positive. Frozen conjunction p=max(p_A,p_B), Bonferroni over two rule
claims: adjusted p=.008. Meets fixed both-halves criterion.

I5: A +3.394918, p=.003; B -.224223, p=.016. Adjusted conjunction tail p=.032,
but required positive score fails in B. Does NOT meet frozen stability criterion;
this is not an exclusion of lag5 echoes. Negative log LR can be in the upper tail
of a null distribution with a much more negative median (B I5: -9.683758).

Controls: I5 plants recover 2/2 in each half; T6 1/2 in A and 2/2 in B. Matching
both-halves recoveries I5 2/2, T6 1/2. Neither fixed rule flags the null in either
half. The frozen coarse per-rule gate passes for both; population power remains
unknown from two plants/rule. These are not reused selection-pipeline controls.

The rules were fixed before THESE runs, not before historical whole-LP2 discovery.
No untouched replication, causal identification, key or plaintext recovery.

## Completed section diagnostic

Observed eight rows persisted first. Same original raw-T6 mean equations and
own-doublet moment fits q_s, same forward generator, seeds, refit and statistics.
Eight FINISHED blocks of at most 25 (last 24), 20.6-33.6 s each; replicate IDs
0..198 complete, no duplicate/missing IDs, same baseline hash. Original incomplete
simulation state was not reused. Merge FINISHED with all input hashes.

Own-rate expected vs observed by section:
7 4.944451/6; 8 6.658524/6; 9 11.567294/10; 11 11.174891/13;
12 5.744783/5; 13 9.063875/11; 14 9.328963/9; 15 20.815578/20.
Total **79.298359 expected vs 80 observed**.
Shape statistic 1.3365592865, 197/199 exceedances, p_upper=.990.
Overall discrepancy 1.3545935182, 198/199 exceedances, p_upper=.995.

No large-discrepancy flag; observed residuals are smaller than almost all forward
books. High upper-tail p does NOT prove correctness. No lower-tail claim was
prespecified or promoted as a discovery. Refitted plug-in bootstrap, selected
family, 199 replicates; heterogeneity-sized power unknown. Does not establish
homogeneity, joint lag5/lag6/S/flat-lag fit or a cipher solution.

## Unchanged limits

Historical selection remains; actual-site spend/hold power and inflation of the
observed 80 remain unknown. No new hypothesis search, retuned I5, alternative
split, sign test, key scan, background job, GPU or spend/hold discriminator.
