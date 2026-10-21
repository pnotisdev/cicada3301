"""Phase 35 (work/log/phase35_words_map.md): rank 1 and rank 3 of the 2016-message coverage map (phase34).

 A  LP2's own word-length and word-sum sequences as additive key streams: for the whole book (sections 0.7-0.15 concatenated) and every section with enough words, the values length n, GP index sum R, GP prime-value sum G (raw, mod 29) and their prefix sums
    (mod 29), forwards and reversed. One value per WORD: the screen consumes one key value per rune, so the sequence is walked rune by rune. Matched null: 10 shuffles of every stream (same values, same lengths).
 B  the ciphertext written reversed per word / per clause / per line: the windows are transformed (runes reversed inside each unit) and run through the DEFAULT engine against the 581 flat library streams. Matched null: the transformed windows against random keystreams.
 Controls: an independent Python planter (pdir_ref.plant with all directions forward) with held-out English; in B the plant is enciphered, then reversed per unit as the hypothesis says, then the pipeline transforms it back; the same plant WITHOUT the transform must stay blind.

    python work/kscreen/phase35.py build|controls|run|verify|summary [--threads 2]
Set KSCREEN_BIN to use another engine binary. Everything is resumable (a finished tsv is skipped).
"""
import argparse
import os
import random
import re
import subprocess
import sys

import pdir_ref as P
import selftest as S
import signrules as R

WORK = R.WORK
sys.path.insert(0, os.path.join(WORK, "layer2"))
from export import read_ksb  # noqa: E402
import keystreams  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402
import numpy as np  # noqa: E402

S.BIN = os.environ.get("KSCREEN_BIN", S.BIN)
HERE = S.HERE
DATA = os.path.join(HERE, "data", "phase35")
RES = os.path.join(S.ROOT, "results", "kscreen", "phase35")
Q = 29
MINWORDS = 450          # a section stream shorter than this barely covers a 300-rune window (key need 383)


def sections():
    """seg -> dict(runes, spans of words, clause spans, line spans); runes checked against data/segments.txt"""
    segf = {}
    cur = None
    for line in open(os.path.join(HERE, "data", "segments.txt"), encoding="utf-8").read().splitlines():
        if line.startswith("W "):
            cur = line.split()[1]
            segf[cur] = {}
        elif line.startswith("R "):
            segf[cur]["runes"] = [int(x) for x in line[2:].split()]
    out = {}
    for seg in range(7, 16):
        if f"seg0.{seg}" not in segf:        # the section(s) data/segments.txt leaves out (too short for a window)
            continue
        toks = stats.SEGS[seg]
        runes = lp.runes_of(toks)
        assert runes == segf[f"seg0.{seg}"]["runes"], seg
        words = [(a, b) for _, a, b in lp.word_spans(toks, runes)]
        cl, ln, k, ca, la = [], [], 0, 0, 0
        for t in toks:
            if isinstance(t, int):
                k += 1
            elif t in (".", "&") and k > ca:
                cl.append((ca, k)); ca = k
            if not isinstance(t, int) and t in ("\n", "%") and k > la:
                ln.append((la, k)); la = k
        if k > ca:
            cl.append((ca, k))
        if k > la:
            ln.append((la, k))
        out[f"seg0.{seg}"] = dict(runes=runes, word=words, clause=cl, line=ln)
    return out


def reverse_units(runes, spans):
    out = []
    for a, b in spans:
        out += runes[a:b][::-1]
    return out


def word_values(runes, words):
    n = [b - a for a, b in words]
    r = [sum(runes[a:b]) for a, b in words]
    g = [sum(lp.PRIME[x] for x in runes[a:b]) for a, b in words]
    return {"n": n, "R": r, "G": g}


def stream_set(secs):
    """name -> list of key values (0..28)"""
    scopes = {"book": {"n": [], "R": [], "G": []}}
    for name, s in secs.items():
        v = word_values(s["runes"], s["word"])
        for k in v:
            scopes["book"][k] += v[k]
        if len(s["word"]) >= MINWORDS:
            scopes[name] = v
    out = {}
    for scope, vals in scopes.items():
        for k, seq in vals.items():
            raw = [x % Q for x in seq]
            pre, acc = [], 0
            for x in seq:
                acc += x
                pre.append(acc % Q)
            for kind, s in (("raw", raw), ("prefix", pre)):
                out[f"p35 {scope} {k} {kind} fwd"] = s
                out[f"p35 {scope} {k} {kind} rev"] = s[::-1]
    return out


def predicted_ioc(v):
    """IoC LP2 would show if English were enciphered with this stream as an additive key (the flat-IoC filter of signrules.flat_library)"""
    pe = keystreams.english_distribution()
    h = np.bincount(np.array(v) % Q, minlength=Q) / len(v)
    q = sum(h[k] * np.roll(pe, k) for k in range(Q))
    return float(Q * (q ** 2).sum())


