"""EXPERIMENTAL common-W score; not an adopted replacement for frozen S."""
import os
for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[v]='1'
import math,numbers
import numpy as np


def log_common(cipher,q,Q):
    c=np.asarray(cipher)
    if not isinstance(Q,numbers.Integral) or Q<2 or not math.isfinite(q) or not 0<=q<=1:
        raise ValueError('invalid null parameters')
    if c.ndim!=1 or (c.size and not np.issubdtype(c.dtype,np.integer)):
        raise ValueError('cipher must be a one-dimensional integer sequence')
    if np.any(c<0) or np.any(c>=Q):raise ValueError('cipher rune out of range')
    n=len(c)
    if not n:return 0.0
    repeat=int(np.count_nonzero(c[1:]==c[:-1]))
    if q==1 and repeat:return -math.inf
    out=-n*math.log(Q)+(n-1-repeat)*math.log1p(q/(Q-1))
    if repeat:out+=repeat*math.log1p(-q)
    return out


def score_common(log_L,cipher,q,Q):
    """Return proposed scores and outside-W-support flag, without inf-inf."""
    x=np.asarray(log_L,dtype=np.float64)
    if np.isnan(x).any() or np.isposinf(x).any() or (x>1e-9).any():
        raise ValueError('invalid log probability')
    w=log_common(cipher,q,Q)
    if w==-math.inf:return np.full_like(x,-math.inf),True
    return x-w,False
