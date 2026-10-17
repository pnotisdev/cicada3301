#!/usr/bin/env python3
"""Overnight campaign runner for the Liber Primus LP2 attacks: long tests and brute-force searches with
positive controls, resume, logs and an automatic report.

    python jobs/overnight.py list                          # campaigns, steps, rough hours, what is done
    python jobs/overnight.py run                           # everything, in priority order
    python jobs/overnight.py run kscreen-sections dsearch  # selected campaigns
    python jobs/overnight.py run --hours 9                 # stop starting new steps after 9 hours
    python jobs/overnight.py report                        # rewrite results/overnight/<machine>/REPORT.md

Options: --threads N (default: all logical CPUs), --force (rerun finished steps), --dry-run.

Resume: a step counts as finished when its output files exist (they are written only at the end), so a run
can be stopped at any time (Ctrl+C, reboot) and restarted; only the interrupted step starts over. Setup steps
(cargo builds, data export) always run and are fast when nothing changed. State, logs and report live in
results/overnight/<machine>/ (committed; one folder per PC, so pushes from two PCs never conflict).

Discipline: every campaign starts with, or depends on, positive controls (planted keys that must be recovered)
and null controls (random keys under identical settings). A campaign's null result is only reported as
validated when its controls passed. See docs/CAMPAIGNS.md for what each campaign tests and why.
"""
import argparse
import json
import os
import platform
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field, replace
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
RES = ROOT / "results"
# Each machine keeps its own runner state, logs and report under results/overnight/<alias>/ (committed), so two
# PCs can push without conflicts. The alias is never the real computer name, because the repository may become
# public. It is LP_MACHINE if set, else the name in the git-ignored file .lp_machine (e.g. "laptop", "desktop"),
# else a random alias that is saved there on first use.
def machine_alias():
    clean = lambda s: re.sub(r"[^A-Za-z0-9_.-]", "_", s.strip())[:40]
    if os.environ.get("LP_MACHINE", "").strip():
        return clean(os.environ["LP_MACHINE"])
    f = ROOT / ".lp_machine"
    if f.exists() and f.read_text(encoding="utf-8").strip():
        return clean(f.read_text(encoding="utf-8"))
    import secrets
    alias = "pc-" + secrets.token_hex(3)
    f.write_text(alias + "\n", encoding="utf-8")
    print(f"note: this PC's runner folder will be results/overnight/{alias}/ (change the name in .lp_machine)")
    return alias


MACHINE = machine_alias()
_HOST = platform.node()


def scrub(text):
    """Remove this PC's identity from text bound for tracked files: repository path, home folder, host name."""
    for p, rep in ((str(ROOT), "<repo>"), (str(Path.home()), "~")):
        forms = {p, p.replace("\\", "/"), p.replace("\\", "\\\\")}     # as is, forward slashes, repr()-escaped
        if p[1:2] == ":":
            forms.add("/" + p[0].lower() + p[2:].replace("\\", "/"))   # Git Bash style /c/...
        for v in sorted(forms, key=len, reverse=True):
            text = text.replace(v, rep)
    if len(_HOST) >= 5:                                  # a very short host name would match ordinary words
        text = re.sub(re.escape(_HOST), "<host>", text, flags=re.IGNORECASE)
    return text


def scrub_file(path):
    p = Path(path)
    if not p.exists() or p.stat().st_size > 50_000_000:
        return
    try:
        t = p.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return
    s = scrub(t)
    if s != t:
        p.write_text(s, encoding="utf-8", newline="\n")
OV = RES / "overnight"
OVM = OV / MACHINE
SELFTEST = OVM / "kscreen_selftest.txt"
UNITTESTS = OVM / "unittests.ok"
LOGS = OVM / "logs"
STATE = OVM / "state.json"
EXE = ".exe" if os.name == "nt" else ""
PY = sys.executable
KS = WORK / "kscreen"
KS_BIN = KS / "target" / "release" / f"kscreen{EXE}"
PHPMT_BIN = WORK / "phpmt" / "target" / "release" / f"phpmt{EXE}"
WALK_BIN = WORK / "walk" / "target" / "release" / f"walk{EXE}"
LIN3_CHUNKS = 24
KS_GPU = KS / "gpu.py"
PH_GPU = WORK / "phpmt" / "gpu.py"
SELFTEST_CUDA = OVM / "kscreen_selftest_cuda.txt"
GPU_VALIDATION = OVM / "gpu_validation.txt"
CHAIN_SELFTEST = OVM / "chain_selftest.txt"
L2 = WORK / "layer2"
L2_BIN = L2 / "target" / "release" / f"layer2{EXE}"
L2_SELFTEST = OVM / "layer2_selftest.txt"
DEVICE = "cpu"                   # the device campaigns are built for: "cuda" only after detect_device() validated it
LANE = "main"                    # runner lane: lanes have their own lock, so a GPU lane and a CPU lane can run together
# measured on the 2080 Ti against the 16-thread Ryzen 7 2700X (work/log/phase8_gpu.md); only scale the --hours estimates
GPU_SPEEDUP = {"kscreen": 3.0, "prng": 7.0}


@dataclass
class Step:
    id: str
    cmd: object                      # list of args, or a Python callable(log) -> bool
    cwd: Path = ROOT
    hours: float = 0.1               # rough estimate on a 16-thread desktop CPU
    outputs: list = field(default_factory=list)
    always: bool = False             # setup steps: run every time
    done_check: object = None        # extra completion test: callable() -> bool
    stdout_to: Path = None
    stderr_to: Path = None
    post: object = None              # callable() run after success (e.g. copy results into results/)
    device: str = "cpu"              # shown in the console prefix: "cpu" or "cuda"
    alt: object = None               # CPU command to rerun the step with if the CUDA run fails

    def done(self):
        if self.always:
            return False
        if not self.outputs and self.done_check is None:
            return False
        if not all(Path(p).exists() and Path(p).stat().st_size > 0 for p in self.outputs):
            return False
        return self.done_check() if self.done_check else True


@dataclass
class Campaign:
    name: str
    title: str
    why: str
    steps: list
    summarize: object = None         # callable() -> list of markdown lines


# ---------------------------------------------------------------- helpers

def ks_screen(cid, name, windows, family, out, threads, extra=(), hours=0.5):
    tsv = RES / "kscreen" / out
    cpu = [str(KS_BIN), "screen", windows, family, str(tsv), f"threads={threads}", *extra]
    if DEVICE == "cuda":
        gpu = [PY, str(KS_GPU), "screen", windows, family, str(tsv), *extra]
        return Step(f"{cid}/{name}", gpu, cwd=KS, hours=hours / GPU_SPEEDUP["kscreen"], outputs=[tsv], device="cuda", alt=cpu)
    return Step(f"{cid}/{name}", cpu, cwd=KS, hours=hours, outputs=[tsv])


def ks_verify(cid, name, tsv_name, top=15, hours=0.05):
    tsv = RES / "kscreen" / tsv_name
    out = RES / "kscreen" / tsv_name.replace(".tsv", "_verify.txt")
    return Step(f"{cid}/{name}", [PY, str(KS / "verify.py"), str(tsv), "--top", str(top), "--out", str(out)],
                hours=hours, outputs=[out])


def l2_screen(cid, name, windows, family, out, threads, extra=(), hours=0.5):
    tsv = RES / "layer2" / out
    return Step(f"{cid}/{name}", [str(L2_BIN), "screen", windows, family, str(tsv), f"threads={threads}", *extra],
                cwd=L2, hours=hours, outputs=[tsv])


def l2_verify(cid, name, tsv_name, top=15, hours=0.1):
    tsv = RES / "layer2" / tsv_name
    out = RES / "layer2" / tsv_name.replace(".tsv", "_verify.txt")
    return Step(f"{cid}/{name}", [PY, str(L2 / "verify.py"), str(tsv), "--top", str(top), "--out", str(out)],
                cwd=L2, hours=hours, outputs=[out])


def l2_summary():
    out = [f"- controls: {last_line(L2_SELFTEST) or 'not run'}"]
    for label, name, unit in (("null: 20 random streams x the solved keys (bigram)", "null_bigram_solved.tsv", "per rune"),
                              ("core streams x the solved keys DIVINITY / FIRFUMFERENFE / CIRCUMFERENCE (bigram)", "bigram_solved.tsv", "per rune"),
                              ("20 Cicada streams x 30 Cicada keywords (bigram)", "bigram_words.tsv", "per rune"),
                              ("core streams x any keyword of period 2-14 (column z)", "periodic_core.tsv", "z"),
                              ("variant A1: 20 streams with a solved key folded in, one pointer (bigram)", "bigram_combined.tsv", "per rune")):
        p = RES / "layer2" / name
        if not p.exists():
            out.append(f"- {label}: not run yet")
            continue
        head = open(p, encoding="utf-8").readline()
        m = re.search(r"runs=(\d+).*secs=(\d+)", head)
        best = next((l.split()[2] for l in open(p, encoding="utf-8") if l.startswith("# best")), "?")
        out.append(f"- {label}: best {best} {unit}" + (f" ({int(m.group(1)):,} decodes in {int(m.group(2)) / 60:.0f} min)" if m else ""))
        v = last_line(RES / "layer2" / name.replace(".tsv", "_verify.txt"), r"re-decoded hits pass")
        if v:
            out.append(f"  - verification: {v}")
    return out


PX = WORK / "prngx"
PT_OUT = RES / "prngx" / "time"                     # CPU engine (work/prngx/time_campaign.py)
PT_GPU_OUT = RES / "prng" / "time_gpu"              # 64-bit CUDA port (work/phpmt/time_gpu.py, bg64.py)
PT_GATE = OVM / "prng_time_gate.txt"
PT_GPU_GATE = OVM / "prng_time_gpu_gate.txt"
# (generator, seeds/s): GPU rates measured on the 2080 Ti (work/log/phase10_prng_time_gpu.md); CPU rates per thread on the laptop.
# ruby: CPython's MT19937 with Ruby's documented seeding and rand(n) rule, NOT checked against a Ruby (none on either machine)
PT_GPU_GENS = (("java", 10.8e6), ("py3", 6.4e6), ("java-abs", 10.8e6), ("ruby", 6.4e6))
PT_CPU_GENS = (("java", 12_000), ("pymt", 10_000))


def prng_time_steps(T):
    """one step per (month, generator), newest month first. On a validated GPU (DEVICE cuda): the desktop's 64-bit port of the
    boundary-free sweep, work/phpmt/time_gpu.py, behind its gate test_bgmt64 (about 9 h for the whole window and all four generators).
    Otherwise the CPU engine, work/prngx/time_campaign.py, behind test_prngx_time (about 210 h: run the newest months with --hours).
    Both gates go through work/tests/run_gate.py, which fails when a test is skipped (a missing build or table)."""
    sys.path.insert(0, str(PX))
    import time_campaign
    if DEVICE == "cuda":
        steps = [Step("prng-time/gpu-gate", [PY, "work/tests/run_gate.py", "work.tests.test_bgmt64"], hours=0.05, outputs=[PT_GPU_GATE],
                      always=True, stdout_to=PT_GPU_GATE, device="cuda")]
        for lab, lo, hi in time_campaign.months():
            for gen, rate in PT_GPU_GENS:
                log, ver = PT_GPU_OUT / f"{gen}_{lab}.log", PT_GPU_OUT / f"{gen}_{lab}_verify.txt"
                steps.append(Step(f"prng-time/{gen}-{lab}", [PY, str(WORK / "phpmt" / "time_gpu.py"), "run", gen, "--only", lab],
                                  hours=(hi - lo) / rate / 3600, outputs=[ver], device="cuda",
                                  done_check=lambda log=log: log.exists() and "swept" in log.read_text(encoding="utf-8", errors="replace")))
        return steps
    steps = [Step("prng-time/build", ["cargo", "build", "--release", "--manifest-path", str(PX / "Cargo.toml")], always=True, hours=0.02),
             Step("prng-time/vectors", [str(PX / "target" / "release" / f"prngx{EXE}"), "vectors", "ref/vectors.txt"], cwd=PX, hours=0.01,
                  outputs=[OVM / "prng_time_vectors.txt"], stdout_to=OVM / "prng_time_vectors.txt",
                  done_check=lambda: " 0 mismatch" in (last_line(OVM / "prng_time_vectors.txt") or "")),
             # gate: independent vectors and keys, timestamp seeds planted with independent keys found at rank 1, random ciphertext
             # without candidates, the whole-section check works; fails on a skipped test
             Step("prng-time/gate", [PY, "work/tests/run_gate.py", "work.tests.test_prngx_time"], hours=0.02, outputs=[PT_GATE],
                  always=True, stdout_to=PT_GATE)]
    for lab, lo, hi in time_campaign.months():
        for gen, rate in PT_CPU_GENS:
            tsv, _, ver = time_campaign.paths(gen, lab)
            steps.append(Step(f"prng-time/{gen}-{lab}", [PY, str(PX / "time_campaign.py"), "run", gen, lab, "--threads", str(T)],
                              hours=(hi - lo) / (rate * 16) / 3600, outputs=[Path(tsv), Path(ver)]))
    return steps


