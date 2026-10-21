"""Phase 48 step 3: re-score past kscreen hits with the A/I oracle (one core, resumable)."""
import os, re, subprocess, sys, json, glob, math
sys.path.insert(0, "work"); sys.path.insert(0, "work/kscreen")
import lp
from verify import read_hits, BIN, HERE   # read-only helper of the repo; the oracle below is new
segs = lp.load_segments()
OUT = "work/mech48/rescore.jsonl"
TOP = int(os.environ.get("TOP", 2))
one = {}
for i in range(7, 16):
    r = lp.runes_of(segs[i])
    one[f"seg0.{i}"] = [a for w, a, b in lp.word_spans(segs[i], r) if b - a == 1]
def files():
    for f in glob.glob("results/**/*.tsv", recursive=True):
        yield f
def flags(meta):
    return [*(["dir=back"] if meta.get("dir") == "back" else []),
            *([f"clock={meta['clock']}"] if meta.get("clock") else []),
            *([f"nulledge={meta['nulledge']}"] if meta.get("nulledge") else []),
            *([f"advsep={meta['advsep']}"] if meta.get("advsep") else [])]
def collect():
    jobs, skipped = {}, {"nonseg": 0, "pdir": 0}
    for f in files():
        with open(f, encoding="utf-8", errors="replace") as fh:
            head = fh.readline()
        if not head.startswith("# kscreen"): continue
        meta, rows = read_hits(f)
        if "ioc" not in (rows[0] if rows else {}): continue
        isnull = "null" in f.lower()
        if meta.get("windows") != "data/segments.txt": skipped["nonseg"] += 1; continue
        if meta.get("pdir"): skipped["pdir"] += 1; continue
        per = {}
        for h in rows:
            if h["window"] not in one: continue
            k = (h["item"], h["offset"], h["mult"], h["model"])
            lst = per.setdefault(h["window"], [])
            if k not in [x[0] for x in lst] and len(lst) < TOP: lst.append((k, h))
        for w, lst in per.items():
            for k, h in lst:
                key = (meta["family"], *k, w, tuple(flags(meta)))
                jobs.setdefault(key, {"meta": meta, "files": set(), "null": isnull, "ioc": float(h["ioc"])})["files"].add(f)
                if not isnull: jobs[key]["null"] = False
    return jobs, skipped
def main():
    jobs, skipped = collect()
    done = set()
    if os.path.exists(OUT):
        for l in open(OUT): done.add(tuple(json.loads(l)["key"]) if False else l.split('"key": ')[1].split(', "n_one"')[0])
    print(len(jobs), "distinct hits;", sum(1 for j in jobs.values() if j["null"]), "from null files only;", skipped, flush=True)
    with open(OUT, "a", encoding="utf-8") as out:
        for n, (key, j) in enumerate(sorted(jobs.items(), key=lambda kv: str(kv[0]))):
            fam, item, off, mult, model, w, fl = key
            tag = json.dumps(list(key) if False else [fam, item, off, mult, model, w, list(fl)])
            if tag in done: continue
            r = subprocess.run([BIN, "verify", j["meta"]["windows"], fam, item, off, mult, model, w, "controls=0", *fl],
                               cwd=HERE, capture_output=True, text=True)
            m = re.search(r"plain (.*)", r.stdout)
            if not m: continue
            plain = [int(x) for x in m.group(1).split(",") if x]
            pos = one[w]
            if len(plain) < max(pos) + 1: continue
            vals = [plain[a] for a in pos]
            rec = {"key": tag, "n_one": len(pos), "n_plain": len(plain), "n_ai": sum(v in (24, 10) for v in vals),
                   "vals": vals, "null": j["null"], "ioc": j["ioc"], "files": sorted(j["files"])[:2]}
            out.write(json.dumps(rec) + "\n"); out.flush()
            if n % 50 == 0: print(n, flush=True)
main()
