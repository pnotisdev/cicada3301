"""Builds the overview pages from the experiment registry (docs/registry.toml), standard library only.

    python scripts/build_overview.py            write STATUS.md, results/INDEX.md, results/index.html and the status block of README.md
    python scripts/build_overview.py --check    validate the registry and its links; fail if a generated file is out of date

The registry is the one place where "what was tested, with what power, what came out, what is left" is written down;
everything generated here is a view of it. Rules for editing it are in its header.
"""
import json
import os
import re
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTRY = os.path.join(ROOT, "docs", "registry.toml")
TEMPLATE = os.path.join(ROOT, "scripts", "overview_template.html")
STATUSES = ["excluded", "partial", "untestable", "open", "explained", "observed"]
LABEL = {"excluded": "Excluded", "partial": "Partly excluded", "untestable": "Cannot be tested at LP2's effect size",
         "open": "Open (not run or partly run)", "explained": "Explained puzzle furniture", "observed": "Observed in LP2"}
BEGIN, END = "<!-- status:begin -->", "<!-- status:end -->"


def load():
    with open(REGISTRY, "rb") as f:
        return tomllib.load(f)


def exists(rel):
    return os.path.exists(os.path.join(ROOT, rel))


def validate(reg):
    """returns a list of problems (empty = fine)"""
    bad, ids = [], set()
    groups = {g["id"] for g in reg["group"]}
    for e in reg["experiment"]:
        i = e.get("id", "?")
        if i in ids:
            bad.append(f"{i}: duplicate id")
        ids.add(i)
        for k in ("group", "title", "status"):
            if k not in e:
                bad.append(f"{i}: missing {k}")
        if e.get("status") not in STATUSES:
            bad.append(f"{i}: status {e.get('status')!r} is not one of {STATUSES}")
        if e.get("group") not in groups:
            bad.append(f"{i}: unknown group {e.get('group')!r}")
        if e.get("status") == "open" and "priority" not in e:
            bad.append(f"{i}: an open row needs a priority")
        if e.get("chart") and "best" not in e:
            bad.append(f"{i}: chart = true needs best")
        for k in ("log", "files"):
            for p in e.get(k, []):
                if not exists(p):
                    bad.append(f"{i}: {k} path does not exist: {p}")
    known = {f["path"] for f in reg["folder"]}
    for d in sorted(os.listdir(os.path.join(ROOT, "results"))):
        if os.path.isdir(os.path.join(ROOT, "results", d)) and f"results/{d}" not in known:
            bad.append(f"results/{d}: folder has no [[folder]] entry in the registry")
    for k in known:
        if not exists(k):
            bad.append(f"{k}: [[folder]] path does not exist")
    wr = os.path.join(ROOT, "work", "README.md")
    if os.path.exists(wr):
        text = open(wr, encoding="utf-8").read()
        for n in sorted(os.listdir(os.path.join(ROOT, "work"))):
            if n.endswith(".py") and f"`{n}`" not in text:
                bad.append(f"work/{n}: not listed in work/README.md")
    else:
        bad.append("work/README.md is missing")
    return bad


def cell(t):
    return str(t).replace("|", "\\|").replace("\n", " ")


def fmt(x):
    return f"{x:.3f}"


def by_status(reg, s):
    return [e for e in reg["experiment"] if e["status"] == s]


def counts(reg):
    return {s: len(by_status(reg, s)) for s in STATUSES}


def tests_on_record(reg):
    return sum(1 for e in reg["experiment"] if e["status"] != "observed")


def top_scores(reg, n=6):
    rows = sorted((e for e in reg["experiment"] if e.get("chart")), key=lambda e: -e["best"])
    return rows[:n]


def link(path, base=""):
    p = path if not base else os.path.relpath(path, base).replace("\\", "/")
    return f"[{os.path.basename(path.rstrip('/'))}]({p})"


def score(e, reg):
    if "best" not in e:
        return ""
    s = fmt(e["best"])
    if "null" in e:
        s += f" (null {fmt(e['null'])})"
    return s


