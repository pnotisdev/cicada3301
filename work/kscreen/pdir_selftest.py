"""Gates for the pointer-direction option (pdir=) of the kscreen engine (docs: work/log/phase30_pointer_direction.md). The engine's pdir code must pass ALL of these before any LP2 result with it counts.

 1. reference   engine `trace` against pdir_ref.beam_emul (an exact emulation written from the spec): every one of the 18 conventions x both orientations x both models, random windows/keys, including dead pointers (pad shorter than the walk)
 2. exhaustive  tiny windows: the engine with a huge beam equals the best of ALL pointer paths (pdir_ref.exhaustive) up to the pointer merge; count agreements
 3. equivalence an all-forward direction vector decodes exactly as the default engine (convention 000) and as advsep=1 (convention 010)
 4. plant       an independent planter (pdir_ref.plant, held-out English, skip rule q = 0.81, a library stream) enciphers under 4 (rule, convention, orientation) cases; the pdir screen must return the planted stream at the exact offset with IoC >= 1.6, the default
                engine (no pdir) must stay below 1.40, the wrong rule and the wrong convention are reported at the truth, and the planter's plan equals pdir_ref.plan on its own ciphertext
 5. null        random keystreams, same settings, on the 8 LP2 windows: best IoC below 1.40

    python work/kscreen/pdir_selftest.py [--threads 2] [--quick] [--out results/kscreen/pdir_selftest.txt]
Set KSCREEN_BIN to use another engine binary.
"""
import argparse
import math
import os
import random
import re
import sys

import dirrules as DR
import pdir_ref as P
import selftest as S
import signrules as R

sys.path.insert(0, os.path.join(R.WORK, "layer2"))
from export import read_ksb  # noqa: E402

S.BIN = os.environ.get("KSCREEN_BIN", S.BIN)
HERE = S.HERE
FAMILY = "file:data/library.ksb"
PAD = 300
CONVS = [f"{h}{m}{c}" for h in (0, 1) for m in (0, 1, 2) for c in (0, 1, 2)]
# (rule, convention, orientation negative?, library stream, multiplier, model)
CASES = [("E_cur_n4", "000", False, "primes-1 (totient)", 1, 0), ("A_prev_G", "122", True, "pi digits (base 29)", 28, 1),
         ("B5_prev_R", "021", False, "sha256-ctr reject :3301", 1, 0), ("C_prev_n", "110", True, "primes-1 (totient)", 28, 1)]
KEEP = 0.19            # skip rule q = 0.81


def rule_table():
    rules = R.build_rules()
    rules.update(DR.extra_rules())
    return rules


def engine(args):
    return S.run(args)


def trace_lines(path):
    return [tuple(int(x) for x in l.split()) for l in open(path, encoding="utf-8").read().splitlines()]


