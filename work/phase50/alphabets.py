"""Phase 50 item (ii): canonical alternative alphabet orders as the addition domain.

    python work/phase50/alphabets.py run <name|all> [--threads 12]

c = sigma(p + k): the cipher runes are written with a mixed alphabet sigma (sigma[x] = rune at position x of the order).
The existing front end (work/kscreen/relabel_export.py) feeds c' = sigma_inv(c) to the ordinary screen. The orders:
  latin           the runes sorted by their Latin spelling (digraph runes after their first letter): A AE B C D E EA EO F ...
  latin-ng        the same with the Ing rune filed as NG (after N)
  futhark-a / -o  Elder Futhark order (Ansuz read as the A rune / the O rune), the runes it lacks last in GP order
  rune-names      alphabetical by the Old English rune names (Ac, Aesc, Beorc, Cen, Daeg, Ear, Eh, Eoh, ...)
Control: English planted under a library key in the screen domain, printed with sigma, relabelled back, screened (item only).
"""
import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reorder as R  # noqa: E402  (also puts work/ and work/kscreen on sys.path)
import lp  # noqa: E402
import relabel_export as rx  # noqa: E402

L = lp.LATIN
IDX = {l: i for i, l in enumerate(L)}


def rest(order):
    return order + [i for i in range(lp.N) if i not in order]


ELDER = ["F", "U", "TH", "@", "R", "C", "G", "W", "H", "N", "I", "J", "EO", "P", "X", "S", "T", "B", "E", "M", "L", "ING", "D", "OE"]
ORDERS = {
    "latin": sorted(range(lp.N), key=lambda i: L[i]),
    "latin-ng": sorted(range(lp.N), key=lambda i: "NG" if L[i] == "ING" else L[i]),
    "futhark-a": rest([IDX["A"] if x == "@" else IDX[x] for x in ELDER]),
    "futhark-o": rest([IDX["O"] if x == "@" else IDX[x] for x in ELDER]),
    "rune-names": [IDX[x] for x in "A AE B C D EA E EO X OE F J G H ING IA I L M N O P R S TH T U W Y".split()],
}
# OEIS sequences whose first 29 terms permute the first 29 primes (the GP values), from 7he5haman's Mayfly document
# (column counts 83 103 101 107 occur in them); terms copied from work/ref/oeis/stripped.gz
OEIS29 = {
    "A107801": "2 23 3 13 11 17 7 37 31 19 29 59 5 53 43 41 47 67 61 71 73 79 89 83 103 101 107 97 109",
    "A107802": "3 13 11 17 7 37 23 2 29 19 31 41 43 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107803": "5 53 3 13 11 17 7 37 23 2 29 19 31 41 43 47 67 61 71 73 79 59 89 83 103 101 107 97 109",
    "A107804": "7 17 11 13 3 23 2 29 19 31 37 43 41 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107805": "11 13 3 23 2 29 19 17 7 37 31 41 43 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107806": "13 3 23 2 29 19 11 17 7 37 31 41 43 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107807": "17 7 37 3 13 11 19 29 2 23 31 41 43 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107808": "19 11 13 3 23 2 29 59 5 53 31 17 7 37 43 41 47 67 61 71 73 79 89 83 103 101 107 97 109",
    "A107809": "23 2 29 19 11 13 3 31 17 7 37 43 41 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107810": "29 2 23 3 13 11 17 7 37 31 19 41 43 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107811": "31 3 13 11 17 7 37 23 2 29 19 41 43 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107812": "37 3 13 11 17 7 47 41 19 29 2 23 31 43 53 5 59 79 67 61 71 73 83 89 97 107 101 103 109",
    "A107813": "41 11 13 3 23 2 29 19 17 7 37 31 43 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A107814": "43 3 13 11 17 7 37 23 2 29 19 31 41 47 67 61 71 73 53 5 59 79 89 83 103 101 107 97 109",
    "A185956": "2 3 5 7 13 11 19 17 29 23 37 43 31 47 41 61 53 67 71 59 73 89 79 83 103 101 107 109 97",
}
PRIMES29 = sorted(int(x) for x in OEIS29["A107801"].split())
for _a, _s in OEIS29.items():
    ORDERS["oeis-" + _a] = [PRIMES29.index(int(x)) for x in _s.split()]
assert all(sorted(o) == list(range(lp.N)) for o in ORDERS.values())


