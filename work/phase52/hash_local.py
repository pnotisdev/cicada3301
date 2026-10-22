"""Phase 52 step 3/4 (local): hash every file in the local archives + wiki download, with variants for text/HTML."""
import os, sys, json, time
sys.path.insert(0, "work/phase52")
import hashlib52 as H
ROOTS = ["Other repositories and work", "work/ref/uncovering_cicada", "work/ref/online_2026-10-21"]
BIN = {".jpg",".jpeg",".png",".gif",".mp4",".mp3",".wav",".ogg",".docx",".pdf",".zip",".gz",".7z",".wmv",".bmp",".webp",".ico",".exe",".dll"}
stats = {"digests":0, "candidates":0, "files":0, "raw_only":0}; hits = []
# positive control: every (variant, function) of a sample page must be found when the target is set to its digest
sample = b"HTTP/1.1 200 OK\r\nServer: x\r\n\r\n<html><body><p>hello &amp; bye</p>\r\n</body></html>\r\n"
ctl_ok = 0; ctl_n = 0
orig = H.TARGET
for vn, vb in H.variants(sample).items():
    for fn, hx in H.digest_all(vb):
        H.TARGET = hx; s = {"digests":0,"candidates":0}; h = []
        H.check("control", sample, s, h)
        ctl_n += 1; ctl_ok += any(x[1]==vn and x[2]==fn and x[3]=="FULL" for x in h)
H.TARGET = orig
print("positive control:", ctl_ok, "/", ctl_n, flush=True)
t0 = time.time()
for root in ROOTS:
    for dp, dn, fn in os.walk(root):
        dn[:] = [d for d in dn if d != ".git"]
        for f in fn:
            p = os.path.join(dp, f)
            try: b = open(p, "rb").read()
            except Exception: continue
            stats["files"] += 1
            ext = os.path.splitext(f)[1].lower()
            if ext in BIN or len(b) > H.VAR_CAP:
                stats["raw_only"] += 1
                for n, fnc in H.FAST.items():
                    stats["digests"] += 1
                    hx = fnc(b)
                    if hx == H.TARGET: hits.append((p, "raw", n, "FULL"))
                stats["candidates"] += 1
            else:
                H.check(p.replace("\\", "/"), b, stats, hits)
            if stats["files"] % 200 == 0: print(stats, round(time.time()-t0), flush=True)
print("DONE", stats, "hits:", hits, flush=True)
json.dump({"stats":stats,"hits":hits,"control":[ctl_ok,ctl_n]}, open("work/phase52/hash_local_result.json","w"))
