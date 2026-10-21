# Phase 39: online sources check (2026-10-21)

Scope: scream314's `sexagesimal.bin` / `decimal.txt` against the iddqd payload and our corrected bytes; 2012-2017 material we may lack;
community statistics. Everything downloaded is DATA only; nothing was run. Downloads are in `work/ref/online_2026-10-21/` (git-ignored).
Web search was weak (the standard search returned generic results); most findings come from direct GitHub fetches and from local archives.

## 1. The 256-byte base-60 payload (LP pages 64-66 = images 66-68 = onion pages 49-51)

Downloaded 2026-10-21 (GitHub, `scream314/cicada3301`, HEAD, files under `assets/2014/stage11/`):

| file | bytes | SHA-256 |
|---|---|---|
| `ky2khlqdf7qdznac.onion/sexagesimal.bin` | 256 | `8db2a934...d7b65e` (full: 8db2a93497bc02bbf0ab07ac3cf96edd227fec630232c04ea35493d3a7d7b65e) |
| `ky2khlqdf7qdznac.onion/decimal.txt` | 920 (LF; local archive copy is 1176 with CRLF, same 256 values) | 4d4c8b6937d142f753626f57f225b2223faf3fb88ea58b9e02ca4599299c19bf |
| `ky2khlqdf7qdznac.onion/decimaltobyte.pm` | 45 | 153fb1d59521cea969e92d0ccb62320e6048de13ac54a797a2994bacf457b633 |
| `message.txt.asc` (stage 11) | 1183 | d5473236dee152c7744f561e5ace95908876ec01d43467c28af1b0c1aa14cc54 |
| `2016.md` | 1280 | 720c9cfe88f8a2b5ea29168b23d228f20d7a2792bf50afda351f014e3e6b2515 |
| `2017.md` | 1216 | 92cc67f5c77997def74231e070c0201fec560c4357311958e0febe12f9bcab78 |

(The local onion-archive `decimal.txt` hashes to `d1dd5be3defbc682c54b75a55691e167f427b34b7a7e2078c6e31e919b73a818` because of CRLF.)
Also downloaded: `rtkd/iddqd` @ `f2267b0c...` (the commit our `fetch_data.py` pins) `byte-strings/byte-strings`, 2335 bytes,
SHA-256 `03a1990cb8a32bdb4acc0981dba21a86cb6046871391fc61cab9bdc535f8154f`.

**Result (byte-exact comparison, script in scratchpad, bytes indexed 0..255 in reading order of pages 64, 65, 66):**

