"""Fixed-input E1 checkpoint runner. Commands: smoke | cal/held START COUNT |
random START COUNT | finish. No newly generated plant seeds. Raw arrays retained.
"""
import os
for x in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS'):os.environ[x]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent;V1=HERE.parent
sys.path.insert(0,str(V1))
import reference as dense
import cpu as oldcpu
import json,math,time,hashlib,itertools
import numpy as np
from fractions import Fraction as F
from engine import all_offsets,MODES
from sparse import backward_rational,backward_numpy
from e0 import models


def compare(a,b):
    assert np.array_equal(np.isfinite(a),np.isfinite(b)),'Support mismatch'
    mask=np.isfinite(a);err=float(np.max(np.abs(a[mask]-b[mask]),initial=0))
    good=np.all(np.isfinite(a),axis=1)
    serr=float(np.max(np.abs(np.diff(a[good],axis=1)-np.diff(b[good],axis=1)),initial=0))
    assert err<=1e-9 and serr<=1e-9,('Tolerance exceeded',err,serr)
    return err,serr


def smoke():
    ncell=0;err=0.
    for m in range(4):
        for key in itertools.product(range(3),repeat=m):
            for s,q,ch in itertools.product((-1,1),(0.,.6,1.),MODES):
                for c in itertools.product(range(3),repeat=3):
                    p,L=models()[1];u,UL=models()[0]
                    want=np.array([[math.log(x) if x else -math.inf for x in backward_rational(c,key,s,F(str(q)),ch,a,b)] for a,b in ((p,L),(u,UL))]).T
                    got=all_offsets(c,key,s,q,ch,np.array(p,float),np.array(L,float))
                    err=max(err,compare(want,got)[0]);ncell+=m+1
    # Adversarial inter-offset dynamic range, not a probabilistic power test.
    pi=np.array([.999999998,1e-9,1e-9]);L=np.tile(pi,(3,1));key=[0]*600+[1]*600;c=[0]*600
    logs=all_offsets(c,key,1,0.,'spend',pi,L)
    for o in (0,600):
        p=(c[0]-key[o])%3
        expected=600*math.log(pi[p]);assert abs(logs[o,0]-expected)<1e-9
    gap=logs[0,0]-logs[600,0];assert gap>1000 and np.isfinite(logs[[0,600]]).all()
    # NumPy log-space implementation and empty-input boundary.
    for ch in MODES:
        pi=np.full(3,1/3);L=np.full((3,3),1/3)
        for c,key in (([],[]),([0],[]),([0,1,1],[1,0,2,2,1,0,0,1])):
            a=all_offsets(c,key,-1,.81,ch,pi,L)
            b=backward_numpy(c,key,-1,.81,ch,pi,L)
            assert np.allclose(a[:,0],b,atol=1e-9,rtol=0)
    return dict(cells=ncell,max_log_error=err,offset_log_gap=gap)


def records(stage,start,count,dest):
    model=np.load(V1/'model.npz');pi,L=model['pi'],model['L']
    qfits=json.loads((V1/'frozen.json').read_text())['q'];T=json.loads((V1/'threshold.json').read_text())['threshold']
    metrics=[]
    for index in range(start,start+count):
        r=json.loads((V1/'raw'/stage/f'{index:03d}.json').read_text())
        expected=np.array([[s['log_L'],s['log_U']] for s in r['scores']]);got=np.empty_like(expected)
        for stream in range(8):
            for sign in (-1,1):
                for ch in ('hold','spend','skip5','coin'):
                    label='m04' if ch=='hold' else ch
                    q=qfits.get(f"{label}|{r['src']}|{r['kind']}",.81)
                    out=all_offsets(r['cipher'],r['bank'][stream],sign,q,ch,pi,L)
                    for j,cell in enumerate(r['scores']):
                        if (cell['stream'],cell['sign'],cell['channel'])==(stream,sign,ch):got[j]=out[cell['offset']]
        np.savez_compressed(dest/f'{index:03d}.npz',expected=expected,actual=got)
        e,se=compare(expected,got)
        wanted=np.array([s['score'] for s in r['scores']]);actual=got[:,0]-got[:,1]
        assert np.max(np.abs(actual-wanted))<=1e-9
        outside=np.abs(wanted-T)>1e-9
        assert np.array_equal(actual[outside]>=T,wanted[outside]>=T),'Threshold decision'
        metrics.append(dict(index=index,max_log_error=e,max_score_error=se,ambiguous=int(np.sum(~outside))))
        print(stage,index,'checked',flush=True)
    return dict(cells=1024*count,records=metrics)


