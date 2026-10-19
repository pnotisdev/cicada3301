"""G1 CPU acceleration parity, fixed seeds; run only after G1 PASS."""
import os
for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[v]='1'
import hashlib
import json
import math
from pathlib import Path
import time
import numpy as np
import cpu
import reference as R

HERE=Path(__file__).resolve().parent


def check():
    rng=np.random.default_rng(1701)
    maxerr=0.; cells=0
    for idx in range(1000):
        Q=3 if idx%2 else 29
        n=(300 if idx==998 else 600) if idx>=998 else int(rng.integers(0,10))
        m=n+10 if idx>=998 else int(rng.integers(0,14))
        key=rng.integers(Q,size=m).tolist()
        c=rng.integers(Q,size=n).tolist()
        if idx%7==0: key=[0]*m
        pi=rng.random(Q); pi/=pi.sum()
        L=rng.random((Q,Q)); L/=L.sum(axis=1,keepdims=True)
        off=int(rng.integers(min(m+1,4)))
        sign=(-1,1)[idx%2]; q=(0.,.81,1.)[idx%3]
        ch=tuple(cpu.MODES)[idx%5] if idx<998 else 'hold'
        x=R.forward(c,key,off,sign,q,ch,pi,L)
        y=cpu.forward(c,key,off,sign,q,ch,pi,L)
        assert math.isfinite(x)==math.isfinite(y),(idx,x,y)
        if math.isfinite(x):
            err=abs(x-y); maxerr=max(maxerr,err)
            assert err<=1e-9,(idx,err)
        assert y.hex()==cpu.forward(c,key,off,sign,q,ch,pi,L).hex()
        cells+=1
    # Controlled additive case: score is ordinary known-plaintext LLR.
    Q=29; pi=np.arange(1,Q+1,dtype=float); pi/=pi.sum()
    L=np.tile(pi,(Q,1)); key=rng.integers(Q,size=400).tolist()
    p=rng.integers(Q,size=300).tolist(); c=[(x+key[i])%Q for i,x in enumerate(p)]
    expected=sum(math.log(pi[x]*Q) for x in p)
    v=R.score(c,key,0,1,0.,'hold',pi,L,engine=cpu.forward)
    assert abs(v['score']-expected)<1e-9
    benchmarks={}
    # Four channels, identical cells with proper L/U scoring, no exclusions.
    for ch in ('hold','spend','skip5','coin'):
        start=time.perf_counter(); checksum=0.
        for off in range(16):
            for sign in (-1,1):
                res=R.score(c,key,off,sign,.81,ch,pi,L,engine=cpu.forward)
                checksum+=res['score']
        sec=time.perf_counter()-start
        benchmarks[ch]=dict(cells=32,seconds=sec,cells_per_second=32/sec,checksum=checksum)
    return dict(status='PASS',cells=cells,max_log_error=maxerr,benchmark=benchmarks)

if __name__=='__main__':
    dest=HERE/'g1_cpu.json'
    if dest.exists(): raise SystemExit('Refusing to overwrite')
    assert json.loads((HERE/'g1.json').read_text())['status']=='PASS'
    t=time.perf_counter()
    try: res=check()
    except Exception as exc: res=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    res['seconds']=time.perf_counter()-t
    res['hashes']={x:hashlib.sha256((HERE/x).read_bytes()).hexdigest() for x in ('cpu.rs','cpu.py','check_cpu.py')}
    dest.write_text(json.dumps(res,indent=2)+'\n')
    print(json.dumps(res,indent=2))
    if res['status']!='PASS':raise SystemExit(1)
