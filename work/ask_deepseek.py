"""One round with DeepSeek through the pi harness: no tools, no project files, no session, no MCP, run from an empty temporary folder, so the model can only read the prompt it is given.

    python work/ask_deepseek.py <prompt.md> [--model deepseek-flash]      # prints the reply, saves prompt + reply to work/ref/deepseek/ (git-ignored: third-party text is data, never committed)

The API key stays in pi's own configuration or environment; this script never reads or prints it. `pi auth check --provider deepseek` tells whether the provider is ready.
"""
import argparse
import datetime
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYSTEM = "You are a research assistant. You have no tools and cannot see any file or repository; answer only from the prompt you are given. State what you are unsure of."


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt")
    ap.add_argument("--model", default="deepseek-flash")
    ap.add_argument("--thinking", default="medium")
    ap.add_argument("--timeout", type=int, default=900)
    a = ap.parse_args()
    prompt = open(a.prompt, encoding="utf-8").read()
    pi = shutil.which("pi.cmd") or shutil.which("pi")
    if pi is None:
        sys.exit("pi not found on PATH")
    with tempfile.TemporaryDirectory() as tmp:
        pf = os.path.join(tmp, "prompt.md")
        with open(pf, "w", encoding="utf-8", newline="\n") as f:
            f.write(prompt)
        cmd = [pi, "-p", "--no-session", "--no-tools", "--no-extensions", "--no-skills", "--no-prompt-templates", "--no-context-files", "--no-mcp", "--no-themes",
               "--provider", "deepseek", "--model", a.model, "--thinking", a.thinking, "--system-prompt", SYSTEM, "@prompt.md", "Follow the instructions in the attached file."]
        r = subprocess.run(cmd, cwd=tmp, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=a.timeout)
    if r.returncode != 0:
        sys.exit(f"pi failed ({r.returncode}): {r.stderr[:500]}")
    out_dir = os.path.join(ROOT, "work", "ref", "deepseek")
    os.makedirs(out_dir, exist_ok=True)
    stem = os.path.splitext(os.path.basename(a.prompt))[0]
    path = os.path.join(out_dir, f"{datetime.datetime.now(datetime.timezone.utc):%Y%m%d_%H%M%S}_{stem}.md")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# prompt ({a.model}, thinking {a.thinking})\n\n{prompt}\n\n# reply\n\n{r.stdout}\n")
    print(r.stdout)
    print(f"[saved: work/ref/deepseek/{os.path.basename(path)}]", file=sys.stderr)


if __name__ == "__main__":
    main()
