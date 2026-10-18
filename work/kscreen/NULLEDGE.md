# Keyless word-edge nulls (NULLEDGE)

Status: engine option `nulledge=<0|1|2>` in `src/main.rs` (screen / trace / verify modes), built and controlled
2026-10 (control transcript: `work/tmp/nulledge_control.txt`; script: `work/tmp/nulledge_control.py`;
campaign results: `results/kscreen/nulledge1_segments.tsv`, `nulledge2_segments.tsv` and their matched nulls).
`docs/NEGATIVE_SPACE.md` section 0 item 9; the word-length model is `docs/registry.toml` `obs-wordlen`
(one extra rune in about 42% of multi-rune words). Nothing in LP2 is solved.

## The hypothesis

Every decoder so far assumes each ciphertext rune consumes exactly one key value and the pointer only moves
forward at anti-repeat events. NOT covered: runes inserted WITHOUT consuming a key value (keyless nulls, e.g.
one per word) and extra key advances at layout events. This option covers the first half for the case where the
null sits at a word EDGE: every word-FINAL rune (`nulledge=1`) or every word-INITIAL rune (`nulledge=2`) of the
window's words is treated as a keyless null: it is NOT scored (it does not count in the IoC denominator) and it
does NOT advance the key pointer. The rest of the decode (skip/coin models, the beam over the key pointer, the
IoC score over the scored runes) is unchanged.

## Exact convention (decided and documented)

* **The L line lists the CIPHERTEXT word lengths, nulls included.** A null adds a rune to its word, so a nulled
  word's L entry is one longer than the plaintext word's. The engine's word-edge logic (word w spans the runes
  between cumulative L sums) therefore lands the edge exactly on the inserted null.
* **Word edges come from the L line.** Missing/unparseable L, a word of length 0, or lengths that do not sum to
  the window's rune count fall back to `nulledge=0` semantics for that window (safety: a mismatched L line would
  silently skip the wrong runes). Windows with a `P` line (per-position prev values, the chain windows) also
  fall back, because their prev chain cannot skip over a null.
* **The null is invisible to the anti-repeat chain.** The collision check of the rune after a null compares
  against the last SCORED rune, not the null's value (`null_adjust` in `src/main.rs`): the null is padding the
  encryptor writes between the enciphered runes, so the skip/coin structure of the real runes is unchanged.
* **Scoring.** The IoC is computed over the scored letters only (`letters = runes - nulls`); the early-abort
  gate (`abort=150:1.2`) is applied at the same rune count but against the letters scored so far. With
  `nulledge=0` the original code path runs unchanged and the engine output is byte-identical (checked against
  the pre-change binary: screen/trace/verify outputs, incl. P-line windows; only the wall-clock `secs=` field
  can differ).
* **Why every word, not 42%.** The word-length model says ONE EXTRA RUNE IN ABOUT 42% OF MULTI-RUNE WORDS.
  A decoder that must decide per word which edge rune is a null has no way to make that decision from the
  ciphertext, and its freedom is exactly the key-pointer phase: measured on the controls, a per-word beam
  variant recovers a 42% plant at the true offset (IoC 1.71) but inflates the random-key null to 1.75 -- the
  null reaches the truth's level, so no single-window IoC screen can separate them (transcript in
  `work/tmp/nulledge_report.md`). The deterministic per-edge skip is the only reading that keeps the null at the
  ordinary screen's level (measured 1.355 / 1.325 <= 1.37), at the price of testing the "null at EVERY word
  edge" variant: a 42% mixture scores ~1.0 with it (measured 1.268 / 1.254). That mixture is therefore NOT
  excluded and NOT testable by this screen; the all-edges variant IS tested.

## How to use it

```
target/release/kscreen screen data/segments.txt file:data/library.ksb out.tsv mults=1 models=0,1 nulledge=1
target/release/kscreen screen data/segments.txt rand:300:11    out_null.tsv mults=1 models=0,1 nulledge=1   # matched null
python work/kscreen/verify.py out.tsv        # passes nulledge through; the ordinary 1.40 + 0.15 rules apply
```

`verify` accepts `nulledge=` too (`controls=K` matched offsets decode with the same semantics). The GPU port
(`gpu.py`) rejects `nulledge!=0` instead of silently ignoring it. Hits count by the ordinary
`docs/CAMPAIGNS.md` rule: IoC >= 1.40 on the first 300 runes, then the whole-window re-decode that must beat the
same keystream's 20 random offsets by 0.15.

## What the planted controls showed (work/tmp/nulledge_control.txt)

Plant: Welcome (segment 1) plaintext, 299 runes in 73 complete words, planted with the engine on the library key
`primes` (offset 100, mult 1, skip model, keep 0.19, seed 12345), then a random keyless null inserted at EVERY
word edge (variant 1 word-final, variant 2 word-initial), L = ciphertext word lengths including the nulls.

| gate | variant 1 (final) | variant 2 (initial) | rule |
|---|---|---|---|
| (a) blindness: default engine on the nulled window | best 1.207, 1.078 at the true offset | best 1.219, 1.076 at the true offset | <= 1.30 |
| (b) positive: nulledge recovers the plant | **1.670 at offset 100** | **1.667 at offset 100** | >= 1.60 |
| (c) null: rand:300:300, same nulledge | **1.355** | **1.325** | <= 1.37 |
| 42%-of-multi-rune-words mixture, nulledge on | 1.268 (no power) | 1.254 (no power) | documented, not a gate |
| nulledge on the un-nulled plant | 1.258 | 1.323 | documented, not a gate |

The 42% row is why the semantics is deterministic: with nulls at 42% of the word edges the decoder misaligns at
the first null-free word and cannot recover; and the alternative (let the beam choose per word whether the edge
rune is a null) makes the random-key null reach 1.75, the same level as the truth (see the report). The
every-edge model is the one this screen has power for, and its controls all pass.

## LP2 first run (bounded, 2026-10-18)

`data/segments.txt` (8 windows, first 300 runes) x `file:data/library.ksb` (1,439 streams, every offset),
mults=1, models=0,1, matched nulls rand:300:401/402 (300 streams), 204,434,192 decodes per variant
(`results/kscreen/nulledge{1,2}_segments.tsv`, `_null_segments.tsv`): best **1.4163** (nulledge=1) and
**1.4294** (nulledge=2) against null maxima **1.3901** / **1.3849**. The ordinary verification (top 12 each,
whole-window re-decode + the same keystream at 20 random offsets): every hit falls back to IoC 1.04-1.10,
**0 of 24 keep IoC >= 1.40 and beat their controls by 0.15** (`nulledge{1,2}_segments_verify.txt`). Verdict:
excluded -- no library key hides behind a keyless null at every word edge of LP2. Details and the 42%-mixture
analysis: `work/tmp/nulledge_report.md`.

## What is NOT excluded

* **Nulls at ~42% of the word edges** (the word-length model's rate): NOT tested by this screen and, as
  measured, not testable by any single-window IoC decoder whose null is allowed to choose its words. A
  key-free, model-specific test (e.g. the echo statistics conditioned on a null pattern) would be needed.
* Nulls INSIDE words (not at the edge), extra key advances at layout events, and any null rate other than 0%
  or 100% of the word edges.
* Everything the nulledge screen shares with the ordinary kscreen: 300-rune windows, the skip/coin models, the
  library family (or whatever family is screened).
