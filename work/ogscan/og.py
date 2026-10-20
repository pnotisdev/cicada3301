"""OutGuess-style LSB extraction, independent re-implementation (own code, written from the algorithm as described in the
program's source, which was read as data; no third-party code is run).

Pipeline: `ogcoef` (Rust, this folder) lists the usable DCT-coefficient LSBs of a JPEG in the reader's order; this module
walks them with a key-driven pseudo-random iterator and decrypts with an RC4 stream, exactly as the retrieval path of the
original program is described:

  key -> iterator: RC4 stream seeded with MD5("Seeding" + key); first position = getword % 32; next position =
         position + getword % skipmod + 1 (skipmod 32 at first)
  header (4 bytes, 8 bits each, least significant bit first) read at those positions and decrypted with the RC4 stream
         MD5("Encryption" + key): seed = b0 | b1 << 8, length = b2 | b3 << 8 (little endian), length <= bitmap bytes
  body: iterator reseeded with the 16-bit seed (arc4_addrandom of the two seed bytes), then for every remaining byte
         skipmod = SKIPADJ(bits, bits - pos) * (bits - pos) / (8 * remaining) (float32) and 8 bits are read; the bytes
         are decrypted with a fresh "Encryption" stream from offset 0.
Default key: "Default key".
"""
import hashlib
import struct

import numpy as np

F32 = np.float32


class Arc4:
    __slots__ = ("s", "i", "j")

    def __init__(self):
        self.s = list(range(256))
        self.i = 0
        self.j = 0

    def addrandom(self, dat):
        self.i = (self.i - 1) & 255
        n_ = len(dat)
        s = self.s
        for n in range(256):
            self.i = (self.i + 1) & 255
            si = s[self.i]
            self.j = (self.j + si + dat[n % n_]) & 255
            s[self.i] = s[self.j]
            s[self.j] = si

    def getbyte(self):
        s = self.s
        self.i = (self.i + 1) & 255
        si = s[self.i]
        self.j = (self.j + si) & 255
        sj = s[self.j]
        s[self.i] = sj
        s[self.j] = si
        return s[(si + sj) & 255]

    def getword(self):
        v = self.getbyte() << 24
        v |= self.getbyte() << 16
        v |= self.getbyte() << 8
        v |= self.getbyte()
        return v


def initkey(typ, key):
    a = Arc4()
    a.addrandom(hashlib.md5(typ + key).digest())
    return a


class Iter:
    def __init__(self, key):
        self.a = initkey(b"Seeding", key)
        self.skipmod = 32
        self.off = self.a.getword() % self.skipmod

    def next(self):
        self.off += self.a.getword() % self.skipmod + 1
        return self.off

    def seed(self, seed16):
        self.a.addrandom(bytes([seed16 & 255, (seed16 >> 8) & 255]))

    def adapt(self, bits, datalen):
        x = bits
        y = bits - self.off
        thr = x // 32
        if y > thr:
            adj = F32(2)
        else:
            adj = F32(2) - F32(thr - y) / F32(thr)
        v = adj * F32(bits - self.off) / F32(8 * datalen)
        self.skipmod = int(v) & 0xFFFFFFFF if v >= 0 else 0


def read_bits(path):
    d = open(path, "rb").read()
    n = struct.unpack_from("<I", d, 0)[0]
    return np.frombuffer(d, dtype=np.uint8, count=n, offset=4)


def header(bits, key, ahead=None):
    """returns (seed, length, iterator, enc stream copy) or None if the walk runs off the bitmap"""
    nb = len(bits)
    it = Iter(key)
    enc = initkey(b"Encryption", key)
    raw = []
    for _ in range(4):
        b = 0
        for k in range(8):
            if it.off >= nb:
                return None
            b |= int(bits[it.off]) << k
            it.next()
        raw.append(b)
    h = [raw[j] ^ enc.getbyte() for j in range(4)]
    return h[0] | (h[1] << 8), h[2] | (h[3] << 8), it


def extract(bits, key, variant="continue", maxbytes=None):
    """body bytes of the payload for this key, or None. variant: 'continue' keeps the iterator position after the header,
    'restart' starts the body from a fresh iterator position (reseeded)."""
    nb = len(bits)
    hd = header(bits, key)
    if hd is None:
        return None
    seed, length, it = hd
    if length == 0 or length > (nb + 7) // 8:
        return None
    if variant == "restart":
        it2 = Iter(key)
        it = it2
    it.seed(seed)
    want = length if maxbytes is None else min(length, maxbytes)
    enc = initkey(b"Encryption", key)
    out = bytearray()
    remaining = length
    for _ in range(want):
        it.adapt(nb, remaining)
        if it.skipmod == 0:
            return None
        b = 0
        for k in range(8):
            if it.off >= nb:
                return None
            b |= int(bits[it.off]) << k
            it.next()
        out.append(b ^ enc.getbyte())
        remaining -= 1
    return seed, length, bytes(out)


def printable(b):
    return sum(1 for x in b if 32 <= x < 127 or x in (9, 10, 13)) / max(1, len(b))


if __name__ == "__main__":
    import sys
    bits = read_bits(sys.argv[1])
    key = sys.argv[2].encode() if len(sys.argv) > 2 else b"Default key"
    for variant in ("continue", "restart"):
        r = extract(bits, key, variant, maxbytes=200)
        if r is None:
            print(variant, "no header")
        else:
            seed, length, body = r
            print(variant, "seed", seed, "length", length, "printable", round(printable(body), 3), body[:120])
