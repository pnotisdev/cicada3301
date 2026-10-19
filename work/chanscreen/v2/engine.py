"""Float64 sparse log-DP Rust adapter. Does not build or write on import."""
import ctypes as C
import os
from pathlib import Path
import numpy as np
MODES={'hold':0,'spend':1,'skip':2,'skip5':3,'coin':4}
LIB=None


def all_offsets(c,key,sign,q,ch,pi,L):
    global LIB
    pi=np.ascontiguousarray(pi,dtype=np.float64);L=np.ascontiguousarray(L,dtype=np.float64)
    c=np.ascontiguousarray(list(c),dtype=np.int32);key=np.ascontiguousarray(list(key),dtype=np.int32)
    Q=len(pi)
    if ch not in MODES or sign not in (-1,1) or not 0<=q<=1 or Q<2:raise ValueError('channel parameters')
    if L.shape!=(Q,Q) or (c<0).any() or (c>=Q).any() or (key<0).any() or (key>=Q).any():raise ValueError('shape/runes')
    if (pi<0).any() or (L<0).any() or not np.isfinite(pi).all() or not np.isfinite(L).all():raise ValueError('model')
    if not np.isclose(pi.sum(),1,atol=1e-14,rtol=0) or not np.allclose(L.sum(1),1,atol=1e-14,rtol=0):raise ValueError('normalization')
    if LIB is None:
        LIB=C.CDLL(str(Path(__file__).resolve().parent/'build'/('backward.dll' if os.name=='nt' else 'libbackward.so')))
        LIB.backward.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_int,C.c_double,C.c_int,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p]
        LIB.backward.restype=None
    out=np.empty((len(key)+1,2),dtype=np.float64)
    LIB.backward(c.ctypes.data,len(c),key.ctypes.data,len(key),sign,q,MODES[ch],Q,pi.ctypes.data,L.ctypes.data,out.ctypes.data)
    return out
