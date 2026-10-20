"""Peek at the bytes after the JPEG EOI marker in scans 05 and 10 (scouting, read-only)."""
import os, collections, math, hashlib
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "orig")
def ent(b):
    c = collections.Counter(b); n = len(b)
    return -sum(v / n * math.log2(v / n) for v in c.values())
for n in (5, 10):
    b = open(os.path.join(ORIG, f"{n:02d}.jpg"), "rb").read()
    # last EOI in the first JPEG: find via scanning for FFD9 after SOS is unreliable; use parser result sizes from audit
    k = b.find(b"\xff\xd9", 0)
    # robust: walk to true EOI by finding the *last* FFD9 whose following bytes are not a JPEG continuation; here use sizes
    sizes = {5: 336713, 10: 3486295}
    end = len(b) - sizes[n]
    print(f"image {n:02d}: jpeg part {end} bytes, trailing {len(b)-end}; bytes at EOI: {b[end-2:end].hex()}")
    t = b[end:]
    print("  trailing head hex :", t[:48].hex())
    print("  trailing head text:", t[:80])
    print("  trailing tail hex :", t[-32:].hex())
    print("  entropy bits/byte :", round(ent(t[:200000]), 4), " sha256:", hashlib.sha256(t).hexdigest()[:16])
    print("  contains FFD8FF (nested JPEG) at:", [i for i in range(0, min(len(t), 4000000)) if t[i:i+3] == b"\xff\xd8\xff"][:5])
    for sig, name in ((b"PK\x03\x04", "zip"), (b"Rar!", "rar"), (b"\x89PNG", "png"), (b"%PDF", "pdf"), (b"-----BEGIN", "pgp/ascii"), (b"7z\xbc\xaf", "7z"), (b"\x1f\x8b", "gzip"), (b"BZh", "bzip2")):
        pos = t.find(sig)
        if pos >= 0:
            print("  signature", name, "at", pos)
