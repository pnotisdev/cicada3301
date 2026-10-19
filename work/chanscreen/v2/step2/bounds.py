"""Exact finite-key LR and common-null audit; no random seeds or real searches."""
import os
for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[v]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[1]))
import reference as V1
from fractions import Fraction as F
from collections import defaultdict
import itertools as it
import hashlib,math

CHANNELS=('hold','spend','skip','skip5','coin')


def common(c,q,Q):
    if not c:return F(1)
    p=F(1,Q)
    for a,b in zip(c,c[1:]):p*=((1-q)/Q if a==b else (Q-1+q)/(Q*(Q-1)))
    return p


def tiny_models():
    u=[F(1,3)]*3;p=[F(1,6),F(2,6),F(3,6)]
    return [(u,[u]*3),(p,[p,[F(3,6),F(1,6),F(2,6)],[F(2,6),F(3,6),F(1,6)]])]


def matched_grid():
    comparisons=inequalities=trees=common_checks=0
    trace=hashlib.sha256();u=[F(1,3)]*3
    for m in range(4):
        for key in it.product(range(3),repeat=m):
            for off,s,q,ch,n in it.product(range(m+1),(-1,1),(F(0),F(3,5),F(1)),CHANNELS,range(4)):
                U,UF=V1.event_tree(key,off,s,q,ch,u,[u]*3,n)
                assert sum(U.values())+sum(UF.values())==1
                if ch in ('hold','spend') and m-off>=n:
                    for c in it.product(range(3),repeat=n):
                        assert U.get(c,F(0))==common(c,q,3)
                        common_checks+=1
                for pi,L in tiny_models():
                    P,PF=V1.event_tree(key,off,s,q,ch,pi,L,n)
                    assert sum(P.values())+sum(PF.values())==1
                    trees+=1;assert set(P)<=set(U)
                    ratios=defaultdict(F);expectation=F(0)
                    for c in it.product(range(3),repeat=n):
                        pu=U.get(c,F(0));pl=P.get(c,F(0));comparisons+=1
                        if pu:
                            expectation+=pu*(pl/pu)
                            if pl:ratios[pl/pu]+=pu
                    assert expectation==sum(P.values()) and expectation<=1
                    tail=F(0)
                    for R,prob in sorted(ratios.items(),reverse=True):
                        tail+=prob
                        assert tail<=1/R,('matched null bound',key,off,s,q,ch,n,R,tail)
                        inequalities+=1
                        trace.update(f'{R}:{tail};'.encode())
    return dict(status='PASS',output_comparisons=comparisons,normalized_L_trees=trees,
                exact_tail_inequalities=inequalities,no_exhaustion_common_law_checks=common_checks,
                comparison_digest=trace.hexdigest())


def small_counterexample():
    q=F(3,5);pi=[F(1),F(0),F(0)];L=[[F(int(a==b)) for b in range(3)] for a in range(3)]
    u=[F(1,3)]*3;key=(0,0);R=F(20)
    P,PF=V1.event_tree(key,0,1,q,'hold',pi,L,3)
    U,UF=V1.event_tree(key,0,1,q,'hold',u,[u]*3,3)
    rows=[];own=wrong=F(0)
    for c in it.product(range(3),repeat=3):
        pl=P.get(c,F(0));pu=U.get(c,F(0));w=common(c,q,3)
        # Independent DP confirms the exact event-tree probabilities.
        assert pl==V1.rational_forward(c,key,0,1,q,'hold',pi,L)
        assert pu==V1.rational_forward(c,key,0,1,q,'hold',u,[u]*3)
        hit=bool(pu and pl>=R*pu)
        if hit:own+=pu;wrong+=w
        rows.append(dict(cipher=c,L=str(pl),U_cell=str(pu),W=str(w),LR=str(pl/pu) if pu else None,hit=hit))
    return dict(key=key,Q=3,n=3,sign=1,q=str(q),threshold_LR=str(R),bound=str(1/R),
                tail_U_cell=str(own),tail_W=str(wrong),own_bound_pass=own<=1/R,
                common_bound_pass=wrong<=1/R,L_success=str(sum(P.values())),U_success=str(sum(U.values())),
                rows=rows)


def long_event(Q,d,a,n,q,threshold_R):
    # D={a,...,Q-1}; for all declared cases a=Q-d.
    assert a==Q-d and 0<a<Q
    pi=[F(1,Q)]*Q
    L=[[F(1,d) if (p-r)%Q>=a else F(0) for p in range(Q)] for r in range(Q)]
    UL=[pi]*Q;key=(a,0)
    c=tuple((i*a)%Q for i in range(n-1));c=c+(c[-1],)
    pl=V1.rational_forward(c,key,0,1,q,'hold',pi,L)
    pu=V1.rational_forward(c,key,0,1,q,'hold',pi,UL)
    expected_l=F(1,Q)*(q/(d*(Q-1)))**(n-2)*(1-q)/d
    expected_u=F(1,Q)*(q/(Q*(Q-1)))**(n-2)*(1-q)/Q
    assert pl==expected_l and pu==expected_u
    ratio=pl/pu;assert ratio==F(Q,d)**(n-1)
    multiplicity=Q*d**(n-2)
    W=(d*F(Q-1+q,Q*(Q-1)))**(n-2)*(1-q)/Q
    assert multiplicity*common(c,q,Q)==W
    U=pu*multiplicity;PL=pl*multiplicity
    assert U<=1/ratio and PL<=1
    bound=F(1,threshold_R);hit=ratio>=threshold_R
    return dict(Q=Q,n=n,key=key,q=str(q),allowed_increments=list(range(a,Q)),
                representative_cipher=c,representative_L=str(pl),representative_U=str(pu),
                event_LR=str(ratio),event_S_nats=math.log(ratio.numerator)-math.log(ratio.denominator),
                campaign_LR_threshold=threshold_R,bound=str(bound),event_W_mass=str(W),event_W_mass_float=float(W),
                event_U_mass=str(U),event_L_mass=str(PL),W_over_bound=float(W/bound),
                above_campaign_threshold=hit,common_bound_refuted=bool(hit and W>bound))


def key_dependence():
    q=F(3,5);Q=3;u=[F(1,Q)]*Q;keys=((0,0,0,0,0,0,0),(0,0,1,1,1,1,1));rows=[]
    for ch in ('skip5','coin'):
        ds=[]
        for key in keys:
            U,fail=V1.event_tree(key,0,1,q,ch,u,[u]*Q,2)
            assert sum(U.values())==1 and not fail
            ds.append(U)
            ratios=[];infinite=False;tv=F(0)
            for c in it.product(range(Q),repeat=2):
                pu=U.get(c,F(0));w=common(c,q,Q);tv+=abs(pu-w)/2
                if pu:ratios.append(w/pu)
                elif w:infinite=True
            rows.append(dict(channel=ch,key=key,U_00=str(U.get((0,0),F(0))),
                TV_from_W=str(tv),max_W_over_U='infinite' if infinite else str(max(ratios)),
                outputs=[dict(cipher=c,U=str(U.get(c,F(0))),W=str(common(c,q,Q))) for c in it.product(range(Q),repeat=2)]))
        tv=sum(abs(ds[0].get(c,F(0))-ds[1].get(c,F(0)))/2 for c in it.product(range(Q),repeat=2))
        assert tv>0
        rows.append(dict(channel=ch,TV_between_keys=str(tv)))
    return rows
