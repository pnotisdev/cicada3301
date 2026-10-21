import json, math, collections, sys
p = 2 / 29
def bsf(k, m): return sum(math.comb(m, j) * p**j * (1-p)**(m-j) for j in range(k, m+1))
recs = [json.loads(l) for l in open("work/mech48/rescore.jsonl")]
def isnull(r): return r["null"] or json.loads(r["key"])[0].startswith("rand:")
def opair(v):
    c = collections.Counter(v); return max(c[x] + c[(x+14) % 29] for x in range(29))
for r in recs:
    r["O"] = r["n_ai"] / r["n_one"]; r["p"] = bsf(r["n_ai"], r["n_one"]); r["op"] = opair(r["vals"]) / r["n_one"]
    r["fam"] = json.loads(r["key"])[0]; r["seg"] = json.loads(r["key"])[5]
for name, sel in (("real (non-null files, non-random families)", [r for r in recs if not isnull(r)]), ("null (null files / rand: families)", [r for r in recs if isnull(r)])):
    print(f"== {name}: {len(sel)} hits scored")
    if not sel: continue
    O = sorted(r["O"] for r in sel)
    print("  O mean %.4f median %.4f max %.3f; hits with O>=0.5: %d (n_one>=5: %d); min binomial p %.2e" % (
        sum(O)/len(O), O[len(O)//2], O[-1], sum(r["O"] >= .5 for r in sel), sum(r["O"] >= .5 and r["n_one"] >= 5 for r in sel), min(r["p"] for r in sel)))
    print("  expected mean under 2/29: %.4f" % p)
    print("  Opair mean %.3f max %.3f" % (sum(r["op"] for r in sel)/len(sel), max(r["op"] for r in sel)))
    by = collections.defaultdict(list)
    for r in sel: by[r["seg"]].append(r)
    for s in sorted(by, key=lambda s: int(s.split(".")[1])):
        b = max(by[s], key=lambda r: (r["O"], r["n_one"]))
        k = json.loads(b["key"])
        print(f"  {s}: n={len(by[s])} n_one={b['n_one']} best O={b['O']:.3f} ({b['n_ai']}/{b['n_one']}) p={b['p']:.1e} Opair={b['op']:.2f}  {k[0][:26]}|{k[1][:30]}|off {k[2]} m{k[3]} model{k[4]} ioc {b['ioc']:.3f}")
    top = sorted(sel, key=lambda r: (r["p"], -r["n_one"]))[:5]
    print("  five smallest p:", [(r["seg"], f'{r["n_ai"]}/{r["n_one"]}', f'{r["p"]:.1e}') for r in top])
    k = len(sel)
    print("  Bonferroni threshold with %d hits: p < %.1e" % (k, 0.05 / k))