def random_cells(start,count,dest):
    with np.load(V1/'gpu_parity.npz') as z:data={k:z[k] for k in z.files}
    model=np.load(V1/'model.npz');pi,L=model['pi'],model['L'];Q=len(pi)
    U=np.full(Q,1/Q);UL=np.full((Q,Q),1/Q)
    a=np.empty((count,2));b=a.copy();numpy_checks=0
    for t,i in enumerate(range(start,start+count)):
        c=data['cipher'][i,:data['n'][i]].tolist();key=data['key'][i,:data['m'][i]].tolist()
        off=int(data['offset'][i]);sign=int(data['sign'][i]);q=float(data['q'][i]);ch=tuple(MODES)[data['mode'][i]]
        a[t]=all_offsets(c,key,sign,q,ch,pi,L)[off]
        b[t]=[oldcpu.forward(c,key,off,sign,q,ch,p,l) for p,l in ((pi,L),(U,UL))]
        try:compare(a[t:t+1],b[t:t+1])
        except AssertionError:
            np.savez_compressed(dest/'failure.npz',index=i,actual=a[t],expected=b[t],cipher=c,key=key)
            raise
        if i<10 or i>=99500:
            ref=np.array([[dense.forward(c,key,off,sign,q,ch,p,l) for p,l in ((pi,L),(U,UL))]])
            compare(a[t:t+1],ref);numpy_checks+=1
    np.savez_compressed(dest/'arrays.npz',actual=a,expected=b,start=start)
    e,se=compare(a,b)
    return dict(cells=count,max_log_error=e,max_score_error=se,numpy_checks=numpy_checks)


def finish():
    parts=[json.loads(p.read_text()) for p in (HERE/'e1_parts').glob('*/result.json')]
    assert all(r['status']=='PASS' for r in parts)
    for stage,total in (('cal',200),('held',380),('random',100020)):
        indices=[i for r in parts if r['stage']==stage for i in range(r['start'],r['start']+r['count'])]
        assert sorted(indices)==list(range(total)),('Incomplete or duplicate',stage,len(indices))
    assert any(r['stage']=='smoke' for r in parts)
    return dict(status='PASS',cells=593920+100020,parts=len(parts),wall_seconds=sum(r['seconds'] for r in parts))

if __name__=='__main__':
    assert json.loads((HERE/'e0.json').read_text())['status']=='PASS'
    if (HERE/'e1_FAILED.json').exists():raise SystemExit('E1 failed: stopped')
    stage=sys.argv[1]
    if stage=='finish':
        r=finish()
        with (HERE/'e1.json').open('x') as f:json.dump(r,f,indent=2)
        print(r);sys.exit()
    start,count=(0,1) if stage=='smoke' else tuple(map(int,sys.argv[2:4]))
    dest=HERE/'e1_parts'/f'{stage}_{start}_{count}';dest.mkdir(parents=True,exist_ok=False)
    (dest/'started').write_text('One-shot block.\n')
    t=time.perf_counter()
    try:
        r=smoke() if stage=='smoke' else random_cells(start,count,dest) if stage=='random' else records(stage,start,count,dest)
        r['status']='PASS'
    except Exception as exc:r=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    r.update(stage=stage,start=start,count=count,seconds=time.perf_counter()-t)
    r['hashes']={x:hashlib.sha256((HERE/x).read_bytes()).hexdigest() for x in ('backward.rs','engine.py','e1.py')}
    (dest/'result.json').write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps(r,indent=2))
    if r['status']!='PASS':
        (HERE/'e1_FAILED.json').write_text(json.dumps(r,indent=2)+'\n');sys.exit(1)
