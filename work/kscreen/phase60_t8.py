"""Phase 60 T8 (work/log/phase60_clue_review.md section 9): the 118,818,811-byte Cicada OS file DATA/560.13 and the 2013/2014 audio files as additive key streams on the plain kscreen
library screen (same engine, rule and controls as the library campaign: all 8 section-start n300 windows, mults 1 and 28, IoC >= 1.40 then verify.py).

 560.13 (uniformly random bytes, see the keyless check): maps = bytes mod 29 and bytes with rejection (>= 232 dropped), forwards and backwards.
   * start region: the first 30,000 offsets of each of the four streams (a pad read from its start; LP2 is 12,956 runes), every window, models 0 and 1;
   * sampled blocks: 30 blocks of 100,000 offsets of mod-forwards and 30 of rejection-forwards at fixed random positions (6.0 M of 118.8 M offsets = 5.05%, i.e. 2.5% per map).
 audio: 761.MP3, the 2014 Interconnectedness MP3 and c.mp3 stripped to frame payload bytes (phase60_t8_mp3.py), mod 29 forwards and backwards, every offset, model 0 only (cheap screen).
    python work/kscreen/phase60_t8.py build | controls | run | summary [--threads 3]
"""
import argparse
import os
import random
import re
import sys

import numpy as np

import pdir_ref as P
import selftest as S
import signrules as R

WORK = R.WORK
sys.path.insert(0, WORK)
import phase60_t8_mp3 as MP3  # noqa: E402

HERE = S.HERE
ROOT = S.ROOT
DATA = os.path.join(HERE, "data", "phase60_t8")
RES = os.path.join(ROOT, "results", "kscreen", "phase60_t8")
F560 = os.path.join(WORK, "ref", "cicados_iso", "560.13")
ARC = os.path.join(ROOT, "Other repositories and work", "The-Complete-Cicada3301-Archive", "assets")
AUDIO = {"761": os.path.join(ARC, "2013", "cicados", "AUDIO", "761.MP3"), "interconnectedness": os.path.join(ARC, "2014", "stage07", "index.mp3"),
         "c.mp3": os.path.join(ARC, "2014", "stage08", "index.3.mp3")}
START, BLOCK, NBLK = 30000, 100000, 30


def rel(p):
    return os.path.relpath(p, HERE).replace("\\", "/")


def maps(b):
    """name -> uint8 array of key values 0..28"""
    return {"mod": (b % 29).astype(np.uint8), "rej": (b[b < 232] % 29).astype(np.uint8)}


def block_positions(n, rng):
    return sorted(rng.randrange(START, n - BLOCK - 400) for _ in range(NBLK))


def build():
    os.makedirs(DATA, exist_ok=True)
    b = np.fromfile(F560, dtype=np.uint8)
    rng = random.Random(6013)
    items = []
    mm = maps(b)
    for mname, v in mm.items():
        items.append((f"b13 {mname} fwd start", v[:START + 400].tolist()))
        items.append((f"b13 {mname} rev start", v[::-1][:START + 400].tolist()))
        for pos in block_positions(len(v), rng):
            items.append((f"b13 {mname} fwd @{pos}", v[pos:pos + BLOCK + 300].tolist()))
    P.write_ksb(os.path.join(DATA, "b13.ksb"), items)
    aud, info = [], {}
    for name, f in AUDIO.items():
        p, inf = MP3.strip(open(f, "rb").read())
        info[name] = inf
        v = (p % 29).astype(np.uint8)
        aud.append((f"{name} mod fwd", v.tolist()))
        aud.append((f"{name} mod rev", v[::-1].tolist()))
    P.write_ksb(os.path.join(DATA, "audio.ksb"), aud)
    ctrl = [("audio-control slice", aud[2][1][:200000]), ("b13-control mod", mm["mod"][5_000_000:5_200_000].tolist())]
    P.write_ksb(os.path.join(DATA, "control.ksb"), ctrl)
    open(os.path.join(DATA, "audio_info.txt"), "w").write(repr(info) + "\n")
    print("b13 items", len(items), "audio items", len(aud), info)


