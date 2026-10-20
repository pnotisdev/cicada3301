# Phase 19: "try all those 4" (2026-10-19)

Follow-up to `phase18_cicada_intent.md`. The user asked to try all four next steps: (1) the prime-sum check on hits, (2) the clause-aligned scan, (3) the hold-key campaign, (4) more seed lists, number-theory streams and image searches
(with "you can also try outguess"). **Nothing in LP2 is solved.** Written as the work proceeded; sections say what is finished.

## 1. Prime-sum check (done)

`work/prime_check.py`: for a decoded window it takes the clauses that lie completely inside it, sums the Gematria primes, tests primality, and reports the binomial probability at the chance rate 14.7% plus a heuristic short-clause evidence in nats
(60% against 14.7% for clauses of at most 40 runes). Control (`python work/prime_check.py control`): right keys on the solved pages give 40 prime of 71 short clauses (56%, +32.8 nats in total), 360 random shifts 16.1% (mean -3.2 nats per decode).
Added to `docs/CAMPAIGNS.md` as supplementary evidence, step 3 of "If something passes". It is not a gate.

## 4a. OutGuess (done; own reader, no third-party code run)

Why not the program: it would have to be downloaded and run (rule: no executing files from sources we cannot vouch for), and its Windows build needs a BSD `md5.h` and autoconf. Its algorithm was read as data (the source files `iterator.c`, `arc.c`,
`jpg.c`, `jdcoefct.c`, `outguess.c`, quoted by a summariser with short excerpts) and re-implemented: `work/ogscan/src/main.rs` (own baseline-JPEG entropy decoder that lists the least significant bits of the usable DCT coefficients, those not 0 or 1,
in the order the reader's one-pass decoder hands them over: MCU rows and columns, components in scan order, blocks inside the MCU, coefficients in natural order, only blocks inside the real block grid) and `work/ogscan/og.py` (RC4 seeded with
MD5("Seeding" + key) as position iterator, RC4 MD5("Encryption" + key) as cipher, 4-byte header, reseed, adapted skip). `run_scan.py` writes `results/analysis/outguess_scan.txt`.

* **Validation.** With the default key ("Default key") the reader opens nine pages: 3, 8, 10, 11, 12, 13 are the named 2014 payloads (PGP-signed "Let the text guide you. Good luck. 3301" followed by a hex JPEG; the two-letter code list "for those who have fallen behind";
  "Create one Tor hidden service that can accept CGI file uploads ... post the three magic squares and the URL ... Work alone." with a 3 x 3 pattern of numbers), and pages **0, 1, 2** (title and chapter pages) carry a 2,899-byte PGP-signed hex message each, which the research note does not name.
  The hex JPEG inside page 3 decodes to a 587 x 109 pixel image of eleven runes with the digits 5 and 3 (`work/figures/outguess_page03_hex_image.png`); both belong to the 2014 chain.
* **Key-free screen.** The writer puts a 32-bit header at key-chosen positions inside the first ~550 usable coefficients. On a page with a blank top margin these are DC values of white blocks, whose least significant bits are constant, so a header flips about half of them.
  All nine controls show 14-258 deviations among the first 600 bits (constant prefix 9-70 bits). The 56 LP2 pages (17-72) have a constant prefix of 5,747-29,443 bits and no deviation; so do pages 5-9, 14-16, 73 and 74. **No OutGuess-style payload, under any key, in LP2.**
* **Sweep.** Page 4 (art at the top, so the screen cannot judge it): 53,227 solved-text strings (the hashscan lore list in its case variants plus the 20k word list in three cases) give no hit; a payload planted into a clean page by the writer's rules is found by the same
  sweep under the keys "welcome" and "DIVINITY", the unplanted page gives none.
* **Not covered.** Embedders that avoid DC coefficients (F5, AC-only schemes), other containers, keys outside the list on page 4. The payload contents are the 2014 chain, not LP2.

## 4b. Seed lists (running)

`jobs/queues/gpu_rest.txt` waits for the `gpu4h` queue (py3 and java over sections 0.8-0.15) and then runs the other eight generators of `prng-bg` (php, glibc, mt32, msvc, drand48, ruby, mt31, net), about 1.1-1.7 h each on the 2080 Ti. py3 finished with 0 candidates at +300.

## 4c. Number-theory streams, image searches (nothing new to add)

The library already holds phi(n), sigma(n), d(n), mu(n), omega(n), Omega(n), triangular numbers, digits of the usual constants and the hash streams of the solved sentences. The sentence sums of the solved pages are a 76-value sequence, too short for a 12,956-rune text.
Image searches beyond `phase18` and OutGuess: none worth running.

## 2 and 3. chanscreen v2: contract, controls, campaign (controls done, campaign running)

Protocol and amendments: `work/chanscreen/v2/step3/PROTOCOL.md` (written before each run). The user's "try all those 4" was read as adopting follow-up option 1: tier-1 rule S_guard = min(S, S_W) >= T, T300 = 29.799 nats (alpha 0.001, 82 windows, 8.74e9 cells),
wrong-offset counts as a diagnostic. If the user objects, discard the campaign results. Engine reviewed by reading (`backward.rs`, 84 lines: arcs and classes as in the v1 reference); its gates E0 and E1 are the evidence.

