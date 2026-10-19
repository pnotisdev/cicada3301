"""Write-once exactness gate. No random seeds, no GPU, no engine build."""
import os
for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[v]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
import reference as V1
from fractions import Fraction as F
import hashlib,itertools as it,json,time
from sparse import CHANNELS,backward_rational,inverse_edges,state_classes


def models():
    u=[F(1,3)]*3;p=[F(1,6),F(2,6),F(3,6)]
    return [(u,[u]*3),(p,[p,[F(3,6),F(1,6),F(2,6)],[F(2,6),F(3,6),F(1,6)]])]


def support(c,key,sign,q,ch):
    live={(j+1,(c[0]-sign*key[j])%3) for j in range(len(key))} if c else set()
    largest=1 if live else 0
    for i in range(1,len(c)):
        nxt=set()
        for j,r in live:
            for p in range(3):
                for y,h,w in V1.arcs(key,j,p,c[i-1],sign,q,3,ch):
                    if y==c[i] and w:nxt.add((h,p))
        for j in range(len(key)+1):
            rs={r for h,r in nxt if h==j}
            assert rs<=set(state_classes(c,key,i+1,j,sign,3,ch)),('support closure',c,key,ch,i,j,rs)
            largest=max(largest,len(rs))
        live=nxt
    assert largest<=2,('R1 counterexample',key,c,ch,largest)
    return largest


def run():
    count=trees=passes=0;max_support={ch:0 for ch in CHANNELS};witnesses={}
    trace=hashlib.sha256()
    old={'hold_spends':'hold','coin_missing_slot':'coin','skip_drops_tail':'skip','replacement_denominator':'spend'}
    new=('merge_r','wrong_end','lost_scale')
    for m in range(4):
        for key in it.product(range(3),repeat=m):
            for sign,q,ch,model,n in it.product((-1,1),(F(0),F(3,5),F(1)),CHANNELS,range(2),range(4)):
                pi,L=models()[model]
                enum=[]
                for off in range(m+1):
                    outputs,fail=V1.event_tree(key,off,sign,q,ch,pi,L,n)
                    assert sum(outputs.values())+sum(fail.values())==1
                    trees+=1;enum.append(outputs)
                    for mutant,target in old.items():
                        if target==ch and mutant not in witnesses:
                            bad=V1.event_tree(key,off,sign,q,ch,pi,L,n,mutant=mutant)
                            if bad!=(outputs,fail):
                                witnesses[mutant]=dict(key=key,offset=off,sign=sign,q=str(q),channel=ch,model=model,n=n)
                for c in it.product(range(3),repeat=n):
                    case=dict(key=key,cipher=c,sign=sign,q=str(q),channel=ch,model=model)
                    b=backward_rational(c,key,sign,q,ch,pi,L);passes+=1
                    for off in range(m+1):
                        f=V1.rational_forward(c,key,off,sign,q,ch,pi,L)
                        expected=enum[off].get(c,F(0))
                        assert b[off]==f==expected,('backward mismatch',case,off,str(b[off]),str(f),str(expected))
                        trace.update(f'{count}:{b[off]};'.encode());count+=1
                    if model==0:max_support[ch]=max(max_support[ch],support(c,key,sign,q,ch))
                    for mutant in new:
                        if mutant not in witnesses:
                            bad=backward_rational(c,key,sign,q,ch,pi,L,mutant=mutant)
                            if bad!=b:witnesses[mutant]=dict(**case,correct=list(map(str,b)),mutated=list(map(str,bad)))
    assert len(witnesses)==7,('undetected mutation',witnesses)
    tails=0
    for ch in CHANNELS:
        u=[F(1,3)]*3;key=(0,)*8
        for c in it.product(range(3),repeat=2):
            b=backward_rational(c,key,1,F(3,5),ch,u,[u]*3)
            for off in range(9):
                assert b[off]==V1.rational_forward(c,key,off,1,F(3,5),ch,u,[u]*3)
                tails+=1
    return dict(status='PASS',comparisons=count,all_offset_passes=passes,normalized_trees=trees,
                long_tail_offset_checks=tails,max_nonzero_classes=max_support,mutations=witnesses,
                comparison_trace_sha256=trace.hexdigest())

if __name__=='__main__':
    dest=HERE/'e0.json'
    if dest.exists() or (HERE/'e0.started').exists():raise SystemExit('E0 already attempted')
    (HERE/'e0.started').write_text('One-shot exactness gate.\n')
    t=time.perf_counter()
    try:r=run()
    except Exception as exc:r=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    r['seconds']=time.perf_counter()-t
    r['hashes']={p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in ('README.md','sparse.py','e0.py')}
    dest.write_text(json.dumps(r,indent=2,default=str)+'\n')
    print(json.dumps(r,indent=2,default=str))
    if r['status']!='PASS':raise SystemExit(1)
