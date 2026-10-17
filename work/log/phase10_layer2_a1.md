# layer2 variant A1 ('combined'): a solved key folded into the stream (2026-10-17, 20:30)

Scope: LP2 sections 0.7-0.15, first 300 runes of each. **Nothing in LP2 is solved.** The slice of the laptop's `layer2` campaign that the runner lists as `layer2/combined` (CPU, estimated 0.6 h): the 20 core streams
of `work/layer2/data/combined.ksb`, each with DIVINITY / FIRFUMFERENFE / CIRCUMFERENCE folded in (one pointer for both, every phase and both signs), screened as a single layer with the English rune-bigram score
(`kw=data/keyword_none.txt litf=0 isigns=1`, both mults, both models, the skip rule in the beam).

Run directly with the runner's command on 12 threads while the GPU swept: 1,159,951,616 decodes in 201 s (5.8 M decodes/s; the runner's estimate of 0.6 h was far too high), `results/layer2/bigram_combined.tsv`.
**Best -5.63 per rune** (a true key about +7, the best of about 10^8 random decodes about -5, the rule +2.0); the top 15 re-decoded over the whole window by `verify.py`: **0 of 15 pass**, every one noise (whole window
-9.0 to -9.7 per rune, matched null max -9.7 to -10.1; `results/layer2/bigram_combined_verify.txt`).

**Control.** `selftest.py` has no plant for this slice (its plants use keyword lists). `work/layer2/combined_control.py` plants English windows with four combined streams under the skip / coin rule with the independent
planter (`plant_ref.py`, keyword [0]) and screens them with exactly the A1 options: **12 of 12 windows recovered at the true offset, +7.2 to +8.3 per rune** (whole window at the truth +7.3 to +8.1, matched null max
-8.8 to -10.2), `results/layer2/combined_control.txt`. The negative is therefore a real negative for the 20 streams with a solved key folded in, at 300 runes.

Not covered: other keywords folded in, the library beyond these 20 streams, windows after the first 300 runes of each section.
