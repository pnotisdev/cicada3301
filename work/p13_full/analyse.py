import json, glob, numpy as np
ld = lambda f: [json.loads(l) for l in open(f)]
real = ld('out_real.jsonl')[0]; S0 = real['max']
print('LP2: S = %.4f at para %d (308 runes = 14) p=%d; no-skip max %.4f; p13 para14: base %.4f skip %.4f' % (S0, real['para'], real['period'], real['base_max'], real['p14_13_base'], real['p14_13_skip']))
nul = {}
for m in ('perm', 'fresh'):
    r = ld('out_%s.jsonl' % m); s = np.array([x['max'] for x in r]); nul[m] = s
    b = np.array([x['base_max'] for x in r]); q = np.array([x['p14_13_skip'] for x in r])
    k = (s >= S0).sum()
    print('%s n=%d: S mean %.3f sd %.3f q50 %.3f q95 %.3f max %.3f | tail P(S>=LP2) = %d/%d = %.3f | arg max in (para14,p=13): %d | p14,p13 skip: mean %.3f max %.3f, >=1.7155: %d | no-skip max mean %.3f' % (
        m, len(s), s.mean(), s.std(), np.median(s), np.quantile(s, .95), s.max(), k, len(s), (k + 1) / (len(s) + 1), sum(x['para'] == 14 and x['period'] == 13 for x in r), q.mean(), q.max(), (q >= 1.7155).sum(), b.mean()))
    print('   arg max periods:', np.bincount([x['period'] for x in r], minlength=41)[30:41], '(p=30..40)', 'paras', np.bincount([x['para'] for x in r], minlength=15))
for f in sorted(glob.glob('out_plant*.jsonl')):
    r = ld(f)
    if not r: continue
    s = np.array([x['max'] for x in r])
    out = ['%s n=%d: S mean %.3f' % (f, len(r), s.mean())]
    for m in nul:
        thr = np.quantile(nul[m], .95); out.append('det>q95(%s %.3f) %d/%d' % (m, thr, (s > thr).sum(), len(s)))
    out.append('argmax at (14,13): %d/%d' % (sum(x['para'] == 14 and x['period'] == 13 for x in r), len(r)))
    out.append('p14,p13 skip IoC mean %.3f; >= LP2 S: %d' % (np.mean([x['p14_13_skip'] for x in r]), (s >= S0).sum()))
    # detection by the period-13 cell alone (a priori p): above the 95th percentile of the null p14,p13 values
    for m in ('fresh',):
        q = np.array([x['p14_13_skip'] for x in ld('out_%s.jsonl' % m)]); thr = np.quantile(q, .95)
        out.append('cell(14,13)-only det>q95(%s %.3f): %d/%d' % (m, thr, sum(x['p14_13_skip'] > thr for x in r), len(r)))
    print('; '.join(out))
