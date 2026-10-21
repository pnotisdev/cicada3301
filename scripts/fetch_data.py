"""Download the third-party data this project needs, verify it, and build the verified transcription.

    python scripts/fetch_data.py            # text data only (transcription, word list, Emerson)
    python scripts/fetch_data.py --images   # also the 75 original Liber Primus page images (~50 MB)
    python scripts/fetch_data.py --corpora  # also the git-ignored key-source / language corpora (~25 MB; docs/SOURCES.md)

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


GUT = "https://www.gutenberg.org/cache/epub/{0}/pg{0}.txt"
# (path under work/ref, url, sha256 of the copy the results were computed on); non-strict: Gutenberg re-generates headers
CORPORA = [(f"corpora/pg{n}.txt", GUT.format(n), d) for n, d in (
    (10, "0204adaed1f25700aa854218cae63c7172228c41088f335e99167a071eed83c0"),
    (1012, "568035b4af7bda4f69f8ed5dea160f59bcf5b9371c7f2a62a97f94b826c0c1c6"),
    (1497, "3d2e397122881d7737a48fb80e71cddf4c78cda54ceac7e0905fe945dfab48fd"),
    (16328, "8909085dc48daf123d29c40ecbb3837b16ba7f96bf0cbb9fe72de133a2d35348"),
    (17489, "a5de514ba7b9f2e1790e7e259c4e8b7a35ae1d29e4bf9a5f8767039c58b80503"),
    (1998, "0854ebabe235d46c8e5e099418c5189b1df0848898c552009b70d924b9065d05"),
    (2000, "534f41d59f7142163fa0964076ac6351845c006ea6433778be637fac6d5b04d7"),
    (2009, "2b13c8524d813e706ad23336d81a142d48b44f1f96788b41494a0a83e1b82f88"),
    (205, "2d9a76a2e3e8195c69430516ebd33c4d0757a53ad432ff6186b7b794e6fe99f9"),
    (218, "84ac8411841a4d8f5f4a49b6a2cd1f466917c6a5af72916d5e0b2b1ecb2f659c"),
    (2229, "fed2a58edd6910ee96d27ada614d34bcc41f03750d86541c41246bb74c564ff7"),
    (227, "2620ba82c00964d1a1f0458c8cf171946f158a06de0d0e764594170602c4c7b8"),
    (26, "aeedc9f33e0c2a6422d2f557462fb87cd2430974c6aed30a26803be5394a741a"),
    (2680, "6977474f82a39dd88a4af31a59504821658174d33c177732c54357e4d680b96c"),
    (3800, "647f0227f3700b5d221a004fc545568c879f6f204e952f1cf0c24672676c2a60"),
    (4363, "6ee088f717d3760036086f108c03d57588036c9d344b7d71edbef4e631bd374a"))] + [
    (f"corpora/cited/pg{n}.txt", GUT.format(n), d) for n, d in (
        (5160, "e177d7c2ff357bc5e3f506c7131d158d8b8f5e05883110bdf495f0d9d7f49886"),
        (1934, "a5b76d4de22f42e1bf40f08256a329728f4cb7ad18d6581709aa7a9683c5e455"),
        (45315, "fc9a76619fcb76c58273d7fc9e034108b0d7fffed3780ad5b8226954a12b289a"))] + [
    ("corpora/cited/agrippa_1651_archive_djvu.txt", "https://archive.org/download/threebooksoccult/threebooksoccult_djvu.txt",
     "18c939d60813846946b37f557ad172f3a4b5ad721cdfb8108891311de2827d9b"),
    ("corpora/cited/liber_al_oto.html", "https://lib.oto-usa.org/libri/liber0220.html?pages=no",
     "2be978efc94fe4b4319d45e5d34f59bda81e344b8475c1ff684b805cb372e6b8")] + [
    (f"oldenglish/pg{n}.txt", GUT.format(n), d) for n, d in (
        (9700, "10cad7e138ca28b0f342711fa6c2d96cab047823bfea518d86d6b2703d83f1a7"),
        (22120, "94ae337faad105ae63b9a72bb82baa34fba4a6e1468de5b97cbb4c56db34cd7a"))]


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
    ap.add_argument("--corpora", action="store_true", help="also fetch the key-source / language corpora (docs/SOURCES.md)")
    args = ap.parse_args()
    if args.corpora:
        for rel, url, digest in CORPORA:
            dest = os.path.join(REF, *rel.split("/"))
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            print(f"{rel:46s} {fetch(url, dest, digest, strict=False)}")
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
