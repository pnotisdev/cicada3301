#!/usr/bin/env python3
"""The `prng-time` window on the GPU: boundary-free sweeps (bg64.py) of every UTC month from 2012-01 to 2014-01 in millisecond timestamps, newest month first, one
file set per (generator, month) under results/prng/time_gpu/ (<gen>_<YYYY-MM>.tsv / .log / _verify.txt). A month already swept (its log has the 'swept' line) is skipped,
so a run can be stopped and resumed, and `--hours H` stops starting new months once the time budget would be exceeded (the length of a month is estimated from the
speed of the months already done, 6.4 M seeds/s on an RTX 2080 Ti when this was written).

    python work/phpmt/time_gpu.py list
    python work/phpmt/time_gpu.py run <py3|ruby|java|java-abs> [--hours H] [--only YYYY-MM]
Window: 2012-01-01 .. 2014-02-01 UTC (1325376000000 .. 1391212800000 ms), section 0.7 (one pad from the first LP2 rune), as in the laptop's prng-time campaign.
"""
import argparse
import calendar
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
OUT = HERE.parent.parent / "results" / "prng" / "time_gpu"


def months():
    """[(label, lo_ms, hi_ms)] newest first"""
    out = []
    for y, m in [(2014, 1)] + [(2013, k) for k in range(12, 0, -1)] + [(2012, k) for k in range(12, 0, -1)]:
        lo = calendar.timegm((y, m, 1, 0, 0, 0)) * 1000
        hi = calendar.timegm((y + (m == 12), m % 12 + 1, 1, 0, 0, 0)) * 1000
        out.append((f"{y}-{m:02d}", lo, hi))
    return out


def done(gen, label):
    log = OUT / f"{gen}_{label}.log"
    return log.exists() and "swept" in log.read_text(encoding="utf-8", errors="replace")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["list", "run"])
    ap.add_argument("gen", nargs="?")
    ap.add_argument("--hours", type=float, default=None)
    ap.add_argument("--only")
    a = ap.parse_args()
    ms = months()
    assert ms[-1][1] == 1325376000000 and ms[0][2] == 1391212800000 and all(ms[i + 1][2] == ms[i][1] for i in range(len(ms) - 1)), "months are not contiguous"
    if a.cmd == "list":
        for label, lo, hi in ms:
            print(f"{label}  {lo} .. {hi}  {(hi - lo):,} seeds  ~{(hi - lo) / 6.4e6 / 60:.1f} min per generator")
        print(f"total {sum(h - l for _, l, h in ms):,} seeds per generator, ~{sum(h - l for _, l, h in ms) / 6.4e6 / 3600:.1f} h")
        return 0
    import bg
    import bg64
    OUT.mkdir(parents=True, exist_ok=True)
    t0, spent, seeds_done = time.time(), 0.0, 0
    for label, lo, hi in ms:
        if a.only and label != a.only:
            continue
        if done(a.gen, label):
            continue
        rate = seeds_done / spent if spent else 6.0e6
        if a.hours is not None and (time.time() - t0 + (hi - lo) / rate) > a.hours * 3600:
            print(f"stop: {label} would exceed the {a.hours} h budget")
            break
        tsv = OUT / f"{a.gen}_{label}.tsv"
        t1 = time.time()
        rows, secs = bg64.sweep(a.gen, "07", lo, hi, str(tsv))
        # the log of bg.py's format (progress lines go to stderr): write the summary line the skip test looks for
        best = max((int(r.split("\t")[0]) for r in rows), default=None)
        (OUT / f"{a.gen}_{label}.log").write_text(f"swept {hi - lo} seeds in {secs:.0f} s; best score {best}; candidates: {len(rows)}\n", encoding="utf-8", newline="\n")
        spent += time.time() - t1
        seeds_done += hi - lo
        with open(OUT / f"{a.gen}_{label}_verify.txt", "w", encoding="utf-8", newline="\n") as f:
            f.write(f"# {a.gen} {label}: {len(rows)} candidates at or above the +300 floor; whole-section check (independent keys) of the best 10\n")
            bg64.verify(rows, a.gen, 10, out=lambda s: f.write(s + "\n"))
        print(f"{a.gen} {label}: {hi - lo:,} seeds in {secs:.0f} s ({(hi - lo) / secs / 1e6:.2f} M/s), best {best}, candidates {len(rows)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
