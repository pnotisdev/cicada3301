"""Detached job queue: runs the jobs of a queue file one after another, resumable, independent of any interactive session.

    python jobs/jobqueue.py <queue name> <queue file> [<scheduled task to delete when done>]            # e.g. python jobs/jobqueue.py cpu jobs/queues/cpu.txt

Queue file: one job per line, `name | command`; blank lines and lines starting with # are ignored. `{PY}` is the interpreter that runs this driver. A trailing `> path` sends the job's stdout to that repository-relative file (its stderr goes to the job log).
A line `WAIT | <text>` holds the queue until no python.exe process whose command line contains <text> has been seen for two minutes (at most 8 h) (so a job started by hand finishes before the queue takes over; jobs themselves must be resumable).
Every job logs to results/overnight/desktop/queue/<queue>__<job>.log; results/overnight/desktop/queue/<queue>.tsv records status and times. A job with status ok is skipped on a restart; a failed job does not stop the queue.
While the driver runs it asks Windows not to sleep (SetThreadExecutionState; no system setting is changed). When the queue is done it removes its own scheduled task (third argument or the environment variable QUEUE_TASK).
The queues are meant to be started by Task Scheduler (`schtasks`), which keeps them running when the session that created them ends; docs/QUEUE.md.
"""
import ctypes
import datetime
import os
import platform
import re
import shlex
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "overnight", "desktop", "queue")
ES_CONTINUOUS, ES_SYSTEM_REQUIRED = 0x80000000, 0x00000001


def scrub_text(t):
    """no absolute repository or home paths and no computer name in anything the queue writes into the repository (CLAUDE.md, privacy)"""
    for r in {ROOT, ROOT.replace("\\", "/"), ROOT.replace("/", "\\")}:
        t = t.replace(r, "<repo>")
    home = os.path.expanduser("~")
    for h in {home, home.replace("\\", "/")}:
        t = t.replace(h, "~")
    t = re.sub(r"~[\\/][^\\/\s]+[\\/]Local[\\/]Programs[\\/]Python[\\/]Python\d+", "<python>", t)    # the interpreter folder in tracebacks
    host = platform.node()
    if len(host) >= 5:
        t = re.sub(re.escape(host), "<host>", t, flags=re.IGNORECASE)
    return t


def scrub_file(path):
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace", newline="") as f:
            t = f.read()
        with open(path, "w", encoding="utf-8", newline="") as f:
            f.write(scrub_text(t))


def now():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def awake(on):
    try:
        ctypes.windll.kernel32.SetThreadExecutionState(ES_CONTINUOUS | (ES_SYSTEM_REQUIRED if on else 0))
    except Exception:  # noqa: BLE001
        pass


def running(text):
    """number of python.exe processes whose command line contains `text` (only python processes: a shell that merely mentions the text must not hold the queue)"""
    pat = text.replace("'", "''")
    ps = ("Get-CimInstance Win32_Process | Where-Object { $_.Name -eq 'python.exe' -and $_.CommandLine -and $_.CommandLine -like '*" + pat + "*' -and $_.ProcessId -ne " + str(os.getpid()) + " } | Measure-Object | Select-Object -ExpandProperty Count")
    r = subprocess.run(["powershell", "-NoProfile", "-Command", ps], capture_output=True, text=True)
    try:
        return int(r.stdout.strip() or 0)
    except ValueError:
        return 0


def read_state(path):
    done = {}
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            p = line.rstrip("\n").split("\t")
            if len(p) >= 3:
                done[p[0]] = p[2]
    return done


def main():
    name, qfile = sys.argv[1], sys.argv[2]
    os.chdir(ROOT)
    os.makedirs(OUT, exist_ok=True)
    state = os.path.join(OUT, name + ".tsv")
    jobs = []
    for line in open(qfile, encoding="utf-8"):
        line = line.strip()
        if line and not line.startswith("#") and "|" in line:
            n, cmd = (x.strip() for x in line.split("|", 1))
            jobs.append((n, cmd))
    awake(True)
    try:
        for n, cmd in jobs:
            if read_state(state).get(n) == "ok":
                continue
            if n == "WAIT":
                idle, polls, gap = 0, int(os.environ.get("QUEUE_IDLE_POLLS", 6)), int(os.environ.get("QUEUE_POLL_SECONDS", 20))
                give_up = time.time() + float(os.environ.get("QUEUE_MAX_WAIT_SECONDS", 8 * 3600))
                while idle < polls and time.time() < give_up:    # six polls 20 s apart by default: two minutes without the process; never longer than 8 h
                    idle = 0 if running(cmd) else idle + 1
                    time.sleep(gap)
                continue
            out_file = None
            if " > " in cmd:
                cmd, out_file = (x.strip() for x in cmd.rsplit(" > ", 1))
            args = [sys.executable if a == "{PY}" else a for a in shlex.split(cmd)]
            t0 = now()
            log = os.path.join(OUT, f"{name}__{n}.log")
            env = dict(os.environ, PYTHONIOENCODING="utf-8")
            with open(log, "a", encoding="utf-8", newline="\n") as lg:
                lg.write(f"# {t0} start: {cmd}\n")
                lg.flush()
                so = open(os.path.join(ROOT, out_file), "w", encoding="utf-8", newline="\n") if out_file else lg
                try:
                    rc = subprocess.run(args, cwd=ROOT, stdout=so, stderr=lg, env=env).returncode
                except Exception as e:  # noqa: BLE001
                    lg.write(f"# could not run: {e}\n")
                    rc = 127
                if out_file:
                    so.close()
                lg.write(f"# {now()} exit {rc}\n")
            scrub_file(log)
            if out_file:
                scrub_file(os.path.join(ROOT, out_file))
            with open(state, "a", encoding="utf-8", newline="\n") as f:
                f.write(f"{n}\t{t0}\t{'ok' if rc == 0 else 'failed'}\t{now()}\t{rc}\n")
    finally:
        awake(False)
        with open(state, "a", encoding="utf-8", newline="\n") as f:
            f.write(f"QUEUE_DONE\t{now()}\tdone\t{now()}\t0\n")
        task = sys.argv[3] if len(sys.argv) > 3 else os.environ.get("QUEUE_TASK")
        if task:
            subprocess.run(["schtasks", "/delete", "/tn", task, "/f"], capture_output=True)


if __name__ == "__main__":
    main()