def controls(threads):
    lines, ok = [], True
    for tag, f, item, off, mult, model in (("b13 start", "b13.ksb", "b13 mod fwd start", 5000, 28, 1), ("b13 rev start", "b13.ksb", "b13 rej rev start", 12000, 1, 0),
                                           ("b13 block", "b13.ksb", [n for n in ("b13 mod fwd @%d",)][0], 0, 0, 0),
                                           ("audio", "control.ksb", "audio-control slice", 100000, 1, 0), ("b13 control", "control.ksb", "b13-control mod", 150000, 28, 1)):
        if tag == "b13 block":
            sys.path.insert(0, os.path.join(WORK, "layer2")); from export import read_ksb
            blk = [n for n, v in read_ksb(os.path.join(DATA, f))][8]
            item, off, mult, model = blk, 60000, 1, 1
        plant = os.path.join(S.TMP, f"p60t8_{tag.replace(' ', '_')}.txt")
        tsv = plant[:-4] + ".tsv"
        S.run(["plant", rel(S.PLAIN), "file:" + rel(os.path.join(DATA, f)), item, str(off), str(mult), str(model), "0.18", str(800 + len(lines)), "0", rel(plant)])
        S.run(["screen", rel(plant), "file:" + rel(os.path.join(DATA, f)), rel(tsv), f"only={item}", f"threads={threads}"])
        best = S.window_bests(tsv)
        for win, (titem, toff) in S.truths(plant).items():
            ioc, bitem, boff = best.get(win, (0.0, "-", "-"))
            good = bitem == item and abs(int(boff) - int(toff)) <= 2 and ioc >= S.THRESHOLD
            ok &= good
            lines.append(f"{'PASS' if good else 'FAIL'}  {tag}: plant {item!r} mult={mult} model={model} {win}: best {ioc:.3f} at offset {boff} (truth {toff})")
    lines.append("PHASE60 T8 CONTROLS " + ("PASSED" if ok else "FAILED"))
    os.makedirs(RES, exist_ok=True)
    open(os.path.join(RES, "controls.txt"), "w", newline="\n").write("\n".join(lines) + "\n")
    print("\n".join(lines))


def screen(name, family, threads, extra=()):
    tsv = os.path.join(RES, name + ".tsv")
    if not os.path.exists(tsv):
        os.makedirs(RES, exist_ok=True)
        S.run(["screen", "data/segments.txt", "file:" + rel(os.path.join(DATA, family)), rel(tsv), f"threads={threads}", "top=200", *extra])
        print("done", name, flush=True)


def run(threads):
    screen("b13", "b13.ksb", threads)
    screen("audio", "audio.ksb", threads, ("models=0",))


def summary():
    lines = []
    for f in sorted(os.listdir(RES)):
        if f.endswith(".tsv"):
            t = open(os.path.join(RES, f), encoding="utf-8", errors="replace").read().split("\n")
            hd = t[0]
            best = [l for l in t if l.startswith("# best")][0]
            lines.append(f"{f[:-4]}: {best}  runs={re.search(r'runs=(\d+)', hd).group(1)}  secs={re.search(r'secs=(\d+)', hd).group(1)}")
            lines += [l for l in t if l.startswith("# window")]
            top = [l for l in t if l and not l.startswith("#") and not l.startswith("ioc")][:3]
            lines += ["   top: " + l for l in top]
    t = "\n".join(lines) + "\n"
    open(os.path.join(RES, "summary.txt"), "w", newline="\n").write(t)
    print(t)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd"); ap.add_argument("--threads", type=int, default=3)
    a = ap.parse_args()
    os.makedirs(S.TMP, exist_ok=True)
    {"build2": lambda: None, "run2": lambda: None, "build": build, "controls": lambda: controls(a.threads), "run": lambda: run(a.threads), "summary": summary}[a.cmd]()


def build2():
    """second batch of sampled blocks for 560.13: 50 more blocks of 100,000 offsets for each of the two forward maps (another 10.0 M offsets), new seed"""
    b = np.fromfile(F560, dtype=np.uint8)
    rng = random.Random(60132)
    items = []
    for mname, v in maps(b).items():
        for pos in sorted(rng.randrange(START, len(v) - BLOCK - 400) for _ in range(50)):
            items.append((f"b13 {mname} fwd @{pos}", v[pos:pos + BLOCK + 300].tolist()))
    P.write_ksb(os.path.join(DATA, "b13b.ksb"), items)
    print("b13b items", len(items))


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] in ("build2", "run2"):
    if sys.argv[1] == "build2":
        build2()
    else:
        os.makedirs(S.TMP, exist_ok=True)
        screen("b13b", "b13b.ksb", 3)
