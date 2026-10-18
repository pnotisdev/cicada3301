"""Generate the matched-null KSB1 files for the h5rs flat-library campaign.

The null streams are the h5rs `rand:<seed>` streams: h5rs's splitmix64 Rng, replicated here
bit-exactly (state += 0x9E3779B97F4A7C15; z = xorshift-multiply mix; z ^= z >> 31; value =
next() % 29). Seeds 9000..9007 (the lp2_look SEED_BASE convention), 2407 values each = the
campaign's max offset 1999 + 300 runes + 107 margin, so every campaign offset is valid.

Writes:
  work/h5rs/data/null8.ksb  - seeds 9000..9007 (the campaign's matched null)
  work/h5rs/data/null4.ksb  - seeds 9000..9003 (the small-grid control)

KSB1 format (work/kscreen/export.py): "KSB1", u32 LE count, then per stream: u16 LE name
length, UTF-8 name, u32 LE stream length, values mod 29.
"""
import os
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
MASK = (1 << 64) - 1
N_VALUES = 2407  # off 0..1999 + 300 + 107


def splitmix64(state):
    """One h5rs Rng::next(): returns (value, new_state)."""
    state = (state + 0x9E3779B97F4A7C15) & MASK
    z = state
    z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & MASK
    z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & MASK
    return (z ^ (z >> 31)) & MASK, state


def random_stream(n, seed):
    s = seed
    out = bytearray(n)
    for i in range(n):
        z, s = splitmix64(s)
        out[i] = z % 29
    return bytes(out)


def write_ksb(path, items):
    b = b"KSB1" + struct.pack("<I", len(items))
    for name, v in items:
        nb = name.encode("utf-8")
        b += struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + v
    with open(path, "wb") as f:
        f.write(b)


def build(seeds, path):
    items = [(f"rand-{s}", random_stream(N_VALUES, s)) for s in seeds]
    write_ksb(path, items)
    print(f"wrote {path}: {len(items)} streams x {N_VALUES} values")
    for name, v in items:
        cnt = [v.count(x) for x in range(29)]
        print(f"  {name} first8={list(v[:8])} min_cnt={min(cnt)} max_cnt={max(cnt)}")


if __name__ == "__main__":
    build(range(9000, 9008), os.path.join(HERE, "data", "null8.ksb"))
    build(range(9000, 9004), os.path.join(HERE, "data", "null4.ksb"))
