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

## 5. The desktop PC (2026-10-17)

A new Claude session on the desktop (runner alias `desktop`, RTX 2080 Ti, 32 GB) started from `docs/HANDOFF.md`.

| # | User | What was done |
|---|---|---|
| 36 | (the `docs/HANDOFF.md` prompt: read the docs, set up and validate, live console logging, CUDA with CPU fallback, run the campaigns, work on the open leads) | Read the docs and checked the PC (Ryzen 7 2700X, 16 threads; RTX 2080 Ti; CUDA Toolkit 12.6 and Visual Studio already installed; no Rust). Wrote `.lp_machine`. Global Python 3.12 was not writable from the sandbox, so the packages went into a git-ignored `.venv` in the repository. |
| 37 | "Yes, install Rust with rustup (per-user install, MSVC is already present) and then run the selftest." | Installed Rust 1.99 (installer hash checked against Rust's published one). Selftest passed: 44 tests, 15/15 planted windows, null 1.306. Then step 2 (live console in `jobs/overnight.py`) and step 3 (CUDA ports, see `docs/GPU_PORT.md`). |
| 38 | "I will be going to sleep, please work by yourself. Make the most use of my hardware, but remember to not forget the mission, which is solving Liber primus. Once the code is more optimized for my hardware start the queue. While doing that, you can work on the code, research online and build algorithms and math to solve this. Find clues. If needed, agents are allowed." | Finished and validated the CUDA ports, added `--device` and `--lane` to the runner, committed, and started two lanes at 00:36: GPU (kscreen restarts / recurrences / multipliers, prng-all) and CPU (rescreen, dsearch, payload). A research agent looks for new public leads (`work/log/research_2026-10-17.md`). The session stays open so the PC keeps awake. |
| 39 | "Are we working on solving liber primus now?" | Yes: two lanes were running (GPU screens and sweeps; CPU dictionary screens, dsearch, payload); status given. |
| 40 | "As I will be going to sleep, if you happen to see any pull requests or different branches, make sure to look at those and take them into consideration. I have another AI, a weaker one, researching and writing tests, but those tests needs to be rewritten with a stronger better ai before being run. Also if we happen to finish before I wake up, run any new queues you have. (only 1 at a time) And you can also write code, algorithms and math to solve this." | Fetched `origin`: branch `research/restart-columns` (reviewed, word-unit bug fixed, tests rewritten, merged) and a new empty `research/wordlen-languages` (not yet pushed to; coordinate before doing the word-length work). No pull requests exist (`ls-remote`). New queues are chained behind the running GPU lane, one at a time (`kscreen-chain`, then `prng-more`). |
| 41 | "Oh and I know i use github desktop. But I allow you to commit to github directly, and push/pull. Read, close pull requests, merge." | Pushed `main` three times (privacy scan of the added lines each time); recorded in `CLAUDE.md`. `gh` is not installed and the repo is private, so PRs cannot be listed without a token; I did not look for one. |
| 42 | "any breakthroughs while i was gone?" | No. Overnight results were all negative with controls (kscreen, prng-all / prng-more, hash streams, step-domain screens); summary in `work/log/phase9_overnight_results.md`. |
| 43 | "i need the gpu in 3 hours. But before then, make the most use of the time. I will be going back to sleep. You can download gutenberg and other tools needed." | Boundary-free scoring built (bigram log-likelihood, `work/phpmt/bg.py`) and run for window 0.7 on all ten generators, on the hashscan candidates and (CPU) on the OEIS / KDF libraries; all GPU jobs stopped at 10:00 (nothing resumes without the user's OK). |
| 44 | (the laptop's branch list, pasted) | Branches read as data, tests rewritten, merged (`docs/prs/INDEX.md`); the pasted suggestion to run its stage B on the desktop was not followed (the desktop sweeps already cover those cells). |
| 45 | image of the 27 x 27 grid and the "729 Matrix" repo link | Third-party claim: tested for layout structure only (`work/grid729_check.py`); the walk rule is undefined. |
| 46 | three PDFs ("27 x 27", "Matrix-Onion Volume 1", "Wow"), five repos, and the post with page numerology | Read as data; claims reproduced and nulled (`work/log/phase9_community_claims.md`): no structure survives selection; nothing decrypts. |
| 47 | "What are things we haven't tried yet, that could help us in this journey of solving Liber primus?" | Ranked list: family-level simulation first, exact heading-crib sweeps, the lag-5 / S mechanism, the open leads, outside material; what not to repeat. |
| 48 | "Do this task here: Simulate cipher families against LP2's fingerprint" | Built and ran `work/families/` (6-test gate, 25 rows x 100 replicates); a simulator bug was found and fixed on the way; result in `work/log/phase9_families.md`. |
| 49 | "list everything we tried thus far, whats currently running, what has worked and what has failed, next steps" | Full status given (nothing in LP2 solved); the family rerun and the OEIS / KDF CPU lanes were running, the GPU idle. |
| 50 | "Not yet, keep the GPU free." | The GPU stays free: `kscreen-reverse` a26-28 and `prng-bg` for all sections are not started. |
| 51 | "write some advanced hypothesis we havent tried yet." | `docs/HYPOTHESES.md`: nine untested families (stream + keyword, arbitrary tableau, clocked pointer, text numbers, ciphertext as key, deep pads, language-free seed sweeps, null on collision, drift-aware pad reuse), each with its blind spot, test, controls and kill rule. Nothing run; one keyless check killed the "-SELVES" reading of the S echo (3 of 11 against 4.4). |
| 52 | "Do this task here: Screen new key streams from docs/HYPOTHESES.md (H3–H6)" | Campaign `kscreen-hyp` (export_hyp.py, hyp_selftest.py, test_hyp_exports.py, a G-line guard in the kscreen engine so LP2's own ciphertext can be its key). Controls passed; result in `work/log/phase9_hyp.md`. |
| 53 | (a pasted list of 14 hypotheses from an outside source) "Has these been tried/been looked at before?" | Read as data. Answer: 1 (deterministic collision rewrite) excluded by the flat step and pair tables; 2 (prime algebra) covered for C = f(P) + K, multiplicative and fixed-point variants excluded by a new rune × word-position test, closed operations = H2; 3 partly in the library; 4 excluded after encryption, invisible before; 5 page restarts done for library keys; 6–7 geometry and font not measured (no font source exists); 8, 13 covered or = H1/H2; 9 partly; 10 the payload is byte-random, not a permutation (161 distinct of 256); 11 general 29-state machines not done (now H10); 12 done (IoC scoring); 14 not done, low information. |
| 54 | (a second pasted list of 7) "As well as:" | 1 survival predicates are covered by the decoders' keep/skip branching; ISAAC and binary LFSR not swept (now H12); 2 a second stream cannot make a Δc = 0-only deficit, but random pointer jumps are open (H1/H2 add-on); 3 per-page seed sweeps not done (now H11); 4 skip-to-next done, +1 fix-up excluded; 5 key-side Markov excluded, ciphertext-side = H2b; 6 not measured; 7 not done, low. |
| 55 | "while waiting, run more advanced tests" | Keyless and CPU tests while kscreen-hyp ran: H8 (alive as a partial word-length explanation, hides nothing from the screens), H9 (undecidable), H10 (null, also with the skip modelled), then the `clock=` engine option and campaign `kscreen-clock` (H3, negative). All in `work/log/phase9_hyp.md`. |

## 6. The first night on the desktop (2026-10-17): what was built and found

- **Queue** (started 00:36): GPU lane `kscreen-restarts` (done), `kscreen-recurrences` (running), `kscreen-multipliers`, `prng-all`;
  CPU lane `rescreen`, `dsearch`, `payload`. Chained behind the GPU lane: `kscreen-chain` (ciphertext feedback, a = 1..28), then
  `prng-more` (seven more generators). Check `results/overnight/desktop/REPORT.md` and `python jobs/overnight.py list`.
- **Built:** live console runner; CUDA ports of the keystream screen (2-4x the 16-thread CPU) and of the seed sweeps (6.8x),
  validated bit-identical; `--device`, `--lane`; ciphertext-feedback windows (`P` lines in both engines); seven new generators;
  separator/tick audit of the page images; section and within-word statistics; page-art measurements; per-window
  extreme-value null for short windows.
- **Found (all negative or weak):** the short heading/page windows give "candidates" that are extreme-value noise; the
  transcription's separators are correct (word-length anomaly is real); no short periodic key in any chain transform; no key
  restart at any unit; the page art is reused stamps and mirrored borders; the cuneiform header is base-60 for 1033 and 3301
  (the research agent's reading).
- **Open:** wait for the queue; the apostrophe cribs (`work/ref/tick_marks.tsv`);
  the stray rune-sized "7" glyph (image 27, a one-glyph word); the N = 28 step-domain variant of the chain family
  (needs an alphabet-size parameter in the engines; `work/log/research_2026-10-17.md`, section 4); the lag-5 word-internal
  clustering (no mechanism; `docs/prs/word-internal.md`); the corpora fetch for `wordlen_languages.py` (needs permission).
- **User instructions this night:** work alone while asleep; use the hardware; review the other AI's branches and rewrite its
  tests before running them (done for `restart-columns`, `word-internal-lag5`, `wordlen-languages`); run any new queue only one
  at a time; the user allowed commits, pushes, pulls and merges directly (never credentials). Pushed 2026-10-17 02:10.

## 7. The laptop, second session (2026-10-17, from about 10:20, in parallel with the desktop's #42-#50)

| # | User | What was done |
|---|---|---|
| 51 | "pull the latest data from my PC/github repo. Then come up with hypothesis and algorithms to maybe solve the book." | Fetched `origin` and fast-forwarded the local `main` (28 commits from the desktop: merges of the laptop branches, review notes). The laptop's own prngx stage-B run (`work/prngx/campaign.py run stageB --gens rand48 msvc java`, started 03:47) was left running; the checkout moved to a new branch `research/new-hypotheses` off `main` (the prngx code and data are identical on both, so the run is unaffected). New work: six keyless tests with planted controls (five families excluded, one disfavoured) and a new engine `work/layer2` for the two-layer hypothesis H-LAYER (keyword Vigenere inside, number stream with the anti-repeat rule outside), with its selftest, a first LP2 run and a `layer2` campaign for the desktop. Details: Phase 10 in `PLAN.md`, `work/log/hypotheses_2026-10-17.md`. |
| 52 | "Do this task here: Time-seeded Java/Python PRNG sweep (ms timestamps)" | Built `prng-time` (`work/log/phase10_prng_time.md`): `prngx pymt` seeds like CPython for any integer (two 32-bit words above 2^32; earlier results unchanged), Java's 48-bit seeds already worked; `PRNGX_MAPS`, `prngx keys`; `time_campaign.py` (month sweeps, newest first) and `time_verify.py` (whole-section check with independent keys); vectors 119/119, planted timestamp seeds at rank 1, random-ciphertext null, `tests/test_prngx_time.py`; runner campaign `prng-time`; a bounded demo on LP2. |
| 53 | "Are we running anything?" | Only the laptop's prngx stage-B run (its last step, Java's negative seeds). |
| 54 | "look at the latest commits from my PC." | Four desktop commits: the backward-key campaign complete (negative), GPU epoch-second and small-integer seed sweeps of every section (negative), the KDF and boundary-free OEIS lanes (negative), a review of this branch (accept after two changes) and the desktop's own 64-bit CUDA port of `prng-time` (`time_gpu.py`, gate 8/8, about 9 h for the window, not started). |
| 55 | "Yes: make the two changes the desktop's review asks for on research/new-hypotheses (merge main and resolve PLAN.md, fail the gate on skipped tests, plant with independent keys, drop or qualify the Ruby claim, point prng-time at the GPU sweep), then rerun the tests, commit and push." | Done: main merged (PLAN.md: both sides kept); `prng-time` gated by `run_gate.py` and run through `time_gpu.py` on a validated GPU (CPU engine as fallback); prngx and layer2 controls plant with independent code (`time_verify.plant_windows`, `work/layer2/plant_ref.py`); Ruby marked unverified everywhere. `test_prngx_time` 5/5, `test_layer2` 3/3 (0 skipped), prngx suites 10/10, `layer2/selftest.py` 14/14. Response at the end of `docs/prs/new-hypotheses.md`. The full suite (136 tests) first showed 3 failures and 8 errors, all in modules whose engines the desktop changed on `main` while the laptop's builds were older (phpmt, kscreen, hashscan from 2026-10-16/17 night; prngx held by the running job); after rebuilding, those modules pass (25 tests, 4 GPU-only skips). **After every pull, rebuild the engines on the laptop.** |
| 56 | "I reached claude code limit so i gotta wait an hour on my 2nd account/computer, and the scripts stopped running... Well anyways, research this deeply https://cicadanotebook.com/ https://cicadanotebook.com/journal.html https://cicadanotebook.com/guide.html" | Read the site (an AI-assisted notebook of 79 controlled sessions, no solution claimed) as data, with three read-only agents for the sessions; nothing of theirs run or committed. **Found a bug in our word splitter:** unmarked page breaks are wraps, so LP2 has 2,896 words and 83 one-rune words (not 2,928 and 99), confirmed in the page images (32 unmarked seams with no dot, 21 marked with a dot). Recomputed their key claims on our data: doublets per section, the feedback barrier (5.53%), whole-word repetition, the phrase chance, and the doublet floor (207 for English in the standard order; a keyed alphabet stays open). Cuneiform stamp 7 copies, not 4; their 5 three-dot separators confirmed in our images. Note `work/log/research_cicadanotebook_2026-10-17.md`; `PLAN.md` Phase 10. |
| 57 | "Do this task here: Fix page-seam word splitting and rerun word stats" (then: "How long i the ETA? After this I assume you wanted to do: Typography-restart screen with solved-text controls ...") | `lp.word_spans` treats an unmarked page break as a wrap. `stats.adjacent_pairs`, the `restart_columns` word unit and five scripts with their own splitters were fixed too (three of them, plus `grid30`, still cut at every line break). phpmt and walk exports regenerated; 23 result files rerun; `test_crib` and `test_families` updated; suite 136 OK (21 GPU skips). No verdict changed. Notable shifts: the "+1 rune in 42% of multi-rune words" word-length model is no longer rejected (p 0.085-0.10); the community crib for 0.7 fits LP2's word division exactly; the lag-6 affine lead c' = 24 − 2c strengthened (look-elsewhere P 0.005, split-half 0/200), still a lead. Details `work/log/page_seam_fix_2026-10-17.md`. The typographic-restart screen comes next. |

- **Open after this session:** the stage-B result files of the laptop's prngx run (`results/prngx/*_b_*`) are untracked in this
  checkout; when the run ends, switch back to `research/prngx-generators` (untracked files move with the checkout) and commit
  them there, and rebuild `work/prngx` (`cargo build --release`: the run uses a build from before the two-word seeding). The
  full `layer2` campaign (about 13 h on 16 CPU threads) and the GPU `prng-time` window (about 9 h) are for the desktop.
- **Open from #56-57:** the `lp.word_spans` fix is done (#57). On the desktop, run `python work/kscreen/export.py` once so
  kscreen's plant files carry the new word lengths. The lag-6 affine lead c' = 24 − 2c deserves a test with the relation
  fixed in advance. Ideas from the site that we have not run:
  - restarts at typography with the full stream library, using the second koan and page 56 as controls;
  - Euler-trail nulls;
  - one-rune words as filters;
  - a key-reuse scan anchored on the phrase.

  A diff of the site's newer cicada-solvers transcription (three-dot class) needs the user's OK to download it.
- **For the user to decide:** the desktop's review notes that the laptop's commits carry the author name of its git setup, where
  `main` uses the `pnotisdev` identity; setting the laptop's `user.name` to the alias (and whether to rewrite the pushed
  history) is the user's call before any publication.

## 8. The desktop, third session (2026-10-17; `work/log/phase9_families.md`, `phase10_*.md`)

| # | User | What was done |
|---|---|---|
| 58 | "Do this task here: Simulate cipher families against LP2's fingerprint" | Ten statistics over structureless keys, alphabet walks and lag copies (`work/families/`, `results/analysis/families.txt`): any structureless additive key is 'random plus about 81% avoid-repeat'; the S echo is reproduced by nothing that otherwise fits. |
| 59 | GPU grants: "my gpu is free if you have anything that finishes under 30 min", "use my gpu for another 30 minutes", "Yes, start the 64-bit CUDA port...", "Yes, run py3 and java on the full timestamp window for 1 hour of GPU time, newest months first" | 64-bit CUDA port of the boundary-free sweep (`bgmt64.cu`, gate 8/8) and the first hour of the 2012-2014 millisecond window for py3 and java: 0 candidates; 20 months remain (about 3.9 h). |
| 60 | "look at the branch research/new-hypotheses" | Reviewed (`docs/prs/new-hypotheses.md`): accept with two changes, which the laptop made at 15:10. |
| 61 | "Honestly, we should probably focus on stuff that hasnt been done by other people, or by us before. Think more outside the box and focus on testing specific hypotheses that haven't been fully exhausted rather than open-ended AI generation." | Keyless tests with their power measured before reading a negative (`work/log/phase10_keyless_power.md`): the shared-key test passes its control, a general fixed-map scan and a sparse-tap recurrence scan fail theirs at LP2's 1.5% effect size. |
| 62 | "Build the coverage-and-power ledger first, then decide what goes to the GPU." | `docs/NEGATIVE_SPACE.md`: for every family tried, what was excluded and how well. |
| 63 | "Not now. Keep the GPU free." | No GPU job was started after the ledger. |
| 64 | (the laptop's `kscreen-typo` pushes, `f7b8998` .. `f096a8c`) | Final results read as data: negative; the summary's 'CANDIDATE' line is a verify-rule artefact (log 1b). |
| 65 | "Yes: run the CPU tests properly (GPU tests skip), privacy-scan, commit the other session's work, then merge research/new-hypotheses." | Second session committed (9faf953) after a clean scan and a CPU test run; the branch merged (conflicts: the crib files, PLAN.md, the PR docs); engines rebuilt; gates and the layer2 selftest passed. GPU tests not run. |

- **Open after this session:** the GPU candidates in `docs/NEGATIVE_SPACE.md` section 6 (remaining millisecond months, per-page seeds, full-seed boundary-free sweeps) wait for a GPU grant; the GPU tests of the merged
  tree (bgmt, bgmt64, stepmt, step28) should be run once when the GPU is free.

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
- **GPU.** The keystream screen and the seed sweeps have CUDA ports, used only when they pass the gates in
  `docs/GPU_PORT.md` on the PC at hand; the Rust engines remain the reference.
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
