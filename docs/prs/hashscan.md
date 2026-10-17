# PR: hashscan: passphrase -> hash stream keys, 19 million candidates (the "derived-key dictionary lane")

**Branch:** `research/hashscan` (new files only; one new crate, dependencies `md-5`, `sha1`, `sha2`)

## Why
The ciphertext is OTP-class: it cannot tell a true external pad from a keystream derived from a short secret. Dukotah's
ledger lists the "derived-key dictionary lane" (a passphrase hashed into a stream) as untested at scale; the earlier
screens here tried 65 Cicada strings. A hashed passphrase costs microseconds, so a very large dictionary is cheap.

## What this adds
- `work/hashscan` (Rust): for every candidate string a byte stream under 4 hashes (MD5, SHA-1, SHA-256, SHA-512) x 4
  stream conventions (H(s||ctr32be), H(s||decimal ctr from 0), H(s||decimal ctr from 1), chain H(H(...))) x 3 byte maps
  (b%29, floor(29b/256), reject b >= 232) x the 8 phpmt cipher variants (skip/coin, sign, Atbash) = 384 decodes per
  candidate, with the same skip-aware dictionary decoder as `work/phpmt` (copied verbatim by `assemble.py`).
- `make_candidates.py`: Cicada lore + every solved-text word and 2-4-word phrase (24k), the 10k frequency words in three
  cases (30k), 146k dates, **9.0M pairs** of the 1,500 most frequent words with 4 separators, **10M decimal numbers**
  0..9,999,999. `campaign.py` runs the tiers resumably; `verify.py` re-decodes the 20 best over the whole segment
  against random-string controls (flag only above 0.25; selection noise reaches ~0.12).
- `tests/test_hashscan.py` (2 tests, 12 s): the 16 (hash, convention) streams equal Python's `hashlib` byte for byte,
  and planted passphrases are recovered at rank 1 for several (hash, convention, map, model, sign, Atbash) settings.
- Results in `results/hashscan/` (top 4,000 per tier, logs, verification).

## Results (key starts on LP2 page 0, windows_07)
| tier | candidates | best screen score | whole-segment check of top 20 |
|---|---|---|---|
| lore | 23,976 | 14 | 0.075-0.103 (random strings 0.078 +- 0.006) |
| words | 29,722 | 14 | 0.084-0.102 |
| dates | 146,327 | 14 | 0.078-0.100 |
| pairs | 8,997,555 | 18 | 0.093-0.112 (z up to +5.5) |
| numbers | 10,000,000 | 20 | 0.084-0.110 |

A planted key scores 35-44 on a 60-rune window and 0.8 over a whole segment. **Negative: no passphrase in these
lists, under any of the 48 stream/map conventions and 8 cipher variants, is the LP2 key.** The throughput on the
16-thread laptop was 40k candidates/s uncontended (about 3k/s while three other sweeps ran).

## For the reviewer / the GPU
- SHA-256/MD5 on a GPU would give ~100x; the decoder is the same as phpmt's, so the CUDA port in `work/` can be reused.
- Obvious extensions: more conventions (HMAC, PBKDF2/scrypt/bcrypt with the common cost factors, "seed as a hex
  digest string" streams), the Cicada 2012-2014 puzzle texts as a phrase source, and key offsets other than 0.
- Not covered: conventions where the passphrase is not the only input (salts, counters in other positions).

## Review (stronger-model pass, 2026-10-17)

Merged locally; the Rust and Python were read before anything ran (no network calls, writes only the output files it is given, subprocess only for its own
binary and `verify.py`); the crate builds (`md-5`, `sha1`, `sha2` from crates.io) and both tests pass (16 hash/convention streams equal `hashlib` byte for byte;
planted passphrases are recovered at rank 1 for three settings).
- **The one reservation is the score, not the code.** `decode_fast` is the phpmt dictionary decoder: it counts dictionary words that sit exactly between the transcription's
  word separators. LP2's word lengths have no serial structure and a planted seed is invisible to that score once LP2's separators replace the English words'
  own (33 -> 0, `work/log/phase9_boundaries.md`). If the printed dots are not the plaintext's word boundaries, "no passphrase is the key" is not established by
  this run. A boundary-free rescore (bigram log-likelihood of the first 120 decoded runes, no separators) of the same candidate lists was run on the desktop CPU
  (`work/hashscan` mode `bgsweep`, `bg_verify.py`, `work/tests/test_hashscan_bg.py`; results in `results/hashscan/bg_*`). **Result, 2026-10-17 10:40: negative.** All 19.2 million
  candidates (lore 23,976; words 29,722; dates 146,327; pairs 8,997,555; numbers 10,000,000) x 4 hashes x 4 conventions x 3 maps x 8 cipher variants (369 M decodes per million candidates):
  not one decode passes the 40-rune gate (best path >= +60; a true key is near +300), the best recorded score is 54-59 in every tier, and the top candidates decoded over the whole
  section (729 runes of section 0.7) score -9.3 to -10.8 per rune against -10.2 to -10.9 for random strings (a true key: about +10). Controls: the Rust scores equal a Python
  reference built on `hashlib` keys, planted passphrases are recovered at rank 1 for three settings with every other candidate below 150. 375 s for the 10 M numbers on 14 threads.
- The candidate lists are reasonable (lore, words, dates, 9 M word pairs, 10 M numbers); the conventions (4 hashes x 4 counters x 3 byte maps) match the
  desktop's library streams, whose mod-29 and rejection maps are two of the three.
