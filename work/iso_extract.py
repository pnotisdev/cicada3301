"""Copy one file out of an ISO 9660 image as raw bytes (nothing is mounted or run).

    python work/iso_extract.py work/ref/cicados_iso/3301.iso DATA/560.13 work/ref/cicados_iso/560.13
    python work/iso_extract.py work/ref/cicados_iso/3301.iso --list

Reads the primary volume descriptor and walks the directory records; names are matched case-insensitively with the
';1' version suffix stripped.
"""
import sys

SECTOR = 2048


def records(f, lba, size):
    f.seek(lba * SECTOR)
    data = f.read(size)
    i = 0
    while i < len(data):
        n = data[i]
        if n == 0:  # records never straddle a sector: skip to the next one
            i = (i // SECTOR + 1) * SECTOR
            continue
        r = data[i:i + n]
        name = r[33:33 + r[32]]
        if name not in (b"\x00", b"\x01"):
            yield (name.decode("ascii", "replace").split(";")[0].rstrip("."), int.from_bytes(r[2:6], "little"),
                   int.from_bytes(r[10:14], "little"), bool(r[25] & 2))
        i += n


def root(f):
    f.seek(16 * SECTOR)
    pvd = f.read(SECTOR)
    assert pvd[1:6] == b"CD001", "not an ISO 9660 image"
    r = pvd[156:190]
    return int.from_bytes(r[2:6], "little"), int.from_bytes(r[10:14], "little")


def walk(f, lba, size, prefix=""):
    for name, l, s, is_dir in records(f, lba, size):
        path = prefix + name
        yield path, l, s, is_dir
        if is_dir:
            yield from walk(f, l, s, path + "/")


if __name__ == "__main__":
    iso = sys.argv[1]
    with open(iso, "rb") as f:
        entries = list(walk(f, *root(f)))
        if sys.argv[2] == "--list":
            for p, l, s, d in entries:
                print(f"{'d' if d else '-'} {s:>12} {p}")
            sys.exit()
        want = sys.argv[2].upper()
        hit = [e for e in entries if e[0].upper() == want and not e[3]]
        assert hit, f"{want} not in image"
        _, l, s, _ = hit[0]
        f.seek(l * SECTOR)
        open(sys.argv[3], "wb").write(f.read(s))
        print(f"{want}: {s} bytes -> {sys.argv[3]}")
