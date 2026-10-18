# Methodology audit: the five assumptions most likely to be wrong

LP2 (0.7–0.15, 12,956 runes). Ranking = plausibility-of-wrong × cost-of-finding-out-late, from the 56-experiment ledger (`docs/registry.toml`), the coverage ledger (`docs/NEGATIVE_SPACE.md`), the prior review (`work/log/phase10_review.md`) and the engine sources. All citations are repo-relative file:line.

## 1. Word separators = plaintext word boundaries  (C)

**Where baked in.** The dictionary scorer of `work/phpmt/src/main.rs:400-403` counts "runes inside dictionary words" and scores only at `word_end` (`:469-475`); `work/lp.py:180-187` builds words from transcription tokens; `work/walk/src/dsearch.rs:1-5` models a per-word key, so its pair counts die with the word cuts. The blindness is admitted in `docs/registry.toml:315,361,423` and `docs/NEGATIVE_SPACE.md:14-17`.

**Evidence it is wrong.** `work/log/phase9_families.md:15-17`: the lag-1 correlation of adjacent word lengths is −0.008 for LP2 against −0.149 ± 0.033 for English runes — LP2 is 4 sd away, "so the separators are not English word boundaries". A planted key scores 33 with its own word cuts and 0 with LP2's cuts imposed (`docs/NEGATIVE_SPACE.md:14-16`). LP2's length histogram rejects English (p ≈ 10⁻⁴⁵, `docs/registry.toml:636-637`; G = 227, `docs/CAMPAIGNS.md:151-160`).

**Cheapest falsifying test — FREE (pure analysis of committed data).** ~20-line Python: per section, the lag-1 word-length correlation of LP2 against the committed English reference (−0.149 ± 0.033, `phase9_families.md:15-17`). Planted control: the committed 33→0 measurement (positive: 33 with natural cuts). Null: section-shuffled word orders. **Decision rule:** if every section's correlation sits >2 sd from −0.149 (pooled LP2: −0.008, 4 sd), the assumption is falsified per section and every dictionary-scored negative (prng-dict, rescreen, dsearch, prngx A/B) is void. Minutes-scale add-on: confirm the boundary-free +300 gate has power on all 8 section starts by reusing the pure-Python reference in `work/phpmt/bg.py:75-80` with `work/phpmt/data/bigram.txt` (planted key passes ≥98% of 120-rune windows, `results/analysis/assumption_checks.txt:3-11`; 1,000 random streams stay < +300).

## 2. Anti-repeat = skip/coin, every rune consumes exactly one key value, pointer moves only forward  (B)

**Where baked in.** Only two models exist: skip and coin, both forward-only (`work/kscreen/src/main.rs:9-13`; `work/phpmt/src/main.rs:440-464` pushes only j+1/j+2/j+3; `work/lp.py:207-216` does j += 1 per rune). A rune that consumes **no** key value desynchronizes every decoder; the repo says so: `docs/NEGATIVE_SPACE.md:27` (blind spot 9) and `work/log/phase10_review.md:14-17` (gaps 2–3); queued as priority 2 (`docs/registry.toml:664-674`).

**Evidence it is wrong.** The only word-length model not rejected is "+1 rune in ~42% of multi-rune words" (p = 0.085; `docs/registry.toml:636-637`, `docs/CAMPAIGNS.md:156-158`) — exactly what a keyless padding/check rune per word looks like. The twist-at-in-word-collision variant W3, which consumes collision budget differently, is "not excluded" (`work/log/phase10_skeleton5.md:24-26`).

**Cheapest falsifying test — minutes, ~50 lines of Python.** Encipher Emerson (`work/ref/emerson_essays1.txt`, runes via `lp.word_to_key`, as `work/phpmt/bg.py:51-56`) with a planted library key, no skips; variant adds one random keyless rune at the end of 42% of words; decode both with the true key using the standard aligned forward pointer (`work/lp.py:207-216` semantics) and score 300-rune IoC. **Controls:** no-insertion plant ≥ 1.57 (`results/analysis/assumption_checks.txt:14-15`); random-key null ≤ 1.37 (`docs/registry.toml:23`). **Decision rule:** insertion plant < 1.40 in ≥95% of 100 replicates ⇒ a true key of this family is invisible to every existing screen, so the 56 negatives cannot be cited against it.

