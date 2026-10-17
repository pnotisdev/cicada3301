# PR: word-length test against other languages and English registers

**Branch:** `research/wordlen-languages` (new files only)

## What this adds
- `work/wordlen_languages.py`: compares LP2's 2,928 word lengths with about 30 models by a G-test (12 bins). Corpora
  are public-domain Gutenberg texts, downloaded by `--fetch` into `work/ref/corpora/` (git-ignored there):
  English (Emerson, Beowulf translation, KJV, Milton, Plato, Marcus Aurelius, Nietzsche x2, Thoreau, Spinoza,
  Darwin), Latin (Caesar, Vergil), German, French, Spanish, Italian. Each is spelled as Gematria Primus runes
  (digraph runes TH/NG/EA/OE/AE/EO/IA as `lp.word_to_key`) and as plain letters. A two-parameter family on English
  adds "each digraph rune spelled as two letters with probability r" and "an extra rune in a fraction a of
  multi-rune words". A final section fits four one-parameter *mechanisms* on English in runes.
- `results/analysis/wordlen_languages.txt`: the full table.

## Results
- **No foreign language is close.** German, French, Spanish, Italian, Latin: p < 1e-57, all with the wrong shape.
- **Mixtures of English registers do not work either** (best 3-weight mixture of the 11 English texts plus the solved
  LP sections: G = 85 on 9 df, p = 2e-14).
- **Plain English in runes is rejected in every register** (p 1e-23 .. 1e-68). English in plain letters is closer
  (Emerson p = 1e-7, Walden 2e-9) but not good.
- **Best fits are mechanisms that start from English in runes (digraph runes as single runes, as in the solved
  pages):**

  | mechanism (one parameter, fitted) | fitted value | p |
  |---|---|---|
  | 2-rune words missing, renormalised | d = 0.49 | 0.071 |
  | +1 rune in a fraction of multi-rune words | a = 0.40 | 0.026 |
  | inserted rune at a rate per rune, anywhere | | 8e-26 |
  | adjacent words fused (lost boundary) | | 4e-38 |

  Both good fits say the same thing: **LP2 has about half the 2-rune words that English has** (15.9% against 27%),
  and slightly more words of 3, 4, 7 and 8 runes. The data cannot tell "missing short words" from "extra symbol in
  40% of words". Per-rune insertion (what a collision-insertion cipher would give) and lost word boundaries are
  rejected.
- The two-parameter family also prefers pure runes (r = 0) plus a = 0.40 (p = 0.015, 2 fitted parameters).
- **The dominant effect is one digraph: TH.** THE is English's commonest word and is a 2-rune word only because TH is
  a single rune (ᚦ). Spelling just TH as T+H (ᛏᚻ) takes G from 223 to 56 with no fitted parameter; spelling any
  other digraph as letters does nothing (G stays at 218-227). Spelling *all* digraphs as letters gives 54. So the
  length data say: **LP2's plaintext probably does not use the single TH rune** (and may spell everything letter by
  letter). Even then p = 5e-8, so a smaller effect remains: still too few 2-rune words (20% vs 15.9%) and too many
  7-8-rune words (4.0 vs 5.4%).
- All p-values are weak evidence once the model was chosen after looking: lead, not finding.

## Consequences
- Dictionary screens (`attack.py`) are blind to an inserted rune inside a word, and to missing function words they
  are not blind (they score what decodes). A null-tolerant dictionary matcher (one wildcard rune per word) is the
  natural next tool.
- An 8-hour-style hypothesis: text with few 2-letter words. Candidates: verse, a terse aphoristic register, or text
  where short function words are dropped. The solved sections (24% 2-rune words) are in between.
- The IoC-based `work/kscreen` screen is unaffected by all of this.

## Correction to an earlier version of this note
An earlier commit on this branch labelled the best two-parameter fit "digraph runes collapsed 0%" and concluded "no
digraph runes". The parameter is the probability of *expanding* a digraph rune to two letters, so r = 0 means pure
runes. Labels and text are fixed.

## For the reviewer
- Check the binning/G-test and the mechanism fits (`mechanisms()`); try your own corpora in `CORPORA`.

## Review (stronger-model pass, 2026-10-17)

Merged locally. The script was read in full before it was run; it touches the network only under `--fetch`, which was
**not** used at first (it downloads Project Gutenberg texts; that needed the user's permission, given later). Run without
`--fetch` it computes everything that depends on the Emerson text only, and those numbers reproduce the branch's
table exactly: English runes G = 222.7, English letters G = 54.1, "+1 rune in a fraction of multi-rune words" G = 20.4
(p = 0.025), "2-rune words missing" G = 17.1 (p = 0.071), per-rune insertion G = 143.5, fused boundaries G = 202.9,
TH spelled as T+H G = 56.0, all digraphs as letters G = 54.1, every other single digraph G = 218-227
(the committed `wordlen_languages.txt`).
- **The full table reproduces too** (follow-up, after the user allowed the download on 2026-10-17): `--fetch` took the 16 Project Gutenberg texts
  (15 MB into the git-ignored `work/ref/corpora/`); the regenerated `results/analysis/wordlen_languages.txt` is byte-identical to the branch's, so the
  language and register rows (all rejected: Latin, German, French, Spanish, Italian p < 1e-57; English registers 1e-23 .. 1e-68 in runes) stand.
- **The TH finding is real in the data and still only descriptive.** One zero-parameter change (THE becomes a 3-rune
  word) takes G from 223 to 56; no other digraph moves it. Still p = 5e-8, so something else is also missing (fewer
  2-rune words, more 7-8-rune words). Both the model and the cell choices were made after looking.
- **Correction to the "Consequences" section:** the repository's dictionary screens are not blind to TH as two
  letters. `attack.rune_spellings` returns every spelling of a word (digraph rune or letters, up to 16 spellings), and
  `rune_dictionary` indexes all of them, so `phpmt`, `rescreen` and `dsearch` already accept both. What they cannot
  handle is an inserted rune inside a word, which is the null-tolerant matcher the note asks for (not built).
- **What would settle the word-length lead:** a model that predicts the full histogram from a mechanism (not a
  fitted fraction) plus a positive control: plant English with the mechanism, run the same fits, and check that the
  true mechanism wins by G and the others lose. The mechanisms list has no such control yet.
