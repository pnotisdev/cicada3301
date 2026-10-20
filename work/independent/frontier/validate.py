"""Validate the review artifact, not cryptanalysis. Standard library; no subprocess.

Run manually: python -B work/independent/frontier/validate.py
Writes only evidence_manifest.json and VALIDATION.md in this directory.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
from pathlib import Path
import re
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
START = time.monotonic()
REPORT = HERE / "REPORT.md"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main():
    text = REPORT.read_text(encoding="utf-8")
    refs = re.findall(r"`((?:work|docs|results)/[^`:\s]+):([0-9]+(?:-[0-9]+)?(?:,[0-9]+(?:-[0-9]+)?)*)`", text)
    inputs, errors = {}, []
    for rel, specs in refs:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"Missing citation file: {rel}")
            continue
        data = path.read_bytes()
        lines = data.decode("utf-8-sig").splitlines()
        rec = inputs.setdefault(rel, dict(sha256=digest(data), lines=len(lines), ranges=[]))
        if specs not in rec["ranges"]:
            rec["ranges"].append(specs)
        for span in specs.split(","):
            nums = list(map(int, span.split("-")))
            lo, hi = nums[0], nums[-1]
            if not 1 <= lo <= hi <= len(lines):
                errors.append(f"Out-of-range citation: {rel}:{span} (file has {len(lines)} lines)")
    for path in sorted(HERE.rglob("*.py")):
        ast.parse(path.read_text(encoding="utf-8"), filename=path.name)
    counts = dict(claim_rows=len(re.findall(r"^\| \*\*\d+\. ", text, re.M)),
                  hypotheses=len(re.findall(r"^### D[1-8]\. ", text, re.M)))
    if counts != {"claim_rows": 12, "hypotheses": 8}:
        errors.append(f"Unexpected section counts: {counts}")
    executive = text.split("## Executive summary — one page", 1)[1].split("\n---\n", 1)[0]
    counts["executive_whitespace_words_including_citations"] = len(executive.split())
    # Do not reveal private environment values even if a check fails.
    private_values = [(key, os.environ.get(key, "")) for key in ("USERNAME", "USER", "COMPUTERNAME")]
    scanned = []
    absolute_pattern = re.compile(r"[A-Za-z]:[\\/]" + "|" + "/" + "home" + "/" + "|" + "/" + "Users" + "/" + "|" + re.escape(chr(92) + "Users" + chr(92)))
    for path in sorted(HERE.rglob("*")):
        if not path.is_file() or path.name in {"evidence_manifest.json", "VALIDATION.md"}:
            continue
        rel = path.relative_to(ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        scanned.append(rel)
        if absolute_pattern.search(content):
            errors.append(f"Possible absolute/private path in {rel}")
        for key, value in private_values:
            if len(value) >= 4 and value.casefold() not in {"root", "user"} and value.casefold() in content.casefold():
                errors.append(f"Possible private {key} value in {rel}")
    pinned = HERE / "evidence/h5_campaign_01b31fe.md"
    expected = "b8a43ad2b7a0e66a823e826d16e57ba5420d04c216f392cb2ca1a3501d5ec94d"
    if digest(pinned.read_bytes()) != expected:
        errors.append("Pinned campaign copy does not match the independently checked git-blob SHA-256")
    latest_controls = HERE / "evidence/h5_prelaunch_b38bc2e.txt"
    if digest(latest_controls.read_bytes()) != "8be6a0b0a8dad6c07b781527972f22932176d80f76057eeaa5340eeebbee54f4":
        errors.append("Concurrent control snapshot does not match its independently checked git-blob SHA-256")
    source_rel = "work/h5rs/CAMPAIGN.md"
    source_data = (ROOT / source_rel).read_bytes()
    source_lines = source_data.decode("utf-8").splitlines()
    excerpts = re.findall(r"<!-- excerpt:start:(\d+)-(\d+) -->\n(.*?)\n<!-- excerpt:end -->", (HERE / "evidence/h5_update_b38bc2e.md").read_text(encoding="utf-8"), re.S)
    inputs.setdefault(source_rel, dict(sha256=digest(source_data), lines=len(source_lines), ranges=[]))
    if len(excerpts) != 4:
        errors.append("Expected four pinned concurrent campaign excerpts")
    for lo, hi, body in excerpts:
        inputs[source_rel]["ranges"].append(f"{lo}-{hi}")
        if body != "\n".join(source_lines[int(lo)-1:int(hi)]):
            errors.append(f"Concurrent campaign excerpt differs from declared source: {lo}-{hi}")
    # Hash local artifacts and bare-path evidence too, without executing any code.
    for rel in ("work/independent/frontier/LIKELIHOOD_NOTE.md", "work/independent/frontier/audit.py",
                "work/independent/frontier/audit.json", "work/independent/frontier/RUN_LOG.md",
                "work/independent/frontier/README.md", "work/independent/frontier/validate.py",
                "work/independent/frontier/evidence/h5_campaign_01b31fe.md",
                "work/independent/frontier/evidence/h5_prelaunch_partial.txt",
                "work/independent/frontier/evidence/h5_prelaunch_b38bc2e.txt",
                "work/independent/frontier/evidence/h5_update_b38bc2e.md"):
        data = (ROOT / rel).read_bytes()
        inputs.setdefault(rel, dict(sha256=digest(data), lines=len(data.decode("utf-8-sig").splitlines()), ranges=[]))
    out = dict(kind="artifact validation only; not a cipher/decoder/power test", reviewed_commit="01b31fe", concurrent_update_commit="b38bc2e",
               report_sha256=digest(REPORT.read_bytes()), counts=counts, numbered_citations=len(refs),
               inputs=inputs, privacy_files_scanned=scanned, errors=errors,
               elapsed_seconds=round(time.monotonic()-START, 4))
    (HERE / "evidence_manifest.json").write_text(json.dumps(out, ensure_ascii=False, indent=2)+"\n", encoding="utf-8", newline="\n")
    lines = ["# Review-artifact validation", "", "Not an engine, planted-key, null, cipher-fit or decryption test.", "",
             f"- Claim rows: {counts['claim_rows']}; hypothesis entries: {counts['hypotheses']}.",
             f"- Executive summary whitespace words, including citations: {counts['executive_whitespace_words_including_citations']}.",
             f"- Numbered citation occurrences checked for file existence and valid line bounds: {len(refs)}.",
             "- Python syntax parsed without importing project modules or writing bytecode.",
             "- Pinned historical H5 campaign and completed concurrent control record match independently checked Git-blob SHA-256s.",
             "- Four concurrent campaign excerpts match their declared source line ranges; full source hash retained.",
             "- New artifact text scanned for absolute paths and private environment-name values; raw values are never recorded.",
             "- Semantic fidelity of citations remains a human review, not something line-bound checking proves.",
             "- Full hashes/ranges: `evidence_manifest.json`.", ""]
    lines += ["## Errors", ""] + ([f"- {e}" for e in errors] if errors else ["None."])
    lines += ["", f"Elapsed seconds: {out['elapsed_seconds']}."]
    (HERE / "VALIDATION.md").write_text("\n".join(lines)+"\n", encoding="utf-8", newline="\n")
    print(json.dumps({"counts": counts, "numbered_citations": len(refs), "errors": errors, "elapsed_seconds": out["elapsed_seconds"]}, ensure_ascii=False))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
