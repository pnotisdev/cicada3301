"""Runs the keyless probes of work/log/hypotheses_2026-10-17.md and writes results/analysis/hypotheses_2026-10-17.txt.

    python work/tmp/hyp/run_all.py
"""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(ROOT, "results", "analysis", "hypotheses_2026-10-17.txt")


def main():
    parts = ["# Keyless probes for new hypotheses (work/tmp/hyp/probe1-5.py; write-up work/log/hypotheses_2026-10-17.md)\n"]
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    for p in ("probe1.py", "probe2.py", "probe3.py", "probe4.py", "probe5.py"):
        r = subprocess.run([sys.executable, os.path.join(HERE, p)], capture_output=True, text=True, encoding="utf-8", env=env)
        if r.returncode != 0:
            sys.exit(f"{p} failed:\n{r.stderr}")
        parts.append(f"\n## {p}\n\n{r.stdout}")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="\n", encoding="utf-8") as f:
        f.write("".join(parts))
    print(f"wrote {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    main()