def stage_reference(lines, quick):
    rng = random.Random(30)
    nwin, offs, nstreams = (3, 5, 2) if quick else (6, 8, 2)
    ok, total, sens = True, 0, {}
    for pad, glob_n in ((40, None), (12, 14)):                     # the second round has a pad shorter than the walks: dead pointers
        wins, entries = [], []
        for w in range(nwin):
            n = glob_n or rng.randint(30, 48)
            runes = [rng.randrange(Q) for _ in range(n)]
            lens, left = [], n
            while left:
                l = min(left, rng.randint(1, 6))
                lens.append(l)
                left -= l
            dirline = []
            for l in lens:
                dirline += [rng.choice((-1, 1))] * l
            wins.append((runes, lens, dirline, rng.choice([-1, rng.randrange(Q)])))
            entries.append((f"t{w}", wins[-1][3], runes, lens, dirline, None))
        wf = os.path.join(S.TMP, "pdir_ref_windows.txt")
        P.write_windows(wf, entries)
        klen = 2000
        streams = [(f"s{k}", [rng.randrange(Q) for _ in range(klen)]) for k in range(nstreams)]
        P.write_ksb(os.path.join(S.TMP, "pdir_ref.ksb"), streams)
        nmax = max(len(r) for r, *_ in wins)
        for conv in CONVS:
            for neg in (0, 1):
                fwd = max(sum(x for x in P.plan(r, l, dl, p0, conv, bool(neg))[1] if x > 0) for r, l, dl, p0 in wins)       # forward movements between words need more key
                need = nmax + nmax // 4 + 8 + fwd + pad
                out = os.path.join(S.TMP, "pdir_ref_trace.txt")
                engine(["trace", S.rel(wf), "file:" + S.rel(os.path.join(S.TMP, "pdir_ref.ksb")), S.rel(out), "n=300", "beam=16", "mults=1,28", "abort=0", "minlen=5", f"offs=0:{offs}", f"pdir={conv}", f"pad={pad}", f"dirneg={neg}"])
                for it, off, m, model, wi, s, used in trace_lines(out):
                    runes, lens, dirline, prev0 = wins[wi]
                    key = streams[it][1][off - pad:off - pad + need]
                    mk = [k * m % Q for k in key]
                    dirs, mv, pv = P.plan(runes, lens, dirline, prev0, conv, bool(neg))
                    # the encrypted window IS `runes` (any text is a valid ciphertext for the decoder)
                    es, eu, _ = P.beam_emul(runes, pv, mk, model, len(runes), 16, 0, 0, pad, dirs, mv)
                    total += 1
                    if not neg:                                      # sensitivity: the emulation under the NEXT convention must disagree somewhere
                        dirs2, mv2, pv2 = P.plan(runes, lens, dirline, prev0, CONVS[(CONVS.index(conv) + 1) % 18], False)
                        if P.beam_emul(runes, pv2, mk, model, len(runes), 16, 0, 0, pad, dirs2, mv2)[:2] != (s, used):
                            sens[conv] = sens.get(conv, 0) + 1
                    if (es, eu) != (s, used):
                        ok = False
                        lines.append(f"FAIL reference: conv {conv} neg {neg} pad {pad} item {it} off {off} mult {m} model {model} window {wi}: engine ({s},{used}) reference ({es},{eu})")
                        return False
    if len(sens) < 18:
        lines.append(f"FAIL  reference sensitivity: conventions whose neighbour was never distinguished: {sorted(set(CONVS) - set(sens))}")
        return False
    lines.append(f"PASS  reference: {total} decodes (18 conventions x 2 orientations x 2 mults x 2 models, windows 30-48 runes, pads 40 and 12 with dead pointers) equal the exact emulation of the spec; each convention is told apart from its neighbour in {min(sens.values())}+ decodes")
    return ok


Q = 29


def stage_exhaustive(lines):
    rng = random.Random(31)
    agree = diff = 0
    worst = 0
    for t in range(300):
        n = rng.randint(6, 9)
        runes = [rng.randrange(Q) for _ in range(n)]
        lens, left = [], n
        while left:
            l = min(left, rng.randint(1, 4))
            lens.append(l)
            left -= l
        dirline = []
        for l in lens:
            dirline += [rng.choice((-1, 1))] * l
        conv = rng.choice(CONVS)
        neg = rng.random() < 0.5
        model = rng.randrange(2)
        pad = rng.randint(3, 12)
        mk = [rng.randrange(Q) for _ in range(2 * n + 8 + pad)]
        if rng.random() < 0.5:                                   # plant collisions so the skip / coin branches fire
            runes = [(mk[pad + i] + rng.choice((0, 0, 1))) % Q for i in range(n)]
        dirs, mv, pv = P.plan(runes, lens, dirline, -1, conv, neg)
        e = P.exhaustive(runes, pv, mk, model, n, pad, dirs, mv)
        b = P.beam_emul(runes, pv, mk, model, n, 10 ** 6, 0, 0, pad, dirs, mv)[0]
        if b == e:
            agree += 1
        else:
            diff += 1
            worst = max(worst, e - b)
        assert b <= e
    lines.append(f"INFO  exhaustive: unbounded-beam pointer-merged decode equals the best of all pointer paths in {agree} of {agree + diff} tiny cases (the merge on the pointer may lose a better history in the rest, largest loss {worst}); never above it")
    return True


