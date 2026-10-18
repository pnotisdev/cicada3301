# h2_coincidence — tableau- and key-map-invariant statistic (the H2 screen gate)

**Hypothesis.** The cipher is a tableau driven by a known stream: c_i = T[k_i](p_i), where T
is any set of 29 permutations (keyed alphabets, Quagmire, an unknown value-to-rune map, a
program's own output mapping). Every additive screen assumes T[k](p) = p + k in Gematria
order, so all of them are blind to this family. This is merged-plan item [13] (H2).

**The statistic (invariant to T).** Count pairs i < i' with **equal raw key value and equal
cipher rune**: k_i = k_i' and c_i = c_i'. Equal key value and equal cipher rune force equal
plaintext, so the count rises from its null by about the plaintext's own coincidence excess
over the true stream/offset, for *any* tableau. No alphabet, no map, no addition is assumed.

**What this gate does.**

1. Plants a text through a random tableau driven by the totient stream (no anti-repeat
   rule — the statistic is defined on aligned pairs; the full campaign adds the drift beam).
2. Computes the coincidence count at the true offset and at 20 random offsets of the same
   stream, plus on shuffled ciphertext at the true offset. True must beat the nulls by
   z >= 5 (the full-window excess is about 30 sigma at 1,600 runes).
3. Blindness control: decoding c - k as if the cipher were additive must give flat IoC
   (this is why kscreen cannot see the plant).
4. Informational: the same statistic on LP2 segment 0.7 with the totient stream at offset 0
   (expected: a null-like z; the full campaign would scan the library at every offset).

**Verdict.** PASS if the true offset clears z >= 5 over both null types and the additive
decode stays flat (< 1.3). A pass validates the statistic and the ~2-4 h library screen;
a fail means the gate is broken and the campaign must not run.

**Cost.** seconds on CPU (n = 1,600 runes, O(n^2) pairs).
