"""Pointer-direction screen driver: the pilot and (with --streams all --windows all) the campaign steps of work/log/phase30_pointer_direction.md.

    python work/kscreen/pdir_pilot.py --conv 000 [--windows seg0.7|seg0.7,seg0.8|all] [--streams 6|all] [--threads 2] [--rules a,b|all] [--null 6] [--tag pilot]

For every rule of dir_rules.txt and both orientations (dirneg=0 / 1) it screens the chosen windows (D lines of data/dirs/<rule>.txt, built by dirrules.py) against `--streams` streams of the flat-IoC library (every stride-th stream, or all 581) at every offset, mults 1 and 28, both
anti-repeat models; then the matched null: the same vectors, windows and options against --null random keystreams. Outputs results/kscreen/pdir/<tag>/<conv>/{real,null}/<rule>_<fwd|rev>.tsv (a finished file is skipped on a restart) and <conv>_summary.txt.
Decision rule (docs/CAMPAIGNS.md): IoC >= 1.40 on the first 300 runes is a hit, then verify.py (pdir options are read from the tsv header) over the whole window against 20 random offsets of the same stream.
"""
import argparse
import os
import subprocess
import sys

import selftest as S

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "layer2"))
from export import read_ksb  # noqa: E402
import pdir_ref as P  # noqa: E402

HERE = S.HERE
BIN = os.environ.get("KSCREEN_BIN", S.BIN)
OUT = os.path.join(S.ROOT, "results", "kscreen", "pdir")


def window_file(rule, wins):
    """the rule's D-line file restricted to the named windows (data/dirs/<rule>.txt has W / R / L / D lines per window)"""
    src = os.path.join(HERE, "data", "dirs", rule + ".txt")
    if wins == "all":
        return os.path.relpath(src, HERE).replace("\\", "/")
    keep = set(wins.split(","))
    dst_dir = os.path.join(HERE, "data", "dirs_" + wins.replace(",", "_"))
    os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, rule + ".txt")
    lines = open(src, encoding="utf-8").read().splitlines()
    out, on = [], False
    for l in lines:
        if l.startswith("W "):
            on = l.split()[1] in keep
        if on:
            out.append(l)
    open(dst, "w", newline="\n", encoding="utf-8").write("\n".join(out) + "\n")
    return os.path.relpath(dst, HERE).replace("\\", "/")


def hits(tsv):
    best, rows = 0.0, []
    for l in open(tsv, encoding="utf-8", errors="replace").read().split("\n"):
        if l.startswith("# best"):
            best = float(l.split()[2])
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--conv", required=True)
    ap.add_argument("--windows", default="seg0.7")
    ap.add_argument("--streams", default="6")
    ap.add_argument("--rules", default="all")
    ap.add_argument("--null", type=int, default=6)
    ap.add_argument("--threads", type=int, default=2)
    ap.add_argument("--tag", default="pilot")
    ap.add_argument("--pad", type=int, default=300)
    ap.add_argument("--parts", default="real,null", help="real, null or real,null")
    a = ap.parse_args()
    rules = [l.strip() for l in open(os.path.join(HERE, "dir_rules.txt"), encoding="utf-8") if l.strip()]
    if a.rules != "all":
        rules = a.rules.split(",")
    fam = "file:data/library_flat.ksb"
    if a.streams != "all":
        ks = read_ksb(os.path.join(HERE, "data", "library_flat.ksb"))
        k = int(a.streams)
        sub = ks[::max(1, len(ks) // k)][:k]
        sub_path = os.path.join(HERE, "data", f"library_flat_sub{k}.ksb")
        P.write_ksb(sub_path, [(n, list(v)) for n, v in sub])
        fam = f"file:data/library_flat_sub{k}.ksb"
        print("streams:", [n for n, _ in sub])
    base = os.path.join(OUT, a.tag, a.conv)
    summary = []
    for kind, family in (("real", fam), ("null", f"rand:{a.null}:{3301 + int(a.conv, 3)}")):
        if kind not in a.parts.split(","):
            continue
        os.makedirs(os.path.join(base, kind), exist_ok=True)
        for rule in rules:
            for neg, tag in ((0, "fwd"), (1, "rev")):
                tsv = os.path.join(base, kind, f"{rule}_{tag}.tsv")
                if os.path.exists(tsv):
                    continue
                cmd = [BIN, "screen", window_file(rule, a.windows), family, tsv, f"threads={a.threads}", f"pdir={a.conv}", f"pad={a.pad}", f"dirneg={neg}", "top=50"]
                r = subprocess.run(cmd, cwd=HERE, capture_output=True, text=True)
                if r.returncode != 0:
                    sys.exit(r.stderr)
                # an engine without the pdir option silently ignores pdir= (phase30_review.md, severity 2): refuse its output
                if f"pdir={a.conv}" not in open(tsv, encoding="utf-8", errors="replace").readline():
                    os.remove(tsv)
                    sys.exit(f"{BIN} wrote no pdir={a.conv} header: wrong engine (set KSCREEN_BIN to target/pdir/kscreen.exe)")
                print(kind, rule, tag, r.stderr.strip().splitlines()[-1], flush=True)
    res = {}
    kinds = [k for k in ("real", "null") if k in a.parts.split(",")]
    for kind in kinds:
        res[kind] = sorted(((hits(os.path.join(base, kind, f"{r}_{t}.tsv")), r, t) for r in rules for t in ("fwd", "rev")), reverse=True)
    for kind in kinds:
        b = [x[0] for x in res[kind]]
        summary.append(f"{kind}: {len(b)} vectors, best IoC {b[0]:.4f} ({res[kind][0][1]} {res[kind][0][2]}); vectors with best >= 1.30: {sum(x >= 1.30 for x in b)}, >= 1.35: {sum(x >= 1.35 for x in b)}, >= 1.40: {sum(x >= 1.40 for x in b)}; median of per-vector best {sorted(b)[len(b) // 2]:.4f}")
        summary.append(f"  top 5: " + ", ".join(f"{s:.4f} {r} {t}" for s, r, t in res[kind][:5]))
    text = f"pdir {a.tag} conv {a.conv}: windows {a.windows}, streams {a.streams} of the flat library, null {a.null} random keystreams, pad {a.pad}\n" + "\n".join(summary) + "\n"
    print(text)
    open(os.path.join(base, "summary_" + a.parts.replace(",", "_") + ".txt"), "w", newline="\n", encoding="utf-8").write(text)


if __name__ == "__main__":
    main()
