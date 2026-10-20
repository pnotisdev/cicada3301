"""Look inside the data appended to scan 05 (scouting, read-only). Own code."""
import os, re, io, hashlib
import numpy as np, cv2
HERE = os.path.dirname(os.path.abspath(__file__))
ORIG = os.path.join(HERE, "..", "..", "orig")
b = open(os.path.join(ORIG, "05.jpg"), "rb").read()
end = len(b) - 336713
t = b[end:]
# printable prefix
k = 0
while k < len(t) and (32 <= t[k] < 127 or t[k] in (9, 10, 13)):
    k += 1
print("printable prefix length:", k)
print(repr(t[:k][:600]))
print("next 64 bytes hex:", t[k:k+64].hex())
# is the remainder a byte-reversed JPEG?
rest = t[k:]
for name, data in (("remainder", rest), ("whole trailing reversed", t[::-1]), ("remainder reversed", rest[::-1])):
    i = data.find(b"\xff\xd8\xff")
    print(name, "FFD8FF at", i, "len", len(data))
    if i >= 0:
        arr = np.frombuffer(data[i:], dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        print("  decode:", None if img is None else img.shape)
        if img is not None:
            out = os.path.join(HERE, f"scan05_trailing_{name.split()[0]}.png")
            cv2.imwrite(out, img)
            print("  wrote", os.path.relpath(out, os.path.join(HERE, "..", "..", "..")))
