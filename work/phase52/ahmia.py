import urllib.request, urllib.parse, re, http.cookiejar, time, json, sys
cj = http.cookiejar.CookieJar()
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj)); op.addheaders=[("User-Agent","Mozilla/5.0")]
qs = sys.argv[1:]
res = {}
for q in qs:
    home = op.open("https://ahmia.fi/", timeout=30).read().decode("utf-8","replace")
    m = re.search(r'type="hidden" name="(\w+)" value="(\w+)"', home)
    u = "https://ahmia.fi/search/?" + urllib.parse.urlencode({"q": q, m.group(1): m.group(2)})
    t = op.open(u, timeout=30).read().decode("utf-8","replace")
    res[q] = {"len": len(t), "onions": sorted(set(re.findall(r"[a-z2-7]{16,56}\.onion", t)))[:20], "noresults": "No results" in t or "no results" in t.lower()}
    print(q, res[q], flush=True); time.sleep(2)
json.dump(res, open("work/phase52/ahmia_results.json","w"), indent=1)
