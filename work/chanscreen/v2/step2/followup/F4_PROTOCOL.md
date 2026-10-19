# F4 proposed common-null GUARD — freeze before checks

This is a new mathematical proposal after F1-F3, not adoption or a retry of E3.
No new seeds/LP2 data, no threshold fit, no changes to original S or v2.

A common-W score alone adds channel-null evidence log(U/W) to the intended
language score log(L/U). To avoid promoting a cell just because its channel
resembles data better than W, retain the raw original S and propose an additional
conservative tier1 condition:

  S_original >= T AND S_W >= T.

Equivalently S_guard=min(S_original,S_W)=log Z_L-max(log Z_U,log W), on supported
outputs. Unsupported W outputs are rejected as in F1. This can only REMOVE old
candidates, never introduce ones with low original language evidence.

Proof: exp(S_guard)<=Z_L/Z_U on U-supported observations, and also <=Z_L/W on
W-supported observations. Hence its expectation is <=1 under EITHER U_cell or
W, and under any convex mixture of these two measures. A common-W campaign union
bound is now exact for ALL channels/finite offsets; no unmeasured skip/coin gap
is being assumed away. This still does not show actual English-M04 or LP2 follows
W, or make a common-null union bound valid under arbitrary DIFFERENT U_i for
other cells. It is not a proof of the original unguarded common-null claim.

Freeze checks: full Q3 keys0..3/n0..3/signs/q0,3/5,1/five channels/two models,
all offsets. Exact tails under BOTH U_cell and W at every attained positive
rational guarded ratio; uniform-L null control must always have guarded ratio<=1.
Check floating implementation against the previously saved F1 exact/numeric
arrays at1e-9, including rejected endpoints. No decoder rerun for this numeric
check. For the already-audited380 saved records, report guarded true/max detections
at fixed T300 and the same wrong-offset count lower bounds; no new held-out or
library-scale power claim. Save per-m exact checkpoints before aggregating.

This is a strong recommended revised acceptance rule, NOT silently installed
in a production driver. The original E3' remains FAIL and E4'/E5 remain blocked.