def build():
    os.makedirs(DATA, exist_ok=True)
    secs = sections()
    streams = stream_set(secs)
    P.write_ksb(os.path.join(DATA, "words.ksb"), list(streams.items()))
    rng = random.Random(35)
    nulls = []
    for name, v in streams.items():
        for i in range(10):
            s = v[:]
            rng.shuffle(s)
            nulls.append((f"null{i} {name}", s))
    P.write_ksb(os.path.join(DATA, "words_null.ksb"), nulls)
    with open(os.path.join(DATA, "streams.tsv"), "w", newline="\n") as f:
        f.write("stream\tlength\tpredicted_ioc\n")
        for name, v in streams.items():
            f.write(f"{name}\t{len(v)}\t{predicted_ioc(v):.4f}\n")
    # B: transformed windows (prev = -1: the previous section's last rune is not known after the transform)
    for unit in ("word", "clause", "line"):
        with open(os.path.join(DATA, f"rev_{unit}.txt"), "w", newline="\n") as f:
            for name, s in secs.items():
                f.write(f"W {name} -1\nR {' '.join(map(str, reverse_units(s['runes'], s[unit])))}\n")
    print(len(streams), "streams,", len(nulls), "null streams;", {u: round(sum(b - a for a, b in secs['seg0.7'][u]) / len(secs['seg0.7'][u]), 2) for u in ('word', 'clause', 'line')}, "mean unit length in 0.7")


def engine(args):
    return S.run(args)


def synthetic_units(lens, rng):
    """clause / line unit spans (in runes) for a plaintext window that has only word lengths: groups of 6-14 / 4-9 words"""
    def group(lo, hi):
        spans, a, i = [], 0, 0
        while i < len(lens):
            k = rng.randint(lo, hi)
            b = a + sum(lens[i:i + k])
            spans.append((a, b)); a = b; i += k
        return spans
    return group(6, 14), group(4, 9)


