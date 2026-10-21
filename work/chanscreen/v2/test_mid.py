"""Gate G1 for the mid-word arc: Rust backward_mid (kind 3) vs the dense reference on tiny random cases, plus wrong-reading mutants."""
import sys,math,random,json
sys.dont_write_bytecode=True
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from engine_mid import all_offsets_mid
from reference_mid import all_offsets_ref
from test_edge import rmodel
ff=lambda x:[float(v) for v in x]


def case(rng,nmax,mmax,Qs=(3,4)):
    Q=rng.choice(Qs);n=rng.randint(1,nmax);m=rng.randint(1,mmax)
    c=[rng.randrange(Q) for _ in range(n)]
    for i in range(1,n):
        if rng.random()<.4:c[i]=c[i-1]
    key=[rng.randrange(Q) for _ in range(m)]
    ws=[1]+[1 if rng.random()<.25 else 0 for _ in range(n-1)]    # long words: interior slots and runs of them
    return Q,n,m,c,key,ws


def run(seed=7,trials=300,nmax=6,mmax=8):
    rng=random.Random(seed);worst=0.;nz=0;byc={}
    for t in range(trials):
        Q,n,m,c,key,ws=case(rng,nmax,mmax)
        ch=rng.choice(('hold','spend','skip5','coin'));s=rng.choice((1,-1))
        q=rng.choice((F(0),F(3,5),F(1),F(4,5)));nu=rng.choice((F(0),F(2,5),F(1),F(2,5)))
        pi,L=rmodel(rng,Q)
        ref=all_offsets_ref(c,key,s,q,ch,pi,L,ws,nu)
        got=all_offsets_mid(c,key,s,float(q),ch,ff(pi),[ff(r) for r in L],3,None,float(nu),ws)
        for o,(zl,zu) in enumerate(ref):
            for col,z in ((0,zl),(1,zu)):
                g=got[o,col]
                if z==0:
                    if g!=-math.inf:raise AssertionError(f'support mismatch trial {t} {ch} o={o} col={col} got={g}')
                else:
                    nz+=1;e=abs(g-math.log(z));worst=max(worst,e)
                    if e>1e-9:raise AssertionError(f'trial {t} {ch} s={s} q={q} nu={nu} c={c} key={key} ws={ws} o={o} col={col}: got {g} ref {math.log(z)}')
        byc[ch]=byc.get(ch,0)+1
    return dict(trials=trials,nonzero_cells=nz,worst_abs_err=worst,by_channel=byc)


def mutants(seed=11,trials=250):
    rng=random.Random(seed);found={m:0 for m in ('null_visible','null_keyed')}
    for t in range(trials):
        Q,n,m,c,key,ws=case(rng,6,7,(3,))
        ch=rng.choice(('hold','spend','skip5','coin'));s=rng.choice((1,-1));q=F(4,5);nu=F(2,5)
        pi,L=rmodel(rng,Q)
        got=all_offsets_mid(c,key,s,float(q),ch,ff(pi),[ff(r) for r in L],3,None,float(nu),ws)
        for mu in found:
            ref=all_offsets_ref(c,key,s,q,ch,pi,L,ws,nu,mutant=mu)
            for o,(zl,zu) in enumerate(ref):
                g=got[o,0]
                if (zl==0)!=(g==-math.inf) or (zl!=0 and abs(g-math.log(zl))>1e-9):found[mu]+=1;break
    return found


if __name__=='__main__':
    print(json.dumps(run(),indent=1));print('mutant witnesses:',mutants())
