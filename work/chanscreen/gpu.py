"""Correctness-first CuPy port; no automatic CPU fallback."""
import os
from pathlib import Path
HERE=Path(__file__).resolve().parent
os.environ['CUPY_CACHE_DIR']=str(HERE/'build'/'cupy_cache')
import numpy as np
_KERNEL=None


def batch(c,k,n,m,o,sign,q,mode,pi,L):
    import cupy as cp
    global _KERNEL
    if _KERNEL is None:
        _KERNEL=cp.RawKernel((HERE/'forward.cu').read_text(),'forward',
                             options=('--std=c++14','--fmad=false'))
    N,NC=c.shape;MC=k.shape[1];Q=len(pi)
    assert N<=128 and c.dtype==k.dtype==np.int32
    args=[cp.asarray(x) for x in (c,k,n,m,o,sign,q,mode)]
    gp,gl=cp.asarray(pi),cp.asarray(L)
    a=cp.empty((N,MC+1,Q),cp.float64);b=cp.empty_like(a)
    out=cp.empty(N,cp.float64)
    outputs=[];seconds=[]
    for uniform in (0,1):
        begin,end=cp.cuda.Event(),cp.cuda.Event()
        begin.record()
        _KERNEL((N,),(128,),(*args,np.int32(NC),np.int32(MC),np.int32(Q),
                            gp,gl,np.int32(uniform),a,b,out))
        end.record();end.synchronize()
        sec=cp.cuda.get_elapsed_time(begin,end)/1000
        seconds.append(sec);outputs.append(out.get())
        assert sec<1.0,('TDR safety launch >=1s',sec)
    return np.stack(outputs,axis=1),seconds
