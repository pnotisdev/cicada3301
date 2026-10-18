# ADVSEP report: extra key-pointer advances at word boundaries / layout breaks (blind spot 9, layout half)

Date: 2026-10-18. Engine: `work/kscreen` (`target/release/kscreen.exe`, rebuilt). Nothing in LP2 is solved.
The long-lived docs are `work/kscreen/ADVSEP.md` (semantics, conventions, controls, campaign numbers) and
`docs/NEGATIVE_SPACE.md` item 9 (the ledger row this closes). This file is the work transcript summary.

## 1. Semantics implemented

`advsep=<n>` (screen / trace / verify modes; n = 0 default, off):

* `adv[i]` = extra key values the pointer consumes BETWEEN rune i-1 and rune i. The decoder adds `adv[i]` to
  every beam state's key index before rune i is read; the rune's own skip/coin re-draw logic, the anti-repeat
  prev chain, the beam and the IoC score are unchanged.
* **advsep=1**: `adv[b] = 1` at every word boundary (cumulative L sums; the same edges as nulledge). The advance
  happens before the next word's first rune: word w starting at key index j(w) consumes j(w), j(w)+1, ... and
  j(w+1) = j(w) + len(w) + 1 modulo skip re-draws (which stay inside the word).
* **advsep=2**: +1 at every word boundary AND +1 at every line/page break. Breaks come from a new optional
  **B line** (`B <positions>`, window-relative rune positions p where a transcription line/page separator sits
  between rune p-1 and p); export.py now writes it into `data/{segments,heads,pages}.txt` from the `\n` / `%`
  tokens. A break at a word boundary costs 2 key values. A window without a B line advances at word boundaries
  only (advsep=2 == advsep=1 there). LP2's 8 segment windows carry 60-71 boundaries and 14-15 breaks in their
  first 300 runes.
* **Fallback to advsep=0 semantics** for a window whose L line is missing/unparseable, has a 0-length word, or
  does not sum to its rune count.
* **advsep=0** runs the untouched original code path: bit-identical to the pre-change binary on
  screen/trace/plant/verify incl. P-line chain windows and a nulledge=1 run (only the wall-clock `secs=`
  header field differs; transcript `work/tmp/advsep_bitcheck/bitcheck.txt`).
* Key-buffer size grows by the window's own advance sum, so no decode runs past the stream; `verify.py` passes
  `advsep=` through to the engine and to the matched-offset controls; `gpu.py` rejects `advsep!=0` instead of
  silently ignoring it. The ordinary 1.40 hit rule and the +0.15 verify margin apply (CAMPAIGNS.md).

## 2. Controls (`work/tmp/advsep_control.py`, transcript `work/tmp/advsep_control.txt`)

Plant: solved Welcome plaintext (segment 1, 299 runes in 73 complete words, IoC 1.6671) planted on the library
key `primes` (offset 100, mult 1, skip model, keep 0.19, seed 12345, no substitution), then RE-ENCRYPTED in
Python -- an independent splitmix64 + first-primes implementation -- with one extra key value consumed after
every word (j(w+1) = j(w) + len(w) + 1, skip re-draws inside the word). The Python re-encryption reproduces the
engine's own plant byte for byte with the advances off (pins key stream + plant RNG).

| gate | result | rule |
|---|---|---|
| self-check: Python re-encryption == engine plant, advances off | byte-identical (299 runes) | exact |
| (a) blindness: default engine (advsep=0) on the advanced window | best **1.213**; **1.097** at the true offset 100 | <= 1.30 |
| (b) positive: advsep=1 recovers the plant | **1.667** at offset 100 (primes, mult 1, model 0) | >= 1.60 |
| (c) null: rand:300:301 with advsep=1 | best **1.286** | <= 1.37 |
| (b2) B-line positive: advsep=2 recovers the plant advanced at every word boundary AND 7 synthetic break positions (B line) | **1.659** at offset 100 | >= 1.60 |
| advsep=1 on the B-line plant (does not know the breaks) | 1.106 at offset 100 | documented, not a gate |
| advsep=2 on the B-less advanced window | identical rows to advsep=1 | documented, not a gate |
| advsep=1 on the un-advanced plant | 1.228 | documented, not a gate |

All gates PASS (CONTROLS PASSED). The wrong-advance rows show the option has power only against a truth that
really consumed the extra values -- a deterministic decoder stays aligned only with the exact L/B positions.

## 3. LP2 first run (bounded)

