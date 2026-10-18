"""Controls for the h5rs flat-library sweep extension (the file: KSB1 path).

Writes work/h5rs/campaign_control.txt with the commands (relative to the repo root), the
key outputs and PASS/FAIL. Run from the repo root.

(a) PLANT  - a totient+DIVINITY window (calib.py conventions: Self-Reliance 3000:3300,
    offset 1234, model 0, keep 0.19, seed 42 = data/truth.txt) swept through the NEW
    file: path over the totient stream of the real library_flat.ksb must find IoC 1.9856
    at exactly (offset 1234, L 8, model 0), and no other cell in the grid may reach 1.6.
    Cross-check: the unchanged tot path and `decode` must agree.
(b) NULL   - 4 random streams (null4.ksb, seeds 9000..9003) over a small grid, both
    models: max IoC < 1.45. Plus a grid-equivalence check: rand:9000 (the unchanged
    splitmix64 path) vs file:null4.ksb:rand:9000 (the Python-replicated stream) must
    produce identical per-cell IoCs across the whole small grid.
(c) READER - the KSB1 reader reproduces known streams: 'primes-1 (totient)' from
    library_flat.ksb must equal an independent prime sieve mod 29, and the Rust
    `h5rs totient` output must equal the same sieve (so file == internal totient).
"""
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

# command paths, relative to the repo root (kept relative in the recorded log)
EXE = "work/h5rs/target/release/h5rs.exe"
LIB = "work/kscreen/data/library_flat.ksb"
TRUTH = "work/h5rs/data/truth.txt"
WINS = "work/h5rs/data/lp2_windows.txt"
NULL4 = "work/h5rs/data/null4.ksb"
A_FILE = "work/h5rs/control_a_file.tsv"
A_TOT = "work/h5rs/control_a_tot.tsv"
B_TSV = "work/h5rs/control_b.tsv"
B_OLD = "work/h5rs/control_b_old.tsv"
B_NEW = "work/h5rs/control_b_new.tsv"
CONTROL_TXT = os.path.join(HERE, "campaign_control.txt")

lines = []
results = []


def log(s=""):
    lines.append(s)
    print(s)


def run(cmd, cwd=ROOT, timeout=900):
    log("$ " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)
    out = (p.stdout or "").strip()
    err = (p.stderr or "").strip()
    for tag, text in (("stdout", out), ("[stderr]", err)):
        if len(text) > 400:
            log(f"{tag} [{len(text)} chars, truncated] " + text[:200] + " ... " + text[-100:])
        elif text:
            log(text)
    log(f"[exit {p.returncode}]")
    return p.returncode, out, err


def check(name, ok, detail=""):
    results.append((name, ok, detail))
    log(f"== {name}: {'PASS' if ok else 'FAIL'} {detail}")


def sieve_primes(n):
    """Independent prime sieve (mirrors h5slice/h5rs logic, plain Python)."""
    if n < 8:
        return [2, 3, 5, 7, 11, 13, 17][:n]
    import math
    bound = int(n * (math.log(n) + math.log(math.log(n)))) + 16
    while True:
        m = bytearray(b"\x01") * (bound + 1)
        m[0] = m[1] = 0
        for i in range(4, bound + 1, 2):
            m[i] = 0
        for i in range(3, int(math.sqrt(bound)) + 1, 2):
            if m[i]:
                for j in range(i * i, bound + 1, i):
                    m[j] = 0
        ps = [i for i in range(bound + 1) if m[i]]
        if len(ps) >= n:
            return ps[:n]
        bound *= 2


def totient(n):
    return [(p - 1) % 29 for p in sieve_primes(n)]


def parse_ksb(path):
    b = open(path, "rb").read()
    assert b[:4] == b"KSB1", "not a KSB1 file"
    n = struct.unpack_from("<I", b, 4)[0]
    p = 8
    out = {}
    for _ in range(n):
        l = struct.unpack_from("<H", b, p)[0]
        p += 2
        name = b[p:p + l].decode("utf-8")
        p += l
        ln = struct.unpack_from("<I", b, p)[0]
        p += 4
        out[name] = b[p:p + ln]
        p += ln
    return out


