# Phase 29: signed streams with all 28 multipliers (2026-10-20/21)

Closes the gap named in `phase21_signed_streams.md` section 2 ("multipliers other than +-1"). **Nothing in LP2 is solved.**
Same engine, windows (8 section windows of 300 runes, `data/segments.txt`), streams (`data/signed.ksb`, rebuilt with `export.py` and `signed.py`:
272 streams, 714,912 stream-offset pairs, as in phase 21), models skip + coin, beam 16, abort 150:1.2; only `mults=all` (1..28) and `threads=2` changed.
Script: `work/tmp/kscreen/run_signed_mults.sh`. The phase 21 controls (`signed_selftest.py`, 18/18 incl. multipliers 1 and 28) cover the engine and streams; the planted-key
test of other multipliers was not rerun here (the engine treats all multipliers alike; the earlier gate's wrong-class streams were 1.19-1.29).

| run | decodes | best IoC | per-window bests |
|---|---|---|---|
| signed streams, mults=all | 320,280,576 | **1.3404** (0.15, `H sha256-ctr reject :sigval0`, offset 1988, mult 13, skip) | 1.287-1.340 |
| null `rand:37:1` (same pairs, same mults) | 325,187,968 | 1.3326 | 1.282-1.333 |
| null `rand:37:2` | 325,187,968 | 1.3359 | 1.286-1.336 |

Phase 21 (mults 1, 28): 1.2971 vs nulls 1.3016, 1.3359. Rule: 1.40.

Verification (`verify.py`, top 15 hits, `results/kscreen/signed_mults_segments_verify.txt`): **0 of 15** keep IoC >= 1.4 over their whole window;
first-300 IoCs 1.308-1.340 fall to 1.05-1.12 over 729-1,729 runes, the same keystream at 20 random offsets gives mean 1.05, max 1.06 (noise).

**Verdict:** negative. The real best (1.3404) is 0.005-0.008 above the two nulls' maxima, inside the spread between null seeds (1.3016-1.3359 across the four nulls of phases 21 and 29), no hit verifies. Not excluded: windows other than section starts; the numbers used as something other than an additive key; signed material not in the scans; unsigned/other sources; a key that is a function of these numbers beyond the conversions built.
Files: `results/kscreen/signed_mults_{segments,null_1,null_2}.tsv|.log`, `signed_mults_segments_verify.txt`. Not done: registry row, `build_overview.py` (the parent records them).
