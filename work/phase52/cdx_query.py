"""Phase 52 step 2: Wayback CDX queries (metadata only). ~1 request per 1.5 s, retries on 429/5xx/HTML."""
import json, re, sys, time, urllib.request, urllib.parse, urllib.error, collections
raw = json.load(open("work/phase52/urls_raw.json"))
onions = set()
for x in raw:
    m = re.match(r'(?i)([a-z2-7]{16})\.', x["url"])
    if x["kind"] in ("onion","gateway") and m: onions.add(m.group(1).lower())
GW = ["onion", "onion.to", "tor2web.org", "tor2web.io", "tor2web.fi", "onion.city", "onion.cab", "onion.link", "onion.ws", "onion.sh", "onion.nu", "onion.lt", "onion.direct", "d2web.org"]
queries = []
for o in sorted(onions):
    for g in GW: queries.append(f"{o}.{g}/*")
for d in ["845145127.com","1853143003544.tk","33091839349.tk","3301.org","cicada3301.org","cicada3301.com","cicadasolver.tumblr.com","dragonstudios.tk","cicada3301.boards.net","www.cicadasolvers.com"]:
    queries.append(d+"/*")
exact = sorted({x["url"].split("#")[0] for x in raw if x["kind"]=="web" and re.search(r"(?i)(i\.)?imgur\.com/|pastebin\.com/|845145127|dpaste", x["url"])})
queries += exact
print(len(queries), "queries", file=sys.stderr)
out = {}
try: out = json.load(open("work/phase52/cdx_results.json"))
except Exception: pass
def fetch(q):
    u = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode({"url": q, "output": "json", "fl": "timestamp,original,mimetype,statuscode,digest,length", "limit": 2000})
    for attempt in range(8):
        try:
            r = urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "lp-research-archive-check/1.0"}), timeout=150)
            t = r.read().decode("utf-8","replace")
            if t.lstrip().startswith("<"): raise ValueError("html")
            return json.loads(t) if t.strip() else []
        except Exception as e:
            wait = 15*(attempt+1)
            print("retry", q, type(e).__name__, wait, file=sys.stderr); time.sleep(wait)
    return None
from concurrent.futures import ThreadPoolExecutor
import threading
lock = threading.Lock(); gate = threading.Lock(); cnt=[0]
def work(q):
    if q in out: return
    with gate: time.sleep(1.0)   # global pacing: at most one request start per second
    rows = fetch(q)
    with lock:
        out[q] = rows[1:] if rows else (None if rows is None else [])
        if out[q]: print("HIT", q, len(out[q]), file=sys.stderr, flush=True)
        cnt[0]+=1
        if cnt[0] % 10 == 0: json.dump(out, open("work/phase52/cdx_results.json","w"))
with ThreadPoolExecutor(4) as ex: list(ex.map(work, queries))
json.dump(out, open("work/phase52/cdx_results.json","w"))
print("done; with captures:", sum(1 for v in out.values() if v), "failed:", sum(1 for v in out.values() if v is None), file=sys.stderr)
