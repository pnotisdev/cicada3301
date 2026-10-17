# Pull requests from the laptop session (2026-10-17, overnight)

The laptop worked alone for eight hours while the desktop ran its own queue. Everything is on separate branches of new
files (no existing file is modified, so they merge next to the desktop's logging/CUDA work). Each PR has its own
description in `docs/prs/<name>.md`. Create a PR from a branch with
`https://github.com/pnotisdev/cicada3301/compare/main...<branch>?expand=1`.

| branch | status on main | what it adds | headline |
|---|---|---|---|
| `research/restart-columns` | merged + reviewed | key-restart test by column coincidences; line-layout explanation; repeat spectrum | no restart at any unit type; the line-start anomaly is glyph width |
| `research/wordlen-languages` | merged + reviewed; later commits (word-gap check) not yet | word lengths against 17 corpora in 6 languages; mechanism fits; TH finding; **word boundaries checked against the page images** | boundaries are authentic (0 of 2,334 transcribed word dots missing); the 2-rune deficit is mostly "TH spelled T+H" (G 223 -> 56) |
| `research/word-internal-lag5` | first commit merged + reviewed; later commits not yet | lag-5 repeated bigrams inside words; dictionary-consistency test for per-word algebraic keys; per-word recurrences of order 2 and 3 | 9 vs 1.5 repeated bigrams at lag 5 (P < 5e-5); excludes per-word constant/linear/quadratic/periodic(<=7)/recurrence(<=3) keys |
| `research/prngx-generators` | new | `work/prngx`: MT (init_genrand and init_by_array), MSVC, Java, drand48 generators with 3-6 key maps each, plus an OEIS lane (199,075 integer sequences as keystreams) | stage A (334 M human-plausible seeds per generator) and the OEIS lane are negative; OEIS lane also negative on page and heading starts; stage B: rand48 8 of 16 chunks done and negative, the rest of rand48, msvc and java are for the desktop |
| `research/hashscan` | new | `work/hashscan`: passphrase -> MD5/SHA-1/SHA-256/SHA-512 stream keys (4 conventions x 3 byte maps) for 19 M candidates | negative |
| `research/restart-llr` | new | log-likelihood-ratio restart test (more informative than counting equal pairs); information limit of drift-aware pairwise alignment; red headings under all 812 affine maps | restart at paragraphs/pages/sentences/lines excluded, restart at the 9 section starts is NOT testable (power Z ~ 2.7); headings are not an affine cipher of English |
| `research/new-hypotheses` | reviewed 14:30, final kscreen-typo push read 19:40, NOT merged (see `docs/prs/new-hypotheses.md`) | keyless exclusions (progressive / multiplicative / cumulative keys, ditto letter, doublet restarts); `work/layer2`, a two-layer screen (keyword Vigenere inside a number stream with the anti-repeat rule); `prng-time`: Java 48-bit and CPython two-word seeds from millisecond timestamps | all negative; vectors independently re-checked (86 of 86 match); accept after two changes (gate that fails on skips, independent planting) |

## Independent reproduction of `main` on the laptop
`main` at 71dc4b5 (the desktop's step-domain work) was built from scratch on the laptop CPU through the runner
(`python jobs/overnight.py run selftest`): **93 tests pass (11 skipped: the CUDA tests), the kscreen controls pass**
(15/15 planted windows, random-key null below the threshold). So the desktop's results do not depend on the desktop.

## Small observations that did not get their own branch
- **The lag-5 echo is carried by the rune S (index 15).** 11 of the 102 within-word lag-5 coincidences are S (10.8%,
  chance 3.25%, z ~ +4.4; other lags: 0-2%), spread over six of the eight sections. In four of the eleven words the equal
  S positions are 0 and 5 (e.g. ᛋᚣᛗᛞᚣᛋ, ᛋᚩᛠᚳᛖᛋ, ᛋᛞᛝᚷᛚᛋᛞᛝ, ᛋᛟᚱᚢᚹᛋᛚᛡ), the others at 1-3 and 6-8. The
  aldegonde note `rune-s-lag5-echo.md` reports the same. Any mechanism for the echo has to explain why S.
- **Clause lengths are English-like**: LP2's '.'-delimited clauses have median 11 and mean 14.8 words (Emerson clauses
  median 14, mean 16.9; the solved pages 6 and 7.7).
- **No word-level checksum**: sums of rune indices or prime values modulo 2-29 (90 tests) show nothing beyond the
  parity of word length.
- **The numeral '7' and the 1-5 list markers** sit where earlier sessions said; no pattern with the preceding text.

## What to run on the desktop
- `python work/prngx/campaign.py run stageB` (finished chunks are skipped): the remaining ~92% of the 32-bit seed space for
  `rand48`, `msvc`, `java` (hours on a CPU, minutes on a GPU) and, if ported, `mt`/`pymt` (~6 h each on a CPU). The
  generators are 5-20 lines of CUDA each (LCGs) or the phpmt kernel (MT).
- `hashscan` is a candidate for the GPU as well (SHA-256/MD5 are cheap there); the dictionary is `make_candidates.py`.
  More conventions (HMAC, PBKDF2) are the obvious extension;
  `work/prngx/kdf_streams.py` already covers RC4, AES-CTR, ChaCha20, PBKDF2 and scrypt for the lore list.
- If hashcat is installed, the 2080 Ti is the natural machine for brute-forcing the last page's 512-bit hash with masks
  (SHA-512 on that card runs at billions per second; every 7-character mask is minutes). The community's
  `Cicada-DWH-HashcatAttempts` shows which charsets were tried; not run here.
- Any new keystream family can be added to the OEIS lane's machinery: `seq` takes a text file `<id> v0 v1 ...` (values
  mod 29).

