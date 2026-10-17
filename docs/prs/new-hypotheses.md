# Review: `research/new-hypotheses` (laptop, 2026-10-17, three commits d89d942 / 161ac5d / 9b4e965; not merged)

Read as data on the desktop at about 14:30. None of the branch's code was run (no cargo build, no unit test); what was checked independently is listed below. Nothing in LP2 is solved.

## What the branch adds

1. **Keyless exclusions** (`work/log/hypotheses_2026-10-17.md`, `results/analysis/hypotheses_2026-10-17.txt`, probes in `work/tmp/hyp/`): running key plus progressive (Trithemius) shift, a multiplicative
   keystream, cumulative-sum running keys, the 86 surviving doublets as a 'ditto' letter, a key restart after each doublet: all excluded with planted controls; a missing key value (prime-based keys at any
   offset) disfavoured at p about 0.05 (modest power, said so by the author). The lag-5 echo is not concentrated in the quoted-speech spans (2 inside, 1.9 expected).
2. **`work/layer2`, a two-layer screen (Rust, 1,213 lines + Python harness)** for hypothesis H-LAYER: a keyword Vigenere inside (Welcome / Koan 2 style, optionally with the literal-F rule), a number stream with the
   anti-repeat rule outside. The outer layer explains the doublet deficit and the flat statistics, and hides the inner layer's literal F, which would explain the missing F excess. kscreen decodes the outer stream
   correctly and then scores a Vigenere text (IoC about 1.18, below its 1.40 rule; `PLAN.md` already records 1.17 for Vigenere with DIVINITY), so kscreen is blind to it; `layer2` scores with the English rune-bigram
   table instead (a true key about +7 per rune, random about -15). Two slices run on the laptop, both negative: An End's prime streams x DIVINITY / FIRFUMFERENFE / CIRCUMFERENCE, every option and offset, 512 M decodes
   (best -4.53 per rune, 0 of 15 verified); 20 Cicada streams x any keyword of period 2-14, 111 M decodes (best column z 9.97, 100 best turned into keywords and re-decoded: best -7.80 per rune, 0 of 100).
   A campaign `layer2` (about 13 h CPU) is queued in `jobs/overnight.py`.
3. **`prng-time`: generators seeded with a MILLISECOND timestamp of 2012-2014.** Java's `Random` takes a 48-bit seed and CPython / Ruby seed MT19937 with two 32-bit words above 2^32, so the 32-bit sweeps
   never covered `new Random(System.currentTimeMillis())` or `random.seed(int(time.time() * 1000))`. `prngx` now seeds `pymt` like CPython for any integer (words of |n|, low first; one word below 2^32, so every earlier
   result is unchanged), gains `PRNGX_MAPS` and a `keys` mode, plus `time_campaign.py` / `time_verify.py` and a campaign `prng-time`. Demo on 2014-01-04/05 UTC (172.8 M timestamps per generator, 0.26% of the window):
   best +59 (the ceiling of a decode that stops at the 40-rune gate), 0 candidates. The full window (6.6e10 seeds per generator, about 210 CPU hours) is GPU work: the log specifies the 64-bit CUDA port and its gates.

## What I checked independently

- **Generator vectors.** The branch's `ref/vectors.txt` (120 lines) was compared with code written here (not the branch's): CPython `random.Random` for the `pymt` lines and my own `java.util.Random` from the specification
  (it reproduces the published values for seeds 42 and 0: -1170105035 and -1155484576). **86 of 86 `pymt` / `java` lines match, 0 mismatches**, including 2^32, 2012-01-01, mid-2013, 2014-01-01 and 2014-01-07 in ms,
  2^40 + 12345, a negative seed and 2^48 - 1. This is the part that decides whether a millisecond sweep can be trusted, and it holds.
- **The Rust seeding change** (diff read): `seed.unsigned_abs()`, one word when `n >> 32 == 0`, else `[n as u32, (n >> 32) as u32]`; CPython does exactly this (absolute value, 32-bit words, least significant first, at
  least one word), and `seed = 0` takes the one-word branch. `PRNGX_MAPS` indexes the key buffers by map number and asserts the range; `nm` is left unused (a compiler warning, nothing else).
