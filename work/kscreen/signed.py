"""Signed 3301 material inside the book's own page scans, as key streams for the library-wide kscreen screen (data/signed.ksb + data/signed.tsv).

Idea (2026-10-20): the key is a flat stream of numbers that sits inside the book, and only PGP-signed 3301 material counts as a source. The signed material that
is physically in the page scans is what work/ogscan recovered from the 2014 OutGuess payloads (results/outguess/payload_NN.txt):
  pages 0, 1, 2     a clearsigned message that is one 991-byte hex blob (random-looking)
  page 3            a clearsigned message with a hex JPEG
  pages 10 .. 13    a clearsigned message (create one Tor hidden service ...)
each with an RSA signature packet. The armor CRC-24 is checked and the issuer key id is printed. The signatures are NOT verified (that needs a trusted public key).

Streams: the three hex blobs and their concatenation, the RSA signature values (one MPI per signature) and their concatenation, each read as
  A  bytes with b >= 232 rejected, then mod 29 (exactly uniform)     B  bytes mod 29 (IoC 1.0018 from the bias alone)
  C  the big integer in base 29, least significant digit first        D  the same, most significant first (the biased top digit dropped)
forwards and with the bytes reversed (tags Ar, Br, Cr, Dr), and
  H  hash streams (sha256 / sha512 / md5 counter, sha256 chain; mod and reject, as export.hash_streams) seeded with every blob, signature value, message text and concatenation, 4,000 values each.
A stream is dropped when it is shorter than 400 values (a 300-rune screen window needs 383) or when LP2's flat IoC excludes it as a key (predicted IoC under English plaintext above
max(1.003, 1.002 + 1.6 / n), export_hyp.py's rule for short streams; hex digits and ASCII text fail this and are not built).

    python work/kscreen/signed.py          # -> work/kscreen/data/signed.ksb, signed.tsv; prints the packet facts
"""
import base64
import datetime
import hashlib
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
ROOT = os.path.dirname(WORK)
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import export  # noqa: E402
import keystreams  # noqa: E402

N = 29
OUT = os.path.join(HERE, "data")
OG = os.path.join(ROOT, "results", "outguess")
PAGES = (0, 1, 2, 3, 10, 11, 12, 13)
BLOB_PAGES = (0, 1, 2)
MINLEN = 400
HASH_LEN = 4000


def crc24(data):
    crc = 0xB704CE
    for b in data:
        crc ^= b << 16
        for _ in range(8):
            crc <<= 1
            if crc & 0x1000000:
                crc ^= 0x1864CFB
    return crc & 0xFFFFFF


def read_payload(page):
    """(clearsigned body text, signature packet bytes, armor CRC ok) of one recovered payload"""
    with open(os.path.join(OG, f"payload_{page:02d}.txt"), encoding="latin-1", newline="") as f:
        lines = f.read().splitlines()
    i = lines.index("-----BEGIN PGP SIGNED MESSAGE-----")
    j = lines.index("-----BEGIN PGP SIGNATURE-----")
    k = lines.index("-----END PGP SIGNATURE-----")
    h = i + 1
    while lines[h].strip():
        h += 1
    body = "\n".join(lines[h + 1:j])
    s = j + 1
    while lines[s].strip() and ":" in lines[s]:          # armor headers, if any
        s += 1
    if not lines[s].strip():
        s += 1
    b64, crc = [], None
    for ln in lines[s:k]:
        if ln.startswith("="):
            crc = ln[1:].strip()
            break
        b64.append(ln.strip())
    sig = base64.b64decode("".join(b64))
    ok = crc is not None and base64.b64encode(crc24(sig).to_bytes(3, "big")).decode() == crc
    return body, sig, ok


def subpackets(data):
    out, i = [], 0
    while i < len(data):
        n = data[i]
        assert n < 192, "long subpacket length not handled"
        out.append((data[i + 1] & 0x7F, data[i + 2:i + 1 + n]))
        i += 1 + n
    return out


