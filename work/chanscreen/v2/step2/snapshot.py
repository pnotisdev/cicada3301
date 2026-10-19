"""Read-only baseline SHA-256 inventory; exclude this new step2 tree."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib,json,sys
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]

def inventory():
    result={}
    for base in (ROOT/'work/chanscreen',ROOT/'work/m04'):
        for p in sorted(base.rglob('*')):
            if not p.is_file() or HERE in p.parents:continue
            h=hashlib.sha256()
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1048576),b''):h.update(b)
            result[p.relative_to(ROOT).as_posix()]={'sha256':h.hexdigest(),'bytes':p.stat().st_size}
    return result

if __name__=='__main__':
    dest=HERE/'baseline_sha256.json'
    if len(sys.argv)>1 and sys.argv[1]=='verify':
        old=json.loads(dest.read_text())['files'];new=inventory()
        changed=[p for p in old if old[p]!=new.get(p)];added=sorted(set(new)-set(old))
        r=dict(unchanged=not changed and not added,files=len(old),changed=changed,added=added)
        print(json.dumps(r));sys.exit(bool(changed or added))
    with dest.open('x') as f:json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),files=inventory()),f,indent=2)
    print('Recorded immutable baseline snapshot')