def readme_block(reg):
    m, c = reg["meta"], counts(reg)
    top = top_scores(reg, 1)[0]
    return "\n".join([
        BEGIN,
        "| As of " + m["updated"] + " | |",
        "|---|---|",
        "| **Solved** | **Nothing.** LP2 (sections 0.7-0.15, 12,956 runes) is still undecoded |",
        f"| Tests on record | {tests_on_record(reg)}: {c['excluded']} excluded, {c['partial']} partly excluded, {c['untestable']} untestable at LP2's effect size, {c['open']} still open |",
        f"| Highest full-window screen score | IoC {fmt(top['best'])} ({top['id']}; fails whole-window verification) against the rule {m['rule']:.2f}; a planted key lands at {m['planted_low']}-{m['planted_high']} |",
        f"| Candidates that survived whole-section verification | **{m['survivors']}** |",
        "| Live pages | [STATUS.md](STATUS.md) (done / left) and [results/INDEX.md](results/INDEX.md) (every result, with its control) |",
        END])


def status_md(reg):
    m, c = reg["meta"], counts(reg)
    g = {x["id"]: x["title"] for x in reg["group"]}
    out = ["# Status: Liber Primus, LP2 (sections 0.7-0.15, 12,956 runes)", "",
           f"*Generated from [docs/registry.toml](docs/registry.toml) by `scripts/build_overview.py`; do not edit by hand. Updated {m['updated']}.*", "",
           "**Nothing in LP2 is solved.** Each line below is a statement of the form: a planted key of this kind, in this much text, would have been found by this test, and nothing was found. "
           "The control column says how well the test is known to work; the last column says what the negative does NOT exclude.", "",
           "## At a glance", "", "| | |", "|---|---|"]
    for s in STATUSES:
        out.append(f"| {LABEL[s]} | {c[s]} |")
    out += [f"| Candidates that survived whole-section verification | **{m['survivors']}** |", "",
            f"Decision rule for the IoC screens: {m['rule']:.2f} on a 300-rune window; planted keys score {m['planted_low']}-{m['planted_high']}, "
            f"random keys top out near {m['null_max']} at 10^10 decodes. A hit counts only after whole-section verification with a positive and a null control (docs/CAMPAIGNS.md).", "",
            "### Highest screen scores (300-rune windows, IoC)", "", "| Campaign | Best | Matched null | Verdict |", "|---|---|---|---|"]
    for e in top_scores(reg, 8):
        out.append(f"| {cell(e['title'])} | {fmt(e['best'])} | {fmt(e['null']) if 'null' in e else ''} | {cell(e['result'])} |")
    out += ["", "## Left to do (suggested order)", "", "| # | Item | Cost | Needs |", "|---|---|---|---|"]
    for e in sorted(by_status(reg, "open"), key=lambda e: e["priority"]):
        out.append(f"| {e['priority']} | **{cell(e['title'])}**" + (f"<br>{cell(e['what'])}" if "what" in e else "") + f" | {cell(e.get('cost', ''))} | {cell(e.get('needs', ''))} |")
    out += ["", "No long runs are queued; `docs/QUEUE.md` explains how to restart the queues.", "",
            "## Done: excluded and partly excluded", ""]
    for gid, gt in g.items():
        rows = [e for e in reg["experiment"] if e["group"] == gid and e["status"] in ("excluded", "partial")]
        if not rows:
            continue
        out += [f"### {gt}", "", "| Test | Best (null) | Control | Result | Does NOT exclude |", "|---|---|---|---|---|"]
        for e in rows:
            tag = " *(partly)*" if e["status"] == "partial" else ""
            out.append(f"| **{cell(e['title'])}**{tag} | {score(e, reg)} | {cell(e.get('control', ''))} | {cell(e.get('result', ''))} | {cell(e.get('gap', ''))} |")
        out.append("")
    for s, head in (("untestable", "## Cannot be tested at LP2's effect size"), ("explained", "## Explained puzzle furniture"), ("observed", "## What LP2 shows (any solution has to explain it)")):
        rows = by_status(reg, s)
        if rows:
            out += [head, "", "| Item | Finding |", "|---|---|"]
            out += [f"| **{cell(e['title'])}** | {cell(e.get('result', ''))}" + (f" *({cell(e['control'])})*" if "control" in e else "") + " |" for e in rows]
            out.append("")
    out += ["## Where things are", "",
            "| I want to... | Open |", "|---|---|",
            "| see every result with its control and files | [results/INDEX.md](results/INDEX.md), or `results/index.html` in a browser |",
            "| read the per-campaign verdicts of a PC | `results/overnight/<alias>/REPORT.md` |",
            "| read why a test was run and how it was controlled | the log named per row in the registry (`work/log/`) |",
            "| see what each doc is | [docs/INDEX.md](docs/INDEX.md) |",
            "| find a script | [work/README.md](work/README.md) |",
            "| see the plan phase by phase | [PLAN.md](PLAN.md) |", ""]
    return "\n".join(out)


