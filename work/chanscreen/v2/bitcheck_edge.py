"""Gate G2: backward_edge(kind=0) is bit-identical to backward.dll on the stored calibration/held records
(every bank stream, 5 channels, both signs, all offsets, q 0.81 and the record's frozen q). Also hashes the base dll.
    python -B bitcheck_edge.py [--records N]   -> bitcheck_edge.json
"""
import sys,json,hashlib,time
sys.dont_write_bytecode=True
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import numpy as np
from engine import all_offsets
from engine_edge import all_offsets_edge
model=np.load(HERE.parent/'model.npz');pi,L=model['pi'],model['L']
frozen=json.loads((HERE.parent/'frozen.json').read_text())['q']
files=sorted((HERE.parent/'raw'/'cal').glob('[0-9]*.json'))+sorted((HERE.parent/'raw'/'held').glob('[0-9]*.json'))
if '--records' in sys.argv:files=files[:int(sys.argv[sys.argv.index('--records')+1])]
t0=time.time();calls=0;cells=0;mismatch=0
for f in files:
    r=json.loads(f.read_text())
    ch0='m04' if r['channel']=='hold' else r['channel']
    qs={.81,float(frozen.get(f"{ch0}|{r['src']}|{r['kind']}",.81))}
    for key in r['bank']:
        for ch in ('hold','spend','skip','skip5','coin'):
            for s in (1,-1):
                for q in sorted(qs):
                    a=all_offsets(r['cipher'],key,s,q,ch,pi,L)
                    b=all_offsets_edge(r['cipher'],key,s,q,ch,pi,L,0)
                    calls+=1;cells+=len(a)
                    if a.tobytes()!=b.tobytes():mismatch+=1
out=dict(records=len(files),calls=calls,offset_cells=cells,byte_mismatches=mismatch,seconds=round(time.time()-t0,1),
         backward_dll_sha256=hashlib.sha256((HERE/'build'/'backward.dll').read_bytes()).hexdigest(),
         backward_rs_sha256=hashlib.sha256((HERE/'backward.rs').read_bytes()).hexdigest())
(HERE/'bitcheck_edge.json').write_text(json.dumps(out,indent=1));print(json.dumps(out,indent=1))
