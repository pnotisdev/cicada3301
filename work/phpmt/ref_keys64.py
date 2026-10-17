"""Independent reference key streams for the 64-bit seed sweeps (bg64.py), written from the generators' specifications and CPython's own `random`, not from
the CUDA kernel or the Rust engines; and the planter used by the gates (the encryption rule of the Rust `plant` mode, ported).

    py3       CPython random.Random(n): randrange(29) | int(random() * 29)
    ruby      Ruby Random.new(n): MT19937 seeded with the 32-bit words of n as CPython does; rand(29) = low 5 bits of an output, rejecting 29..31 | rand = res53 float.
              (No Ruby is available here: this is the documented rule on top of CPython's MT19937, not a Ruby run.)
    java      java.util.Random(seed) from the specification: nextInt(29) with its rejection | (int)(nextDouble() * 29)
    java-abs  java.util.Random: nextInt(29) | abs(nextInt()) % 29 (a wrapping abs, unsigned %, as prngx does)
A seed below 2^32 is a Java INT (sign-extended: 2^31..2^32-1 are negative), as in the 32-bit engines; a larger seed is a long.
"""
import os
import random

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
K = 160
M48 = (1 << 48) - 1


class JavaRandom:
    def __init__(self, seed):
        self.s = (seed ^ 0x5DEECE66D) & M48

    def next(self, bits):
        self.s = (self.s * 0x5DEECE66D + 0xB) & M48
        r = self.s >> (48 - bits)
        return r - (1 << 32) if (bits == 32 and r >= 1 << 31) else r

    def next_int(self, bound=None):
        if bound is None:
            return self.next(32)
        while True:
            bits = self.next(31)
            val = bits % bound
            if bits - val + (bound - 1) < 1 << 31:
                return val

    def next_double(self):
        return ((self.next(26) << 27) + self.next(27)) * 2.0 ** -53


def _java_seed(seed):
    return seed - (1 << 32) if (1 << 31) <= seed < (1 << 32) else seed


def keys(gen, seed, n=K):
    """[map 0 values, map 1 values] of the generator for one seed"""
    if gen in ("py3", "ruby"):
        r = random.Random(seed)
        if gen == "py3":
            m0 = [r.randrange(29) for _ in range(n)]
        else:
            m0 = []
            while len(m0) < n:
                y = r.getrandbits(32) & 31
                if y <= 28:
                    m0.append(y)
        r = random.Random(seed)
        m1 = [int(r.random() * 29) for _ in range(n)]
    elif gen in ("java", "java-abs"):
        j = JavaRandom(_java_seed(seed))
        m0 = [j.next_int(29) for _ in range(n)]
        j = JavaRandom(_java_seed(seed))
        if gen == "java":
            m1 = [int(j.next_double() * 29) for _ in range(n)]
        else:
            m1 = []
            for _ in range(n):
                v = j.next_int()
                m1.append(((-v if v < 0 else v) & 0xFFFFFFFF) % 29)
    else:
        raise ValueError(gen)
    return [np.array(m0), np.array(m1)]


def english_runes(n=120):
    """the first n runes of the English window of data/english.txt (the plaintext of the planted tests)"""
    with open(os.path.join(HERE, "data", "english.txt"), encoding="utf-8") as f:
        lines = f.read().splitlines()
    return np.array([int(x) for x in lines[1][2:].split()][:n])


def plant(gen, seed, mp, model, sign, atb, keep=0.18, n=120):
    """English enciphered under the seed's key stream (map mp) with the skip (model 0) or coin (model 1) anti-repeat rule: the first n cipher runes.
    The rule of the Rust `plant` mode: y = t + sign * key (t = 28 - p with Atbash); a repeat is redrawn, with probability 1 - keep."""
    stream = [int(x) for x in keys(gen, seed, 4 * n + 64)[mp]]
    lcg = 0x2545F4914F6CDD1D ^ (seed & (2 ** 64 - 1))
    pos = [0]

    def coin():
        nonlocal lcg
        lcg = (lcg * 6364136223846793005 + 1442695040888963407) & (2 ** 64 - 1)
        return (lcg >> 11) / float(1 << 53)

    def draw():
        pos[0] += 1
        return stream[pos[0] - 1]

    prev, out = -1, []
    for p in english_runes(n):
        t = 28 - int(p) if atb else int(p)
        y = (t + sign * draw()) % 29
        if model == 0:
            tries = 0
            while prev >= 0 and y == prev and coin() >= keep and tries < 5:
                y = (t + sign * draw()) % 29
                tries += 1
        elif prev >= 0 and y == prev:
            c100 = draw() * (100.0 / 29.0)                    # the coin spends one key value
            if c100 >= keep * 100.0:
                y = (t + sign * draw()) % 29
        out.append(y)
        prev = y
    return np.array(out)
