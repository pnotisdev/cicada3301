"""Compare two kscreen screen outputs (CPU engine vs GPU port, or two CPU builds).

    python work/kscreen/tsvdiff.py a.tsv b.tsv

They must agree on: the number of decodes and early aborts, the whole IoC histogram, each window's best IoC,
and the top hits. Ties make the identity of a window's best and of the hits at the cut-off arbitrary (threads
and blocks finish in any order), so those are compared as follows: every hit strictly above the lowest kept IoC
must be the same decode in both; at the cut-off only the IoC values must agree. Exit status 1 on any difference.
"""
import re
import sys


def parse(path):
    d = {"hist": {}, "wbest": {}, "hits": []}
    with open(path, encoding="utf-8") as f:
        lines = f.read().split("\n")      # stream names can contain control characters that splitlines() treats as line ends
    header = None
    for line in lines:
        if line.startswith("# kscreen"):
            m = re.search(r"runs=(\d+) aborted=(\d+)", line)
            d["runs"], d["aborted"] = int(m.group(1)), int(m.group(2))
        elif line.startswith("# window"):
            m = re.match(r"# window (\S+) best ([\d.]+) item=(.*) offset=(\S+) mult=(\d+) model=(\d+)", line)
            d["wbest"][m.group(1)] = (m.group(2), m.group(3), m.group(4), m.group(5), m.group(6))
        elif line.startswith("# hist"):
            for tok in line.split()[2:]:
                b, c = tok.split(":")
                d["hist"][b] = int(c)
        elif line.startswith("ioc\t"):
            header = True
        elif header and line:
            d["hits"].append(tuple(line.split("\t")))          # ioc, item, offset, mult, model, window, n
    return d


def compare(a, b):
    diffs = []
    for k in ("runs", "aborted"):
        if a[k] != b[k]:
            diffs.append(f"{k}: {a[k]} != {b[k]}")
    if a["hist"] != b["hist"]:
        bins = sorted(set(a["hist"]) | set(b["hist"]))
        bad = [(x, a["hist"].get(x, 0), b["hist"].get(x, 0)) for x in bins if a["hist"].get(x, 0) != b["hist"].get(x, 0)]
        diffs.append(f"histogram differs in {len(bad)} bins, e.g. {bad[:4]}")
    for w in sorted(set(a["wbest"]) | set(b["wbest"])):
        x, y = a["wbest"].get(w), b["wbest"].get(w)
        if x is None or y is None or x[0] != y[0]:
            diffs.append(f"window {w} best IoC: {x and x[0]} != {y and y[0]}")
    ha, hb = a["hits"], b["hits"]
    if [h[0] for h in ha] != [h[0] for h in hb]:
        diffs.append(f"hit IoC lists differ ({len(ha)} vs {len(hb)} hits)")
    elif ha:
        cut = ha[-1][0]
        sa = {h[1:] for h in ha if h[0] != cut}
        sb = {h[1:] for h in hb if h[0] != cut}
        if sa != sb:
            diffs.append(f"{len(sa ^ sb)} hits above the cut-off ({cut}) are not the same decode in both")
    return diffs


if __name__ == "__main__":
    d = compare(parse(sys.argv[1]), parse(sys.argv[2]))
    print("IDENTICAL" if not d else "DIFFERENT:\n  " + "\n  ".join(d))
    sys.exit(1 if d else 0)
