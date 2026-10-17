"""Resumable hashscan campaign (standalone; does not touch jobs/overnight.py).

    python work/hashscan/campaign.py list
    python work/hashscan/campaign.py run [--tiers lore words dates pairs numbers] [--threads N] [--low]

Builds the candidate lists on first use (make_candidates.py), sweeps each tier over all 4 hashes x 4 stream
conventions x 3 byte maps x 8 cipher variants on windows_07 (the key starts on LP2 page 0), then re-decodes the 20
best over the whole segment against random-string controls. Output: results/hashscan/<tier>.tsv (+ .log, _verify.txt);
finished tiers are skipped. Measured on a 16-thread laptop CPU: about 40k candidates/s, i.e. ~5 min for 10M candidates.
"""
import argparse
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
EXE = os.path.join(HERE, "target", "release", "hashscan" + (".exe" if os.name == "nt" else ""))
DATA = os.path.join(ROOT, "work", "phpmt", "data")
OUT = os.path.join(ROOT, "results", "hashscan")
TIERS = ["lore", "words", "dates", "pairs", "numbers"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["list", "run"])
    ap.add_argument("--tiers", nargs="+", default=TIERS)
    ap.add_argument("--threads", type=int, default=os.cpu_count())
    ap.add_argument("--low", action="store_true")
    a = ap.parse_args()
    os.makedirs(OUT, exist_ok=True)
    if a.action == "run" and not all(os.path.exists(os.path.join(HERE, "data", t + ".txt")) for t in a.tiers):
        subprocess.run([sys.executable, os.path.join(HERE, "make_candidates.py")], check=True,
                       env=dict(os.environ, PYTHONIOENCODING="utf-8"))
    for t in a.tiers:
        tsv = os.path.join(OUT, t + ".tsv")
        print(("done" if os.path.exists(tsv) else "todo"), t)
        if a.action == "list" or os.path.exists(tsv):
            continue
        cmd = [EXE, "sweep", os.path.join(HERE, "data", t + ".txt"), os.path.join(DATA, "windows_07.txt"),
               os.path.join(DATA, "dict.txt"), tsv + ".part", str(a.threads)]
        flags = 0x00004000 if (a.low and os.name == "nt") else 0
        if a.low and os.name != "nt":
            cmd = ["nice", "-n", "10"] + cmd
        t0 = time.time()
        with open(os.path.join(OUT, t + ".log"), "w", encoding="utf-8", newline="\n") as lf:
            rc = subprocess.run(cmd, stderr=lf, creationflags=flags).returncode
        if rc != 0:
            sys.exit(f"sweep failed ({t})")
        os.replace(tsv + ".part", tsv)
        print(f"   {t} finished in {(time.time() - t0) / 60:.1f} min", flush=True)
        with open(os.path.join(OUT, t + "_verify.txt"), "w", encoding="utf-8", newline="\n") as vf:
            subprocess.run([sys.executable, os.path.join(HERE, "verify.py"), tsv, "--top", "20"], stdout=vf,
                           env=dict(os.environ, PYTHONIOENCODING="utf-8"))


if __name__ == "__main__":
    main()
