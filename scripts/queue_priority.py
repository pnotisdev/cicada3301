"""Keep the PC usable while the job queues run: priority, cores, pause. Acts on every running jobs/jobqueue.py (or one queue, --queue) and
on everything it started.

    python scripts/queue_priority.py                       # below-normal priority: the runs only take CPU time nobody else wants
    python scripts/queue_priority.py normal                # undo
    python scripts/queue_priority.py --cores 8             # also pin them to logical processors 0-7 (slower in proportion); --cores 0 undoes
    python scripts/queue_priority.py pause --queue gpu_rest   # freeze one queue (CPU 0%, the GPU idles once the running kernel ends); state is kept
    python scripts/queue_priority.py resume --queue gpu_rest

A queue (or a step) started later begins at normal priority: run this again. The GPU power cap needs an administrator and is not set here:
see the last section of docs/QUEUE.md. A paused queue still counts wall-clock time against its --hours budget. Needs psutil.
"""
import argparse
import os

import psutil

LEVELS = {"idle": psutil.IDLE_PRIORITY_CLASS, "below": psutil.BELOW_NORMAL_PRIORITY_CLASS, "normal": psutil.NORMAL_PRIORITY_CLASS}


def is_runner(argv, queue):
    """a python whose script argument is jobqueue.py (not a shell that merely has the text in its command line)"""
    for i, x in enumerate(argv):
        if x.replace("\\", "/").split("/")[-1] == "jobqueue.py":
            return not queue or argv[i + 1:i + 2] == [queue]
    return False


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", nargs="?", default="below", choices=[*LEVELS, "pause", "resume"])
    ap.add_argument("--queue", default="", help="only this queue (the name after jobqueue.py), default all")
    ap.add_argument("--cores", type=int, help="pin to the first N logical processors; 0 = all of them")
    a = ap.parse_args()
    procs = {}
    for r in psutil.process_iter(["name", "cmdline"]):
        if r.info["name"].lower().startswith("python") and is_runner(r.info["cmdline"] or [], a.queue):
            for p in [r] + r.children(recursive=True):
                procs[p.pid] = p
    for pid in [os.getpid(), *(x.pid for x in psutil.Process().parents())]:
        procs.pop(pid, None)                                    # never freeze the shell or this script
    done = 0
    for p in procs.values():
        try:
            if a.action == "pause":
                p.suspend()
            elif a.action == "resume":
                p.resume()
            else:
                p.nice(LEVELS[a.action])
            if a.cores is not None:
                p.cpu_affinity(list(range(a.cores or psutil.cpu_count())))
            done += 1
        except psutil.Error:
            pass
    print(f"{a.action}: {done} of {len(procs)} processes (the queue runners and everything they started)")


if __name__ == "__main__":
    main()