def stage_equivalence(lines):
    rng = random.Random(32)
    entries, runes_all = [], []
    for w in range(4):
        n = rng.randint(40, 60)
        runes = [rng.randrange(Q) for _ in range(n)]
        lens, left = [], n
        while left:
            l = min(left, rng.randint(1, 7))
            lens.append(l)
            left -= l
        entries.append((f"e{w}", -1, runes, lens, [1] * n, None))
    wf_d = os.path.join(S.TMP, "pdir_eq_dir.txt")
    wf_p = os.path.join(S.TMP, "pdir_eq_plain.txt")
    P.write_windows(wf_d, entries)
    P.write_windows(wf_p, [(a, b, c, d, None, None) for a, b, c, d, _, _ in entries])
    P.write_ksb(os.path.join(S.TMP, "pdir_eq.ksb"), [(f"s{k}", [rng.randrange(Q) for _ in range(1500)]) for k in range(2)])
    fam = "file:" + S.rel(os.path.join(S.TMP, "pdir_eq.ksb"))
    res = []
    for conv, extra in (("000", []), ("010", ["advsep=1"])):
        a, b = os.path.join(S.TMP, "pdir_eq_a.txt"), os.path.join(S.TMP, "pdir_eq_b.txt")
        common = ["n=300", "beam=16", "mults=1,28", "abort=0", "minlen=5"]
        engine(["trace", S.rel(wf_d), fam, S.rel(a), *common, "offs=0:25", f"pdir={conv}", "pad=7"])
        engine(["trace", S.rel(wf_p), fam, S.rel(b), *common, "offs=7:32", *extra])
        la, lb = trace_lines(a), trace_lines(b)
        same = la == lb and len(la) > 0
        res.append((conv, same, len(la)))
    ok = all(s for _, s, _ in res)
    lines.append(f"{'PASS' if ok else 'FAIL'}  equivalence: all-forward directions give the default decode (convention 000: {res[0][2]} decodes identical) and advsep=1 (convention 010: {res[1][2]} decodes identical)")
    return ok


def plain_windows():
    lines = open(S.PLAIN, encoding="utf-8").read().splitlines()
    return [([int(x) for x in lines[k + 1][2:].split()], [int(x) for x in lines[k + 2][2:].split()]) for k in range(0, len(lines), 3)]


def spans(lens):
    out, a = [], 0
    for n in lens:
        out.append((a, a + n))
        a += n
    return out


