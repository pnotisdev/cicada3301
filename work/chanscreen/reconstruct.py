"""Full-state Viterbi traceback for accuracy ONLY; never used for detection."""
import math
import numpy as np
from reference import arcs, validate


def edges(key, prev, y, sign, q, channel, Q):
    out=[]
    for j in range(len(key)):
        # Only ordinary plaintext or initial colliding plaintext can emit y.
        ps=sorted({(y-sign*key[j])%Q, (prev-sign*key[j])%Q}) if prev is not None else [(y-sign*key[j])%Q]
        for p in ps:
            for emitted,h,w in arcs(key,j,p,prev,sign,q,Q,channel):
                if emitted==y and w>0:
                    out.append((j,p,h,math.log(w)))
    return out


def viterbi(cipher,key,off,sign,q,channel,pi,L):
    validate(cipher,key,off,sign,q,channel,pi,L)
    n,m,Q=len(cipher),len(key),len(pi)
    if not n:return [],[],0.
    if not m:return [],[],-math.inf
    with np.errstate(divide='ignore'):
        logL=np.log(L); logpi=np.log(pi)
    a=np.full((m+1,Q),-np.inf)
    links=np.full((n,m+1,Q),-1,dtype=np.int32)
    for i,y in enumerate(cipher):
        b=np.full_like(a,-np.inf)
        ee=edges(key,cipher[i-1] if i else None,y,sign,q,channel,Q)
        if not ee:return [],[],-math.inf
        js=np.array([e[0] for e in ee]); ps=np.array([e[1] for e in ee])
        if i:
            candidates=a[js,:]+logL[:,ps].T
            rs=np.argmax(candidates,axis=1)
            vs=candidates[np.arange(len(ee)),rs]
        else:
            rs=np.zeros(len(ee),dtype=int)
            vs=np.where(js==off,logpi[ps],-np.inf)
        for idx,(j,p,h,w) in enumerate(ee):
            val=vs[idx]+w
            if val>b[h,p]:
                b[h,p]=val;links[i,h,p]=j*Q+rs[idx]
        a=b
    state=int(np.argmax(a)); value=float(a.flat[state])
    if not math.isfinite(value):return [],[],-math.inf
    plain,ptr=[],[]
    for i in range(n-1,-1,-1):
        j,p=divmod(state,Q);plain.append(p)
        state=int(links[i,j,p]);ptr.append(state//Q)
    return plain[::-1],ptr[::-1],value