def prng_time_summary():
    import glob
    out = [f"- gate on {MACHINE}: GPU {last_line(PT_GPU_GATE) or 'not run'}; CPU {last_line(PT_GATE) or 'not run'}",
           f"- generator vectors (Java 48-bit and CPython two-word seeds): {last_line(OVM / 'prng_time_vectors.txt') or 'not run'}"]
    month = re.compile(r"_\d{4}-\d{2}_verify\.txt$")
    for where, folder, gens in (("GPU", PT_GPU_OUT, [g for g, _ in PT_GPU_GENS]), ("CPU", PT_OUT, [g for g, _ in PT_CPU_GENS])):
        for gen in gens:
            vers = sorted(v for v in glob.glob(str(folder / f"{gen}_*_verify.txt")) if month.search(v))
            if not vers:
                continue
            cands = [Path(v).name for v in vers if "CANDIDATE" in open(v, encoding="utf-8").read()]
            out.append(f"- {where} {gen}{' (Ruby rule unverified)' if gen == 'ruby' else ''}: {len(vers)} of 25 months done; candidates after the "
                       f"whole-section check: {', '.join(cands) if cands else 'none'}")
    if len(out) == 2:
        out.append("- no month swept yet")
    return out


def ks_best(tsv_name):
    p = RES / "kscreen" / tsv_name
    if not p.exists():
        return None
    for line in open(p, encoding="utf-8"):
        m = re.match(r"# best ([\d.]+)", line)
        if m:
            return float(m.group(1))
    return None


def ks_header(tsv_name):
    p = RES / "kscreen" / tsv_name
    if not p.exists():
        return ""
    line = open(p, encoding="utf-8").readline().strip()
    m = re.search(r"runs=(\d+).*secs=(\d+)", line)
    return f"{int(m.group(1)):,} decodes in {int(m.group(2)) / 60:.0f} min" if m else ""


def last_line(path, pattern=None):
    p = Path(path)
    if not p.exists():
        return None
    lines = [l.rstrip() for l in open(p, encoding="utf-8", errors="replace") if l.strip()]
    if pattern:
        lines = [l for l in lines if re.search(pattern, l)]
    return lines[-1] if lines else None


def ks_summary(screens, null_name, verify_names):
    out = []
    nb = ks_best(null_name) if null_name else None
    for label, name in screens:
        b = ks_best(name)
        if b is None:
            out.append(f"- {label}: not run yet")
            continue
        flag = "**above threshold, see verification**" if b >= 1.40 else "below the 1.40 threshold"
        out.append(f"- {label}: best IoC {b:.3f} ({flag}; {ks_header(name)})")
    if nb is not None:
        out.append(f"- matched null (random keystreams, same windows/settings): best {nb:.3f}")
    for v in verify_names:
        line = last_line(RES / "kscreen" / v, r"re-decoded hits")
        if line:
            out.append(f"- verification ({v}): {line}")
    return out


def chain_summary(prefix="", avals=range(1, 29)):
    out = [f"- controls: {last_line(CHAIN_SELFTEST) or 'not run'}"]
    allv, flagged = [], []
    for a in avals:
        v = {n: ks_best(f"chain/{prefix}{n}_a{a}.tsv") for n in ("library", "lin2", "poly3", "null")}
        if all(x is None for x in v.values()):
            continue
        allv.append((a, v))
        if any((x or 0) >= 1.40 for n, x in v.items() if n != "null"):
            flagged.append(a)
    if not allv:
        return out + ["- not run yet"]
    f = lambda x: "-" if x is None else f"{x:.3f}"
    out.append(f"- {len(allv)}/{len(avals)} multipliers done. best IoC per multiplier (library / order-2 recurrences / cubic polynomials; matched null):")
    for a, v in allv:
        out.append(f"  - a={a:2d}: {f(v['library'])} / {f(v['lin2'])} / {f(v['poly3'])}; null {f(v['null'])}")
    mx = max(((v[n] or 0, a, n) for a, v in allv for n in ("library", "lin2", "poly3")), default=(0, 0, ""))
    out.append(f"- largest: {mx[0]:.3f} (a={mx[1]}, {mx[2]})" + ("; above 1.40 for a = " + ", ".join(map(str, flagged)) + ": see the verification files" if flagged else "; none reaches the 1.40 threshold"))
    for a, _ in allv:
        line = last_line(RES / "kscreen" / "chain" / f"{prefix}library_a{a}_verify.txt", r"re-decoded hits")
        if line and ("0 of" not in line):
            out.append(f"  - a={a} verification: {line}")
    return out


def first_data_line(path):
    """the first line of a file that is not a '#' header: the best-ranked row of a verification listing"""
    p = Path(path)
    if not p.exists():
        return None
    for l in open(p, encoding="utf-8", errors="replace"):
        if l.strip() and not l.startswith("#"):
            return l.rstrip()
    return None


STEP28_SELFTEST = OVM / "step28_selftest.txt"
STEP28_NULLS = 4


def step28_steps():
    """step-domain (relative-rank) chain screen: CUDA only, the CPU engine is a reference for the controls"""
    if DEVICE != "cuda":
        return []
    S28 = [PY, str(KS / "step28.py")]
    lib = RES / "kscreen" / "step28_library.tsv"
    steps = [
        Step("kscreen-step28/controls", S28 + ["selftest", "--engine", "cuda"], hours=0.02, outputs=[STEP28_SELFTEST],
             always=True, device="cuda", stdout_to=STEP28_SELFTEST),
        Step("kscreen-step28/library", S28 + ["screen", str(KS / "data" / "library.ksb"), str(lib)], hours=0.05, outputs=[lib],
             device="cuda"),
    ]
    for r in range(STEP28_NULLS):
        nul = RES / "kscreen" / f"step28_null{r}.tsv"
        steps.append(Step(f"kscreen-step28/null{r}", S28 + ["screen", f"rand:655:{700 + r}", str(nul)], hours=0.05,
                          outputs=[nul], device="cuda"))
    ver = RES / "kscreen" / "step28_library_verify.txt"
    steps.append(Step("kscreen-step28/verify", S28 + ["verify", str(lib), "--top", "8", "--out", str(ver)], hours=0.01, outputs=[ver]))
    # the same families built natively mod 28 (variants A and C read Z28 keys; work/kscreen/export28.py)
    l28 = KS / "data" / "library28.ksb"
    t28 = RES / "kscreen" / "step28_library28.tsv"
    steps.append(Step("kscreen-step28/export28", [PY, str(KS / "export28.py")], hours=0.05, outputs=[l28]))
    steps.append(Step("kscreen-step28/library28", S28 + ["screen", str(l28), str(t28), "--variants", "AC"], hours=0.05, outputs=[t28],
                      device="cuda"))
    for r in range(2):
        nul = RES / "kscreen" / f"step28_null28_{r}.tsv"
        steps.append(Step(f"kscreen-step28/null28-{r}", S28 + ["screen", f"rand:655:{800 + r}", str(nul), "--variants", "AC"], hours=0.05,
                          outputs=[nul], device="cuda"))
    v28 = RES / "kscreen" / "step28_library28_verify.txt"
    steps.append(Step("kscreen-step28/verify28", S28 + ["verify", str(t28), "--top", "8", "--out", str(v28)], hours=0.01, outputs=[v28]))
    per = RES / "analysis" / "step_periodicity.txt"
    steps.append(Step("kscreen-step28/periodicity", [PY, str(WORK / "step_periodicity.py")], hours=0.05, outputs=[per]))
    return steps


def step28_summary():
    lib = RES / "kscreen" / "step28_library.tsv"
    if not lib.exists():
        return ["- not run yet (CUDA only)"]
    pat = re.compile(r"# window (\S+) best ([\d.]+) variant=(\w) mode=(\w+) m=(\d+)")

    def bests(p):
        return {m.group(1): float(m.group(2)) for m in map(pat.match, p.read_text(encoding="utf-8").splitlines()) if m}

    lb = bests(lib)
    nulls = [bests(RES / "kscreen" / f"step28_null{r}.tsv") for r in range(STEP28_NULLS)
             if (RES / "kscreen" / f"step28_null{r}.tsv").exists()]
    out = [f"- controls: {last_line(STEP28_SELFTEST) or 'not run'}"]
    top = max(lb.items(), key=lambda kv: kv[1])
    out.append(f"- {len(lb)} windows of 300 steps, 1,447 library streams x every offset x variants A/B/C x modes drop/keep x 12 multipliers: "
               f"best IoC {top[1]:.3f} ({top[0]})")
    if nulls:
        nmax = {w: max(n.get(w, 0) for n in nulls) for w in lb}
        above = [w for w in lb if lb[w] > nmax[w] + 0.02 and lb[w] >= 1.30]
        out.append(f"- matched null ({len(nulls)} replicates of random streams, same pair count): largest per-window best "
                   f"{max(nmax.values()):.3f}; windows where the library beats every replicate by 0.02 and reaches 1.30: "
                   + (", ".join(above) if above else "none"))
    t28 = RES / "kscreen" / "step28_library28.tsv"
    if t28.exists():
        n28 = [bests(RES / "kscreen" / f"step28_null28_{r}.tsv") for r in range(2) if (RES / "kscreen" / f"step28_null28_{r}.tsv").exists()]
        b28 = bests(t28)
        top28 = max(b28.items(), key=lambda kv: kv[1])
        out.append(f"- native mod-28 library (variants A and C, keys 0..27; export28.py): best IoC {top28[1]:.3f} ({top28[0]}); "
                   f"largest per-window best in {len(n28)} null replicates: {max((max(n.values()) for n in n28), default=0):.3f}")
        v28 = first_data_line(RES / "kscreen" / "step28_library28_verify.txt")
        if v28:
            out.append(f"- verification of the native library (best-ranked window): {v28}")
    ver = first_data_line(RES / "kscreen" / "step28_library_verify.txt")
    if ver:
        out.append(f"- verification (the best-ranked window continued to the end of its section): {ver}")
    per = RES / "analysis" / "step_periodicity.txt"
    if per.exists():
        out.append(f"- periodic keys (coincidences at lag 2..3000, planted controls and a structured null): "
                   f"{last_line(per, r'largest z of all scopes') or ''}; {last_line(per, r'^controls') or ''}")
    return out


BG_GENS = ("py3", "java", "php", "glibc", "mt32", "msvc", "drand48", "ruby", "mt31", "net")      # by speed of sweep and plausibility
BG_SELFTEST = OVM / "prng_bg_selftest.txt"


def prng_bg_steps(T, tags=("07",)):
    """seed sweeps with the boundary-free bigram score (work/phpmt/bg.py): CUDA only"""
    if DEVICE != "cuda":
        return []
    steps = [Step("prng-bg/controls", [PY, "work/tests/run_gate.py", "work.tests.test_bgmt"], hours=0.02, outputs=[BG_SELFTEST],
                  always=True, stdout_to=BG_SELFTEST, device="cuda")]
    for tag in tags:
        for gen in BG_GENS:
            tsv = RES / "prng" / f"bg_{gen}_{tag}.tsv"
            log = RES / "prng" / f"bg_{gen}_{tag}.log"
            ver = RES / "prng" / f"bg_{gen}_{tag}_verify.txt"
            hi = 2 ** 31 if gen == "net" else 2 ** 32
            done = lambda log=log: "swept" in log.read_text(encoding="utf-8", errors="replace") if log.exists() else False
            steps.append(Step(f"prng-bg/{gen}-{tag}", [PY, str(WORK / "phpmt" / "bg.py"), "sweep", gen, tag, "0", str(hi), str(tsv)],
                              hours=0.3 if tag == "07" else 2.0, outputs=[tsv], stderr_to=log, done_check=done, device="cuda"))
            steps.append(Step(f"prng-bg/{gen}-{tag}-verify", [PY, str(WORK / "phpmt" / "bg.py"), "verify", str(tsv), "--gen", gen],
                              hours=0.05, outputs=[ver], stdout_to=ver))
    return steps


def prng_bg_summary(tags=("07",)):
    out = [f"- controls (a skipped test counts as failed): {last_line(BG_SELFTEST, r'^GATE') or 'not run'}"]
    for tag in tags:
        for gen in BG_GENS:
            sw = last_line(RES / "prng" / f"bg_{gen}_{tag}.log", "swept")
            ver = first_data_line(RES / "prng" / f"bg_{gen}_{tag}_verify.txt")
            out.append(f"- {gen} ({tag}): {sw or 'not run'}" + (f"; best-ranked candidate: {ver}" if ver else ""))
    return out


