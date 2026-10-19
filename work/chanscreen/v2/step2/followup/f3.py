"""Exact finite-hold factor and conservative skip/coin density diagnostics."""
from proposal import log_common
from checkpoint import HERE,save,log
import sys,itertools as it,math,json,time,hashlib
from fractions import Fraction as F
from functools import lru_cache
import numpy as np
sys.path.insert(0,str(HERE.parent))
from bounds import common,V1
sys.path.insert(0,str(HERE.parents[1]))
from engine import all_offsets

@lru_cache(None)
def binomial_cdf(B,a,k):
    if k<0:return F(0)
    if k>=B:return F(1)
    return sum((F(math.comb(B,j))*a**j*(1-a)**(B-j) for j in range(k+1)),F(0))


def hold_mass(c,r,q,Q):
    n=len(c)
    if not n:return F(1)
    if not r:return F(0)
    w=common(c,q,Q)
    if n==1:return w
    Dp=sum(a==b for a,b in zip(c[:-2],c[1:-1]));Bp=n-2-Dp
    return w*binomial_cdf(Bp,F(Q-1,Q-1+q),r-2-Dp)


def hold_log_all(c,m,q,Q):
    n=len(c)
    if not n:return np.zeros(m+1)
    w=log_common(c,q,Q);out=np.full(m+1,-math.inf)
    if w==-math.inf:return out
    if n==1:out[:m]=w;return out
    Dp=sum(a==b for a,b in zip(c[:-2],c[1:-1]));B=n-2-Dp
    cdf=np.full(B+1,-math.inf)
    if q==0:cdf[B]=0.
    else:
        term=B*(math.log(q)-math.log(Q-1+q));acc=term;cdf[0]=min(0.,acc)
        for k in range(1,B+1):
            term+=math.log(B-k+1)-math.log(k)+math.log(Q-1)-math.log(q)
            hi=max(acc,term);acc=hi+math.log1p(math.exp(min(acc,term)-hi));cdf[k]=min(0.,acc)
        cdf[B]=0. # complete binomial sum is exactly1
    for off in range(m+1):
        k=m-off-2-Dp
        if k>=0:out[off]=w+(cdf[k] if k<B else 0.)
    return out


def tiny(m):
    Q=3;pi=[F(1,3)]*3;cells=heq=seq=lower=outside=0;h=hashlib.sha256()
    for key in it.product(range(Q),repeat=m):
        for off,s,q,ch,n in it.product(range(m+1),(-1,1),(F(0),F(3,5),F(1)),('hold','spend','skip5','coin'),range(5)):
            U,fail=V1.event_tree(key,off,s,q,ch,pi,[pi]*3,n)
            assert sum(U.values())+sum(fail.values())==1
            for c in it.product(range(Q),repeat=n):
                pu=U.get(c,F(0));w=common(c,q,Q);cells+=1
                if ch=='hold':
                    want=hold_mass(c,m-off,q,Q);assert want==pu;heq+=1
                elif ch=='spend':
                    want=w if m-off>=n else F(0);assert want==pu;seq+=1
                else:
                    D=sum(a==b for a,b in zip(c,c[1:]));required=n+(D if ch=='coin' else 0)
                    if not w:outside+=1;continue
                    if m-off>=required:
                        base=F(1,Q)**n*(1-q)**D;B=(1+q/(Q-1))**max(0,n-1-D)
                        assert pu>=base and w<=B*pu;lower+=1
                h.update(f'{pu};'.encode())
    return dict(status='PASS',m=m,output_cells=cells,hold_equalities=heq,spend_equalities=seq,
                eligible_skip_coin_bounds=lower,outside_W_support_outputs=outside,digest=h.hexdigest())


def long_check():
    rows=[];raw=[]
    Q=29;q=.81;m=2000;pi=np.full(Q,1/Q);L=np.full((Q,Q),1/Q)
    for n,repeat,keytype in it.product((300,600),(False,True),('constant','cycling')):
        c=[i%Q for i in range(n)]
        if repeat:
            for i in range(17,n,17):c[i]=c[i-1]
        key=[0]*m if keytype=='constant' else [i%Q for i in range(m)]
        want=hold_log_all(c,m,q,Q);got=all_offsets(c,key,1,q,'hold',pi,L)[:,1]
        assert np.array_equal(np.isfinite(want),np.isfinite(got))
        finite=np.isfinite(want);error=float(np.max(abs(want[finite]-got[finite]),initial=0));assert error<=1e-9
        raw.append(np.column_stack((want,got)))
        rows.append(dict(n=n,repeated_pattern=repeat,key_pattern=keytype,offsets=m+1,max_error_nats=error))
    np.savez_compressed(HERE/'f3_long.npz',values=np.array(raw),columns=np.array(['closed_form_log_U','Rust_log_U']))
    return dict(status='PASS',cases=rows,penalty_nats={str(n):(n-1)*math.log1p(.81/28) for n in (300,600)},
                note='Conservative skip5/coin bound only on stated sufficient-horizon scope; not deployment authorization')

if __name__=='__main__':
    arg=sys.argv[1];name='f3_'+arg
    if (HERE/(name+'.started')).exists() or (HERE/(name+'.json')).exists():raise SystemExit('Already attempted; no retry')
    save(name+'.started',dict(protocol_sha256=hashlib.sha256((HERE/'F3_PROTOCOL.md').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((HERE/'f3.py').read_bytes()).hexdigest()))
    t=time.perf_counter()
    try:r=long_check() if arg=='long' else tiny(int(arg))
    except Exception as exc:r=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    r['seconds']=time.perf_counter()-t;save(name+'.json',r);log(name,**r);print(json.dumps(r))
    if r['status']!='PASS':raise SystemExit(1)
