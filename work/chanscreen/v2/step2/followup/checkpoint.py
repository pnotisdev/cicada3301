"""Write-once checkpoints; all paths in records relative to repository."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[4]

def save(name,data):
    p=HERE/name;p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8',newline='\n') as f:
        json.dump(data,f,indent=2,allow_nan=False);f.write('\n')

def hashes():
    out={}
    for base in (ROOT/'work/chanscreen',ROOT/'work/m04'):
        for p in sorted(base.rglob('*')):
            if not p.is_file() or HERE in p.parents:continue
            h=hashlib.sha256()
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1048576),b''):h.update(b)
            out[p.relative_to(ROOT).as_posix()]=h.hexdigest()
    return out

def log(name,**data):save('checkpoints/'+name+'.json',dict(utc=datetime.now(timezone.utc).isoformat(),**data))

if __name__=='__main__':
    save('baseline.json',dict(utc=datetime.now(timezone.utc).isoformat(),files=hashes()))
    log('001_intake',status='SNAPSHOTTED',scope='Diagnostic follow-up only; failed E3 retained; original score unchanged',
        max_command_seconds=600,max_workers=4,gpu=False,elapsed_budget_hours=8)
    print('Snapshot and intake checkpoint saved')
