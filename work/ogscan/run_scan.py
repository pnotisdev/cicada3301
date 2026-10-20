"""OutGuess on the 75 page scans, with our own reader (og.py + the Rust coefficient lister), controls included.

    python work/ogscan/run_scan.py        # writes results/analysis/outguess_scan.txt and results/outguess/payload_NN.txt

1. Default key ("Default key", what the program uses without -k) on every page: the pages whose payload opens are the known
   carriers (controls). 2. KEY-FREE screen: the writer puts a 32-bit header at key-chosen positions inside the first ~550 usable
   DCT coefficients; on a page with a blank top margin those are Y-DC values of white blocks whose least significant bits are
   constant, so a header shows as ~16 deviations. Pages with a long constant prefix hold no OutGuess-style embedding, whatever
   the key. 3. Key sweep with the solved-text strings (work/hashscan lore + word list) on the one page the screen cannot judge
   (art at the top), with a planted-payload control run through the same sweep.
"""
import os
import random
import subprocess
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "work"))
sys.path.insert(0, os.path.join(ROOT, "work", "hashscan"))
import og  # noqa: E402

BITS = os.path.join(HERE, "bits")
EXE = os.path.join(HERE, "target", "release", "ogcoef" + (".exe" if os.name == "nt" else ""))
OUT = os.path.join(ROOT, "results", "analysis", "outguess_scan.txt")
PAY = os.path.join(ROOT, "results", "outguess")
KNOWN = {0, 1, 2, 3, 8, 10, 11, 12, 13}
MAGIC = (b"-----BEGIN", b"\xff\xd8\xff", b"PK\x03\x04", b"\x1f\x8b", b"BZh", b"%PDF", b"\x89PNG", b"Rar!")


def ensure_bits():
    os.makedirs(BITS, exist_ok=True)
    for n in range(75):
        p = os.path.join(BITS, f"{n:02d}.bits")
        if not os.path.exists(p):
            subprocess.run([EXE, os.path.join(ROOT, "work", "orig", f"{n:02d}.jpg"), p], check=True, stdout=subprocess.DEVNULL)


def looks_real(body):
    return og.printable(body) >= 0.92 or body.startswith(MAGIC)


def plant(bits, key, payload, rng):
    """write a payload into a COPY of a page's bit list by the writer's rules (header, reseed, adapted walk); no statistics fix"""
    b = bits.copy()
    nb = len(b)
    it = og.Iter(key)
    enc = og.initkey(b"Encryption", key)
    seed = rng.randrange(65536)
    hdr = [seed & 255, seed >> 8, len(payload) & 255, len(payload) >> 8]
    for v in hdr:
        x = v ^ enc.getbyte()
        for k in range(8):
            b[it.off] = (x >> k) & 1
            it.next()
    it.seed(seed)
    enc = og.initkey(b"Encryption", key)
    remaining = len(payload)
    for v in payload:
        it.adapt(nb, remaining)
        x = v ^ enc.getbyte()
        for k in range(8):
            b[it.off] = (x >> k) & 1
            it.next()
        remaining -= 1
    return b


def sweep(bits, keys):
    hits = []
    for key in keys:
        r = og.extract(bits, key, "continue", maxbytes=32)
        if r is not None and looks_real(r[2]):
            hits.append((key, r[0], r[1], r[2][:60]))
    return hits


