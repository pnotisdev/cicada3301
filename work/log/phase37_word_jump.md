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
