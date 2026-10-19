"""One-shot G3. Protocol GPU_README.md. Saves arrays even on parity failure."""
import os
for v in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):
    os.environ[v]='1'
import sys
sys.dont_write_bytecode=True
import hashlib
import json
import math
from pathlib import Path
import random
import time
import numpy as np
import cpu
import gpu
from reference import score
HERE=Path(__file__).resolve().parent


def scrub(text):
    for token in (str(HERE.parent.parent),os.environ.get('USERPROFILE',''),os.environ.get('USERNAME',''),os.environ.get('COMPUTERNAME','')):
        if token:text=text.replace(token,'[redacted]')
    # Do not preserve stack traces or compiler installation paths in public logs.
    return text.splitlines()[0][:500]


def check():
    import cupy as cp
    props=cp.cuda.runtime.getDeviceProperties(0)
    assert props['major']>=6
    model=np.load(HERE/'model.npz');pi,L=model['pi'],model['L']
    rng=np.random.default_rng(1703)
    N=100020;cs=np.zeros((N,600),np.int32);ks=np.zeros((N,620),np.int32)
    ns=np.zeros(N,np.int32);ms=ns.copy();offs=ns.copy();signs=ns.copy();modes=ns.copy();qs=np.zeros(N)
    for i in range(100000):
        n=int(rng.integers(0,13)) if i<99500 else (300 if i%2==0 else 600)
        m=int(rng.integers(0,21)) if i<99500 else n+20
        ns[i]=n;ms[i]=m;offs[i]=int(rng.integers(m+1)) if i<99500 else i%16
        signs[i]=(-1,1)[i%2];qs[i]=(0.,.81,1.)[i%3] if i<99500 else .81;modes[i]=i%5
        cs[i,:n]=rng.integers(29,size=n);ks[i,:m]=rng.integers(29,size=m)
        if i%7==0:ks[i,:m]=0
    sys.path.insert(0,str(HERE.parent/'m04'))
    import run_baseline as B
    import m04 as M
    for j in range(20):
        i=100000+j;n=300;m=398
        prng=random.Random(170300+j)
        plain,_=B.window('train',('cicada','english')[j%2],prng)
        key=list(M.draw_stream(prng,'iid')[1]);off=j%16;sg=(-1,1)[j%2]
        ch=('hold','spend','skip5','coin')[j//5]
        if ch in ('hold','spend'):
            out=(M.enc_m04 if ch=='hold' else M.enc_spend)(plain,key,off,.81,prng,mult=sg)[0]
        else:out=(M.enc_skip if ch=='skip5' else M.enc_coin)(plain,key,off,prng,mult=sg)[0]
        ns[i]=n;ms[i]=m;offs[i]=off;signs[i]=sg;qs[i]=.81;modes[i]=cpu.MODES[ch]
        cs[i,:n]=out;ks[i,:m]=key
    cpuout=np.full((N,2),np.nan);gpuout=cpuout.copy();timings=[]
    status=dict(status='INCOMPLETE',completed=0)
    started=time.perf_counter();longwall=0.;longdevice=0.
    try:
        # Group short/long/positive ranges so short cells do not pay padded 620 slots.
        for lo,hi in ((0,99500),(99500,100000),(100000,N)):
            for start in range(lo,hi,128):
                stop=min(start+128,hi);sl=slice(start,stop)
                nc=max(1,int(ns[sl].max()));mc=max(1,int(ms[sl].max()))
                t=time.perf_counter()
                gout,secs=gpu.batch(np.ascontiguousarray(cs[sl,:nc]),np.ascontiguousarray(ks[sl,:mc]),
                    ns[sl],ms[sl],offs[sl],signs[sl],qs[sl],modes[sl],pi,L)
                wall=time.perf_counter()-t
                if lo==99500:longwall+=wall;longdevice+=sum(secs)
                timings.append(dict(start=start,stop=stop,wall=wall,kernel_seconds=secs))
                gpuout[sl]=gout
                for i in range(start,stop):
                    ch=tuple(cpu.MODES)[modes[i]]
                    r=score(cs[i,:ns[i]].tolist(),ks[i,:ms[i]].tolist(),int(offs[i]),int(signs[i]),
                            float(qs[i]),ch,pi,L,engine=cpu.forward)
                    cpuout[i]=[r['log_L'],r['log_U']]
                assert np.array_equal(np.isfinite(cpuout[sl]),np.isfinite(gout)),('support mismatch',start)
                mask=np.isfinite(gout)
                assert np.max(np.abs(cpuout[sl][mask]-gout[mask]),initial=0)<=1e-8,('log mismatch',start)
                good=np.all(mask,axis=1)
                assert np.max(np.abs(np.diff(cpuout[sl][good],axis=1)-np.diff(gout[good],axis=1)),initial=0)<=1e-8,('score mismatch',start)
                status['completed']=stop
            print(f'parity {hi}/{N}',flush=True)
        plants=gpuout[100000:,0]-gpuout[100000:,1]
        assert np.all(plants>0),('training plant nonpositive',plants.tolist())
        attrs=gpu._KERNEL.attributes
        finite=np.isfinite(cpuout)&np.isfinite(gpuout)
        maxerr=float(np.max(np.abs(cpuout[finite]-gpuout[finite])))
        # Upper bound: register allocation granularity/compiler spills can lower it.
        regs=int(attrs['num_regs']);smregs=int(props['regsPerMultiprocessor'])
        smshared=int(props['sharedMemPerMultiprocessor']);smthreads=int(props['maxThreadsPerMultiProcessor'])
        shared=int(attrs['shared_size_bytes'])
        blocks=min(smthreads//128,smregs//max(1,128*regs),smshared//max(1,shared),16)
        status.update(status='PASS',max_log_error=maxerr,plant_scores=plants.tolist(),
            device=dict(name=props['name'].decode(),cc=[props['major'],props['minor']],sms=props['multiProcessorCount'],
                        memory_bytes=props['totalGlobalMem']),kernel_attributes=attrs,
            theoretical_occupancy_upper_bound=blocks*128/smthreads,
            occupancy_note='resource bound, not measured achieved occupancy; block granularity may lower it',
            long_cells=500,long_wall_seconds=longwall,long_kernel_seconds=longdevice,
            long_cells_per_second_wall=500/longwall,long_cells_per_second_device=500/longdevice,
            max_launch_seconds=max(max(t['kernel_seconds']) for t in timings),cupy=cp.__version__)
    except Exception as e:
        status.update(status='FAIL',error=type(e).__name__,detail=scrub(str(e)))
    finally:
        np.savez_compressed(HERE/'gpu_parity.npz',cipher=cs,key=ks,n=ns,m=ms,offset=offs,sign=signs,q=qs,
                            mode=modes,cpu=cpuout,gpu=gpuout)
        status['seconds']=time.perf_counter()-started
        status['device_seconds']=sum(sum(t['kernel_seconds']) for t in timings)
        status['timings']=timings
    return status

if __name__=='__main__':
    dest=HERE/'g3.json'
    if dest.exists() or (HERE/'g3.started').exists():raise SystemExit('G3 already attempted')
    assert json.loads((HERE/'g2.json').read_text())['status']=='PASS'
    (HERE/'g3.started').write_text('One-shot gate; do not retry after failure.\n')
    t=time.perf_counter()
    try:res=check()
    except Exception as e:res=dict(status='FAIL',error=type(e).__name__,detail=scrub(str(e)),seconds=time.perf_counter()-t)
    res['hashes']={x:hashlib.sha256((HERE/x).read_bytes()).hexdigest() for x in ('GPU_README.md','forward.cu','gpu.py','check_gpu.py')}
    dest.write_text(json.dumps(res,indent=2)+'\n')
    print(json.dumps({k:v for k,v in res.items() if k!='timings'},indent=2))
    if res['status']!='PASS':raise SystemExit(1)
