# Phase 50: language-independent verifier checks, and the cheap untested block (2026-10-21)

Nothing in LP2 is solved. Two parts: (1) two language-independent checks added to `work/kscreen/verify.py`; (2) the cheap untested block of
`work/log/phase46_todo_and_leads.md` (block B), each item with a planted-key control and a matched null, decision rule 1.40 plus whole-window
verification (`docs/CAMPAIGNS.md`). Machine: the desktop alias, 12 threads, default engine binary untouched (never rebuilt; only run).

## Part 1: the two checks in verify.py

New module `work/kscreen/lang_checks.py` (imported by `verify.py`); `work/prime_check.py` is reused unchanged.

* **A/I oracle** (phase 48): of the window's one-rune words (`lp.word_spans`, the page-safe cut, only words whose rune lies inside the decoded
  window), the number whose decoded value is A or I; reported as `k/n`, with the binomial p at 2/29. Null 2/29 = 6.9%; solved pages 27/27 (phase 48).
* **Prime-sum check** (`prime_check.check`): clauses of the section lying completely inside the decoded window; of those with <= 40 runes, how
  many have a prime Gematria sum (chance 14.7%, solved pages about 56-60%), plus the evidence in nats.
* **Output**: both are appended to the first line of each hit, after the existing `max ...` text:
  `; A/I k/n (p ..., null 2/29); prime short clauses a/b (chance 15%, solved 60%), evidence +x.x nats`. The decision (`REAL? check by eye` /
  `noise`), the other columns, the `decoded` / `by rank` lines and the summary line are untouched; the checks are NOT a gate.
* **Where they apply** (`lang_checks.applies`): windows in LP's own reading order with a forward key and no keyless nulls: `data/segments.txt`,
  `pages.txt`, `heads.txt`, the sign-rule windows `data/signs/*.txt`. For `dir=back`, `nulledge`, reordered windows (item (i) of part 2) and
  other window files the fields read `n/a`: there the plain text has no map back onto words and clauses. The checks use the identity alphabet
  and shift 0, as the solved pages do; a hit whose true alphabet is a substitution is not tested by A/I (phase 48 caveat).
* **Existing output unchanged** (proof): the HEAD version of `verify.py` and the new one were run on two stored hit files
  (`results/kscreen/booknum_segments.tsv`, `advsep1_segments.tsv`; `--top 8 --controls 10`); the new output with the appended
  `; A/I ...` suffix stripped by `sed` is identical to the old output (`diff` empty, both files).
* **Controls** (`work/kscreen/lang_checks_selftest.py`, `results/kscreen/lang_checks_selftest.txt`, PASSED): the eight solved sections with a rule
  (0.0, 0.1, 0.3, 0.4, 0.5, 0.6, 0.16, 0.17) are planted with the library stream `primes-1 (totient)` under the engine's skip rule, then
  decoded by the engine (`kscreen verify`) at the true offset and run through `lang_checks`:

  | case | A/I | prime short clauses |
  |---|---|---|
  | planted true key (8 windows) | 25/27 = 0.93 | 31/66 = 0.47 (exact plaintext: 36/66 = 0.55; the beam decode loses a few runes) |
  | same ciphertext, 160 wrong offsets of the same stream | 36/540 = 0.07 | 163/1320 = 0.12 |
  | uniform random plaintext, 200 draws x 8 windows | 364/5400 = 0.067 (2/29 = 0.069) | 2045/13200 = 0.155 (chance 0.147) |

  The prime check of the Koan windows (0.3, 0.5) is low by itself (the repo's own control gives 2/13 and 1/4 for the right key): the 60% belongs to
  the other pages. The evidence in nats is the number to read, and only with >= 6 short clauses.

## Part 2: the block

(results below; scripts in `work/phase50/`, outputs in `results/kscreen/phase50/`)

Scripts in `work/phase50/` (`reorder.py`, `alphabets.py`, `phrases.py`, `sign_cross.py`), outputs in `results/kscreen/phase50/` (`summary_*.txt`, one
tsv per screen, `*_verify.txt`). Common settings: the default engine (`kscreen screen`, n 300, beam 16, abort 150:1.2, mults 1,28, models skip / coin,
every offset), 12 threads, the eight section windows of `data/segments.txt` (0.7, 0.8, 0.9, 0.11-0.15; 0.10 has 9 runes; first 300 runes of each window),
decision rule: a hit is IoC >= 1.40 on the first 300 runes, then `verify.py` over the whole window (>= 1.40 and >= 0.15 above the same keystream at 20 random
offsets). Every screen has (a) a planted-key control run through the same front end, (b) a matched null (`rand:N` i.i.d. keystreams through the same windows and
flags), (c) `verify.py` on the 10 best distinct hits (5 for item iv). Nothing reached a candidate; **nothing in LP2 is solved**.

## (i) Reading-order transforms (`reorder.py`; pages = `%`, lines = line breaks of the transcription)

Each section's runes are re-read in the new order and the first 300 runes of the reordered window are screened against the 1,439 library streams. `prev = -1` (the
chain across sections is meaningless after reordering). Control: English planted under `primes-1 (totient)` in the *reading* order, printed back into LP's layout through
the inverse permutation, pipeline applied, `only=item` screen: all 8 windows recover the item at the planted offset (+-10; skips shift it by 0-2) with IoC about 1.6-2.1. Matched
null: `rand:300` (about 165 M decodes). `identity` is the pipeline with no reordering (baseline: same windows with prev = -1).

