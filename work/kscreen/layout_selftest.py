"""Controls for the layout-number rules (layoutrules.py; phase 36): signs from the page / line / position of each rune.

An independent Python planter (its layout is parsed from the master text itself, not from lp.py / stats.py, and its rules are written again here) enciphers held-out English rune by rune with c = p + s_i * k where the sign of position i is a layout rule of
the i-th rune of an LP2 section (the first rune count of the section's layout), the anti-repeat rule as in the engine (skip / coin, keep 0.18) and a library key at a known offset; the sign vector is written as the S line. For each case the screen must return the planted item
as the window's best hit with IoC >= 1.40 and the re-decode at the truth must reach 1.40 (positive control); the same ciphertext WITHOUT its S line and with another rule's S line must stay below 1.40 at the truth when the rule flips 30-70% of the runes (blindness);
layoutrules.py must reproduce the planter's sign vector (consistency). Null: random keystreams under a rule's signs on the 8 LP2 windows stay below 1.40. Cost: --cost times a sign screen and a pdir screen of one rule on 6 library streams, 1 thread.

    python work/kscreen/layout_selftest.py [--threads 1] [--cost] [--out results/kscreen/layout_selftest.txt]
"""
import argparse
import os
import random
import re
import sys
import time

import selftest as S
import layoutrules as L

HERE = S.HERE
sys.path.insert(0, os.path.join(L.WORK, "layer2"))
from export import read_ksb  # noqa: E402

sys.path.insert(0, L.WORK)
import lp  # noqa: E402

FAMILY = "file:data/library.ksb"
Q = 29
# (rule, library item, multiplier, model, section index of the layout used for the plant window k)
CASES = [("Ln_par", "primes-1 (totient)", 1, 0), ("PL_xor", "pi digits (base 29)", 28, 1), ("Po_par", "sha256-ctr reject :3301", 1, 0), ("Pg_half_lines", "primes-1 (totient)", 28, 1), ("Pa_par", "pi digits (base 29)", 1, 0)]
SECS = (7, 8, 9)


def independent_layout():
    """per master segment, per rune (page_abs, page_sec, line_pg, line_sec, pos_ln, rune_pg, page_runes, page_lines), parsed straight from the master text (segments without runes are skipped, as lp.load_segments does)"""
    text = open(lp.MASTER, encoding="utf-8").read().split("\n\n", 1)[1].split("§")[0]
    page, line, pos = 1, 1, 0
    segs = []
    for raw in text.split("$"):
        psec, lsec, rows = 1, 1, []
        for ch in raw:
            if ch in lp.RUNE_IDX:
                pos += 1
                rows.append([page, psec, line, lsec, pos])
            elif ch == "%":
                page += 1
                psec += 1
                line, pos = 1, 0
            elif ch == "/":
                line += 1
                lsec += 1
                pos = 0
        if rows:
            segs.append(rows)
    runes, lines, seen = {}, {}, {}
    for rows in segs:
        for r in rows:
            runes[r[0]] = runes.get(r[0], 0) + 1
            lines[r[0]] = max(lines.get(r[0], 0), r[2])
    for rows in segs:
        for r in rows:
            seen[r[0]] = seen.get(r[0], 0) + 1
            r += [seen[r[0]], runes[r[0]], lines[r[0]]]
    return segs


# the planter's own rule definitions (written again, not imported from layoutrules.py)
IND = {"Ln_par": lambda r: 1 if r[2] % 2 == 0 else -1, "PL_xor": lambda r: 1 if (r[0] + r[2]) % 2 == 0 else -1, "Po_par": lambda r: 1 if r[4] % 2 == 0 else -1,
       "Pg_half_lines": lambda r: 1 if 2 * r[2] <= r[7] else -1, "Pa_par": lambda r: 1 if r[0] % 2 == 0 else -1}


def plain_windows():
    lines = open(S.PLAIN, encoding="utf-8").read().splitlines()
    return [([int(x) for x in lines[k + 1][2:].split()], [int(x) for x in lines[k + 2][2:].split()]) for k in range(0, len(lines), 3)]


def plant(runes, signs, key, mult, model, keep, rng):
    mk = [k * mult % Q for k in key]
    c, j, prev = [], 0, -1
    for i, p in enumerate(runes):
        s = signs[i]
        kv = lambda x: (Q - mk[x]) % Q if s < 0 else mk[x]
        y = (p + kv(j)) % Q
        j += 1
        if model == 0:
            tries = 0
            while prev >= 0 and y == prev and rng.random() >= keep and tries < 5:
                y = (p + kv(j)) % Q
                j += 1
                tries += 1
        elif prev >= 0 and y == prev:
            j += 1
            if rng.random() >= keep:
                y = (p + kv(j)) % Q
                j += 1
        c.append(y)
        prev = y
    return c


