"""Measured throughput and length-only campaign inventory. NEVER scores LP2."""
import os
for x in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[x]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];V1=HERE.parent
import json,time,statistics,hashlib,concurrent.futures as CF
import numpy as np
from engine import all_offsets,MODES


def main():
    assert json.loads((HERE/'e1.json').read_text())['status']=='PASS'
    dest=HERE/'e2.json'
    if dest.exists() or (HERE/'e2.started').exists():raise SystemExit('E2 already attempted')
    (HERE/'e2.started').write_text('Frozen E2 benchmark attempt.\n')
    t0=time.perf_counter();cpu0=time.process_time()
    rng=np.random.default_rng(1702);model=np.load(V1/'model.npz');pi,L=model['pi'],model['L']
    timings=[];parallel=[];inputs={}
    for n in (300,600):
        for m in (2000,20000):
            key=rng.integers(29,size=m).tolist();c=[int(rng.integers(29))]
            for _ in range(n-1):
                y=int(rng.integers(28));y+=int(y>=c[-1])
                c.append(c[-1] if rng.random()<86/12947 else y)
            inputs[f'c_{n}_{m}']=np.array(c);inputs[f'k_{n}_{m}']=np.array(key)
            def call(ch,sign):
                start=time.perf_counter();cp=time.process_time()
                out=all_offsets(c,key,sign,.81,ch,pi,L)
                finite=out[np.isfinite(out)]
                return dict(wall=time.perf_counter()-start,cpu=time.process_time()-cp,checksum=float(finite.sum()))
            for ch in MODES:
                for sign in (-1,1):
                    warm=call(ch,sign)
                    repeats=[call(ch,sign) for _ in range(3)]
                    med=statistics.median(r['wall'] for r in repeats)
                    row=dict(n=n,m=m,channel=ch,sign=sign,warmup=warm,repeats=repeats,
                             median_seconds=med,passes_per_second=1/med,offsets_per_second=m/med)
                    timings.append(row)
                    print(n,m,ch,sign,round(med,6),flush=True)
                    # Checkpoint each completed timing, without overwriting earlier rows.
                    d=HERE/'e2_rows';d.mkdir(exist_ok=True)
                    with (d/f'{n}_{m}_{ch}_{sign}.json').open('x') as f:json.dump(row,f,indent=2)
            seq=sum(r['median_seconds'] for r in timings if r['n']==n and r['m']==m)
            for rep in range(3):
                start=time.perf_counter();cp=time.process_time()
                with CF.ThreadPoolExecutor(max_workers=4) as ex:
                    fs=[ex.submit(call,ch,s) for ch in MODES for s in (-1,1)]
                    checks=[f.result()['checksum'] for f in fs]
                wall=time.perf_counter()-start
                parallel.append(dict(n=n,m=m,rep=rep,wall=wall,cpu=time.process_time()-cp,
                                     tasks=10,speedup=seq/wall,checksums=checks))
    np.savez_compressed(HERE/'e2_inputs.npz',**inputs)
    # Read only metadata lengths, not decryptions. M04 library parser already reviewed.
    sys.path.insert(0,str(ROOT/'work/m04'));import m04
    library=m04.read_ksb(ROOT/'work/kscreen/data/library.ksb')
    assert len(library)==1439,('Unexpected real library size',len(library))
    import lp
    seg=lp.load_segments();lengths={str(i):len(lp.runes_of(seg[i])) for i in range(7,16)}
    windows={}
    for section,length in lengths.items():
        starts=list(range(0,length-300+1,150)) if length>=300 else []
        if starts and starts[-1]!=length-300:starts.append(length-300)
        windows[section]=starts
    speedup=statistics.median(x['speedup'] for x in parallel)
    per_window={}
    for n in (300,600):
        total=0.
        for _,key in library:
            m=len(key)
            for ch in ('hold','spend','skip5','coin'):
                for s in (-1,1):
                    vals={r['m']:r['median_seconds'] for r in timings if r['n']==n and r['channel']==ch and r['sign']==s}
                    estimate=vals[2000]*m/2000 if m<2000 else vals[2000]+(vals[20000]-vals[2000])*(m-2000)/18000
                    total+=max(0.,estimate)
        per_window[n]=total
    nw=sum(map(len,windows.values()));serial=per_window[300]*nw/3600
    res=dict(status='PASS',timings=timings,parallel=parallel,measured_speedup4=speedup,
             library_count=len(library),library_total_values=sum(len(k) for _,k in library),
             library_lengths=[len(k) for _,k in library],section_lengths=lengths,window_starts=windows,
             window_count=nw,normalized_passes=nw*len(library)*8,
             offset_cells=nw*sum(len(k) for _,k in library)*8,
             cpu_work_hours=serial,wall_hours_4=serial/speedup,
             wall_hours_14_extrapolated=serial/(speedup*14/4),
             full_bank_seconds_cpu_per_window=per_window,
             pilot30_each_length_cpu_hours=30*sum(per_window.values())/3600,
             full199_each_length_cpu_hours=199*sum(per_window.values())/3600,
             wall_seconds=time.perf_counter()-t0,cpu_seconds=time.process_time()-cpu0)
    res['gpu_plan_required']=res['wall_hours_14_extrapolated']>8
    res['hashes']={x:hashlib.sha256((HERE/x).read_bytes()).hexdigest() for x in ('E2_README.md','e2.py','backward.rs')}
    dest.write_text(json.dumps(res,indent=2)+'\n')
    print(json.dumps({k:v for k,v in res.items() if k not in ('timings','parallel','library_lengths','window_starts')},indent=2))

if __name__=='__main__':main()