STEP_GENS = ("py3", "php", "glibc", "java", "mt32", "net", "msvc", "drand48", "ruby", "mt31")
STEP_SELFTEST = OVM / "prng_step_selftest.txt"


def prng_step_steps():
    """seed sweeps of the step-domain cipher: CUDA only (2^32 seeds x 144 settings x 2 windows per generator is about 2.5 hours on the GPU)"""
    if DEVICE != "cuda":
        return []
    steps = [Step("prng-step/controls", [PY, "work/tests/run_gate.py", "work.tests.test_stepmt"], hours=0.02, outputs=[STEP_SELFTEST],
                  always=True, stdout_to=STEP_SELFTEST, device="cuda")]
    for gen in STEP_GENS:
        tsv = RES / "prng" / f"step_{gen}_07.tsv"
        log = RES / "prng" / f"step_{gen}_07.log"
        ver = RES / "prng" / f"step_{gen}_07_verify.txt"
        done = lambda log=log: "swept" in log.read_text(encoding="utf-8", errors="replace") if log.exists() else False
        steps.append(Step(f"prng-step/{gen}", [PY, str(WORK / "phpmt" / "step.py"), "sweep", gen, "07", "0", str(2 ** 32), str(tsv)],
                          hours=2.8, outputs=[tsv], stderr_to=log, done_check=done, device="cuda"))
        steps.append(Step(f"prng-step/{gen}-verify", [PY, str(WORK / "phpmt" / "step_verify.py"), str(tsv), "--gen", gen],
                          hours=0.05, outputs=[ver], stdout_to=ver))
    return steps


def prng_step_summary():
    out = [f"- controls (a skipped test counts as failed): {last_line(STEP_SELFTEST, r'^GATE') or 'not run'}"]
    for gen in STEP_GENS:
        sw = last_line(RES / "prng" / f"step_{gen}_07.log", "swept")
        ver = first_data_line(RES / "prng" / f"step_{gen}_07_verify.txt")
        out.append(f"- {gen}: {sw or 'not run'}" + (f"; best-ranked candidate: {ver}" if ver else ""))
    return out


def selftest_ok():
    return SELFTEST.exists() and "SELFTEST PASSED" in SELFTEST.read_text(encoding="utf-8")


# ---------------------------------------------------------------- campaigns

