"""Pin SHA-256 of the edge engine, adapter, reference, tests and plant code (phase 24); writes results/chanscreen/edge/pins.json."""
import hashlib, json, sys
from pathlib import Path
H = Path(__file__).resolve().parent
V2 = H.parent
files = ['backward.rs', 'build/backward.dll', 'backward_edge.rs', 'build/backward_edge.dll', 'engine_edge.py', 'reference_edge.py', 'test_edge.py', 'test_edge_scale.py',
         'bitcheck_edge.py', 'bitcheck_edge.json', 'step4/plant_edge.py', 'step4/ladder_edge.py', 'step4/null_scan_edge.py', 'step4/hit_rule.py', 'step4/lp_mask.py', 'step4/cost.py']
out = {f: hashlib.sha256((V2 / f).read_bytes()).hexdigest() for f in files if (V2 / f).exists()}
dest = V2.parent.parent.parent / 'results' / 'chanscreen' / 'edge' / 'pins.json'
dest.parent.mkdir(parents=True, exist_ok=True)
dest.write_text(json.dumps(out, indent=1)); print(json.dumps(out, indent=1))
