"""Exploratory (post hoc, after the main run): per-cell exact IoC for the two exactly-searched paragraphs (3 = 333 runes, 14 = 308 runes) x
periods 2..40, for LP2 and nulls; min-p over those 78 cells (empirical p per cell from the pooled null of the same model)."""
import sys, json, numpy as np, run, pipe
def cells(s):
    return np.array([[pipe.exact_best(pipe.deltas(s[g]), int(p)) for p in pipe.PERIODS] for g in (3, 14)])
if __name__ == '__main__':
    model, n = sys.argv[1], int(sys.argv[2]); out = []
    for i in range(n):
        rng = np.random.default_rng([{'perm': 1, 'fresh': 2}[model], i])
        s = run.perm_stream(rng) if model == 'perm' else run.fresh_stream(rng)
        out.append(cells(s).tolist())
    json.dump(out, open('cells_%s.json' % model, 'w'))
    if model == 'perm': json.dump(cells(run.paras).tolist(), open('cells_real.json', 'w'))