| transform | planted control | library best | null best (rand:300) | verify (top 10) |
|---|---|---|---|---|
| identity (baseline) | 8/8 | 1.3663 | 1.3423 | 0 kept |
| boustrophedon, odd lines reversed | 8/8 | 1.3559 | 1.3507 | 0 kept |
| boustrophedon, even lines reversed | 8/8 | 1.3236 | 1.3288 | 0 kept |
| lines of a page reversed | 8/8 | 1.3184 | 1.3216 | 0 kept |
| pages of a section reversed | 8/8 | 1.3714 | 1.3339 | 0 kept |
| column-major per page (ragged lines skipped) | 8/8 | 1.3229 | 1.3132 | 0 kept |

The first pass of the script labelled the control FAIL (5/8) because three windows had their best offset 1-2 off the planted one (skips shift it); the tolerance was
corrected to +-10 and the controls re-run (`summary_reorder.txt`; the first pass is kept as `summary_reorder_firstpass.txt`, the screens themselves were not repeated).
The A/I and prime checks are `n/a` here (a reordered window has no word map). Not covered: other reading orders (spirals, per-word reversal), the page and head windows
(46 + 18 further windows), a different order per section, two transforms combined.

## (ii) Alternative alphabet orders as the addition domain (`alphabets.py`, front end `relabel_export.py`)

`c = sigma(p + k)`, `sigma[x]` = the rune at position x of the order; the screen sees `sigma_inv(c)`. Five orders: `latin` (runes sorted by Latin spelling, digraph runes after
their first letter), `latin-ng` (the Ing rune filed as NG), `futhark-a` / `futhark-o` (Elder Futhark order, Ansuz read as the A / the O rune, runes it lacks last in GP order;
**25 / 27 of 29 positions equal the GP order**, so these two are nearly the ordinary screen), `rune-names` (alphabetical by Old English rune names, 1 fixed point). Windows:
`data/segments.txt` only (as the earlier relabel runs). Control: planted in the screen domain, printed with sigma, relabelled back, screened; plus a blindness check (the
printed text screened without relabelling).

| order | planted control (8 windows) | blindness (plant without relabelling) | library best | null best (rand:300) | verify |
|---|---|---|---|---|---|
| latin | 8/8 | 1.245 | 1.3475 | 1.3288 | 0 kept |
| latin-ng | 8/8 | 1.272 | 1.3268 | 1.3262 | 0 kept |
| futhark-a | 8/8 | 1.756 (near-identity order: expected) | 1.3178 | 1.3495 | 0 kept |
| futhark-o | 8/8 | 1.954 (near-identity order: expected) | 1.3753 | 1.3533 | 0 kept |
| rune-names | 8/8 | 1.252 | 1.3520 | 1.3727 | 0 kept |

`summary_alphabets.txt` labels the two Futhark controls FAIL because its blindness criterion (unrelabelled plant < 1.40) cannot hold for an order that moves 2-4 runes; the
recovery itself is 8/8 for all five. Negative at the depth of the ordinary screen for the three orders that differ from the GP order; the two Futhark orders differ from it so little
that the earlier ordinary screens already covered most of them.

## (iii) Solved-page phrases as Vigenere keywords (`phrases.py`)

