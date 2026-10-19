"""Exact sparse classes and all-offset backward recurrence (Fraction/NumPy).
Independent inverse transitions; no calls to v1 arcs. No code executes on import.
"""
from fractions import Fraction as F
import math
import numpy as np

CHANNELS=('hold','spend','skip','skip5','coin')


def classes(c,key,i,j,sign,Q):
    """Union for all channels; channel-specific narrowing in state_classes."""
    raise NotImplementedError('Use state_classes with explicit channel')


def state_classes(c,key,i,j,sign,Q,ch):
    if i==0:return ()
    rs=set()
    if j>0:rs.add((c[i-1]-sign*key[j-1])%Q)
    if i>=2:
        if ch=='hold' and j<len(key):rs.add((c[i-2]-sign*key[j])%Q)
        if ch=='spend' and j>0:rs.add((c[i-2]-sign*key[j-1])%Q)
        if ch=='coin' and j>=2:rs.add((c[i-2]-sign*key[j-2])%Q)
    return tuple(sorted(rs))


def inverse_edges(key,j,a,y,sign,q,Q,ch):
    """Yield (plaintext,next pointer,weight) for observed y. Failure has no edge."""
    m=len(key)
    if j>=m:return
    d=(y-sign*key[j])%Q
    if a is None:
        yield d,j+1,F(1)
        return
    p=(a-sign*key[j])%Q
    if y!=a:yield d,j+1,F(1)
    if ch in ('hold','spend'):
        if y==a:yield p,j+1,1-q
        else:yield p,j+int(ch=='spend'),q/(Q-1)
    elif ch=='coin':
        if j+1<m:
            if y==a:yield p,j+2,1-q
            if j+2<m and (p+sign*key[j+2])%Q==y:yield p,j+3,q
    elif ch in ('skip','skip5'):
        w=F(1)
        for h in range(j,m):
            x=(p+sign*key[h])%Q
            if x!=a or (ch=='skip5' and h-j==5):
                if x==y:yield p,h+1,w
                break
            if x==y:yield p,h+1,w*(1-q)
            w*=q
    else:raise ValueError(ch)


def backward_rational(c,key,sign,q,ch,pi,L,mutant=None):
    n,m,Q=len(c),len(key),len(pi)
    if n==0:return [F(1)]*(m+1)
    b={(j,r):F(int(not(mutant=='wrong_end' and j==m)))
       for j in range(m+1) for r in state_classes(c,key,n,j,sign,Q,ch)}
    for i in range(n-1,0,-1):
        new={}
        for j in range(m+1):
            edges=list(inverse_edges(key,j,c[i-1],c[i],sign,q,Q,ch))
            for r in state_classes(c,key,i,j,sign,Q,ch):
                v=F(0)
                for p,h,w in edges:
                    if not w:continue
                    actual=p
                    if mutant=='merge_r':actual=state_classes(c,key,i+1,h,sign,Q,ch)[0]
                    # Exact lookup also tests closure of the sparse graph.
                    v+=L[r][p]*w*b[h,actual]
                new[j,r]=v
        if mutant=='lost_scale':
            scale=max(new.values(),default=F(0))
            if scale:new={k:v/scale for k,v in new.items()}
        b=new
    return [pi[(c[0]-sign*key[o])%Q]*b[o+1,(c[0]-sign*key[o])%Q]
            for o in range(m)]+[F(0)]


def logadd(a,b):
    if a==-math.inf:return b
    if b==-math.inf:return a
    a,b=max(a,b),min(a,b)
    return a+math.log1p(math.exp(b-a))


def backward_numpy(c,key,sign,q,ch,pi,L,uniform=False):
    """Audit-friendly all-offset Float64 LOG recursion; no shared offset scale.

    This Python version is intentionally slow. Rust specialization follows only
    after exact sparse-state and backward gates pass.
    """
    Q=len(pi);n=len(c);m=len(key)
    if n==0:return np.zeros(m+1,dtype=np.float64)
    b={(j,r):0. for j in range(m+1) for r in state_classes(c,key,n,j,sign,Q,ch)}
    # Fractions preserve arbitrarily long geometric tails until log conversion.
    fq=F.from_float(float(q))
    for i in range(n-1,0,-1):
        new={}
        for j in range(m+1):
            ee=list(inverse_edges(key,j,c[i-1],c[i],sign,fq,Q,ch))
            for r in state_classes(c,key,i,j,sign,Q,ch):
                v=-math.inf
                for p,h,w in ee:
                    lp=1/Q if uniform else L[r,p]
                    if w and lp:
                        lw=math.log(w.numerator)-math.log(w.denominator)
                        v=logadd(v,math.log(lp)+lw+b[h,p])
                new[j,r]=v
        b=new
    out=np.full(m+1,-np.inf)
    for o in range(m):
        p=(c[0]-sign*key[o])%Q;lp=1/Q if uniform else pi[p]
        if lp:out[o]=math.log(lp)+b[o+1,p]
    return out
