"""Dense/brute-force EXACT reference for the word-edge channels (Fractions, no memoisation).

P(output == c | offset o) is summed over the whole generative event tree: for each position the latent edge
choice (keyless null / extra key advance), the plaintext symbol (language model), and the channel's own randomness
(hold/spend repair, skip5 redraws, coin). Written from the encryptors (work/m04/m04.py: enc_m04, enc_spend, enc_skip,
enc_coin), not from the DP in backward_edge.rs. Only for tiny cases (Q^n paths).
"""
from fractions import Fraction as F


def prob(c,key,o,s,q,ch,pi,L,cand=None,kind=0,nu=F(0),uniform=False,mutant=None,memo=False):
    Q=len(pi);n=len(c);m=len(key);q=F(q);nu=F(nu)
    if n==0:return F(1)
    cand=[0]*n if cand is None else [int(x) if i else 0 for i,x in enumerate(cand)]
    def lm(r,pt):
        if uniform:return F(1,Q)
        return pi[pt] if r is None else L[r][pt]
    def emit(j,ell,pt,y):
        """yield (new pointer, prob) of emitting exactly y for plaintext pt from pointer j after real cipher rune ell"""
        if j>=m:return
        x=(pt+s*key[j])%Q
        coll=ell is not None and x==ell
        if ch in ('hold','spend'):
            if coll:
                if y==x:yield j+1,1-q                      # repair skipped: the doublet survives
                if y!=ell:yield (j if ch=='hold' else j+1),q/(Q-1)   # uniform among the Q-1 other runes
            elif y==x:yield j+1,F(1)
        elif ch=='skip5':
            jj=j+1;w=F(1);tries=0
            while True:
                if not (ell is not None and x==ell and tries<5):   # accepted (no collision, or the 5-redraw cap)
                    if x==y:yield jj,w
                    return
                if x==y:yield jj,w*(1-q)                  # kept the doublet
                w*=q                                       # redraw
                if jj>=m:return
                x=(pt+s*key[jj])%Q;jj+=1;tries+=1
        elif ch=='coin':
            if not coll:
                if x==y:yield j+1,F(1)
            else:
                if j+1>=m:return
                if y==x:yield j+2,1-q                      # coin spent, kept
                if j+2<m and (pt+s*key[j+2])%Q==y:yield j+3,q   # coin spent, redrawn
        else:raise ValueError(ch)
    cache={}
    def go(i,j,ell,r):
        if i==n:return F(1)
        if memo:
            kk=(i,j,ell,r)
            if kk in cache:return cache[kk]
            cache[kk]=go_(i,j,ell,r);return cache[kk]
        return go_(i,j,ell,r)
    def go_(i,j,ell,r):
        y=c[i];tot=F(0)
        branches=[(F(1),0,'real')]
        if cand[i] and kind==1:branches=[(1-nu,0,'real'),(nu,0,'null')]
        if cand[i] and kind==2:branches=[(1-nu,0,'real'),(nu,1,'real')]
        for wb,adv,what in branches:
            if wb==0:continue
            if what=='null':
                if mutant=='null_visible':tot+=wb*F(1,Q)*go(i+1,j,y,r)          # null seen by the anti-repeat rule
                elif mutant=='null_keyed':tot+=wb*F(1,Q)*go(i+1,j+1,ell,r)     # null consumes a key value
                elif mutant=='null_resets_lm':tot+=wb*F(1,Q)*go(i+1,j,ell,None)   # LM restarts after a null
                else:tot+=wb*F(1,Q)*go(i+1,j,ell,r)
                continue
            jj=j+adv if mutant!='adv_ignored' else j
            for pt in range(Q):
                lp=lm(r,pt)
                if lp==0:continue
                for h,w in emit(jj,ell,pt,y):
                    if w:tot+=wb*lp*w*go(i+1,h,y,pt)
        return tot
    return go(0,o,None,None)


def all_offsets_ref(c,key,s,q,ch,pi,L,cand=None,kind=0,nu=F(0),mutant=None):
    """[(Z_L,Z_U)] for offsets 0..m (offset m: 0 for n>=1, as the engine)"""
    m=len(key);n=len(c)
    out=[]
    for o in range(m+1):
        if n>=1 and o>=m:out.append((F(0),F(0)));continue
        out.append((prob(c,key,o,s,q,ch,pi,L,cand,kind,nu,mutant=mutant),prob(c,key,o,s,q,ch,pi,L,cand,kind,nu,uniform=True,mutant=mutant)))
    return out
