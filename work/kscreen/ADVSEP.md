# Separator key-pointer advances (ADVSEP)

Status: engine option `advsep=<0|1|2>` in `src/main.rs` (screen / trace / verify modes), built and controlled
2026-10 (control transcript: `work/tmp/advsep_control.txt`; script: `work/tmp/advsep_control.py`; bit-identity
transcript: `work/tmp/advsep_bitcheck/bitcheck.txt`; campaign results: `results/kscreen/advsep{1,2}_segments.tsv`
and their matched nulls). `docs/NEGATIVE_SPACE.md` section 0 item 9, the remaining undecoded half: the key
pointer may advance one or more EXTRA values at layout events (word separators, line / page breaks). Nothing in
LP2 is solved.

## The hypothesis

Every decoder so far assumes each ciphertext rune consumes exactly one key value and the pointer only moves
forward at anti-repeat events. The keyless-null half of blind spot 9 (runes inserted WITHOUT consuming a key
value) is covered by `nulledge` (NULLEDGE.md). This option covers the other half: the key pointer consumes ONE
extra key value at every word boundary (`advsep=1`) and, for `advsep=2`, also ONE extra key value at every
line/page break. The advance happens BETWEEN words, before the next word's first rune is enciphered. The
skip/coin collision logic (re-draws stay inside the rune), the beam over the key pointer, the anti-repeat prev
chain and the IoC score over the (scored) runes are all unchanged. `advsep=0` runs the untouched original code
path, byte-identical to before.

## Exact convention (decided and documented)

* **Word edges come from the window's L line**, exactly as in the nulledge implementation: word w spans the
  runes between cumulative L sums, and `adv[b] = 1` at every cumulative sum b (the first rune of the next
  word). The L line lists the CIPHERTEXT word lengths; the advsep plant inserts no runes, so the plain and
  cipher L lines agree.
