"""Power of the shared-key test of the five list items (typo_shared_key.py): can it see a key that restarts at every item?

A library key is PLANTED at the same offset into English twins of the five items (the scored lengths of the laptop's windows, 139 / 91 / 98 / 96 / 129 runes), each twin is
screened ALONE against the keystream library with the campaign's settings (top 2,000 kept), and the planted setting is looked up in each list; the test of typo_shared_key.py is
then run on the five lists. The planted setting is in the top 2,000 of an item only if the true key stands out among 52 million settings in that single short window, so the number of
lists containing it (and the test's verdict) is the power to be expected from the real run.

    python work/typo_shared_key_power.py <work dir>        # writes the twins, plants, screens (kscreen CPU engine) and prints the table
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
KS = os.path.join(HERE, "kscreen")
BIN = os.path.join(KS, "target", "release", "kscreen.exe" if os.name == "nt" else "kscreen")
LENS = [139, 91, 98, 96, 129]
# (library item, offset, multiplier, model): the three families of the laptop's planted controls, skip and coin models
PLANTS = [("primes-1 (totient)", 5000, 1, 0), ("pi digits (base 29)", 9000, 1, 1), ("sha256-ctr reject :3301", 12000, 28, 0),
          ("primes-1 (totient)", 14000, 28, 1), ("pi digits (base 29)", 3000, 1, 0), ("sha256-ctr reject :3301", 7000, 1, 1)]


def run(*args):
    return subprocess.run([BIN, *args], cwd=KS, capture_output=True, text=True, check=True, encoding="utf-8").stdout


def twins(work):
    """one single-window English twin file per item (the scored lengths of the laptop's windows); returns their paths"""
    lines = open(os.path.join(HERE, "phpmt", "data", "english.txt"), encoding="utf-8").read().splitlines()
    runes = [x for k in range(0, len(lines), 3) for x in lines[k + 1][2:].split()]
    pos, paths = 0, []
    for i, n in enumerate(LENS):
        path = os.path.join(work, f"twin_{i}.txt")
        open(path, "w", encoding="utf-8", newline="\n").write(f"W twin_{i} -1\nR {' '.join(runes[pos:pos + n])}\nL {n}\n")
        pos += n
        paths.append(path)
    return paths


def windows(text):
    """the W / R / L blocks of a planted file (the '# truth' comment lines are dropped)"""
    ls = [l for l in text.splitlines() if l.strip() and not l.startswith("#")]
    return ["\n".join(ls[k:k + 3]) + "\n" for k in range(0, len(ls), 3)]


def kept(tsv):
    rows = []
    with open(tsv, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or line.startswith("ioc\t"):
                continue
            p = line.rstrip("\n").split("\t")
            rows.append((float(p[0]), p[1], int(p[2]), int(p[3]), int(p[4])))
    return rows


def main():
    work = sys.argv[1]
    os.makedirs(work, exist_ok=True)
    plains = twins(work)
    sys.path.insert(0, HERE)
    import typo_shared_key as T
    print(f"{'planted setting':44s} " + "  ".join(f"item{i + 1}({n})" for i, n in enumerate(LENS)) + "   lists holding it   test: >=2 / >=3 lists")
    hits = []
    for pi, (item, off, mult, model) in enumerate(PLANTS):
        wins = []
        for i, plain in enumerate(plains):                     # the SAME (item, offset, multiplier, model) in every item: a key that restarts at the same place each time
            pf = os.path.join(work, f"plant{pi}_{i + 1}.txt")
            run("plant", plain, "file:data/library.ksb", item, str(off), str(mult), str(model), "0.18", str(300 + 10 * pi + i), "0", pf)
            wins.append(windows(open(pf, encoding="utf-8").read())[0])
        files, ranks = {}, []
        for i, w in enumerate(wins):
            wf, tsv = os.path.join(work, f"p{pi}_item{i + 1}.txt"), os.path.join(work, f"p{pi}_library_item{i + 1}.tsv")
            open(wf, "w", encoding="utf-8", newline="\n").write(w)
            run("screen", wf, "file:data/library.ksb", tsv, "n=300", "beam=16", "mults=1,28", "models=0,1", "threads=16", "top=2000", "abort=150:1.2")
            files[i + 1] = tsv
            rows = kept(tsv)
            r = next((k + 1 for k, (_, it, o, m, md) in enumerate(rows) if (it, o, m, md) == (item, off, mult, model)), None)
            ranks.append(r)
        d = os.path.join(work, f"set{pi}")
        os.makedirs(d, exist_ok=True)
        for i, p in files.items():
            os.replace(p, os.path.join(d, f"library_item{i}.tsv"))
        out, ks, N, S, cnt = T.table({i: os.path.join(d, f"library_item{i}.tsv") for i in files})
        held = sum(r is not None for r in ranks)
        hits.append(held)
        print(f"{item + f' @{off} x{mult} m{model}':44s} " + "  ".join(f"{('#' + str(r)) if r else '-':>{len(f'item{i + 1}({n})')}s}" for i, (r, n) in enumerate(zip(ranks, LENS)))
              + f"   {held} of 5               {out[2][0]} / {out[3][0]}", flush=True)
    print(f"\nthe planted setting was in the top 2,000 of at least 3 of the 5 items in {sum(h >= 3 for h in hits)} of {len(hits)} plants; in at least 2 in {sum(h >= 2 for h in hits)}")


if __name__ == "__main__":
    main()
