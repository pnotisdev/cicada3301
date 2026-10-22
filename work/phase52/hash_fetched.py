"""Phase 52 step 4 (fetched): hash every fetched capture with all variants. Usage: hash_fetched.py <tag> <shard> <nshards>"""
import json, sys, os
sys.path.insert(0, "work/phase52")
import hashlib52 as H
OUT = "work/ref/an_end_hunt"
stats = {"digests": 0, "candidates": 0}; hits = []; seen = set(); blocked = []
SH, NSH = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 1)
tag = sys.argv[1] if len(sys.argv) > 1 else "t"
for idx, l in enumerate(open(os.path.join(OUT, "manifest.jsonl"), encoding="utf-8")):
    if idx % NSH != SH: continue
    r = json.loads(l)
    if not r["file"] or r["sha256"] in seen: continue
    seen.add(r["sha256"])
    try: b = open(os.path.join(OUT, r["file"]), "rb").read()
    except OSError:
        blocked.append(r["original"] + " @" + r["timestamp"]); continue
    lab = f'{r["original"]} @{r["timestamp"]}'
    ext = r["original"].lower().rsplit(".", 1)[-1]
    if ext in ("jpg", "jpeg", "png", "gif", "mp3", "mp4", "ico") or len(b) > H.VAR_CAP:
        for n, f in H.FAST.items():
            stats["digests"] += 1
            if f(b) == H.TARGET: hits.append((lab, "raw", n, "FULL"))
        stats["candidates"] += 1
    elif "pastebin" in r["original"] or "dpaste" in r["original"]:
        # pastes are not deep-web pages: whirlpool/streebog on the raw bytes only, fast functions on all variants
        for vn, vb in H.variants(b).items():
            for fn, hx in H.digest_all(vb, allow_slow=(vn == "raw" and len(vb) <= H.SLOW_CAP)):
                stats["digests"] += 1
                if hx == H.TARGET: hits.append((lab, vn, fn, "FULL"))
                elif hx[:12] == H.TARGET[:12] or hx[-12:] == H.TARGET[-12:]: hits.append((lab, vn, fn, "PREFIX/SUFFIX12"))
        stats["candidates"] += 1
    else:
        H.check(lab, b, stats, hits)
print("unique fetched bodies hashed:", stats["candidates"], "digests:", stats["digests"], "hits:", hits, "blocked/unreadable (not hashed):", blocked)
json.dump({"stats": stats, "hits": hits, "blocked": blocked}, open(f"work/phase52/hash_fetched_result_{tag}_{SH}.json", "w"))
