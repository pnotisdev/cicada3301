"""Structure audit of the 75 original page scans (work/orig/NN.jpg): marker segments, trailing bytes, quant tables.
Read-only scouting (2026-10-19). Own parser, no third-party code."""
import hashlib, os, struct, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "orig")
MARK = {0xD8: "SOI", 0xD9: "EOI", 0xDB: "DQT", 0xC0: "SOF0", 0xC1: "SOF1", 0xC2: "SOF2", 0xC4: "DHT", 0xDA: "SOS",
        0xDD: "DRI", 0xFE: "COM", 0xE0: "APP0", 0xE1: "APP1", 0xE2: "APP2", 0xEE: "APP14"}

def parse(b):
    segs, i = [], 0
    assert b[0:2] == b"\xff\xd8"
    i = 2
    sos_end = None
    while i < len(b):
        if b[i] != 0xFF:
            return segs, i, "non-marker byte"
        while b[i] == 0xFF:
            i += 1
        m = b[i]; i += 1
        name = MARK.get(m, "M%02X" % m)
        if m == 0xD9:
            segs.append((name, 0)); return segs, i, "EOI"
        if 0xD0 <= m <= 0xD7 or m == 0x01:
            continue
        ln = struct.unpack(">H", b[i:i + 2])[0]
        body = b[i + 2:i + ln]
        segs.append((name, ln, body[:40]))
        i += ln
        if m == 0xDA:  # entropy-coded data until next real marker
            j = i
            while j < len(b) - 1:
                if b[j] == 0xFF and b[j + 1] not in (0x00,) and not (0xD0 <= b[j + 1] <= 0xD7):
                    break
                j += 1
            i = j
    return segs, i, "ran off end"

rows = []
for n in range(75):
    p = os.path.join(ORIG, f"{n:02d}.jpg")
    b = open(p, "rb").read()
    segs, end, why = parse(b)
    names = [s[0] for s in segs]
    qt = hashlib.sha1(b"".join(s[2] for s in segs if s[0] == "DQT")).hexdigest()[:8]
    com = [s[2] for s in segs if s[0] == "COM"]
    app = [(s[0], s[1]) for s in segs if s[0].startswith("APP")]
    sof = [s for s in segs if s[0].startswith("SOF")]
    prog = "progressive" if any(s[0] == "SOF2" for s in segs) else "baseline"
    trailing = len(b) - end if why == "EOI" else None
    rows.append((n, len(b), prog, qt, app, len(com), trailing, why, hashlib.sha512(b).hexdigest()[:12]))
print("n size prog qt-hash app comments trailing-bytes end sha512[:12]")
for r in rows:
    print(*r)
print("distinct quant-table hashes:", collections.Counter(r[3] for r in rows))
print("trailing bytes after EOI != 0:", [(r[0], r[6]) for r in rows if r[6]])
tgt = "36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a8425893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4"
hit = [n for n in range(75) if hashlib.sha512(open(os.path.join(ORIG, f"{n:02d}.jpg"), "rb").read()).hexdigest() == tgt]
print("scan whose SHA-512 equals the An End hash:", hit)