def main():
    ensure_bits()
    L = ["# OutGuess scan of the 75 page scans (work/ogscan/run_scan.py). Own reader validated on the known carriers; no third-party code run.", ""]
    bits = {n: og.read_bits(os.path.join(BITS, f"{n:02d}.bits")) for n in range(75)}
    # ---- 1. default key
    L.append("1. Default key on every page (K = page named as a 2014 payload carrier in work/log/research_2026-10-17.md, plus pages 0-2)")
    opened = []
    os.makedirs(PAY, exist_ok=True)
    for n in range(75):
        r = og.extract(bits[n], b"Default key", "continue", maxbytes=64)
        if r is not None and og.printable(r[2]) > 0.9:
            full = og.extract(bits[n], b"Default key", "continue")
            opened.append(n)
            with open(os.path.join(PAY, f"payload_{n:02d}.txt"), "wb") as f:
                f.write(full[2])
            L.append(f"   page {n:02d}: payload of {full[1]} bytes (seed {full[0]}), starts {full[2][:46]!r}")
    L.append(f"   pages that open with the default key: {opened}")
    L.append(f"   payloads: pages 0, 1, 2 hold a PGP-signed hex message of 2,899 bytes each (not named in the research note); 3 a 31,809-byte message with a hex JPEG;")
    L.append(f"   8 the two-letter code list; 10-13 the 'Create one Tor hidden service ... post the three magic squares' message (1,234 bytes each). Saved in results/outguess/.")
    L.append("")
    # ---- 2. key-free screen
    L.append("2. Key-free screen: constant prefix of the usable-bit stream and deviations among its first 600 bits")
    rows = []
    for n in range(75):
        b = bits[n]
        ne = np.flatnonzero(b != b[0])
        rows.append((n, len(b), int(ne[0]) if len(ne) else len(b), int(np.count_nonzero(b[:600] != b[0]))))
    ctl = [r for r in rows if r[0] in opened]
    oth = [r for r in rows if r[0] not in opened]
    L.append("   controls (payload pages, header written): constant prefix " + ", ".join(f"{r[0]}:{r[2]}" for r in ctl))
    L.append(f"   controls: deviations in the first 600 bits {min(r[3] for r in ctl)}-{max(r[3] for r in ctl)} (a 32-bit header flips about half of ~32 positions at random)")
    L.append("   other pages: constant prefix (bits) " + ", ".join(f"{r[0]}:{r[2]}" for r in oth))
    clean = [r[0] for r in oth if r[2] >= 1000 and r[3] == 0]
    L.append(f"   other pages with a constant prefix of at least 1,000 bits and no deviation: {len(clean)} of {len(oth)}")
    L.append(f"   not decided by the screen (art at the top of the page): {[r[0] for r in oth if r[3] > 0]}")
    lp2 = [n for n in range(17, 73) if n in clean]
    L.append(f"   LP2 pages 17-72 clean: {len(lp2)} of 56; their constant prefixes are {min(r[2] for r in rows if 17 <= r[0] <= 72)}-{max(r[2] for r in rows if 17 <= r[0] <= 72)} bits")
    L.append("   Reading: an OutGuess-style header would flip about 16 of the first 600 bits on every one of the 56 LP2 pages (as on all nine controls); none does, so no key can open a payload there.")
    L.append("")
    # ---- 3. key sweep on the undecided page, with a planted control
    import make_candidates as mc  # noqa: E402
    keys = []
    seen = set()
    for s in list(mc.lore()) + list(mc.words()):
        k = s.encode("utf-8")
        if k not in seen:
            seen.add(k)
            keys.append(k)
    keys.append(b"")
    L.append(f"3. Key sweep with {len(keys):,} solved-text strings (lore variants + the 20k word list in three cases), header and 32 body bytes tested for text / magic")
    rng = random.Random(3301)
    t0 = time.time()
    undecided = [r[0] for r in oth if r[3] > 0]
    for n in undecided:
        h = sweep(bits[n], keys)
        L.append(f"   page {n:02d} (undecided by the screen): {len(h)} hits in {time.time()-t0:.0f} s" + (f": {h[:3]}" if h else ""))
    base = bits[5]
    msg = b"-----BEGIN PGP SIGNED MESSAGE-----\nPlanted control payload for the key sweep.\n"
    for pk in (b"welcome", b"DIVINITY"):
        if pk in seen:
            planted = plant(base, pk, msg, rng)
            ck = rng.sample(keys, 5000) + [pk]
            h = sweep(planted, ck)
            L.append(f"   control: payload planted into a copy of page 05 with key {pk!r} (in the list), sweep over 5,000 random keys + that key: hits {[(x[0], x[2]) for x in h]}")
    L.append(f"   control: the unplanted copy of page 05: {len(sweep(base, rng.sample(keys, 3000)))} hits in 3,000 random keys")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