def file_rows(tsv):
    """Parse the file: tsv rows: stream offset L model window IoC (skip # comments)."""
    rows = []
    for line in open(tsv, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if parts[0] == "best":
            continue
        name, off, L, m, win, ioc = parts
        rows.append((name, int(off), int(L), int(m), win, float(ioc)))
    return rows


# ------------------------------------------------------------------ (a) plant
log("# (a) plant: totient+DIVINITY window via the new file: path over library_flat.ksb")
run([EXE, "sweep", TRUTH, "file:" + LIB + ":primes-1 (totient)",
     "1233", "1236", "7", "10", "0", "1", A_FILE])
rows = file_rows(os.path.join(ROOT, A_FILE))
target = [r for r in rows if r[0] == "primes-1 (totient)" and r[1:4] == (1234, 8, 0)]
check("a-file-plant-found", len(target) == 1,
      f"row (1234, 8, 0) present exactly once: {target}")
check("a-file-ioc", len(target) == 1 and round(target[0][5], 4) == 1.9856,
      f"IoC = {target[0][5] if target else None} vs 1.9856 (4-dec rounded)")
others = [r for r in rows if r[1:4] != (1234, 8, 0)]
check("a-file-no-other-1.6", all(r[5] < 1.6 for r in others),
      f"grid rows: {[(r[1], r[2], r[3], round(r[5], 4)) for r in rows]}")
if rows:
    mx = max(rows, key=lambda r: r[5])
    log(f"  overall grid max: {(mx[1], mx[2], mx[3], mx[5])}")

run([EXE, "sweep", TRUTH, "tot", "1233", "1236", "7", "10", "0", "1", A_TOT])
best_tot = None
for line in open(os.path.join(ROOT, A_TOT), encoding="utf-8"):
    if line.startswith("truth\t"):
        parts = line.split("\t")
        best_tot = (float(parts[1]), int(parts[2]), int(parts[3]))
check("a-tot-agrees", best_tot is not None and round(best_tot[0], 4) == 1.9856
      and best_tot[1:] == (1234, 8), f"tot path best: {best_tot} vs (1.9856, 1234, 8)")

rc, out, _ = run([EXE, "decode", TRUTH, "1234", "8", "0"])
m = re.search(r"ioc=(\d+\.\d+)", out)
ioc_dec = float(m.group(1)) if m else 0.0
check("a-decode-agrees", m is not None and round(ioc_dec, 4) == 1.9856,
      f"decode: {out}")
check("a-three-paths-same-value", len(target) == 1 and best_tot is not None
      and m is not None and abs(target[0][5] - ioc_dec) < 1e-5
      and round(best_tot[0], 4) == round(ioc_dec, 4) == round(target[0][5], 4),
      "file: row IoC == tot sweep best == decode IoC (same f64)")

# ------------------------------------------------------------------ (b) null
log("# (b) null: 4 random streams (seeds 9000..9003), small grid, both models, --best")
run([EXE, "sweep", WINS, "file:" + NULL4, "0", "50", "2", "20", "2", "1", B_TSV, "--best"])
brows = file_rows(os.path.join(ROOT, B_TSV))
bbest = []
for line in open(os.path.join(ROOT, B_TSV), encoding="utf-8"):
    if line.startswith("best\t"):
        p = line.split("\t")
        bbest.append((p[1], int(p[2]), int(p[3]), int(p[4]), p[5], float(p[6])))
bmax = max((r[5] for r in bbest), default=0.0)
check("b-null-max-under-1.45", bmax < 1.45,
      f"max IoC over {4 * 8 * 50 * 19 * 2} null cells = {bmax:.4f} (< 1.45)")
log(f"  null rows >= 1.5: {len(brows)}; per-(stream,window,model) best cells: {len(bbest)}")

log("# (b2) grid equivalence: rand:9000 (old path) vs file:null4.ksb:rand-9000 (new path)")
run([EXE, "sweep", WINS, "rand:9000", "0", "50", "2", "20", "0", "1", B_OLD, "--hits", "0"])
run([EXE, "sweep", WINS, "file:" + NULL4 + ":rand-9000",
     "0", "50", "2", "20", "0", "1", B_NEW, "--hits", "0"])
old_cells = {}
win = None
for line in open(os.path.join(ROOT, B_OLD), encoding="utf-8"):
    line = line.rstrip("\n")
    if line.startswith("#"):
        continue
    parts = line.split("\t")
    if len(parts) == 6:  # window best_ioc off L model hits
        win = parts[0]
        continue
    if line.strip().startswith("hit"):
        p = line.split()
        old_cells.setdefault(win, []).append((int(p[2]), int(p[3]), float(p[1])))
new_cells = {}
for (name, off, L, m, w, ioc) in file_rows(os.path.join(ROOT, B_NEW)):
    new_cells.setdefault(w, []).append((off, L, round(ioc, 4)))
same = True
n = 0
for w in sorted(set(old_cells) | set(new_cells)):
    a = sorted(old_cells.get(w, []))
    b = sorted(new_cells.get(w, []))
    n += max(len(a), len(b))
    if a != b:
        same = False
        log(f"  MISMATCH window {w}: old {len(a)} cells vs new {len(b)} cells")
check("b2-rand-file-equivalent", same,
      f"all {n} cells of 8 windows x 50 offsets x 19 L identical (IoC to 4 decimals)")

# ------------------------------------------------------------------ (c) reader
log("# (c) KSB1 reader reproduces known streams: 'primes-1 (totient)'")
ksb = parse_ksb(os.path.join(ROOT, LIB))
check("c-lib-has-totient", "primes-1 (totient)" in ksb,
      f"{len(ksb)} streams parsed from library_flat.ksb")
t_file = list(ksb["primes-1 (totient)"])
t_sieve = totient(len(t_file))
check("c-file-equals-sieve", t_file == t_sieve,
      f"library totient ({len(t_file)} values) == independent sieve totient")

rc, out, _ = run([EXE, "totient", str(len(t_file))])
t_rust = [int(x) for x in out.split()]
check("c-rust-equals-sieve", t_rust == t_sieve,
      f"h5rs totient ({len(t_rust)} values) == independent sieve totient")
check("c-file-equals-rust", t_file == t_rust,
      "library totient == h5rs internal totient (so the file: path reads it correctly)")

# also cross-check the library structure: 581 streams, 'primes' first
check("c-streams-structure", len(ksb) == 581 and "primes" in ksb,
      f"581 streams, 'primes' present, names spot: {sorted(ksb)[:3]}")

# ------------------------------------------------------------------ verdict
npass = sum(1 for _, ok, _ in results if ok)
nfail = len(results) - npass
log("")
log(f"CONTROLS: {npass} PASS, {nfail} FAIL, {len(results)} checks")
header = [
    "# h5rs flat-library sweep extension - campaign controls (see CAMPAIGN.md)",
    "# all paths relative to the repo root; run `python work/h5rs/run_controls.py`",
    "",
]
with open(CONTROL_TXT, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(header + lines) + "\n")
print(f"\nwrote {CONTROL_TXT}")
sys.exit(1 if nfail else 0)
