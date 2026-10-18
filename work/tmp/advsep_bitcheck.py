"""Bit-identity check for the kscreen advsep change: the new binary with advsep=0 (and nulledge untouched)
must reproduce the pre-change binary byte for byte on the same inputs. Only the wall-clock `secs=` field of
screen headers may differ. Screen hit rows are compared as a multiset (the top-N sort is unstable over equal
IoC, so tie order can vary between runs); the window-best lines and trace/plant/verify outputs are compared
line by line.

    python work/tmp/advsep_bitcheck.py [--threads N]
"""
import argparse
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KS = os.path.join(ROOT, "work", "kscreen")
OLD = os.path.join(HERE, "advsep_bitcheck", "kscreen_old.exe")
NEW = os.path.join(KS, "target_advsep", "release", "kscreen.exe")
TMP = os.path.join(HERE, "advsep_bitcheck")


def run(bin_path, args, log):
    r = subprocess.run([bin_path] + args, cwd=KS, capture_output=True, text=True)
    if r.returncode != 0:
        log.append(f"FAIL {os.path.basename(bin_path)} {' '.join(args)}:\n{r.stderr}")
        return None
    return r.stdout


def strip_secs(text):
    return [re.sub(r"secs=\d+", "secs=", l) for l in text.splitlines()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--threads", type=int, default=min(8, os.cpu_count()))
    args = ap.parse_args()
    os.makedirs(TMP, exist_ok=True)
    log, ok = [], True
    # (label, args-with-{out}-placeholder, compare: exact | screen | trace)
    plain = os.path.join(HERE, "nulledge_plain.txt")
    nullwin = os.path.join(HERE, "nulledge_window_v1_p100.txt")
    cases = [
        ("screen rand on segments", ["screen", "data/segments.txt", "rand:2:99", "{out}", f"threads={args.threads}"], "screen"),
        ("screen rand on chain (P lines)", ["screen", "data/chain/segments_a7.txt", "rand:2:99", "{out}", f"threads={args.threads}"], "screen"),
        ("trace rand", ["trace", "data/segments.txt", "rand:2:99", "{out}", "items=0:1", "offs=0:5"], "exact"),
        ("nulledge=1 screen", ["screen", os.path.relpath(nullwin, KS).replace("\\", "/"), "file:data/library.ksb", "{out}",
                               "only=primes", "mults=1", "models=0,1", "nulledge=1", f"threads={args.threads}"], "screen"),
    ]
    for label, tmpl, kind in cases:
        outs = {}
        for tag, bin_path in (("old", OLD), ("new", NEW)):
            out = os.path.join(TMP, f"bc_{label.replace(' ', '_').replace('(', '').replace(')', '')}_{tag}.txt")
            outs[tag] = run(bin_path, [a.format(out=out.replace("\\", "/")) for a in tmpl], log)
            outs[tag + "_path"] = out
        if outs["old"] is None or outs["new"] is None:
            ok = False
            continue
        same = True
        if kind == "screen":
            old_l, new_l = strip_secs(outs["old"]), strip_secs(outs["new"])
            if old_l != new_l:
                same = False
                # rows may reorder among ties; compare header, best, window-best lines exactly and the rest as multisets
                rows = lambda ls: [l for l in ls if l and not l.startswith("#")]
                meta = lambda ls: [l for l in ls if l.startswith("# kscreen") or l.startswith("# best") or l.startswith("# window")]
                if meta(old_l) == meta(new_l) and sorted(rows(old_l)) == sorted(rows(new_l)):
                    same = True
                    log.append(f"info  {label}: identical except row order among IoC ties")
                else:
                    log.append(f"FAIL  {label}:\n  old meta: {meta(old_l)}\n  new meta: {meta(new_l)}")
        elif kind == "exact":
            if strip_secs(outs["old"]) != strip_secs(outs["new"]):
                same = False
                log.append(f"FAIL  {label}: outputs differ")
        if same:
            log.append(f"PASS  {label}: byte-identical (secs excepted)")
        else:
            ok = False
    # plant + verify on the planted file (each binary its own plant output, both compared)
    for tag, bin_path in (("old", OLD), ("new", NEW)):
        plant_out = os.path.join(TMP, f"bc_plant_{tag}.txt")
        run(bin_path, ["plant", os.path.relpath(plain, KS).replace("\\", "/"), "file:data/library.ksb",
                       "primes", "100", "1", "0", "0.19", "12345", "0", plant_out.replace("\\", "/")], log)
        v = run(bin_path, ["verify", os.path.relpath(plant_out, KS).replace("\\", "/"), "file:data/library.ksb",
                           "primes", "100", "1", "0", "plant_0", "n=300"], log)
        with open(os.path.join(TMP, f"bc_verify_{tag}.txt"), "w", newline="\n", encoding="utf-8") as f:
            f.write(v or "")
    for name in ("plant", "verify"):
        o = open(os.path.join(TMP, f"bc_{name}_old.txt"), encoding="utf-8").read()
        n = open(os.path.join(TMP, f"bc_{name}_new.txt"), encoding="utf-8").read()
        if o == n:
            log.append(f"PASS  {name}: byte-identical")
        else:
            ok = False
            log.append(f"FAIL  {name}: outputs differ")
    text = "\n".join(log) + "\n"
    print(text)
    with open(os.path.join(TMP, "bitcheck.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
