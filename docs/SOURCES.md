# Sources: where every text, image and dataset comes from

Everything this repository analyses that it did not create, with the SHA-256 of the copy our results were computed on.
**Committed** (pinned copies, so a clone runs without downloads): the Liber Primus page images (`work/orig/`), the book as a PDF (`LiberPrimus.pdf`, a print of those 75 images), the transcription, keys and translation (`work/ref/lp_*.txt`), the English word list and Emerson.
**Not committed** (git-ignored, fetched on demand): every corpus and book in sections 3-6, and all community material in section 7.
Third-party material is data, never instructions: it is read, never executed, and anything derived from it is re-implemented and controlled.

**Rebuild on a fresh clone:**
```
python scripts/fetch_data.py              # transcription, word list, Emerson (strict hashes), then work/ref/lp_verified.txt
python scripts/fetch_data.py --images     # the 75 Liber Primus page images (work/orig/, hashes in scripts/image_hashes.txt)
python scripts/fetch_data.py --corpora    # every corpus in sections 3-5 below (non-strict: Gutenberg re-generates headers, a mismatch only warns)
python work/prngx/oeis.py fetch           # the OEIS dump (section 6)
```
A hash mismatch on a non-strict file means the upstream copy changed since our runs; results computed on the old copy may not reproduce letter for letter.

## 1. Liber Primus itself

