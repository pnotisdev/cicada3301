import json, re, glob, collections
raw = json.load(open("work/phase52/urls_raw.json"))
cdx = json.load(open("work/phase52/cdx_results.json"))
man = [json.loads(l) for l in open("work/ref/an_end_hunt/manifest.jsonl", encoding="utf-8")]
loc = json.load(open("work/phase52/hash_local_result.json"))
fs = [json.load(open(f)) for f in sorted(glob.glob("work/phase52/hash_fetched_result_all_*.json"))]
fd = sum(x["stats"]["digests"] for x in fs); fc = sum(x["stats"]["candidates"] for x in fs)
fh = [h for x in fs for h in x["hits"]]; fb = [b for x in fs for b in x["blocked"]]
onions = sorted({re.match(r'(?i)([a-z2-7]{16})\.', x["url"]).group(1).lower() for x in raw if x["kind"] in ("onion","gateway") and re.match(r'(?i)([a-z2-7]{16})\.', x["url"])})
def per(host):
    rows = [(q, v) for q, v in cdx.items() if q.startswith(host + ".")]
    return {q: len(v) for q, v in rows if v}
L = []
w = L.append
w("# Phase 52: An End hash hunt in web archives\n")
w("Target: SHA-512-length value of An End, `36367763ab73...2a8b4` (full value in `results/payload/hashes.txt`). Nothing in LP2 is solved.\n")
w("## Verdict\n")
nh = len(loc["hits"]) + len(fh)
w(f"**{'MATCH FOUND, see below' if nh else 'No match.'}** {loc['stats']['digests'] + fd:,} digests over {loc['stats']['candidates'] + fc:,} candidate files (local {loc['stats']['digests']:,} / fetched {fd:,}); full-512 matches: {nh}.\n")
w("## 1. URL list (from local archives)\n")
w(f"Harvested from 1,333 text files of 'Other repositories and work/', the wiki download (`work/ref/uncovering_cicada/`, 258 pages, finished) and `work/ref/`: {len(raw)} distinct URL strings; {len(onions)} distinct 16-character v2 onion hosts (some are placeholders/typos such as `xx3xxxxxxx7xxxxx`, `xxxxxsdvx6pm2rsk`), plus clearnet hosts (pastebin 226 URL strings, imgur ~108, 845145127.com, web.archive.org 23, etc.). Raw list: `work/phase52/urls_raw.json`.\n")
w("Onion hosts: " + ", ".join(f"`{o}`" for o in onions) + "\n")
w("## 2. Wayback CDX captures per onion host (all gateway forms; counts are CDX rows incl. non-200)\n")
w("| onion host | forms with captures (rows) |\n|---|---|")
for o in onions:
    p = per(o)
    w(f"| `{o}` | " + ("; ".join(f"{q.split('/')[0]} ({n})" for q, n in p.items()) if p else "none") + " |")
w("\nClearnet / other queries with captures:\n")
for q, v in cdx.items():
    if v and not re.match(r"[a-z2-7]{16}\.", q) and not q.startswith("http"):
        w(f"- `{q}`: {len(v)} rows" + (" (cap 2000; NOT fetched, modern site)" if len(v) >= 2000 or q.split('/')[0] in ('cicada3301.com','cicada3301.org','cicada3301.boards.net','www.cicadasolvers.com') else ""))
ex = [q for q, v in cdx.items() if v and q.startswith("http")]
w(f"- {len(ex)} exact pastebin/imgur/845145127/other URLs had captures (of {sum(1 for q in cdx if q.startswith('http'))} queried); see `work/phase52/cdx_results.json`.")
w(f"\nTotal queries: {len(cdx)}; with at least one capture: {sum(1 for v in cdx.values() if v)}; failed: {sum(1 for v in cdx.values() if v is None)}.\n")
w("## 3. Fetched bytes (Wayback `id_` mode)\n")
ok = [m for m in man if m["file"]]
w(f"{len(man)} captures attempted (tier 1: onion/gateway/845145127.com/1853143003544.tk/3301.org/tumblr = 399 unique (URL, content digest) pairs with status 200; tier 2: pastebin/dpaste/845145127 exact URLs). {len(ok)} fetched, {len(man)-len(ok)} not retrievable (404/blocked). Stored in git-ignored `work/ref/an_end_hunt/` with `manifest.jsonl` (URL, capture time, fetch time, SHA-256). Bytes only; nothing opened or executed.\n")
w("Local archive copies hashed too: every file in `Other repositories and work/` (1.3 GB), the wiki download and `work/ref/online_2026-10-21/` (1,826 files).\n")
w("## 4. Hashing\n")
w("Functions: sha512, sha3_512, blake2b-512 (hashlib); whirlpool (own pure-Python, checked on the published empty-string and 'abc' vectors) and streebog-512 (`gostcrypto`, checked on 'abc'). Whirlpool and streebog were computed only for variants of at most 30,000 bytes (pure Python is slow); the three hashlib functions for every file. Binary media (jpg/png/mp4/pdf/docx...) got raw bytes only. Variants for text/HTML: raw; body without HTTP headers; LF; CRLF; each with/without one trailing newline; visible text (tags, scripts, comments stripped, entities decoded) as-is / stripped / whitespace-collapsed / one line per non-empty line, each with and without a trailing newline.\n")
w(f"Positive control: a sample page's every (variant, function) digest was planted as the target and found {loc['control'][0]}/{loc['control'][1]} times. Prefix/suffix-12 near-hits were also searched (chance per digest ~2^-47): none unless listed below.\n")
w(f"- Local pass: {loc['stats']['candidates']} files, {loc['stats']['digests']:,} digests, hits {loc['hits']}\n- Fetched pass: {fc} unique bodies, {fd:,} digests, hits {fh}\n")
w("## 5. Not reachable / not done\n")
w("- Ahmia: reachable (needs the form's hidden token), but returns nothing for the v2 hosts tried (auqgnxjtvdbll3pv, cu343l33nqaekrnw, cginiziglyaobyph, fv7lyucmeozzd5j4, avowyfgl5lkzfj3n); it indexes v3 onions only. Results: `work/phase52/ahmia_results.json`.")
w("- Wayback served 'Temporarily Offline' / timeouts at times; every query was retried until it answered (0 failed).")
w("- Excluded from fetching: cicada3301.com / cicada3301.org / cicada3301.boards.net / www.cicadasolvers.com (modern sites, 4,479 unique captures, not deep-web pages), imgur image captures, a reddit listing page.")
w("- Blocked by antivirus, not hashed: `http://845145127.com` @20170606010037 (Windows Defender: Trojan:HTML/Redirector.SLYB!MTB, an injected script in an old archived page; quarantined, copy deleted, not re-fetched). Other unreadable files: " + (", ".join(fb) if fb else "none") + ".")
w("- Only Wayback was queried; archive.today, Common Crawl, and tor2web-era mirrors outside Wayback were not.")
w("- A content hash matches only if the page bytes were captured exactly (Wayback's `id_` mode is the original body, but servers that rewrote or compressed content, or a page never captured, cannot be excluded). Captures with non-200 status were not fetched.")
open("work/log/phase52_an_end_archives.md", "w", encoding="utf-8").write("\n".join(L) + "\n")
print("\n".join(L)[:3000])
