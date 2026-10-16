"""Ciphertext-feedback screen (work/kscreen/chain_windows.py, chain_selftest.py): the window transform preserves the
collision rule, a = 0 is the ordinary model, and a planted feedback key is found only with the right multiplier."""
import os
import random
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
KS = os.path.join(os.path.dirname(HERE), "kscreen")
sys.path.insert(0, KS)
import chain_selftest as ct  # noqa: E402
import chain_windows as cw  # noqa: E402

BIN = ct.BIN
READY = os.path.exists(BIN) and os.path.exists(os.path.join(KS, "data", "library.ksb"))


class ChainWindows(unittest.TestCase):
    def test_collision_check_is_equivalent(self):
        # "c_i == c_{i-1}" in the real ciphertext  <=>  c'_i == (1-a) c_{i-1}  in the transformed window, for every a
        rng = random.Random(1)
        c = [rng.randrange(29) for _ in range(600)]
        c += [c[-1]] * 3                                  # force some real doublets
        for a in range(29):
            w = cw.chain_window({"name": "x", "prev": -1, "R": c, "P": None}, a)
            self.assertEqual(len(w["R"]), len(c) - 1)     # the first rune has no predecessor
            for i, (cp, pv) in enumerate(zip(w["R"], w["P"])):
                self.assertEqual(cp == pv, c[i + 1] == c[i], (a, i))
                self.assertEqual((cp + a * c[i]) % 29, c[i + 1])          # c' really is c_i - a c_{i-1}

    def test_a_zero_is_the_ordinary_model(self):
        rng = random.Random(2)
        c = [rng.randrange(29) for _ in range(100)]
        w = cw.chain_window({"name": "x", "prev": 7, "R": c, "P": None}, 0)
        self.assertEqual(w["R"], c)
        self.assertEqual(w["P"], [7] + c[:-1])            # the rune before the window is used when it is known

    def test_unknown_predecessor_drops_the_first_rune_only(self):
        w = cw.chain_window({"name": "x", "prev": -1, "R": [5, 6, 7], "P": None}, 1)
        self.assertEqual(w["R"], [1, 1])
        w = cw.chain_window({"name": "x", "prev": 4, "R": [5, 6, 7], "P": None}, 1)
        self.assertEqual(w["R"], [1, 1, 1])


@unittest.skipUnless(READY, "build with: cargo build --release (in work/kscreen) and run work/kscreen/export.py")
class ChainRecovery(unittest.TestCase):
    def test_planted_feedback_key_needs_the_right_multiplier(self):
        import tempfile
        a = 7
        win = ct.plant(a, 47)
        with tempfile.TemporaryDirectory() as d:
            right, wrong = os.path.join(d, "right.txt"), os.path.join(d, "wrong.txt")
            cw.write_windows([cw.chain_window(w, a) for w in win], right)
            cw.write_windows([cw.chain_window(w, 3) for w in win], wrong)
            for name, (ioc, item, off) in ct.screen(right, "file:data/library.ksb", [f"only={ct.ITEM}"], "cpu").items():
                self.assertEqual(item, ct.ITEM, name)
                self.assertGreater(ioc, 1.4, name)
                self.assertLessEqual(abs(off - ct.OFFSET), 6, name)
            top = max(v[0] for v in ct.screen(wrong, "file:data/library.ksb", [f"only={ct.ITEM}"], "cpu").values())
            self.assertLess(top, 1.4)


if __name__ == "__main__":
    unittest.main()
