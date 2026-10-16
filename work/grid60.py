"""The base-60 number grid inside segment 0.15 (pages 64-66, images 66-68): 256 bytes.

    python grid60.py hashes     # compare hashes of the grid (and LP texts) with the An End hash
    python grid60.py decrypt    # passphrase-derived AES / RC4 / XOR decryptions, scored
"""
import hashlib
import itertools
import math
import re
import sys
from collections import Counter

import lp
import stats

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx"  # 60 symbols


def grid_tokens():
    body = open(lp.MASTER, encoding="utf-8").read().split("\n\n", 1)[1].split("§")[0]
    pages = body.split("%")
    toks = []
    for p in (64, 65, 66):
        toks += re.findall(r"\b[0-4][0-9A-Za-x]\b", pages[p])
    return toks


def grid_bytes():
    toks = grid_tokens()
    vals = [DIGITS.index(t[0]) * 60 + DIGITS.index(t[1]) for t in toks]
    assert len(vals) == 256 and max(vals) <= 255, (len(vals), max(vals))
    return bytes(vals)


def an_end_hash():
    h = "".join(t[1:] for t in stats.SEGS[16] if isinstance(t, str) and t.startswith("#"))
    return h.lower()


def entropy(b):
    c = Counter(b)
    return -sum(v / len(b) * math.log2(v / len(b)) for v in c.values())


# ---------------------------------------------------------------- hash identity tests

def hash_candidates():
    """Byte strings that might be 'the page that hashes to' the An End value."""
    g = grid_bytes()
    toks = grid_tokens()
    cands = {
        "grid bytes": g,
        "grid hex": g.hex().encode(),
        "grid HEX": g.hex().upper().encode(),
        "grid base60 tokens joined": "".join(toks).encode(),
        "grid base60 tokens spaced": " ".join(toks).encode(),
        "grid base60 rows": "\n".join(" ".join(toks[i:i + 8]) for i in range(0, 256, 8)).encode(),
        "grid reversed": g[::-1],
    }
    segs = lp.load_segments()
    for i, (title, f) in lp.KNOWN.items():
        txt = lp.decrypt_known(segs, i)
        cands[f"solved {title} 0.{i}"] = txt.encode()
    for i in stats.UNSOLVED:
        r = lp.runes_of(segs[i])
        cands[f"runes 0.{i}"] = "".join(lp.GP[x][0] for x in r).encode("utf-8")
    return cands


def hashes():
    target = an_end_hash()
    print("An End hash:", target, f"({len(target) * 4} bits)")
    algos = ["sha512", "sha3_512", "blake2b"]
    hits = 0
    for name, data in hash_candidates().items():
        for a in algos:
            h = hashlib.new(a, data).hexdigest()
            if h == target:
                print("  MATCH:", name, a)
                hits += 1
    print(f"tested {len(hash_candidates())} candidates x {algos}: {hits} matches")
    g = grid_bytes()
    print(f"grid: 256 bytes, entropy {entropy(g):.3f} bits/byte (uniform random 256 bytes ~7.2), "
          f"first 16: {g[:16].hex()}")


# ---------------------------------------------------------------- passphrase decryption

def passphrases():
    segs = lp.load_segments()
    words, phrases = set(), set()
    for i, (title, f) in lp.KNOWN.items():
        plain = f(lp.runes_of(segs[i]))
        ws = [w for w, _, _ in lp.word_spans(segs[i], plain)]
        words.update(ws)
        for a in range(len(ws)):
            for n in (2, 3, 4):
                phrases.add(" ".join(ws[a:a + n]))
        for sentence in re.split(r"[.]", lp.decrypt_known(segs, i)):
            s = sentence.strip()
            if s:
                phrases.add(s)
    extra = ["3301", "1033", "cicada", "cicada3301", "liberprimus", "liber primus", "intus", "instar", "divinity",
             "firfumferenfe", "circumference", "primes", "totient", "pilgrim", "welcome", "parable", "koan",
             "self-reliance", "agrippa", "an end", "deep web", "FULMAEAYOEA", "7A35090F", "0x7A35090F"]
    out = set()
    for p in list(words) + list(phrases) + extra:
        for v in (p, p.lower(), p.upper(), p.lower().replace(" ", ""), p.upper().replace(" ", ""),
                  p.replace("U", "V").replace("C", "K") if p.isupper() else p):
            out.add(v)
    return sorted(out)