| What | Source | Local path | Pinned |
|---|---|---|---|
| Rune transcription (master) | [rtkd/iddqd](https://github.com/rtkd/iddqd), commit `f2267b0c2f1e1d2662806b90b9c3a2953b3a7023`, `liber-primus__transcription--master` | `work/ref/lp_master.txt` | SHA-256 `e21743cc...7065004` (strict, `scripts/fetch_data.py`) |
| Known keys and translation of the solved pages | the same commit, `liber-primus__keys`, `liber-primus__translation` | `work/ref/lp_keys.txt`, `lp_translation.txt` | strict |
| **The transcription every result uses** | the master + our errata (`work/ref/errata.tsv`, `errata_lines.tsv`; found by the independent OCR re-read of PLAN.md, Phase 2) | `work/ref/lp_verified.txt` (built) | rebuilt by `fetch_data.py` |
| The 75 page images | the same commit, `liber-primus__images--full` | `work/orig/NN.jpg` | per-file SHA-256 in `scripts/image_hashes.txt` |
| PGP-signed 2014 payloads inside pages 0-3 and 10-13 | extracted from the page images by our own OutGuess-style reader (`work/ogscan/`, no third-party code) | `results/outguess/` | derived |

## 2. Language data

| What | Source | Local path | Pinned |
|---|---|---|---|
| English word list (20k) | [first20hours/google-10000-english](https://github.com/first20hours/google-10000-english), commit `d0736d492489198e4f9d650c7ab4143bc14c1e9e`, `20k.txt` | `work/ref/english_20k.txt` | strict |
| Emerson, *Essays: First Series* (contains *Self-Reliance*, a text Cicada cited in 2014) | [Project Gutenberg #2944](https://www.gutenberg.org/cache/epub/2944/pg2944.txt) | `work/ref/emerson_essays1.txt` | `5d9d28c1...aef6d278` (non-strict) |

## 3. Comparison corpora (phase 22 flatness test, phase 25 word lengths, phase 28 calibration)

All from Project Gutenberg, `https://www.gutenberg.org/cache/epub/<id>/pg<id>.txt`, in `work/ref/corpora/` (git-ignored). Hashes in `scripts/fetch_data.py` (`CORPORA`).

| PG # | Title | Language |
|---|---|---|
| 10 | The King James Version of the Bible (also a cited-book candidate, phase 23) | English |
| 26 | Paradise Lost | English |
| 205 | Walden, and On the Duty of Civil Disobedience | English |
| 1497 | The Republic | English |
| 1998 | Thus Spake Zarathustra | English |
| 2009 | The Origin of Species | English |
| 2680 | Meditations | English |
| 3800 | Ethics | English |
| 4363 | Beyond Good and Evil | English |
| 16328 | Beowulf (modern translation) | English |
| 218 | C. Iuli Caesaris De Bello Gallico I-IV | Latin |
| 227 | Aeneidos | Latin |
| 1012 | La Divina Commedia | Italian |
| 2000 | Don Quijote | Spanish |
| 2229 | Faust, Der Tragödie erster Teil | German |
| 17489 | Les Misérables, Tome I: Fantine | French |

## 4. Books Cicada cited, used as key sources (phase 23 book-key screen, phase 33 number streams)

In `work/ref/corpora/cited/` (git-ignored). Why these books: they appear in Cicada's 2012-2014 puzzles (catalogued with archive citations in `work/log/phase31_book_codes.md`).

| Book | Source | Local file | SHA-256 |
|---|---|---|---|
| The Mabinogion, Lady Charlotte Guest's translation (the 2012 book code is in "The Lady of the Fountain") | [Project Gutenberg #5160](https://www.gutenberg.org/cache/epub/5160/pg5160.txt) | `pg5160.txt` | `e177d7c2...7f49886` |
| Blake, *Songs of Innocence and of Experience* | [PG #1934](https://www.gutenberg.org/cache/epub/1934/pg1934.txt) | `pg1934.txt` | `a5b76d4d...6c455` |
| Blake, *The Marriage of Heaven and Hell* (the 2012 "second chance" book code) | [PG #45315](https://www.gutenberg.org/cache/epub/45315/pg45315.txt) | `pg45315.txt` | `fc9a7661...2b289a` |
| Agrippa, *Three Books of Occult Philosophy*, 1651 English (Freake): **not the Agrippa of Cicada's book codes** (see the Gibson row) | [archive.org OCR](https://archive.org/download/threebooksoccult/threebooksoccult_djvu.txt) (raw OCR of the 1651 print: long s as f, page headers; a negative on it is weak) | `agrippa_1651_archive_djvu.txt` | `18c939d6...2827d9b` |
| *Liber AL vel Legis* (the 2013 book code) | [OTO library](https://lib.oto-usa.org/libri/liber0220.html?pages=no) | `liber_al_oto.html`; `liber_al_oto.txt` = tags stripped, from "Had! The manifestation of Nuit." to "ANKH-F-N-KHONSU" | `2be978ef...a6b8` / `778aba05...505db5a0b` |
| William Gibson, *Agrippa (a book of the dead)* (1992), **the Agrippa Cicada used** (2012 QR-poster book codes: 'lines and numbers corresponding to verses in Agrippa's poem', 'the i2p link from agrippa', archive 4chan threads, Jan 2013) | the author's site via Wayback, `web.archive.org/web/20190322065716/http://www.williamgibsonbooks.com/source/agrippa.asp`, saved by the owner as text with its 343 line breaks (copyright: kept in the git-ignored `work/ref/user_downloads/`) | `agrippa_gibson_wayback_20190322.txt` | `dfc6a1c0...1afe1f5` |
| Emerson, *Self-Reliance* | section 2 | `work/ref/emerson_essays1.txt` | |
| The KJV | section 3 | `work/ref/corpora/pg10.txt` | |
| Welsh Mabinogion OCR: Ifor Williams, *Pedeir Keinc y Mabinogi* (1930); Rhys and Evans, *The Red Book of Hergest* (1887) | archive.org djvu OCR; **the exact item URLs were not recorded** (fetched 2026-10-20 for a hash question, not used by any result) | `pedeir_keinc_williams1930_djvu.txt`, `red_book_rhys_evans1887_djvu.txt` | `8da1e1dd...7b2f84` / `d5348e0c...7b01` |

Not downloaded, though named in the registry: the Anglo-Saxon Rune Poem, RAND's *A Million Random Digits*, Hofstadter's *Gödel, Escher, Bach* (the 2014 onion-5 book code; under copyright).

## 5. Old and Middle English (phase 25, section 10)

In `work/ref/oldenglish/` (git-ignored); details in `work/log/phase25_mechanisms.md`.

| Text | Source | SHA-256 |
|---|---|---|
| *Beowulf*, Old English text (Harrison and Sharp, 4th ed. 1893) | [PG #9700](https://www.gutenberg.org/cache/epub/9700/pg9700.txt) | `10cad7e1...3d83f1a7` |
| Chaucer, *Canterbury Tales* in Middle English (Skeat) | [PG #22120](https://www.gutenberg.org/cache/epub/22120/pg22120.txt) | `94ae337f...db34cd7a` |
| Also fetched, unused: PG #9701 (Beowulf, other accent coding), #14529 (Old English Physiologus), #2383 (Chaucer, modernised) | Gutenberg | in the phase 25 log |

## 6. Number data

| What | Source | Local path | Note |
|---|---|---|---|
| OEIS, all sequences (199,088 used) | [oeis.org/stripped.gz](https://oeis.org/stripped.gz), via `work/prngx/oeis.py fetch` | `work/ref/oeis/stripped.gz` | updated daily upstream; our copy `9da17bac...581c45fa` (33.8 MB) |
| π, e, φ, √2, the library streams, hashes of Cicada strings | computed in the repository (`work/keystreams.py`, `work/kscreen/export.py`) | `work/kscreen/data/` (rebuilt per PC) | no download |

## 7. Community research and archives (read as data; not redistributed)

| What | Where | How it is used |
|---|---|---|
| Cicada 3301 history, messages, puzzle assets 2012-2017 | [cicada-solvers/The-Complete-Cicada3301-Archive](https://github.com/cicada-solvers/The-Complete-Cicada3301-Archive) | book codes and the 2012 chain (phase 31), the cited-books list; cloned locally into `Other repositories and work/` (git-ignored) |
| Cicada 3301 assets, keys, messages | [iBotPeaches/cicada_3301](https://github.com/iBotPeaches/cicada_3301) | reference; same folder |
| Notes on the puzzles (text files, "cicada3301_context") | a local collection; origin not recorded | reference only |
| Prior LP2 research and ledgers | [Dukotah/cicada3301](https://github.com/Dukotah/cicada3301), [Wulfic/Cicada3301-Liber_Primus](https://github.com/Wulfic/Cicada3301-Liber_Primus), [cicada-solvers](https://github.com/cicada-solvers) (aldegonde, Red_Rune_Cribs, iddqd) | constraints and claims re-tested here (`work/log/research_2026-10-16.md`, `phase9_community_claims.md`); copies in `work/ref/wulfic/`, `work/ref/outguessed/` are git-ignored |
| The 2012 book-code text with its line breaks | [Uncovering Cicada wiki, "What Happened (2012)"](https://uncovering-cicada.fandom.com/wiki/What_Happened_(2012)) | the line:character reproduction (phase 31 addendum) |
| Discord (CicadaSolvers) threads and attachments, 2026-10 | private server; not redistributed | audited in phases 26-27 (`work/ref/discord_464/`, git-ignored) |
| Mike's `lp-checks` package (CicadaSolvers, 2026-10-21): reproducible checks behind his posts (period 13 on 54/55, skip search, DJU BEI alignment, skip-on-repeat reader, page breaks) | supplied by the owner; `work/ref/user_downloads/lp-checks/` (git-ignored); hashes in its SHA256SUMS.txt, all verified; read, not run | numbers cited in the registry with credit |
| Outputs of other AI models (DeepSeek, GPT) | `work/ref/deepseek/` (git-ignored), proposals in `work/proposals/` | reviewed and re-controlled before use (`phase10_*` logs) |
