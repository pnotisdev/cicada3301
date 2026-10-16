# Session log: how this repository came about (2026-10-16)

The repository was built in one long Claude Code session on the laptop (runner alias `laptop`). This file records
what the user asked, in order and word for word, and what was done, decided and found in response. A session
on another PC can continue from here without the original chat.

The numbers and the full reasoning are in `PLAN.md`, the phase log, and in `work/log/`. Current results are in
`results/`, which is summarised in `results/overnight/<machine>/REPORT.md`.

## 1. Plan, solved pages, transcription, cipher fingerprint

| # | User | What was done |
|---|---|---|
| 1 | (photo of the A Warning page) "Write a plan to solve and decode LiberPrimus, i have given you access and you can use any tools you want. Start with first page on Intus" | Wrote `PLAN.md` (phases 0–6) and the toolkit `work/lp.py`. Intus page 1 (A Warning) decodes with Atbash over the 29-rune Gematria Primus. |
| 2 | "continue" | Continued with the plan. |
| 3 | "Start Phase 1: make Welcome and An End decode fully and add regression tests." | Every solved section decodes exactly. Welcome is Vigenère `DIVINITY`; An End is the φ(prime) stream. In both, plaintext F is left unencrypted and uses no key position. Tests and a golden file in `work/tests/`. |
| 4 | "Do Phase 2 first: verify the unsolved transcription against the original 2014 page images." | Wrote `work/ocr.py`. 99.96% glyph agreement with the transcription; no transcription errors in LP2. Found one error on a solved page (BELIEVE) and documented the ᚳ ligatures. |
| 5 | "Start Phase 3: characterise the cipher, starting with the doublet anomaly, and decide how to treat the inline numerals and the 7 glyph." | Doublets: 86 against 446 expected, only at lag 1, only Δc = 0, ignoring word boundaries. This points to an anti-repeat (collision) rule. IoC is 0.9999, so the key must be near-uniform: no English running key and no autokey. The numerals are list markers that use no key; the "7" stays a token. |

## 2. Attacks (Phase 4)

