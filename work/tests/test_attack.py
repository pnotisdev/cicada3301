"""Phase 4: collision-skip decoder and fast keystream screen."""
import os
import random
import sys
import unittest

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

import attack  # noqa: E402
import lp  # noqa: E402

PRIMES = lp.primes(5000)
TOTIENT = lambda j: PRIMES[j] - 1  # noqa: E731


class CollisionSkipDecoder(unittest.TestCase):
    pt = attack.synthetic_tokens(800)
    truth = lp.runes_of(pt)

    def _check(self, keyfn, sign, atbash, min_acc=0.98):
        skips = []
        enc = attack.encrypt_tokens(self.pt, keyfn, q=0.8, sign=sign, atbash=atbash, seed=1, skips_out=skips)
        T = attack.Text(enc)
        self.assertGreater(len(skips), 5)  # the rule actually fired
        plain, found, _ = attack.decode(T, keyfn, sign=sign, atbash=atbash)
        acc = sum(a == b for a, b in zip(plain, self.truth)) / len(self.truth)
        self.assertGreaterEqual(acc, min_acc)

    def test_totient_key(self):
        self._check(TOTIENT, 1, False)

    def test_keyword_key_atbash_minus(self):
        kw = lp.word_to_key("DIVINITY")
        self._check(lambda j: kw[j % len(kw)], -1, True)

    def test_random_key_with_double_skips(self):
        R = random.Random(5)
        r = [R.randrange(29) for _ in range(5000)]
        self._check(lambda j: r[j], 1, False)

    def test_wrong_key_scores_low(self):
        enc = attack.encrypt_tokens(self.pt, TOTIENT, q=0.8, seed=1)
        _, _, sc = attack.decode(attack.Text(enc), lambda j: PRIMES[j] + 3)
        self.assertLess(sc, 0.2)


class FastScreen(unittest.TestCase):
    def test_planted_key_and_shift_found(self):
        pt = attack.synthetic_tokens(300, start=20000)
        ks = np.array([p - 1 for p in PRIMES], dtype=np.int64) % 29
        enc = attack.encrypt_tokens(pt, lambda j: int(ks[500 + j]) + 11, q=0.8, sign=-1, atbash=True, seed=4)
        T = attack.Text(enc)
        s = attack.fast_screen(np.array(T.c), T.words, ks[500:], -1, True)
        self.assertEqual(int(s.argmax()), 11)
        self.assertGreater(s.max(), 0.45)
        R = random.Random(3)
        noise = attack.fast_screen(np.array(T.c), T.words, np.array([R.randrange(29) for _ in range(400)]), -1, True)
        self.assertLess(noise.max(), 0.25)



class SlidingScreen(unittest.TestCase):
    def test_batch_finds_planted_offset(self):
        ks = np.array([p - 1 for p in PRIMES], dtype=np.int64) % 29
        pt = attack.synthetic_tokens(300, start=30000)
        enc = attack.encrypt_tokens(pt, lambda j: int(ks[1501 + j]) + 19, q=0.8, sign=-1, seed=8)
        T = attack.Text(enc)
        offs = np.arange(1200, 1900, attack.STEP)
        S = attack.fast_screen_batch(np.array(T.c), T.words, ks, offs, -1, False)
        o, b = np.unravel_index(S.argmax(), S.shape)
        self.assertTrue(offs[o] <= 1501 < offs[o] + 24)
        self.assertEqual(b, 19)
        self.assertGreater(S.max(), 0.45)
        self.assertLess(np.sort(S.max(axis=1))[-4], 0.25)  # neighbouring windows aside, the rest is noise


if __name__ == "__main__":
    unittest.main()
