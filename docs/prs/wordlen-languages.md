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
