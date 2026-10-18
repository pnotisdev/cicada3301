# Outer-alphabet relabelling front-end (RELABEL)

Status: STATUS left-item 1 / `docs/NEGATIVE_SPACE.md` section 0 item 5. Built and controlled 2026-10 (control
transcript: `work/tmp/relabel_control.txt`; script: `work/kscreen/relabel_export.py`). Nothing in LP2 is solved.

## The family

Every screen so far assumed the additive model with the substitution on the *plaintext* side:

    c = D(p) + m*k + b   (mod 29)          (D = any fixed substitution of the plaintext alphabet)

NOT covered anywhere: a keyword-mixed or otherwise permuted **OUTER** alphabet — the ciphertext runes relabelled
by a permutation `sigma` BEFORE they reach the page, i.e.

    c_i = sigma(p_i + m*k_{j_i} + b)   (mod 29)

The IoC of the ciphertext is invariant to `sigma`, so every screen saw flat text for this family. This front-end
turns the family into the existing screen instead of building a new one.

## Exact convention (decided and documented)

* `sigma` is a list of length 29, `sigma[i]` = image of `i` (tableau position `x` -> rune). For a keyword-mixed
  alphabet, `sigma` IS the mixed alphabet itself.
* **The front-end transformation is `c' = sigma_inv(c)`**: the screen's decoder computes `p = c' - k`, and
  `sigma_inv(sigma(p + k)) - k = p`, so the screen sees plaintext exactly. `relabel_window(cipher_indices, sigma)`
  returns `sigma_inv` applied to every ciphertext index.
* The anti-repeat rule survives: `sigma_inv` is a bijection, so the encryptor's collision `c_i == c_{i-1}` is
  exactly the collision `c'_i == c'_{i-1}` the screen's prev/P chain checks.
* In a windows file the `W` line's `prev` rune is relabelled too; `L` lines pass through. `P`/`S`/`G` lines are
  rejected (P values are affine combinations of ciphertext runes and G indices point into the un-relabelled
  ciphertext; those hypotheses need their own treatment). The plain library windows
  (`data/segments.txt`, `heads.txt`, `pages.txt`) contain no such lines.

## Concrete sigmas

1. **Atbash** — `sigma(x) = 28 - x` (spec `atbash`). In-book precedent: the A Warning page applies Atbash over
   the Gematria Primus. An involution (`sigma == sigma_inv`).
2. **Keyword-mixed, standard Vigenere-tableau convention** (spec `kw:<KEYWORD>`): the keyword is uppercased;
   `V->U, K->C, Q->C, Z->S` are applied (letters with no rune of their own; only these — `QU`, `IA`, `ING` are
   NOT collapsed). Each character is then ONE GP letter via its single-letter Latin name; digraphs are never
   auto-merged (`TRUTH` -> `T R U T H`, five runes, not `T R U TH`). The mixed alphabet is: keyword letters in
   first-appearance order, then the remaining runes in GP order 0..28. `sigma[x] = mixed[x]`.
3. **Affine** — `sigma(x) = (a*x + b) mod 29` (spec `aff:<a>[:<b>]`, a in 1..28). Covers the 29 reflections
   (`x -> r - x`, i.e. Atbash plus a rotation, `a = 28`) and the 27 proper multipliers `a = 2..28`. Rotations
   (`a = 1`) and the `b` shift are redundant with the ordinary screen: they are absorbed by its D/b freedom, so
   relabelling with or without them gives identical scores.

### The DIVINITY permutation table (`python work/kscreen/relabel_export.py table kw:DIVINITY`)

Mixed alphabet (sigma[x] = rune at tableau position x):
`D I U N T Y F TH O R C G W H J EO P X S B E M L ING OE A AE IA EA`

| pos | rune | -> sigma[pos] (rune) | pos | rune | -> sigma[pos] (rune) |
|---|---|---|---|---|---|
| 0 | F | 23 D | 15 | S | 12 EO |
| 1 | U | 10 I | 16 | T | 13 P |
| 2 | TH | 1 U | 17 | B | 14 X |
| 3 | O | 9 N | 18 | E | 15 S |
| 4 | R | 16 T | 19 | M | 17 B |
| 5 | C | 26 Y | 20 | L | 18 E |
| 6 | G | 0 F | 21 | ING | 19 M |
| 7 | W | 2 TH | 22 | OE | 20 L |
| 8 | H | 3 O | 23 | D | 21 ING |
| 9 | N | 4 R | 24 | A | 22 OE |
| 10 | I | 5 C | 25 | AE | 24 A |
| 11 | J | 6 G | 26 | Y | 25 AE |
| 12 | EO | 7 W | 27 | IA | 27 IA |
| 13 | P | 8 H | 28 | EA | 28 EA |
| 14 | X | 11 J | | | |

(DIVINITY -> V normalizes to U -> D I U I N I T Y -> first appearances D, I, U, N, T, Y = runes 23, 10, 1, 9, 16, 26,
then the remaining runes in GP order.)

## How to use it

Relabel the windows (one line; naming: `data/relabel/<spec with : -> _>/<segments|heads|pages>.txt`):

    python work/kscreen/relabel_export.py batch kw:DIVINITY

Then run the ORDINARY screen on the relabelled windows, unchanged options (cwd `work/kscreen`):

    target/release/kscreen screen data/relabel/kw_DIVINITY/segments.txt file:data/library.ksb results/kscreen/relabel_kw_DIVINITY.tsv

Hits count by the ordinary `docs/CAMPAIGNS.md` rule (IoC >= 1.40 on the first 300 runes, then `verify.py`
matched-null re-decode over the whole window). Short heading/page windows stay weak (`NEGATIVE_SPACE.md` section 0
item 2). `relabel_export.py one <sigma> <in.txt> <out.txt>` relabels any single windows file.

## What the planted control showed (work/tmp/relabel_control.txt)

Plant: `c_i = sigma(p_i + k_i) mod 29`, `k_i = i mod 29`, no anti-repeat events planted (the skip/coin machinery
is covered by the engine's own selftest; this isolates the relabelling transformation). Plaintext: solved section
0.1 (Welcome), first 300 runes, plaintext IoC **1.6702** (rule: >= 1.40). Decode = `sigma_inv(c) - k` via
`work/lp.ioc`, plus an end-to-end replay through the real Rust engine with the planted key as a one-stream family
(218 offsets x 2 models per run).

| case | atbash | kw:DIVINITY |
|---|---|---|
| (a) unrelabelled ciphertext, true key | IoC 1.0068 (noise) | IoC 1.0637 (noise) |
| (b) sigma_inv-relabelled, true key | **1.6702** (== plaintext) | **1.6702** (== plaintext) |
| (c) null (uniform plaintext, same sigma+key, relabelled), 5 reps | mean 0.994, max 1.017 | mean 1.008, max 1.052 |
| (d) wrong sigma (5 wrong permutations), relabelled | mean 1.014, max 1.055 | mean 1.019, max 1.039 |

End-to-end engine (kw:DIVINITY plant, key = 600 uniform splitmix64 values, one-stream family, 218 offsets x 2
models per run): unrelabelled window best **1.1729**; relabelled window best **1.6702** at the true offset 0
(only aligned offset; runner-up **1.1632**, margin 0.51 vs the 0.15 matched-control rule); null window best
**1.1348**; wrong-sigma window best **1.1581**.

Caution for replays: a period-29 ramp key (k_i = i mod 29, as used in the Python cells) makes EVERY offset
shift-equivalent to the true key, which the screen's D/b invariance absorbs — all 218 offsets then decode to
the same shifted plaintext (verified 1.6721 everywhere). The offset search only discriminates on a key without
that symmetry; real library streams are unaffected.

Conclusion: the front-end makes the true sigma visible far above the 1.40 rule (and above a keystream-matched
null) and everything else invisible (~1.0-1.2); without it, the same screen scores the true plant as noise.

## Open question: which sigmas in a real run

* **Cheap and definitely worth it (about 29+27 settings, one relabel + one ordinary library screen each):**
  the 29 reflections `x -> r - x` (`aff:28:<r>`, r = 0..28, includes Atbash) and the 26 proper affine multipliers
  `aff:<a>:0`, a = 2..27. The 29 rotations alone are redundant (absorbed by the screen's D/b freedom — equal
  scores), so the 29+29 settings the parent mentions reduce to 29 reflections + 26 multipliers of genuinely new
  shape.
* **Keyword-derived from the solved pages' vocabulary** (`kw:<KEYWORD>` for each of `lp.KEYWORDS` — DIVINITY,
  FIRFUMFERENFE, CIRCUMFERENCE, INSTAR, PRIMES, CICADA, LIBERPRIMUS, WELCOME, KOAN, INTUS, PILGRIM, WISDOM,
  TRUTH, SACRED, DIVINE, EMERGE, SELF; add phrases like A WARNING / BELIEVE NOTHING): 17+ settings. Rotations of
  a keyword alphabet are redundant, so one shape per keyword.
* All 29-cycles and the full permutation group are infeasible as a sweep; if the cheap families stay null, the
  next step is deciding which keyword/phrase set the solved pages motivate, not blind permutation search.
