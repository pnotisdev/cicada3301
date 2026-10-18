"""Outer-alphabet relabelling front-end for the kscreen engine (STATUS left-item 1 /
docs/NEGATIVE_SPACE.md section 0 item 5).

Hypothesis family (NOT covered by any previous screen):

    c_i = sigma(p_i + m * k_{j_i} + b)   (mod 29)

where sigma is a permutation of the GP alphabet 0..28 applied AFTER the additive key:
the ciphertext runes are relabelled by a keyword-mixed (or otherwise permuted) OUTER
alphabet before they reach the page. Every existing screen assumes the model
c = D(p) + m*k + b with the substitution D on the PLAINTEXT side (inner). An outer
sigma does not change the IoC of the ciphertext, so all screens saw flat text and
this family is a live blind spot.

The exact transformation that makes the family visible to the existing screen:

    c' = sigma_inv(c)

Why: the screen's decoder computes p = c' - k (mod 29) per rune (through its
anti-repeat beam, but the per-rune value is always c' - k). With c' = sigma_inv(c) =
sigma_inv(sigma(p + k)) = p + k, the screen decodes p exactly. The anti-repeat rule
is preserved: sigma_inv is a bijection, so the encryptor's collision c_i == c_{i-1}
is exactly the collision c'_i == c'_{i-1} that the screen's prev/P chain checks.

Convention decided and documented here:
  * sigma is given as a list of length 29 with sigma[i] = image of i (tableau position
    x -> rune). For a keyword-mixed alphabet, sigma IS the mixed alphabet itself.
  * relabel_window(cipher_indices, sigma) returns sigma_inv applied to every
    ciphertext index (the front-end transformation c -> c' above).
  * In a windows file, the W line's `prev` rune is relabelled the same way (it is a
    ciphertext rune, part of the collision chain). L lines (word lengths) pass
    through unchanged. P / S / G lines are rejected: those hypotheses do not commute
    with an outer relabelling (P values are affine combinations of ciphertext runes,
    G indices point into un-relabelled ciphertext).

CLI:
    python work/kscreen/relabel_export.py table atbash | kw:<KEYWORD> | aff:<a>[:<b>]
    python work/kscreen/relabel_export.py one <sigma> <windows.txt> <out.txt>
    python work/kscreen/relabel_export.py batch <sigma>
        # rewrites data/segments.txt, data/heads.txt, data/pages.txt into
        # data/relabel/<sigma-name>/... (sigma-name = spec with ':' -> '_')
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)

import lp  # noqa: E402

N = lp.N

# The 23 single-letter Latin names of the Gematria Primus. The six digraph runes
# (TH EO NG OE AE IA EA) cannot be spelled by one keyword character and are never
# auto-merged: a keyword is read character by character.
_SINGLE = {latin: i for i, (_, latin, _) in enumerate(lp.GP) if len(latin) == 1}
# Sound-equivalent spellings with no rune of their own; the V->U normalization this
# project uses (work/lp.normalize), plus K->C, Q->C, Z->S. Only these are applied:
# QU, IA, ING and the rest of lp.normalize are NOT collapsed here.
_ALIAS = {"V": "U", "K": "C", "Q": "C", "Z": "S"}


def sigma_atbash():
    """Atbash over the whole GP alphabet: sigma(x) = 28 - x. In-book precedent: the
    'A Warning' page applies Atbash over the Gematria Primus. An involution, so
    sigma == sigma_inv."""
    return [N - 1 - x for x in range(N)]


def sigma_affine(a, b=0):
    """Affine outer alphabet sigma(x) = (a*x + b) mod 29, a in 1..28, b in 0..28.
    The 29 rotations (a = 1) are the ordinary screen's own D/b freedom (redundant);
    a = 2..27 are genuinely new outer alphabets, and a = 28 with b = 0..28 is the
    family of 29 reflections (Atbash plus a rotation)."""
    if not (1 <= a < N):
        raise ValueError(f"affine multiplier a={a} must be in 1..28")
    b %= N
    return [(a * x + b) % N for x in range(N)]


def keyword_sigma(keyword):
    """Keyword-mixed outer alphabet, standard Vigenere-tableau convention.

    The keyword is uppercased; V->U, K->C, Q->C, Z->S are applied (letters with no
    rune of their own). Each character is then one GP letter via its single-letter
    Latin name; digraphs are never auto-merged ('TRUTH' -> T R U T H, five runes,
    not T R U TH). The mixed alphabet is: keyword letters in first-appearance order,
    then the remaining runes in GP order 0..28.

    Returns sigma with sigma[x] = mixed[x]: a rune at GP index x is written as the
    rune at mixed-alphabet position x (the tableau convention: mixed alphabet under
    the plain alphabet).
    """
    key = []
    for ch in keyword.upper():
        ch = _ALIAS.get(ch, ch)
        if ch not in _SINGLE:
            raise ValueError(
                f"keyword {keyword!r}: character {ch!r} has no single-letter GP rune "
                f"(digraph runes TH EO NG OE AE IA EA are never auto-merged)")
        if _SINGLE[ch] not in key:
            key.append(_SINGLE[ch])
    return key + [i for i in range(N) if i not in key]


def sigma_inverse(sigma):
    """Inverse permutation of sigma (sigma[i] = image of i)."""
    if sorted(sigma) != list(range(N)):
        raise ValueError("sigma is not a permutation of 0..28")
    inv = [0] * N
    for i, v in enumerate(sigma):
        inv[v] = i
    return inv


def relabel_window(cipher_indices, sigma):
    """The front-end transformation: returns sigma_inv applied to every ciphertext
    index. Model c = sigma(p + k); the screen decodes p = c' - k, so feeding it
    c' = sigma_inv(c) makes it see plaintext."""
    inv = sigma_inverse(sigma)
    return [inv[x] for x in cipher_indices]