* **E3 (as frozen) failed its literal criterion, by my error.** Five v1 calibration records were searched against the full 1,439-stream bank. Records 0 and 100 (iid keys) are nulls: maxima -102.4 and -100.6. Records 50, 150, 175 were encrypted with slices of library streams,
  which the bank contains: for each the campaign's best cell is exactly its own stream (`sha512-ctr mod :1311` 181.8, `sha512-ctr reject :<256 bytes 50bd24b4>` 218.1, `md5-ctr reject :parable` 227.6; hold channel, sign +1): a library-scale positive control, 3 of 3.
  The dense v1 engine re-scores the cell to 1.4e-12 nats and the Viterbi text is readable English (`verify_cell.py`). **E3b**: five more iid-key records (10, 30, 110, 130, 145), same code, gate `e3b_gate.json` (all maxima < T300); running when this was written.
* **E4 (200 library-scale plants, mid-text windows, own stream searched): detection 200 of 200** at 300 runes (50 of 50 per channel, Cicada and Emerson plaintext, Emerson-trained LM); prefixes of the same plants 194 of 200 at 60 runes and 200 of 200 at 80, 100, 150, 200;
  Viterbi accuracy of the winner 0.9906 (198 of 200 at least 0.95). The winner is the true cell (+-3 offsets, same channel) in only 8-21 of 25 per group: aliases in other channels and at other offsets win, the sign is right in 99%.
  The wrong-offset diagnostic (band +-20) is far above N e^-t (269,508 cells >= 10 against 837), because the 94 short keyword / periodic streams repeat at every period and the hold likelihood can re-synchronise by holding the pointer (about -6 nats per hold), so aliases of a strong cell reach about +50 offsets.
  Amendment 2 (`e4_bands.py`) counts them in wider bands; it changes no rule.
* **Campaign (item 3) and clause scan (item 2):** detached queue `jobs/queues/chanscreen.txt` (waits for E3b, runs the gate, then the 82 LP2 windows of 300 runes against the whole library with hold, spend, skip5 and coin, both signs, every offset: about 49 CPU-hours, then the 82 clauses
  of at least 60 runes: about 21). Results will appear as `results/chanscreen/summary_n300.txt` and `summary_clause.txt` (tier 1 = S_guard >= T, candidates not leads; tier 2 = top 50 per channel and window, unverified ranks). Nothing in them has been read yet.
  Power on record: E4 above. A negative excludes a library stream at any offset of these windows under the four channels, q = 0.81 and an English-like plaintext; it does not exclude other streams, other languages, restarts inside a window or other q.

## Wrap-up state (2026-10-19, midday)

Finished: prime-sum checker and rule addendum, OutGuess (own reader, nothing in LP2), E4. Running without me: E3b -> gate -> n300 campaign -> clause scan (CPU), `prng-bg` for ten generators on sections 0.8-0.15 (GPU; py3 done with 0 candidates, java nearly, `gpu_rest` queue for the other eight).
Not done: reading any of those results, committing, the E4 band diagnostic run (`e4_bands.py` written, not run), the registry update of the campaign rows once results exist.

## 5. Outcome (2026-10-20 04:20)

* **n300 campaign** (finished 2026-10-19 22:15, 1,148 of 1,148 tasks): 0 tier-1 cells; 0 cells reach S_guard 0 of 8.74e9 searched; best per channel -75.7 hold, -161.2 spend, -179.5 skip5, -201.4 coin; per-window maximum -107.5 to -75.7 (median -100.5).
* **Clause scan** (finished 2026-10-20 02:15; 5 tasks had raised `invalid log likelihood` and one stored a false 335.1 nats cell, window `0.8c@122+174`, spend, `sha512-ctr reject :welcome`, which the new check rejected: recomputed best -98.1; all six re-run clean at 04:17): 1,148 of 1,148 tasks, 0 tier-1 cells; best 7.5 hold,
  6.8 spend, 5.5 skip5, -2.0 coin; 116 cells above 0, 9 above 5, none above 10 (short windows, English-like LM: expected).
* **Faults:** n300 3 tasks (two errors at about 13:29, one false 98-cell band of 132.6 nats finished 14:29), clause 6 tasks; 9 of 2,296 tasks, one engine call each as far as seen, about 1e-5 per call. Not reproducible in isolation, 4 of 4 re-run tasks bit for bit identical; cause not established. `summary.py` recomputes tier-1 groups.
* **Seed sweeps** (`gpu4h` and `gpu_rest`, finished 2026-10-19 23:55): py3, java, php, glibc, mt32, mt31, msvc, drand48, ruby over 2^32 seeds and net over 2^31, sections 0.8-0.15: 0 candidates at +300 in each.
* Registry rows `chanscreen-step3`, `open-clause-windows`, `open-bg-sections` are now `excluded` with the scope above. Not done: the E4 band diagnostic (`e4_bands.py`), an audit of more finished tasks by re-running them, the GPU sweeps' reliability.
