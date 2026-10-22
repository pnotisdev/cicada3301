"""Phase 50 item (i): reading-order transforms of the LP2 section windows through the default kscreen engine.

    python work/phase50/reorder.py run <transform|all> [--threads 12]   # control, null, library screen, verify
    python work/phase50/reorder.py windows <transform> <out.txt>

A section is split into pages ('%') and printed lines (newline). A transform gives the order in which the section's
runes are read; the first 300 runes of the transformed window are screened against the library (both signs, both
models), exactly as data/segments.txt. prev = -1 (the chain across sections is meaningless once the order is changed).
  boustrophedon-odd / -even   every odd / even line of a page (counted per page, from 0) is read right to left
  linerev                     lines of a page in reverse order, each line left to right
  pagerev                     pages of the section in reverse order
  colmajor                    per page, column 0 of every line top to bottom, then column 1 ... (ragged lines skip)
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ROOT = os.path.dirname(WORK)
KS = os.path.join(WORK, "kscreen")
sys.path.insert(0, WORK)
sys.path.insert(0, KS)
import lp  # noqa: E402
import verify as V  # noqa: E402

BIN = V.BIN
OUT = os.path.join(ROOT, "results", "kscreen", "phase50")
TMP = os.path.join(KS, "data", "phase50")           # windows (derived, small)
SECS = list(range(7, 16))
TRANSFORMS = ["identity", "boustrophedon-odd", "boustrophedon-even", "linerev", "pagerev", "colmajor"]


def pages_of(toks):
    """pages -> lines -> rune positions (indices into the section's rune list)"""
    pages, lines, line, k = [], [], [], 0
    for t in toks:
        if isinstance(t, int):
            line.append(k)
            k += 1
        elif t in ("\n", "%"):
            if line:
                lines.append(line)
            line = []
            if t == "%" and lines:
                pages.append(lines)
                lines = []
    if line:
        lines.append(line)
    if lines:
        pages.append(lines)
    return pages


def order(toks, name):
    """perm: perm[i] = original rune index read i-th"""
    pages = pages_of(toks)
    if name == "pagerev":
        pages = pages[::-1]
    out = []
    for lines in pages:
        if name == "linerev":
            lines = lines[::-1]
        if name.startswith("boustrophedon"):
            par = 1 if name.endswith("odd") else 0
            lines = [l[::-1] if i % 2 == par else l for i, l in enumerate(lines)]
        if name == "colmajor":
            w = max(len(l) for l in lines)
            out += [l[c] for c in range(w) for l in lines if c < len(l)]
        else:
            out += [x for l in lines for x in l]
    assert sorted(out) == list(range(len(out)))
    return out


def windows(name, segs=None, cipher=None):
    segs = segs or lp.load_segments()
    items = []
    for i in SECS:
        c = lp.runes_of(segs[i]) if cipher is None else cipher.get(i, [])
        if len(c) < 100:
            continue
        p = order(segs[i], name)
        items.append((f"seg0.{i}", [c[j] for j in p]))
    return items


def write(path, items):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as f:
        for n, r in items:
            f.write(f"W {n} -1\nR {' '.join(map(str, r))}\n")


def kscreen(args):
    r = subprocess.run([BIN] + args, cwd=KS, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-500:])
    return r.stdout


def rel(p):
    return os.path.relpath(p, KS).replace("\\", "/")


def best(tsv):
    return {m.group(1): (float(m.group(2)), m.group(3), m.group(4)) for m in
            re.finditer(r"# window (\S+) best ([\d.]+) item=(.*?) offset=(\S+) ", open(tsv, encoding="utf-8").read())}


def control(name, thr, threads=12):
    """plant English under a library key in the transformed reading order, print it back in LP's layout, run the
    pipeline on the printed text, screen only that item: it must come back at the planted offset"""
    segs = lp.load_segments()
    eng = [int(x) for l in open(os.path.join(WORK, "phpmt", "data", "english.txt")) if l.startswith("R ") for x in l[2:].split()]
    names = [i for i in SECS if len(lp.runes_of(segs[i])) >= 100]
    plain = os.path.join(TMP, f"{name}_ctl_plain.txt")
    write(plain, [(f"seg0.{i}", [eng[(j + 977 * i) % len(eng)] for j in range(len(lp.runes_of(segs[i])))]) for i in names])
    plant = os.path.join(TMP, f"{name}_ctl_plant.txt")
    item, off = "primes-1 (totient)", "1234"
    kscreen(["plant", rel(plain), "file:data/library.ksb", item, off, "1", "0", "0.18", "11", "0", rel(plant)])
    text = open(plant).read()
    cips = [[int(x) for x in l[2:].split()] for l in text.split("\n") if l.startswith("R ")]
    truth = re.findall(r"# truth plant_\d+ item=.*? offset=(\d+)", text)
    printed = {}
    for i, cw in zip(names, cips):
        pr = [0] * len(cw)
        for k, j in enumerate(order(segs[i], name)):
            pr[j] = cw[k]
        printed[i] = pr
    win = os.path.join(TMP, f"{name}_ctl_windows.txt")
    write(win, windows(name, segs, printed))
    tsv = os.path.join(OUT, f"{name}_control.tsv")
    kscreen(["screen", rel(win), "file:data/library.ksb", rel(tsv), f"only={item}", f"threads={threads}"])
    b = best(tsv)
    ok, lines = True, []
    for i, t in zip(names, truth):
        ioc, bi, bo = b[f"seg0.{i}"]
        good = bi == item and abs(int(bo) - int(t)) <= 10 and ioc >= thr
        ok &= good
        lines.append(f"{'PASS' if good else 'FAIL'} plant {name} seg0.{i}: best {ioc:.3f} at offset {bo} (truth {t})")
    return ok, lines


def run(name, threads):
    os.makedirs(OUT, exist_ok=True)
    win = os.path.join(TMP, f"{name}.txt")
    write(win, windows(name))
    ok, ctl = control(name, 1.40, threads)
    nul = os.path.join(OUT, f"{name}_null.tsv")
    lib = os.path.join(OUT, f"{name}_library.tsv")
    if not os.path.exists(nul):
        kscreen(["screen", rel(win), "rand:300:5050", rel(nul), f"threads={threads}"])
    if not os.path.exists(lib):
        kscreen(["screen", rel(win), "file:data/library.ksb", rel(lib), "mults=1,28", "models=0,1", f"threads={threads}"])
    bl, bn = best(lib), best(nul)
    res = [f"{name}: control {'PASS' if ok else 'FAIL'} ({sum('PASS' in l for l in ctl)}/{len(ctl)}); library best "
           f"{max(v[0] for v in bl.values()):.4f}, null best {max(v[0] for v in bn.values()):.4f}"] + ctl
    v = subprocess.run([sys.executable, os.path.join(KS, "verify.py"), lib, "--top", "10", "--controls", "20", "--out",
                        os.path.join(OUT, f"{name}_library_verify.txt")], capture_output=True, text=True)
    res.append(v.stdout.strip().splitlines()[-1])
    text = "\n".join(res)
    print(text, flush=True)
    return text


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("name")
    ap.add_argument("out", nargs="?")
    ap.add_argument("--threads", type=int, default=12)
    a = ap.parse_args()
    if a.cmd == "windows":
        write(a.out, windows(a.name))
    else:
        names = TRANSFORMS if a.name == "all" else [a.name]
        os.makedirs(OUT, exist_ok=True)
        with open(os.path.join(OUT, "summary_reorder.txt"), "a", encoding="utf-8", newline="\n") as f:
            for n in names:
                f.write(run(n, a.threads) + "\n")
                f.flush()