def run(name, threads, control_only=False):
    sigma = ORDERS[name]
    seg = os.path.join(R.KS, "data", "segments.txt")
    out_dir = os.path.join(R.TMP, "alpha_" + name)
    win = os.path.join(out_dir, "segments.txt")
    os.makedirs(out_dir, exist_ok=True)
    rx.relabel_windows_file(seg, sigma, win)
    # control: plant in the screen domain, print with sigma, relabel back
    eng = [int(x) for l in open(os.path.join(R.WORK, "phpmt", "data", "english.txt")) if l.startswith("R ") for x in l[2:].split()]
    names, lens = [], []
    for l in open(seg).read().split(chr(10)):
        if l.startswith("W "):
            names.append(l.split()[1])
        elif l.startswith("R "):
            lens.append(len(l.split()) - 1)
    plain = os.path.join(R.TMP, f"alpha_{name}_ctl_plain.txt")
    R.write(plain, [(n, [eng[(j + 977 * k) % len(eng)] for j in range(m)]) for k, (n, m) in enumerate(zip(names, lens))])
    plant = os.path.join(R.TMP, f"alpha_{name}_ctl_plant.txt")
    item = "primes-1 (totient)"
    R.kscreen(["plant", R.rel(plain), "file:data/library.ksb", item, "1234", "1", "0", "0.18", "13", "0", R.rel(plant)])
    text = open(plant).read()
    cips = [[int(x) for x in l[2:].split()] for l in text.split("\n") if l.startswith("R ")]
    truth = re.findall(r"# truth plant_\d+ item=.*? offset=(\d+)", text)
    printed = os.path.join(out_dir, "ctl_printed.txt")
    R.write(printed, [(n, [sigma[x] for x in c]) for n, c in zip(names, cips)])
    back = os.path.join(out_dir, "ctl_back.txt")
    rx.relabel_windows_file(printed, sigma, back)
    ctl = os.path.join(R.OUT, f"alpha_{name}_control.tsv")
    R.kscreen(["screen", R.rel(back), "file:data/library.ksb", R.rel(ctl), f"only={item}", f"threads={threads}"])
    b = R.best(ctl)
    res, ok = [], True
    for n, t in zip(names, truth):
        ioc, bi, bo = b[n]
        good = bi == item and abs(int(bo) - int(t)) <= 10 and ioc >= 1.40
        ok &= good
        res.append(f"{'PASS' if good else 'FAIL'} plant {name} {n}: best {ioc:.3f} at offset {bo} (truth {t})")
    raw = os.path.join(R.OUT, f"alpha_{name}_control_unrelabelled.tsv")        # blindness: without the relabelling the plant is invisible
    R.kscreen(["screen", R.rel(printed), "file:data/library.ksb", R.rel(raw), f"only={item}", f"threads={threads}"])
    blind = max(v[0] for v in R.best(raw).values())
    res.append(f"unrelabelled printed text, same item: best {blind:.3f} over all windows (must stay below 1.40)")
    ok &= blind < 1.40
    if control_only:
        print(f"control {name} {'PASS' if ok else 'FAIL'}", *res, sep=chr(10))
        return ""
    nul = os.path.join(R.OUT, f"alpha_{name}_null.tsv")
    lib = os.path.join(R.OUT, f"alpha_{name}_library.tsv")
    if not os.path.exists(nul):
        R.kscreen(["screen", R.rel(win), "rand:300:5051", R.rel(nul), f"threads={threads}"])
    if not os.path.exists(lib):
        R.kscreen(["screen", R.rel(win), "file:data/library.ksb", R.rel(lib), "mults=1,28", "models=0,1", f"threads={threads}"])
    bl, bn = R.best(lib), R.best(nul)
    head = (f"alpha {name}: control {'PASS' if ok else 'FAIL'} ({sum('PASS' in x for x in res)}/{len(res)}); library best "
            f"{max(v[0] for v in bl.values()):.4f}, null best {max(v[0] for v in bn.values()):.4f}")
    import subprocess
    v = subprocess.run([sys.executable, os.path.join(R.KS, "verify.py"), lib, "--top", "10", "--controls", "20", "--out",
                        os.path.join(R.OUT, f"alpha_{name}_library_verify.txt")], capture_output=True, text=True)
    out = "\n".join([head] + res + [v.stdout.strip().splitlines()[-1]])
    print(out, flush=True)
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("name")
    ap.add_argument("--threads", type=int, default=12)
    ap.add_argument("--control-only", action="store_true")
    a = ap.parse_args()
    names = list(ORDERS) if a.name == "all" else [a.name]
    with open(os.path.join(R.OUT, "summary_alphabets.txt"), "a", encoding="utf-8", newline="\n") as f:
        for n in names:
            f.write(run(n, a.threads, a.control_only) +"\n")
            f.flush()