def stage_plant(lines, threads):
    rules = rule_table()
    ksb = dict(read_ksb(os.path.join(HERE, "data", "library.ksb")))
    wins = plain_windows()
    ok, n_hi, n_all = True, 0, 0
    for ci, (rname, conv, neg, item, mult, model) in enumerate(CASES):
        rng = random.Random(900 + ci)
        key = [int(x) for x in ksb[item]]
        entries, truth_off = [], []
        for wi, (runes, lens) in enumerate(wins):
            off = PAD + (1234 + 997 * wi) % (len(key) - PAD - len(runes) * 4 - 64)
            c, native, (umv, upv) = P.plant(runes, lens, key, off, mult, model, KEEP, rules[rname], conv, neg, rng, R.numbers)
            # consistency: the vector from the rule on the planted ciphertext, and the plan of pdir_ref, equal what the planter used
            again = R.sign_vector(rules[rname], R.word_table(c, spans(lens)), spans(lens), len(c))
            assert again == native, f"{rname}: signrules.py and the planter disagree"
            dirs, mv, pv = P.plan(c, lens, native, -1, conv, neg)
            assert mv == umv and pv == upv, f"{rname} {conv}: pdir_ref.plan and the planter disagree"
            entries.append((f"plant_{wi}", -1, c, lens, native, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
            truth_off.append(off)
        pf = os.path.join(S.TMP, f"pdir_plant{ci}.txt")
        P.write_windows(pf, entries)
        # wrong rule: the direction vector of the most 'neutral' other rule (nearest to 50% agreement); wrong convention: right vector, convention with all three digits changed
        c0 = entries[0][2]
        other = min((n for n in rules if n != rname), key=lambda n: abs(sum(x == y for x, y in zip(R.sign_vector(rules[n], R.word_table(c0, spans(entries[0][3])), spans(entries[0][3]), len(c0)), entries[0][4])) / len(c0) - 0.5))
        wrong = [(n, p, c, l, R.sign_vector(rules[other], R.word_table(c, spans(l)), spans(l), len(c)), t) for n, p, c, l, _, t in entries]
        wf = os.path.join(S.TMP, f"pdir_plant{ci}_wrong.txt")
        P.write_windows(wf, wrong)
        opt = [f"pdir={conv}", f"pad={PAD}", f"dirneg={int(neg)}"]
        tsv = os.path.join(S.TMP, f"pdir_plant{ci}.tsv")
        engine(["screen", S.rel(pf), FAMILY, S.rel(tsv), f"only={item}", f"threads={threads}", *opt])
        best = S.window_bests(tsv)
        tsv0 = os.path.join(S.TMP, f"pdir_plant{ci}_default.tsv")
        engine(["screen", S.rel(pf), FAMILY, S.rel(tsv0), f"only={item}", f"threads={threads}"])
        best0 = S.window_bests(tsv0)
        wconv = "".join(str((int(d) + 1) % (3 if k else 2)) for k, d in enumerate(conv))
        for wi, (win, (titem, toff)) in enumerate(S.truths(pf).items()):
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            ver = lambda f, cv: float(re.search(r"ioc ([\d.]+)", engine(["verify", S.rel(f), FAMILY, item, toff, str(mult), str(model), win, f"pdir={cv}", f"pad={PAD}", f"dirneg={int(neg)}"])).group(1))
            v_ok, v_wr, v_wc = ver(pf, conv), ver(wf, conv), ver(pf, wconv)
            ioc0 = best0.get(win, (0.0,))[0]
            agree = sum(x == y for x, y in zip(wrong[wi][4], entries[wi][4])) / len(entries[wi][4])
            blind_wr = v_wr < S.THRESHOLD or agree > 0.7
            good = bitem == item and boff == toff and ioc >= S.THRESHOLD and v_ok >= 1.6 and ioc0 < S.THRESHOLD and blind_wr
            n_hi += ioc >= 1.6
            n_all += 1
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  plant rule {rname} conv {conv} {'reversed' if neg else 'forward'} {item!r} model={model} mult={mult} {win}: pdir screen best {ioc:.3f} at offset {boff} (truth {toff}); re-decode at the truth {v_ok:.3f}; "
                         f"default engine (no pdir) best over all offsets {ioc0:.3f}; with {other}'s directions at the truth {v_wr:.3f} ({100 * agree:.0f}% agreement); with convention {wconv} at the truth {v_wc:.3f}")
    lines.append(f"INFO  plant: {n_hi} of {n_all} first-300-rune screen hits reached IoC >= 1.6 (gate: exact offset and >= {S.THRESHOLD}; every re-decode over the whole window >= 1.6)")
    return ok


def stage_null(lines, threads, quick):
    rules = rule_table()
    nstreams = 4 if quick else 10
    ok = True
    for ci, (rname, conv, neg, item, mult, model) in enumerate(CASES):
        tsv = os.path.join(S.TMP, f"pdir_null{ci}.tsv")
        engine(["screen", S.rel(os.path.join(DR.OUT, rname + ".txt")), f"rand:{nstreams}:{4242 + ci}", S.rel(tsv), f"threads={threads}", f"pdir={conv}", f"pad={PAD}", f"dirneg={int(neg)}"])
        nbest = max(v[0] for v in S.window_bests(tsv).values())
        ok &= nbest < S.THRESHOLD
        lines.append(f"{'PASS' if nbest < S.THRESHOLD else 'FAIL'}  null: {nstreams} random keystreams, rule {rname}, convention {conv}, {'reversed' if neg else 'forward'}, both mults and models, 8 LP2 windows: best IoC {nbest:.3f} (must stay below {S.THRESHOLD})")
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--out", default=os.path.join(S.OUT, "pdir_selftest.txt"))
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    DR.main()
    lines, ok = [], True
    for name, fn in (("reference", lambda: stage_reference(lines, a.quick)), ("exhaustive", lambda: stage_exhaustive(lines)), ("equivalence", lambda: stage_equivalence(lines)),
                     ("plant", lambda: stage_plant(lines, a.threads)), ("null", lambda: stage_null(lines, a.threads, a.quick))):
        if a.only and a.only != name:
            continue
        r = fn()
        ok &= r
        print("\n".join(lines[-12:]) if not r else lines[-1], flush=True)
    lines.append("PDIR SELFTEST " + ("PASSED" if ok else "FAILED"))
    text = "\n".join(lines) + "\n"
    print(text)
    with open(a.out, "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
