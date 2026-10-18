"""Read-only inputs and isolated, privacy-scrubbed outputs for human-run experiments."""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path
import re
import sys
import time
from datetime import datetime, timezone
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
WORK = HERE.parent


def repo_path(value: str | Path) -> Path:
    path = Path(value)
    path = (ROOT / path).resolve() if not path.is_absolute() else path.resolve()
    if not path.is_relative_to(ROOT):
        raise ValueError("Inputs and outputs must stay inside the repository")
    return path


def relative(path: str | Path) -> str:
    return repo_path(path).relative_to(ROOT).as_posix()


def sha256(path: str | Path) -> str:
    return hashlib.sha256(repo_path(path).read_bytes()).hexdigest()


def scrub(text: object) -> str:
    text = str(text)
    private = [str(ROOT), ROOT.as_posix()]
    private += [os.environ.get(k, "") for k in
                ("USERPROFILE", "HOME", "COMPUTERNAME", "USERNAME", "USER")]
    for value in sorted(set(private), key=len, reverse=True):
        if len(value) >= 3:
            text = re.sub(re.escape(value), "<private>", text, flags=re.IGNORECASE)
    return text


class Run:
    """Each invocation gets a NEW directory, never an existing runner's files."""
    def __init__(self, command: str, seconds: float = 900):
        if seconds <= 0:
            raise ValueError("seconds must be positive")
        alias_file = ROOT / ".lp_machine"
        alias = alias_file.read_text(encoding="utf-8").strip() if alias_file.exists() else "manual"
        if alias not in ("laptop", "desktop"):
            alias = "manual"
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        self.directory = ROOT / "results" / "independent" / alias / f"{stamp}-{command}-{uuid.uuid4().hex[:6]}"
        self.directory.mkdir(parents=True, exist_ok=False)
        self.file = (self.directory / "run.log").open("x", encoding="utf-8", newline="\n", buffering=1)
        self.start = time.monotonic()
        self.seconds = seconds
        if hasattr(sys.stdout, "reconfigure"):
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        self.log(f"Command: {command}; output: {relative(self.directory)}")
        self.log("CPU only; no network, builds, background jobs, or shared-engine writes.")
        self.log("Nothing in LP2 is solved. These are bounded hypothesis tests, not translations.")

    def log(self, message: object):
        line = f"[{time.monotonic() - self.start:8.1f}s] {scrub(message)}"
        print(line, flush=True)
        self.file.write(line + "\n")

    def check(self):
        if time.monotonic() - self.start > self.seconds:
            raise TimeoutError("Time budget reached: INCOMPLETE, not a negative result")

    def save(self, name: str, value: object):
        # Artifact names are supplied by our code, never by external documents.
        if Path(name).name != name:
            raise ValueError("Artifact must be a simple file name")
        with (self.directory / name).open("x", encoding="utf-8", newline="\n") as f:
            json.dump(value, f, indent=2, ensure_ascii=True, allow_nan=False)
            f.write("\n")

    def close(self):
        self.file.close()


def lp_module():
    # Do not import export.py, GPU modules, proposals, or anything in work/tmp/.
    if str(WORK) not in sys.path:
        sys.path.insert(0, str(WORK))
    import lp
    return lp


def reference_model():
    """Proper bigram probabilities, trained ONLY on the committed Emerson reference."""
    lp = lp_module()
    path = WORK / "ref" / "emerson_essays1.txt"
    text = path.read_text(encoding="utf-8")
    marker = text.find("SELF-RELIANCE")
    if marker < 0:
        raise ValueError("Reference corpus lacks the expected marker")
    text = text[marker:].split("*** END OF")[0]
    stream = [r for word in re.findall(r"[A-Za-z]+", text)
              for r in lp.word_to_key(word.upper().replace("IO", "IA"))]
    if len(stream) < 10000:
        raise ValueError("Reference corpus is unexpectedly short")
    counts = [[0.5] * 29 for _ in range(30)]
    for a, b in zip(stream, stream[1:]):
        counts[a][b] += 1
    for b in stream:
        counts[29][b] += 1
    logs = [[math.log(v / sum(row)) for v in row] for row in counts]
    return logs, {"path": relative(path), "sha256": sha256(path), "runes": len(stream)}


def fingerprint():
    files = [HERE / name for name in ("manual_common.py", "echo_nulls.py", "test_core.py")]
    files += [WORK / "lp.py", WORK / "ref" / "lp_verified.txt", WORK / "ref" / "emerson_essays1.txt"]
    return {relative(path): sha256(path) for path in files}


def execute(command, function, seconds=900):
    run = Run(command, seconds)
    try:
        if not __debug__:
            raise RuntimeError("Do not use Python -O: it disables assertion-based controls")
        function(run)
        run.log("FINISHED")
        return 0
    except (Exception, KeyboardInterrupt) as exc:
        run.log(f"STOPPED: {type(exc).__name__}: {exc}")
        run.log("FAILED / INCOMPLETE. Do not interpret this as an LP2 negative.")
        return 1
    finally:
        run.close()