## How these relate to the community notes (read after the fact, third-party data)
The cicada-solvers/aldegonde `hypotheses/` notes contain independent versions of several observations: the line-initial
glyph-width artefact, the within-word lag-5 echo with paired matches at separations 1 and 4, the disproof of an additive
per-word 5-periodic key, and the 2-rune short-word deficit with "boundary authenticity unresolved". The branches above
turn some of those into checks with controls: the word boundaries are now verified against the images, the lag-5
excess has a within-word localisation and an English yardstick, and per-word algebraic keys are excluded by a dictionary
test with planted controls. Their length-clocked-walk model (period-5 mixed alphabets plus a per-word step) is a
different family that none of these tests can see; see `word-internal.md` for why a dictionary has almost nothing to
test there.

## Honest status
Nothing here is a solution. The two new positive observations are small: the word-internal lag-5 clustering
(P ~ 1e-4 .. 5e-3 depending on the null) and the word-length shape (best fits: TH not a single rune, plus about 40%
extra runes or half the 2-rune words missing, p 0.03-0.07). Everything else is a negative with a planted positive control.

## Review notes from the desktop (2026-10-17)

- Everything above is merged on `main`; each PR file has a "Review" section. All tests were read first and run afterwards (`restart_llr`, `hashscan`, `prngx`, `kdf_streams`, `word_recurrence` pass).
- **The rune-S observation is real and stronger than the lag-5 total**: of the 102 within-word lag-5 coincidences 11 are S (expected 2.3; Poisson P = 3e-5 per (lag, rune) cell, about 0.007
  after the 232 cells looked at); no other lag has a rune above z 3.4. Four of the 22 S-initial words of 6+ runes have S again at position 5 (P = 0.006).
  Five of the 11 pairs are in section 0.15 (the longest, 3,316 runes), two in 0.14 and one each in 0.7, 0.8, 0.9 and 0.11; P(S) by position in the word is flat (2.8-4.0%). Still no mechanism.
- **Clause lengths:** the figures agree with the desktop's once the page and paragraph marks count as clause ends (median 12 words, CV 0.81); with '.' alone the CV is 0.94. The desktop's reading of the word separators
  (`work/log/phase9_boundaries.md`) rests on the serial structure of the word lengths and on the first word of a clause being an ordinary word, not on the clause lengths.
- **Boundary caveat for the dictionary-scored PRs** (hashscan, prngx): see their review sections. Stage B is covered on the GPU.