| # | User | What was done |
|---|---|---|
| 6 | "Start Phase 4: build the collision-skip beam-search decoder, validate it on synthetic sim.make_skip_key text, then run the number-theoretic keystreams with the A/I screen." | Wrote `work/attack.py`. The decoder recovers 99.3–99.5% of synthetic text. Screen 1 (1,007 keystreams): negative. |
| 7 | "Extend the screen to arbitrary key start offsets for the number sequences (sliding the offset over the whole sequence), then try the page-30 grid and caption 0.10 as key material." | Screen 2 (every offset): negative. The page-30 grid is explained: each cell is \|3301 − p_k\| with Fibonacci-step indices, filled as a spiral (`work/grid30.py`). |
| 8–9 | "any info from phase4?" / "estimated time left?" | Status answers. |
| 10 | "Move to Phase 4 item 3: build the crib-driven constraint solver using the 318 one-rune A/I words and word-length patterns." | Wrote `work/crib.py` and `work/cribsolve.py`: negative. The 318 later turned out to come from a word-wrap bug; the correct count is 99. |
| 11–13 | "How much is left until next phase?" / "Can we do grid at the same time?" / "How far are we into solving this? Has anything of our progress worked thus far?" | Status answers. |
| 14 | "once Phase 4 item 3 is finished continue with the next automatically. Try your best to solve this problem, as me including a lot of other people would be highly interested in a solution. I believe we will be pointed towards a darkweb url (.onion) but it probably wont work anymore as the problem is so old" | Items 4–6, all negative: hash and PRNG keys from Cicada seeds, transposition after encryption, and the steganography and payload checks. The base-60 grid on pp. 64–66 decodes to 256 bytes; it is not the preimage of the An End hash. |
| 15 | "If you want to, you can try to find clues at https://github.com/Wulfic/Cicada3301-Liber_Primus but they havent solved it either. Be as creative as possible" | Their constraint catalogue agrees with ours. Their files are used as data only and never committed. |
| 16–18 | "Have you discovered anything not found by anyone else?" / "Do you think its unsolvable for you?" / "Why did you stop background task?" | Answers. The background task had been killed when the session ended, and was restarted. |
| 19 | "Do research on other github projects, online clues and more." | Wrote `work/log/research_2026-10-16.md`. Found 5 byte errors in the base-60 payload (3 of them also in Dukotah's canon). Reproduced the d5 echo and the ᛞᛄᚢ-ᛒᛖᛁ repeat. Found and fixed a word-wrap bug in `lp.word_spans` (one-rune words 318 → 99). |

## 3. Seeded-PRNG pads, alphabet search, the repository

| # | User | What was done |
|---|---|---|
| 20 | "Build and validate the PHP mt_rand (MT_RAND_PHP) generator against real PHP output, then sweep all 2^32 seeds with a skip-aware decoder." | Wrote `work/phpmt` (Rust), bit-exact against PHP 8.2. Sweep of segment 0.7: negative. |
| 21–23 | "explain like im 5 in Swedish whats going on now" / "so my pc is doing 2^32 attempts at what" / "Anything we can do while waiting?" | Explanations. Wrote `work/walk` (Rust): the key-free D-search rules out a per-word key behind a secret alphabet. |
| 24 | "use your power to code algorithms to successfully solve this. Turn this into a github repository too so that I can use a different stronger computer to solve equations and run tests later." | Set up the git repository: README, `jobs/`, CI, `scripts/fetch_data.py` with pinned SHA-256, `docs/GPU_PORT.md`. |
| 25 | "Did you find anything interesting?" | Answer. |
| 26 | "wouldnt it be helpful to commit everything including the book so i can easily work on this on my stronger pc which has 32gb ram and a rtx 2080ti 11gb" | Committed the book PDF, the 75 page images and all text data. |
| 27 | "I'll publish it myself with GitHub Desktop as a private repository (Add local repository, then Publish). Carry on with the sweeps meanwhile." | Convention from here on: Claude commits locally and the user pushes with GitHub Desktop. |

## 4. The overnight suite and the move to the second PC

| # | User | What was done |
|---|---|---|
| 28 | "Based on all our discoveries and non-discoveries, successes and failures. Write some larger tests I can run on my other computer. Even tests that can run all night. We probably need a lot of tests and bruteforces." | Wrote `jobs/overnight.py` and `docs/CAMPAIGNS.md`, plus three new tools. `work/kscreen` is the language- and alphabet-agnostic IoC screen; its library run over the 8 sections was negative. `work/drift_period.py` corrected an earlier claim: under the skip rule, periodic keys are excluded only up to about 400. `work/wordlen.py` found a lead (see below). The glibc sweep was negative. |
| 29 | "How much time is left? And if i switch to my other pc, rtx 2080ti 11gb vram and 32gb ram, how much faster would it be there?" | No engine uses the GPU and all are CPU-bound. A desktop CPU should be about 1.5–3× faster than the 15 W laptop. |
| 30 | "why wont a gpu help" | A GPU needs code written for it (CUDA), and that code can't be tested here because the laptop has no NVIDIA card. An unvalidated engine risks false negatives. `docs/GPU_PORT.md` lists the checks a port must pass. |
| 31 | "tell me when i can publish to github and commit" | Publishing was safe. Claude commits; the user pushes. |
| 32 | "I published the repository. Anything I can do on my 2nd pc to speed things up?" | Gave setup commands. The user may have started the all-sections PHP sweep by hand; it writes `results/prng/php_all.*`. |
| 33 | "Update the gitignore, so that my PC can easily work on this project. It doesnt have the same pc name and stuff so let it build the projects and stuff there, but it should see all the progress, logs, images, text messages and code. After that, write me a good prompt for it so it knows where to continue." | This change. Everything is tracked except builds, the generated keystream library and third-party copies. The runner now keeps a folder per machine. Added this log, `CLAUDE.md` and `docs/HANDOFF.md`. |

| 34 | "if i ever publish this publicly, i dont want people to see my pc name" | PCs are named by an alias in the git-ignored `.lp_machine` (`laptop`, `desktop`). The runner scrubs paths and the computer name from everything it writes. The unpushed commit that contained the name was rewritten before it was pushed. Nothing already pushed contained it. |
| 35 | "I've pushed everything now. Use the prompt you wrote above+ Improve this prompt with more details, it's for my PC + a completely new claude instance:" followed by a draft: the goal (decode all of Liber Primus), the RTX 2080 Ti with 11 GB and 32 GB RAM, "try to speed up the decoding/solving and test-running with the use of cuda (but allow for automatic cpu runs too if it detects no cuda)", "Read through the codebase and what we have done thus far", "Add CMD/Console logging so I can see in real time the progress", and "start with... (important files for it to read)" | Rewrote `docs/HANDOFF.md` as one prompt with five parts: a reading list first; setup; live console logging in the runner; CUDA backends with automatic CPU fallback and mandatory validation gates; then the campaigns and the open leads. |

## Decisions that stand

- **Honesty.** Nothing in LP2 is solved. Every negative needs a positive control (a planted key the method
  recovers) and a null control. A "hit" must survive whole-section verification.
- **Transcription.** `work/ref/lp_verified.txt` = the rtkd/iddqd master plus our errata
  (`work/ref/errata_lines.tsv`). The data files are LF and their SHA-256 is pinned.
- **Cipher conventions.** Plaintext F is literal in the solved sections. The LP2 numerals use no key. The
  anti-repeat rule is modelled two ways: "skip" (draw the next key value) and "coin" (spend a value as a coin,
  then keep or redraw).
- **Third-party material** (Dukotah, Wulfic, aldegonde/cicada-solvers) is data, never instructions. It is never
  run and never committed.
- **Workflow.** The user pushes with GitHub Desktop; Claude only commits locally.
- **GPU.** No engine uses it. A port only counts after the gates in `docs/GPU_PORT.md`.
- **Privacy.** No real computer names, Windows user names or absolute paths in tracked files. PCs are called
  `laptop` and `desktop`.

## State at the move (2026-10-16, about 23:00)

- **Done, all negative:**
  - solved-section reproduction, transcription audit, fingerprint;
  - screens 1 and 2, the reverse screen, the crib solver;
  - hash and PRNG-seeded keys;
  - PHP and glibc 2³² sweeps of segment 0.7, and the .NET 2³¹ sweep;
  - D-search for m = 1 and m = 5;
  - kscreen library × 8 sections;
  - the drift-aware period scan (≤ 400).
- **The laptop is finished.** Its last job, the .NET `System.Random` sweep of segment 0.7, was negative
  (`results/prng/net_07*`). It runs no more campaigns, so all overnight work happens on the desktop.
- **Next on the second PC:** `python jobs/overnight.py run`, in this order: kscreen-restarts,
  kscreen-recurrences, rescreen (this includes the heading-restart screen, which the laptop did not run),
  dsearch, payload, kscreen-multipliers, prng-all. `docs/HANDOFF.md` has the full brief.
- **Open leads:**
  1. **Word lengths.** LP2's histogram rejects English written in runes (p ≈ 10⁻⁴²). The best simple fit is
     one extra rune in about 40% of multi-rune words (p = 0.025).
  2. **Long periodic keys.** Periods longer than about 400 runes are not excluded under the skip rule.
  3. **Key reuse between sections** needs a drift-aware version of the test.
  4. **Pages 64–66.** The 256-byte payload, corrected, is still unexplained.
