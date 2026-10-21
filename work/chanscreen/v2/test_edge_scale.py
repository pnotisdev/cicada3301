"""Gate G1b: Q = 29, n = 12-16, key length 30-40, real-size alphabet: Rust sparse classes vs a MEMOISED exact event-tree reference
(explicit previous plaintext and last real rune, no class sets), all four channels, both kinds, long candidate runs."""
import sys,math,random,json,time
sys.dont_write_bytecode=True
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from engine_edge import all_offsets_edge
from reference_edge import prob

def run(seed=3,trials=24):
    rng=random.Random(seed);Q=29;worst=0;nz=0;t0=time.time()
    # smooth rational model: weights 1..3
    def dist():
        w=[rng.randint(1,3) for _ in range(Q)];t=sum(w);return [F(x,t) for x in w]
    pi=dist();L=[dist() for _ in range(Q)]
    ff=lambda x:[float(v) for v in x]
    for t in range(trials):
        n=rng.randint(10,14);m=rng.randint(28,36);ch=('hold','spend','skip5','coin')[t%4];kind=1+(t//4)%2;s=rng.choice((1,-1))
        key=[rng.randrange(Q) for _ in range(m)]
        # a plausible ciphertext: encipher random plaintext with the key then force a few doublets
        c=[(rng.randrange(Q)+s*key[i])%Q for i in range(n)]
        for i in range(1,n):
            if rng.random()<.25:c[i]=c[i-1]
        cand=[1 if rng.random()<.8 else 0 for _ in range(n)]
        q=F(4,5);nu=F(2,5)
        got=all_offsets_edge(c,key,s,float(q),ch,ff(pi),[ff(r) for r in L],kind,cand,float(nu))
        for o in rng.sample(range(m-n),6)+[0]:
            for col,uni in ((0,False),(1,True)):
                z=prob(c,key,o,s,q,ch,pi,L,cand,kind,nu,uniform=uni,memo=True)
                g=got[o,col]
                if z==0:
                    assert g==-math.inf,(t,o,g)
                else:
                    nz+=1;e=abs(g-math.log(z));worst=max(worst,e);assert e<1e-9,(t,ch,kind,o,col,g,math.log(z))
    return dict(trials=trials,nonzero_cells=nz,worst_abs_err=worst,seconds=round(time.time()-t0,1))
if __name__=='__main__':print(json.dumps(run()))
