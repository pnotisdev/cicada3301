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
    out.append(f"- {len(lb)} windows of 300 steps, 1,447 library streams x every offset x variants A/B x modes drop/keep x 12 multipliers: "
               f"best IoC {top[1]:.3f} ({top[0]})")
    if nulls:
        nmax = {w: max(n.get(w, 0) for n in nulls) for w in lb}
        above = [w for w in lb if lb[w] > nmax[w] + 0.02 and lb[w] >= 1.30]
        out.append(f"- matched null ({len(nulls)} replicates of random streams, same pair count): largest per-window best "
                   f"{max(nmax.values()):.3f}; windows where the library beats every replicate by 0.02 and reaches 1.30: "
                   + (", ".join(above) if above else "none"))
    ver = last_line(RES / "kscreen" / "step28_library_verify.txt")
    if ver:
        out.append(f"- verification (best window continued to the end of its section): {ver}")
    per = RES / "analysis" / "step_periodicity.txt"
    if per.exists():
        out.append(f"- periodic keys (scan of coincidences at lag 2..3000): {last_line(per) or ''}")
    return out


STEP_GENS = ("py3", "php", "glibc", "java", "mt32", "net", "msvc", "drand48", "ruby", "mt31")
STEP_SELFTEST = OVM / "prng_step_selftest.txt"


def prng_step_steps():
    """seed sweeps of the step-domain cipher: CUDA only (2^32 seeds x 96 settings per generator is about an hour on the GPU)"""
    if DEVICE != "cuda":
        return []
    steps = [Step("prng-step/controls", [PY, "-m", "unittest", "work.tests.test_stepmt", "-v"], hours=0.02, outputs=[STEP_SELFTEST],
                  always=True, stderr_to=STEP_SELFTEST, device="cuda")]
    for gen in STEP_GENS:
        tsv = RES / "prng" / f"step_{gen}_07.tsv"
        log = RES / "prng" / f"step_{gen}_07.log"
        ver = RES / "prng" / f"step_{gen}_07_verify.txt"
        done = lambda log=log: "swept" in log.read_text(encoding="utf-8", errors="replace") if log.exists() else False
        steps.append(Step(f"prng-step/{gen}", [PY, str(WORK / "phpmt" / "step.py"), "sweep", gen, "07", "0", str(2 ** 32), str(tsv)],
                          hours=1.0, outputs=[tsv], stderr_to=log, done_check=done, device="cuda"))
        steps.append(Step(f"prng-step/{gen}-verify", [PY, str(WORK / "phpmt" / "step_verify.py"), str(tsv), "--gen", gen],
                          hours=0.05, outputs=[ver], stdout_to=ver))
    return steps


def prng_step_summary():
    out = [f"- controls: {last_line(STEP_SELFTEST, r'^(OK|FAILED)') or 'not run'}"]
    for gen in STEP_GENS:
        sw = last_line(RES / "prng" / f"step_{gen}_07.log", "swept")
        ver = last_line(RES / "prng" / f"step_{gen}_07_verify.txt")
        out.append(f"- {gen}: {sw or 'not run'}" + (f"; best candidate: {ver}" if ver else ""))
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
        "kscreen-step28", "Relative-rank chain cipher: the plaintext enters the STEP c_i - c_{i-1}, keyed mod 28",
        "The doublet fingerprint is also what a cipher gives whose ciphertext step is never zero (research note C1, "
        "work/log/research_2026-10-17.md): D_i = 1 + (q_i + m*K_j) mod 28 (variant A) or 2^(q_i + m*log K_j) (variant B), with "
        "the rare zero step as a 'ditto' that consumes a key value or not. In the c domain the plaintext is a random walk and "
        "every earlier screen was blind to it; in the step domain the decoder is a plain subtraction with no beam. "
        "work/kscreen/step28.py counts the class histogram at every (stream, offset) for the 1,447-stream library and every "
        "unit multiplier of Z28, with planted-key recovery (both variants and modes), CPU/CUDA agreement and matched nulls; "
        "work/step_periodicity.py scans periodic keys (lags to 3,000).",
        step28_steps(), step28_summary))

    C.append(Campaign(
        "prng-step", "Seeded-PRNG pads for the step-domain cipher, window 0.7: all ten generators",
        "Research note C2: the seed sweeps of the ordinary cipher (c = p + k) cannot see a key that enters the STEP "
        "c_i - c_{i-1}. work/phpmt/step.py runs the ten generators of phpmt.cu over all 2^32 seeds and scores, per seed, 96 "
        "settings on the first 240 steps of section 0.7 (variant A with keys mod 28 / variant B with log2 of the non-zero "
        "keys of Z29, both key maps, zero steps spending a key value or not, the 12 unit multipliers of Z28) by the index "
        "of coincidence of the decoded classes. Gates: keys equal the Rust engine for both alphabets, scores equal the numpy "
        "reference, planted seeds recovered for every generator, random ciphertext gives no candidate (work/tests/test_stepmt.py).",
        prng_step_steps(), prng_step_summary))
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


NEW_GENS = ("py3", "mt32", "mt31", "java", "msvc", "drand48", "ruby")


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
