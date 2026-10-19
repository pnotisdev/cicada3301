"""Fast deterministic suite. No calibration, new seeds, GPU, or LP2 search."""
import os
for x in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[x]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import unittest,json,math
from fractions import Fraction as F
import numpy as np
import reference as dense
from sparse import backward_rational,backward_numpy,state_classes
from engine import all_offsets,MODES
from e0 import run,models,support
from e1 import smoke,compare
from snapshot import hashes


class TestV2(unittest.TestCase):
    def test_exact_full_E0(self):
        self.assertEqual(run()['status'],'PASS')

    def test_rust_tiny_and_extreme_scaling(self):
        self.assertGreater(smoke()['offset_log_gap'],1000)

    def test_coin_two_classes_beyond_tiny_key_limit(self):
        c=(0,0);key=(0,1,0,1)
        self.assertEqual(support(c,key,1,F(3,5),'coin'),2)
        p,L=models()[1]
        b=backward_rational(c,key,1,F(3,5),'coin',p,L)
        self.assertEqual(b,[dense.rational_forward(c,key,o,1,F(3,5),'coin',p,L) for o in range(5)])

    def test_stored_cases_subset(self):
        model=np.load(HERE.parent/'model.npz');pi,L=model['pi'],model['L']
        for stage,index in (('cal',0),('held',1),('held',81),('held',278),('held',288)):
            r=json.loads((HERE.parent/'raw'/stage/f'{index:03d}.json').read_text())
            cell=r['argmax'];ch=cell['channel'];label='m04' if ch=='hold' else ch
            q=json.loads((HERE.parent/'frozen.json').read_text())['q'].get(f"{label}|{r['src']}|{r['kind']}",.81)
            a=all_offsets(r['cipher'],r['bank'][cell['stream']],cell['sign'],q,ch,pi,L)[cell['offset']]
            compare(np.array([a]),np.array([[cell['log_L'],cell['log_U']]]))

    def test_zero_and_positive_model_boundaries(self):
        pi=np.array([1.,0.,0.]);L=np.eye(3)
        for ch in MODES:
            for c,key in (([],[]),([0],[]),([0,1],[0]),([0,1],[0,1,1,0])):
                a=all_offsets(c,key,-1,.81,ch,pi,L)
                b=backward_numpy(c,key,-1,.81,ch,pi,L)
                self.assertTrue(np.allclose(a[:,0],b,atol=1e-9,rtol=0))
        with self.assertRaises(ValueError):all_offsets([0],[0],1,.81,'hold',pi*2,L)

    def test_v1_and_m04_immutable(self):
        old=json.loads((HERE/'v1_m04_snapshot.json').read_text())['files']
        self.assertEqual(old,hashes())

if __name__=='__main__':unittest.main(verbosity=2)
