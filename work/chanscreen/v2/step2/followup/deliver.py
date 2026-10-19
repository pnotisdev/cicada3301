"""Write-once delivery records: originals unchanged, privacy scan, SHA-256 of this folder."""
from checkpoint import HERE,ROOT,save,hashes
import json,hashlib,getpass,platform,re

if __name__=='__main__':
    base=json.loads((HERE/'baseline.json').read_text())['files'];now=hashes()
    changed=sorted(p for p in base if now.get(p)!=base[p]);added=sorted(set(now)-set(base))
    save('immutability.json',dict(status='PASS' if not changed and not added else 'FAIL',files_checked=len(base),changed=changed,added=added))
    # names are read at run time so they never appear in a tracked file; .npz members are compressed, so this scans raw bytes only
    pats=[re.escape(x).encode() for x in (getpass.getuser(),platform.node(),str(ROOT),ROOT.as_posix()) if len(x)>=5]
    pats+=[rb'C:[\\/]+Users',rb'D:[\\/]+Github',rb'miniconda',rb'AppData']
    rx=re.compile(b'|'.join(pats),re.IGNORECASE);files=sorted(p for p in HERE.parent.rglob('*') if p.is_file() and p.name!='deliver.py')  # skip this file: it holds the patterns
    hits=[p.relative_to(ROOT).as_posix() for p in files if rx.search(p.read_bytes())]
    save('privacy_scan.json',dict(status='PASS' if not hits else 'FAIL',files_scanned=len(files),files_with_hits=hits))
    save('artifacts_sha256.json',{p.relative_to(HERE).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
         for p in sorted(HERE.rglob('*')) if p.is_file() and p.name!='artifacts_sha256.json' and '__pycache__' not in p.parts})
    print(json.loads((HERE/'immutability.json').read_text())['status'],json.loads((HERE/'privacy_scan.json').read_text()))
