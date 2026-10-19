"""Freeze threshold inventory without evaluating any ciphertext likelihood."""
from pathlib import Path
from fractions import Fraction as F
import json,math,hashlib
HERE=Path(__file__).resolve().parent

def make():
    base=json.loads((HERE.parent/'e2.json').read_text())
    lengths=base['section_lengths'];data={}
    assert base['library_count']==1439
    assert sum(base['library_lengths'])==base['library_total_values']
    for n in (300,600):
        windows={}
        for section,length in lengths.items():
            starts=list(range(0,length-n+1,150)) if length>=n else []
            if starts and starts[-1]!=length-n:starts.append(length-n)
            windows[section]=starts
        nw=sum(map(len,windows.values()))
        N=nw*base['library_total_values']*8
        if n==300:
            assert nw==82 and N==base['offset_cells'] and windows==base['window_starts']
        data[str(n)]=dict(windows=windows,window_count=nw,N_cells=N,LR_threshold_integer=N*1000,
                         T_nats=math.log(N*1000),per_cell_bound=str(F(1,N*1000)))
    return dict(alpha_per_length='1/1000',inventory=data,validity='PROPOSED; proof gate pending',
                source_sha256=hashlib.sha256((HERE.parent/'e2.json').read_bytes()).hexdigest(),
                README_sha256=hashlib.sha256((HERE/'README.md').read_bytes()).hexdigest())

if __name__=='__main__':
    r=make()
    with (HERE/'thresholds.json').open('x') as f:json.dump(r,f,indent=2);f.write('\n')
    print(json.dumps(r,indent=2))
