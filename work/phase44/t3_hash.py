"""Phase 44 T3: hash every candidate file under every 512-bit hashlib function, compare with the An End value."""
import glob, hashlib, os, re, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import lp
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..")
md = open(os.path.join(ROOT, "Other repositories and work/cicada_3301/liber_primus/markdown/73.md"), encoding="utf-8").read()
FULL = re.search(r"\b36367763[0-9a-f]{120}\b", md).group(0)
assert len(FULL) == 128
FUN = {"sha512": hashlib.sha512, "sha3_512": hashlib.sha3_512, "blake2b": hashlib.blake2b}
items = {}
def addf(p):
    items[os.path.relpath(p, ROOT)] = open(p, "rb").read()
for pat in ["work/pages/*", "LiberPrimus.pdf", "work/ref/lp_*.txt", "work/ref/*.txt", "work/ref/*.tsv", "results/outguess/*", "work/ogscan/**/*", "work/orig/**/*", "assets/*"]:
    for p in glob.glob(os.path.join(ROOT, pat), recursive=True):
        if os.path.isfile(p) and os.path.getsize(p) < 80e6:
            addf(p)
for p in glob.glob(os.path.join(ROOT, "results/**/*payload*"), recursive=True):
    if os.path.isfile(p): addf(p)
# text variants of the transcription
t = open(lp.MASTER, encoding="utf-8").read()
for name, s in [("master_full", t), ("master_body", t.split("\n\n", 1)[1])]:
    for vn, v in [("raw", s), ("strip", s.strip()), ("crlf", s.replace("\n", "\r\n")), ("nonl", s.replace("\n", ""))]:
        items[f"variant:{name}:{vn}"] = v.encode()
body = t.split("\n\n", 1)[1]
runes = "".join(c for c in body if c in lp.RUNE_IDX)
items["variant:runes_only"] = runes.encode()
items["variant:runes_only_nl"] = (runes + "\n").encode()
for i, seg in enumerate(lp.load_segments()):
    items[f"variant:seg{i}_runes"] = "".join(lp.GP[x][0] for x in lp.runes_of(seg)).encode()
# hex-decoded payload strings
for k, v in list(items.items()):
    if "payload" in k and k.endswith(".txt"):
        try:
            h = re.sub(r"\s", "", v.decode())
            if re.fullmatch(r"[0-9a-fA-F]+", h) and len(h) % 2 == 0:
                items[k + ":hexdecoded"] = bytes.fromhex(h)
        except Exception:
            pass
n = hits = pre = 0
for k, v in sorted(items.items()):
    for fn, f in FUN.items():
        d = f(v).hexdigest(); n += 1
        if d == FULL: hits += 1; print("FULL MATCH", k, fn)
        if d[:8] == FULL[:8] or FULL[:8] in d: pre += 1; print("PREFIX-8 hit", k, fn, d[:20])
print(f"files/variants {len(items)}, digests {n}, full hits {hits}, 8-hex-prefix hits {pre}; chance of one 32-bit prefix hit ~ {n/2**32:.2e}")
