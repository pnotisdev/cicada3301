"""Diagnostic checks of a conservative AND rule; original gate remains FAIL."""
from guard import guarded
from checkpoint import HERE,save,log
import sys,itertools as it,math,json,time,hashlib
from fractions import Fraction as F
from collections import defaultdict
import numpy as np
sys.path.insert(0,str(HERE.parent))
from bounds import common,tiny_models,CHANNELS,V1


def exact(m):
    cells=tails=nulls=0;h=hashlib.sha256();u=[F(1,3)]*3
    for key in it.product(range(3),repeat=m):
        for off,s,q,ch,n in it.product(range(m+1),(-1,1),(F(0),F(3,5),F(1)),CHANNELS,range(4)):
            U,ufail=V1.event_tree(key,off,s,q,ch,u,[u]*3,n)
            assert sum(U.values())+sum(ufail.values())==1
            for model,(pi,L) in enumerate(tiny_models()):
                P,fail=V1.event_tree(key,off,s,q,ch,pi,L,n)
                assert sum(P.values())+sum(fail.values())==1
                bins=defaultdict(lambda:[F(0),F(0)])
                for c in it.product(range(3),repeat=n):
                    cells+=1;pu=U.get(c,F(0));p=P.get(c,F(0));w=common(c,q,3)
                    if not (pu and w and p):continue
                    R=p/max(pu,w)
                    if model==0:assert R<=1;nulls+=1
                    bins[R][0]+=pu;bins[R][1]+=w
                a=b=F(0)
                for R,(pu,pw) in sorted(bins.items(),reverse=True):
                    a+=pu;b+=pw;assert a<=1/R and b<=1/R;tails+=1
                    h.update(f'{R}:{a}:{b};'.encode())
    return dict(status='PASS',m=m,output_model_cells=cells,tail_bounds_each_measure=tails,uniform_null_controls=nulls,digest=h.hexdigest())


def numeric():
    maxerr=0.;total=0
    for m in range(4):
        with np.load(HERE/f'f1_{m}.npz') as z:v=z['values'];idx=z['index']
        U={tuple(np.delete(k,5)):row[2] for k,row in zip(idx,v) if k[5]==0}
        exact_u=np.array([U[tuple(np.delete(k,5))] for k in idx])
        old=np.full(len(v),-math.inf);np.subtract(v[:,2],exact_u,out=old,where=np.isfinite(exact_u))
        expected=np.minimum(old,v[:,4]);actual=np.empty(len(v))
        for qi,n in it.product(range(3),range(4)):
            for ci in range(3**n):
                c=tuple((ci//(3**(n-1-j)))%3 for j in range(n))
                mask=(idx[:,2]==qi)&(idx[:,4]==n)&(idx[:,6]==ci)
                actual[mask],_=guarded(v[mask,0],v[mask,1],c,(0.,.6,1.)[qi],3)
        assert np.array_equal(np.isfinite(actual),np.isfinite(expected))
        use=np.isfinite(expected);err=float(np.max(abs(actual[use]-expected[use]),initial=0));assert err<=1e-9
        maxerr=max(maxerr,err);total+=len(v)
        np.savez_compressed(HERE/f'f4_numeric_{m}.npz',actual=actual,expected=expected)
    return dict(status='PASS',cells=total,max_error_nats=maxerr)


def reuse():
    with np.load(HERE/'f2_scores.npz') as z:g=np.min(z['scores'],axis=2)
    rr=[]
    for p in sorted((HERE/'f2_records').glob('*.json')):
        if p.stem.count('_')==1:rr.extend(json.loads(p.read_text()))
    assert [r['index'] for r in rr]==list(range(380))
    T=json.loads((HERE/'f2.json').read_text())['T300'];stats=defaultdict(lambda:dict(n=0,true_at_T=0,max_at_T=0))
    for r in rr:
        k=r['type']+'|'+r['source']+'|'+r['kind'];a=stats[k];a['n']+=1;a['max_at_T']+=int(max(g[r['index']])>=T)
        if r['type']!='null':a['true_at_T']+=int(min(r['old_true_score'],r['proposed_true_score'])>=T)
    pp=json.loads((HERE/'f2_pass_counts.json').read_text());groups=defaultdict(list)
    for p in pp:groups[p['record'],p['sign'],p['channel']].append(p)
    rows=[]
    for key,pair in groups.items():
        assert len(pair)==2 and pair[0]['stored_offsets']==pair[1]['stored_offsets']
        scores=np.minimum([x if x is not None else -math.inf for x in pair[0]['stored_scores']],
                          [x if x is not None else -math.inf for x in pair[1]['stored_scores']])
        counts={str(t):int(np.sum(scores>=t)) for t in (0,5,10)}
        rows.append(dict(record=key[0],sign=key[1],channel=key[2],counts=counts,
            full_pass_failure_proven={t:counts[t]>pair[0]['full_bounds'][t] for t in counts}))
    save('f4_guard_pass_counts.json',rows);np.savez_compressed(HERE/'f4_guard_scores.npz',scores=g)
    return dict(status='COMPLETE_DESCRIPTIVE_AUDIT',groups=dict(stats),
        full_pass_failures_proven={str(t):sum(p['full_pass_failure_proven'][str(t)] for p in rows) for t in (0,5,10)},
        records_with_a_proven_failure={str(t):len({p['record'] for p in rows if p['full_pass_failure_proven'][str(t)]}) for t in (0,5,10)},
        null_max=float(max(g[r['index']].max() for r in rr if r['type']=='null')),
        note='Same previously audited held data and numerator q; no independent power validation')

if __name__=='__main__':
    arg=sys.argv[1];name='f4_'+arg
    if (HERE/(name+'.started')).exists() or (HERE/(name+'.json')).exists():raise SystemExit('Already attempted; no retry')
    save(name+'.started',dict(protocol_sha256=hashlib.sha256((HERE/'F4_PROTOCOL.md').read_bytes()).hexdigest(),
         source_sha256=hashlib.sha256((HERE/'f4.py').read_bytes()).hexdigest(),guard_sha256=hashlib.sha256((HERE/'guard.py').read_bytes()).hexdigest()))
    t=time.perf_counter()
    try:r=numeric() if arg=='numeric' else reuse() if arg=='reuse' else exact(int(arg))
    except Exception as exc:r=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    r['seconds']=time.perf_counter()-t;save(name+'.json',r);log(name,**r);print(json.dumps(r))
    if r['status']=='FAIL':raise SystemExit(1)
