"""Privacy scan before a commit (CLAUDE.md, Privacy): the computer name, the Windows user name, the home folder and this repository's
absolute path must not appear in any modified or new file, nor the conda or app-data folder names. The names are read from the
environment at run time and the folder names are assembled from pieces, so this file contains none of them.

    python scripts/privacy_scan.py          # prints the hits and exits with 1, or prints 'no hits' and exits with 0
    python scripts/privacy_scan.py --fix    # first scrubs the flagged files with the queue runner's own scrubber (jobs/jobqueue.py scrub_text)
"""
import getpass
import os
import re
import socket
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def pattern():
    names = {getpass.getuser(), socket.gethostname(), os.environ.get("COMPUTERNAME", ""), os.environ.get("USERNAME", "")}
    parts = [re.escape(n) for n in names if len(n) >= 3]
    for p in (str(Path.home()), str(ROOT)):
        parts += [re.escape(p), re.escape(p.replace("\\", "/"))]
    parts += ["mini" + "conda", "App" + "Data", r"[A-Za-z]:\\Users\\", r"[A-Za-z]:/Users/"]
    return re.compile("|".join(parts), re.I)


def scan():
    out = subprocess.run(["git", "ls-files", "-m", "-o", "--exclude-standard", "-z"], cwd=ROOT, capture_output=True, check=True).stdout
    rx, hits, n = pattern(), [], 0
    for rel in filter(None, out.decode("utf-8", "replace").split("\0")):
        f = ROOT / rel
        if not f.is_file():
            continue
        data = f.read_bytes()
        if b"\0" in data[:8000]:
            continue
        n += 1
        for i, line in enumerate(data.decode("utf-8", "ignore").splitlines(), 1):
            if rx.search(line):
                hits.append((rel, i, line.strip()[:160]))
    return hits, n


def main():
    hits, n = scan()
    if hits and "--fix" in sys.argv:
        sys.path.insert(0, str(ROOT / "jobs"))
        import jobqueue
        files = sorted({h[0] for h in hits})
        for rel in files:
            f = ROOT / rel
            f.write_bytes(jobqueue.scrub_text(f.read_bytes().decode("utf-8", "surrogateescape")).encode("utf-8", "surrogateescape"))
        print(f"scrubbed {len(files)} file(s) with jobqueue.scrub_text")
        hits, n = scan()
    for rel, i, line in hits:
        print(f"{rel}:{i}: {line}")
    print(f"{len(hits)} hits in {n} modified or new text files" if hits else f"no hits ({n} modified or new text files scanned)")
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main())
