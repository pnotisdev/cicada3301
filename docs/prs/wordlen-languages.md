# PR: word-length test against other languages and English registers

**Branch:** `research/wordlen-languages` (new files only)

## What this adds
- `work/wordlen_languages.py`: compares LP2's 2,928 word lengths with about 30 models by a G-test (12 bins). Corpora
  are public-domain Gutenberg texts, downloaded by `--fetch` into `work/ref/corpora/` (git-ignored there):
  English (Emerson, Beowulf translation, KJV, Milton, Plato, Marcus Aurelius, Nietzsche x2, Thoreau, Spinoza,
  Darwin), Latin (Caesar, Vergil), German, French, Spanish, Italian. Each is spelled as Gematria Primus runes
  (digraph runes TH/NG/EA/OE/AE/EO/IA as `lp.word_to_key`) and as plain letters. A two-parameter family on English
  adds "digraph runes collapsed with probability r" and "an extra rune in a fraction a of multi-rune words".
- `results/analysis/wordlen_languages.txt`: the full table.

## Results
- **No foreign language is close.** German, French, Spanish, Italian, Latin: p < 1e-57, all with the wrong shape.
- **English in runes is rejected in every register** (p 1e-23 .. 1e-68). **English in plain letters (no digraph
  runes) is much closer**: Emerson p = 1e-7, Beowulf translation 8e-8, Zarathustra 3.5e-9, Walden 2e-9, other
  registers 1e-16 .. 1e-38. None fits.
- **The best model is English letters + an extra rune in about 40% of multi-rune words**: G = 20.4, 9 df, p = 0.015
  with two fitted parameters (the digraph collapse fits at 0%, i.e. no digraph runes; the exact a is in the table
  file). LP2's lengths look like English spelled letter by letter, with roughly one extra symbol in two of every five
  multi-letter words (nulls, padding or per-word initialisation symbols). One-rune words (3.4%, the A/I rate) show
  no such padding.
- Caveat: p = 0.015 with 2 fitted parameters is weak. It is a lead, not a finding.

## Consequences
- Dictionary screens (`attack.py`) already spell each word both ways (digraph on/off), so they were not blind to the
  letter-by-letter convention, but they are blind to a 40% extra rune: a word with a null inside never matches.
  A null-tolerant dictionary matcher is the natural next tool (a word may carry one wildcard rune).
- The IoC-based `work/kscreen` screen is unaffected by all of this.

## For the reviewer
- Check the binning/G-test and whether the two-parameter family double counts the digraph collapse.
- Try your own corpora in `CORPORA`.
