"""Proposed additional guard, not adopted as the campaign acceptance rule."""
from proposal import score_common
import numpy as np
import math


def guarded(log_L,log_U,cipher,q,Q):
    l=np.asarray(log_L,dtype=np.float64);u=np.asarray(log_U,dtype=np.float64)
    if l.shape!=u.shape or np.isnan(u).any() or np.isposinf(u).any() or (u>1e-9).any():
        raise ValueError('invalid matched-U log probabilities')
    if np.any(np.isfinite(l)&np.isneginf(u)):raise ValueError('L support outside U')
    common,outside=score_common(l,cipher,q,Q)
    original=np.full_like(l,-math.inf)
    np.subtract(l,u,out=original,where=np.isfinite(u))
    return np.minimum(original,common),outside
