"""Collect Cicada-related onion/web URLs from local archive text (data only, never executed)."""
import os, re, sys, json, collections
ROOTS = ["Other repositories and work", "work/ref/uncovering_cicada", "work/ref/online_2026-10-21", "docs", "work/ref"]
SKIP_EXT = {".png",".jpg",".jpeg",".gif",".bmp",".pdf",".zip",".gz",".7z",".mp3",".wav",".ogg",".exe",".dll",".pyc",".npy",".npz",".bin",".jp2",".tif",".tiff",".webp",".ico",".wmv",".mp4"}
ONION = re.compile(rb"(?i)\b([a-z2-7]{16}|[a-z2-7]{56})\.onion(?:\.(?:to|city|cab|link|ws|sh|nu|lt|casa|direct|rip|pet|in\.net))?(?:/[^\s\"'<>\)\]\}]*)?")
GW = re.compile(rb"(?i)\b([a-z2-7]{16})\.(?:tor2web\.(?:org|io|fi|su|blutmagie\.de)|onion\.[a-z.]+|d2web\.org)(?:/[^\s\"'<>\)\]\}]*)?")
WEB = re.compile(rb"(?i)https?://[^\s\"'<>\)\]\}]*(?:845145127\.com|1853143003544\.tk|33091839349\.tk|3301\.org|cicada3301|cicadasolver|imgur\.com|pastebin|dpaste)[^\s\"'<>\)\]\}]*")
res = collections.defaultdict(set)
n=0
for root in ROOTS:
    for dp, dn, fn in os.walk(root):
        if "an_end_hunt" in dp or ".git" in dp.split(os.sep): continue
        for f in fn:
            ext = os.path.splitext(f)[1].lower()
            if ext in SKIP_EXT: continue
            p = os.path.join(dp, f)
            try:
                if os.path.getsize(p) > 30_000_000: continue
                b = open(p,"rb").read()
            except Exception: continue
            n+=1
            for rx,kind in ((ONION,"onion"),(GW,"gateway"),(WEB,"web")):
                for m in rx.finditer(b):
                    s = m.group(0).decode("latin1").rstrip(".,;:'\"")
                    res[(kind,s)].add(p.replace("\\","/"))
print("files scanned", n, file=sys.stderr)
out = [{"kind":k,"url":u,"sources":sorted(v)[:5],"nsources":len(v)} for (k,u),v in sorted(res.items())]
json.dump(out, open("work/phase52/urls_raw.json","w"), indent=1)
print(len(out))
