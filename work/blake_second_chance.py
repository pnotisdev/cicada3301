"""Reproduce Cicada's 2012 "second chance" book code (NHYLD.jpg, signed) on plate 4 of Blake's Marriage of Heaven and Hell.

    python work/blake_second_chance.py

Text: plate 4 ("The Voice of the Devil") with the plate's own line breaks, read from the plate image at
gailgastfield.com/mhh/mhh4.jpg (Blake, public domain); the title is not counted. Rule: line:character, both from 1,
spaces, punctuation and the item numbers ("1.") counted -- the same rule as the 2012 Mabinogion and Agrippa codes.
"""
PLATE4 = """All Bibles or sacred codes, have been
the causes of the following Errors.
1. That Man has two real existing princi-
ples Viz: a Body & a Soul.
2. That Energy, call'd Evil, is alone from the
Body, & that Reason, call'd Good, is alone from
the Soul.
3. That God will torment Man in Eternity
for following his Energies.
But the following Contraries to these are True
1. Man has no Body distinct from his Soul
for that call'd Body is a portion of Soul discern'd
by the five Senses, the chief inlets of Soul in this
age.
2. Energy is the only life and is from the Body
and Reason is the bound or outward circumference
of Energy.
3. Energy is Eternal Delight.""".split("\n")

# the 22 pointers of the signed message (archive: 2012/additional docs/outguss/NHYLD.jpg.out)
CODE = "1:22 3:33 3:40 6:19 4:7 4:8 4:7 9:23 12:12 4:16 16:7 11:16 1:7 5:14 3:35 2:2 4:26 1:12 3:11 3:28 4:23 18:18"
EXPECTED = "cginiziglyaobyph.onion"  # the onion solvers reached (archive account of the second chance)


def decode(code=CODE, lines=PLATE4):
    get = lambda l, c: lines[l - 1][c - 1] if l <= len(lines) and c <= len(lines[l - 1]) else "?"
    return "".join(get(int(l), int(c)) for l, c in (p.split(":") for p in code.split())).lower()


if __name__ == "__main__":
    out = decode()
    assert out == EXPECTED, out
    # control: the same text re-wrapped at the plate's line length (40 columns, word wrap) gives garbage
    import textwrap
    wrapped = textwrap.wrap(" ".join(PLATE4), 40)
    ctrl = decode(lines=wrapped)
    hits = sum(a == b for a, b in zip(ctrl, EXPECTED))
    assert ctrl != EXPECTED
    print(f"plate 4, plate lines: {out}  (22/22)\n40-column wrap control: {ctrl}  ({hits}/22; the first lines wrap alike)")