def parse_signature(pkt):
    """minimal OpenPGP v4 signature packet reader: the facts and the RSA signature value (the MPI)"""
    t = pkt[0]
    assert t & 0x80 and not t & 0x40, "old-format packet expected"
    assert (t >> 2) & 0xF == 2, "not a signature packet"
    n = (1, 2, 4)[t & 3]
    ln = int.from_bytes(pkt[1:1 + n], "big")
    body = pkt[1 + n:1 + n + ln]
    ver, stype, pub, hsh = body[0], body[1], body[2], body[3]
    hl = int.from_bytes(body[4:6], "big")
    hashed = body[6:6 + hl]
    p = 6 + hl
    ul = int.from_bytes(body[p:p + 2], "big")
    unhashed = body[p + 2:p + 2 + ul]
    p += 2 + ul + 2                                       # skip the 2-byte hash prefix
    bits = int.from_bytes(body[p:p + 2], "big")
    mpi = body[p + 2:p + 2 + (bits + 7) // 8]
    issuer = next((v for ty, v in subpackets(unhashed) if ty == 16), b"")
    created = next((int.from_bytes(v, "big") for ty, v in subpackets(hashed) if ty == 2), 0)
    return dict(ver=ver, stype=stype, pub=pub, hash=hsh, bits=bits, mpi=mpi, issuer=issuer.hex().upper(),
                created=datetime.datetime.fromtimestamp(created, datetime.timezone.utc).strftime("%Y-%m-%d %H:%M"))


def digits_lsd(b):
    """the big-endian integer of b in base 29, least significant digit first, without the (biased) top digit"""
    x = int.from_bytes(b, "big")
    d = []
    while x:
        x, r = divmod(x, N)
        d.append(r)
    return np.array(d[:-1], dtype=np.int64)


def conversions(b, tag):
    a = np.frombuffer(b, dtype=np.uint8).astype(np.int64)
    lsd = digits_lsd(b)
    return {f"A{tag}": a[a < 232] % N, f"B{tag}": a % N, f"C{tag}": lsd, f"D{tag}": lsd[::-1]}


def hash_streams(seed, label):
    need = HASH_LEN * 2
    streams = {}
    for hn, H in (("sha256", hashlib.sha256), ("sha512", hashlib.sha512), ("md5", hashlib.md5)):
        raw, i = bytearray(), 0
        while len(raw) < need:
            raw += H(seed + i.to_bytes(4, "big")).digest()
            i += 1
        streams[f"{hn}-ctr"] = bytes(raw)
    raw, x = bytearray(), hashlib.sha256(seed).digest()
    while len(raw) < need:
        raw += x
        x = hashlib.sha256(x).digest()
    streams["sha256-chain"] = bytes(raw)
    out = {}
    for g, raw in streams.items():
        b = np.frombuffer(raw, dtype=np.uint8).astype(np.int64)
        out[f"H {g} mod :{label}"] = (b % N)[:HASH_LEN]
        out[f"H {g} reject :{label}"] = (b[b < 232] % N)[:HASH_LEN]
    return out


def sources():
    """name -> bytes of every block of signed material, and the human-readable facts"""
    blocks, facts = {}, []
    sigs, texts, blobs = {}, {}, {}
    for pg in PAGES:
        body, pkt, crc_ok = read_payload(pg)
        info = parse_signature(pkt)
        sigs[pg], texts[pg] = info["mpi"], body.encode("latin-1")
        if pg in BLOB_PAGES:
            blobs[pg] = bytes.fromhex("".join(body.split()))
        facts.append(f"page {pg:2d}: signature armor CRC {'ok' if crc_ok else 'BAD'}, v{info['ver']} type {info['stype']} pubkey {info['pub']} (1 = RSA) hash {info['hash']} (2 = SHA-1), "
                     f"{info['bits']}-bit value, created {info['created']} UTC, issuer {info['issuer']}; message {len(body)} characters"
                     + (f", hex blob {len(blobs[pg])} bytes" if pg in blobs else ""))
    for pg, b in blobs.items():
        blocks[f"blob{pg}"] = b
    blocks["blob012"] = b"".join(blobs[pg] for pg in BLOB_PAGES)
    for pg, b in sigs.items():
        blocks[f"sigval{pg}"] = b
    blocks["sigval-all"] = b"".join(sigs[pg] for pg in PAGES)
    seeds = dict(blocks)
    for pg, t in texts.items():
        seeds[f"message{pg}"] = t
    return blocks, seeds, facts


def main():
    os.makedirs(OUT, exist_ok=True)
    blocks, seeds, facts = sources()
    print("\n".join(facts))
    cand = {}
    for name, b in blocks.items():
        for suffix, bb in (("", b), (" reversed", b[::-1])):
            for key, v in conversions(bb, "r" if suffix else "").items():
                cand[f"{key} {name}"] = v
    for name, b in seeds.items():
        cand.update(hash_streams(b, name))
    P = keystreams.english_distribution()
    kept, stats = {}, {}
    for name, v in cand.items():
        fam = name.split()[0]
        s = stats.setdefault(fam, {"built": 0, "too short": 0, "flat-IoC excluded": 0, "kept": 0})
        s["built"] += 1
        if len(v) < MINLEN:
            s["too short"] += 1
            continue
        n = min(4000, len(v))
        pi = max(keystreams.predicted_ioc(v, P, 1, n=n), keystreams.predicted_ioc(v, P, -1, n=n))
        if pi > max(1.003, 1.002 + 1.6 / n):              # the histogram of a short flat stream alone adds about 0.8 / n
            s["flat-IoC excluded"] += 1
            continue
        kept[name] = v
        s["kept"] += 1
    rows = export.write_ksb(os.path.join(OUT, "signed.ksb"), kept, os.path.join(OUT, "signed.tsv"))
    for fam, s in sorted(stats.items()):
        print(fam, s)
    pairs = sum(max(0, n - 382) for _, n, _, _ in rows)
    print(f"signed.ksb: {len(rows)} streams, {pairs} (stream, offset) pairs for a 300-rune window")


if __name__ == "__main__":
    main()