def campaigns(threads):
    T = threads
    C = []

    C.append(Campaign(
        "setup", "Build engines and data",
        "Cargo builds of the three Rust engines and the generated inputs (fast when nothing changed).",
        [
            Step("setup/build-phpmt", ["cargo", "build", "--release", "--manifest-path", str(WORK / "phpmt" / "Cargo.toml")], always=True, hours=0.02),
            Step("setup/build-walk", ["cargo", "build", "--release", "--manifest-path", str(WORK / "walk" / "Cargo.toml")], always=True, hours=0.02),
            Step("setup/build-kscreen", ["cargo", "build", "--release", "--manifest-path", str(KS / "Cargo.toml")], always=True, hours=0.02),
            Step("setup/fetch-data", [PY, "scripts/fetch_data.py"], always=True, hours=0.02),
            Step("setup/data-phpmt", [PY, "work/phpmt/export_data.py"], hours=0.02,
                 outputs=[WORK / "phpmt" / "data" / f for f in ("windows.txt", "windows_07.txt", "dict.txt", "english.txt")]),
            Step("setup/data-walk", [PY, "work/walk/make_data.py"], hours=0.02,
                 outputs=[WORK / "walk" / "data" / f for f in ("lm3.bin", "lp2.txt", "english_test.txt")]),
            Step("setup/data-kscreen", [PY, "work/kscreen/export.py"], hours=0.1,
                 outputs=[KS / "data" / f for f in ("segments.txt", "heads.txt", "pages.txt", "library.ksb")]),
        ]))

    C.append(Campaign(
        "selftest", "Regression tests and keystream-screen controls",
        "The 71 unit tests (solved pages, transcription, statistics, engines) and the kscreen plant/recover and "
        "random-key null. Nothing else is trusted unless this passes.",
        [
            Step("selftest/unittests", [PY, "-m", "unittest", "discover", "-s", "work/tests"], hours=0.1,
                 outputs=[UNITTESTS]),
            # always rerun: it validates this machine's build, and its result file may come from another machine
            Step("selftest/kscreen-controls", [PY, str(KS / "selftest.py"), "--threads", str(T), "--out", str(SELFTEST)],
                 hours=0.05, outputs=[SELFTEST], always=True),
        ],
        lambda: [f"- unit tests on {MACHINE}: {'passed' if UNITTESTS.exists() else 'not passed yet'}",
                 f"- kscreen controls on {MACHINE}: {last_line(SELFTEST) or 'not run'}"]
                + ([f"- kscreen controls through the CUDA port on {MACHINE}: {last_line(SELFTEST_CUDA) or 'not run'}",
                    f"- GPU validation on {MACHINE}: {last_line(GPU_VALIDATION) or 'not run'}"] if SELFTEST_CUDA.exists() else [])))

    C.append(Campaign(
        "analysis", "Fingerprint analyses",
        "Drift-aware periodic-key scan (the old lag scan cannot see periods beyond ~60 under the skip rule) and "
        "the word-length model test (LP2 has too few 2-rune words for English in runes).",
        [
            Step("analysis/drift-period", [PY, "work/drift_period.py"], hours=0.4,
                 outputs=[RES / "analysis" / "drift_period.tsv", RES / "analysis" / "drift_period.txt"],
                 stdout_to=RES / "analysis" / "drift_period.txt"),
            Step("analysis/wordlen", [PY, "work/wordlen.py"], hours=0.02, outputs=[RES / "analysis" / "wordlen.txt"]),
        ],
        lambda: [f"- drift period scan: {last_line(RES / 'analysis' / 'drift_period.txt', 'verdict') or 'not run'}",
                 f"- word lengths: {last_line(RES / 'analysis' / 'wordlen.txt', 'null rune') or 'not run'}"]))

    C.append(Campaign(
        "kscreen-sections", "Keystream library at every offset, LP2 sections",
        "1,447 keystreams (number theory, constants, Cicada numbers, hash streams of Cicada strings and of the "
        "corrected payload) at every start offset, both key signs, both anti-repeat models, scored by IoC: any "
        "plaintext language, any substituted plaintext alphabet.",
        [
            ks_screen("kscreen-sections", "null", "data/segments.txt", "rand:300:11", "null_segments.tsv", T, hours=0.3),
            ks_screen("kscreen-sections", "library", "data/segments.txt", "file:data/library.ksb", "library_segments.tsv", T, hours=0.4),
            ks_verify("kscreen-sections", "verify", "library_segments.tsv"),
        ],
        lambda: ks_summary([("library x 8 sections", "library_segments.tsv")], "null_segments.tsv",
                           ["library_segments_verify.txt"])))

    C.append(Campaign(
        "kscreen-restarts", "Keystream library restarted at headings and page starts",
        "Same library, with the key restarting at each red heading / paragraph start (10 windows) and at each "
        "page start (46 windows). Caution: windows shorter than ~250 runes (two heading windows of 91 and 121 runes, two "
        "page windows of 131 and 137) exceed the 1.40 threshold by chance after ~10^8 decodes; judge them with the per-window "
        "extreme-value null of work/kscreen/short_window_null.py (results/analysis/short_window_null_*.txt), not with 1.40.",
        [
            ks_screen("kscreen-restarts", "heads", "data/heads.txt", "file:data/library.ksb", "library_heads.tsv", T, hours=0.6),
            ks_screen("kscreen-restarts", "pages", "data/pages.txt", "file:data/library.ksb", "library_pages.tsv", T, hours=2.5),
            ks_screen("kscreen-restarts", "null-pages", "data/pages.txt", "rand:100:12", "null_pages.tsv", T, hours=0.4),
            # the 91- and 121-rune heading windows reach IoC 1.7-2.1 by chance; their matched null is per window
            ks_screen("kscreen-restarts", "null-heads", "data/heads.txt", "rand:600:13", "null_heads.tsv", T, hours=0.5),
            ks_verify("kscreen-restarts", "verify-heads", "library_heads.tsv"),
            ks_verify("kscreen-restarts", "verify-pages", "library_pages.tsv"),
        ],
        lambda: ks_summary([("library x 10 heading restarts", "library_heads.tsv"),
                            ("library x 46 page restarts", "library_pages.tsv")], "null_pages.tsv",
                           ["library_heads_verify.txt", "library_pages_verify.txt"])))

    C.append(Campaign(
        "kscreen-typo", "Keystream library restarted at typographic marks",
        "cicadanotebook.com proposed key restarts at the numbered list of 0.14 (items 1-5 and its 10-dot brackets), at the "
        "three-dot marks and right after the red headings (work/log/typo_restarts_2026-10-17.md). 22 windows from "
        "work/typo_restarts.py; the null has the library's size (1,439 random keystreams of 20,000), because windows under "
        "250 runes are judged against their own maximum. Plants show the power per window length; the solved sections give "
        "the known answer (their keys run through the marks); one keystream restarted at every list item is a separate "
        "pooled test.",
        [
            Step("kscreen-typo/export", [PY, str(WORK / "typo_restarts.py"), "export"], hours=0.01,
                 outputs=[KS / "data" / "typo.txt", KS / "data" / "typo_plain.txt"]),
            ks_screen("kscreen-typo", "library", "data/typo.txt", "file:data/library.ksb", "library_typo.tsv", T, hours=1.0),
            ks_screen("kscreen-typo", "null", "data/typo.txt", "rand:1439:17", "null_typo.tsv", T, hours=1.0),
            ks_verify("kscreen-typo", "verify", "library_typo.tsv"),
            Step("kscreen-typo/plants", [PY, str(WORK / "typo_restarts.py"), "plants"], hours=0.05,
                 outputs=[RES / "kscreen" / "typo_plants.txt"]),
            Step("kscreen-typo/known", [PY, str(WORK / "typo_restarts.py"), "known"], hours=0.01,
                 outputs=[RES / "kscreen" / "typo_known.txt"]),
            Step("kscreen-typo/pooled", [PY, str(WORK / "typo_restarts.py"), "pooled"], hours=0.1,
                 outputs=[RES / "kscreen" / "typo_pooled.txt"]),
            Step("kscreen-typo/summary", [PY, str(WORK / "typo_restarts.py"), "summary"], hours=0.01,
                 outputs=[RES / "kscreen" / "typo_summary.txt"]),
        ],
        lambda: [f"- {line}" for line in (last_line(RES / "kscreen" / "typo_summary.txt", r"windows where") or "not run yet",)]))

    lin3_items = 28 * 29 * 29
    per = -(-lin3_items // LIN3_CHUNKS)
    lin3 = [ks_screen("kscreen-recurrences", f"lin3-{k:02d}", "data/segments.txt", "lin:3", f"lin3/chunk{k:02d}.tsv", T,
                      ("mults=1", f"items={k * per}:{(k + 1) * per}"), hours=0.3) for k in range(LIN3_CHUNKS)]
    C.append(Campaign(
        "kscreen-recurrences", "Every linear recurrence and polynomial key mod 29",
        "All linear recurrences of order 1-3 mod 29 (Fibonacci, Lucas, Pell, Tribonacci, Padovan and 23,000 "
        "others) from every start state, and all polynomial keys up to degree 3, on the 8 sections.",
        [
            ks_screen("kscreen-recurrences", "lin1", "data/segments.txt", "lin:1", "lin1_segments.tsv", T, ("mults=1",), 0.01),
            ks_screen("kscreen-recurrences", "lin2", "data/segments.txt", "lin:2", "lin2_segments.tsv", T, ("mults=1",), 0.05),
            ks_screen("kscreen-recurrences", "poly3", "data/segments.txt", "poly:3", "poly3_segments.tsv", T, ("mults=1",), 0.1),
        ] + lin3 + [
            Step("kscreen-recurrences/lin3-merge", lambda log: merge_chunks("lin:3", "lin3", "lin3_segments.tsv", log),
                 hours=0.01, outputs=[RES / "kscreen" / "lin3_segments.tsv"]),
            ks_verify("kscreen-recurrences", "verify-lin2", "lin2_segments.tsv", top=8),
            ks_verify("kscreen-recurrences", "verify-poly3", "poly3_segments.tsv", top=8),
            ks_verify("kscreen-recurrences", "verify-lin3", "lin3_segments.tsv", top=10),
        ],
        lambda: ks_summary([("order-1 recurrences", "lin1_segments.tsv"), ("order-2 recurrences", "lin2_segments.tsv"),
                            ("polynomials deg <= 3", "poly3_segments.tsv"), ("order-3 recurrences", "lin3_segments.tsv")],
                           "null_segments.tsv",
                           ["lin2_segments_verify.txt", "poly3_segments_verify.txt", "lin3_segments_verify.txt"])))

    C.append(Campaign(
        "rescreen", "Dictionary screens rerun with the corrected word segmentation",
        "Screens 1 and 2, the reverse-direction screen and the heading-restart screen were run before the "
        "word-wrap fix (wrapped words were split, a handicap for a true key). English-dictionary scoring.",
        [
            Step("rescreen/screen1", [PY, "work/attack.py", "screen"], hours=1.0,
                 outputs=[RES / "screens" / "screen1.log"], stdout_to=RES / "screens" / "screen1.log",
                 post=lambda: copy_json("screen.json", "screen1_top.json", top=1000)),
            Step("rescreen/screen2-slide", [PY, "work/attack.py", "slide"], hours=1.2,
                 outputs=[RES / "screens" / "screen2_slide.log"], stdout_to=RES / "screens" / "screen2_slide.log",
                 post=lambda: copy_json("screen_sliding.json", "screen2_slide.json")),
            Step("rescreen/reverse", [PY, "work/rev_screen.py"], hours=1.5,
                 outputs=[RES / "screens" / "reverse.log"], stdout_to=RES / "screens" / "reverse.log",
                 post=lambda: copy_json("rev_screen.json", "reverse.json")),
            Step("rescreen/headings", [PY, "work/heading_screen.py"], hours=2.0,
                 outputs=[RES / "screens" / "headings.log"], stdout_to=RES / "screens" / "headings.log",
                 post=lambda: copy_json("heading_screen.json", "headings.json")),
        ],
        lambda: [f"- {n}: {last_line(RES / 'screens' / f, r'(?i)control') or 'not run'}" for n, f in
                 (("screen 1 (3 offsets)", "screen1.log"), ("screen 2 (all offsets)", "screen2_slide.log"),
                  ("reverse direction", "reverse.log"), ("heading restarts", "headings.log"))]))

    C.append(Campaign(
        "dsearch", "Key-free secret-alphabet search, large",
        "walk dsearch: a per-word additive key behind any secret outer alphabet, with m = 1-8 position phases and "
        "gap sets {1,2} and {1,2,3} (the earlier runs used gap 1 only), against 4 structure-free surrogates each. "
        "Starts with a synthetic positive control that must recover the planted alphabet.",
        dsearch_steps(T),
        dsearch_summary))

    C.append(Campaign(
        "payload", "The 256-byte payload, corrected bytes",
        "Hash identity tests and 832k passphrase AES/RC4/XOR decryptions, rerun on the corrected payload (5 bytes "
        "fixed in Phase 2/research; earlier runs and the community's used the uncorrected bytes).",
        [
            Step("payload/hashes", [PY, "work/grid60.py", "hashes"], hours=0.05,
                 outputs=[RES / "payload" / "hashes.txt"], stdout_to=RES / "payload" / "hashes.txt"),
            Step("payload/decrypt", [PY, "work/grid60.py", "decrypt"], hours=0.5,
                 outputs=[RES / "payload" / "decrypt.txt"], stdout_to=RES / "payload" / "decrypt.txt"),
        ],
        lambda: [f"- hashes: {last_line(RES / 'payload' / 'hashes.txt', 'matches') or 'not run'}",
                 f"- decryptions: {last_line(RES / 'payload' / 'decrypt.txt') or 'not run'}"]))

    C.append(Campaign(
        "kscreen-multipliers", "Keystream library x every key multiplier",
        "The library again on the 8 sections with all 28 key multipliers (c = p + m*k), e.g. 3301*k = 24*k mod 29.",
        [
            ks_screen("kscreen-multipliers", "library-all-mults", "data/segments.txt", "file:data/library.ksb",
                      "library_segments_allmults.tsv", T, ("mults=all",), hours=5.0),
            ks_verify("kscreen-multipliers", "verify", "library_segments_allmults.tsv"),
        ],
        lambda: ks_summary([("library x 28 multipliers", "library_segments_allmults.tsv")], "null_segments.tsv",
                           ["library_segments_allmults_verify.txt"])))

    sacred_selftest = RES / "kscreen" / "sacred_selftest.txt"
    C.append(Campaign(
        "kscreen-sacred", "New stream families from an outside LLM: two-stream combinations, functions at the primes, reciprocals, prime residues",
        "work/kscreen/sacred.py builds streams the library lacks: F1 s1 + t*s2 and interleaves of 20 number-theoretic streams, F3 phi / sigma / d / Fibonacci / Lucas / Pell / triangular read at p_i - 1, p_i, p_i + 1, "
        "F4 base-29 digits of 1/3301, 1/1033 and their ratios, F5 rational functions of the prime residue p mod 29. Streams LP2's flat IoC already excludes as keys, and affine duplicates of library streams, are dropped "
        "(sacred.tsv). Screened on the 8 sections at every offset like the library (kscreen-sections), against that campaign's 300-stream random null. Controls: work/kscreen/sacred_selftest.py "
        "(one planted key per family, recovered). F2 of the proposal (order-4 recurrences with chosen coefficients) is not built.",
        [
            Step("kscreen-sacred/build", [PY, str(KS / "sacred.py")], hours=0.02, outputs=[KS / "data" / "sacred.ksb"]),
            Step("kscreen-sacred/controls", [PY, str(KS / "sacred_selftest.py"), "--threads", str(T), "--out", str(sacred_selftest)], hours=0.05,
                 outputs=[sacred_selftest], done_check=lambda: "PASSED" in (last_line(sacred_selftest) or "")),
            ks_screen("kscreen-sacred", "library", "data/segments.txt", "file:data/sacred.ksb", "sacred_segments.tsv", T, hours=0.3),
            ks_verify("kscreen-sacred", "verify", "sacred_segments.tsv"),
        ],
        lambda: [f"- controls: {last_line(sacred_selftest) or 'not run'}"] + ks_summary([("sacred streams x 8 sections", "sacred_segments.tsv")], "null_segments.tsv",
                                                                                    ["sacred_segments_verify.txt"])))

    sacred2_selftest = RES / "kscreen" / "sacred2_selftest.txt"
    C.append(Campaign(
        "kscreen-sacred2", "DeepSeek's second batch: n^-1, discrete log, g^n, n^3 modulo primes = 1 (mod 29), base-29 digit sum",
        "work/kscreen/sacred.py --round 2 builds 19 streams (G1 inverses, G2 discrete logs, G3 g^n for p = 59, 233, 349, 523, 929; G4 cubes for p = 59, 233, 929; G5 the sum of the two base-29 digits), each repeated over whole "
        "periods so it is exactly uniform mod 29, all periodic with period 58-928. Same screen as kscreen-sacred. Controls: sacred_selftest.py --set sacred2. Periods up to about 400 were already excluded key-agnostically by the drift-period scan.",
        [
            Step("kscreen-sacred2/build", [PY, str(KS / "sacred.py"), "--round", "2"], hours=0.02, outputs=[KS / "data" / "sacred2.ksb"]),
            Step("kscreen-sacred2/controls", [PY, str(KS / "sacred_selftest.py"), "--set", "sacred2", "--threads", str(T), "--out", str(sacred2_selftest)], hours=0.05,
                 outputs=[sacred2_selftest], done_check=lambda: "PASSED" in (last_line(sacred2_selftest) or "")),
            ks_screen("kscreen-sacred2", "library", "data/segments.txt", "file:data/sacred2.ksb", "sacred2_segments.tsv", T, hours=0.05),
            ks_verify("kscreen-sacred2", "verify", "sacred2_segments.tsv"),
        ],
        lambda: [f"- controls: {last_line(sacred2_selftest) or 'not run'}"] + ks_summary([("DeepSeek batch 2 x 8 sections", "sacred2_segments.tsv")], "null_segments.tsv",
                                                                                      ["sacred2_segments_verify.txt"])))

    sign_names = []
    if (KS / "sign_rules.txt").exists():
        sign_names = [l.strip() for l in open(KS / "sign_rules.txt", encoding="utf-8") if l.strip()]
        sign_names.sort(key=lambda n: ("EDACB".index(n[0]), n))               # the lore-most-plausible templates first: length thresholds, within-word comparisons, parity
    sign_selftest = RES / "kscreen" / "sign_selftest.txt"

    def sign_summary():
        out = [f"- controls: {last_line(sign_selftest) or 'not run'}"]
        best, flagged = [], []
        for n in sign_names:
            b = ks_best(f"signs/{n}.tsv")
            if b is not None:
                best.append((b, n))
                if b >= 1.40:
                    flagged.append(n)
        if not best:
            return out + ["- not run yet"]
        top = max(best)
        out.append(f"- {len(best)} of {len(sign_names)} rules done; best IoC {top[0]:.3f} ({top[1]}); " + ("above 1.40 for " + ", ".join(flagged) if flagged else "none reaches the 1.40 rule"))
        for n in flagged:
            line = last_line(RES / "kscreen" / "signs" / f"{n}_verify.txt", r"re-decoded hits")
            if line:
                out.append(f"  - {n} verification: {line}")
        return out

    C.append(Campaign(
        "kscreen-signs", "Word-level key-sign rules ('their numbers are the direction'): 61 rules over the flat-IoC library",
        "c = p + s_w * k with the sign s_w of the key for every rune of word w from a rule on word numbers (work/kscreen/signrules.py; engine S lines): parity, mod-3/5/7 half splits, comparisons with the previous word, length thresholds, over "
        "the current word's length and positions and the previous words' ciphertext (the current word's own ciphertext numbers are circular for an encryptor and excluded; the two orientations of a rule are the multiplier 28). 581 library streams "
        "(those LP2's flat IoC does not exclude) x 8 sections at every offset, about 6.5 min per rule on 14 threads. Controls: sign_selftest.py (independent planter, 12 windows over 4 rules, blindness without the signs, null).",
        [
            Step("kscreen-signs/build", [PY, str(KS / "signrules.py")], hours=0.02, outputs=[KS / "data" / "signs" / "rules.tsv", KS / "data" / "library_flat.ksb"]),
            Step("kscreen-signs/controls", [PY, str(KS / "sign_selftest.py"), "--threads", str(T), "--out", str(sign_selftest)], hours=0.05,
                 outputs=[sign_selftest], done_check=lambda: "PASSED" in (last_line(sign_selftest) or "")),
        ] + [s for n in sign_names for s in (
            ks_screen("kscreen-signs", n, f"data/signs/{n}.txt", "file:data/library_flat.ksb", f"signs/{n}.tsv", T, hours=0.11),
            ks_verify("kscreen-signs", f"verify-{n}", f"signs/{n}.tsv", top=5))],
        sign_summary))

    sp_names = []
    if (KS / "sign_periodic_rules.txt").exists():
        sp_names = [l.strip() for l in open(KS / "sign_periodic_rules.txt", encoding="utf-8") if l.strip()]
    sp_selftest = RES / "kscreen" / "sign_periodic_selftest.txt"

    def sp_summary():
        out = [f"- controls: {last_line(sp_selftest) or 'not run'}"]
        best = [(b, n) for n in sp_names if (b := ks_best(f"signs_periodic/{n}.tsv")) is not None]
        if not best:
            return out + ["- not run yet"]
        top = max(best)
        flagged = [n for b, n in best if b >= 1.40]
        out.append(f"- {len(best)} of {len(sp_names)} templates done; best IoC {top[0]:.3f} ({top[1]}); " + ("above 1.40 for " + ", ".join(flagged) if flagged else "none reaches the 1.40 rule"))
        return out

    C.append(Campaign(
        "kscreen-signs-periodic", "Per-rune periodic key-sign templates (period 2-5): the Beaufort / Vigenere alternation as a sign pattern",
        "c = p + s_i * k with s_i = pattern[i mod L], L = 2..5, one representative per complement class (the complement is the multiplier 28): 25 distinct templates after dropping constants and repeats of shorter patterns "
        "(work/kscreen/signrules_periodic.py; the engine's S lines). 581 flat-IoC library streams x 8 sections at every offset, about 6.5 min per template on 14 threads. Controls: sign_periodic_selftest.py (independent planter, 3 templates x 3 windows, blindness, null).",
        [
            Step("kscreen-signs-periodic/build", [PY, str(KS / "signrules_periodic.py")], hours=0.02, outputs=[KS / "data" / "signs_periodic" / "P2_pm.txt"]),
            Step("kscreen-signs-periodic/controls", [PY, str(KS / "sign_periodic_selftest.py"), "--threads", str(T), "--out", str(sp_selftest)], hours=0.05,
                 outputs=[sp_selftest], done_check=lambda: "PASSED" in (last_line(sp_selftest) or "")),
        ] + [s for n in sp_names for s in (
            ks_screen("kscreen-signs-periodic", n, f"data/signs_periodic/{n}.txt", "file:data/library_flat.ksb", f"signs_periodic/{n}.tsv", T, hours=0.11),
            ks_verify("kscreen-signs-periodic", f"verify-{n}", f"signs_periodic/{n}.tsv", top=5))],
        sp_summary))

    sacred3_selftest = RES / "kscreen" / "sacred3_selftest.txt"
    C.append(Campaign(
        "kscreen-sacred3", "Book-derived streams: phi / sigma of 3301 i + 1033 and 1033 i + 3301, primes at index multiples of 58 .. 3301, base-29 digits of 1/45415",
        "work/kscreen/sacred.py --round 3 builds 15 streams from the book's numbers (leads on the two magic squares from an outside LLM): H1 phi and sigma (d is not flat) of the progressions 3301 i + 1033 and 1033 i + 3301; H2 the primes p_(k i) for "
        "k = 58, 87, 116, 174, 348, 464, 1033, 3301 (decimations up to 29 were covered by kscreen-hyp); H3 base-29 digits of 1/45415, 45415/1033 and 45415/3301. Same screen as kscreen-sacred. Controls: sacred_selftest.py --set sacred3.",
        [
            Step("kscreen-sacred3/build", [PY, str(KS / "sacred.py"), "--round", "3"], hours=0.02, outputs=[KS / "data" / "sacred3.ksb"]),
            Step("kscreen-sacred3/controls", [PY, str(KS / "sacred_selftest.py"), "--set", "sacred3", "--threads", str(T), "--out", str(sacred3_selftest)], hours=0.05,
                 outputs=[sacred3_selftest], done_check=lambda: "PASSED" in (last_line(sacred3_selftest) or "")),
            ks_screen("kscreen-sacred3", "library", "data/segments.txt", "file:data/sacred3.ksb", "sacred3_segments.tsv", T, hours=0.05),
            ks_verify("kscreen-sacred3", "verify", "sacred3_segments.tsv"),
        ],
        lambda: [f"- controls: {last_line(sacred3_selftest) or 'not run'}"] + ks_summary([("book-derived streams x 8 sections", "sacred3_segments.tsv")], "null_segments.tsv",
                                                                                      ["sacred3_segments_verify.txt"])))

    C.append(Campaign(
        "prng-all", "Seeded-PRNG pads with a fresh seed per section",
        "phpmt sweeps of every seed of PHP<7.1 mt_rand, glibc random() and .NET System.Random on all 8 sections "
        "(the single-section runs only covered LP2 page 0), then full-segment verification of the best candidates.",
        prng_steps(T),
        prng_summary))
    chain = [
        Step("kscreen-chain/windows", [PY, str(KS / "chain_windows.py")], hours=0.01,
             outputs=[KS / "data" / "chain" / f"{k}_a28.txt" for k in ("segments", "heads", "pages")]),
        # always rerun: the controls validate this machine's engines for the chain windows
        Step("kscreen-chain/controls", [PY, str(KS / "chain_selftest.py"), "--engine", DEVICE, "--out", str(CHAIN_SELFTEST)],
             hours=0.03, outputs=[CHAIN_SELFTEST], always=True, device=DEVICE),
    ]
    for a in range(1, 29):
        w = f"data/chain/segments_a{a}.txt"
        chain += [ks_screen("kscreen-chain", f"a{a}-library", w, "file:data/library.ksb", f"chain/library_a{a}.tsv", T, hours=0.12),
                  ks_screen("kscreen-chain", f"a{a}-null", w, "rand:300:11", f"chain/null_a{a}.tsv", T, hours=0.03),
                  ks_screen("kscreen-chain", f"a{a}-lin2", w, "lin:2", f"chain/lin2_a{a}.tsv", T, ("mults=1",), 0.01),
                  ks_screen("kscreen-chain", f"a{a}-poly3", w, "poly:3", f"chain/poly3_a{a}.tsv", T, ("mults=1",), 0.01),
                  ks_verify("kscreen-chain", f"a{a}-verify", f"chain/library_a{a}.tsv", top=10)]
    C.append(Campaign(
        "kscreen-chain", "Ciphertext-feedback ciphers c_i = a*c_{i-1} + p_i + k_i, a = 1..28",
        "The doublet fingerprint (c_i - c_{i-1} flat except that 0 is missing) is what a cipher with ciphertext feedback gives "
        "if the encryptor avoids the shift that would repeat a rune. Every earlier screen assumed c = p + k, so none of them "
        "could see such a key. For each multiplier a the 8 sections are rewritten as c' = c_i - a*c_{i-1} with the collision "
        "check against (1-a)*c_{i-1} (work/kscreen/chain_windows.py) and screened with the 1,447-keystream library, every order-2 "
        "linear recurrence and every cubic polynomial, at every offset, both anti-repeat models, any plaintext language and alphabet.",
        chain, chain_summary))
    gens_why = ("py3 (CPython random.seed), mt32 / mt31 (std::mt19937, PHP >= 7.1), java (java.util.Random), msvc (rand()), "
                "drand48 (drand48, Perl) and ruby (Ruby <= 2.7), each with two natural key mappings, all 2^32 seeds, 16 cipher "
                "variants (work/phpmt/src/gens.rs; the CUDA port is validated against the Rust engine, which is validated "
                "against CPython, NumPy and published vectors). ")
    C.append(Campaign(
        "prng-more", "More seeded-PRNG pads, window 0.7: Python, C++/PHP 7, Java, MSVC, drand48/Perl, Ruby",
        gens_why + "Window 0.7 only: one pad starting at the first unsolved rune.",
        prng_more_steps(T, ("07",)), lambda: prng_more_summary(("07",))))

    rev = [
        Step("kscreen-reverse/windows", [PY, str(KS / "chain_windows.py"), "--reverse"], hours=0.01,
             outputs=[KS / "data" / "chain" / "segments_a28_rev.txt", KS / "data" / "chain" / "segments_a0_rev.txt"]),
        Step("kscreen-reverse/controls", [PY, str(KS / "chain_selftest.py"), "--engine", DEVICE, "--out", str(CHAIN_SELFTEST)],
             hours=0.03, outputs=[CHAIN_SELFTEST], always=True, device=DEVICE),
    ]
    for a in range(0, 29):
        w = f"data/chain/segments_a{a}_rev.txt"
        back = ("dir=back",)
        rev += [ks_screen("kscreen-reverse", f"a{a}-library", w, "file:data/library.ksb", f"chain/rev_library_a{a}.tsv", T, back, 0.12),
                ks_screen("kscreen-reverse", f"a{a}-null", w, "rand:300:11", f"chain/rev_null_a{a}.tsv", T, back, 0.03),
                ks_screen("kscreen-reverse", f"a{a}-lin2", w, "lin:2", f"chain/rev_lin2_a{a}.tsv", T, ("mults=1",) + back, 0.01),
                ks_screen("kscreen-reverse", f"a{a}-poly3", w, "poly:3", f"chain/rev_poly3_a{a}.tsv", T, ("mults=1",) + back, 0.01),
                ks_verify("kscreen-reverse", f"a{a}-verify", f"chain/rev_library_a{a}.tsv", top=10)]
    C.append(Campaign(
        "kscreen-reverse", "Key running BACKWARD through the text, with and without ciphertext feedback (a = 0..28)",
        "Every IoC screen so far read the key forward along the text. A key read from the end is covered by reversed windows "
        "and the engines' dir=back mode (a re-draw then uses a lower key index, so the used key comes first in pointer order). "
        "a = 0 is the ordinary cipher with a backward key; a = 1..28 combine it with ciphertext feedback. Same library, "
        "recurrences and polynomials as kscreen-sections; controls: planted backward keys recovered at the exact key index, "
        "the same ciphertext read forward not found (work/kscreen/chain_selftest.py).",
        rev, lambda: chain_summary("rev_", range(0, 29))))

    C.append(Campaign(
        "prng-more-all", "More seeded-PRNG pads with a fresh seed per section",
        gens_why + "A fresh seed per section: all 8 windows at once.",
        prng_more_steps(T, ("all",)), lambda: prng_more_summary(("all",))))

    C.append(Campaign(
        "prng-bg", "Seeded-PRNG pads with a boundary-free score (English rune-bigram log-likelihood), window 0.7 (and every section)",
        "The dictionary score of the earlier seed sweeps counts words between the transcription's word separators. LP2's word lengths have no "
        "serial structure (results/analysis/wordlen_adjacency.txt: mean PMI -0.060 against +0.050 for English and +0.006 for the solved sections), "
        "and with LP2's separators imposed on English plaintext a planted seed scores 0 instead of 33 (work/log/phase9_boundaries.md): if the separators "
        "are independent of the plaintext words, those sweeps could not see a true key. work/phpmt/bg.py scores a decoded window "
        "(120 runes) by the log-likelihood ratio of its plaintext under an English rune-bigram table instead, with the same ten generators, "
        "16 variants and skip/coin beam. Gates: generators identical to phpmt.cu, scores equal to a Python reference, planted seeds "
        "recovered for every generator, random ciphertext gives no candidate (work/tests/test_bgmt.py).",
        prng_bg_steps(T, ("07",)) + [x for x in prng_bg_steps(T, ("all",)) if not x.id.endswith("controls")],
        lambda: prng_bg_summary(("07", "all"))))

    C.append(Campaign(
        "kscreen-hashwords", "Hash-seed keystreams of every word and phrase of the solved text",
        "The library holds hash streams for only ~65 Cicada strings. work/kscreen/export_hashwords.py adds sha256/sha512/md5 counter streams and "
        "the sha256 chain, reduced mod 29 and by rejection, for each of the 809 words and two-word phrases of the solved text in upper and lower case "
        "(12,944 streams of 20,000 values), screened at every offset like kscreen-sections, with a null of the same number of random streams.",
        [
            Step("kscreen-hashwords/export", [PY, str(KS / "export_hashwords.py")], hours=0.1, outputs=[KS / "data" / "library_hashwords.ksb"]),
            ks_screen("kscreen-hashwords", "null", "data/segments.txt", "rand:12944:21", "null_hashwords.tsv", T, hours=0.7),
            ks_screen("kscreen-hashwords", "library", "data/segments.txt", "file:data/library_hashwords.ksb", "library_hashwords.tsv", T, hours=0.7),
            ks_verify("kscreen-hashwords", "verify", "library_hashwords.tsv"),
        ],
        lambda: ks_summary([("12,944 hash streams x 8 sections", "library_hashwords.tsv")], "null_hashwords.tsv",
                           ["library_hashwords_verify.txt"])))

    hyp_selftest = OVM / "hyp_selftest.txt"
    C.append(Campaign(
        "kscreen-hyp", "Untested key families H3-H6 of docs/HYPOTHESES.md",
        "work/kscreen/export_hyp.py: H3 every library stream decimated by d = 2..29; H4 prefix sums and per-word Gematria sums of the solved "
        "plaintext and of Self-Reliance; H6 pi, e, phi, sqrt2 digits (bases 10, 29) from positions 10^6 and 3301*1033; H5 ciphertext as key "
        "(the keyed solved sections, LP2 read backwards, and LP2's own ciphertext forwards, i.e. long-lag ciphertext autokey and keys from "
        "another section; all 28 multipliers). Only streams that keep LP2's flat IoC are screened. LP2's own ciphertext needs the engine's G "
        "guard (a window must not be deciphered with itself), which only the Rust engine has. Controls: work/kscreen/hyp_selftest.py.",
        [
            Step("kscreen-hyp/export", [PY, str(KS / "export_hyp.py")], hours=0.3,
                 outputs=[KS / "data" / f for f in ("library_hyp.ksb", "library_h5.ksb", "library_self.ksb", "segments_self.txt")]),
            # always rerun: it validates this machine's build and the guard
            Step("kscreen-hyp/controls", [PY, str(KS / "hyp_selftest.py"), "--threads", str(T), "--out", str(hyp_selftest)],
                 hours=0.05, outputs=[hyp_selftest], always=True),
            ks_screen("kscreen-hyp", "null", "data/segments.txt", "rand:1300:31", "null_hyp.tsv", T, hours=0.6),
            ks_screen("kscreen-hyp", "library", "data/segments.txt", "file:data/library_hyp.ksb", "library_hyp.tsv", T, hours=0.6),
            ks_screen("kscreen-hyp", "h5", "data/segments.txt", "file:data/library_h5.ksb", "library_h5.tsv", T, ("mults=all",), hours=0.05),
            Step("kscreen-hyp/self", [str(KS_BIN), "screen", "data/segments_self.txt", "file:data/library_self.ksb",
                                      str(RES / "kscreen" / "library_self.tsv"), f"threads={T}", "mults=all"],
                 cwd=KS, hours=0.05, outputs=[RES / "kscreen" / "library_self.tsv"]),
            ks_verify("kscreen-hyp", "verify", "library_hyp.tsv"),
            ks_verify("kscreen-hyp", "verify-h5", "library_h5.tsv"),
            ks_verify("kscreen-hyp", "verify-self", "library_self.tsv"),
        ],
        lambda: [f"- controls on {MACHINE}: {last_line(hyp_selftest) or 'not run'}"]
        + ks_summary([("H3 decimations, H4 text numbers, H6 deep constants x 8 sections", "library_hyp.tsv"),
                      ("H5 solved ciphertexts and LP2 backwards x 28 multipliers", "library_h5.tsv"),
                      ("H5 LP2's own ciphertext forwards (guarded) x 28 multipliers", "library_self.tsv")],
                     "null_hyp.tsv", ["library_hyp_verify.txt", "library_h5_verify.txt", "library_self_verify.txt"])))

    clock_selftest = OVM / "clock_selftest.txt"
    clock_steps = [Step("kscreen-clock/controls", [PY, str(KS / "clock_selftest.py"), "--threads", str(T), "--out", str(clock_selftest)],
                        hours=0.05, outputs=[clock_selftest], always=True)]
    for ck, n, seed in (("c1", 300, 41), ("p1", 300, 42), ("ct", 150, 43), ("cp", 150, 44), ("pt", 150, 45), ("pp", 150, 46)):
        for name, fam in (("null", f"rand:300:{seed}"), ("library", "file:data/library.ksb")):
            tsv = RES / "kscreen" / f"clock_{ck}_{name}.tsv"
            # CPU only: gpu.py has no clocked pointer
            clock_steps.append(Step(f"kscreen-clock/{ck}-{name}", [str(KS_BIN), "screen", "data/segments.txt", fam, str(tsv),
                                                                   f"threads={T}", f"clock={ck}", f"n={n}"],
                                    cwd=KS, hours=0.08 if name == "null" else 0.35, outputs=[tsv]))
        clock_steps.append(ks_verify("kscreen-clock", f"{ck}-verify", f"clock_{ck}_library.tsv"))
    C.append(Campaign(
        "kscreen-clock", "Clocked key pointer (H3): the pointer moves on by g(rune) instead of 1",
        "docs/HYPOTHESES.md H3: after each rune the key pointer advances by 1 + its index, its Gematria prime or prime - 1, read from "
        "the cipher rune (c1, cp, ct) or from the deciphered rune (p1, pp, pt; plaintext only without a substitution or shift). Every "
        "earlier screen stepped the pointer by one. The 1,447-stream library at every offset on the 8 sections, both signs and "
        "both anti-repeat models; the prime clocks use 150-rune windows because they consume about 44 key values per rune. "
        "Controls: work/kscreen/clock_selftest.py (planted keys per clock, blindness of the unclocked screen); a 300-stream null per clock.",
        clock_steps,
        lambda: [f"- controls on {MACHINE}: {last_line(clock_selftest) or 'not run'}"]
        + [x for ck in ("c1", "p1", "ct", "cp", "pt", "pp")
           for x in ks_summary([(f"clock={ck}, library x 8 sections", f"clock_{ck}_library.tsv")], f"clock_{ck}_null.tsv",
                               [f"clock_{ck}_library_verify.txt"])]))

    C.append(Campaign(
        "kscreen-step28", "Relative-rank chain cipher: the plaintext enters the STEP c_i - c_{i-1}, keyed mod 28",
        "The doublet fingerprint is also what a cipher gives whose ciphertext step is never zero (research note C1, "
        "work/log/research_2026-10-17.md): D_i = 1 + (q_i + m*K_j) mod 28 (variant A), 2^(q_i + m*log K_j) (variant B) or the (q_i + m*K_j) mod 28-th of the "
        "28 runes other than c_{i-1} (variant C, rank), with the rare zero step as a 'ditto' that consumes a key value or not. In the c domain the plaintext is a random walk and "
        "every earlier screen was blind to it; in the step domain the decoder is a plain subtraction with no beam. "
        "work/kscreen/step28.py counts the class histogram at every (stream, offset) for the 1,447-stream library and every "
        "unit multiplier of Z28, with planted-key recovery (variants A, B, C and both modes), CPU/CUDA agreement and matched nulls; "
        "work/step_periodicity.py scans periodic keys (lags to 3,000).",
        step28_steps(), step28_summary))

    C.append(Campaign(
        "prng-step", "Seeded-PRNG pads for the step-domain cipher, window 0.7: all ten generators",
        "Research note C2: the seed sweeps of the ordinary cipher (c = p + k) cannot see a key that enters the STEP "
        "c_i - c_{i-1}. work/phpmt/step.py runs the ten generators of phpmt.cu over all 2^32 seeds and scores, per seed, 144 "
        "settings on the first 240 steps of section 0.7 (at key index 0 and 1) (variants A and C with keys mod 28 / variant B with log2 of the non-zero "
        "keys of Z29, both key maps, zero steps spending a key value or not, the 12 unit multipliers of Z28) by the index "
        "of coincidence of the decoded classes. Gates: keys equal the Rust engine for both alphabets, scores equal the numpy "
        "reference, planted seeds recovered for every generator, random ciphertext gives no candidate (work/tests/test_stepmt.py).",
        prng_step_steps(), prng_step_summary))

    seg = "../kscreen/data/segments.txt"
    C.append(Campaign(
        "layer2", "Two layers from the solved pages: keyword Vigenere inside, number stream with the anti-repeat rule outside",
        "Hypothesis H-LAYER (work/log/hypotheses_2026-10-17.md): q = p + K[phi mod m] with the literal-F rule of Welcome / Koan 2 "
        "(or without), then c = q + S_j with the skip / coin anti-repeat models. The outer layer explains the doublet deficit and "
        "the flat statistics, and it hides the inner literal F (LP2 has no F excess); kscreen decodes the outer stream but scores a "
        "Vigenere text (IoC ~1.1-1.2), so it is blind. work/layer2 keeps a beam over the outer pointer and the inner phase and scores "
        "the decoded letters with an English rune-bigram table (identity and Atbash alphabets): a true key ~ +7 per rune, random "
        "~ -15. Periodic mode covers any keyword of period 2-14 by column coincidences; its hits are checked by estimating the keyword "
        "and rescoring. Controls: work/layer2/selftest.py (plants with and without literal F, both alphabets, both models; kscreen "
        "blind to them; random streams below +2.0).",
        [
            Step("layer2/build", ["cargo", "build", "--release", "--manifest-path", str(L2 / "Cargo.toml")], always=True, hours=0.02),
            Step("layer2/export", [PY, str(L2 / "export.py")], hours=0.02,
                 outputs=[L2 / "data" / f for f in ("core.ksb", "core20.ksb", "combined.ksb", "keywords.txt", "keywords_solved.txt",
                                                    "keyword_none.txt", "plain.txt")]),
            Step("layer2/selftest", [PY, str(L2 / "selftest.py"), "--threads", str(T), "--out", str(L2_SELFTEST)], hours=0.3,
                 outputs=[L2_SELFTEST], done_check=lambda: "PASSED" in (last_line(L2_SELFTEST) or "")),
            l2_screen("layer2", "null", seg, "rand:20:91", "null_bigram_solved.tsv", T,
                      ["mode=bigram", "kw=data/keywords_solved.txt"], hours=1.1),
            l2_screen("layer2", "bigram-solved", seg, "file:data/core.ksb", "bigram_solved.tsv", T,
                      ["mode=bigram", "kw=data/keywords_solved.txt"], hours=6.3),
            l2_verify("layer2", "verify-solved", "bigram_solved.tsv"),
            l2_screen("layer2", "bigram-words", seg, "file:data/core20.ksb", "bigram_words.tsv", T,
                      ["mode=bigram", "kw=data/keywords.txt", "atb=0"], hours=4.0),
            l2_verify("layer2", "verify-words", "bigram_words.tsv"),
            l2_screen("layer2", "periodic", seg, "file:data/core.ksb", "periodic_core.tsv", T,
                      ["mode=periodic", "ms=2:14", "litf=0"], hours=1.5),
            l2_verify("layer2", "verify-periodic", "periodic_core.tsv", top=100, hours=0.3),
            # variant A1: the keyword folded into the stream (one pointer); single layer, English-bigram score
            l2_screen("layer2", "combined", seg, "file:data/combined.ksb", "bigram_combined.tsv", T,
                      ["mode=bigram", "kw=data/keyword_none.txt", "litf=0", "isigns=1"], hours=0.6),
            l2_verify("layer2", "verify-combined", "bigram_combined.tsv"),
        ],
        l2_summary))

    C.append(Campaign(
        "prng-time", "Generators seeded with a millisecond timestamp of 2012-2014 (Java 48-bit, CPython two-word seeds)",
        "The 32-bit sweeps cover every time(NULL) seed but not new Random(System.currentTimeMillis()) (Java's seed is 48-bit) or "
        "random.seed(int(time.time() * 1000)) (CPython seeds MT19937 with two 32-bit words above 2^32). Every UTC month of 2012-01 .. 2014-01, "
        "newest first, section 0.7, boundary-free bigram score, then a whole-section check of the best rows with independently built keys against "
        "random timestamps. With a validated GPU: work/phpmt/time_gpu.py (the desktop's 64-bit port bgmt64.cu, gate tests/test_bgmt64; java, py3, "
        "java-abs, and 'ruby' = Ruby's documented seeding and rand(n) rule on CPython's MT19937, not checked against a Ruby; about 9 h for all). "
        "Without one: work/prngx/time_campaign.py on the CPU (gate tests/test_prngx_time: vectors from CPython and the Java specification, seeds "
        "planted with independent keys found at rank 1, random ciphertext without candidates; about 210 h, so run the newest months with --hours). "
        "Both gates run through run_gate.py and fail on a skipped test.",
        prng_time_steps(T), prng_time_summary))
    return C


def copy_json(src, dst, top=None):
    """Copy a dictionary screen's JSON from work/tmp/phase4 into results/screens (optionally the top rows)."""
    p = WORK / "tmp" / "phase4" / src
    if not p.exists():
        return
    data = json.loads(p.read_text(encoding="utf-8"))
    if top is not None and isinstance(data, list):
        data = data[:top]
    (RES / "screens").mkdir(parents=True, exist_ok=True)
    (RES / "screens" / dst).write_text(json.dumps(data), encoding="utf-8")


def merge_chunks(family, sub, out_name, log):
    """Merge chunked kscreen TSVs into one file in the screen's own format."""
    rows, wbest, runs, aborted, secs, header = [], {}, 0, 0, 0, None
    files = sorted((RES / "kscreen" / sub).glob("chunk*.tsv"))
    if len(files) < LIN3_CHUNKS:
        print(f"only {len(files)} of {LIN3_CHUNKS} chunks present", file=log)
        return False
    for f in files:
        for line in open(f, encoding="utf-8"):
            line = line.rstrip("\n")
            if line.startswith("# kscreen"):
                header = line
                m = re.search(r"runs=(\d+) aborted=(\d+) secs=(\d+)", line)
                runs, aborted, secs = runs + int(m.group(1)), aborted + int(m.group(2)), secs + int(m.group(3))
            elif line.startswith("# window"):
                w, b = line.split()[2], float(line.split()[4])
                if b > wbest.get(w, (0.0, ""))[0]:
                    wbest[w] = (b, line)
            elif line and not line.startswith("#") and not line.startswith("ioc"):
                rows.append(line)
    rows.sort(key=lambda r: -float(r.split("\t")[0]))
    header = re.sub(r"runs=\d+ aborted=\d+ secs=\d+", f"runs={runs} aborted={aborted} secs={secs}", header)
    with open(RES / "kscreen" / out_name, "w", newline="\n", encoding="utf-8") as f:
        f.write(header + "\n")
        f.write(f"# best {float(rows[0].split(chr(9))[0]) if rows else 0:.4f}\n")
        for _, line in sorted(wbest.values(), key=lambda t: t[1]):
            f.write(line + "\n")
        f.write("ioc\titem\toffset\tmult\tmodel\twindow\tn\n")
        for r in rows[:2000]:
            f.write(r + "\n")
    print(f"merged {len(files)} chunks, {runs} decodes", file=log)
    return True


def dsearch_steps(T):
    out = RES / "walk"
    data = WORK / "walk" / "data"
    tmp = WORK / "tmp" / "walk"
    iters, restarts, nsur = 600_000, max(16, T), 4
    steps = [
        Step("dsearch/control-synth", [str(WALK_BIN), "synth", str(data / "english_test.txt"), str(tmp / "synth5.txt"),
                                       str(tmp / "synth5_truth.txt"), "5", "1", "0.18"],
             hours=0.01, outputs=[tmp / "synth5.txt", tmp / "synth5_truth.txt"]),
        Step("dsearch/control-recover", [str(WALK_BIN), "dsearch", str(tmp / "synth5.txt"), "5", "1", "300000",
                                         str(max(16, T)), str(T), str(tmp / "synth5_truth.txt")],
             hours=0.05, outputs=[out / "dsearch_control.txt"], stdout_to=out / "dsearch_control.txt"),
    ]
    for s in range(1, nsur + 1):
        steps.append(Step(f"dsearch/surrogate{s}", [str(WALK_BIN), "surrogate", str(data / "lp2.txt"),
                                                    str(data / "sur" / f"sur{s}.txt"), str(s), "0.18"],
                          hours=0.01, outputs=[data / "sur" / f"sur{s}.txt"]))
    for m in (1, 2, 3, 4, 5, 6, 7, 8):
        for gaps in ("1,2", "1,2,3"):
            tag = f"m{m}_g{gaps.replace(',', '')}"
            for k, text in enumerate([data / "lp2.txt"] + [data / "sur" / f"sur{s}.txt" for s in range(1, nsur + 1)]):
                who = "lp2" if k == 0 else f"sur{k}"
                steps.append(Step(f"dsearch/{tag}-{who}", [str(WALK_BIN), "dsearch", str(text), str(m), gaps, str(iters),
                                                          str(restarts), str(T)],
                                  hours=0.07 if gaps == "1,2" else 0.1,
                                  outputs=[out / "dsearch_big" / f"{tag}_{who}.txt"],
                                  stdout_to=out / "dsearch_big" / f"{tag}_{who}.txt"))
    return steps


def dsearch_summary():
    out = []
    c = last_line(RES / "walk" / "dsearch_control.txt", "agrees with truth")
    out.append(f"- positive control (synthetic m=5): {c or 'not run'}")
    d = RES / "walk" / "dsearch_big"
    if not d.exists():
        return out + ["- not run yet"]
    tags = sorted({p.name.rsplit("_", 1)[0] for p in d.glob("*_lp2.txt")})
    for tag in tags:
        def best(p):
            m = re.search(r"best G (\d+)", p.read_text(encoding="utf-8")) if p.exists() else None
            return int(m.group(1)) if m else None
        lp2 = best(d / f"{tag}_lp2.txt")
        sur = [b for b in (best(p) for p in sorted(d.glob(f"{tag}_sur*.txt"))) if b is not None]
        if lp2 is None:
            continue
        flag = ""
        if sur:
            mu = sum(sur) / len(sur)
            sd = (sum((x - mu) ** 2 for x in sur) / max(1, len(sur) - 1)) ** 0.5
            z = (lp2 - mu) / sd if sd > 0 else 0.0
            flag = f"surrogates {sur} (z = {z:+.1f})" + ("  **LP2 stands out**" if lp2 > max(sur) and z > 4 else "")
        out.append(f"- {tag}: LP2 best G {lp2}; {flag}")
    return out


def prng_steps(T):
    steps = []
    for gen, hi in (("php", 2 ** 32), ("glibc", 2 ** 32), ("net", 2 ** 31)):
        tsv = RES / "prng" / f"{gen}_all.tsv"
        log = RES / "prng" / f"{gen}_all.log"
        args = [gen, str(WORK / "phpmt" / "data" / "windows.txt"), str(WORK / "phpmt" / "data" / "dict.txt"), "0", str(hi),
                str(tsv), str(T)]
        hours = 8.0 if hi == 2 ** 32 else 4.0
        done = lambda log=log: "swept" in log.read_text(encoding="utf-8", errors="replace") if log.exists() else False
        cpu = [str(PHPMT_BIN), "sweep", *args]
        if DEVICE == "cuda":
            steps.append(Step(f"prng-all/{gen}", [PY, str(PH_GPU), "sweep", *args], hours=hours / GPU_SPEEDUP["prng"],
                              outputs=[tsv], stderr_to=log, done_check=done, device="cuda", alt=cpu))
        else:
            steps.append(Step(f"prng-all/{gen}", cpu, hours=hours, outputs=[tsv], stderr_to=log, done_check=done))
        ver = RES / "prng" / f"{gen}_all_verify.txt"
        steps.append(Step(f"prng-all/{gen}-verify", [PY, "work/phpmt/verify_top.py", str(tsv), "--gen", gen],
                          hours=0.1, outputs=[ver], stdout_to=ver))
    return steps


NEW_GENS = ("java", "msvc", "drand48", "mt31", "mt32", "ruby", "py3")      # cheapest sweeps first (java, msvc and drand48 take ~3 min per window on the GPU)


def prng_more_steps(T, tags=("07", "all")):
    """The generators of work/phpmt/src/gens.rs: window 0.7 only (one pad from the start of LP2) and/or every section."""
    steps = []
    for tag, wfile, hours in [t for t in (("07", "windows_07.txt", 0.7), ("all", "windows.txt", 5.4)) if t[0] in tags]:
        for gen in NEW_GENS:
            tsv = RES / "prng" / f"{gen}_{tag}.tsv"
            log = RES / "prng" / f"{gen}_{tag}.log"
            args = [gen, str(WORK / "phpmt" / "data" / wfile), str(WORK / "phpmt" / "data" / "dict.txt"), "0", str(2 ** 32),
                    str(tsv), str(T)]
            done = lambda log=log: "swept" in log.read_text(encoding="utf-8", errors="replace") if log.exists() else False
            if DEVICE == "cuda":       # no CPU fallback: a CPU sweep of 2^32 seeds is hours per generator
                steps.append(Step(f"prng-more/{gen}-{tag}", [PY, str(PH_GPU), "sweep", *args], hours=hours / GPU_SPEEDUP["prng"],
                                  outputs=[tsv], stderr_to=log, done_check=done, device="cuda"))
            else:
                steps.append(Step(f"prng-more/{gen}-{tag}", [str(PHPMT_BIN), "sweep", *args], hours=hours, outputs=[tsv],
                                  stderr_to=log, done_check=done))
            ver = RES / "prng" / f"{gen}_{tag}_verify.txt"
            steps.append(Step(f"prng-more/{gen}-{tag}-verify", [PY, "work/phpmt/verify_top.py", str(tsv), "--gen", gen],
                              hours=0.1, outputs=[ver], stdout_to=ver))
    return steps


def prng_more_summary(tags=("07", "all")):
    out = []
    for tag, what in [t for t in (("07", "window 0.7 (one pad from the start of LP2)"), ("all", "every section")) if t[0] in tags]:
        out.append(f"- {what}:")
        for gen in NEW_GENS:
            sw = last_line(RES / "prng" / f"{gen}_{tag}.log", "swept")
            ver = last_line(RES / "prng" / f"{gen}_{tag}_verify.txt")
            out.append(f"  - {gen}: {sw or 'not run'}" + (f"; verification: {ver}" if ver else ""))
    return out


def prng_summary():
    out = []
    for gen in ("php", "glibc", "net"):
        sw = last_line(RES / "prng" / f"{gen}_all.log", "swept")
        ver = last_line(RES / "prng" / f"{gen}_all_verify.txt")
        out.append(f"- {gen}: {sw or 'not run'}" + (f"; verification: {ver}" if ver else ""))
    return out


# ---------------------------------------------------------------- device

def detect_device(want):
    """'cpu' or 'cuda'. --device auto uses CUDA only if it works AND reproduces the CPU engines (docs/GPU_PORT.md gates):
    probe, decode-by-decode selfchecks of both ports, and the planted-key controls through the GPU screen. The record is
    results/overnight/<machine>/gpu_validation.txt. On any failure auto falls back to the CPU engines; cuda stops."""
    if want == "cpu":
        say("device", "cpu (--device cpu)")
        return "cpu"
    checks = [("CUDA probe", [PY, str(KS_GPU), "probe"]),
              ("kscreen port, decode by decode", [PY, str(KS_GPU), "selfcheck"]),
              ("seed-sweep port, decode by decode", [PY, str(PH_GPU), "selfcheck"]),
              ("kscreen planted-key controls through CUDA", [PY, str(KS / "selftest.py"), "--engine", "cuda", "--out", str(SELFTEST_CUDA)])]
    lines, fail = [], None
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1")
    for name, cmd in checks:
        if not (KS_GPU.exists() and PH_GPU.exists() and KS_BIN.exists() and PHPMT_BIN.exists()):
            fail = "the CUDA ports or the CPU engines are missing"
            break
        t0 = time.time()
        try:
            r = subprocess.run(cmd, cwd=KS if "selftest" in str(cmd[1]) else ROOT, capture_output=True, text=True, env=env,
                               timeout=900)
            out, ok = (r.stdout.strip().splitlines() or [""])[-1] or (r.stderr.strip().splitlines() or [""])[-1], r.returncode == 0
        except (OSError, subprocess.TimeoutExpired) as e:
            out, ok = f"{type(e).__name__}", False
        lines.append(f"{'ok  ' if ok else 'FAIL'} {name}: {scrub(out)} ({time.time() - t0:.0f} s)")
        say("device", lines[-1])
        if not ok:
            fail = name
            break
    OVM.mkdir(parents=True, exist_ok=True)
    verdict = "GPU VALIDATION PASSED" if fail is None else f"GPU VALIDATION FAILED: {fail}"
    atomic_write(GPU_VALIDATION, "\n".join([f"{time.strftime('%Y-%m-%d %H:%M:%S')} on {MACHINE}", *lines, verdict]) + "\n")
    if fail is None:
        say("device", "cuda: validated, GPU backends will be used for the kscreen screens and the seed sweeps")
        return "cuda"
    if want == "cuda":
        sys.exit(f"--device cuda requested but {verdict}")
    say("device", f"cpu: CUDA not used ({fail}); the CPU engines run unchanged")
    return "cpu"


# ---------------------------------------------------------------- running

def load_state():
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {}


def record_state(sid, entry):
    """Set one step's entry. Lanes share the file, so re-read it first and replace it atomically."""
    OVM.mkdir(parents=True, exist_ok=True)
    st = load_state()
    st[sid] = entry
    atomic_write(STATE, json.dumps(st, indent=1))


def atomic_write(path, text):
    tmp = Path(str(path) + f".{os.getpid()}.tmp")
    tmp.write_text(text, encoding="utf-8", newline="\n")
    for attempt in range(20):                            # another lane may have the target open for a moment (Windows)
        try:
            os.replace(tmp, path)
            return
        except PermissionError:
            time.sleep(0.25)
    tmp.unlink(missing_ok=True)


CON_EVERY = 15      # console: at most one progress line per step every 15 s
LOG_EVERY = 30      # logs: at most one progress line every 30 s (the newest skipped one is kept for the end)
HEARTBEAT = 60      # console: a line when a step has been silent this long (s)
# The Rust engines print "12.50% (123 seeds) 820000 seeds/s, eta 90 s"; the Python screens print "k/N ...".
RE_ENGINE = re.compile(r"^\s*(\d+(?:\.\d+)?)%\s+\(([\d,]+) (\w+)\)\s+([\d.]+) (\w+)/s, eta (\d+) s")
RE_FRAC = re.compile(r"^\s*(\d+)/(\d+)\b")


def hms(sec):
    sec = int(max(0, sec))
    h, r = divmod(sec, 3600)
    m, s = divmod(r, 60)
    return f"{h}h{m:02d}m" if h else f"{m}m{s:02d}s" if m else f"{s}s"


def say(label, msg):
    print(f"[{time.strftime('%H:%M:%S')}] [{label}] {msg}", flush=True)


def classify(line, elapsed):
    """(is_progress, console text) for one output line."""
    m = RE_ENGINE.match(line)
    if m:
        pct, n, unit, rate, runit, eta = m.groups()
        return True, f"{float(pct):6.2f}%  {int(n.replace(',', '')):,} {unit}  {float(rate):,.0f} {runit}/s  eta {hms(int(eta))}"
    m = RE_FRAC.match(line)
    if m and 0 < int(m.group(1)) <= int(m.group(2)):
        k, n = int(m.group(1)), int(m.group(2))
        return True, f"{100 * k / n:6.2f}%  {line.strip()}  eta ~{hms(elapsed * (n - k) / k)}"
    return False, line


class Throttled:
    """Line writer for a log: progress lines at most once per `every` s. The newest skipped progress line is
    written before the next ordinary line, so a log still ends with its final 100% line."""

    def __init__(self, f, every=LOG_EVERY):
        self.f, self.every, self.last, self.pending = f, every, 0.0, None

    def write(self, text, progress):
        text = scrub(text)
        if progress and time.time() - self.last < self.every:
            self.pending = text
            return
        if self.pending is not None and not progress:
            self.f.write(self.pending + "\n")
        self.f.write(text + "\n")
        self.f.flush()
        if progress:
            self.last = time.time()
        self.pending = None

    def close(self):
        if self.pending is not None:
            self.f.write(self.pending + "\n")
        self.f.flush()


def pump(fd, tag, q):
    """Read a child's pipe in chunks and queue (tag, line, ended_by_CR). Lines end at \\n, \\r\\n or a bare \\r
    (what progress bars use); None marks the end of the stream."""
    buf = b""
    while True:
        chunk = os.read(fd, 65536)
        if not chunk:
            break
        buf += chunk
        hold = b"\r" if buf.endswith(b"\r") else b""        # a trailing \r may be half of \r\n
        parts = re.split(rb"(\r\n|\n|\r)", buf[:len(buf) - len(hold)])
        buf = parts.pop() + hold
        for i in range(0, len(parts), 2):
            q.put((tag, parts[i].decode("utf-8", "replace"), parts[i + 1] == b"\r"))
    if buf.strip():
        q.put((tag, buf.decode("utf-8", "replace").rstrip("\r"), False))
    q.put((tag, None, False))


def run_cmd(step, env, log, label):
    """Run a command step and stream its output: live to the console (timestamped, progress throttled, a
    heartbeat when silent), to the step's log (progress throttled) and to its output files. Returns the exit code."""
    # stdout goes to <file>.part and is renamed only on success, so an interrupted step never leaves an
    # output that looks finished; it is written in full (it is the result), only the log copy is throttled
    part = Path(str(step.stdout_to) + ".part") if step.stdout_to else None
    part_f = open(part, "w", encoding="utf-8", newline="\n") if part else None
    err_f = open(step.stderr_to, "w", encoding="utf-8", newline="\n") if step.stderr_to else None
    log_w = Throttled(log)
    err_w = Throttled(err_f) if err_f else log_w
    write = {"out": (lambda t, p: part_f.write(t + "\n")) if part_f else log_w.write, "err": err_w.write}
    t0 = time.time()
    proc = subprocess.Popen([str(c) for c in step.cmd], cwd=step.cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            env=env, bufsize=0)
    q = queue.Queue()
    for tag, pipe in (("out", proc.stdout), ("err", proc.stderr)):
        threading.Thread(target=pump, args=(pipe.fileno(), tag, q), daemon=True).start()
    open_streams, last_say, last_prog, last_text, skipped = 2, time.time(), 0.0, "", None
    try:
        while open_streams:
            try:
                tag, text, cr = q.get(timeout=1.0)
            except queue.Empty:
                if time.time() - last_say >= HEARTBEAT:
                    say(label, f"still running ({hms(time.time() - t0)}), last output: {last_text[:100] or '(none yet)'}")
                    last_say = time.time()
                continue
            if text is None:
                open_streams -= 1
                continue
            if not text.strip():
                if part_f and tag == "out":
                    part_f.write("\n")
                continue
            progress, shown = classify(text, time.time() - t0)
            progress = progress or cr
            write[tag](text, progress)
            last_text = shown.strip()
            if progress and time.time() - last_prog < CON_EVERY:
                skipped = shown                      # shown later if nothing else follows: the final 100% line
                continue
            if skipped and not progress:
                say(label, skipped)
            skipped = None
            say(label, shown)
            last_say = time.time()
            if progress:
                last_prog = last_say
        if skipped:
            say(label, skipped)
        for pipe in (proc.stdout, proc.stderr):
            pipe.close()
    finally:
        if proc.poll() is None:
            proc.kill()
        log_w.close()
        for f, w in ((err_f, err_w), (part_f, None)):
            if f:
                if w:
                    w.close()
                f.close()
    return proc.wait()


def run_step(step, dry, label=""):
    LOGS.mkdir(parents=True, exist_ok=True)
    logp = LOGS / (step.id.replace("/", "__") + ".log")
    for p in step.outputs:
        Path(p).parent.mkdir(parents=True, exist_ok=True)
    if dry:
        print(f"   would run: {step.cmd if callable(step.cmd) else ' '.join(map(str, step.cmd))}")
        return True
    env = dict(os.environ, PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONUNBUFFERED="1")
    t0 = time.time()
    with open(logp, "w", encoding="utf-8", newline="\n") as log:
        if callable(step.cmd):
            ok = bool(step.cmd(log))
        else:
            log.write(scrub(f"# {' '.join(map(str, step.cmd))}\n# cwd {step.cwd}\n# device {step.device}\n"))
            log.flush()
            rc = run_cmd(step, env, log, label)
            ok = rc == 0
            if step.stdout_to:
                part = Path(str(step.stdout_to) + ".part")
                os.replace(part, step.stdout_to if ok else Path(str(step.stdout_to) + ".failed"))
            log.write(f"\n# exit code {rc}, {time.time() - t0:.0f} s\n")
    if ok and step.post:
        step.post()
    if ok and step.id == "selftest/unittests":
        UNITTESTS.write_text(time.strftime("%Y-%m-%d %H:%M:%S"), encoding="utf-8")
    # tracked text outputs must not carry this PC's paths or name (the repository may become public)
    for p in [logp, step.stdout_to, step.stderr_to, *step.outputs]:
        if p:
            scrub_file(p)
    return ok


def pid_alive(pid):
    if os.name == "nt":
        import ctypes
        k = ctypes.windll.kernel32
        h = k.OpenProcess(0x1000, False, pid)            # PROCESS_QUERY_LIMITED_INFORMATION
        if not h:
            return False
        code = ctypes.c_ulong()
        ok = k.GetExitCodeProcess(h, ctypes.byref(code))
        k.CloseHandle(h)
        return bool(ok) and code.value == 259           # STILL_ACTIVE
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def take_lock():
    """One runner at a time: two would race on the same outputs and halve each other's speed."""
    OVM.mkdir(parents=True, exist_ok=True)
    lock = OVM / ("runner.lock" if LANE == "main" else f"runner.{LANE}.lock")
    if lock.exists():
        try:
            pid = int(lock.read_text().strip())
        except ValueError:
            pid = -1
        if pid > 0 and pid != os.getpid() and pid_alive(pid):
            sys.exit(f"another overnight.py run is active in lane {LANE!r} (pid {pid}); wait for it, stop it, or use --lane")
    lock.write_text(str(os.getpid()))
    import atexit
    atexit.register(lambda: lock.unlink(missing_ok=True))


def cmd_run(args):
    global DEVICE
    if not args.dry_run:
        take_lock()
    T = args.threads
    DEVICE = "cpu" if args.dry_run and args.device == "auto" else detect_device(args.device)
    cs = campaigns(T)
    names = [c.name for c in cs]
    want = args.campaigns or names
    bad = [w for w in want if w not in names]
    if bad:
        sys.exit(f"unknown campaign(s) {bad}; known: {names}")
    if "setup" not in want:
        want = ["setup"] + list(want)
    t_start = time.time()
    budget = args.hours * 3600 if args.hours else None
    todo = [s for c in cs if c.name in want for s in c.steps if args.force or not s.done()]
    N, k, ran, touched = len(todo), 0, [], []
    say("overnight", f"{MACHINE} lane {LANE}: {len(want)} campaigns, {N} steps to run (~{sum(s.hours for s in todo):.1f} h by "
                     f"the rough estimates), {T} threads, device {DEVICE}" + (f", budget {args.hours} h" if budget else ""))
    stopped = None
    for c in cs:
        if c.name not in want or stopped:
            continue
        touched.append(c)
        print(f"\n== {c.name}: {c.title}", flush=True)
        for s in c.steps:
            if s.done() and not args.force:
                say("overnight", f"done  {s.id}")
                continue
            elapsed = time.time() - t_start
            if budget and not s.always and elapsed > 0 and elapsed + s.hours * 3600 > budget:
                stopped = f"budget reached before {s.id} (est. {s.hours:.1f} h); stopping. Rerun to continue."
                break
            k += 1
            label = f"{k}/{N} {s.id} {s.device}"
            say(label, f"start (est. {s.hours:.2f} h)")
            t0 = time.time()
            ok = run_step(s, args.dry_run, label)
            dev = s.device
            if not ok and s.alt and not args.dry_run:        # the CUDA run failed: the CPU engine is the reference, rerun on it
                say(label, "FAILED on cuda; rerunning this step on the CPU engine")
                ok, dev = run_step(replace(s, cmd=s.alt, device="cpu", alt=None), False, label.replace(" cuda", " cpu")), "cpu (cuda failed)"
            dt = time.time() - t0
            say(label, f"{'ok' if ok else 'FAILED'} in {hms(dt)}")
            ran.append((s.id, ok, dt, dev))
            if not args.dry_run:
                record_state(s.id, {"ok": ok, "minutes": round(dt / 60, 1), "device": dev,
                                    "finished": time.strftime("%Y-%m-%d %H:%M:%S")})
            if not ok:
                say("overnight", f"{c.name}: stopping this campaign after a failed step (log: {LOGS})")
                break
        write_report(cs, load_state())
    write_report(cs, load_state())
    print_summary(ran, touched, stopped, time.time() - t_start)


def print_summary(ran, touched, stopped, secs):
    print(f"\n[{time.strftime('%H:%M:%S')}] ===== summary: {MACHINE}, {hms(secs)} =====")
    if stopped:
        print(stopped)
    for sid, ok, dt, dev in ran:
        print(f"  {'ok    ' if ok else 'FAILED'} {sid:46s} {dev:5s} {hms(dt):>8s}")
    if not ran:
        print("  nothing to run: every step already has its output (--force reruns)")
    for c in touched:
        if c.summarize and c.name != "setup":
            print(f"\n{c.name}: {c.title}")
            for line in c.summarize():
                print("  " + line)
    print(f"\nreport: results/overnight/{MACHINE}/REPORT.md")


def write_report(cs, st):
    OVM.mkdir(parents=True, exist_ok=True)
    lines = [f"# Overnight campaigns: report from {MACHINE}", "",
             f"Generated on {MACHINE} at {time.strftime('%Y-%m-%d %H:%M:%S')} by `python jobs/overnight.py`. "
             "Thresholds and method: docs/CAMPAIGNS.md.", ""]
    valid = selftest_ok() and UNITTESTS.exists()
    lines.append("**Controls:** " + (f"unit tests and kscreen selftest passed on {MACHINE}; null results below are validated." if valid else
                                     f"the selftest has NOT passed on {MACHINE}; treat every null below as unvalidated."))
    for c in cs:
        done = sum(s.done() for s in c.steps if not s.always)
        total = sum(1 for s in c.steps if not s.always)
        lines += ["", f"## {c.name}: {c.title} ({done}/{total} steps done)", "", c.why, ""]
        if c.summarize:
            try:
                lines += c.summarize()
            except Exception as e:  # noqa: BLE001
                lines.append(f"- (summary failed: {e})")
        failed = [s.id for s in c.steps if st.get(s.id, {}).get("ok") is False and not s.done()]
        if failed:
            lines.append(f"- failed steps: {', '.join(failed)} (see results/overnight/{MACHINE}/logs/)")
    (OVM / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def cmd_list(args):
    global DEVICE
    DEVICE = "cuda" if args.device == "cuda" else "cpu"   # list does not probe the GPU; --device cuda shows the CUDA estimates
    cs = campaigns(args.threads)
    tot = 0.0
    for c in cs:
        h = sum(s.hours for s in c.steps)
        tot += h
        done = sum(s.done() for s in c.steps if not s.always)
        n = sum(1 for s in c.steps if not s.always)
        print(f"{c.name:22s} ~{h:5.1f} h  {done:3d}/{n:<3d} done  {c.title}")
        if args.verbose:
            for s in c.steps:
                print(f"    {'x' if s.done() else ' '} {s.id}  ({s.hours:.2f} h)")
    print(f"{'total':22s} ~{tot:5.1f} h (rough, 16-thread desktop CPU); this machine: {MACHINE}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["list", "run", "report"])
    ap.add_argument("campaigns", nargs="*")
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--device", choices=["auto", "cuda", "cpu"], default="auto",
                    help="auto: CUDA if it works and reproduces the CPU engines, else CPU; cuda: stop if it does not; cpu")
    ap.add_argument("--lane", default="main", help="runner lane; lanes run at once (e.g. a GPU lane and a CPU lane)")
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    global LANE
    LANE = re.sub(r"[^A-Za-z0-9_.-]", "_", args.lane)[:20] or "main"
    for s in (sys.stdout, sys.stderr):                  # runes in a step's output must not crash a cp1252 console
        s.reconfigure(errors="replace")
    if shutil.which("cargo") is None and args.action == "run":
        sys.exit("cargo not found: install Rust from https://rustup.rs first")
    if args.action == "list":
        cmd_list(args)
    elif args.action == "run":
        cmd_run(args)
    else:
        write_report(campaigns(args.threads), load_state())
        print((OVM / "REPORT.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    main()