def parse_sigma(spec):
    if spec == "atbash":
        return sigma_atbash()
    if spec.startswith("kw:"):
        return keyword_sigma(spec[3:])
    if spec.startswith("aff:"):
        parts = spec[4:].split(":")
        a = int(parts[0])
        b = int(parts[1]) if len(parts) > 1 else 0
        return sigma_affine(a, b)
    raise ValueError(f"sigma {spec!r}: use 'atbash', 'kw:<KEYWORD>' or 'aff:<a>[:<b>]'")

def sigma_name(spec):
    return spec.replace(":", "_")


def relabel_windows_file(path, sigma, out_path):
    """Relabel every rune value in a kscreen windows file by sigma_inv.

    Handles W (name, prev) and R (rune list) lines; L lines pass through unchanged.
    P / S / G lines raise: those hypotheses do not commute with an outer relabelling.
    """
    inv = sigma_inverse(sigma)
    with open(path, encoding="utf-8") as f:
        lines = [ln for ln in f.read().splitlines() if ln.strip()]
    out = []
    for line in lines:
        tag, rest = line[0], line[2:]
        if tag == "W":
            parts = rest.split()
            name = parts[0]
            prev = int(parts[1]) if len(parts) > 1 else -1
            prev = inv[prev] if prev >= 0 else -1
            out.append(f"W {name} {prev}")
        elif tag == "R":
            out.append("R " + " ".join(str(inv[int(x)]) for x in rest.split()))
        elif tag == "L":
            out.append(line)
        else:
            raise ValueError(
                f"{path}: {tag}-lines do not commute with an outer relabelling "
                f"(P values are affine combinations of ciphertext runes, G indices "
                f"point into the un-relabelled ciphertext); relabel W/R windows only")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(out) + "\n")


def batch(spec, data_dir=None):
    """Relabel data/segments.txt, heads.txt, pages.txt into data/relabel/<name>/."""
    data_dir = data_dir or os.path.join(HERE, "data")
    sigma = parse_sigma(spec)
    name = sigma_name(spec)
    written = []
    for base in ("segments.txt", "heads.txt", "pages.txt"):
        src = os.path.join(data_dir, base)
        if not os.path.exists(src):
            print(f"batch {spec}: {src} missing, skipped")
            continue
        dst = os.path.join(data_dir, "relabel", name, base)
        relabel_windows_file(src, sigma, dst)
        written.append(dst)
    print(f"batch {spec}: {len(written)} windows relabelled -> data/relabel/{name}/")
    return written


def table_lines(sigma):
    out = [f"{'pos':>3} {'rune':>4} {'latin':>4}  sigma[pos] rune latin"]
    for x in range(N):
        y = sigma[x]
        out.append(f"{x:>3} {lp.GP[x][0]:>4} {lp.LATIN[x]:>4}  {y:>2} {lp.GP[y][0]:>4} {lp.LATIN[y]:>4}")
    return out


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    cmd, args = argv[1], argv[2:]
    if cmd == "table":
        print("\n".join(table_lines(parse_sigma(args[0]))))
    elif cmd == "one":
        spec, src, dst = args
        sigma = parse_sigma(spec)
        relabel_windows_file(src, sigma, dst)
        print(f"{src} -> {dst} (sigma_inv relabelling, sigma {spec})")
    elif cmd == "batch":
        batch(args[0])
    else:
        print(__doc__)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
