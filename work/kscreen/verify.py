"""Re-decode the best kscreen hits over whole windows and show the plaintext.

    python work/kscreen/verify.py <hits.tsv> [--top 15] [--controls 20] [--out report.txt]

For each distinct (keystream, window) among the top hits, the whole window is decoded at the hit's offset
(beam 64, no early abort). A true key keeps a language-like IoC over the whole window (English runes ~1.8,
any natural language well above 1.3); a lucky 300-rune stretch falls back towards 1.05. The plaintext is
printed as decoded and with letters relabelled by frequency rank onto English (a hint for the case where the
plaintext alphabet was also substituted).

Keystream-matched null: the same keystream, multiplier and model are also decoded at --controls random offsets
on the same window. A structured keystream (e.g. a short period) can let the beam overfit, so a real hit must
beat its own keystream's controls by MARGIN as well as reach REAL.
"""
import argparse
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lp  # noqa: E402
import lang_checks  # noqa: E402

BIN = os.environ.get("KSCREEN_BIN") or os.path.join(HERE, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
REAL = 1.40
MARGIN = 0.15


def english_rank():
    import sim
    c = Counter(sim.english_runes())
    return [x for x, _ in c.most_common()] + [x for x in range(lp.N) if x not in c]


def read_hits(path):
    meta, rows, header = {}, [], None
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")      # not splitlines(): stream names can contain control characters (the binary seed)
    for line in lines:
        if line.startswith("# kscreen"):
            meta = dict(kv.split("=", 1) for kv in line.split()[3:] if "=" in kv)
        elif line.startswith("ioc\t"):
            header = line.split("\t")
        elif header and line and not line.startswith("#"):
            rows.append(dict(zip(header, line.split("\t"))))
    return meta, rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tsv")
    ap.add_argument("--top", type=int, default=15)
    ap.add_argument("--controls", type=int, default=20)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    meta, rows = read_hits(args.tsv)
    fam, windows = meta["family"], meta["windows"]
    rank = english_rank()
    seen, out, real, checked = set(), [], 0, 0
    for h in rows:
        key = (h["item"], h["window"])
        if key in seen:
            continue
        seen.add(key)
        if len(seen) > args.top:
            break
        checked += 1
        r = subprocess.run([BIN, "verify", windows, fam, h["item"], h["offset"], h["mult"], h["model"], h["window"],
                            f"controls={args.controls}", *(["dir=back"] if meta.get("dir") == "back" else []),
                            *([f"clock={meta['clock']}"] if meta.get("clock") else []),
                            *([f"nulledge={meta['nulledge']}"] if meta.get("nulledge") else []),
                            *([f"advsep={meta['advsep']}"] if meta.get("advsep") else []),
                            *([f"pdir={meta['pdir']}", f"pad={meta['pad']}", f"dirneg={meta['dirneg']}"] if meta.get("pdir") else [])],
                           cwd=HERE, capture_output=True, text=True)
        m = re.search(r"window (\S+) n (\d+) ioc ([\d.]+) pointer_jumps (\d+)", r.stdout)
        if not m:
            out.append(f"{h['ioc']}  {h['item']} {h['window']}: verify failed {r.stderr.strip()[:200]}")
            continue
        n, ioc, jumps = int(m.group(2)), float(m.group(3)), int(m.group(4))
        c = re.search(r"controls \d+ random offsets: mean ([\d.]+) max ([\d.]+)", r.stdout)
        cmean, cmax = (float(c.group(1)), float(c.group(2))) if c else (0.0, 0.0)
        plain = [int(x) for x in re.search(r"plain (.*)", r.stdout).group(1).split(",")]
        freq = [x for x, _ in Counter(plain).most_common()]
        relabel = {x: rank[i] for i, x in enumerate(freq)}
        latin = "".join(lp.LATIN[x] for x in plain[:160])
        guess = "".join(lp.LATIN[relabel[x]] for x in plain[:160])
        good = ioc >= REAL and ioc >= cmax + MARGIN
        real += good
        out.append(f"{float(h['ioc']):.3f} (first {h['n']}) -> {ioc:.3f} over {n} runes "
                   f"[{'REAL? check by eye' if good else 'noise'}]  {h['item']!r} offset={h['offset']} "
                   f"mult={h['mult']} model={h['model']} window={h['window']} jumps={jumps}; same keystream at "
                   f"{args.controls} random offsets: mean {cmean:.3f}, max {cmax:.3f}"
                   + ("" if not lang_checks.applies(meta) else f"; {lang_checks.fmt(lang_checks.checks(h['window'], plain))}"))
        out.append(f"    decoded : {latin}")
        out.append(f"    by rank : {guess}")
    out.append("")
    out.append(f"{real} of {checked} re-decoded hits keep IoC >= {REAL} over their whole window and beat their own "
               f"keystream's random offsets by {MARGIN} ({'CANDIDATE - inspect' if real else 'none: noise'})")
    text = "\n".join(out) + "\n"
    print(text)
    if args.out:
        with open(args.out, "w", newline="\n", encoding="utf-8") as f:
            f.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
