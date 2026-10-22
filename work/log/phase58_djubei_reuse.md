# Phase 58: DJU BEI as reused key

## Plan (written before the run)
1. Locate both DJU BEI copies, their distance, and any section / page break between them.
2. For every stream of `work/kscreen/data/library.ksb`, count pairs (i, j), j - i in 5,700-6,500, with equal 6-runs (and 5-runs). Null: 100 shuffles per stream, plus the iid expectation 29^-m per pair. Equal runs are invariant under key sign and every multiplier, so one scan covers all 28 x 2 variants. Positive control: a 6-run planted at distance 6,100 must be found.
3. For streams with excess or a repeat consistent with the copies, decode LP2 at the implied offset (copy 1 at the first run, both signs) and look at the IoC around copy 1. verify.py only if something reaches 1.40.
4. State what equal plaintext at the copies demands of an additive key.

## Result (`results/analysis/phase58_djubei_reuse.txt`, script `work/phase58_djubei_reuse.py`)
- Copies: words in segment 13 (flat rune 6,555, 28 runes into the section) and the last two words of segment 15 (flat 12,950); distance 6,395 runes; one section (0.14) and 29 page breaks between whole segments 13-15. No restart marker identified beyond the section change.
- Controls: planted 6-run at distance 6,100 found; 300 iid streams of 20,000 average 0.013 pairs (expected 0.019).
- Library (1,439 streams): 6-pairs real 279,213 vs shuffle mean 29,340 and iid expectation 11; 31 streams exceed their shuffle maximum, all structured number families (pi(n), composites, mu, omega, rad, d(n), prime gaps, primes and affine transforms of primes, digit sums). They are low-entropy or arithmetic regularities, not specific to distance 6,395. Four streams (composites, primes popcount, mu, pi(n)) have a pair at exactly 6,395.
- Decode screen (686 candidate offsets, both signs): best 306-rune window IoC 1.088 (random windows 1.05-1.35; threshold 1.40). verify.py not run: nothing reached the threshold.
- Constraint: equal ciphertext at both copies means equal plaintext iff k[a..a+5] = k[b..b+5] at the key positions (b - a = 6,395 plus extra key steps). Any screen's reported key and offset must satisfy this; a periodic family needs its period to divide b - a.

Verdict: no library stream explains DJU BEI as reused key; the test is partial (an additive key from outside the library, or one with a skip model that shifts the repeat outside 5,700-6,500, is untouched).
