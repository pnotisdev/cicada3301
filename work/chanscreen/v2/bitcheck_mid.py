"""Gate G2 for the mid-word dll: backward_mid kind 0 == backward.dll, kinds 1/2 == backward_edge.dll (random word-edge masks), byte for byte;
kind 3 with nu = 0 against the base engine (reported as byte-equal or max |diff|). Stored calibration + held records, every STRIDE-th record, first BANK bank streams.
    python -B bitcheck_mid.py [--stride 5] [--bank 3]   -> bitcheck_mid.json"""
import sys,json,hashlib,time,random
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import numpy as np
from engine import all_offsets
from engine_edge import all_offsets_edge
from engine_mid import all_offsets_mid
model=np.load(HERE.parent/'model.npz');pi,L=model['pi'],model['L']
frozen=json.loads((HERE.parent/'frozen.json').read_text())['q']
files=sorted((HERE.parent/'raw'/'cal').glob('[0-9]*.json'))+sorted((HERE.parent/'raw'/'held').glob('[0-9]*.json'))
arg=lambda k,d:int(sys.argv[sys.argv.index(k)+1]) if k in sys.argv else d
stride,nbank=arg('--stride',5),arg('--bank',3)
files=files[::stride]
rng=random.Random(51)
t0=time.time();cnt=dict(base=0,edge1=0,edge2=0,mid_nu0=0);bad=dict(base=0,edge1=0,edge2=0,mid_nu0=0);maxdiff=0.;cells=0
for f in files:
    r=json.loads(f.read_text());c=r['cipher'];n=len(c)
    cand=[1 if rng.random()<.2 else 0 for _ in range(n)];ws=[1]+[1 if rng.random()<.18 else 0 for _ in range(n-1)]
    for key in r['bank'][:nbank]:
        for ch in ('hold','spend','skip','skip5','coin'):
            for s in (1,-1):
                a=all_offsets(c,key,s,.81,ch,pi,L)
                b=all_offsets_mid(c,key,s,.81,ch,pi,L,0)
                cnt['base']+=1;cells+=len(a);bad['base']+=a.tobytes()!=b.tobytes()
                if ch=='skip':continue
                for kind,nm in ((1,'edge1'),(2,'edge2')):
                    e=all_offsets_edge(c,key,s,.81,ch,pi,L,kind,cand,.42)
                    g=all_offsets_mid(c,key,s,.81,ch,pi,L,kind,cand,.42,ws)
                    cnt[nm]+=1;bad[nm]+=e.tobytes()!=g.tobytes()
                g=all_offsets_mid(c,key,s,.81,ch,pi,L,3,None,0.0,ws)
                cnt['mid_nu0']+=1
                if g.tobytes()!=a.tobytes():
                    bad['mid_nu0']+=1
                    fin=np.isfinite(a)&np.isfinite(g)
                    assert (np.isfinite(a)==np.isfinite(g)).all()
                    maxdiff=max(maxdiff,float(np.max(np.abs(a[fin]-g[fin]))) if fin.any() else 0.)
out=dict(records=len(files),stride=stride,bank_per_record=nbank,calls=cnt,byte_mismatches=bad,kind3_nu0_max_abs_diff=maxdiff,base_offset_cells=cells,seconds=round(time.time()-t0,1),
         sha256={p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in ('backward.rs','backward_edge.rs','backward_mid.rs','build/backward.dll','build/backward_edge.dll','build/backward_mid.dll')})
(HERE/'bitcheck_mid.json').write_text(json.dumps(out,indent=1));print(json.dumps(out,indent=1))
