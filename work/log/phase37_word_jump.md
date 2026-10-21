# Phase 37: "words are the map" as a key-pointer JUMP (engine option advsep=3|4|5) (side session, 2026-10-21)

Nothing in LP2 is solved. Rank 2 of `phase34_2016_message_map.md`: at each word boundary the key pointer advances by an extra n_w or a constant, generalising `advsep=1` (row `advsep`: +1 per boundary, excluded). **The gate was built and passed with two documented near-misses; the 581-stream screen was NOT run: its measured cost is above the 6-hour limit (below), so this is the cost note.**

## The option (`work/kscreen/src/main.rs`, docs `ADVSEP.md`; `adv_positions` and the three `advsep` parsers; `advsep=0|1|2` code paths unchanged)
Extra key values consumed at each word boundary b < rune count (word edges from the window's L line, exactly the advsep=1 convention; the advance is applied to every beam state before the next word's first rune, then the skip/coin logic of that rune runs as before; no line/page breaks in modes 3-5):
- `advsep=3`: n_w, the length of the word just ended (the extra values equal the words' own lengths: the pointer jumps by 1 + n_w per word boundary pair);
- `advsep=4`: a constant 2;
- `advsep=5`: the length of the NEXT word.
Same safety fallbacks as advsep=1 (missing / zero / non-summing L line -> no advances for that window). `key_need` grows by the window's own advance sum, so screens never run past a stream.
The engine was built into its OWN target dir: `CARGO_TARGET_DIR=work/kscreen/target/advlen cargo build --release --offline` -> `work/kscreen/target/advlen/release/kscreen.exe`. The release and pdir binaries (queues) were not rebuilt.

## Default behaviour is bit-identical (proved)
- `python work/kscreen/pdir_identity.py --orig target/release/kscreen.exe --new target/advlen/release/kscreen.exe` (absolute paths) -> `results/kscreen/wordjump_identity.txt`: **PDIR IDENTITY PASSED**, every case IDENTICAL (default, sign S lines, guard G, nulledge 1/2, **advsep=1, advsep=2**, dir=back, clock, short windows: trace of 3,840 decodes and the whole screen file equal).
- `selftest.py` with the new binary (`S.BIN` overridden) -> `results/kscreen/wordjump_selftest.txt`: **SELFTEST PASSED** (lin2 / poly2 / library plants, null best 1.306 < 1.40).

## Controls (`work/kscreen/wordjump_control.py` -> `results/kscreen/wordjump_control.txt`, `work/tmp/wj_control.log`)
Independent Python planter (does not use the engine's `plant`): held-out English windows (`work/phpmt/data/english.txt`, 300 runes with their word lengths), `library_flat.ksb` streams (sha256/sha512 hash streams of cicada strings, random offsets up to 16,462), the fitted 81% enforcement (`KEEP` 0.18-0.19), both models, multipliers 1 and 28, plain / substituted alphabet; four plants per mode.
- **Positive:** 12 of 12 plants are returned by the engine with the same advsep **at the exact planted offset** (offset == truth in all 12), re-decode at the truth equals the best IoC. IoC >= 1.60 in **10 of 12**: advsep=3 1.749, 2.056, 1.749 (+ 1.584); advsep=4 1.671, 2.056, 1.757 (+ 1.589); advsep=5 1.772, 2.056, 1.626, 1.749. The two below the pre-set 1.60 gate (**FAIL as defined**: advsep=3 sha512-ctr cicada3301, model 0, mult 28, substituted: 1.584; advsep=4 sha256-chain 3301, model 0, mult 28, substituted: 1.589) are plants on the third English window (index 2), whose plaintext IoC is intrinsically low: the repository's own selftest plants on the same window give 1.609-1.617 (`results/kscreen/selftest.txt` plant_2), so the engine recovers the key at the exact offset and the shortfall is the plaintext. I did NOT relax the gate after the fact; the control run reports FAILED and these two numbers stand.
- **Blind:** the default engine and the wrong conventions on the same ciphertext stay 1.23-1.34 (advsep=0, 1 and the other word-jump modes): the conventions are distinguishable and the default screens cannot see a word-jump key.
- **Null:** `rand:300:373/374/375` on the 8 section windows, mults=1, models 0,1, advsep=3/4/5: best **1.3145 / 1.3469 / 1.3165** (all < 1.40).

## Cost of the screen (not run)
The flat-library sweep is 581 streams x 8 windows x mults 1 and 28 x 2 models = about 355 M decodes per mode (phase 34 note: 6.4 min on 14 threads). Measured on this machine at **2 threads while the other queues run: 92.7 M decodes in 1,244 s (advsep=3), 93.5 M in 1,409 s (4), 92.7 M in 1,027 s (5) = about 66-90 k decodes/s**, so one sweep of one mode is **about 1.1-1.5 hours**. The task's plan (3 modes x [real + matched null] = 6 sweeps, plus verify.py) is about **7-9 hours** at 2 threads: over the 6-hour limit, so the screen was not started. Real sweeps only (3 modes) would be about 3.5-4.5 hours; one null per mode doubles it.

## How to run it (nothing else needed)
```
cd work/kscreen
B=target/advlen/release/kscreen.exe
$B screen data/segments.txt file:data/library_flat.ksb ../../results/kscreen/wordjump3_segments.tsv mults=1,28 models=0,1 advsep=3 threads=2
$B screen data/segments.txt rand:581:373 ../../results/kscreen/wordjump3_null.tsv mults=1,28 models=0,1 advsep=3 threads=2   # matched null (581 streams x 20000)
python verify.py ../../results/kscreen/wordjump3_segments.tsv --top 15 --controls 20      # verify.py passes advsep through; rule 1.40 + 0.15 margin
```
and the same with advsep=4 (the constant 2) and advsep=5. A queue entry can run the 3 real sweeps first (about 4 h), the nulls after. The engine option and the controls are in place; only the sweeps remain.

## What this does NOT cover
Jump rules other than the three built (n_w of the previous word, 2, n_w of the next word; no cumulative length, rule-chosen 1-3, advances at only a fraction of the boundaries, advances at line / page breaks combined with word lengths); a jump that depends on the word's content; a jump together with nulls; windows other than the section starts; GPU (gpu.py rejects advsep != 0). The two near-miss plants show the 1.60 recovery threshold is sensitive to the plaintext window's own IoC.

## Restated gate (written BEFORE the fresh plants were run; 2026-10-21)
The first gate demanded IoC >= 1.60 at the planted offset; two plants on a plaintext window with an intrinsically low IoC missed it by 0.01-0.02 with the key recovered at the exact offset. The new criterion does not depend on the window's IoC: **a plant passes if the engine with the same advsep returns the planted stream at the exact planted offset AND its IoC is >= 0.9 x the plaintext window's own IoC (measured on the 300 plaintext runes before encryption) AND the re-decode at the truth gives the same IoC; the default engine (advsep=0) and advsep=1 on the same ciphertext must stay < 1.40.** Twelve fresh plants (4 per mode, the same mix of model / multiplier / alphabet substitution) on twelve NEW plaintext windows (Walden, not the three windows of english.txt), then the three nulls from before are unchanged (< 1.40). The criterion is used as written; nothing is changed after seeing the plants.

## Result of the restated gate (12 fresh plants on 12 new Walden windows; `work/kscreen/wordjump_control2.py`, `results/kscreen/wordjump_control2.txt`): **FAILED as written, 10 of 12 pass**
Passing plants: engine returns the planted stream at the exact offset with IoC 1.575-1.926, never below the window's own IoC (best 1.684 vs own 1.670, 1.714 vs 1.710, 1.575 vs 1.575, 1.877 vs 1.877, 1.838 vs 1.834, 1.902 vs 1.896, 1.785 vs 1.785, 1.818 vs 1.803, 1.926 vs 1.926, 1.641 vs 1.641), re-decode at the truth equal; the default engine and advsep=1 on the same ciphertexts 1.240-1.304 (blind).
The two failures, reported as they came:
1. advsep=3, `primes reversed digits`, model 0, mult 1: the engine's best is **1.819 at offset 17,686, truth 17,685** (one off: the known skip-model alias; the other selftests accept +-5), IoC above the window's own 1.805, re-decode at the truth 1.813. The criterion demanded the exact offset: FAIL.
2. advsep=5, `sha256-ctr reject :2014`, model 1, mult 28, substituted: exact offset 3,453, but the screen's beam (16) returns **1.662 while the re-decode at the truth (beam 64) gives 1.721**, a 0.059 difference against the 0.02 tolerance of the criterion (1.662 is still above 0.9 x 1.721 = 1.549): FAIL. This is a beam-16 shortfall, not a missed stream.
Neither failure is a missed key or a blind spot of the option (both plants were located at the right stream and offset to within 1), but the gate was fixed in advance and is not relaxed. **The queue was therefore NOT launched.** If the owner of the decision accepts "within 1 offset and IoC >= 0.9 x the window's own IoC at the engine's own screen beam" as a criterion, all 12 would pass; that would be a post-hoc change, recorded here as an option, not applied.

## Queued (prepared, NOT launched)
`jobs/queues/wordjump.txt` (WAIT lines for book_key_screen, pdir_pilot / pdir_verify and layout_queue, then advsep3, null-advsep3, advsep4, null-advsep4, advsep5, null-advsep5 at 14 threads with verify.py on the top 15 after each real screen) and its job runner `work/kscreen/wordjump_queue.py` (uses `target/advlen/release/kscreen.exe` via KSCREEN_BIN for verify). Dry run: `wordjump_queue.py 3 --streams 1` and `4 --null --streams 3` ran to the end (screen with `advsep=3` in the header, verify.py passed the option through: "0 of 8 re-decoded hits keep IoC >= 1.4"); dry outputs deleted. To launch after a gate decision, from the repo root in PowerShell: `$env:QUEUE_MAX_WAIT_SECONDS='172800'; Start-Process .venv\Scripts\python.exe -ArgumentList 'jobs\jobqueue.py','wordjump','jobs\queues\wordjump.txt' -WindowStyle Hidden`.

## Decision and launch (2026-10-21)
The user accepted the restated gate with a +-1 offset tolerance (the skip alias every other selftest accepts) and the beam-16 screening shortfall (the key is still found at the exact stream and offset); under that tolerance 12 of 12 fresh plants pass. The queue `jobs/queues/wordjump.txt` was launched detached (14 threads, `QUEUE_MAX_WAIT_SECONDS=172800`); it waits for the booknight, pdir and layout queues. A screen hit still needs `verify.py` (whole window >= 1.40 and +0.15 over 20 random offsets of the same stream).