## 3. The key is a stream indexed by global position  (I)

**Where baked in.** The beam state is the global key pointer j, "states merged on the pointer; the future depends only on it" (`work/kscreen/src/main.rs:14-15`; `work/phpmt/src/main.rs:478`; `work/lp.py:207-216`). No per-word or position-in-word state machine is decodable by any engine.

**Evidence it is wrong.** Both echoes are strictly word-internal: lag-5 equality within z +3.65 vs cross z +0.04; lag-6 relation within z +5.16 vs cross z +0.05 (`results/analysis/echo_position.txt:3-9,22-27`); "a mechanism must know where words begin and end" (`docs/NEGATIVE_SPACE.md:82-84`). No structureless global model reproduces the S-concentration (calibrated chance 0.0073; "a mechanism has to contain a fixed element (S)", `work/log/phase9_families.md:60-62`), and the evolving-alphabet walk is "the one family the fingerprint leaves standing" (`docs/registry.toml:459-469`).

**Cheapest falsifying test — FREE (committed data).** The planted controls in `results/analysis/echo_position.txt:34-37`: a position-independent echo spreads excess across boundaries (+162.1 lag-5, +321.5 lag-6) where LP2 has +0.8 and +1.1. A mechanism whose state depends only on global position cannot confine an echo to words. **Decision rule:** cross excess ≤ 3% of the within excess (LP2: 0.8/31.1, 1.1/35.1) ⇒ I is falsified for LP2's mechanism. Minutes-scale add-on (~40 lines): simulate W3 (per-word state, T applied at in-word collisions, `phase10_skeleton5.md:24-25`) and require `work/families/fam_fingerprint.py` to reproduce within-word lag-5 z ≥ 3 with cross z ≤ 1 (control), where the additive global stream reproduces 8/10 but fails z5/maxz5 (null, `phase9_families.md:37`).

## 4. The cipher is additive mod 29 in GP-order indices: c = D(p) + m·k + b  (A)

**Where baked in.** The formula is the engine's header (`work/kscreen/src/main.rs:3-7`); decode is plain modular subtraction (`work/phpmt/src/main.rs:410-417`; `work/lp.py:195-196`); 28 key multipliers (`docs/registry.toml:68-79`).

**Evidence it is wrong.** The lag-6 relation c′ = 24 − 2c (z +5.0; `docs/registry.toml:623-630`) is multiplicative — no additive stream produces it; its T(x) = 24 − 2x is the same map whose twist W3 survives, and 24 = 3301 mod 29 (`docs/registry.toml:70`). A two-layer cipher yields IoC 1.1–1.2 and is blind (`docs/NEGATIVE_SPACE.md:23`). "Prime-value" arithmetic mod 29 is not even a permutation: F (prime 2) and D (89) share residue 2, N (29) → 0 (`work/lp.py:17-24`) — a lossy operation no screen models.

**Cheapest falsifying test — minutes, existing kscreen binary.** Plant c = π⁻¹(π(p) + k) with π a random permutation of 0..28 and a **non-constant** library key (with a constant key it collapses to a fixed substitution, which D already covers — `kscreen/src/main.rs:5-7`). Screen 5 random πs, one 300-rune window, `mults=1, models=0` on the built `kscreen` (5 × ~1,400 × ~160 ≈ 1.1 M decodes, ≈ 1 min; the 409 M-decode reference took 19 min, `docs/registry.toml:62`). **Controls:** π = identity plant recovered at the exact offset, IoC ≥ 1.6 (`docs/registry.toml:21-22`); `rand:300` null ≤ 1.37 (`:23`, `work/kscreen/src/main.rs:31`). **Decision rule:** all π-plants < 1.40 while the identity plant ≥ 1.6 ⇒ the additive coverage claim is falsified for non-affine arithmetic, and the 4.5 B-decodes say nothing about it.

