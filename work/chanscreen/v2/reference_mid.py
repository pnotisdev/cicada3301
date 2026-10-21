"""Dense brute-force EXACT reference for the mid-word null channel (Fractions, no DP, no class sets).

P(c | offset o) = sum over every per-word placement of the (at most one) interior keyless null of
  prod_words weight(word, placement) * P(c | explicit null positions)
where weight = 1-nu (no null) or nu/(Lc-2) (null at one interior slot) for words with Lc >= 3 and 1 for shorter words, and
P(c | null positions) is the exact event tree of the encryptors (plaintext symbol x channel randomness), nulls emitted 1/Q, no key, invisible to
the anti-repeat rule and the LM. Written from the encryptors (work/m04/m04.py) like reference_edge.py. Only for tiny cases.
"""
from fractions import Fraction as F
from itertools import product


def words_of(n,wstart):
    ws=[0]+[i for i in range(1,n) if wstart[i]]
    return [(a,(ws[x+1] if x+1<len(ws) else n)) for x,a in enumerate(ws)]


def prob_nulls(c,key,o,s,q,ch,pi,L,nulls,uniform=False,mutant=None):
    Q=len(pi);n=len(c);m=len(key);q=F(q)
    def lm(r,pt):
        if uniform:return F(1,Q)
        return pi[pt] if r is None else L[r][pt]
    def emit(j,ell,pt,y):
        if j>=m:return
        x=(pt+s*key[j])%Q
        coll=ell is not None and x==ell
        if ch in ('hold','spend'):
            if coll:
                if y==x:yield j+1,1-q
                if y!=ell:yield (j if ch=='hold' else j+1),q/(Q-1)
            elif y==x:yield j+1,F(1)
        elif ch=='skip5':
            jj=j+1;w=F(1);tries=0
            while True:
                if not (ell is not None and x==ell and tries<5):
                    if x==y:yield jj,w
                    return
                if x==y:yield jj,w*(1-q)
                w*=q
                if jj>=m:return
                x=(pt+s*key[jj])%Q;jj+=1;tries+=1
        elif ch=='coin':
            if not coll:
                if x==y:yield j+1,F(1)
            else:
                if j+1>=m:return
                if y==x:yield j+2,1-q
                if j+2<m and (pt+s*key[j+2])%Q==y:yield j+3,q
        else:raise ValueError(ch)
    cache={}
    def go(i,j,ell,r):
        kk=(i,j,ell,r)
        if kk not in cache:cache[kk]=go_(i,j,ell,r)
        return cache[kk]
    def go_(i,j,ell,r):
        if i==n:return F(1)
        y=c[i]
        if i in nulls:
            if mutant=='null_visible':return F(1,Q)*go(i+1,j,y,r)
            if mutant=='null_keyed':return F(1,Q)*go(i+1,j+1,ell,r)
            return F(1,Q)*go(i+1,j,ell,r)
        tot=F(0)
        for pt in range(Q):
            lp=lm(r,pt)
            if lp==0:continue
            for h,w in emit(j,ell,pt,y):
                if w:tot+=lp*w*go(i+1,h,y,pt)
        return tot
    return go(0,o,None,None)


def prob(c,key,o,s,q,ch,pi,L,wstart,nu,uniform=False,mutant=None):
    n=len(c);nu=F(nu)
    if n==0:return F(1)
    opts=[]   # per word: list of (weight, null positions)
    for a,b in words_of(n,wstart):
        lc=b-a
        if lc<3:opts.append([(F(1),())])
        else:opts.append([(1-nu,())]+[(nu/(lc-2),(t,)) for t in range(a+1,b-1)])
    tot=F(0)
    for combo in product(*opts):
        w=F(1);ns=set()
        for wt,t in combo:
            w*=wt;ns.update(t)
        if w==0:continue
        tot+=w*prob_nulls(c,key,o,s,q,ch,pi,L,ns,uniform,mutant)
    return tot


def all_offsets_ref(c,key,s,q,ch,pi,L,wstart,nu,mutant=None):
    m=len(key);n=len(c);out=[]
    for o in range(m+1):
        if n>=1 and o>=m:out.append((F(0),F(0)));continue
        out.append((prob(c,key,o,s,q,ch,pi,L,wstart,nu,mutant=mutant),prob(c,key,o,s,q,ch,pi,L,wstart,nu,uniform=True,mutant=mutant)))
    return out
