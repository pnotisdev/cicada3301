"""Unit tests and an engine smoke test for the M04 harness (python -m unittest work/m04/test_m04.py from the repository root)."""
import os
import random
import tempfile
import unittest

import m04 as M

PLAIN = M.english_pool(0.0, 0.01)[:300]


def key(rng, n=M.SLICE):
    return bytes(rng.randrange(M.Q) for _ in range(n))


class Channels(unittest.TestCase):
    def test_zero_repair_probability_is_the_additive_cipher(self):
        rng = random.Random(1)
        k = key(rng)
        base = M.enc_additive(PLAIN, k, 3)[0]
        self.assertEqual(M.enc_m04(PLAIN, k, 3, 0.0, rng)[0], base)
        self.assertEqual(M.enc_spend(PLAIN, k, 3, 0.0, rng)[0], base)

    def test_full_repair_never_leaves_a_doublet(self):
        for seed in range(20):
            rng = random.Random(seed)
            k = key(rng)
            for enc in (M.enc_m04, M.enc_spend):
                out = enc(PLAIN, k, 0, 1.0, rng)[0]
                self.assertEqual(M.doublets(out), 0)

    def test_hold_keeps_and_spend_advances_the_key_position(self):
        rng = random.Random(7)
        k = key(rng)
        for seed in range(30):
            rng = random.Random(seed)
            out, used, rep = M.enc_m04(PLAIN, k, 0, 1.0, rng)
            self.assertTrue(any(rep))
            for i in range(1, len(out)):
                if rep[i - 1]:
                    self.assertEqual(used[i], used[i - 1])       # held: the next output uses the same key index
            out, used, rep = M.enc_spend(PLAIN, k, 0, 1.0, random.Random(seed))
            for i in range(1, len(out)):
                if rep[i - 1]:
                    self.assertEqual(used[i], used[i - 1] + 1)   # spent

    def test_held_key_reveals_the_plaintext_difference(self):
        """after a repair at i: the next attempt is c_(i-1) + (p_(i+1) - p_i)"""
        rng = random.Random(3)
        k = key(rng)
        hits = 0
        for seed in range(60):
            out, used, rep = M.enc_m04(PLAIN, k, 0, 1.0, random.Random(seed))
            for i in range(1, len(out) - 1):
                if rep[i] and not rep[i + 1] and used[i + 1] == used[i]:
                    self.assertEqual(out[i + 1], (out[i - 1] + PLAIN[i + 1] - PLAIN[i]) % M.Q)
                    hits += 1
        self.assertGreater(hits, 20)

    def test_iid_doublet_rate_is_one_over_29_times_one_minus_q(self):
        rng = random.Random(11)
        q = 0.8074
        for enc in (M.enc_m04, M.enc_spend):
            d = t = 0
            for _ in range(400):
                out = enc(PLAIN, key(rng), 0, q, rng)[0]
                d += M.doublets(out)
                t += len(out) - 1
            self.assertAlmostEqual(d / t, (1 - q) / 29, delta=0.0018)

    def test_skip_and_coin_without_survivors_leave_few_doublets(self):
        rng = random.Random(5)
        d = t = 0
        for _ in range(100):
            out = M.enc_skip(PLAIN, key(rng), 0, rng, keep=0.0)[0]
            d += M.doublets(out)
            t += len(out) - 1
        self.assertLess(d / t, 0.0005)                           # only the five-try cap can leave one
        d = 0
        for _ in range(100):
            d += M.doublets(M.enc_coin(PLAIN, key(rng), 0, rng, keep=0.0)[0])
        self.assertLess(d / t, 0.0075)                           # coin spends a key value, then redraws once: a fresh collision can remain


class Streams(unittest.TestCase):
    def test_ksb_round_trip(self):
        streams = [("a", bytes(range(29))), ("b c", bytes([5] * 400))]
        with tempfile.TemporaryDirectory() as d:
            p = os.path.join(d, "x.ksb")
            M.write_ksb(p, streams)
            self.assertEqual(M.read_ksb(p), streams)

    def test_library_reads_and_slices(self):
        self.assertGreater(len(M.library()), 500)
        name, s = M.draw_stream(random.Random(1), "lib")
        self.assertEqual(len(s), M.SLICE)

    def test_period_detection(self):
        self.assertEqual(M.period_of(bytes([3] * 50)), 1)
        self.assertEqual(M.period_of(bytes([1, 2, 3] * 20)), 3)
        rng = random.Random(2)
        self.assertEqual(M.period_of(bytes(rng.randrange(29) for _ in range(200))), 0)


@unittest.skipUnless(os.path.exists(M.BIN), "kscreen is not built")
class EngineSmoke(unittest.TestCase):
    def test_skip_plant_is_recovered_by_the_unchanged_engine_and_the_search_has_512_cells(self):
        rng = random.Random(21)
        with tempfile.TemporaryDirectory() as d:
            streams = [M.draw_stream(rng, "iid") for _ in range(8)]
            names = [f"k{i}" for i in range(8)]
            true, off = 3, 5
            out, used, _ = M.enc_skip(PLAIN, streams[true][1], off, rng)
            M.write_ksb(os.path.join(d, "b.ksb"), [(n, s[1]) for n, s in zip(names, streams)])
            M.write_window(os.path.join(d, "w.txt"), "p0", out)
            best, rows = M.screen(os.path.join(d, "w.txt"), os.path.join(d, "b.ksb"), os.path.join(d, "o.tsv"))
            self.assertGreater(best, 1.5)
            top = max(rows)
            self.assertEqual((top[1], top[2], top[3], top[4]), ("k3", 5, 1, 0))
            ioc, plain, ptr = M.verify(os.path.join(d, "w.txt"), os.path.join(d, "b.ksb"), "k3", 5, 1, 0, "p0")
            self.assertGreater(sum(a == b for a, b in zip(plain, PLAIN)) / len(PLAIN), 0.95)


if __name__ == "__main__":
    unittest.main()