def controls(threads):
    import sign_selftest as SS
    lines, ok = [], True
    preds = {l.split("\t")[0]: float(l.split("\t")[2]) for l in open(os.path.join(DATA, "streams.tsv"), encoding="utf-8").read().splitlines()[1:]}
    flat = [n for n, p in preds.items() if p <= 1.003]
    lines.append(f"INFO  {len(flat)} of {len(preds)} word streams are predicted flat (<= 1.003 under English); the rest cannot be additive keys of a flat text (the screen is run on all of them)")
    ksb = dict(read_ksb(os.path.join(DATA, "words.ksb")))
    plains = SS.plain_windows()
    fam = "file:" + os.path.relpath(os.path.join(DATA, "words.ksb"), HERE).replace("\\", "/")
    cases = [(flat[i * max(1, len(flat) // 4)], mult, model) for i, (mult, model) in enumerate([(1, 0), (28, 1), (1, 1), (28, 0)])]
    one = lambda t, w: 1
    for ci, (item, mult, model) in enumerate(cases):
        key = list(ksb[item])
        rng = random.Random(3500 + ci)
        entries = []
        for wi, (runes, lens) in enumerate(plains):
            off = (400 + 211 * wi) % max(1, len(key) - len(runes) * 2 - 60)
            c, _, _ = P.plant(runes, lens, key, off, mult, model, 0.19, one, "000", False, rng, R.numbers)
            entries.append((f"plant_{wi}", -1, c, lens, None, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
        pf = os.path.join(S.TMP, f"p35a_plant{ci}.txt")
        P.write_windows(pf, entries)
        tsv = os.path.join(S.TMP, f"p35a_plant{ci}.tsv")
        engine(["screen", S.rel(pf), fam, S.rel(tsv), f"only={item}", f"threads={threads}"])
        best = S.window_bests(tsv)
        other = [n for n in flat if n.split()[1] == 'book' and n.split()[2:4] != item.split()[2:4]][0]      # a different value type (a section stream is a constant shift of a book stream, the screen's shift b absorbs it)
        tsvo = os.path.join(S.TMP, f"p35a_plant{ci}_other.tsv")
        engine(["screen", S.rel(pf), fam, S.rel(tsvo), f"only={other}", f"threads={threads}"])
        besto = S.window_bests(tsvo)
        for win, (_, toff) in S.truths(pf).items():
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            good = bitem == item and abs(int(boff) - int(toff)) <= 2 and ioc >= S.THRESHOLD and besto.get(win, (9,))[0] < S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  A plant {item!r} model={model} mult={mult} {win}: best {ioc:.3f} at offset {boff} (truth {toff}); another word stream ({other!r}) on the same ciphertext: {besto.get(win, (0,))[0]:.3f}")
    # B: plant, enciphered forward, then reversed per unit; the pipeline transform restores it; the untransformed plant stays blind
    lib = "file:data/library_flat.ksb"
    lk = dict(read_ksb(os.path.join(HERE, "data", "library.ksb")))
    for ui, unit in enumerate(("word", "clause", "line")):
        item, mult, model = ("primes-1 (totient)", 1, 0) if ui != 1 else ("pi digits (base 29)", 28, 1)
        key = [int(x) for x in lk[item]]
        rng = random.Random(3600 + ui)
        raw, trans = [], []
        for wi, (runes, lens) in enumerate(plains):
            off = 500 + (1234 + 997 * wi) % (len(key) - len(runes) * 4 - 560)
            c, _, _ = P.plant(runes, lens, key, off, mult, model, 0.19, one, "000", False, rng, R.numbers)
            words, (cl, ln) = [], synthetic_units(lens, rng)
            a = 0
            for n in lens:
                words.append((a, a + n)); a += n
            spans = {"word": words, "clause": cl, "line": ln}[unit]
            x = reverse_units(c, spans)                                # what the hypothesis says LP2 shows
            raw.append((f"plant_{wi}", -1, x, lens, None, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
            trans.append((f"plant_{wi}", -1, reverse_units(x, spans), lens, None, f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model}"))
        for tag, ent in (("raw", raw), ("trans", trans)):
            P.write_windows(os.path.join(S.TMP, f"p35b_{unit}_{tag}.txt"), ent)
            engine(["screen", S.rel(os.path.join(S.TMP, f"p35b_{unit}_{tag}.txt")), "file:data/library.ksb", S.rel(os.path.join(S.TMP, f"p35b_{unit}_{tag}.tsv")), f"only={item}", f"threads={threads}"])
        bt, br = S.window_bests(os.path.join(S.TMP, f"p35b_{unit}_trans.tsv")), S.window_bests(os.path.join(S.TMP, f"p35b_{unit}_raw.tsv"))
        for win, (_, toff) in S.truths(os.path.join(S.TMP, f"p35b_{unit}_raw.txt")).items():
            ioc, bitem, boff = bt.get(win, (0.0, "-", "-"))
            good = bitem == item and abs(int(boff) - int(toff)) <= 2 and ioc >= S.THRESHOLD and br.get(win, (9,))[0] < S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  B plant reversed per {unit} {item!r} model={model} mult={mult} {win}: transformed pipeline best {ioc:.3f} at offset {boff} (truth {toff}); the plant WITHOUT the transform {br.get(win, (0,))[0]:.3f}")
    lines.append("PHASE35 CONTROLS " + ("PASSED" if ok else "FAILED"))
    os.makedirs(RES, exist_ok=True)
    open(os.path.join(RES, "controls.txt"), "w", newline="\n", encoding="utf-8").write("\n".join(lines) + "\n")
    print("\n".join(lines))
    return ok


def screen(name, windows, family, threads):
    tsv = os.path.join(RES, name + ".tsv")
    if not os.path.exists(tsv):
        os.makedirs(RES, exist_ok=True)
        engine(["screen", windows, family, tsv, f"threads={threads}", "top=200"])
        print("done", name, flush=True)
    return tsv


def run(threads):
    segs = "data/segments.txt"
    rel = lambda p: os.path.relpath(p, HERE).replace("\\", "/")
    screen("A_real", segs, "file:" + rel(os.path.join(DATA, "words.ksb")), threads)
    screen("A_null", segs, "file:" + rel(os.path.join(DATA, "words_null.ksb")), threads)
    for unit in ("word", "clause", "line"):
        w = rel(os.path.join(DATA, f"rev_{unit}.txt"))
        screen(f"B_{unit}_real", w, "file:data/library_flat.ksb", threads)
        screen(f"B_{unit}_null", w, "rand:150:35", threads)


def best_of(tsv):
    for l in open(tsv, encoding="utf-8", errors="replace").read().split("\n"):
        if l.startswith("# best"):
            return float(l.split()[2])
    return 0.0


def verify():
    for f in sorted(os.listdir(RES)):
        if f.endswith("_real.tsv") and not os.path.exists(os.path.join(RES, f[:-4] + "_verify.txt")):
            subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), os.path.join(RES, f), "--top", "10", "--out", os.path.join(RES, f[:-4] + "_verify.txt")], capture_output=True, text=True)


def summary():
    lines = []
    for n in ("A_real", "A_null", "B_word_real", "B_word_null", "B_clause_real", "B_clause_null", "B_line_real", "B_line_null"):
        p = os.path.join(RES, n + ".tsv")
        if os.path.exists(p):
            hd = open(p, encoding="utf-8", errors="replace").readline()
            lines.append(f"{n}: best IoC {best_of(p):.4f}  ({re.search(r'runs=(\d+)', hd).group(1)} decodes)")
        v = os.path.join(RES, n + "_verify.txt")
        if os.path.exists(v):
            lines.append("   verify: " + open(v, encoding="utf-8").read().strip().splitlines()[-1])
    text = "\n".join(lines) + "\n"
    open(os.path.join(RES, "summary.txt"), "w", newline="\n", encoding="utf-8").write(text)
    print(text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--threads", type=int, default=2)
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    {"build": build, "controls": lambda: controls(a.threads), "run": lambda: run(a.threads), "verify": verify, "summary": summary}[a.cmd]()