def results_md(reg):
    m = reg["meta"]
    g = {x["id"]: x["title"] for x in reg["group"]}
    out = ["# Results index", "",
           f"*Generated from [docs/registry.toml](../docs/registry.toml) by `scripts/build_overview.py`; do not edit by hand. Updated {m['updated']}. An interactive version with a chart is [index.html](index.html) (open it in a browser).*", "",
           "**Nothing in LP2 is solved.** Every negative below has a positive control (a planted key the method recovers) and a null control. How to read a result file:", "",
           "* `*_verify.txt`: the best hits re-decoded over their whole window. `0 of N ... (none: noise)` is a negative; `no candidate reached the sweep's floor` is a negative.",
           "* `*_selftest.txt`: the planted-key control (`SELFTEST PASSED`). A screen without it counts for nothing.",
           "* `*.tsv`: the top hits; header lines starting with `#` give the settings and a histogram of all decodes.", "",
           "## Folders", "", "| Folder | Content | Start with |", "|---|---|---|"]
    for f in reg["folder"]:
        rd = f.get("read", "")
        out.append(f"| [{os.path.relpath(f['path'], 'results').replace(chr(92), '/')}/]({os.path.relpath(f['path'], 'results').replace(chr(92), '/')}/) | {cell(f['what'])} | {cell(rd)} |")
    out += ["", "## Results by question", ""]
    for gid, gt in g.items():
        rows = [e for e in reg["experiment"] if e["group"] == gid and e.get("files")]
        if not rows:
            continue
        out += [f"### {gt}", "", "| Test | Status | Best (null) | Files |", "|---|---|---|---|"]
        for e in rows:
            fl = ", ".join(link(p, "results") for p in e["files"])
            out.append(f"| {cell(e['title'])} | {e['status']} | {score(e, reg)} | {fl} |")
        out.append("")
    return "\n".join(out)


def results_html(reg):
    tpl = open(TEMPLATE, encoding="utf-8").read()
    data = json.dumps({"meta": reg["meta"], "groups": reg["group"], "experiments": reg["experiment"], "folders": reg["folder"],
                       "labels": LABEL, "statuses": STATUSES}, ensure_ascii=False).replace("</", "<\\/")
    return tpl.replace("/*REGISTRY_JSON*/null", data)


def outputs(reg):
    """path -> content of every generated file (README: only the block between the markers)"""
    o = {"STATUS.md": status_md(reg), "results/INDEX.md": results_md(reg), "results/index.html": results_html(reg)}
    rp = os.path.join(ROOT, "README.md")
    t = open(rp, encoding="utf-8").read()
    if BEGIN in t and END in t:
        a, b = t.index(BEGIN), t.index(END) + len(END)
        o["README.md"] = t[:a] + readme_block(reg) + t[b:]
    return o


def main():
    reg = load()
    bad = validate(reg)
    for b in bad:
        print("PROBLEM:", b)
    out = outputs(reg)
    stale = []
    for rel, text in out.items():
        new = text if rel == "README.md" else text.rstrip("\n") + "\n"
        p = os.path.join(ROOT, rel)
        old = open(p, encoding="utf-8", newline="").read() if os.path.exists(p) else None
        if old != new:
            stale.append(rel)
            if "--check" not in sys.argv:
                with open(p, "w", encoding="utf-8", newline="\n") as f:
                    f.write(new)
                print("wrote", rel)
    if "--check" in sys.argv:
        for s in stale:
            print("OUT OF DATE:", s, "(run python scripts/build_overview.py)")
        return 1 if bad or stale else 0
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
