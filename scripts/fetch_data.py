"""Download the third-party data this project needs, verify it, and build the verified transcription.

    python scripts/fetch_data.py            # text data only (transcription, word list, Emerson)
    python scripts/fetch_data.py --images   # also the 75 original Liber Primus page images (~50 MB)

Nothing here is redistributed in the repository: every file is fetched from its public source at a
pinned commit and checked against a SHA-256 recorded below. The script then applies
work/ref/errata_lines.tsv to the rtkd/iddqd master transcription to produce work/ref/lp_verified.txt.
"""
import argparse
import hashlib
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REF = os.path.join(ROOT, "work", "ref")
ORIG = os.path.join(ROOT, "work", "orig")
IDDQD = "https://raw.githubusercontent.com/rtkd/iddqd/f2267b0c2f1e1d2662806b90b9c3a2953b3a7023"
WORDS = "https://raw.githubusercontent.com/first20hours/google-10000-english/d0736d492489198e4f9d650c7ab4143bc14c1e9e"

# (local name, url, sha256, strict)  -- strict=False: upstream may re-generate headers; mismatch only warns
TEXT_FILES = [
    ("lp_master.txt", f"{IDDQD}/liber-primus__transcription--master/liber-primus__transcription--master.txt",
     "e21743ccd9a07f3845d52a329c61b9fa69e9ca6a44ee3ba0db8f28a0d7065004", True),
    ("lp_keys.txt", f"{IDDQD}/liber-primus__keys/liber-primus__keys.txt",
     "ff1106e69d2136381c0ac166a0836c64a6d64078bce4be33436c2198af758ac3", True),
    ("lp_translation.txt", f"{IDDQD}/liber-primus__translation/liber-primus__translation.txt",
     "adce48cfea746fd5add5071c85a34a998a546ca94c009bcd796cd3e699cc1c47", True),
    ("english_20k.txt", f"{WORDS}/20k.txt",
     "4ed6e5336d7760d281f7e72df31827da880c861363e820d8c65666b0f10d9ac0", True),
    ("emerson_essays1.txt", "https://www.gutenberg.org/cache/epub/2944/pg2944.txt",
     "5d9d28c12da8bd9aaf3043e9a2d08fbd46116efd5a3736490a393599aef6d278", False),
]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(url, dest, digest, strict=True):
    if os.path.exists(dest) and sha256(dest) == digest:
        return "cached"
    req = urllib.request.Request(url, headers={"User-Agent": "cicada3301-research/1.0"})
    with urllib.request.urlopen(req, timeout=120) as r:
        data = r.read()
    with open(dest, "wb") as f:
        f.write(data)
    got = sha256(dest)
    if got != digest:
        msg = f"SHA-256 mismatch for {os.path.basename(dest)}: got {got}"
        if strict:
            os.remove(dest)
            raise SystemExit(msg)
        print("  WARNING:", msg, "(non-strict; continuing)")
    return "downloaded"


def build_verified():
    master = os.path.join(REF, "lp_master.txt")
    lines = open(master, "rb").read().decode("utf-8").split("\n")
    patches = 0
    with open(os.path.join(REF, "errata_lines.tsv"), "rb") as f:
        for raw in f.read().decode("utf-8").split("\n"):
            if not raw or raw.startswith("#"):
                continue
            n, old, new = raw.split("\t")
            n = int(n)
            if lines[n - 1] != old:
                raise SystemExit(f"errata line {n} does not match the master transcription")
            lines[n - 1] = new
            patches += 1
    with open(os.path.join(REF, "lp_verified.txt"), "wb") as f:
        f.write("\n".join(lines).encode("utf-8"))
    return patches


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--images", action="store_true", help="also fetch the 75 original page images (~50 MB)")
    args = ap.parse_args()
    os.makedirs(REF, exist_ok=True)
    for name, url, digest, strict in TEXT_FILES:
        print(f"{name:22s} {fetch(url, os.path.join(REF, name), digest, strict)}")
    print(f"lp_verified.txt        built ({build_verified()} errata lines applied)")
    if args.images:
        os.makedirs(ORIG, exist_ok=True)
        hashes = {}
        with open(os.path.join(ROOT, "scripts", "image_hashes.txt")) as f:
            for line in f:
                d, name = line.split()
                hashes[name.lstrip("*")] = d
        for name, digest in sorted(hashes.items()):
            url = f"{IDDQD}/liber-primus__images--full/{name}"
            status = fetch(url, os.path.join(ORIG, name), digest, True)
            print(f"\r{name} {status}   ", end="", flush=True)
        print(f"\n{len(hashes)} page images verified in work/orig/")


if __name__ == "__main__":
    sys.exit(main())
