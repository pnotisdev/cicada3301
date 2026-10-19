"""Read-only audit/summary. Does not evaluate a single cipher cell or alter gates."""
import hashlib
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def audit():
    frozen=json.loads((HERE/'frozen.json').read_text())
    for path,want in frozen['hashes'].items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==want,path
    T=json.loads((HERE/'threshold.json').read_text())['threshold']
    counts={};scores=0;held=[]
    for stage,want in (('train',8),('cal',200),('held',380)):
        paths=sorted((HERE/'raw'/stage).glob('*.json'))
        assert len(paths)==want,(stage,len(paths))
        counts[stage]=len(paths)
        for i,p in enumerate(paths):
            r=json.loads(p.read_text())
            assert r['index']==i and r['stage']==stage
            assert len(r['scores'])==1024
            assert len({(s['stream'],s['offset'],s['sign'],s['channel']) for s in r['scores']})==1024
            assert max(s['score'] for s in r['scores'])==r['best']
            assert len(r['bank'])==8 and all(len(k)==398 for k in r['bank'])
            assert len(r['plain'])==len(r['cipher'])==300
            scores+=len(r['scores'])
            if stage=='held':held.append(r)
    for i,want in json.loads((HERE/'threshold.json').read_text())['records_sha256'].items():
        assert hashlib.sha256((HERE/'raw'/'cal'/(i+'.json')).read_bytes()).hexdigest()==want
    summary=json.loads((HERE/'g2.json').read_text())
    for ch,yes in (('m04',True),('spend',True),('skip',True),('coin',True),('m04',False)):
        rs=[r for r in held if r['channel']==ch and r['with_key']==yes]
        expected=summary['summary'][ch if yes else 'null']
        assert sum(r['best']>=T for r in rs)==expected['detected']
        if yes:
            assert sum(r['best']>=T and r['winner_decode']['accuracy']>=.95 for r in rs)==expected['accurate_detected']
    times={s:sum(json.loads(p.read_text())['seconds'] for p in HERE.glob(s+'_*_timing.json')) for s in counts}
    rate=200*1024/times['cal']
    return dict(status='PASS',records=counts,scored_cells=scores,batch_wall_seconds=times,
                calibration_cells_per_second_4_workers=rate,
                optimistic_2e8_cells_cpu_hours=2e8/rate/3600,
                optimistic_8e8_cells_cpu_hours=8e8/rate/3600,
                gates={g:json.loads((HERE/(g+'.json')).read_text())['status'] for g in ('g0','g1','g1_cpu','g2','g3')})

if __name__=='__main__':print(json.dumps(audit(),indent=2))
