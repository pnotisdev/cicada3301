"""Small fixed-rule and block-integrity controls; never reads LP2."""
import copy
import importlib.util
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

if "fixed_gate" not in sys.modules:
    spec = importlib.util.spec_from_file_location("fixed_gate", Path(__file__).with_name("gate.py"))
    module = importlib.util.module_from_spec(spec)
    sys.modules["fixed_gate"] = module
    spec.loader.exec_module(module)
import fixed_gate as G


class StubRun:
    def check(self):
        pass

    def log(self, message):
        pass


class FixedTests(unittest.TestCase):
    def test_rules_and_halves_frozen(self):
        self.assertEqual(G.HALVES, {"A": (7, 9, 12, 14), "B": (8, 11, 13, 15)})
        self.assertEqual(G.RULES["T6_raw"], dict(lag=6, a=27, b=24, guarded=False))
        self.assertEqual(G.RULES["I5_raw"], dict(lag=5, a=1, b=0, guarded=False))

    def test_no_selection_called_and_fixed_mc_floor(self):
        c = list(range(14))
        d = dict(sections=[dict(section=s, runes=c, word_lengths=[7, 7], length=14) for s in (7, 8)])
        with patch.object(G.M, "scan", side_effect=AssertionError("Selection forbidden")):
            result = G.fixed_halves(d, StubRun(), 611001, replicates=3)
        for half in result["halves"].values():
            for rule in half.values():
                self.assertEqual(len(rule["null_scores"]), 3)
                self.assertEqual(rule["p_mc"], (1+rule["exceedances"])/4)
                self.assertGreaterEqual(rule["p_mc"], .25)

    def test_conjunction_and_multiplicity(self):
        data = {h: {r: dict(p_mc=.01, score=1.) for r in G.RULES} for h in G.HALVES}
        for value in G.both_claim(data).values():
            self.assertTrue(value["both_halves_flag"])
            self.assertEqual(value["p_adjusted"], .02)
        data["B"]["T6_raw"]["p_mc"] = .026
        self.assertFalse(G.both_claim(data)["T6_raw"]["both_halves_flag"])
        data["B"]["I5_raw"]["score"] = 0.
        self.assertFalse(G.both_claim(data)["I5_raw"]["both_halves_flag"])

    def test_ranges_exactly_cover_original_199_seeds(self):
        seq = [r for b in range(8) for r in G.block_range(b)]
        self.assertEqual(seq, list(range(199)))
        self.assertEqual(len(G.block_range(7)), 24)
        with self.assertRaises(ValueError):
            G.block_range(8)

    def test_merge_positive_and_missing_duplicate_null_controls(self):
        blocks = [dict(block=b, samples=[dict(rep=r, shape=0., fit=0.) for r in G.block_range(b)]) for b in range(8)]
        self.assertEqual(len(G.merge_samples(blocks)), 199)
        missing = copy.deepcopy(blocks)
        missing[3]["samples"].pop()
        with self.assertRaises(ValueError):
            G.merge_samples(missing)
        with self.assertRaises(ValueError):
            G.merge_samples(blocks[:-1]+[blocks[6]])

    def test_section_block_replays_old_generator_and_refits(self):
        # Independent tiny wiring check, same formula as the old monolithic loop.
        s = dict(section=7, word_lengths=[7, 7], length=14, runes=list(range(14)))
        d = dict(sections=[s], c=s["runes"])
        base = G.section_observed(d)
        q = base["rows"][0]["q_raw_moment"]
        c, _ = G.M.collision_plant([0, 1, 2, 3, 4, 5, 6]*2, [14], 6, 1, 3100007, q)
        shape, fit = G.P.heterogeneity(G.P.section_rows(G.P.replace_book(d, c)))
        with patch.object(G, "block_range", return_value=range(1)):
            block = G.section_block(d, base, 0, StubRun())
        self.assertEqual(block["samples"], [dict(rep=0, shape=shape, fit=fit)])


if __name__ == "__main__":
    unittest.main(verbosity=2)