2,310 repeating keys, each as the plaintext runes ("direct") and with digraph runes spelled letter by letter ("spelled"): 44 headings (WELCOME PILGRIM, A WARNING, DIVINITY,
CIRCUMFERENCE, INSTAR, ...; see `HEADINGS`), the 152 clauses of the solved plaintext, their 3-5 word phrases (2,094), the 18 solved sections and all solved text. The library already
holds single words (>= 4 letters) and two-word phrases (`kw:`); these are the longer ones. Screen: every phase of every key, both signs, skip and coin models, in the first 300 runes
of the eight windows (a keyword starting at the section start is one phase; the offset sweep also covers a start elsewhere). Control: three keys (a heading, a clause, a 4-word phrase)
x both models x 3 planted English windows: 18/18 recovered (offsets compared modulo the key's period, +-10). Matched null: 234 i.i.d. streams (about the same number of offsets,
4.7 M). Library best **1.2635**, null best 1.3456 (the null is higher because a repeating key of period p has only p distinct phases, so these keys give far fewer independent decodes than
random streams); verify: 0 kept.

## (iv) Mechanism crossings (`sign_cross.py`) - PILOT SCALE

The 10 strongest of the 61 word-level sign rules (best IoC of their own screen: C_cur_ws, B7_prev_pf, B5_cur_wp, B5_cur_w, A_prev_pf, C_cur_n, A_prev_pl, B3_cur_ws, E_cur_n3, B5_prev_n;
E_cur_n4 ties B5_prev_n at 1.3559 and was not run) x `nulledge=1`, `nulledge=2`, `advsep=1`, `advsep=2` (for `advsep=2` the B lines of `data/segments.txt` were added to the sign windows).
**Streams: every third stream of `library_flat.ksb` (194 of 581), not the full 581: 40 full screens would take about 5 h.** A stream outside the subset is not tested. Control (an independent
planter: sign from the rule before the word, then keyless nulls at every word end / start, or one extra key value at every word boundary and every 23rd rune; rules E_cur_n4, B5_cur_w,
A_prev_pf x four mechanisms x 3 windows): 36/36 recovered at the planted offset (IoC 1.60-2.14). Matched null per (rule, mechanism): `rand:60` through the same windows and flag.

| mechanism | best hit over the 10 rules | best null over the 10 rules | screens with hit >= 1.40 / null >= 1.40 | verify kept |
|---|---|---|---|---|
| nulledge=1 | 1.4252 (A_prev_pf) | 1.4382 | 3 / 4 | 0 (see below) |
| nulledge=2 | 1.4512 (B3_cur_ws) | 1.4172 | 4 / 1 | 0 |
| advsep=1 | 1.3753 (C_cur_ws) | 1.3533 | 0 / 0 | 0 |
| advsep=2 | 1.3624 (B5_cur_wp) | 1.3268 | 0 / 0 | 0 |

With signs, the keyless-null decoder has a heavy null tail (a null stream reaches 1.43-1.44 for 4 of the 10 rules at nulledge=1), so 1.40 is not a clean line there; what decides is
verification. One screen shows a `REAL? check by eye` line: A_prev_pf x nulledge=1, window 0.14, `sha256-chain reject :<128 bytes 33363336>`, offset 19564, mult 28, model 1: first-229-scored IoC
1.425, "whole window" 1.433 over **220 runes only** (the stream ends 220 runes into a 1,589-rune window, so it is not a whole-window verification), same keystream at 20 random offsets max 1.179,
decoded text not language-like (runs of X, TH, ING); it lies below the null maximum of three other rules at nulledge=1 (1.438, 1.431, 1.428). Not a candidate. The two 1.451 hits (B7_prev_pf and
B3_cur_ws x nulledge=2) fall to noise over the whole window (1.15 for the first). The A/I and prime checks are `n/a` for nulledge runs (the plain has no position map) and were not needed for advsep
(no hit survived). Not run: the full 581-stream library (the next step), E_cur_n4, the other 50 rules, nulledge x advsep, two sign templates combined.

## Summary

| item | control | best vs null | verified hits |
|---|---|---|---|
| (i) reading orders, 5 transforms (+ baseline) | planted 8/8 each | library best 1.318-1.371, null 1.313-1.351 (baseline 1.366 / 1.342) | 0 |
| (ii) alphabet orders, 5 orders | planted 8/8 each; blindness 1.25-1.27 (3 non-trivial orders) | library best 1.318-1.375, null 1.326-1.373 | 0 |
| (iii) phrases / headings as keywords, 2,310 keys | planted 18/18 | library best 1.2635, null (234 streams) 1.3456 | 0 |
| (iv) 10 sign rules x 4 mechanisms, a third of the flat streams | planted 36/36 | hit max 1.4512 vs null max 1.4382 (nulledge); advsep 1.375 vs 1.353 | 0 (one 220-rune stream-end artefact) |

Run time at 12 threads: (i) about 70 min, (ii) 75 min, (iii) a few minutes, (iv) about 2.5 h. Level 0: four more families with no signal at the depth of the ordinary screen. The shared engine
binaries (`work/kscreen/target/release`, `target/pdir`) were only run, never rebuilt; `verify.py` and the new files are the only changes to tracked code.

