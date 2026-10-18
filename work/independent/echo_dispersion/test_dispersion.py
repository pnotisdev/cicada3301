"""Independent small enumerations, matching marginals and dispersion wiring."""
from fractions import Fraction as F
import importlib.util
import itertools
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

import numpy as np

if "dispersion_gate" not in sys.modules:
    spec = importlib.util.spec_from_file_location("dispersion_gate", Path(__file__).with_name("gate.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["dispersion_gate"] = module
    spec.loader.exec_module(module)
import dispersion_gate as G


class DispersionTests(unittest.TestCase):
    def test_conditioning_against_exact_subset_enumeration(self):
        p = [F(1, 5), F(2, 5), F(3, 5), F(7, 10)]
        subsets = []
        for bits in itertools.product((0, 1), repeat=4):
            if sum(bits) != 2:
                continue
            weight = F(1)
            for a, bit in zip(p, bits):
                weight *= a if bit else 1-a
            subsets.append((bits, weight))
        z = sum(w for _, w in subsets)
        sampler = G.ConditionalBernoulli(list(map(float, p)), 2)
        self.assertAlmostEqual(sampler.total_probability, float(z), places=13)
        expected = [sum(w for bits, w in subsets if bits[i])/z for i in range(4)]
        np.testing.assert_allclose(sampler.marginal, list(map(float, expected)), atol=1e-13)
        for bits, weight in subsets:
            likelihood, remaining = 1., 2
            for i, bit in enumerate(bits):
                chance = (sampler.p[i]*sampler.suffix[i+1, remaining-1]/sampler.suffix[i, remaining]) if remaining else 0.
                likelihood *= chance if bit else 1-chance
                remaining -= bit
            self.assertAlmostEqual(likelihood, float(weight/z), places=13)

    def test_equal_rates_fixed_count_and_reproducibility(self):
        sampler = G.ConditionalBernoulli([.2]*30, 7)
        np.testing.assert_allclose(sampler.marginal, [7/30]*30, atol=1e-13)
        for seed in range(40):
            draw = sampler.draw(seed)
            self.assertEqual(int(draw.sum()), 7)
            np.testing.assert_array_equal(draw, sampler.draw(seed))

    def test_even_systematic_sampling_matches_marginals(self):
        sampler = G.ConditionalBernoulli(np.linspace(.1, .6, 20), 4)
        tally = np.zeros(20)
        for i in range(1000):
            with patch.object(G.random, "Random") as rng:
                rng.return_value.random.return_value = (i+.5)/1000
                mask = sampler.evenly_spaced(0)
            self.assertEqual(int(mask.sum()), 4)
            tally += mask
        np.testing.assert_allclose(tally/1000, sampler.marginal, atol=.0011)

    def test_hundred_bins_reset_and_keep_short_tails(self):
        sampler = G.ConditionalBernoulli([.1]*270, 20)
        model = G.Dispersion(sampler, [7]*125+[8]*145)
        self.assertEqual([len(g) for g in model.bins], [100, 25, 100, 45])
        self.assertAlmostEqual(float(model.bin_means.sum()), 20, places=10)
        self.assertEqual(model.bins[2][0], 125)
        with self.assertRaises(ValueError):
            model.statistics(np.zeros(270, dtype=bool))

    def test_regular_gaps_and_clustered_counts_wiring(self):
        sampler = G.ConditionalBernoulli([.05]*400, 20)
        model = G.Dispersion(sampler, [7]*100+[8]*100+[9]*100+[11]*100)
        even = np.zeros(400, dtype=bool)
        uneven = even.copy()
        for start in (0, 100, 200, 300):
            even[start+np.asarray([5, 25, 45, 65, 85])] = True
            uneven[start+np.asarray([0, 1, 2, 30, 90])] = True
        self.assertLess(model.statistics(even)[2], 1e-20)
        self.assertGreater(model.statistics(uneven)[2], .5)
        concentrated = np.zeros(400, dtype=bool); concentrated[:20] = True
        self.assertGreater(model.statistics(concentrated)[0], model.statistics(even)[0]+10)

    def test_tail_direction_ties_and_three_scale_penalty(self):
        reference = np.repeat(np.arange(1, 1000, dtype=float)[:, None], 3, axis=1)
        plant = G.assess([0, 0, 0], reference)
        self.assertEqual(plant["p_omnibus"], .003)
        self.assertTrue(plant["flag"])
        null = G.assess([999, 999, 999], reference)
        self.assertEqual(null["p_omnibus"], 1.)
        self.assertFalse(null["flag"])
        ties = G.assess([1, 1, 1], np.ones((999, 3)))
        self.assertEqual(ties["p_lower"], dict.fromkeys(G.NAMES, 1.))

    def test_invalid_inputs(self):
        with self.assertRaises(ValueError):
            G.ConditionalBernoulli([.2, .4], 0)
        with self.assertRaises(ValueError):
            G.ConditionalBernoulli([.2, 1.], 1)
        with self.assertRaises(ValueError):
            G.Dispersion(G.ConditionalBernoulli([.1]*10, 2), [8]*5+[7]*5)


if __name__ == "__main__":
    unittest.main(verbosity=2)