- **Privacy:** no host name, user name or absolute path in the added lines; the commit author metadata carries a personal name where main's commits use the `pnotisdev` identity (history, not a file; set the laptop's `user.name` to the alias before any publication).
- **Merge:** `git merge-tree` against `main` conflicts in `PLAN.md` only (both sides add a bullet in Phase 9). The branch also edits `docs/CAMPAIGNS.md`, `docs/SESSION_LOG.md` and `jobs/overnight.py`, files on which the
  desktop's second session ('Advanced hypotheses', campaign `kscreen-hyp`) has UNCOMMITTED edits at the time of writing, so a merge into the shared working tree has to wait for that session to commit.

## Findings and risks

1. **The runner gate does not fail on a skip.** `prng-time/gate` uses `python -m unittest discover` and treats an output starting with `OK` as passed; `OK (skipped=5)` also starts with `OK`, so a machine without the build
   or the bigram table would pass the gate having tested nothing. Use `work/tests/run_gate.py work.tests.test_prngx_time` (fails on skips), as the other campaigns do.
2. **The planted-seed tests are partly circular.** `plant` and `bgsweep` share the engine's generator and decoder, so rank 1 for a plant shows the sweep finds what the engine writes, not that the engine writes what Java or
   Python would. The independent part is `test_vectors_including_millisecond_seeds` and `test_engine_keys_equal_independent_keys` (both against code outside the engine; the vector half reproduced above). That is enough for
   Java and CPython. The null test is small (20,000 seeds; the 200,000-seed null in the log is the stronger one).
3. **Ruby is claimed but not verified.** The vectors are CPython and the Java specification only. As far as I recall (not checked here), Ruby's `Random.new(n)` seeding differs between versions (older releases always use `init_by_array` with the integer's
   32-bit words, newer ones may use `init_genrand` for a one-word seed), and its `rand(n)` / `randint` maps were not checked against a Ruby. Treat the Ruby coverage as unconfirmed until a Ruby vector is added.
4. **Coverage is section 0.7 and one pad from the first LP2 rune**, like the first pass of every earlier sweep (the branch says so). A fresh timestamp seed per section is not covered.
5. **`layer2` is large and its tests plant with its own engine** (same circularity); the selftest result (14 of 14) is the laptop's and was not re-run here. The design argument is sound and consistent with the repository:
   an outer random-looking stream with the anti-repeat rule and an inner keyword layer produce exactly the fingerprint of `work/log/phase9_families.md` (a structureless additive key), and only a decryption test can
   tell. The honest limit: its negative slices cover the solved keys and the 20 core streams, not the seeded-generator streams (proposal 5 of the log: a GPU kernel with the layer2 decoder).
6. **The 'periodic' slice cannot rank a true key first on its own** (chance z about 10 overlaps the weaker planted keys 10.4-17.7); the author widened the verification to the top 100, which is the right response.
7. **Overlap with today's desktop work.** The desktop swept epoch-second seeds 2011-2015 (8 generators, all section windows, boundary-free, 0 candidates) and small-integer seeds: `prng-time` covers the millisecond
   resolution those cannot. The branch's crib-filtered seed sweep idea (proposal 3: the first 13-16 key values of every seed compared with a crib, 29^-13 per seed, no scoring) is the cheapest decisive test on the
   list; the desktop's exact lookup of the DIVINITY WITHIN / FIND YOU ARE keys in 199,088 OEIS sequences (`results/analysis/crib_exact_lookup.txt`) is the library version of it.

## Verdict and merge plan

**Accept, with two changes**, after the desktop's second session has committed (so the shared files do not collide):
1. replace the `prng-time/gate` command by `work/tests/run_gate.py work.tests.test_prngx_time`; add a Ruby vector (or drop the Ruby claim from the campaign text);
2. rewrite the two test files' planted-seed halves so that the key stream used to PLANT comes from the independent implementation (`time_verify.keys`), then run `test_prngx_time` and `layer2/selftest.py` on the
   desktop (CPU, about 30 min) before the `layer2` campaign (about 13 h) is queued. Resolve `PLAN.md` by keeping both bullets.

**Most valuable next step from the branch: the 64-bit CUDA port of the boundary-free sweep (`phpmt.cu` / `bgmt.cu`), spec in `work/log/phase10_prng_time.md` (about 4.6 h per generator for the full 2012-2014 window once
ported, against 210 CPU hours).** The generator gates it asks for (keys equal to `prngx keys` for the vector seeds, planted seeds recovered, random ciphertext without candidates) are the project's usual ones.

## Response from the laptop (2026-10-17, about 15:10; branch commits after the merge of main c31c6a9)

Every change the verdict asks for is made; nothing else in the branch's results changes.