def score_plain(b):
    printable = sum(32 <= x < 127 or x in (9, 10, 13) for x in b) / len(b)
    magic = None
    for m, name in ((b"\x1f\x8b", "gzip"), (b"PK\x03\x04", "zip"), (b"-----", "armor"), (b"\x89PNG", "png"),
                    (b"\xff\xd8\xff", "jpeg"), (b"%PDF", "pdf"), (b"BZh", "bzip2"), (b"\x78\x9c", "zlib"),
                    (b"http", "url"), (b"Salted__", "openssl")):
        if b.startswith(m):
            magic = name
    if b[:1] and b[0] & 0x80 and (b[0] & 0x3C) >> 2 in (1, 3, 9, 18) and b[0] & 0x40 == 0:
        magic = magic or "pgp-old-packet?"
    return printable, magic


def evp_bytes_to_key(password, salt, key_len, iv_len, md=hashlib.md5):
    d, prev = b"", b""
    while len(d) < key_len + iv_len:
        prev = md(prev + password + salt).digest()
        d += prev
    return d[:key_len], d[key_len:key_len + iv_len]


def decrypt():
    from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
    g = grid_bytes()
    pw = passphrases()
    print(f"{len(pw)} passphrases")
    results = []
    kdfs = {
        "md5": lambda p, n: (hashlib.md5(p).digest() * 2)[:n],
        "sha1": lambda p, n: (hashlib.sha1(p).digest() * 2)[:n],
        "sha256": lambda p, n: hashlib.sha256(p).digest()[:n],
        "sha512": lambda p, n: hashlib.sha512(p).digest()[:n],
        "evp_md5": lambda p, n: evp_bytes_to_key(p, b"", n, 16)[0],
        "raw-pad": lambda p, n: (p + b"\0" * n)[:n],
    }
    zero = b"\0" * 16
    for p in pw:
        pb = p.encode()
        for kname, kdf in kdfs.items():
            for klen in (16, 24, 32):
                key = kdf(pb, klen)
                if len(key) != klen:
                    continue
                trials = {
                    "ecb": Cipher(algorithms.AES(key), modes.ECB()),
                    "cbc-iv0": Cipher(algorithms.AES(key), modes.CBC(zero)),
                    "ctr-0": Cipher(algorithms.AES(key), modes.CTR(zero)),
                }
                for mname, ciph in trials.items():
                    out = ciph.decryptor().update(g)
                    pr, mg = score_plain(out)
                    results.append((pr, mg, f"AES-{klen * 8}-{mname}", kname, p, out[:48]))
                # CBC with the first block as IV
                out = Cipher(algorithms.AES(key), modes.CBC(g[:16])).decryptor().update(g[16:])
                pr, mg = score_plain(out)
                results.append((pr, mg, f"AES-{klen * 8}-cbc-iv=block0", kname, p, out[:48]))
        # stream: XOR with SHA-512 counter stream, RC4-like via ARC4
        stream = b"".join(hashlib.sha512(pb + i.to_bytes(4, "big")).digest() for i in range(4))
        out = bytes(a ^ b for a, b in zip(g, stream))
        pr, mg = score_plain(out)
        results.append((pr, mg, "XOR sha512-ctr", "-", p, out[:48]))
        try:
            from cryptography.hazmat.decrepit.ciphers.algorithms import ARC4
        except Exception:
            ARC4 = getattr(algorithms, "ARC4", None)
        if ARC4 is not None:
            out = Cipher(ARC4(hashlib.md5(pb).digest()), mode=None).decryptor().update(g)
            pr, mg = score_plain(out)
            results.append((pr, mg, "RC4 md5(key)", "-", p, out[:48]))
    results.sort(key=lambda r: (r[1] is not None, r[0]), reverse=True)
    n = len(results)
    print(f"{n} decryptions. Random 256-byte output is printable ~37% of the time per byte "
          f"(max over {n} trials ~0.47).")
    for r in results[:12]:
        print(f"  printable {r[0]:.2f} magic={r[1]} {r[2]} kdf={r[3]} pass={r[4]!r}  {r[5][:32]!r}")
    return results


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    {"hashes": hashes, "decrypt": decrypt}[sys.argv[1]]()
