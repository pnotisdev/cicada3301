# All-sections relabel run: 17 keyword alphabets + Atbash x the library on the 8 section windows,
# both key signs (mults 1,28), both anti-repeat models. H1 of work/log/phase11_review.md, part 2
# (the window-0.7 gate for the affine sigmas is already negative, work/tmp/relabel_gate/).
import sys, os, subprocess, time

HERE = os.path.dirname(os.path.abspath(__file__))
KS = os.path.join(HERE, "..", "kscreen")
sys.path.insert(0, KS)
import relabel_export as rx
sys.path.insert(0, os.path.join(HERE, ".."))
import lp

BIN = os.path.join(KS, "target", "release", "kscreen.exe")
LIB = os.path.join(KS, "data", "library.ksb")
SEGMENTS = os.path.join(HERE, "relabel_gate", "segments_frozen.txt")  # frozen copy incl. B lines
OUT = os.path.join(HERE, "..", "..", "results", "kscreen")

specs = ["atbash"] + [f"kw:{kw}" for kw in lp.KEYWORDS]  # 18 settings
print(f"{len(specs)} sigma settings, 8 section windows, mults 1,28, models 0,1")

summary = []
t0 = time.time()
for n, spec in enumerate(specs):
    name = rx.sigma_name(spec)
    win = os.path.join(KS, "data", "relabel", name, "segments.txt")
    out = os.path.join(OUT, f"relabel_all_{name}.tsv")
    rx.relabel_windows_file(SEGMENTS, rx.parse_sigma(spec), win)
    if os.path.exists(out):
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
with open(os.path.join(HERE, "relabel_all_summary.txt"), "w", encoding="utf-8") as f:
    f.write("best\tspec\n")
    for b, spec, name in summary:
        f.write(f"{b}\t{spec}\n")
print("top 10:")
for b, spec, name in summary[:10]:
    print(f"  {b}  {spec}")
print(f"done in {time.time()-t0:.0f}s; summary in work/tmp/relabel_all_summary.txt")