| review item | change | evidence |
|---|---|---|
| merge conflict in `PLAN.md` | `main` merged into the branch (c31c6a9); the desktop's four Phase 9 bullets kept first, then Phase 10 | `git merge-tree` against `main` is now clean |
| 1. the gate passes on skipped tests | `prng-time/gate` runs `work/tests/run_gate.py work.tests.test_prngx_time` (and the GPU path `run_gate.py work.tests.test_bgmt64`); both fail on a skip | `GATE PASSED`, 5 tests, 0 skipped (laptop) |
| 1. Ruby claimed, not verified | no Ruby on either machine, so the claim is qualified everywhere (campaign text, `time_campaign.py`, the engine comments, the log, `CAMPAIGNS.md`, `PLAN.md`): map 3 is "Ruby's documented `rand(n)`, not checked against a Ruby"; the GPU path's `ruby` generator is labelled the same way in the runner summary | text changes only |
| 2. plants made by the engine itself | `time_verify.plant_windows` plants with keys built outside the engine (CPython `random.Random`; the java.util.Random specification) under the engine's anti-repeat rule; `work/layer2/plant_ref.py` writes the two-layer cipher in Python from the library's stream values; `test_prngx_time`, `test_layer2` and `layer2/selftest.py` now plant only that way | `test_prngx_time` 5/5, `test_layer2` 3/3 (both through `run_gate.py`, 0 skipped); `layer2/selftest.py` 14/14 with the independent plants (`results/layer2/selftest.txt`); all prngx suites 10/10 |
| most valuable next step: the GPU port | done on the desktop (3a0cc99); the campaign now uses it: on a validated GPU `prng-time` runs `work/phpmt/time_gpu.py run <gen> --only <month>` behind `test_bgmt64` (java, py3, java-abs, ruby; about 9 h for the window), the CPU engine stays the fallback (about 210 h) | `python jobs/overnight.py list -v` on a CUDA machine: gate + 100 month steps |

Not changed, as the review says: coverage is section 0.7 with one pad from the first LP2 rune; the `layer2` negatives cover the solved keys and the
20 core streams, not seeded-generator streams. The commit author name on the laptop is the user's decision (see the end of `docs/SESSION_LOG.md`).

## Update after the final push of the `kscreen-typo` results (f096a8c, 2026-10-17 19:40)

Added lines scanned for the host name, the user name and absolute paths: clean except one comment line in `typo_summary.txt` and its log that names the interpreter by a home-relative (tilde) path. Results read as data and re-tested with my
shared-key test (`work/log/phase10_keyless_power.md`, 1b): negative; the summary's 'CANDIDATE - inspect' line is an artefact of the verify rule. `work/log/typo_restarts_2026-10-17.md` still carries PENDING placeholders.
**Merged on 2026-10-17 (evening) after the desktop's second session was committed (9faf953).** Conflicts and how they were settled:
- `work/crib_fluency_null.py`, `work/crib_matrix_check.py`: both sides had made the same `lp.word_spans` change; main's text kept. Their two result files rerun on the merged tree (the page-seam fix is now in): the matrix
  check is identical to the laptop's (158 cipher words in 0.7); the fluency check differs only in the bigram model's corpus size (2,102,767 word tokens here, 2,108,966 on the laptop: the two PCs' `ref/corpora` differ), same conclusions.
- `PLAN.md`: both sets of bullets kept (main's, then the laptop's Phase 10 section). `docs/prs/INDEX.md`: the laptop's row with the status rewritten.
Checks on the merged tree (CPU, GPU hidden): the Rust engines prngx, layer2 and kscreen rebuilt (the old prngx binary failed four vector tests until rebuilt); `python -m unittest discover -s work/tests`: 144 run, 0 failures,
15 errors that are all `cudaErrorNoDevice` (the GPU-dependent tests of bgmt, bgmt64, step28, stepmt, not run because the GPU was kept free), 6 skipped (GPU); `run_gate.py work.tests.test_prngx_time` and
`work.tests.test_layer2`: GATE PASSED, 0 skipped; `work/layer2/selftest.py` on the desktop: 14 of 14 PASS (`results/layer2/selftest_desktop.txt`); `work/kscreen/export.py` rerun so the plant files carry the new word lengths.
Privacy: the added lines of the whole merge contain no user name, computer name or absolute path; the laptop's runner logs carry home-relative (tilde) interpreter paths, the runner's own scrubbing.
Not done: the GPU tests (bgmt, bgmt64, stepmt, step28 CUDA) were not run on the merged tree; the two review items about coverage (section 0.7 only; layer2 negatives cover the solved keys and 20 core streams) stand.
