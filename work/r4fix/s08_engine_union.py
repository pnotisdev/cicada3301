"""Float64 union-null backward adapter (R4 repair s08). Does not build or write on import.

all_offsets_union(c, key, sign, q, ch, pi, L, nu, wstart, place='any'): same output as engine_mid.all_offsets_mid ([log_L, log_U] per offset 0..m).
One keyless null per word with probability nu at a slot of the word's slot set: place 'any' = every cipher position 0..Lc-1 (Lc >= 2; the union arc),
'interior' = 1..Lc-2 (Lc >= 3; equals the mid arc, kind 3), 'edge' = {0, Lc-1} (diagnostic). wstart[i]=1 marks the first rune of a word (position 0 always is).
DLL: work/r4fix/build/backward_union.dll, built from work/r4fix/s08_backward_union.rs (rustc --crate-type cdylib -O).
"""
import ctypes as C
import os
from pathlib import Path
import numpy as np
MODES = {'hold': 0, 'spend': 1, 'skip': 2, 'skip5': 3, 'coin': 4}
PLACES = {'any': 0, 'interior': 1, 'edge': 2}
LIB = None


def all_offsets_union(c, key, sign, q, ch, pi, L, nu, wstart, place='any'):
    global LIB
    pi = np.ascontiguousarray(pi, dtype=np.float64)
    L = np.ascontiguousarray(L, dtype=np.float64)
    c = np.ascontiguousarray(list(c), dtype=np.int32)
    key = np.ascontiguousarray(list(key), dtype=np.int32)
    Q = len(pi)
    if ch not in MODES or sign not in (-1, 1) or not 0 <= q <= 1 or Q < 2 or place not in PLACES or not 0 <= nu <= 1:
        raise ValueError('channel parameters')
    if ch == 'skip':
        raise ValueError('uncapped skip is not supported by the union arc')
    if L.shape != (Q, Q) or (c < 0).any() or (c >= Q).any() or (key < 0).any() or (key >= Q).any():
        raise ValueError('shape/runes')
    if (pi < 0).any() or (L < 0).any() or not np.isfinite(pi).all() or not np.isfinite(L).all():
        raise ValueError('model')
    if not np.isclose(pi.sum(), 1, atol=1e-14, rtol=0) or not np.allclose(L.sum(1), 1, atol=1e-14, rtol=0):
        raise ValueError('normalization')
    if wstart is None or len(wstart) != len(c):
        raise ValueError('wstart length')
    wsd = np.zeros(max(len(c), 1), dtype=np.uint8)
    wsd[:len(c)] = np.asarray(wstart, dtype=np.uint8)
    if LIB is None:
        LIB = C.CDLL(str(Path(__file__).resolve().parent / 'build' / ('backward_union.dll' if os.name == 'nt' else 'libbackward_union.so')))
        LIB.backward_union.argtypes = [C.c_void_p, C.c_size_t, C.c_void_p, C.c_size_t, C.c_int, C.c_double, C.c_int, C.c_size_t, C.c_void_p, C.c_void_p, C.c_void_p,
                                       C.c_int, C.c_double, C.c_void_p]
        LIB.backward_union.restype = C.c_int
    out = np.empty((len(key) + 1, 2), dtype=np.float64)
    rc = LIB.backward_union(c.ctypes.data, len(c), key.ctypes.data, len(key), sign, q, MODES[ch], Q, pi.ctypes.data, L.ctypes.data, out.ctypes.data,
                            PLACES[place], nu, wsd.ctypes.data)
    if rc:
        raise ValueError(f'backward_union returned {rc}')
    return out
