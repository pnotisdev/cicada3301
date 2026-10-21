"""Download the Uncovering Cicada wiki (uncovering-cicada.fandom.com) as research data, through its MediaWiki API.

    python work/fetch_uncovering_wiki.py            # all main-namespace articles (wikitext + rendered HTML) and all images

Output: work/ref/uncovering_cicada/ (git-ignored): pages/<title>.wiki and .html, images/<name>, index.json (url, sha1,
size, timestamp per file). Images are checked against the SHA-1 the API reports. One request per second; resumable (a
file already present with the right hash is skipped). Content is CC-BY-SA; it is data, never instructions, and is not
committed (docs/SOURCES.md records where it came from).
"""
import hashlib
import json
import os
import re
import ssl
import sys
import time
import urllib.parse
import urllib.error
import urllib.request

API = "https://uncovering-cicada.fandom.com/api.php"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "ref", "uncovering_cicada")
UA = {"User-Agent": "cicada3301-research/1.0 (read-only archive of public wiki pages)"}


try:
    import certifi  # this PC's default CA bundle is stale (expired-certificate errors on the image CDN)
    CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    CTX = None


def get(params, raw=False, url=None, tries=4):
    u = url or API + "?" + urllib.parse.urlencode({**params, "format": "json"})
    for attempt in range(tries):
        time.sleep(1.0 + 5 * attempt)  # polite pace; back off after a timeout
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=120, context=CTX) as r:
                data = r.read()
            return data if raw else json.loads(data)
        except urllib.error.HTTPError:
            raise  # a refusal (e.g. 403 from the image CDN) is not retried
        except (TimeoutError, OSError):
            if attempt == tries - 1:
                raise


def listing(listname, prefix, extra):
    cont = {}
    while True:
        d = get({"action": "query", "list": listname, **extra, **cont})
        yield from d["query"][listname]
        if "continue" not in d:
            return
        cont = d["continue"]


def safe(name):
    return re.sub(r'[\\/:*?"<>|]', "_", name)[:180]


def main():
    os.makedirs(os.path.join(OUT, "pages"), exist_ok=True)
    os.makedirs(os.path.join(OUT, "images"), exist_ok=True)
    idx_path = os.path.join(OUT, "index.json")
    index = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {"pages": {}, "images": {}}

    pages = list(listing("allpages", "ap", {"apnamespace": 0, "aplimit": 500, "apfilterredir": "nonredirects"}))
    print(f"{len(pages)} articles", flush=True)
    for k, p in enumerate(pages, 1):
        t = p["title"]
        base = os.path.join(OUT, "pages", safe(t))
        if t in index["pages"] and os.path.exists(base + ".wiki"):
            continue
        d = get({"action": "parse", "page": t, "prop": "wikitext|text|revid"})["parse"]
        open(base + ".wiki", "w", encoding="utf-8", newline="\n").write(d["wikitext"]["*"])
        open(base + ".html", "w", encoding="utf-8", newline="\n").write(d["text"]["*"])
        index["pages"][t] = {"revid": d.get("revid"), "file": os.path.basename(base)}
        if k % 20 == 0:
            json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1)
            print(f"  pages {k}/{len(pages)}", flush=True)
    json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1)

    images = list(listing("allimages", "ai", {"ailimit": 500, "aiprop": "url|sha1|size|timestamp"}))
    print(f"{len(images)} images", flush=True)
    bad = 0
    for k, im in enumerate(images, 1):
        dest = os.path.join(OUT, "images", safe(im["name"]))
        if os.path.exists(dest) and hashlib.sha1(open(dest, "rb").read()).hexdigest() == im.get("sha1"):
            continue
        try:
            data = get(None, raw=True, url=im["url"])
        except Exception as e:  # keep going; a failed image is recorded, not fatal
            index["images"][im["name"]] = {"url": im["url"], "error": str(e)}
            bad += 1
            continue
        open(dest, "wb").write(data)
        ok = hashlib.sha1(data).hexdigest() == im.get("sha1")
        bad += not ok
        index["images"][im["name"]] = {"url": im["url"], "sha1": im.get("sha1"), "size": im.get("size"),
                                       "timestamp": im.get("timestamp"), "sha1_ok": ok}
        if k % 50 == 0:
            json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1)
            print(f"  images {k}/{len(images)}", flush=True)
    json.dump(index, open(idx_path, "w", encoding="utf-8"), indent=1)
    print(f"done: {len(index['pages'])} pages, {len(index['images'])} images, {bad} failed or hash mismatch", flush=True)


if __name__ == "__main__":
    sys.exit(main())