## (ii) addendum: 15 OEIS alphabet orders (owner request, 2026-10-22)

Orders `oeis-A107801` ... `oeis-A107814` and `oeis-A185956`: each sequence's first 29 terms permute the first 29 primes, i.e. the Gematria values, read as an order of the 29 runes
(definitions in the `OEIS29` block of `work/phase50/alphabets.py`, terms copied from the local OEIS dump; source of the idea: 7he5haman's "The Mayfly" document, 2020-21, via the
column counts 83 103 101 107). Same method, windows and decision rule as (ii) (below-normal priority; about 15-25 min each).

| order | planted control | blindness | library best | null best (rand:300) | verify |
|---|---|---|---|---|---|
| A107801 | 8/8 | 1.269 | 1.3359 | 1.3262 | 0 kept |
| A107802 | 8/8 | 1.247 | 1.3604 | 1.3126 | 0 kept |
| A107803 | 8/8 | 1.257 | 1.3495 | 1.3540 | 0 kept |
| A107804 | 8/8 | 1.295 | 1.3313 | 1.3171 | 0 kept |
| A107805 | 8/8 | 1.273 | 1.3540 | 1.3055 | 0 kept |
| A107806 | 8/8 | 1.254 | 1.3268 | 1.3495 | 0 kept |
| A107807 | 8/8 | 1.269 | 1.3533 | 1.3281 | 0 kept |
| A107808 | 8/8 | 1.252 | 1.3184 | 1.3042 | 0 kept |
| A107809 | 8/8 | 1.243 | 1.3307 | 1.3268 | 0 kept |
| A107810 | 8/8 | 1.274 | 1.3436 | 1.3120 | 0 kept |
| A107811 | 8/8 | 1.266 | 1.3320 | 1.3333 | 0 kept |
| A107812 | 8/8 | 1.257 | 1.3857 | 1.3320 | 0 kept |
| A107813 | 8/8 | 1.240 | 1.3210 | 1.3126 | 0 kept |
| A107814 | 8/8 | 1.258 | 1.3184 | 1.3902 | 0 kept |
| A185956 | 8/8 | 1.272 | 1.3352 | 1.3359 | 0 kept |

As one family of 15: library best 1.3184-1.3857 (none at 1.40; the 15 maxima lie inside the null range 1.3042-1.3902), 0 of 150 re-decoded hits verified. Negative at the depth of the ordinary screen.
Windows: `data/segments.txt` only. Not covered: page and head windows; orders read in the other direction are the key sign (mult 28), already tried.

## Row solved-phrase-keys: Cicada's key habits as single-layer Vigenere keys (`phrase_keys.py`, layer2 engine, mode=known)

Keys of <= 24 runes (layer2's MAXM) from every word (>= 3 runes), clause, 2-3 word phrase, title and first / last printed line of the solved pages 0.0-0.6, 0.16, 0.17, and the words and lines of the
2014 signed messages (`results/outguess/payload_10..13`), in all 8 spellings of three habits: C written as F (FIRFUMFERENFE), NG as N,G instead of the ING rune, IA as I,O. U/V needs no variant
(V is U in this repo's alphabet, so DIVINITY = DIUINITY). **1,841 distinct keys.** Each key: both inner signs, literal-F rule off and on (a plaintext F stays F and does not advance the key, as on pages 3-4
and 14-15), every phase, first 300 runes of the eight section windows, IoC of the decoded letters (any language); the outer layer is a stream of zeros. Control: English planted with CIRCUMFERENCE
spelled C->F (literal F on), WELCOME PILGRIM (off), DIVINITY (on), each in 3 windows, searched among 200 other keys: 8/9 recovered with the right key and IoC 1.45-2.06 (one window of the DIVINITY plant, IoC
1.447, was won by a wrong key with the literal-F freedom, so a short window can lose to the overfit branch). Null: 1,841 random keywords of the same lengths.

| | best IoC (8 windows) |
|---|---|
| solved-phrase keys | 1.3320 (seg0.7, `phrase:UNREASONABLE_THINGS`) |
| random keys of the same lengths | 1.3773 |

No IoC >= 1.40, so nothing to verify (A/I oracle and prime sums were not needed). Per-window table in `results/kscreen/phase50/summary_phrase_keys.txt`. Not covered: keys longer than 24 runes, keys whose spelling habit
is another one, keyword + number-stream layers (layer2's other slices), the pages 14-15 skip-at-solved-positions rule beyond the F rule, windows other than the section starts.
