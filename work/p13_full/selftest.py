import pipe, numpy as np, itertools, time
rng = np.random.default_rng(1)
def brute(d, p):
    best = pipe.base_ioc(d, p)
    for v in range(29):
        pos = [i for i in range(1, len(d)) if d[i] == v]
        for k in range(1, min(5, len(pos)) + 1):
            for sk in itertools.combinations(pos, k):
                best = max(best, pipe.ioc_skip(d, np.array(sk, np.int64), k, p))
    return best
# 1. table value == direct value
d = rng.integers(0, 29, 90).astype(np.int64)
for p in (3, 7, 13):
    P = pipe.build_tables(d, p, min(p, 6)); mx = 0
    for _ in range(200):
        k = rng.integers(0, 6); sk = np.sort(rng.choice(np.arange(1, 90), k, replace=False)).astype(np.int64)
        mx = max(mx, abs(pipe.eval_sk(P, p, 90, sk, k) - pipe.ioc_skip(d, sk, k, p)))
    print('table vs direct max abs diff p=%d: %.2e' % (p, mx))
# 2. exact == brute on small streams (skewed alphabet so subsets matter)
for t in range(6):
    d = rng.integers(0, 8, 60).astype(np.int64); p = int(rng.choice([2, 5, 8, 13]))
    print('exact vs brute', p, pipe.exact_best(d, p), brute(d, p))
# 3. greedy vs exact, L=308 fresh null deltas, p=13 and others
t = time.time(); agree = 0; gaps = []
for _ in range(20):
    d = rng.integers(1, 29, 308).astype(np.int64); p = int(rng.choice(np.arange(2, 41)))
    e = pipe.exact_best(d, p); g = pipe.greedy_best(d, p); gaps.append(e - g); agree += abs(e - g) < 1e-12
print('greedy==exact on %d/20, mean gap %.3f max gap %.3f' % (agree, np.mean(gaps), np.max(gaps)), time.time() - t)
