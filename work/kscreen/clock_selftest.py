"""Controls for kscreen-clock (docs/HYPOTHESES.md H3: a key pointer that moves on by g instead of 1).

    python work/kscreen/clock_selftest.py [--threads N] [--out results/kscreen/clock_selftest.txt]

For each clock (c1, cp, ct read from the cipher rune; p1, pp, pt from the deciphered rune) a key is planted into
held-out English under the anti-repeat rule and must come back as its window's best hit at IoC >= 1.40, with a full
re-decode at the true offset >= 1.40 (a clocked pointer can resynchronise, so a nearby offset counts as found, as in
selftest.py). The 1+index clocks use the totient stream; the prime clocks step about 44 key values per rune, more than a
20,000-value stream holds for a 400-rune window, so they use the 41,235-value Self-Reliance prefix sum. Blindness: the
same c1 ciphertext screened without the clock must stay below 1.40.
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import selftest as st  # noqa: E402

CLOCKS = ("c1", "cp", "ct", "p1", "pp", "pt")
N_OF = {"c1": 300, "p1": 300}                     # the prime clocks screen 150 runes (key_need in the engine)


def case(ck):
    if ck in N_OF:
        return "file:data/library.ksb", "primes-1 (totient)", "1234"
    return "file:data/library_hyp.ksb", "Self-Reliance prefix sum of prime values", "2345"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--out", default=os.path.join(st.OUT, "clock_selftest.txt"))
    args = ap.parse_args()
    os.makedirs(st.TMP, exist_ok=True)
    lines, ok = [], True
    for ci, ck in enumerate(CLOCKS):
        fam, item, off = case(ck)
        n = N_OF.get(ck, 150)
        plant, tsv = os.path.join(st.TMP, f"clock_plant_{ck}.txt"), os.path.join(st.TMP, f"clock_plant_{ck}.tsv")
        model, mult = ci % 2, (1, 28)[ci % 2]
        st.run(["plant", st.rel(st.PLAIN), fam, item, off, str(mult), str(model), "0.18", str(500 + ci), "0", st.rel(plant), f"clock={ck}"])
        st.run(["screen", st.rel(plant), fam, st.rel(tsv), f"only={item}", f"threads={args.threads}", f"clock={ck}", f"n={n}"])
        best = st.window_bests(tsv)
        for win, (_, toff) in st.truths(plant).items():
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            vout = st.run(["verify", st.rel(plant), fam, item, toff, str(mult), str(model), win, f"clock={ck}"])
            vioc = float(re.search(r"ioc ([\d.]+)", vout).group(1))
            good = bitem == item and ioc >= st.THRESHOLD and vioc >= st.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  clock={ck} plant {item!r} mult={mult} model={model} {win}: best {ioc:.3f} "
                         f"at offset {boff} (truth {toff}); re-decode at truth {vioc:.3f}")
        if ck == "c1":
            tsv0 = os.path.join(st.TMP, "clock_plant_c1_unclocked.tsv")
            st.run(["screen", st.rel(plant), fam, st.rel(tsv0), f"only={item}", f"threads={args.threads}"])
            b0 = max(v[0] for v in st.window_bests(tsv0).values())
            good = b0 < st.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  blindness: the clock=c1 plants screened without the clock: best {b0:.3f} "
                         f"(must stay below {st.THRESHOLD})")
    lines.append("CLOCK SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
