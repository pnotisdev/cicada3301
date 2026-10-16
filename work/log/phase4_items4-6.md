# Phase 4 items 4–6 and new leads (2026-10-16)

## Reference: the Wulfic/Cicada3301-Liber_Primus project
That is a large community project (constraints C1–C28, about 853 files). I read its summaries
(`ref/wulfic/*.md`) as data. It agrees with our independent results: primes, φ, constants and English keys are
ruled out, periodic keys and key reuse are ruled out, and it derived the same page-30 formula
|3301 − p(F + 1)|. It lists as open: a named custom generator, a "re-draw" or missed-check anti-doublet rule,
and the meaning of the 256-byte base-60 grid inside 0.15.

Their C14 rules out "skip to the next key value" on the grounds that surviving doublets would need about 19% key
repeats. Our model is different: skip, plus a check that is missed about 20% of the time. Under it, a skipped
rune gives Δc = k_{j+1} − k_j, which is flat for a uniform key, and the survivors come from the missed checks. That
matches the fingerprint (`sim.py`) and is the "hand check missing" row they list as consistent. **So our
skip-tolerant screens add coverage that their ledger does not have.**

## Item 6 – steganography
The `lp_outguessed/*.txt` files in rtkd/iddqd are the 2014 chain's OutGuess payloads. They include PGP-signed hex,
"Let the text guide you" with an embedded JPEG, the "For those who have fallen behind" grid, and the "Create one
Tor hidden service…" instructions. All of these are known stages that were solved in 2014. The 58,152-byte
binaries look random. None of it contains new key material for the unsolved runes.

## Base-60 grid in 0.15 (pages 64–66): 256 bytes (`work/grid60.py`)
- It is 32 rows of 8 two-digit base-60 numbers (digits 0–9, A–Z, a–x). The maximum is "4F" = 255, so they are
  bytes. Entropy is 7.17 bits/byte, which is what random bytes give.
- **Hash identity:** none of the grid bytes, the grid in hex or base-60 text form, the reversed grid, the solved
  texts or the unsolved rune strings has a SHA-512, SHA3-512 or BLAKE2b hash equal to the An End hash.
- **Passphrase decryption:** I tried 11,246 passphrases (every solved word, 2–4 word phrases, sentences and Cicada
  terms, in several cases) with AES-128/192/256 (ECB, CBC with a zero IV, CBC with the first block as IV, CTR) under
  MD5/SHA-1/SHA-256/SHA-512/EVP_BytesToKey/raw keys, plus a SHA-512 counter-mode XOR and RC4. That is 832,204
  decryptions. The best was 51% printable, which is chance level (real text would be about 100%). No file-format
  header appeared.

## Item 4 – hash and random-generator keystreams (`work/prng_screen.py`)
- 64 seeds: Cicada phrases, numbers, the An End hash, the grid hex. Generators: SHA-256/SHA-512/MD5 in counter
  mode, a SHA-256 hash chain, Python's MT19937 and a glibc-style LCG, with bytes taken mod 29 or by rejection. Each
  ran on 8 segments, 2 key offsets, ± sign and Atbash on/off, with the skip-tolerant fast screen.
- Best 0.198, against a control maximum of 0.185 here and 0.192–0.208 in earlier screens. The top 3 decode to
  0.09–0.13 with the exact decoder (noise; a real key is about 0.7). **Negative.**

## Item 5 – transposition
- **Transposition after encryption is ruled out.** The doublet deficit is present in normal reading order
  inside words (0.62%), across word gaps (0.81%) and across line breaks (0.77%). Reordering the ciphertext
  afterwards (columnar, spiral, page grid, word order) would make those neighbours random pairs at 3.45%. So the
  collision check was done on the text in the order we read it.
- Transposition before encryption cannot be tested without the key. The English-like word lengths and the 99 (corrected from 318)
  one-rune words make a rune-level scramble of the plaintext unlikely.
- **Reading direction:** all earlier screens ran the key forward from a segment's start. `rev_screen.py` tests a
  key running from the end of each segment, using a reversed-word dictionary (planted sanity check: 0.60 vs 0.15).
  **Result: negative.** All 80 number keystreams were slid over every offset, plus all keyword keys, on 8 segments
  with ± sign and Atbash on/off. Best 0.212, against 0.206 for 4 random controls (earlier full-slide controls reached
  0.208). The top numeric hits decode to 0.08–0.11 with the exact decoder (noise; a real key is about 0.7). Caveat:
  this run used the pre-fix word segmentation, which splits line-wrapped words. The heading-restart screen
  (`heading_screen.py`) was stopped before it ran and still needs a run with the corrected segmentation.
