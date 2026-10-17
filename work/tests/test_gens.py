"""Key generators of work/phpmt/src/gens.rs (py3, mt32, mt31, java, msvc, drand48, ruby) against independent references:
CPython's own `random` (py3 and Ruby's MT stream), NumPy's legacy MT19937 (mt32), and published first outputs
(Java seed 42, MSVC srand(1), drand48 seed 1). The Python rules below are written from the documented algorithms and share
no code with the Rust."""
import os
import random
import subprocess
import tempfile
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(os.path.dirname(HERE), "phpmt")
_EXE = "phpmt.exe" if os.name == "nt" else "phpmt"
_CAND = [p for p in (os.path.join(PH, "target", "release", _EXE), os.path.join(PH, "target_gen", "release", _EXE))
         if os.path.exists(p)]
BIN = max(_CAND, key=os.path.getmtime) if _CAND else None          # the newest build (older ones ignore the km argument)
K = 160
SEEDS = [0, 1, 2, 42, 12345, 2 ** 31 - 1, 2 ** 31, 2 ** 32 - 2, 2 ** 32 - 1]


def rust_keys(gen, seed, km=29):
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "k.txt")
        subprocess.run([BIN, "keys", gen, str(seed), str(seed + 1), out, str(km)], check=True, capture_output=True)
        with open(out) as f:
            v = [int(x) for x in f.read().split()]
    assert v[0] == seed and len(v) == 1 + 2 * K
    return v[1:1 + K], v[1 + K:]


# ---- references -------------------------------------------------------------------------------------------------

def mt_raw(seed, n, by_array):
    """MT19937 outputs: CPython's random for init_by_array([seed]); NumPy's legacy RandomState for init_genrand(seed)."""
    if by_array:
        random.seed(seed)
        return [random.getrandbits(32) for _ in range(n)]
    return [int(x) for x in np.random.RandomState(seed).randint(0, 2 ** 32, size=n, dtype=np.uint32)]


def res53(y1, y2):
    return ((y1 >> 5) * 67108864.0 + (y2 >> 6)) * (1.0 / 9007199254740992.0)


def py3_keys(seed, km=29):
    random.seed(seed)
    m0 = [random.randrange(km) for _ in range(K)]                      # CPython's own randrange
    random.seed(seed)
    m1 = [int(random.random() * km) for _ in range(K)]                 # Python 2's randrange(km)
    return m0, m1


def ruby_keys(seed, km=29):
    y = mt_raw(seed, 2 * K + 200, True)
    m0, i = [], 0
    while len(m0) < K:
        v = y[i] & 31
        i += 1
        if v < km:
            m0.append(v)
    return m0, [int(res53(y[2 * j], y[2 * j + 1]) * km) for j in range(K)]


def mt32_keys(seed, km=29):
    y = mt_raw(seed, 2 * K + 50, False)
    m0, i = [], 0
    while len(m0) < K:                                                  # Lemire's nearly divisionless draw
        prod = y[i] * km
        i += 1
        if prod & 0xFFFFFFFF < km:
            thr = (2 ** 32 - km) % km
            while prod & 0xFFFFFFFF < thr:
                prod = y[i] * km
                i += 1
        m0.append(prod >> 32)
    return m0, [v % km for v in y[:K]]


def mt31_keys(seed, km=29):
    y = mt_raw(seed, K, False)
    return [(v >> 1) % km for v in y], [int(km * ((v >> 1) / 2147483648.0)) for v in y]


class Java:
    def __init__(self, seed):
        seed = seed - 2 ** 32 if seed >= 2 ** 31 else seed             # Java int, sign-extended to long
        self.s = (seed ^ 0x5DEECE66D) & ((1 << 48) - 1)

    def next(self, bits):
        self.s = (self.s * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        return self.s >> (48 - bits)


def java_keys(seed, km=29):
    r, m0 = Java(seed), []
    while len(m0) < K:
        bits = r.next(31)
        val = bits % km
        while bits - val + km - 1 >= 2 ** 31:                          # int overflow in Java: redraw
            bits = r.next(31)
            val = bits % km
        m0.append(val)
    r, m1 = Java(seed), []
    for _ in range(K):
        d = ((r.next(26) << 27) + r.next(27)) * (1.0 / 9007199254740992.0)
        m1.append(int(d * km))
    return m0, m1


def msvc_stream(seed, n):
    x, out = seed, []
    for _ in range(n):
        x = (x * 214013 + 2531011) & 0xFFFFFFFF
        out.append((x >> 16) & 0x7FFF)
    return out


def msvc_keys(seed, km=29):
    r = msvc_stream(seed, K)
    return [v % km for v in r], [(v * km) // 32768 for v in r]


def drand48_x(seed, n):
    x, out = (seed << 16) | 0x330E, []
    for _ in range(n):
        x = (x * 0x5DEECE66D + 0xB) & ((1 << 48) - 1)
        out.append(x)
    return out


def drand48_keys(seed, km=29):
    xs = drand48_x(seed, K)
    return [int(x / 2.0 ** 48 * km) for x in xs], [(x >> 17) % km for x in xs]


REF = {"py3": py3_keys, "ruby": ruby_keys, "mt32": mt32_keys, "mt31": mt31_keys, "java": java_keys, "msvc": msvc_keys,
       "drand48": drand48_keys}


class References(unittest.TestCase):
    """The Python references themselves, against published first outputs."""

    def test_java_seed_42(self):
        self.assertEqual(Java(42).next(32) - 2 ** 32, -1170105035)     # new Random(42).nextInt()

    def test_msvc_srand_1(self):
        self.assertEqual(msvc_stream(1, 5), [41, 18467, 6334, 26500, 19169])

    def test_drand48_seed_1(self):
        self.assertAlmostEqual(drand48_x(1, 1)[0] / 2.0 ** 48, 0.0416303447718782, places=12)

    def test_mt19937_default_seed(self):
        self.assertEqual(mt_raw(5489, 1, False)[0], 3499211612)        # std::mt19937 default-seeded first output


@unittest.skipUnless(BIN, "build with: cargo build --release (in work/phpmt)")
class RustMatchesReferences(unittest.TestCase):
    def test_every_generator_and_map(self):
        for gen, ref in REF.items():
            for seed in SEEDS:
                r0, r1 = ref(seed)
                k0, k1 = rust_keys(gen, seed)
                self.assertEqual(k0, r0, f"{gen} map 0 seed {seed}")
                self.assertEqual(k1, r1, f"{gen} map 1 seed {seed}")

    def test_every_generator_and_map_with_28_classes(self):
        """the step-domain cipher reduces the generators to 0..27: the same rules with 28 in place of 29"""
        for gen, ref in REF.items():
            for seed in SEEDS:
                r0, r1 = ref(seed, 28)
                k0, k1 = rust_keys(gen, seed, 28)
                self.assertEqual(k0, r0, f"{gen} map 0 seed {seed} km 28")
                self.assertEqual(k1, r1, f"{gen} map 1 seed {seed} km 28")
                self.assertTrue(max(k0 + k1) <= 27)

    def test_keys_are_in_range_and_not_degenerate(self):
        for gen in REF:
            k0, k1 = rust_keys(gen, 7)
            for k in (k0, k1):
                self.assertTrue(all(0 <= v <= 28 for v in k), gen)
                self.assertGreater(len(set(k)), 15, gen)


if __name__ == "__main__":
    unittest.main()
