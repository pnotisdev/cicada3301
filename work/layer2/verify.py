"""Verification of layer2 screen hits (work/layer2).

    python work/layer2/verify.py <screen.tsv> [--top 15] [--controls 20] [--out <file>]

mode=bigram / known screens: each of the best hits (the best per window first, then the overall list) is re-decoded
over its WHOLE window with a wide beam, and the same setting is decoded at `--controls` random offsets of the same
stream (a keystream-matched null). A candidate must reach +2.0 per rune over the whole window and beat the matched
null's maximum by 5 (a true key keeps about +7; a chance hit falls to the null's -8 .. -15).
mode=periodic screens: the keyword is estimated from the decoded columns (best shift of English unigram frequencies,
identity and Atbash alphabets) and the window is re-decoded in mode=bigram with that keyword; same rule.
Writes the report (and the decoded text of anything that passes) to --out (default: next to the tsv).
"""
import argparse
import os
import random
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
BIN = os.path.join(HERE, "target", "release", "layer2" + (".exe" if os.name == "nt" else ""))
BIGRAM = os.path.join(WORK, "phpmt", "data", "bigram.txt")
N = 29
PASS_SCORE = 2.0
PASS_MARGIN = 5.0


def run(args):
    r = subprocess.run([BIN] + args, cwd=HERE, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"layer2 {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def parse_tsv(path):
    head, hits, wins = {}, [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("# layer2 screen"):
                head = dict(kv.split("=", 1) for kv in line[len("# layer2 screen "):].split() if "=" in kv)
            elif line.startswith("# window "):
                m = re.match(r"# window (\S+) best (\S+) item=(.*) offset=(\d+) mult=(\d+) model=(\d+) (.*)$", line)
                if m and m.group(3) != "-":
                    wins.append(dict(window=m.group(1), score=float(m.group(2)), item=m.group(3), offset=int(m.group(4)),
                                     mult=int(m.group(5)), model=int(m.group(6)), inner=m.group(7)))
            elif line and not line.startswith("#") and not line.startswith("score\t"):
                sc, item, off, mult, model, win, n, inner = line.split("\t")
                hits.append(dict(window=win, score=float(sc), item=item, offset=int(off), mult=int(mult), model=int(model),
                                 inner=inner))
    return head, wins, hits


def keywords(path):
    out = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            if line.strip() and not line.startswith("#"):
                p = line.split()
                out[p[0]] = [int(x) for x in p[1:]]
    return out


def unigram():
    rows = [list(map(int, l.split())) for l in open(BIGRAM, encoding="utf-8") if l.strip()]
    return rows[N]


def estimate_keyword(plain, m, uni):
    """plain: decoded q values of a periodic decode (-1 = literal F). Returns [(atb, keyword values)]."""
    cols = [[] for _ in range(m)]
    k = 0
    for q in plain:
        if q < 0:
            continue
        cols[k % m].append(q)
        k += 1
    out = []
    for atb in (0, 1):
        kw = []
        for col in cols:
            best = max(range(N), key=lambda s: sum(uni[(N - 1 - (q - s) % N) if atb else (q - s) % N] for q in col))
            kw.append(best)
        out.append((atb, kw))
    return out


def inner_fields(inner):
    return dict(kv.split("=", 1) for kv in inner.split())


def verify_bigram(head, h, kwvals, isign, phase, litf, atb, controls):
    out = run(["verify", head["windows"], head["family"], h["item"], str(h["offset"]), str(h["mult"]), str(h["model"]),
               h["window"], "mode=bigram", "kwvals=" + ",".join(map(str, kwvals)), f"isign={isign}", f"phase={phase}",
               f"litf={litf}", f"atb={atb}", f"controls={controls}"])
    m = re.search(r"score (-?[\d.]+) ioc ([\d.]+)", out)
    c = re.search(r"controls \d+ random offsets: mean (-?[\d.]+) max (-?[\d.]+)", out)
    t = re.search(r"^text (.*)$", out, re.M)
    return float(m.group(1)), float(m.group(2)), float(c.group(2)) if c else None, t.group(1) if t else ""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--controls", type=int, default=20)
    ap.add_argument("--out")
    a = ap.parse_args()
    head, wins, hits = parse_tsv(a.tsv)
    mode = head.get("mode")
    kws = keywords(os.path.join(HERE, head["kw"])) if head.get("kw", "-") != "-" else {}
    uni = unigram()
    todo, seen = [], set()
    for h in sorted(wins, key=lambda x: -x["score"]) + hits:
        key = (h["window"], h["item"], h["offset"], h["inner"])
        if key not in seen and len(todo) < a.top:
            seen.add(key)
            todo.append(h)
    lines = [f"# verify {os.path.basename(a.tsv)} (mode={mode}): top {len(todo)} hits re-decoded over the whole window, "
             f"{a.controls} matched-null offsets each; pass = score >= {PASS_SCORE} and >= null max + {PASS_MARGIN}"]
    passed = 0
    for h in todo:
        f = inner_fields(h["inner"])
        if mode in ("bigram", "known"):
            kw = kws[f["kw"]]
            tries = [(int(f.get("atb", 0)), kw, int(f["isign"]), int(f["phase"]), int(f["litf"]))]
            if mode == "known":
                tries = [(ab, kw, int(f["isign"]), int(f["phase"]), int(f["litf"])) for ab in (0, 1)]
        else:
            out = run(["verify", head["windows"], head["family"], h["item"], str(h["offset"]), str(h["mult"]), str(h["model"]),
                       h["window"], "mode=periodic", f"m={f['m']}", f"litf={f['litf']}", "n=300"])
            plain = [int(x) for x in re.search(r"^plain (.*)$", out, re.M).group(1).split(",")]
            tries = [(ab, kw, 1, 0, int(f["litf"])) for ab, kw in estimate_keyword(plain, int(f["m"]), uni)]
        best = None
        for atb, kw, isign, phase, litf in tries:
            sc, ioc, cmax, text = verify_bigram(head, h, kw, isign, phase, litf, atb, a.controls)
            if best is None or sc > best[0]:
                best = (sc, ioc, cmax, text, atb, kw)
        sc, ioc, cmax, text, atb, kw = best
        ok = sc >= PASS_SCORE and (cmax is None or sc >= cmax + PASS_MARGIN)
        passed += ok
        lines.append(f"{'CANDIDATE' if ok else 'noise    '}  {h['window']} {h['item']!r} offset={h['offset']} mult={h['mult']} "
                     f"model={h['model']} {h['inner']}: screen {h['score']:.3f}; whole window {sc:+.3f}/rune (IoC {ioc:.3f}), "
                     f"matched null max {cmax:+.3f}; keyword {kw} atb={atb}")
        if ok:
            lines.append("    text " + text[:600])
    lines.append(f"{passed} of {len(todo)} re-decoded hits pass ({'CANDIDATE - read the text' if passed else 'none: noise'})")
    text = "\n".join(lines) + "\n"
    print(text)
    out = a.out or a.tsv.replace(".tsv", "_verify.txt")
    with open(out, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text)


if __name__ == "__main__":
    sys.exit(main())
