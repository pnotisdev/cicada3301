# Relabel gate: 72 outer-alphabet sigmas x the library screen on the 0.7 window (first 300 runes),
# both key signs (mults 1,28), both anti-repeat models. This is H1 of work/log/phase11_review.md.
# Control (already on record, work/tmp/relabel_control.txt): planted sigma recovered at IoC 1.6702
# relabelled vs 1.0068-1.0637 unrelabelled; null <= 1.052; wrong sigma <= 1.055.
import sys, os, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
KS = os.path.join(HERE, "..", "kscreen")
sys.path.insert(0, KS)
import relabel_export as rx
sys.path.insert(0, os.path.join(HERE, ".."))
import lp

BIN = os.path.join(KS, "target", "release", "kscreen.exe")
LIB = os.path.join(KS, "data", "library.ksb")
SEGMENTS = os.path.join(KS, "data", "segments.txt")
GATE = os.path.join(HERE, "relabel_gate")
os.makedirs(GATE, exist_ok=True)

# extract the first (seg0.7) window block
with open(SEGMENTS, encoding="utf-8") as f:
    lines = [ln for ln in f.read().splitlines() if ln.strip()]
block = lines[:3]
assert block[0].startswith("W seg0.7"), block[0]
win07 = os.path.join(GATE, "seg07.txt")
with open(win07, "w", newline="\n", encoding="utf-8") as f:
    f.write("\n".join(block) + "\n")

specs = [f"aff:28:{r}" for r in range(29)]                    # 29 reflections (incl. Atbash r=28)
specs += [f"aff:{a}:0" for a in range(2, 28)]                 # 26 proper multipliers
specs += [f"kw:{kw}" for kw in lp.KEYWORDS]                   # 17 keyword alphabets
print(f"{len(specs)} sigma settings; window 0.7 (300 runes); mults 1,28; models 0,1")

summary = []
t0 = time.time()
for n, spec in enumerate(specs):
    name = rx.sigma_name(spec)
    win = os.path.join(GATE, f"w_{name}.txt")
    out = os.path.join(GATE, f"{name}.tsv")
    rx.relabel_windows_file(win07, rx.parse_sigma(spec), win)
    if os.path.exists(out):  # resume: skip finished sigmas
        with open(out, encoding="utf-8") as f:
            for ln in f:
                if ln.startswith("# best "):
                    summary.append((float(ln.split()[2]), spec, name))
        print(f"[{n+1}/{len(specs)}] {spec:18s} cached", flush=True)
        continue
    cmd = [BIN, "screen", win, f"file:{LIB}", out, "mults=1,28", "models=0,1"]
    best = None
    for attempt in range(3):
        try:
            subprocess.run(cmd, cwd=KS, capture_output=True, check=True)
            best = "-"
            with open(out, encoding="utf-8") as f:
                for ln in f:
                    if ln.startswith("# best "):
                        best = ln.split()[2]
            break
        except subprocess.CalledProcessError as e:
            print(f"  attempt {attempt+1} failed rc={e.returncode}, retrying", flush=True)
            time.sleep(2)
    if best is None:
        best = "ERR"
    else:
        summary.append((float(best), spec, name))
    print(f"[{n+1}/{len(specs)}] {spec:18s} best IoC {best}  ({time.time()-t0:.0f}s)", flush=True)

summary.sort(reverse=True)
with open(os.path.join(GATE, "summary.txt"), "w", encoding="utf-8") as f:
    f.write("best\tspec\n")
    for b, spec, name in summary:
        f.write(f"{b}\t{spec}\n")
print("top 10:")
for b, spec, name in summary[:10]:
    print(f"  {b}  {spec}")
print(f"done in {time.time()-t0:.0f}s; summary in {GATE}/summary.txt")
