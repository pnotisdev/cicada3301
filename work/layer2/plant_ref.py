"""Independent planter for the layer2 controls: the two-layer cipher of H-LAYER written in Python, so that the engine's own `plant`
mode is not what the screen is tested against (review of research/new-hypotheses, docs/prs/new-hypotheses.md).

    inner:  q = D(p) + isign * K[phase]    (D = Atbash if atb; a literal F (p = 0) is written as F and does not advance the phase)
    outer:  c = q + mult * S_j             (the anti-repeat rule: model 0 re-draws up to 5 times, model 1 spends one key value as a coin,
                                            each with probability 1 - keep per collision)

The stream values S come from the keystream file (a KSB written by work/kscreen/export.py and work/layer2/export.py), the window
offsets follow the engine's plant convention (offset + 997 * window index, modulo the room the stream leaves), and the file has the same
'# truth' lines, so selftest.py and the unit tests read it the same way.
"""
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from export import read_ksb  # noqa: E402

Q = 29


def stream(ksb_path, item):
    for name, v in read_ksb(ksb_path):
        if name == item:
            return list(v)
    raise KeyError(item)


def plant(plain_path, ksb_path, item, off0, mult, model, keep, coin_seed, kw, phase, isign, litf, atb):
    """returns the windows file text of the planted ciphertext"""
    s = stream(ksb_path, item)
    rng = random.Random(coin_seed)
    with open(plain_path, encoding="utf-8") as f:
        lines = f.read().splitlines()
    out, wi, m = [], 0, len(kw)
    for i, line in enumerate(lines):
        if not line.startswith("W "):
            continue
        runes = [int(x) for x in lines[i + 1][2:].split()]
        lens = lines[i + 2][2:] if i + 2 < len(lines) and lines[i + 2].startswith("L ") else ""
        need = len(runes) * 4 + 64
        noff = len(s) + 1 - need
        assert noff > 0, "keystream too short to plant"
        off = (off0 + 997 * wi) % noff
        mk = [v * mult % Q for v in s[off:off + need]]
        j, ph, prev, c = 0, phase % m, -1, []
        for p in runes:
            if litf and p == 0:
                q = 0
            else:
                x = Q - 1 - p if atb else p
                q = (x + isign * kw[ph]) % Q
                ph = (ph + 1) % m
            y = (q + mk[j]) % Q
            j += 1
            if model == 0:
                tries = 0
                while prev >= 0 and y == prev and rng.random() >= keep and tries < 5:
                    y = (q + mk[j]) % Q
                    j += 1
                    tries += 1
            elif prev >= 0 and y == prev:
                j += 1                                   # the coin value
                if rng.random() >= keep:
                    y = (q + mk[j]) % Q
                    j += 1
            c.append(y)
            prev = y
        out += [f"# truth plant_{wi} item={item} offset={off} mult={mult} model={model} keep={keep} kw={','.join(map(str, kw))} "
                f"phase={phase} isign={isign} litf={int(litf)} atb={int(atb)} (planted by plant_ref.py)",
                f"W plant_{wi} -1", "R " + " ".join(map(str, c)), "L " + lens]
        wi += 1
    return "\n".join(out) + "\n"
