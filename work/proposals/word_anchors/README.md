# word_anchors — per-word anchor schedules into a key stream

**Hypothesis.** "their numbers are the direction" read as a *pointer*: each word's key run
starts at a position computed from the word's number (word index, Gematria sum, a sacred
multiple), then runs contiguously through the word; the next word jumps to a new anchor.
This is merged-plan item [2]. Any per-word schedule makes all key relations word-internal,
which is the one structural property the two fingerprint leads actually show.

**Schedules (16, stated in advance).** anchor(w, L) with L = stream length:

| # | anchor | direction |
|---|---|---|
| 1-2 | w mod L | fwd / back |
| 3-4 | G_w mod L (Gematria sum) | fwd / back |
| 5-6 | (3301*w) mod L | fwd / back |
| 7-8 | (w*w) mod L | fwd / back |
| 9-10 | (1033*w + 3301) mod L | fwd / back |
| 11-12 | G_w * w mod L | fwd / back |
| 13-14 | G_w + w mod L | fwd / back |
| 15-16 | (G_w * 3301) mod L | fwd / back |

Within a word the key runs contiguously from the anchor: key[anchor], key[anchor+1], ...
("back": key[anchor], key[anchor-1], ... cycled).

**What this gate does.**

1. Plants a text with one randomly chosen schedule over a totient stream, anti-repeat skip.
2. Builds the per-position key array for every schedule and decodes: the planted schedule
   must rank #1 by IoC (>= 1.5), and the contiguous-pointer decode (schedule "none") must
   fail (blindness).
3. Null: random anchors per word — must stay below 1.5.
4. Informational: nothing on LP2 (the real screen needs the library streams; this gate
   only establishes that the schedule space is searchable).

**Verdict.** PASS if blind IoC < 1.3, planted schedule ranks #1 with IoC >= 1.5, null < 1.5.
A pass means the 412-variant GPU screen ([2], ~22 h) is a valid build; a fail means the gate
is broken and the campaign must not run.

**Cost.** seconds on CPU (16 schedules x one short decode each).
