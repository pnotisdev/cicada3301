# R4 repair s07: one reference simulator `work/r4fix/r4sim.py` (2026-10-23)

Nothing in LP2 is solved. No LP2 ciphertext was used or decrypted. Idea 14 of `work/laptop_review/11_next_100.md`.

## Question
The R4 fit (`work/phase57_mechanism.py`, null slot 0..L, vectorised) and the R4 plants (`work/phase57_pilot.py::make_r4`, `work/chanscreen/v2/step4/plant_mid.py`, `plant_edge.py`, interior slot 1..L-1)
each carry their own copy of the mechanism and drifted apart. Build one simulator every later plant generator and simulation imports, with every semantic stated and every disagreement exposed as a parameter.

## API
`from r4sim import encrypt_r4, invert, words_from_lengths` (put `work/r4fix` on `sys.path`). Pure Python + numpy, no repository imports. One call = one section (no check at its first rune, nothing carries over).

    encrypt_r4(plain_words, key, rng, *, q=0.81, repair='T'|'uniform', lag=6, T=T_MAP, nu=0.45, slots='any'|'interior'|'edge'|'start'|'end',
               nulls_per_word=(1.0,), min_word=2, null_check='left'|'both'|'none', null_visible=True, lag_basis='cipher'|'real',
               channel='hold'|'spend', sign=+1, key_start=0, n_cipher=None) -> R4Result

`plain_words`: list of words (sequences of runes 0..28). `key`: array indexed by the key pointer (IndexError if exhausted). `rng`: `random.Random` or numpy Generator.
`R4Result` (numpy arrays over cipher runes): `cipher, word_start, word_end, is_null, is_repair, repair_is_T, key_index, plain_index, word_id, word_pos, null_slot`; scalars `plain_consumed, key_end`; `plaintext`.
`invert(res, key, sign)` decrypts every real rune with its recorded key index and returns (plaintext, repair mask). `n_cipher` cuts the output after that many cipher runes (sections of fixed length).

## Semantics (all in the module docstring)
| term | definition |
|---|---|
| null | one extra keyless rune; a word of L >= `min_word` (2) plaintext runes gets nulls with prob `nu`; the count is 1, 2, .. with probabilities `nulls_per_word` |
| slot s | null emitted just before plaintext rune s (s = L: after the last); cipher position in the word = s (+ earlier nulls of the word) |
| `slots` | any: uniform 0..L (L+1 values); interior: 1..L-1; edge: 0 or L (1/2 each); start: 0; end: L. k nulls = k independent draws, sorted |
| checked (`null_check`) | none: uniform; left: value != previous cipher rune of the output (null or real; none at section start); both: also != the right neighbour (the pre-repair encryption of the next plaintext rune if that is the next element, else redrawn in place once the neighbour exists) |
| visible (`null_visible`) | True: the anti-repeat rule compares x with the previous cipher rune, a null counts. False: with the last REAL rune (repairs are real) |
| anti-repeat | x = p + sign*key[j] mod 29; if x == prev, with prob q the rune is repaired; no check at the first rune of the call |
| repair | uniform: uniform on the 28 runes != prev. T: T(c[-lag]) = 24-2c if the rune `lag` back is in the same word and != prev, else uniform != prev. The plaintext rune of a repaired position is lost in every mode |
| hold / spend | a repair leaves the key pointer (hold) or advances it (spend); a normal real rune advances it; a null never does |
| word position | `lag_basis='cipher'`: counts every cipher rune of the word, nulls included, out[-lag] with >= lag cipher runes before it in the word. `'real'`: counts real runes only, looks back in the real stream |
| word flags | start / end flag on the first / last CIPHER rune of the word (a slot-0 null carries the start flag, a slot-L null the end flag) |
| `key_index` | pointer used by the rune (for a repair the pointer whose key collided); -1 for a null. `plain_index`: plaintext rune index (for a repair the lost one); -1 for a null |