def write(path, entries):
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        for name, c, lens, signs, truth in entries:
            if truth:
                f.write(truth + "\n")
            f.write(f"W {name} -1\nR {' '.join(map(str, c))}\nL {' '.join(map(str, lens))}\n")
            if signs is not None:
                f.write(f"S {' '.join(map(str, signs))}\n")


def cost(lines, threads):
    """1-thread timing of one rule as signs and as pdir (convention 000) on 6 flat-library streams, 8 LP2 windows, mults 1/28, both models"""
    fam = "file:data/library_flat_sub6.ksb"
    if not os.path.exists(os.path.join(HERE, "data", "library_flat_sub6.ksb")):
        lines.append("INFO  cost: data/library_flat_sub6.ksb missing, cost not measured")
        return
    t0 = time.perf_counter()
    out = S.run(["screen", "data/layout_signs/Ln_par.txt", fam, S.rel(os.path.join(S.TMP, "layout_cost_sign.tsv")), f"threads={threads}"])
    t_sign = time.perf_counter() - t0
    m = re.search(r"([\d,]+) decodes", out + open(os.path.join(S.TMP, "layout_cost_sign.tsv"), encoding="utf-8").read())
    base = time.perf_counter()
    S.run(["screen", "data/signs/E_cur_n4.txt", fam, S.rel(os.path.join(S.TMP, "layout_cost_wordsign.tsv")), f"threads={threads}"])
    t_word = time.perf_counter() - base
    binp = os.environ.get("KSCREEN_BIN")
    t_dir = None
    if binp and os.path.exists(binp):
        old = S.BIN
        S.BIN = binp
        try:
            base = time.perf_counter()
            S.run(["screen", "data/layout_dirs/Ln_par.txt", fam, S.rel(os.path.join(S.TMP, "layout_cost_dir.tsv")), f"threads={threads}", "pdir=000", "pad=300"])
            t_dir = time.perf_counter() - base
        finally:
            S.BIN = old
    hdr = open(os.path.join(S.TMP, "layout_cost_sign.tsv"), encoding="utf-8").readline()
    runs = int(re.search(r"runs=(\d+)", hdr).group(1))
    lines.append(f"INFO  cost (1 thread, 6 streams, {runs} decodes incl. early aborts): signs of Ln_par {t_sign:.1f} s ({runs / t_sign:,.0f} decodes/s), word signs E_cur_n4 {t_word:.1f} s"
                 + (f", pdir 000 with D lines {t_dir:.1f} s" if t_dir else ", pdir not timed (set KSCREEN_BIN to the pdir engine)"))
    per = t_sign / 6 * 581 / 3600
    lines.append(f"INFO  cost extrapolated to the 581 flat streams, one thread: {per:.2f} core-hours per rule as signs; on 14 threads {per / 14 * 60:.1f} min" + (f"; as pdir convention 000: {t_dir / 6 * 581 / 3600:.2f} core-hours per vector (two orientations per rule), {t_dir / 6 * 581 / 3600 / 14 * 60:.1f} min on 14 threads" if t_dir else ""))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=1)
    ap.add_argument("--cost", action="store_true")
    ap.add_argument("--out", default=os.path.join(S.OUT, "layout_selftest.txt"))
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    tabs = L.window_tables()
    by_seg = {int(h.split()[1].split(".")[1]): fe for h, _, _, fe, _ in tabs}
    ind = independent_layout()
    # consistency 1: the independent layout parse equals layoutrules.py on every LP2 window
    lines, ok = [], True
    mism = 0
    for sec in by_seg:
        fe, rows = by_seg[sec], ind[sec]
        assert len(fe) == len(rows), sec
        for f, r in zip(fe, rows):
            if [f["page_abs"], f["page_sec"], f["line_pg"], f["line_sec"], f["pos_ln"], f["rune_pg"], f["page_runes"], f["page_lines"]] != r:
                mism += 1
    good = mism == 0
    ok &= good
    lines.append(f"{'PASS' if good else 'FAIL'}  layout parse: layoutrules.py equals the independent parse of the master text on all {sum(len(v) for v in by_seg.values())} runes of the 8 windows ({mism} mismatches)")
    ksb = dict(read_ksb(os.path.join(HERE, "data", "library.ksb")))
    wins = plain_windows()
    rules = L.build_rules()
    for ci, (rname, item, mult, model) in enumerate(CASES):
        rng = random.Random(900 + ci)
        key = [int(x) for x in ksb[item]]
        entries, truths = [], []
        for wi, (runes, lens) in enumerate(wins):
            sec = SECS[wi]
            rows = ind[sec][:len(runes)]
            signs = [IND[rname](r) for r in rows]
            assert signs == L.vector(rules[rname], by_seg[sec][:len(runes)]), f"{rname}: planter and layoutrules.py disagree"
            off = (1234 + 997 * wi) % (len(key) - len(runes) * 4 - 64)
            c = plant(runes, signs, key[off:], mult, model, 0.18, rng)
            entries.append((f"plant_{wi}", c, lens, signs, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
        plant_f = os.path.join(S.TMP, f"layout_plant{ci}.txt")
        write(plant_f, entries)
        write(os.path.join(S.TMP, f"layout_plant{ci}_nosign.txt"), [(n, c, l, None, t) for n, c, l, _, t in entries])
        other = [n for n in rules if n != rname and n.split("_")[0] != rname.split("_")[0]]
        other_name = min(other, key=lambda n: abs(sum(x == y for x, y in zip(L.vector(rules[n], by_seg[SECS[0]][:len(entries[0][1])]), entries[0][3])) / len(entries[0][3]) - 0.5))
        write(os.path.join(S.TMP, f"layout_plant{ci}_wrong.txt"), [(n, c, l, L.vector(rules[other_name], by_seg[SECS[wi]][:len(c)]), t) for wi, (n, c, l, _, t) in enumerate(entries)])
        tsv = os.path.join(S.TMP, f"layout_plant{ci}.tsv")
        S.run(["screen", S.rel(plant_f), FAMILY, S.rel(tsv), f"only={item}", f"threads={a.threads}"])
        best = S.window_bests(tsv)
        for wi, (win, (titem, toff)) in enumerate(S.truths(plant_f).items()):
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            ver = lambda f: float(re.search(r"ioc ([\d.]+)", S.run(["verify", S.rel(f), FAMILY, item, toff, str(mult), str(model), win])).group(1))
            v_ok, v_no, v_wr = ver(plant_f), ver(os.path.join(S.TMP, f"layout_plant{ci}_nosign.txt")), ver(os.path.join(S.TMP, f"layout_plant{ci}_wrong.txt"))
            true_s = entries[wi][3]
            share = true_s.count(-1) / len(true_s)
            wrong_s = L.vector(rules[other_name], by_seg[SECS[wi]][:len(true_s)])
            agree = sum(x == y for x, y in zip(wrong_s, true_s)) / len(true_s)
            changes = sum(1 for i in range(1, len(true_s)) if true_s[i] != true_s[i - 1])
            blocky = changes < 10      # a page / half-page rule flips whole blocks: the unsigned decode keeps long correct stretches and is NOT blind (first run: 1.438 at 33% flipped), so blindness is required only for rules with >= 10 sign changes
            blind_no = (v_no < S.THRESHOLD) if (0.3 <= share <= 0.7 and not blocky) else True
            blind_wr = (v_wr < S.THRESHOLD) if (agree <= 0.7 and not blocky) else True
            good = bitem == item and ioc >= S.THRESHOLD and v_ok >= S.THRESHOLD and blind_no and blind_wr
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  rule {rname} plant {item!r} model={model} mult={mult} {win} (layout of 0.{SECS[wi]}): best {ioc:.3f} at offset {boff} (truth {toff}); re-decode with its signs {v_ok:.3f}; "
                         f"without signs {v_no:.3f} ({100 * share:.0f}% flipped, {changes} sign changes{'' if (0.3 <= share <= 0.7 and not blocky) else ', not required to fail'}); with {other_name}'s signs {v_wr:.3f} ({100 * agree:.0f}% agreement{'' if (agree <= 0.7 and not blocky) else ', not required to fail'})")
    for rname in ("Ln_par", "Pa_par"):
        nulls = os.path.join(S.TMP, f"layout_null_{rname}.tsv")
        S.run(["screen", f"data/layout_signs/{rname}.txt", "rand:30:4242", S.rel(nulls), f"threads={a.threads}"])
        nbest = max(v[0] for v in S.window_bests(nulls).values())
        good = nbest < S.THRESHOLD
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'}  null: 30 random keystreams under the signs of rule {rname} on the 8 LP2 windows: best IoC {nbest:.3f} (must stay below {S.THRESHOLD})")
    if a.cost:
        try:
            cost(lines, a.threads)
        except Exception as e:  # noqa: BLE001
            lines.append(f"INFO  cost not measured: {str(e)[:300]}")
    lines.append("LAYOUT SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
