# step3: full-library sanity null (E3' sanity) — PASS, descriptive only

**Nothing in LP2 is solved. No LP2 ciphertext was scored.**

## Corrections to the first version of this report (2026-10-20)

1. Cells: one window is **106,626,192** cells ((13,326,835 key values + 1,439 end offsets) x 2 signs x 4 channels),
   **533,130,960** for the five windows. The first version said 26.6M / 133M and left out the four channels.
2. The offset-alias radius k = 15 was justified by "the saved aliases all lie within +-15". That is vacuous: v1
   scored only offsets 0..15 (`m04.OFFSETS = 16`), so every stored exceedance is within 15 of the true offset by
   construction. k = 15 stays as a pre-registered engineering choice (frozen before E4 and before any LP2 scoring),
   not as a data-derived value; the saved data show only that most aliases sit at +-1..+-4. E4 scores every offset of
   the planted stream and will measure the real alias profile. k only groups hits into classes and excludes
   near-true cells from the wrong-offset count; it never decides whether a cell passes T.
3. The caveat that "English passed through M04 is not distributed like the common null W" is not supported by this run
   and is removed. What the run shows: the highest plain-S cells (-17 to -27) are cut to -97..-102 by the guard, so
   S_guard sits far below T. I have not inspected where those cells are.
4. The cost I quoted for E4 (about 179 CPU-h) priced a FULL-bank search per plant (v2/REPORT.md). The frozen
   `step2/README.md` E4' searches only the planted stream: 8 passes, about 1.5 s per plant (measured per-pass timings
   x library lengths), about 2.5 CPU-min for 100 n300 plants.

## What was run

- Control: `check_regen.py` regenerated v1 calibration windows 0..4 (Cicada/iid, M04 plants, wrong-key) and
  reproduced each stored v1 maximum to <=3.6e-12 nats (`check_regen.log`). Windows are in `windows.json`.
- Run (`e3s.py`): each window against all 1,439 library streams, 4 channels x 2 signs x every offset
  (106,626,192 cells per window, 533,130,960 in total), score S_guard = min(S, S_W), q = .81, T300 = 29.799
  (`T_nats` in `step2/thresholds.json`, unchanged). Run on `laptop`, 4 workers (the laptop has 16 threads), blocks of
  48 streams. Wall time per window at 4 workers: 11.6 to 17.6 min (w0 was split across two runs; 9 of its 30 blocks came
  from a run I stopped, and all 150 block files parse and cover all 1,439 streams).
- Result: all five windows are far below T300 and have zero exceedances at t = 0, 5 and 10.

| Window | max S_guard | max S | argmax (channel) |
|---|---:|---:|---|
| 0 | -102.37 | -17.72 | hold |
| 1 | -102.11 | -19.19 | hold |
| 2 | -97.29 | -17.23 | hold |
| 3 | -99.43 | -26.55 | hold |
| 4 | -97.30 | -21.01 | hold |

Offset-alias radius k = 15 (pre-registered, see correction 2). No exceedance occurred here, so the alias rule was not
exercised on null data.

## Caveats

- Five windows cannot certify a .001 tail rate. This is a sanity check, not a calibration. The step2 sanity design also
  listed three n600 windows; they were not run (the campaign is n300 only).
- The guard binds: S_guard is 73 to 85 nats below plain S on the null maxima. On the saved small-bank true plants it
  removed none (F4: 280/280 kept), but library-scale power under the guard is unmeasured (E4).
- Single source (Cicada/iid) and single length (n300). English windows were not run.
- e3s.py has only ever scored nulls. It has not yet recovered a plant, so it cannot support a negative on LP2 until it
  does (end-to-end positive control, below).

## Next (not run)

1. E4' conditional-stream power, n300 only (n600 needs its own sanity windows first): about 3 CPU-min.
2. End-to-end positive control: planted windows through the full 1,439-stream bank with `e3s.py`, one per channel.
3. Limited LP2 pilot on pre-registered windows, tier 1 only (S_guard >= T300), then a decision on the other windows.