`data/segments.txt` (8 windows, first 300 runes, B lines) x `file:data/library.ksb` (1,439 streams, every
offset), mults=1, models=0,1, and matched rand:300:401/402 nulls (300 streams each):

| variant | decodes | library best | matched null max |
|---|---|---|---|
| advsep=1 | 202,799,488 | **1.3191** (sha512-ctr reject :DIVINITY, seg0.15, off 11792, model 0) | **1.3682** |
| advsep=2 | 202,477,152 | **1.3288** (sha256-ctr reject :FULMAEAYOEA, seg0.12, off 236, model 1) | **1.3055** |

No hit reaches 1.40, so the campaign rule required no verification; the top 5 of each were re-decoded anyway
(whole window, beam 64, controls=20 same keystream, `advsep` passed through):
`results/kscreen/advsep{1,2}_segments_verify.txt` -- **0 of 5 and 0 of 5 keep IoC >= 1.40 over the whole
window**; every hit falls back to IoC 1.04-1.15 (first-300 values 1.30-1.33 shrink to 1.05-1.15), the ordinary
noise pattern. The advsep=1 library best sits BELOW its own matched random-key null (1.3191 < 1.3682): the
option has no power on LP2 at all; advsep=2 is +0.023 above its null, far below 1.40, and verifies as noise.

**Verdict: excluded.** No library key hides behind one extra key value per word boundary, with or without one
extra per line/page break, in the first 300 runes of the 8 LP2 sections. Report numbers, no decryptions claimed.

## 4. Sibling gates / environment notes

* `python jobs/overnight.py run selftest`: the kscreen controls (15 planted windows + 30-stream null) ran with
  the NEW binary and ended **SELFTEST PASSED** (best null 1.306). The runner's `setup/build-kscreen` step
  failed only because an unrelated relabel campaign was holding the exe file lock; the unit-test step was
  skipped as already-done, so I re-ran the suite directly.
* Full `unittest discover` (148 tests, 24 skipped): after my `export_hyp.py` unpacking fix (`segment_windows`
  now returns 5-tuples: name, prev, runes, lens, breaks -- write_self_windows unpacks and emits the B line),
  the only remaining failures are pre-existing and unrelated to advsep: (1) `test_overview` registry/STATUS
  drift in the working tree (uncommitted `docs/registry.toml` edits by whoever owns them); (2)
  `test_separator_audit` module import fails because `cv2` is not installed on this machine (the same reason
  export.py skips page windows); (3) `test_layer2` fails only inside the full suite because
  `work/tests/test_hyp_exports.py` and `work/layer2/plant_ref.py` both `import export` (kscreen's vs layer2's
  module of the same name) -- each passes alone, the collision is order-dependent and predates this change.
* A third-party `relabel` campaign was running on this machine throughout (writes
  `results/kscreen/relabel_all_*.tsv`); I did not stop it. Its screens run through the same binary with default
  options, whose output is byte-identical to the pre-change binary, so its results are unaffected.

## 5. What is NOT excluded

* Advance counts other than 1 per event (e.g. 2 per word boundary), and advances at only some fraction of the
  word edges (e.g. the word-length model's ~42%): a deterministic per-edge advance is the only reading a
  single-window IoC decoder can test without the pointer freedom leaking into the null, exactly as NULLEDGE.md
  measured for keyless nulls.
* Breaks not present in the transcription (page images only), breaks/windows beyond the first 300 runes of the
  8 sections, and advances tied to anything other than the L/B positions.
* Everything the ordinary kscreen shares: 300-rune windows, the skip/coin anti-repeat models, the library
  family, the additive form c = D(p) + m*k + b.

## Files

* engine: `work/kscreen/src/main.rs` (option `advsep`, `adv_positions`, `adv_need`, decoder plumbing),
  `work/kscreen/export.py` (B lines), `work/kscreen/export_hyp.py` (5-tuple fix), `work/kscreen/verify.py`
  (passthrough), `work/kscreen/gpu.py` (rejects advsep!=0), docs `work/kscreen/ADVSEP.md`.
* controls: `work/tmp/advsep_control.py`, transcript `work/tmp/advsep_control.txt`.
* bit-identity: `work/tmp/advsep_bitcheck.py`, transcript `work/tmp/advsep_bitcheck/bitcheck.txt`.
* results: `results/kscreen/advsep1_segments.tsv`, `advsep2_segments.tsv`, `advsep1_null_segments.tsv`,
  `advsep2_null_segments.tsv`, `advsep1_segments_verify.txt`, `advsep2_segments_verify.txt`.
