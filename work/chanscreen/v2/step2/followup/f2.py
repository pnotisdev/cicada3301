"""One-shot descriptive reuse of saved v1 scores; no new decoding or seeds."""
from proposal import score_common,log_common
from checkpoint import HERE,save,log
import json,math,time,hashlib
from collections import defaultdict
import numpy as np
V1=HERE.parents[2]


def finite(x):return float(x) if math.isfinite(x) else None


def run():
    T=json.loads((HERE.parent/'thresholds.json').read_text())['inventory']['300']['T_nats']
    records=[];passes=[];inputs={};arrays=[];groups=defaultdict(list)
    for i in range(380):
        path=V1/'raw/held'/f'{i:03d}.json';b=path.read_bytes();r=json.loads(b)
        inputs[f'work/chanscreen/raw/held/{i:03d}.json']=hashlib.sha256(b).hexdigest()
        assert len(r['cipher'])==300 and len(r['scores'])==1024
        old=np.array([x['score'] if x['score'] is not None else -math.inf for x in r['scores']])
        ll=np.array([x['log_L'] if x['log_L'] is not None else -math.inf for x in r['scores']])
        new,bad=score_common(ll,r['cipher'],.81,29);assert not bad
        arrays.append(np.column_stack((old,new)))
        typ=r['channel'] if r['with_key'] else 'null'
        row=dict(index=i,type=typ,source=r['src'],kind=r['kind'],true_offset=r['offset'] if r['with_key'] else None,
                 log_W_fixed_q81=log_common(r['cipher'],.81,29),old_max=finite(max(old)),proposed_max=finite(max(new)),
                 old_max_at_T=bool(max(old)>=T),proposed_max_at_T=bool(max(new)>=T))
        if r['with_key']:
            planted={'m04':'hold','skip':'skip5'}.get(r['channel'],r['channel'])
            truth=[j for j,c in enumerate(r['scores']) if (c['stream'],c['offset'],c['sign'],c['channel'])==(r['true_i'],r['offset'],1,planted)]
            assert len(truth)==1;truth=truth[0]
            row.update(old_true_score=finite(old[truth]),proposed_true_score=finite(new[truth]),
                       old_true_at_T=bool(old[truth]>=T),proposed_true_at_T=bool(new[truth]>=T))
            m=len(r['bank'][r['true_i']])
            for sign in (-1,1):
                for ch in ('hold','spend','skip5','coin'):
                    ids=[j for j,c in enumerate(r['scores']) if c['stream']==r['true_i'] and c['sign']==sign and c['channel']==ch and c['offset']!=r['offset']]
                    assert len(ids)==15
                    for name,scores in (('original',old),('proposed_common_W',new)):
                        counts={str(t):int(np.sum(scores[ids]>=t)) for t in (0,5,10)}
                        full={str(t):(m-1)*math.exp(-t) for t in (0,5,10)}
                        subset={str(t):15*math.exp(-t) for t in (0,5,10)}
                        passes.append(dict(record=i,type=typ,source=r['src'],kind=r['kind'],sign=sign,channel=ch,statistic=name,
                            full_wrong_cells=m-1,stored_wrong_cells=15,counts=counts,full_bounds=full,subset_bounds=subset,
                            full_pass_failure_proven={t:counts[t]>full[t] for t in counts},
                            stored_offsets=[r['scores'][j]['offset'] for j in ids],stored_scores=[finite(scores[j]) for j in ids]))
        records.append(row);groups[f'{typ}|{r["src"]}|{r["kind"]}'].append(row)
        if (i+1)%25==0 or i==379:
            a=(i//25)*25
            save(f'f2_records/{a:03d}_{i:03d}.json',records[a:i+1])
            save(f'f2_records/{a:03d}_{i:03d}_passes.json',[p for p in passes if a<=p['record']<=i])
            np.savez_compressed(HERE/f'f2_records/{a:03d}_{i:03d}_scores.npz',scores=np.array(arrays[a:i+1]))
            log(f'f2_checkpoint_{i:03d}',status='SAVED',records_completed=i+1,
                input_hashes={f'work/chanscreen/raw/held/{j:03d}.json':inputs[f'work/chanscreen/raw/held/{j:03d}.json'] for j in range(a,i+1)})
    save('f2_pass_counts.json',passes)
    np.savez_compressed(HERE/'f2_scores.npz',scores=np.array(arrays),columns=np.array(['original_S','proposed_S_W_fixed_q81']))
    save('f2_input_hashes.json',inputs)
    groupstats={}
    for group,rr in groups.items():
        groupstats[group]=dict(n=len(rr),old_max_at_T=sum(x['old_max_at_T'] for x in rr),proposed_max_at_T=sum(x['proposed_max_at_T'] for x in rr),
            old_true_at_T=sum(x.get('old_true_at_T',False) for x in rr) if rr[0]['type']!='null' else None,
            proposed_true_at_T=sum(x.get('proposed_true_at_T',False) for x in rr) if rr[0]['type']!='null' else None)
    summary={}
    for name in ('original','proposed_common_W'):
        pp=[p for p in passes if p['statistic']==name]
        summary[name]=dict(passes=len(pp),full_pass_failures_proven={str(t):sum(p['full_pass_failure_proven'][str(t)] for p in pp) for t in (0,5,10)},
            records_with_a_proven_failure={str(t):len({p['record'] for p in pp if p['full_pass_failure_proven'][str(t)]}) for t in (0,5,10)})
    nn=[r for r in records if r['type']=='null']
    return dict(status='COMPLETE_DESCRIPTIVE_AUDIT',records=380,positives=280,nulls=100,T300=T,
        groupstats=groupstats,wrong_offset_counts=summary,
        old_null_max=max(x['old_max'] for x in nn),proposed_null_max=max(x['proposed_max'] for x in nn),
        note='Reused small-bank held scores, source-specific original numerator q. NOT new held-out validation or full-bank null calibration.')

if __name__=='__main__':
    if (HERE/'f2.started').exists() or (HERE/'f2.json').exists():raise SystemExit('Already attempted; no retry')
    assert all(json.loads((HERE/f'f1_{m}.json').read_text())['status']=='PASS' for m in (0,1,2,3,'long'))
    save('f2.started',dict(protocol_sha256=hashlib.sha256((HERE/'PROTOCOL.md').read_bytes()).hexdigest(),source_sha256=hashlib.sha256((HERE/'f2.py').read_bytes()).hexdigest()))
    t=time.perf_counter()
    try:r=run()
    except Exception as exc:r=dict(status='FAIL',error=type(exc).__name__,detail=str(exc))
    r['seconds']=time.perf_counter()-t;save('f2.json',r);log('f2_complete',**r)
    print(json.dumps(r,indent=2))
    if r['status']=='FAIL':raise SystemExit(1)
