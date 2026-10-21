"""Float64 mid-word-null backward adapter (phase 51). Does not build or write on import.

all_offsets_mid(c,key,sign,q,ch,pi,L,kind,cand,nu,wstart): same output as engine.all_offsets ([log_L,log_U] per offset 0..m).
kind 0/1/2 = backward_edge (bit-identical to backward_edge.dll; cand as there), kind 3 = ONE keyless null at an interior position of a
word (prob nu per word of length >= 3, uniform over its Lc-2 interior slots); wstart[i]=1 marks the first rune of a word (position 0 always is).
"""
import ctypes as C
import os
from pathlib import Path
import numpy as np
MODES={'hold':0,'spend':1,'skip':2,'skip5':3,'coin':4}
LIB=None


def all_offsets_mid(c,key,sign,q,ch,pi,L,kind=0,cand=None,nu=0.0,wstart=None):
    global LIB
    pi=np.ascontiguousarray(pi,dtype=np.float64);L=np.ascontiguousarray(L,dtype=np.float64)
    c=np.ascontiguousarray(list(c),dtype=np.int32);key=np.ascontiguousarray(list(key),dtype=np.int32)
    Q=len(pi)
    if ch not in MODES or sign not in (-1,1) or not 0<=q<=1 or Q<2 or kind not in (0,1,2,3) or not 0<=nu<=1:raise ValueError('channel parameters')
    if kind and ch=='skip':raise ValueError('uncapped skip is not supported by the edge / mid-word arcs')
    if L.shape!=(Q,Q) or (c<0).any() or (c>=Q).any() or (key<0).any() or (key>=Q).any():raise ValueError('shape/runes')
    if (pi<0).any() or (L<0).any() or not np.isfinite(pi).all() or not np.isfinite(L).all():raise ValueError('model')
    if not np.isclose(pi.sum(),1,atol=1e-14,rtol=0) or not np.allclose(L.sum(1),1,atol=1e-14,rtol=0):raise ValueError('normalization')
    cd=np.zeros(max(len(c),1),dtype=np.uint8);wsd=np.zeros(max(len(c),1),dtype=np.uint8)
    if cand is not None:
        if len(cand)!=len(c):raise ValueError('cand length')
        cd[:len(c)]=np.asarray(cand,dtype=np.uint8)
    if wstart is not None:
        if len(wstart)!=len(c):raise ValueError('wstart length')
        wsd[:len(c)]=np.asarray(wstart,dtype=np.uint8)
    if kind==3 and wstart is None:raise ValueError('kind 3 needs wstart')
    if LIB is None:
        LIB=C.CDLL(str(Path(__file__).resolve().parent/'build'/('backward_mid.dll' if os.name=='nt' else 'libbackward_mid.so')))
        LIB.backward_mid.argtypes=[C.c_void_p,C.c_size_t,C.c_void_p,C.c_size_t,C.c_int,C.c_double,C.c_int,C.c_size_t,C.c_void_p,C.c_void_p,C.c_void_p,C.c_int,C.c_void_p,C.c_double,C.c_void_p]
        LIB.backward_mid.restype=C.c_int
    out=np.empty((len(key)+1,2),dtype=np.float64)
    rc=LIB.backward_mid(c.ctypes.data,len(c),key.ctypes.data,len(key),sign,q,MODES[ch],Q,pi.ctypes.data,L.ctypes.data,out.ctypes.data,kind,cd.ctypes.data,nu,wsd.ctypes.data)
    if rc:raise ValueError(f'backward_mid returned {rc}')
    return out
