# Proposal gates: small runnable tests for the merged campaign plan

This folder holds one test per proposed campaign family, each a **gate**: it plants a key of
the family, shows the method recovers it at rank 1, and nulls it against random settings under
identical code paths. Nothing here attacks LP2 directly; LP2 numbers, where printed, are
informational consistency checks only. **Nothing in LP2 is solved.**

## Structure

```
proposals/
  common.py          shared helpers (rune conversion, anti-repeat encryptor, skip-aware beam, IoC)
  sign_rules/        [2]+my enumeration   +/- sign of the key per word from word-level numbers (112 rules)
  word_anchors/      [2]                  per-word anchor schedules into a key stream (16 schedules)
  h2_coincidence/    [13]                 tableau-invariant coincidence statistic (H2 screen gate)
  outer_alphabet/    [3],[25]             keyword-mixed outer alphabet: blindness + recovery gate
  null_beam/         [0],[7],[23]         unkeyed per-word null runes: null-aware vs null-blind beam
  section_depth/     [1],[10],[15]        shared pad at section starts: power of the difference statistic
```

Each folder contains:

- `README.md` — hypothesis (with the lore citation), what the test does, the controls,
  the verdict rule, and what a pass/fail means for the full campaign.
- `run.py` — the test itself (standard library + the repo's own `work/lp.py` only).
- `run.bat` — Windows run script (sets `PYTHONIOENCODING=utf-8`, runs `run.py`).

## How to run

From the repository root (or any folder):

```
python work/proposals/sign_rules/run.py          # one test
work\proposals\run_all.bat                       # all tests, Windows
```

Use the repository Python (`.venv\Scripts\python.exe` on Windows) if the global one cannot
import `work/lp.py`. Every test finishes in seconds to minutes and prints a verdict; exit
code 0 = gate passed, 1 = failed.

## How to review

1. Read the folder's `README.md` first — the hypothesis and the verdict rule are stated there.
2. Check `run.py` plants the key **independently of the recovery code** (the plant uses the
   plain encryptor, the recovery uses the decoder) — a gate that shares code between plant and
   check proves nothing.
3. Check the null: random settings must run through the *same* code path and fail.
4. Check the numbers printed: planted IoC should be >= 1.5 (English runes), nulls around 1.0.
5. If a gate passes, the corresponding full campaign (library stream, GPU cost) is worth
   building; the gate alone says nothing about LP2.

## Correspondence to the merged plan (2026-10-17 review)

| Gate | Merged plan item | Full campaign cost (2080 Ti) |
|---|---|---|
| sign_rules | Word-pointer/sign family (my 112 rules + [2]) | ~22 h (fast slice ~3 h) |
| word_anchors | [2] per-word anchor schedules | included above |
| h2_coincidence | [13] tableau-invariant screen | 2-4 h library lane |
| outer_alphabet | [3]+[25] keyed alphabet tiers | Tier 1 ~14 h |
| null_beam | [0],[7],[23],[29] unkeyed nulls | window 0.7 first (~2.4 h/generator) |
| section_depth | [1],[10],[15],[21],[26] reuse family | stage 1 < 1 h (needs the rune LM later) |

The one common dependency the gates deliberately do **not** use (to stay self-contained) is the
rune language model; `section_depth` documents why it will be needed (skip drift destroys the
unigram statistic over a full section).
