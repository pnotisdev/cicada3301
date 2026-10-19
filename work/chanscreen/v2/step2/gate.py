"""One-shot E3' proof prerequisite. A false common-null claim is a FAIL."""
from pathlib import Path
import json,time,hashlib
from bounds import matched_grid,small_counterexample,long_event,key_dependence,F
HERE=Path(__file__).resolve().parent


def run(thresholds):
    matched=matched_grid()
    tiny=small_counterexample()
    tails=[long_event(3,2,1,n,F(81,100),thresholds['inventory'][str(n)]['LR_threshold_integer']) for n in (300,600)]
    tails.append(long_event(29,26,3,300,F(81,100),thresholds['inventory']['300']['LR_threshold_integer']))
    gaps=key_dependence()
    fail=not tiny['common_bound_pass'] or any(r['common_bound_refuted'] for r in tails)
    return dict(status='FAIL' if fail else 'PASS',reason='Common anti-repeat null substituted for a finite-key hold null' if fail else None,
                matched_U=matched,small_counterexample=tiny,long_event_checks=tails,skip_coin_key_dependence=gaps,
                real_bank_null_windows_completed=0,plants_completed=0,
                note='Counterexamples test the normalization-only theorem, not actual English-LM FWER.')

if __name__=='__main__':
    dest=HERE/'E3_proof.json'
    if dest.exists() or (HERE/'E3_proof.started').exists():raise SystemExit('Proof gate already attempted; no retry')
    threshold=json.loads((HERE/'thresholds.json').read_text())
    (HERE/'E3_proof.started').write_text('One-shot deterministic proof audit.\n')
    t=time.perf_counter()
    try:r=run(threshold)
    except Exception as exc:r=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    r['seconds']=time.perf_counter()-t
    r['hashes']={p:hashlib.sha256((HERE/p).read_bytes()).hexdigest() for p in ('README.md','PROOF.md','bounds.py','gate.py','thresholds.json')}
    dest.write_text(json.dumps(r,indent=2)+'\n')
    print('E3 proof:',r['status'],'seconds',r['seconds'])
    print('Reason:',r.get('reason',r.get('detail')))
    if 'matched_U' in r:print('Cell-matched controls:',r['matched_U'])
    if r['status']!='PASS':raise SystemExit(1)
