# nulledge report (keyless word-edge nulls)

Date: 2026-10-18. Engine: `work/kscreen` option `nulledge=<0|1|2>` (screen / trace / verify). Nothing in LP2 is solved.

## Option semantics (final, documented)

* `nulledge=0` (default): the untouched original decode; output verified byte-identical to the pre-change
  binary (screen / trace / verify, incl. P-line chain windows and planted round-trips; only the wall-clock
  `secs=` header field can differ).
* `nulledge=1`: every word-FINAL rune of each window's words is a keyless null -- NOT scored, does NOT advance
  the key pointer, and is invisible to the anti-repeat prev chain (the next rune's collision check compares
  against the last scored rune).
* `nulledge=2`: the same for word-INITIAL runes.
* Word boundaries come from the window's **L line = the CIPHERTEXT word lengths including the nulls** (a null
  adds a rune to its word). A window whose L line is missing/unparseable, has a length-0 word, does not sum to
  the window's rune count, or carries a P line falls back to `nulledge=0` semantics for that window.
* IoC is over the scored letters; the early-abort gate uses the letters scored so far. `verify.py` passes the
  option through; `gpu.py` rejects `nulledge!=0`.

## Why deterministic every-edge (the L-line iteration)

The word-length model is "one extra rune in ~42% of multi-rune words". Two readings were implemented and
measured on the Welcome/primes control plant (below):

1. **Free per-word beam** (each edge rune may be a null, the beam keeps both continuations): recovers the 42%
   plant (1.71 at the true offset) BUT the rand null with the same freedom reaches **1.7547** -- the beam's
   per-word choice is key-pointer phase freedom and it cherry-picks phases on random keys (winner decode
   inspected: 261 letters, 43 x the same rune, coherent c-k decode; the null reaches the truth's level). Gate
   (c) <= 1.37 is unreachable; the ordinary 1.40-hit framework collapses.
2. **Deterministic per-edge skip** (the option spec as written): with nulls at 42% of the edges the decoder
   misaligns at the first null-free word and scores 1.268 / 1.254 (no power); with a null at EVERY edge it
   recovers 1.670 / 1.667 at the exact offset and the rand null stays 1.355 / 1.325.

Only reading 2 keeps the parent's gates consistent, so it is the shipped semantics: the screen has power for
"null at every word edge" (0% and 100% rates), and the ~42% mixture is documented as NOT testable by any
single-window IoC screen with a free null placement (see "not excluded").

## Control numbers (work/tmp/nulledge_control.py, work/tmp/nulledge_control.txt; CONTROLS PASSED)

Plant: Welcome 0.1 plaintext (299 runes, 73 complete words in the first 300, plaintext IoC 1.6671), engine
plant on `file:data/library.ksb` item `primes`, offset 100, mult 1, model 0, keep 0.19, seed 12345, subst 0;
then a random keyless null at EVERY word edge; L = ciphertext word lengths incl. nulls (73 nulls, 372 runes).

| gate | variant 1 (word-final) | variant 2 (word-initial) | rule | result |
|---|---|---|---|---|
| (a) blindness: default engine on the nulled window | best 1.207 (1.078 at offset 100) | best 1.219 (1.076 at offset 100) | ~1.0 | PASS |
| (b) positive: nulledge recovers at the exact offset | **1.670** at offset 100 | **1.667** at offset 100 | >= 1.60 | PASS |
| (c) null: rand:300:301/302, same nulledge | **1.355** | **1.325** | <= 1.37 | PASS |
| 42%-of-multi-rune-word nulls, nulledge on | 1.268 (no power) | 1.254 (no power) | documented | - |
| nulledge on the un-nulled plant | 1.258 | 1.323 | documented | - |

## LP2 first run (bounded)

Screens: `data/segments.txt` (8 section windows, first 300 runes each) vs `file:data/library.ksb` (1,439
streams, every offset), mults=1, models=0,1, beam 16, abort 150:1.2, 15 threads; matched nulls
rand:300:401/402 with the same settings. `results/kscreen/nulledge{1,2}_segments.tsv`,
`results/kscreen/nulledge{1,2}_null_segments.tsv`.

| run | decodes | best IoC (window) | null max (300 streams, 8 windows) | margin |
|---|---|---|---|---|
| nulledge=1 (word-final nulls) | 204,434,192 | 1.4163 (seg0.14, sha256-chain reject :<128 bytes 33363336>, off 19564, model 1) | 1.3901 | +0.026 |
| nulledge=2 (word-initial nulls) | 204,434,192 | 1.4294 (seg0.11, sha256-chain mod :2014, off 18146, model 0) | 1.3849 | +0.045 |

Both library bests sit above the 1.40 hit rule but only 0.03-0.05 above the matched null's maximum, which is
the selection-noise signature. Ordinary verification (`verify.py`, nulledge passed through, top 12 each,
whole-window re-decode + the same keystream at 20 random offsets):

- nulledge=1: every re-decoded hit falls back to IoC 1.037-1.104 over its whole window (matched controls
  mean ~1.05, max ~1.15); **0 of 12 keep IoC >= 1.40 and beat their controls by 0.15**.
- nulledge=2: every re-decoded hit falls back to IoC 1.041-1.063 over its whole window (controls mean ~1.05,
  max ~1.11); **0 of 12 keep IoC >= 1.40 and beat their controls by 0.15**.

Per-window bests (library / null): seg0.7 1.356/1.390, seg0.8 1.367/1.334, seg0.9 1.392/1.347, seg0.11
1.347/1.345, seg0.12 1.354/1.346, seg0.13 1.365/1.343, seg0.14 1.416/1.356, seg0.15 1.368/1.359 (nulledge=1);
seg0.7 1.370/1.361, seg0.8 1.373/1.378, seg0.9 1.355/1.341, seg0.11 1.429/1.378, seg0.12 1.351/1.385, seg0.13
1.376/1.337, seg0.14 1.375/1.350, seg0.15 1.382/1.358 (nulledge=2).

## Verdict

**Excluded (for the every-word-edge null model, the only rate this screen has power for): no library keystream
at any offset, under either anti-repeat model, is hidden behind a keyless null at every word-final or
word-initial position in the first 300 runes of the 8 LP2 sections.** Both variants' best hits (1.4163, 1.4294)
are barely above their matched nulls (1.3901, 1.3849) and every one of them falls back to IoC ~1.04-1.10 over
the whole window, far below the 1.40 rule and inside its own keystream's random-offset controls: 0 of 24
re-decoded hits survive verification. No candidates, no decryptions claimed.

## What is NOT excluded

* The ~42%-of-word-edges null mixture (the word-length model's rate): untestable by single-window IoC with a
  per-word null placement (measured: free-pattern beam null = 1.75 = the truth's level; deterministic skip has
  no power). A key-free, model-specific test conditioned on a null pattern would be needed.
* Nulls inside words (not at an edge), extra key advances at layout events, null rates other than 0% and 100%
  of the word edges.
* Everything the ordinary kscreen shares: 300-rune windows only, keys outside the library, restarts at unknown
  places, later windows.
