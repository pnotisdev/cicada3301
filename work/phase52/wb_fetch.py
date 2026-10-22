"""Phase 52 step 3: fetch original bytes of Wayback captures (id_ mode). DATA ONLY: saved, never executed."""
import json, os, sys, time, hashlib, urllib.request, urllib.error, datetime
OUT = "work/ref/an_end_hunt"; os.makedirs(OUT, exist_ok=True)
MAN = os.path.join(OUT, "manifest.jsonl")
cdx = json.load(open("work/phase52/cdx_results.json"))
seen_fetch = {}
if os.path.exists(MAN):
    for l in open(MAN, encoding="utf-8"):
        r = json.loads(l); seen_fetch[(r["timestamp"], r["original"])] = r
# one capture per (original, wayback content digest); keep earliest timestamp
TIER = sys.argv[2] if len(sys.argv) > 2 else "1"
EXC = ("cicada3301.com/", "cicada3301.org/", "cicada3301.boards.net/", "www.cicadasolvers.com/")
def tier(q):
    if q.startswith(EXC) or "old.reddit.com" in q: return "x"
    if q.startswith("http"): return "2" if any(h in q for h in ("pastebin.com","dpaste","845145127")) else "x"
    return "1"
cands = {}
for q, rows in cdx.items():
    if tier(q) != TIER: continue
    for ts, orig, mime, status, dig, length in (rows or []):
        if status not in ("200", "-", "203", "206"): continue
        k = (orig, dig)
        if k not in cands or ts < cands[k][0]: cands[k] = (ts, orig, mime, status, dig, length)
order = sorted(cands.values(), key=lambda r: (r[1], r[0]))
print(len(order), "unique captures to fetch", file=sys.stderr)
LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
n = 0
for ts, orig, mime, status, dig, length in order:
    if (ts, orig) in seen_fetch: continue
    if n >= LIMIT: break
    u = f"https://web.archive.org/web/{ts}id_/{orig}"
    body = None
    for attempt in range(5):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "lp-research-archive-check/1.0"}), timeout=90)
            body = r.read(); break
        except urllib.error.HTTPError as e:
            if e.code in (404, 403, 410, 451): body = None; break
            time.sleep(10 * (attempt + 1))
        except Exception:
            time.sleep(10 * (attempt + 1))
    rec = {"timestamp": ts, "original": orig, "mimetype": mime, "wayback_digest": dig, "fetch_url": u,
           "fetched_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")}
    if body is not None:
        sh = hashlib.sha256(body).hexdigest()
        fn = f"{ts}_{sh[:16]}.bin"
        open(os.path.join(OUT, fn), "wb").write(body)
        rec.update(sha256=sh, file=fn, size=len(body))
    else: rec.update(sha256=None, file=None, size=None)
    open(MAN, "a", encoding="utf-8").write(json.dumps(rec) + "\n")
    n += 1; time.sleep(1.0)
print("fetched", n, file=sys.stderr)
