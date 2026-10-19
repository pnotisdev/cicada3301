"""Deterministic follow-up suite: guard semantics, F4 exact digest, originals unchanged. No Rust DLL, no search."""
import unittest,json,math
import numpy as np
from guard import guarded
from checkpoint import HERE,hashes
import f4


class Tests(unittest.TestCase):
    def test_guard_is_min_of_both_scores_and_rejects_outside_W(self):
        g,out=guarded([-3.,-math.inf],[-5.,-4.],(0,1),.5,3)
        w=-2*math.log(3)+math.log1p(.5/2)
        self.assertFalse(out);self.assertAlmostEqual(g[0],min(2.,-3.-w));self.assertEqual(g[1],-math.inf)
        g,out=guarded([-1.],[-2.],(1,1),1.,3)
        self.assertTrue(out);self.assertEqual(g[0],-math.inf)
        with self.assertRaises(ValueError):guarded([-1.],[-math.inf],(0,1),.5,3)

    def test_f4_exact_m2_reproduces_saved_digest(self):
        self.assertEqual(f4.exact(2),{k:v for k,v in json.loads((HERE/'f4_2.json').read_text()).items() if k!='seconds'})

    def test_f4_reuse_scores_are_min_of_f2_columns(self):
        with np.load(HERE/'f2_scores.npz') as z,np.load(HERE/'f4_guard_scores.npz') as y:
            self.assertTrue(np.array_equal(np.min(z['scores'],axis=2),y['scores']))

    def test_original_files_unchanged(self):
        self.assertEqual(hashes(),json.loads((HERE/'baseline.json').read_text())['files'])

if __name__=='__main__':unittest.main(verbosity=2)