## Presets that reproduce each existing script
- phase 57 R4 (fit): `slots='any', null_check='left', null_visible=True, repair='T', lag_basis='cipher', q=0.81, nu=0.448`; its fresh random key per step = an iid key with `channel='spend'`.
- phase 57 R3: `q=1, slots='any', null_check='none', null_visible=False, lag_basis='real'`.
- phase 57 R7 (end check rune): `slots='end', null_check='left'`.
- `phase57_pilot.make_r4`: `slots='interior', null_check='left', null_visible=True, repair='T', lag_basis='cipher', nu=0.45`, channel hold (`m04`) or spend.
- `plant_mid.make_plant`: `slots='interior', null_check='none', null_visible=False, repair='uniform', nu=0.42`; `plant_edge` nullf / nulli: `slots='end'` / `'start'`, same flags (its `adv` kind is NOT covered).
Not covered: phase 57 R2 (collision -> null), R5 (null value = T), R6 (per-rune null), R8 (plaintext F -> T); the plant_edge skip5 / coin channels.

## Disagreements found between the existing scripts (each is a parameter now)
1. **Slot range** (the known one): phase 57 sim and `mech25/insert47` draw 0..L (`rng.integers(0, Ln+1)`); `make_r4`, `plant_mid` (`randrange(1, L)`) and the phase 51 decoder use 1..L-1. Parameter `slots`.
2. **Null visibility and check**: phase 57 R4 (non-blind) = visible and checked; R3 / phase 47 / `plant_mid` / `plant_edge.step` = invisible (`ell` = last REAL rune) and unchecked; `make_r4` = visible and checked. Parameters `null_visible`, `null_check` (independent).
3. **T repair**: phase 57 R1/R3/R4 and `make_r4` write T(c[-6]); `plant_mid` / `plant_edge.step` always repair with a uniform rune. Parameter `repair`.
4. **Lag with nulls present**: phase 57 non-blind R4 and `make_r4` count the six runes back in the cipher stream (a null in between counts); phase 57 blind R3 counts six REAL runes back (`RH`, `off >= LAG`). Parameter `lag_basis`.
5. **Key**: phase 57 draws a fresh uniform key at every step (hold and spend are indistinguishable, = spend with an iid key); the plants use library keys with hold (m04) or spend. Parameter `channel`.
6. **Null rate**: 0.448 (phase 57 fit), 0.45 (`make_r4` rho), 0.42 (`plant_mid.RHO`, `plant_edge.RHO`, decoder nu). Parameter `nu`.
7. **Sections**: phase 57 resets the check at section starts (and jumps the plaintext to the next word start); plants are single windows. One r4sim call = one section (callers loop; test 4 shows how).
8. **Word-start flag**: phase 57 flags the first cipher rune (the null for slot 0); `make_r4` flags the first plaintext rune (same thing for interior slots); `plant_edge` nulli flags the null. r4sim: first cipher rune (end flag: last cipher rune).
9. Minor: phase 57 draws one random number per rune whether needed or not, the plants only on a collision (same distribution, different streams). In phase 57 blind mode `lastreal` is not reset at a section start (a section-initial slot-0 null can leave the previous section's last rune as `prev`); r4sim resets it.
10. Data (orchestrator note): `fam_data.english` silently uses only the corpora that exist; with Emerson alone the fitted rate is 0.399, not 0.448. Test T0 now fails loudly when a corpus named in `fam_data.CORPORA` is missing. All numbers below are from the full corpora (150,004 words); two earlier runs with Emerson only are superseded.

## Tests (`python -B work/r4fix/test_r4sim.py -v`; 12 tests, OK; 85 s wall, 75 s CPU, one process, below-normal priority)
- **T0** corpora present (`english()` gives 607,561 runes, 150,004 words).
- **T1** q 1, no nulls, 20,000 runes: 0 doublets for repair T / uniform x hold / spend x visible / not (8 runs). Control q 0: 728 doublets (expect 690 +- 26). q 1 with nulls at nu 0.45: visible + left-checked 0, visible + both 0; controls: invisible 52, unchecked 51, invisible + unchecked 75 residual doublets (phase 47's mechanism).
- **T2** slot histograms, 6,000 nu-1 words per length L in {2,3,5,8}, q 0, all five modes: Wilson-Hilferty z of the chi-square against the declared rule between -1.11 and +1.13 (any L=8: chi2 10.0 / 8 dof; interior L=8: 5.8 / 6); start / end exact; cipher position = slot. Power controls: a wrong rule gives infinite chi2, interior tested against any rule z > 20, a planted 15% excess at slot 0 gives z 5.2 (threshold 3.5). Rates: 0.4456 of 35,513 multi-rune words carry a null (target 0.45, se 0.0026: 1.7 se low), two-null share 0.2918 (target 0.30, se 0.0036: 2.3 se low); no null in one-rune words; never more than 2.
- **T3** null checks (6,000 words, nu 0.9, 1 or 2 nulls, q 0.81): left: 0 nulls equal their left neighbour in 8,131 (visible) and 8,156 (invisible); both: 0 equal either neighbour in 8,015 / 8,119 (adjacent nulls included). Controls: unchecked 299 of 8,044 equal left (expect 277), 'left' leaves 54 / 269 equal right.
- **T4** against `phase57_mechanism.simulate` (R4 as in RULES, rate 0.448 fixed, LP2 section layout, English from the full corpora), 100 replicates, r4sim with `channel='spend'`: mean phase 57 / mean r4sim (z): doublets in-word 59.2 / 59.9 (-0.59), across gaps 16.75 / 17.74 (-1.67), T hits in-word 76.5 / 77.1 (-0.34), words 2892.2 / 2904.1 (-1.52). All within 3 se. `hold` (40 replicates, reported, bound 4 se): 59.4 (-0.14), 17.0 (-0.32), 79.3 (-1.18), 2888.0 (+0.39). (A scratch 200-replicate run on the Emerson-only data gave z within +-1 for spend and nw z +2.1 for hold; superseded.)
- **T5** against `make_r4` (400 plants, a counting word list and a recording `random` shim patched in for the call only, synthetic key and plaintext, LP2 word lengths): null rate per multi-rune word pilot 0.4507 (14,760 draws / 32,750 words), r4sim 0.4483 (52,223 / 116,502), target 0.45 +- 0.0027. Every pilot draw is interior; slot histograms are uniform in each L (z < 3.5) and homogeneous with r4sim's interior mode (L 3..10, total chi2 51.0 / 36 dof, z 1.64). 300-rune windows: nulls 26.56 vs 26.66 (z -0.42), doublets 1.692 vs 1.684 (z +0.11). A separate 12,000-plant scratch run: pilot draws against exact uniform, total chi2 91.5 / 78 dof (z 1.07), rate 0.4500. (A 3,000-plant run showed chi2 117 / 78, z 2.8, with an excess at L=7 and 12; a second seed set gave z 1.6; judged chance.)
- **T6** ground truth, 6 configurations (hold / spend, sign +-1, visible or not, cipher / real lag, T / uniform repair, all slot modes, 1-2 nulls, checks none / left / both): the recorded plaintext is the flat plaintext prefix, one rune per non-null cipher rune; removing the nulls and inverting with the recorded key index recovers the plaintext exactly except at repair positions (> 50 repairs each); the key pointer steps 0 (hold repair) or 1; every T repair equals T(c[-6]) of the right stream and sits at word position >= 6; null slots obey the mode, none in words of length 1.
- **T7** (extra) no nulls, uniform repair, q 0.81 against `plant_edge.step` (m04 / spend), 100 sequences of 2,500 runes: doublets 16.12 vs 16.44 (z -0.56) hold, 16.32 vs 16.70 (z -0.65) spend; key pointer 2430.7 vs 2431.1 (z -0.3), 2500.0 vs 2500.0.

## What this does NOT establish
- It reproduces the stated rule's distributions; it does not show Cicada used R4. Tests 4 and 5 compare means of a few statistics (and slot histograms and rates), not whole distributions; T5's plaintext is uniform, T4's English.
- T4 matches the spend channel with an iid key only; hold with a structured library key is checked in T7 (no nulls) but not against nulls and T repairs in any other script. The two-null share is 2.3 se below 0.30 in the one seed run (within the 3.5 bound), not re-run with other seeds.
- Phase 57 R2 / R5 / R6 / R8 and the skip5 / coin channels are not implemented. 'both' (right neighbour = pre-repair next rune plus in-place redraw) exists in no earlier script.
- No plant was regenerated and no decoder run. Next sessions should use `slots='any'` / `'edge'` with `null_visible=True, null_check='left'` for R4 plants, and keep `slots='interior'` only for comparison with the old negatives.

## Files
`work/r4fix/r4sim.py`, `work/r4fix/test_r4sim.py`, this log. CPU: about 9 minutes in all (test runs 82 + 117 + 99 + 75 s while developing, two scratch diagnostics of 40 and 74 s), one process at a time, below-normal priority.