## 5. 300-rune windows at section/page/heading starts  (D)

**Where baked in.** Windows are the 8 section starts and page/heading starts (`work/kscreen/export.py:41-51,62-88`); n defaults to 300 (`work/kscreen/src/main.rs:676`); the 1.40 rule is per 300-rune window (`docs/registry.toml:20-23`).

**Evidence it is wrong.** Planted keys: 45/45 recovered at 250–300 runes but only 13/21 at 0–149 (`docs/NEGATIVE_SPACE.md:18-19`); "A key that is right only somewhere else is not tested" (`:20-21`). Short-window maxima are heavy-tailed (`docs/registry.toml:492,503-505`). Mid-page starts are the one placement gap, queued priority 11 (`docs/registry.toml:759-767`).

**Cheapest falsifying test — minutes, existing kscreen binary.** Hand-write ~12 staggered 300-rune windows starting at mid-section positions (~15 lines in the `export.py` format, `work/kscreen/export.py:35-38`), then `kscreen screen staggered.txt file:library.ksb --mults=1 --models=0` on 16 threads: ≈ 12 × 1,447 × ~160 ≈ 2.8 M decodes ≈ 1–2 min. **Controls:** plant mode (`work/kscreen/src/main.rs:24`) plants a library key at a staggered start (must recover ≥ 1.6); `rand:300:1` null (≤ 1.37). **Decision rule:** any stream with IoC ≥ 1.40, +0.15 over its matched null, surviving whole-window `verify.py` (`docs/CAMPAIGNS.md:97-107`) ⇒ the placement assumption is wrong; otherwise it holds for the library at staggered starts (one sign/model; the other 3 combos are a 4× rerun).

## Compact table

| # | Assumption | P(wrong) | Cost | Cheapest falsifier | Free? |
|---|---|---|---|---|---|
| 1 | C: separators = plaintext words | highest (4 sd + 33→0 already on record) | all dictionary lanes void | per-section word-length correlation | **free** |
| 2 | B: skip/coin, 1 key value per rune, forward pointer | very high (repo's own priority-2 gap; +1-rune fit p 0.085) | every decoder desyncs | keyless-insertion plant blinds aligned decoder | minutes |
| 3 | I: global-position stream state | high (word-internal echoes; S needs fixed element) | all engines state-free of words | cross-boundary echo null (+160/+320 plants vs LP2 +0.8/+1.1) | **free** |
| 4 | A: additive mod 29 in GP indices | moderate-high (lag-6 T(x)=24−2x; W3 alive) | 4.5 B decodes moot | conjugate-permutation plant invisible to kscreen | minutes |
| 5 | D: 300-rune windows at starts | moderate (45/45 vs 13/21 power curve) | all IoC negatives inherit the hole | 12 staggered windows × library, ≈3 M decodes | minutes |

## Deprioritized

E (scoring rules: outer alphabet excluded, +300 gate English-tabled) is my strongest non-listed suspicion: a keyword-mixed ciphertext alphabet is a real blind spot (`docs/registry.toml:653-663`) and the +300 power holds only at 120-rune windows (`work/log/phase10_review.md:13`). It is deprioritized because it is already tracked at priority 1 with a designed planted control, IoC is invariant under plaintext-side relabelling so half the damage is bounded (`work/kscreen/src/main.rs:14-17`), and the cheap fix (relabel-then-screen) needs GPU hours rather than minutes. F folds into A/E (GP rotations are exactly the covered shift b, and all 812 affine relations were scanned), and G is covered for continuous keys by the per-section offset sweeps, with reuse proven untestable (power 0.05–0.42, `docs/registry.toml:510-517`).
