"""Hash read-only dependencies before work; verify them without writing later."""
from pathlib import Path
import hashlib,json,sys
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]

def hashes():
    out={}
    for base in (ROOT/'work/chanscreen', ROOT/'work/m04'):
        for p in sorted(base.rglob('*')):
            if not p.is_file() or HERE in p.parents:continue
            h=hashlib.sha256()
            with p.open('rb') as f:
                for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
            out[p.relative_to(ROOT).as_posix()]=dict(sha256=h.hexdigest(),bytes=p.stat().st_size)
    return out

if __name__=='__main__':
    dest=HERE/'v1_m04_snapshot.json'
    if len(sys.argv)>1 and sys.argv[1]=='verify':
        old=json.loads(dest.read_text())['files'];new=hashes()
        changed=[x for x in old if old[x]!=new.get(x)]
        added=sorted(set(new)-set(old))
        print(json.dumps(dict(unchanged=not changed and not added,changed=changed,added=added,files=len(old))))
        sys.exit(bool(changed or added))
    with dest.open('x',encoding='utf-8') as f:
        json.dump(dict(utc=datetime.now(timezone.utc).isoformat(),files=hashes()),f,indent=2)
        f.write('\n')
    print('Recorded v1 + M04 snapshot')
