"""sign_rules gate: per-word +/- sign of the key from word-level numbers (112 rules).

Run: python run.py   (Windows: run.bat)
"""
import os
import random
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import common  # noqa: E402
from common import N, PRIME, ioc, encrypt_anti, decode_beam, totient_key, words_of, \
    print_verdict

# ---------------------------------------------------------------- rules

def word_quantities(words):
    """Per word: [n, G, R, f, l, F, L, w, wp, ws]."""
    qs = []
    w = wp = ws = 0
    for runes, clause_end in words:
        n = len(runes)
        G = sum(PRIME[x] for x in runes)
        R = sum(runes)
        f, l = runes[0], runes[-1]
        F, L = PRIME[f], PRIME[l]
        w += 1
        wp += 1
        ws += 1
        qs.append([n, G, R, f, l, F, L, w, wp, ws])
        if clause_end:
            ws = 0
    return qs


def build_rules():
    """The 112 sign rules as (name, fn) pairs; fn = None for 'rising' rules,
    which compare against the previous word and are handled in signs_for."""
    rules = []

    def add(name, fn):
        rules.append((name, fn))
        rules.append((name + " (inverse)", None if fn is None else (lambda q, _f=fn: -_f(q))))

    def parity(name, idx):
        add(name, lambda q, i=idx: +1 if q[i] % 2 == 0 else -1)

    def modp(name, idx, p):
        add(name, lambda q, i=idx, p=p: +1 if q[i] % p <= (p - 1) // 2 else -1)

    names = ["n", "G", "R", "f", "l", "F", "L", "w", "wp", "ws"]
    for i, nm in enumerate(names):
        parity(f"parity({nm})", i)
        for p in (3, 5, 7):
            modp(f"mod{p}({nm})", i, p)
    modp("mod29(G)", 1, 29)
    modp("mod29(R)", 2, 29)
    for i, nm in enumerate(names[:7] + names[8:]):  # w excluded (its diff is constant 1)
        idx = i if i < 7 else i + 1
        add(f"rising({nm})", None)
    add("first<last", lambda q: +1 if q[3] < q[4] else -1)
    add("F<L", lambda q: +1 if q[5] < q[6] else -1)
    for t in (3, 4, 5):
        add(f"n>={t}", lambda q, t=t: +1 if q[0] >= t else -1)
    return rules


def signs_for(words, qs, rule):
    """Per-word signs for a rule; 'rising' rules use the previous word's quantity."""
    name = rule[0]
    inv = "inverse" in name
    if name.startswith("rising"):
        base = name.replace(" (inverse)", "")
        idx = {"rising(n)": 0, "rising(G)": 1, "rising(R)": 2, "rising(f)": 3, "rising(l)": 4,
               "rising(F)": 5, "rising(L)": 6, "rising(wp)": 8, "rising(ws)": 9}[base]
        out = [+1]
        for i in range(1, len(qs)):
            out.append(+1 if qs[i][idx] > qs[i - 1][idx] else -1)
        return [-s for s in out] if inv else out
    return [(-rule[1](q)) if inv else rule[1](q) for q in qs]


def run_lp2_info():
    """Informational: sign balance of each rule over LP2's real words."""
    segs = common.lp.load_segments()
    cl = []
    cur = []
    for s in range(7, 16):
        for t in segs[s] + [" "]:
            if isinstance(t, int):
                cur.append(t)
            elif t == ".":
                if cur:
                    cl.append((cur, True))
                    cur = []
            elif t in ("\n", "%"):
                continue
            elif cur:
                cl.append((cur, False))
                cur = []
    qs = word_quantities(cl)
    rules = build_rules()
    bal = []
    for name, fn in rules:
        if name.startswith("rising"):
            continue
        ss = [fn(q) for q in qs]
        bal.append((sum(1 for s in ss if s > 0) / len(ss), name))
    bal.sort()
    print("LP2 informational: sign balance (fraction +1) extremes over %d words:" % len(cl))
    for frac, name in bal[:4] + bal[-4:]:
        print("   %.3f  %s" % (frac, name))


def main():
    print("=" * 72)
    print("sign_rules gate: per-word +/- key sign from word-level numbers (112 rules)")
    print("=" * 72)
    rng = random.Random(20261017)
    words = common.cap_words(words_of(common.CORPUS_B))
    plain = [x for w, _ in words for x in w]
    qs = word_quantities(words)
    key = totient_key(len(plain) * 2)
    rules = build_rules()

    # Plant: pick one rule, sign the key per word, encrypt with anti-repeat skip.
    plant_name, plant_fn = rules[rng.randrange(len(rules))]
    signs = signs_for(words, qs, (plant_name, plant_fn))
    signed = []
    wi = 0
    for (runes, _), s in zip(words, signs):
        signed.extend([(key[wi + j] * s) % N for j in range(len(runes))])
        wi += len(runes)
    c = encrypt_anti(plain, signed, rng=rng)
    print("planted rule: %s" % plant_name)

    # Control 1: plain key (no signs) must fail: with half the words flipped it
    # recovers only ~half the text (IoC ~1.35-1.45), so 'blind' means < 1.5 here.
    blind = decode_beam(c, key)
    ioc_blind = ioc(blind)
    print("blind decode (un-signed key):        IoC %.3f  (must be < 1.5)" % ioc_blind)

    # Control 2: scan all 112 rules; the planted one must rank #1.
    best = []
    for name, fn in rules:
        ss = signs_for(words, qs, (name, fn))
        sk = []
        wi = 0
        for (runes, _), s in zip(words, ss):
            sk.extend([(key[wi + j] * s) % N for j in range(len(runes))])
            wi += len(runes)
        dec = decode_beam(c, sk)
        best.append((ioc(dec), name))
    best.sort(reverse=True)
    top = best[:5]
    for v, nm in top:
        print("rule scan: IoC %.3f  %s" % (v, nm))
    rank = [nm for _, nm in best].index(plant_name) + 1
    print("planted rule rank: %d of %d, IoC %.3f" % (rank, len(rules), best[0][0]))

    # Control 3: null (random per-word signs, no rule) must not reach 1.5.
    null_max = 0.0
    for _ in range(5):
        ss = [rng.choice([+1, -1]) for _ in words]
        sk = []
        wi = 0
        for (runes, _), s in zip(words, ss):
            sk.extend([(key[wi + j] * s) % N for j in range(len(runes))])
            wi += len(runes)
        null_max = max(null_max, ioc(decode_beam(c, sk)))
    print("null (random signs, 5 draws):        max IoC %.3f  (must be < 1.5)" % null_max)

    ok = (ioc_blind < 1.5) and (rank == 1 and best[0][0] >= 1.5 and best[0][0] >= ioc_blind + 0.4) \
        and (null_max < 1.5)
    run_lp2_info()
    return print_verdict("sign_rules", ok,
                         "blind %.2f / planted rank %d IoC %.2f / null %.2f" %
                         (ioc_blind, rank, best[0][0], null_max))


if __name__ == "__main__":
    sys.exit(main())
