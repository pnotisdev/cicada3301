"""Reproducible suite (<5 min); does not rerun any held-out seeds."""
import os
for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[v]='1'
import math
import unittest
from fractions import Fraction as F
import itertools
import numpy as np
import gates
import reference as R
from reconstruct import viterbi
import cpu


class Tests(unittest.TestCase):
    def test_g0_exhaustive(self):
        self.assertEqual(gates.g0()['status'],'PASS')

    def test_g1_exhaustive(self):
        self.assertEqual(gates.g1()['status'],'PASS')

    def test_cpu_parity(self):
        from check_cpu import check
        self.assertEqual(check()['status'],'PASS')

    def test_long_branching_numeric(self):
        rng=np.random.default_rng(1710)
        pi=np.full(29,1/29);L=rng.random((29,29));L/=L.sum(1,keepdims=True)
        for n in (300,600):
            key=rng.integers(29,size=n+20).tolist()
            c=rng.integers(29,size=n).tolist()
            for ch in ('hold','spend','skip5','coin'):
                a=R.forward(c,key,0,-1,.81,ch,pi,L)
                b=cpu.forward(c,key,0,-1,.81,ch,pi,L)
                self.assertAlmostEqual(a,b,places=9)

    def test_viterbi_tiny_exhaustive(self):
        # Independent maximum over plaintext sequences and every channel path.
        pi=np.array([1,2,3])/6.;L=np.array([[1,2,3],[3,1,2],[2,3,1]])/6.
        key=[0,1,1,2]
        for ch in gates.CHANNELS:
            for c in itertools.product(range(3),repeat=3):
                paths=[(0,-1,0.,[])]
                for i,y in enumerate(c):
                    nxt=[]
                    for j,r,v,pp in paths:
                        for p in range(3):
                            for out,h,w in R.arcs(key,j,p,c[i-1] if i else None,-1,.6,3,ch):
                                if out==y and w:
                                    nxt.append((h,p,v+math.log((pi if r<0 else L[r])[p])+math.log(w),pp+[p]))
                    paths=nxt
                expected=max((x[2] for x in paths),default=-math.inf)
                pp,_,v=viterbi(c,key,0,-1,.6,ch,pi,L)
                self.assertAlmostEqual(v,expected,places=12)
                if paths:self.assertTrue(any(x[3]==pp and abs(x[2]-expected)<1e-12 for x in paths))
                summed=R.forward(c,key,0,-1,.6,ch,pi,L)
                self.assertLessEqual(v,summed+1e-12)

    def test_bytes_key_adapter(self):
        pi=np.full(3,1/3);L=np.full((3,3),1/3)
        for key in (bytes([0,1,2,1]), bytearray([0,1,2,1])):
            for ch in gates.CHANNELS:
                a=cpu.forward([0,1,0],key,0,1,.81,ch,pi,L)
                b=cpu.forward([0,1,0],list(key),0,1,.81,ch,pi,L)
                self.assertEqual(a.hex(),b.hex())

    def test_invalid_support_and_model(self):
        pi=np.full(3,1/3);L=np.full((3,3),1/3)
        self.assertIsNone(R.score([0],[],0,1,.8,'hold',pi,L)['score'])
        self.assertEqual(R.score([],[],0,1,.8,'hold',pi,L)['score'],0.)
        with self.assertRaises(ValueError):R.forward([0],[0],0,1,.8,'extension',pi,L)
        with self.assertRaises(ValueError):R.forward([0],[0],0,1,.8,'hold',pi*2,L)


if __name__=='__main__':unittest.main(verbosity=2)
