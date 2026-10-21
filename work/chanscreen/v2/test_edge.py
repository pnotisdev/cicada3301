"""Gate G1 for the word-edge arc: Rust backward_edge vs the exact generative reference on tiny cases (random, seeded)."""
import os,sys,math,random,json
sys.dont_write_bytecode=True
from pathlib import Path
from fractions import Fraction as F
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE));sys.path.insert(0,str(HERE.parent))
import numpy as np
from engine_edge import all_offsets_edge
from reference_edge import all_offsets_ref


def rmodel(rng,Q):
    def dist():
        w=[rng.randint(1,5) for _ in range(Q)];t=sum(w);return [F(x,t) for x in w]
    return dist(),[dist() for _ in range(Q)]


def run(seed=7,trials=400):
    rng=random.Random(seed);worst=0.;cnt=0;nz=0;byk={}
    for t in range(trials):
        Q=rng.choice((3,4));n=rng.randint(1,5);m=rng.randint(1,8)
        ch=rng.choice(('hold','spend','skip5','coin'));kind=rng.choice((0,1,1,2,2));s=rng.choice((1,-1))
        q=rng.choice((F(0),F(3,5),F(1),F(4,5)));nu=rng.choice((F(0),F(2,5),F(1),F(2,5)))
        c=[rng.randrange(Q) for _ in range(n)]
        if rng.random()<.5:                      # make doublets and runs likely
            for i in range(1,n):
                if rng.random()<.4:c[i]=c[i-1]
        key=[rng.randrange(Q) for _ in range(m)]
        cand=[1 if rng.random()<.6 else 0 for _ in range(n)]
        pi,L=rmodel(rng,Q)
        ref=all_offsets_ref(c,key,s,q,ch,pi,L,cand,kind,nu)
        got=all_offsets_edge(c,key,s,float(q),ch,[float(x) for x in pi],[[float(x) for x in r] for r in L],kind,cand,float(nu))
        for o,(zl,zu) in enumerate(ref):
            for col,z in ((0,zl),(1,zu)):
                g=got[o,col]
                if z==0:
                    if g!=-math.inf:raise AssertionError(f'support mismatch trial {t} {ch} kind={kind} o={o} col={col} got={g}')
                else:
                    nz+=1
                    e=abs(g-math.log(z))
                    worst=max(worst,e)
                    if e>1e-9:raise AssertionError(f'trial {t} {ch} kind={kind} s={s} q={q} nu={nu} c={c} key={key} cand={cand} o={o} col={col}: got {g} ref {math.log(z)}')
        cnt+=1;byk[(ch,kind)]=byk.get((ch,kind),0)+1
    return dict(trials=cnt,nonzero_cells=nz,worst_abs_err=worst,by_channel_kind={f'{a}/{b}':v for (a,b),v in sorted(byk.items())})


def mutants(seed=11,trials=300):
    """E0-style witnesses: each wrong reading of the channel must disagree with the engine on some tiny case"""
    rng=random.Random(seed);found={m:0 for m in ('null_visible','null_keyed','null_resets_lm','adv_ignored')}
    for t in range(trials):
        Q=3;n=rng.randint(3,5);m=rng.randint(3,7)
        ch=rng.choice(('hold','spend','skip5','coin'));s=rng.choice((1,-1));q=F(4,5);nu=F(2,5)
        c=[rng.randrange(Q) for _ in range(n)]
        for i in range(1,n):
            if rng.random()<.4:c[i]=c[i-1]
        key=[rng.randrange(Q) for _ in range(m)];cand=[1 if rng.random()<.7 else 0 for _ in range(n)]
        pi,L=rmodel(rng,Q);ff=lambda x:[float(v) for v in x]
        for mu in found:
            kind=2 if mu=='adv_ignored' else 1
            got=all_offsets_edge(c,key,s,float(q),ch,ff(pi),[ff(r) for r in L],kind,cand,float(nu))
            ref=all_offsets_ref(c,key,s,q,ch,pi,L,cand,kind,nu,mutant=mu)
            for o,(zl,zu) in enumerate(ref):
                g=got[o,0]
                if (zl==0)!=(g==-math.inf) or (zl!=0 and abs(g-math.log(zl))>1e-9):found[mu]+=1;break
    return found


if __name__=='__main__':
    print(json.dumps(run(),indent=1));print('mutant witnesses (trials in which the mutant disagrees with the engine):',mutants())
