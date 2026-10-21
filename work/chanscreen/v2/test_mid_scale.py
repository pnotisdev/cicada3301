"""Gate G1b for the mid-word arc: Q = 29, n = 10-14, key 28-36, memoised exact reference (explicit previous plaintext and last real rune), 4 channels, word lengths 3-7."""
import sys,math,random,json,time
sys.dont_write_bytecode=True
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from engine_mid import all_offsets_mid
from reference_mid import prob


def run(seed=3,trials=24):
    rng=random.Random(seed);Q=29;worst=0;nz=0;t0=time.time()
    def dist():
        w=[rng.randint(1,3) for _ in range(Q)];t=sum(w);return [F(x,t) for x in w]
    pi=dist();L=[dist() for _ in range(Q)]
    ff=lambda x:[float(v) for v in x]
    for t in range(trials):
        n=rng.randint(10,14);m=rng.randint(28,36);ch=('hold','spend','skip5','coin')[t%4];s=rng.choice((1,-1))
        key=[rng.randrange(Q) for _ in range(m)]
        c=[(rng.randrange(Q)+s*key[i])%Q for i in range(n)]
        for i in range(1,n):
            if rng.random()<.25:c[i]=c[i-1]
        ws=[1]+[0]*(n-1);i=0
        while True:
            i+=rng.randint(3,7)
            if i>=n:break
            ws[i]=1
        q=F(4,5);nu=F(2,5)
        got=all_offsets_mid(c,key,s,float(q),ch,ff(pi),[ff(r) for r in L],3,None,float(nu),ws)
        for o in rng.sample(range(m-n),6)+[0]:
            for col,uni in ((0,False),(1,True)):
                z=prob(c,key,o,s,q,ch,pi,L,ws,nu,uniform=uni)
                g=got[o,col]
                if z==0:
                    assert g==-math.inf,(t,o,g)
                else:
                    nz+=1;e=abs(g-math.log(z));worst=max(worst,e);assert e<1e-9,(t,ch,o,col,g,math.log(z))
    return dict(trials=trials,nonzero_cells=nz,worst_abs_err=worst,seconds=round(time.time()-t0,1))
if __name__=='__main__':print(json.dumps(run()))
