"""ctypes adapter, no auto-build or downloads. Validation before entering Rust."""
import ctypes as C
from pathlib import Path
import os
import numpy as np
from reference import validate

MODES = {'hold':0,'spend':1,'skip':2,'skip5':3,'coin':4}
_LIB = None


def forward(cipher,key,off,sign,q,channel,pi,L):
    global _LIB
    pi=np.ascontiguousarray(pi,dtype=np.float64)
    L=np.ascontiguousarray(L,dtype=np.float64)
    validate(cipher,key,off,sign,q,channel,pi,L)
    if _LIB is None:
        path=Path(__file__).resolve().parent/'build'/('cpu.dll' if os.name=='nt' else 'libcpu.so')
        _LIB=C.CDLL(str(path))
        _LIB.likelihood.restype=C.c_double
        _LIB.likelihood.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,
            C.c_size_t,C.c_int,C.c_double,C.c_int,C.c_size_t,C.c_void_p,C.c_void_p]
    c=np.ascontiguousarray(cipher,dtype=np.int32)
    k=np.ascontiguousarray(key,dtype=np.int32)
    return _LIB.likelihood(c.ctypes.data,len(c),k.ctypes.data,len(k),off,sign,q,
                           MODES[channel],len(pi),pi.ctypes.data,L.ctypes.data)
