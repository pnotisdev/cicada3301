"""Frozen G2 adapter to read-only M04. Commands: init, train, cal START COUNT,
held START COUNT, threshold, summarize. One-shot task markers, <=4 workers.
"""
import os
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):
    os.environ[name]='1'
import sys
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
sys.path.insert(0,str(ROOT/'work'/'m04'))
import run_baseline as B
import m04 as M
import concurrent.futures as CF
import hashlib
import importlib.metadata
import json
import math
import random
import time
import numpy as np
import cpu
from reference import score
from reconstruct import viterbi

CHANNELS=('hold','spend','skip5','coin')


def dump(path,obj):
    path.write_text(json.dumps(obj,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def init():
    dest=HERE/'frozen.json'
    if dest.exists():raise RuntimeError('Already frozen')
    for g in ('g0','g1','g1_cpu'):
        assert json.loads((HERE/(g+'.json')).read_text())['status']=='PASS'
    pool=B.pool('train','english')
    pi=np.bincount(pool,minlength=29).astype(float)+.5;pi/=pi.sum()
    L=np.full((29,29),.5)
    np.add.at(L,(pool[:-1],pool[1:]),1)
    L/=L.sum(axis=1,keepdims=True)
    np.savez(HERE/'model.npz',pi=pi,L=L)
    inputs=['work/m04/m04.py','work/m04/run_baseline.py','results/analysis/m04_q_fit.json',
            'work/ref/emerson_essays1.txt','work/ref/lp_verified.txt','work/kscreen/data/library_flat.ksb']
    files=['README.md','reference.py','cpu.rs','cpu.py','reconstruct.py','power.py','channels.json','model.npz']
    manifest={str(Path('work/chanscreen')/x).replace(os.sep,'/'):digest(HERE/x) for x in files}
    manifest.update({x:digest(ROOT/x) for x in inputs})
    dump(dest,dict(protocol='v1',hashes=manifest,q=B.qfit(),training_runes=len(pool),
                   numpy=importlib.metadata.version('numpy'),python=sys.version.split()[0],threads=4))
    print('Frozen model and source hashes; no held-out evaluation')


def jobs(stage):
    if stage=='train':
        return [('m04',s,k,B.seed_of('chanscreen-train',s,k,i),'train',bool(i)) for s,k in B.STRATA for i in range(2)]
    if stage=='cal':
        return [('m04',s,k,B.seed_of('cal',s,k,i),'train',False) for s,k in B.STRATA for i in range(50)]
    return [(ch,s,k,B.seed_of('held',ch,s,k,yes,i),'held',yes)
            for ch,per,yes in (('m04',25,True),('spend',25,True),('skip',10,True),('coin',10,True),('m04',25,False))
            for s,k in B.STRATA for i in range(per)]


def one(stage,index,model,qfits):
    dest=HERE/'raw'/stage/f'{index:03d}.json'
    marker=dest.with_suffix('.started')
    marker.parent.mkdir(parents=True,exist_ok=True)
    with marker.open('x') as f:f.write('One-shot attempt. Do not rerun this seed.\n')
    ch,src,kind,seed,split,with_key=jobs(stage)[index]
    t=time.perf_counter()
    rng=random.Random(seed)
    plain,start=B.window(split,src,rng)
    drawn=[M.draw_stream(rng,kind) for _ in range(8)]
    true_i,off=rng.randrange(8),rng.randrange(M.OFFSETS)
    out,used,rep=B.encrypt(ch,plain,drawn[true_i][1],off,qfits.get(f'{ch}|{src}|{kind}',0.),rng)
    bank=drawn if with_key else [M.draw_stream(rng,kind) for _ in range(8)]
    pi,L=model
    rows=[]
    for ki,(_,key) in enumerate(bank):
        for o in range(16):
            for sign in (-1,1):
                for decoder in CHANNELS:
                    label={'hold':'m04'}.get(decoder,decoder)
                    q=qfits.get(f'{label}|{src}|{kind}',.81)
                    r=score(out,key,o,sign,q,decoder,pi,L,engine=cpu.forward)
                    rows.append(dict(stream=ki,offset=o,sign=sign,channel=decoder,**r))
    top=max(rows,key=lambda r:r['score'] if r['score'] is not None else -math.inf)
    rec=dict(stage=stage,index=index,seed=seed,channel=ch,src=src,kind=kind,with_key=with_key,
             window_start=start,true_i=true_i,offset=off,true_stream=drawn[true_i][0],
             period=M.period_of(drawn[true_i][1]),repairs=sum(rep),doublets=M.doublets(out),
             best=top['score'],argmax=top,bank_names=[b[0] for b in bank],
             plain=plain,cipher=out,bank=[list(k) for _,k in bank],used=used,repair_flags=rep,
             scores=rows)
    if with_key:
        dec={'m04':'hold','skip':'skip5'}.get(ch,ch)
        rec['true_cell']=next(r for r in rows if r['stream']==true_i and r['offset']==off and r['sign']==1 and r['channel']==dec)
        rec['identified_alias']=top['stream']==true_i and top['sign']==1 and abs(top['offset']-off)<=3
        rec['exact_offset']=top['stream']==true_i and top['sign']==1 and top['offset']==off
        rec['ties']=sum(abs(r['score']-top['score'])<=1e-9 for r in rows if r['score'] is not None)
        rec['aliases']=[r for r in rows if r['stream']==true_i and r['sign']==1 and abs(r['offset']-off)<=3 and r['score']>=top['score']-10]
        for label,cell in (('winner',top),('truth',rec['true_cell'])):
            q=qfits.get(f"{ {'hold':'m04'}.get(cell['channel'],cell['channel']) }|{src}|{kind}",.81)
            pp,jj,v=viterbi(out,bank[cell['stream']][1],cell['offset'],cell['sign'],q,cell['channel'],pi,L)
            rec[label+'_decode']=dict(plain=pp,pointers=jj,log_joint=v,
                accuracy=sum(a==b for a,b in zip(pp,plain))/len(plain))
    rec['seconds']=time.perf_counter()-t
    dump(dest,rec)
    print(f'{stage} {index} done {rec["seconds"]:.1f}s',flush=True)
    return rec['seconds']


def run(stage,start,count):
    frozen=json.loads((HERE/'frozen.json').read_text())
    for path,want in frozen['hashes'].items():
        assert digest(ROOT/path)==want,('frozen input changed',path)
    if stage=='held':assert (HERE/'threshold.json').exists()
    todo=range(start,start+count)
    assert 0<=start and start+count<=len(jobs(stage)) and count<=50
    for i in todo:
        assert not (HERE/'raw'/stage/f'{i:03d}.started').exists(),('already attempted',stage,i)
    model=np.load(HERE/'model.npz');data=(model['pi'],model['L'])
    # Populate shared read-only caches before worker threads; no racing pool/library loads.
    for _,s,k,_,split,_ in jobs(stage):B.pool(split,s)
    M.library()
    t=time.perf_counter()
    with CF.ThreadPoolExecutor(max_workers=4) as executor:
        fs=[executor.submit(one,stage,i,data,frozen['q']) for i in todo]
        for f in fs:f.result()
    dump(HERE/f'{stage}_{start}_{count}_timing.json',dict(seconds=time.perf_counter()-t,tasks=count,threads=4))


def records(stage):
    paths=[HERE/'raw'/stage/f'{i:03d}.json' for i in range(len(jobs(stage)))]
    assert all(p.exists() for p in paths),'Missing records; gate INCOMPLETE'
    return [json.loads(p.read_text()) for p in paths]


def threshold():
    dest=HERE/'threshold.json'
    if dest.exists():raise RuntimeError('Threshold already frozen')
    rr=records('cal');bests=sorted((r['best'] for r in rr),reverse=True)
    dump(dest,dict(threshold=bests[9],max=bests[0],median=float(np.median(bests)),n=200,
                   rule='10th largest of 200 matched maxima, 1024 cells each',null_bests=bests,
                   records_sha256={f"{r['index']:03d}":digest(HERE/'raw'/'cal'/f"{r['index']:03d}.json") for r in rr}))
    print('Frozen threshold',bests[9])


def summarize():
    dest=HERE/'g2.json'
    if dest.exists():raise RuntimeError('G2 artifact exists')
    rr=records('held');T=json.loads((HERE/'threshold.json').read_text())['threshold']
    stats={}
    for ch,yes in (('m04',True),('spend',True),('skip',True),('coin',True),('m04',False)):
        rs=[r for r in rr if r['channel']==ch and r['with_key']==yes]
        ds=[r for r in rs if r['best']>=T]
        row=dict(n=len(rs),detected=len(ds),by_stratum={f'{s}|{k}':sum(r['best']>=T for r in rs if r['src']==s and r['kind']==k) for s,k in B.STRATA})
        if yes:
            row.update(accurate_detected=sum(r['winner_decode']['accuracy']>=.95 for r in ds),
                mean_winner_accuracy=float(np.mean([r['winner_decode']['accuracy'] for r in rs])),
                mean_true_accuracy=float(np.mean([r['truth_decode']['accuracy'] for r in rs])),
                alias_identified=sum(r['identified_alias'] for r in rs),exact_identified=sum(r['exact_offset'] for r in rs))
        stats[ch if yes else 'null']=row
    m=stats['m04']
    conditions=dict(hold_total=m['detected']>=90,hold_strata=min(m['by_stratum'].values())>=20,
        hold_accuracy=m['accurate_detected']>m['detected']/2,null_size=stats['null']['detected']<=5,
        spend=stats['spend']['detected']>=90,skip=stats['skip']['detected']>=36,coin=stats['coin']['detected']>=36)
    res=dict(status='PASS' if all(conditions.values()) else 'FAIL',threshold=T,conditions=conditions,summary=stats,
             distinct_starts={s:len({r['window_start'] for r in rr if r['src']==s}) for s in ('cicada','english')})
    dump(dest,res);print(json.dumps(res,indent=2))

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd in ('init','threshold','summarize'):globals()[cmd]()
    elif cmd=='train':run('train',0,8)
    else:run(cmd,int(sys.argv[2]),int(sys.argv[3]))
