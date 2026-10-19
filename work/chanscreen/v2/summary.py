"""Read-only result summary and budget calculations; never scores ciphertext."""
from pathlib import Path
import json,statistics
HERE=Path(__file__).resolve().parent


def summarize():
    e2=json.loads((HERE/'e2.json').read_text())
    parts=[json.loads(p.read_text()) for p in (HERE/'e1_parts').glob('*/result.json')]
    errs=[r for p in parts for r in p.get('records',[])]+[p for p in parts if p['stage']=='random']
    rate=[]
    for n in (300,600):
        for m in (2000,20000):
            for ch in ('hold','spend','skip','skip5','coin'):
                sec=statistics.median(r['median_seconds'] for r in e2['timings'] if (r['n'],r['m'],r['channel'])==(n,m,ch))
                rate.append(dict(n=n,m=m,channel=ch,seconds=sec,passes_per_second=1/sec,offsets_per_second=m/sec))
    return dict(E0='PASS',E1='PASS',E2='PASS',E3='INCOMPLETE',E4='INCOMPLETE',E5='INCOMPLETE',
        max_regression_log_error=max(r['max_log_error'] for r in errs),
        max_regression_score_error=max(r['max_score_error'] for r in errs),
        threshold_ambiguous_cells=sum(r.get('ambiguous',0) for r in errs),
        parity_cells=json.loads((HERE/'e1.json').read_text())['cells'],
        benchmark_rows=rate,library_windows=e2['window_count'],library_offset_cells=e2['offset_cells'],
        campaign_work_cpu_hours=e2['cpu_work_hours'],campaign_wall_hours_4=e2['wall_hours_4'],
        campaign_wall_hours_14_extrapolated=e2['wall_hours_14_extrapolated'],
        pilot30_n300_work_cpu_hours=30*e2['full_bank_seconds_cpu_per_window']['300']/3600,
        pilot30_each_length_work_cpu_hours=e2['pilot30_each_length_cpu_hours'],
        calibration199_each_length_work_cpu_hours=e2['full199_each_length_cpu_hours'],
        plant200_work_cpu_hours=100*sum(e2['full_bank_seconds_cpu_per_window'].values())/3600,
        E1_single_worker_wall_seconds=sum(p['seconds'] for p in parts),E2_process_cpu_seconds=e2['cpu_seconds'],
        GPU_seconds=0,numeric_real_bank_threshold='unknown',library_scale_power='unknown')

if __name__=='__main__':print(json.dumps(summarize(),indent=2))