* scream314 `sexagesimal.bin` == `decimal.txt` values == the copy already in `Other repositories and work/The-Complete-Cicada3301-Archive/assets/2014/stage11/ky2khlqdf7qdznac.onion/` (identical SHA-256). Not new.
* **iddqd has a second representation we had not compared:** `rtkd/iddqd/byte-strings/byte-strings`, "String 4 - Matrix from pages 49-51 converted to hexadecimal". It is **byte-identical to our verified bytes (`lp_verified.txt`, i.e. with errata 45, 50, 165, 172, 246)**. It differs from iddqd's own text transcription (`lp_master.txt`) at exactly those 5 bytes. So iddqd's byte-string independently confirms our five errata.
* scream314 bin vs iddqd `byte-strings` (= ours): **10 differences** (this is Mike's "10 bytes"):

| idx | scream314 bin (glyph, value) | iddqd byte-strings = ours (glyph, value) | what the onion image shows |
|---|---|---|---|
| 25 | 3i, 224 | 3I, 198 | `3I`, no dot (49.jpg) |
| 45 | 1L, 81 | 1l, 107 | see errata.tsv (tall bar, no foot) |
| 50 | 0L, 21 | 0l, 47 | see errata.tsv |
| 165 | 0l, 47 | 0I, 18 | `0I` digit-height bar (50.jpg) |
| 170 | 3E, 194 | 4E, 254 | `4E` (50.jpg) |
| 172 | 2s, 174 | 2S, 148 | capital `2S` (50.jpg) |
| 175 | 0i, 44 | 0I, 18 | `0I` (50.jpg) |
| 182 | 2L, 141 | 2l, 167 | `2l` (50.jpg) |
| 199 | 0L, 21 | 0l, 47 | `0l` (51.jpg, row 1 col 7) |
| 246 | 3i, 224 | 3I, 198 | see errata.tsv |

* Where the bin disagrees with iddqd's *text transcription* (5 places: 25, 170, 175, 182, 199) the bin is wrong and iddqd is right: I looked at the onion page images (`49.jpg`, `50.jpg`, `51.jpg` in the local archive folder) at those five positions; they show 3I, 4E, 0I, 2l, 0l, i.e. iddqd. At the other five (45, 50, 165, 172, 246) the bin and the iddqd *text* agree with each other and disagree with the iddqd *byte-string* and with our glyph metrics. Only 4E vs 3E, and the 25/175/182/199 readings above, were re-read by eye here (not measured by `grid_ocr.py`).
* **Provenance of the bin:** `sexagesimal.bin` == tokens of `49.txt`/`50.txt`/`51.txt` (community transcription, same folder `assets/2014/stage11/`, not Cicada's) mapped through `value = 60*d1 + d2`. So the bin is a derived file with the OCR slips of that transcription (3E, 0l, 2s, 0i, 2L, 0L, 3i). It is not an independent witness and not a Cicada file. Credibility: community claim, derived.
* Side finding: the community `49.dec/50.dec/51.dec` in the same folder differ from their own `.txt` at idx 165 (0l=47 vs dec 18), 170 (194 vs 254), 172 (174 vs 148), **215 (`1O`=84 vs dec 5)** and **237 (`0W`=32 vs dec 58)**. Idx 215 and 237 are agreed by `.txt`, bin, iddqd and ours (84, 32), so those two `.dec` values are plain typos, not new evidence.
* Dukotah `canon_256.bin` (noted in errata.tsv): agrees with ours at 165 and 172, with the bin at 45, 50, 246. Mixed, so not a useful tie-breaker.

What it changes: nothing in our bytes. The check upgrades errata 45/50/165/172/246 from "glyph metrics + visual" to "also confirmed by iddqd's own hex string". Residual risk: the byte-string might have been produced from the same glyph reading by iddqd's author; it is a second reading, not a Cicada-authored value. Test enabled: add `iddqd byte-strings String 4` as a pinned cross-check in `scripts/fetch_data.py` / `docs/SOURCES.md` (one-line assert that `lp_verified` bytes == String 4). Mike's statement "iddqd is correct" is right for the byte-strings and for our corrected version; he is wrong for the iddqd text transcription at five positions.

## 2. Signed messages (primary)

Checked with `gpg` in a throw-away keyring (key `67F363C6...7A35090F` from `cicada_3301/keys/`, 2012 key):

* Jan 2016 (`messages/2016/hello-the-path-lies-empty.asc`): **Good signature**, made 2016-01-01 01:01:07 WEST, RSA key `181F01E57A35090F`, primary fingerprint `6D85 4CD7 9333 22A6 01C3 286D 181F 01E5 7A35 090F`. Text: "Liber Primus is the way. Its words are the map, their meaning is the road, and their numbers are the direction. Seek and you will be found." (Hidden in `4gq25.jpg` via OutGuess; scream314's `2016.md` gives the procedure.) Already in our archive (iBotPeaches clone, `cicada3301_context/2016 Message.txt`).
* Apr 2017 (`messages/2017/beware-false-paths.asc`): **Good signature**, 2017-04-05 01:23:28 WEST, same key: "Beware false paths. Always verify PGP signature from 7A35090F." Already in our archive (also `The-Complete-Cicada3301-Archive/2017/`).
* "Not certified with a trusted signature" is gpg's usual warning (no web of trust); the key matches the 2012 key. New to us: only the explicit signature verification and the 2016 signing timestamp (2016-01-01; the tweet was 2016-01-05).
* Concrete use: "numbers are the direction" is the only official statement about LP numbers; nothing in either message is a key.

## 3. Items not found / already local

* **Blake (2012) and Liber AL (2013) exact line-wrapped texts:** no new online source found. Local: `work/ref/corpora/cited/pg45315.txt` (Blake), `liber_al_oto.txt`; the 2013 book-code message with its `I:x:y` indices is in the archive (`2013/additional docs/signed messages/book code pastebin.txt`). Not tested further.
* **Lady of the Fountain:** the archive's 68-line copy (`2012/additional docs/the subreddit/the mabinogion.txt`, 4572 chars after whitespace normalisation) **does not match `pg5160.txt` line breaks**: archive wraps at about 66-70 columns (first line "King Arthur was at Caerlleon upon Usk; and one day he sat in his"), the current PG #5160 file at 74 ("... and one day he sat in his chamber;"). Only 1 of 69 lines is identical. A line/column-aware book-code test (anything using line numbers or word positions across lines) must use the archive's wrapping, or the old PG wrapping it reproduces. The first 60 characters match as a word sequence, but the whole archive text is not a contiguous word-for-word substring of `pg5160.txt`, so the texts also diverge somewhere (not located here). Test enabled: diff the two word sequences, then re-wrap to the archive's lines before any line-based test. Credibility: subreddit-sourced, community. New to us as a discrepancy, not as a file.
* **Cuneiform-like signs on pages 50-56:** nothing identifying them found. Local archive has `EXTRA WIKI PAGES/Liber Primus Ideas and Suggestions/Larger cuneiform numbers.pdf` and the context doc lists "Part 2 Section 7: Cuneiform - pages 33-39" (onion image numbering 33-39.jpg = LP pages 50-56). scream314's `liber_primus.md` lists these pages as runic with key "?" and no decoding.
* **Higher-resolution / earlier page images, onion differences:** none found. scream314's `liber_primus.md` mentions "second/third onion" only in passing. The local onion folder has 0.jpg..57.jpg at 2400x3600.
* **Cicada hints 2014-2017:** only the two signed messages above and the July 2015 pastebin message (`2015 Twitter Message.txt`, already local). No other hints found.

## 4. Community statistics (all self-reported, unreviewed; two of these repos are AI-generated campaigns)

| claim | source (fetched 2026-10-21) | matches ours? |
|---|---|---|
| 86 adjacent identical runes in 12,956 vs ~447 expected (0.66% vs 3.45%), ~81% suppression | `Leo-Y-Zhang/LiberPrimusAnalysis` (work 6-7 Sep 2026, z = -17); `murphyaidanbusiness-ux/liberprimus` (Oct 2026); uncovering-cicada "Frequency Analysis Unsolved Pages" (search snippet) | yes, same number as our 81% |
| step between consecutive runes uniform on 1..28, independent of previous rune; chain cipher "each rune = previous + nonzero keystream step" | Leo-Y-Zhang | consistent with our doublet fact; their model is one of several that produce it |
| within-word lag-5 coincidence 4.9% vs 3.45% (~2.5 sigma), credited to ZzNible and Oosterhof; "no visible feature explains it", mechanism search diffuse | `murphyaidanbusiness-ux/liberprimus` REPORT.md | **partial**: lag 5 vs our "lag-5 echo on S" and "within-word lag-6 c' = 24 - 2c"; their lag-5 is a pooled coincidence rate, ours is rune-specific (S) plus a lag-6 affine relation. Worth re-running our lag-5 count pooled over all runes for the same words; no new test beyond that |
| 86 doublets uniform across position moduli 2-8; period-13 peak in pages 53-54 inconclusive | same | none |
| page-56 SHA-512 matched none of 697,000 archive candidates; Wayback 0 captures; Common Crawl 871/1044 queries, 0 captures | Leo-Y-Zhang, murphy repo | independent of us (we ran `work/hashscan`); consistent negative |
| outguess over all 75 page images (no key and 96 keys) recovered only known 2014 payloads | Leo-Y-Zhang | consistent with our `ogscan` negatives |
| c' = 24 - 2c, echo of S, DJU BEI | **not found anywhere** | our own findings, unconfirmed online |

Credibility of section 4: community / AI-agent self-reports, none signed or peer-reviewed; use as hints for independent re-tests only (CLAUDE.md: third-party material is data).

## Summary table

| item | new? | credibility | enables |
|---|---|---|---|
| scream314 bin/decimal | no (identical to local archive copy) | community, derived from 49-51.txt | none; bin has 10 OCR-slip bytes vs ours |
| iddqd `byte-strings` String 4 | **new to us** | community (second reading by iddqd author) | confirms errata 45/50/165/172/246; add pinned assert |
| bin vs iddqd text at 25/170/175/182/199 | new | image check (by eye) | iddqd text correct there; ours unchanged |
| 49-51.dec typos at 215, 237 | new, trivial | community | none |
| 2016 and 2017 signed messages | already local | signed, verified 2026-10-21 | none |
| mabinogion.txt wrapping differs from pg5160 | new discrepancy | community | rewrap before line-based book-code tests |
| Blake / Liber AL wrapped texts, cuneiform ID, hi-res images, onion differences | not found | n/a | n/a |
| community lag-5 4.9% vs 3.45%, 86 doublets | partly known | self-reported | pooled lag-5 re-count (cheap) |