* **Line/page breaks come from the window's B line** (`B <positions>`): export.py writes, for each window it
  generates, the window-relative rune positions p where a line or page break of the transcription ('/' or '%',
  the `\n` / `%` tokens of `lp.load_segments`) sits between rune p-1 and rune p. `adv[p] += 1` for each such
  p (0 < p < rune count). A line break that falls at a word boundary therefore costs 2 key values under
  `advsep=2` (LP2's lines usually end at a word separator, and words also wrap across lines mid-word).
* **adv[i] = extra key values consumed between rune i-1 and rune i.** The decoder applies the advance to every
  beam state's key pointer before rune i is read, so rune i's own skip/coin logic (the values it may re-draw)
  is unchanged and the prev chain is unchanged. The key index an aligned decoder uses for rune i is
  i + sum(adv[0..i]) + the skip/coin draws before i.
* **Fallbacks.** A window whose L line is missing/unparseable, holds a word of length 0, or does not sum to its
  rune count decodes exactly as with `advsep=0` (safety: a mismatched L would advance at the wrong places).
  A window without a B line simply gets no break advances: `advsep=2` behaves like `advsep=1` there (the
  planted controls have no breaks, and the B-less check below shows the two decodes are identical). Breaks at
  or after the window edge are ignored (they move no pointer inside the window; a break before the first rune
  is a shift of the start offset, and every offset is screened anyway).
* **The key buffer.** A screen's `key_need` grows by the window's own advance sum (boundaries + breaks over the
  first n runes), so a decode never runs past the stream; the offsets screened per stream shrink accordingly
  (a few percent). LP2 windows carry 60-71 boundaries and 14-15 breaks in their first 300 runes.
* **Scoring and gates.** IoC, the early-abort gate, the 1.40 hit rule and the +0.15 verify margin are the
  ordinary kscreen ones (CAMPAIGNS.md); `verify.py` passes `advsep=` through to the engine, and the matched
  random offsets decode with the same advances. The GPU port (`gpu.py`) rejects `advsep!=0` instead of silently
  ignoring it. `advsep` composes with `nulledge` mechanically (a null rune does not consume its own advance;
  the advance applies to the next scored rune), but no control covers the combination.
* **Identity.** With `advsep=0` (and with `nulledge` untouched) screen/trace/verify/plant outputs are
  byte-identical to the pre-change binary; only the wall-clock `secs=` field of screen headers can differ
  (checked on rand screens over `data/segments.txt` and the P-line chain windows, a trace, a plant and its
  verify, and a `nulledge=1` screen: `work/tmp/advsep_bitcheck/bitcheck.txt`).

## How to use it

```
target/release/kscreen screen data/segments.txt file:data/library.ksb out.tsv mults=1 models=0,1 advsep=1
target/release/kscreen screen data/segments.txt rand:300:401    out_null.tsv mults=1 models=0,1 advsep=1   # matched null
python work/kscreen/verify.py out.tsv        # passes advsep through; the ordinary 1.40 + 0.15 rules apply
```

`verify` accepts `advsep=` too (`controls=K` matched offsets decode with the same semantics). `advsep=2` needs
the B lines: run `python work/kscreen/export.py` once after pulling this change (it regenerates
`data/segments.txt` and friends with the B lines; windows without B advance at word boundaries only).

## What the planted controls showed (work/tmp/advsep_control.txt)

Plant: Welcome (segment 1) plaintext, 299 runes in 73 complete words, planted with the engine on the library key
`primes` (offset 100, mult 1, skip model, keep 0.19, seed 12345, no substitution), then RE-ENCRYPTED in Python
(an independent splitmix64 + first-primes implementation) with one extra key value consumed after every word:
word w starting at key index j(w) consumes j(w), j(w)+1, ... and j(w+1) = j(w) + len(w) + 1, modulo skip
re-draws that stay inside the word. The Python re-encryption reproduces the engine's own plant byte for byte
with the advances off, which pins the key stream and the plant RNG.

| gate | result | rule |
|---|---|---|
| self-check: Python re-encryption == engine plant (advances off) | byte-identical, 299 runes | exact |
| (a) blindness: default engine on the advanced window | best 1.213, 1.097 at the true offset | <= 1.30 |
| (b) positive: advsep=1 recovers the plant | **1.667 at offset 100** | >= 1.60 |
| (c) null: rand:300:301, same advsep=1 | **1.286** | <= 1.37 |
| (b2) B-line positive: advsep=2 recovers the plant advanced at every word boundary AND 7 synthetic break positions (B line) | **1.659 at offset 100** | >= 1.60 |
| advsep=1 on the B-line plant (does not know the breaks) | 1.106 at offset 100 | documented, not a gate |
| advsep=2 on the B-less advanced window == advsep=1 | identical rows | documented, not a gate |
| advsep=1 on the un-advanced plant | 1.228 | documented, not a gate |

The un-advanced and wrong-advance rows show the option has no power unless the truth really consumed the extra
values: a deterministic decoder stays aligned only with a truth that advanced exactly where the L/B lines say.

## LP2 first run (bounded, 2026-10-18)

`data/segments.txt` (8 windows, first 300 runes, B lines) x `file:data/library.ksb` (1,439 streams, every
offset), mults=1, models=0,1, matched nulls rand:300:401/402 (300 streams, 20,000 values each).

| variant | decodes | library best IoC | matched null max IoC | verdict |
|---|---|---|---|---|
| advsep=1 | 202,799,488 | **1.3191** (sha512-ctr reject :DIVINITY, seg0.15, offset 11792) | **1.3682** | below its own null |
| advsep=2 | 202,477,152 | **1.3288** (sha256-ctr reject :FULMAEAYOEA, seg0.12, offset 236) | **1.3055** | +0.023 above the null, far below 1.40 |

No hit reaches the 1.40 rule, so nothing required verification; the top 5 of each were re-decoded anyway
(whole-window, beam 64, + 20 random offsets of the same keystream, `advsep` passed through): **0 of 5 and 0 of 5
keep IoC >= 1.40 over the whole window**, every hit falls back to IoC 1.04-1.15, exactly the noise pattern
(`results/kscreen/advsep{1,2}_segments_verify.txt`). Verdict: **excluded** -- no library key hides behind one
extra key value per word boundary (advsep=1) or per word boundary plus line/page break (advsep=2) in the first
300 runes of the 8 sections. The advsep=1 screen has no power at all on LP2: its library best sits below its
own matched random-key null.

## What is NOT excluded

* **Advance counts other than 1 per event** (e.g. 2 per word boundary, or advances at only ~42% of the word
  edges - the word-length model's rate): the deterministic per-edge advance is the only reading that keeps the
  null at the ordinary screen's level; a decoder free to choose its own advances is a pointer-phase freedom the
  null would pay for, exactly as in NULLEDGE.md.
* **Breaks that are not in the transcription** (page images only), breaks in windows other than the first 300
  runes of the 8 sections, and any convention that ties the advance to something other than the L/B positions.
* Everything the advsep screen shares with the ordinary kscreen: 300-rune windows, the skip/coin models, the
  library family (or whatever family is screened), and any mechanism outside additive `c = D(p) + m*k + b`.
