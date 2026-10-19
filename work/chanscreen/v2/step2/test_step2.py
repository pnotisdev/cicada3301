"""Deterministic regression suite. Expected theorem counterexamples stay failures
of E3', even though tests that preserve their existence pass. No search or GPU.
"""
import unittest,json
from pathlib import Path
from fractions import Fraction as F
from bounds import matched_grid,small_counterexample,long_event,key_dependence
from freeze import make
from snapshot import inventory
HERE=Path(__file__).resolve().parent


class Tests(unittest.TestCase):
    def test_cell_matched_exact_bound_full_tiny_grid(self):
        r=matched_grid()
        self.assertEqual(r['status'],'PASS')
        self.assertEqual(r['output_comparisons'],340800)

    def test_small_common_null_counterexample_preserved(self):
        r=small_counterexample()
        self.assertEqual(F(r['tail_U_cell']),F(13,450))
        self.assertEqual(F(r['tail_W']),F(169,1350))
        self.assertTrue(r['own_bound_pass'])
        self.assertFalse(r['common_bound_pass'])

    def test_Q29_campaign_threshold_counterexample(self):
        R=json.loads((HERE/'thresholds.json').read_text())['inventory']['300']['LR_threshold_integer']
        r=long_event(29,26,3,300,F(81,100),R)
        self.assertTrue(r['common_bound_refuted'])
        self.assertGreater(r['W_over_bound'],2)

    def test_do_not_claim_Q3_n600_refutes_this_threshold(self):
        R=json.loads((HERE/'thresholds.json').read_text())['inventory']['600']['LR_threshold_integer']
        r=long_event(3,2,1,600,F(81,100),R)
        self.assertTrue(r['above_campaign_threshold'])
        self.assertFalse(r['common_bound_refuted'])

    def test_skip_coin_gap_is_measured_not_assumed(self):
        r=key_dependence()
        self.assertEqual([x['TV_between_keys'] for x in r if 'TV_between_keys' in x],['1/5','1/5'])

    def test_frozen_inventory_and_original_files(self):
        self.assertEqual(make(),json.loads((HERE/'thresholds.json').read_text()))
        self.assertEqual(inventory(),json.loads((HERE/'baseline_sha256.json').read_text())['files'])

if __name__=='__main__':unittest.main(verbosity=2)
