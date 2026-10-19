"""Write-once per-key-length exact audit of a PROPOSED, undeployed statistic."""
from proposal import score_common,log_common
from checkpoint import HERE,save,log
import sys,json,time,hashlib,math,itertools as it
from functools import lru_cache
from collections import defaultdict
from fractions import Fraction as F
import numpy as np
sys.path.insert(0,str(HERE.parent))
from bounds import common,tiny_models,CHANNELS,V1
sys.path.insert(0,str(HERE.parents[1]))
from engine import all_offsets


def ln(x):return math.log(x.numerator)-math.log(x.denominator) if x else -math.inf

@lru_cache(None)
def W_dist(q,n):
    d={c:common(c,q,3) for c in it.product(range(3),repeat=n)}
    assert sum(d.values())==1
    return d


def part(m):
    raw=[];meta=[];ntails=outside=equal_controls=0;maxerr=0.;h=hashlib.sha256()
    for ki,key in enumerate(it.product(range(3),repeat=m)):
        for s,qi,ch,n,model in it.product((-1,1),range(3),range(5),range(4),range(2)):
            q=(F(0),F(3,5),F(1))[qi];name=CHANNELS[ch];pi,L=tiny_models()[model]
            W=W_dist(q,n);trees=[]
            for off in range(m+1):
                P,fail=V1.event_tree(key,off,s,q,name,pi,L,n)
                assert sum(P.values())+sum(fail.values())==1
                if model==0 and name in ('hold','spend') and m-off>=n:
                    assert all(P.get(c,F(0))==w for c,w in W.items());equal_controls+=len(W)
                bins=defaultdict(F)
                for c,p in P.items():
                    if W[c]:bins[p/W[c]]+=W[c]
                    else:outside+=1
                tail=F(0)
                for ratio,pw in sorted(bins.items(),reverse=True):
                    tail+=pw;assert tail<=1/ratio
                    ntails+=1;h.update(f'{ratio}:{tail};'.encode())
                trees.append(P)
            for ci,(c,w) in enumerate(W.items()):
                got=all_offsets(c,key,s,float(q),name,np.array(pi,float),np.array(L,float))
                sw,unsupported=score_common(got[:,0],c,float(q),3)
                assert unsupported==(w==0)
                if model==0:
                    assert np.array_equal(np.isfinite(got[:,0]),np.isfinite(got[:,1]))
                    use=np.isfinite(got[:,0]);assert np.max(abs(got[use,0]-got[use,1]),initial=0)<1e-9
                for off,P in enumerate(trees):
                    expected_l=ln(P.get(c,F(0)))
                    expected_s=expected_l-ln(w) if w and expected_l!=-math.inf else -math.inf
                    assert math.isfinite(got[off,0])==math.isfinite(expected_l)
                    assert math.isfinite(sw[off])==math.isfinite(expected_s)
                    if math.isfinite(expected_l):maxerr=max(maxerr,abs(got[off,0]-expected_l))
                    if math.isfinite(expected_s):maxerr=max(maxerr,abs(sw[off]-expected_s))
                    assert maxerr<=1e-9
                    raw.append([got[off,0],got[off,1],expected_l,sw[off],expected_s])
                    meta.append([ki,s,qi,ch,n,model,ci,off])
    return dict(status='PASS',m=m,cells=len(raw),exact_tail_inequalities=ntails,
                zero_W_positive_L_cells=outside,no_exhaustion_W_controls=equal_controls,
                max_error_nats=maxerr,tail_digest=h.hexdigest()),np.array(raw),np.array(meta,dtype=np.int32)


def long_check():
    from bounds import long_event
    thresholds=json.loads((HERE.parent/'thresholds.json').read_text())
    r=long_event(29,26,3,300,F(81,100),thresholds['inventory']['300']['LR_threshold_integer'])
    c=r['representative_cipher'];pi=np.full(29,1/29)
    L=np.array([[1/26 if (p-a)%29>=3 else 0. for p in range(29)] for a in range(29)])
    got=all_offsets(c,[3,0],1,.81,'hold',pi,L)[0]
    want=np.array([ln(F(r['representative_L'])),ln(F(r['representative_U']))])
    error=float(max(abs(got-want)));assert error<=1e-9
    proposed,unsupported=score_common(got[0],c,.81,29);assert not unsupported
    return dict(status='PASS',Q=29,n=300,key=[3,0],log_L=float(got[0]),log_U=float(got[1]),
                log_W=log_common(c,.81,29),S_original=float(got[0]-got[1]),S_W_proposed=float(proposed),
                rational_log_error_nats=error,original_common_bound_refuted=r['common_bound_refuted'],
                note='Numerical/proof diagnostic only, not an E3 pass or a power test')

if __name__=='__main__':
    arg=sys.argv[1];name='f1_'+arg
    if (HERE/(name+'.json')).exists() or (HERE/(name+'.started')).exists():raise SystemExit('Already attempted; no retry')
    save(name+'.started',dict(command='f1.py '+arg,protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest()))
    t=time.perf_counter()
    try:
        if arg=='long':r=long_check()
        else:
            r,raw,meta=part(int(arg));np.savez_compressed(HERE/(name+'.npz'),values=raw,index=meta)
            r['columns']=['actual_log_L','actual_log_U','exact_log_L','proposed_S_W','exact_S_W']
            r['index_columns']=['key_index','sign','q_index','channel_index','n','model_index','cipher_index','offset']
    except Exception as exc:r=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    r['seconds']=time.perf_counter()-t;save(name+'.json',r);log(name,**r)
    print(json.dumps(r))
    if r['status']!='PASS':raise SystemExit(1)
