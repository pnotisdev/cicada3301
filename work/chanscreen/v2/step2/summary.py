"""Read-only delivery summary, NOT a campaign candidate/ranking script."""
from pathlib import Path
import json
HERE=Path(__file__).resolve().parent

def summary():
    gate=json.loads((HERE/'E3_proof.json').read_text())
    threshold=json.loads((HERE/'thresholds.json').read_text())
    old=json.loads((HERE.parent/'e2.json').read_text())
    sanity_serial=5*old['full_bank_seconds_cpu_per_window']['300']+3*old['full_bank_seconds_cpu_per_window']['600']
    plant_serial=100*sum(r['median_seconds'] for r in old['timings'] if r['m']==20000 and r['channel'] in ('hold','spend','skip5','coin'))
    return dict(E3_proof_status=gate['status'],E3_sanity='INCOMPLETE: blocked by proof failure',
        E4='INCOMPLETE: blocked by proof failure',E5='INCOMPLETE: review only, no queue',
        thresholds={n:{k:v for k,v in row.items() if k!='windows'} for n,row in threshold['inventory'].items()},
        thresholds_certified_for_common_null=False,
        counters=gate['matched_U'],real_bank_null_maxima=None,real_bank_gap=None,
        plants_completed=0,detection_and_identification=None,Viterbi_accuracy=None,
        wall_projections_hours=dict(sanity_5x300_3x600=sanity_serial/old['measured_speedup4']/3600,
            conditional_200_plants_at_20k_key_values_scoring_only=plant_serial/old['measured_speedup4']/3600,
            n300_82_window_campaign_four_workers=old['wall_hours_4']),
        estimate_caveats='Inherited v2 synthetic benchmark interpolation, not new timing. Traceback, export/checkpoints, model mismatch and contention extra/unknown.',
        resources=dict(proof_seconds=gate['seconds'],threads_used=1,GPU_compute_seconds=0,program_external_API_calls=0,session_cost='unknown'),
        no_LP2_search=True)

if __name__=='__main__':print(json.dumps(summary(),indent=2))
