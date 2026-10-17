"""H10 of docs/HYPOTHESES.md: is LP2 a small 29-state machine with no external key?

    python work/state_machines.py            # about 10 minutes; writes results/analysis/state_machines.txt

Model: c_i = E(x_i, S_i), S_(i+1) = F(S_i, x_i, c_i), S in Z29, x the plaintext rune (after any fixed substitution).
  E (9): x = c - t(S), c + t(S) or t(S) - c, with t in {S, prime(S) mod 29, prime(S)-1 mod 29} (Gematria prime of index S).
  F (512): linear S' = a*u(S) + b*x + g*c + d with u in {S, prime, prime-1, S^2}, a, b, g in {0, 1, 2, 28}, d in {0, 1}
           (not a = b = g = 0); and the products (S + e1)(x + e2), (S + e1)(c + e2), e1, e2 in {0, 1}.
Every (F, E) and every start state S0 is decoded on each LP2 section (S0 free per section, so a machine running across
sections is included) and scored by the IoC of the decoded runes, which ignores any substitution of the plaintext.
A machine with a fixed state is a plain shift (IoC ~1.8 on LP2: excluded long ago) and is left out.

Controls: English sections enciphered with random machines (recovered as the best (F, E) with IoC near 1.8); the same
with the anti-repeat skip (on a collision the state advances once more and the rune is re-enciphered, keep 0.18), for a
machine driven by the ciphertext only (S' = g*c + d: it resynchronises after a skip) and one with memory (it does not:
the decoder has no skip model, which is the limit of this test); null: LP2's runes shuffled inside each section.
"""
import itertools
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402
import sim  # noqa: E402
import stats  # noqa: E402

N = 29
S_ = np.arange(N)
U = np.array([S_, np.array(lp.PRIME) % N, (np.array(lp.PRIME) - 1) % N, S_ * S_ % N], dtype=np.int32)
U_NAMES = ["S", "prime(S)", "prime(S)-1", "S^2"]
COEF = (0, 1, 2, 28)


def machines():
    F = [(0, u, a, b, g, d, 0, 0) for u, a, b, g, d in itertools.product(range(4), COEF, COEF, COEF, (0, 1))
         if (a, b, g) != (0, 0, 0)]
    F += [(k, 0, 0, 0, 0, 0, e1, e2) for k in (1, 2) for e1 in (0, 1) for e2 in (0, 1)]
    E = [(t, fc, ft) for t in range(3) for fc, ft in ((1, -1), (1, 1), (-1, 1))]
    return F, E


def f_name(f):
    k, u, a, b, g, d, e1, e2 = f
    if k == 1:
        return f"S'=(S+{e1})(x+{e2})"
    if k == 2:
        return f"S'=(S+{e1})(c+{e2})"
    return f"S'={a}*{U_NAMES[u]}+{b}*x+{g}*c+{d}"


def e_name(e):
    t, fc, ft = e
    tn = ["S", "prime(S)", "prime(S)-1"][t]
    return {(1, -1): f"x=c-{tn}", (1, 1): f"x=c+{tn}", (-1, 1): f"x={tn}-c"}[(fc, ft)]


def tables(F, E):
    """per-configuration parameter arrays; configuration = (F index, E index, S0)"""
    grid = np.array([(fi, ei, s0) for fi in range(len(F)) for ei in range(len(E)) for s0 in range(N)], dtype=np.int32)
    f = np.array(F, dtype=np.int32)[grid[:, 0]]
    e = np.array(E, dtype=np.int32)[grid[:, 1]]
    return grid, f.T, e.T


def decode(c, F, E, prm=None):
    """IoC of the decoded runes for every configuration, shape (len(F), len(E), 29)"""
    grid, (k, u, a, b, g, d, e1, e2), (t, fc, ft) = prm or tables(F, E)
    S = grid[:, 2].copy()
    cnt = np.zeros(len(S) * N, dtype=np.int32)
    base = np.arange(len(S), dtype=np.int64) * N
    lin, prod = k == 0, k == 1
    for ci in c:
        x = (fc * ci + ft * U[t, S]) % N
        cnt[base + x] += 1
        nl = (a * U[u, S] + b * x + g * ci + d) % N
        nx = (S + e1) * (x + e2) % N
        nc = (S + e1) * (ci + e2) % N
        S = np.where(lin, nl, np.where(prod, nx, nc)).astype(np.int32)
    cnt = cnt.reshape(-1, N).astype(np.int64)
    n = len(c)
    return (N * (cnt * (cnt - 1)).sum(1) / (n * (n - 1))).reshape(len(F), len(E), N)


def encrypt(p, f, e, s0, keep=1.0, rng=None):
    k, u, a, b, g, d, e1, e2 = f
    t, fc, ft = e

    def enc(x, S):                      # invert x = fc*c + ft*t(S)
        return (fc * (x - ft * U[t, S])) % N

    def step(S, x, c):
        if k == 0:
            return (a * U[u, S] + b * x + g * c + d) % N
        return (S + e1) * ((x if k == 1 else c) + e2) % N

    S, out, prev = s0, [], -1
    for x in p:
        c = enc(x, S)
        tries = 0
        while c == prev and keep < 1.0 and rng.random() >= keep and tries < 5:
            S = step(S, x, c)                       # the rejected rune still feeds the state
            c = enc(x, S)
            tries += 1
        out.append(int(c))
        S = step(S, x, c)
        prev = c
    return out


def sections():
    return [(f"0.{i}", lp.runes_of(stats.SEGS[i])) for i in stats.UNSOLVED if len(lp.runes_of(stats.SEGS[i])) >= 100]


def score(secs, F, E, prm):
    """best S0 per section, then the mean over sections: shape (len(F), len(E)); plus the per-section maxima"""
    per = np.stack([decode(c, F, E, prm).max(axis=2) for _, c in secs])
    return per.mean(axis=0), per


def report_best(label, secs, F, E, prm, top=5):
    mean, per = score(secs, F, E, prm)
    order = np.argsort(mean, axis=None)[::-1][:top]
    lines = [f"{label}: best mean IoC over {len(secs)} sections {mean.max():.4f}; best single section {per.max():.4f}"]
    for o in order:
        fi, ei = np.unravel_index(o, mean.shape)
        lines.append(f"    {mean[fi, ei]:.4f}  {f_name(F[fi])}  {e_name(E[ei])}  per section "
                     + " ".join(f"{v:.3f}" for v in per[:, fi, ei]))
    return lines, mean, per


def viterbi(c, F, E, cfg, logp):
    """Best log-likelihood path over the 29 states, per (F, E) in cfg, with the anti-repeat skip modelled exactly:
    a skip at rune i means the encryptor's first try equalled c_(i-1), so x = E^-1(c_(i-1), S), the state advanced once
    with that rejected rune, and the second try gave c_i (checked). Start state free. Returns the best score per config."""
    K = len(cfg)
    f = np.array([F[i] for i, _ in cfg], dtype=np.int32).repeat(N, axis=0).T
    e = np.array([E[j] for _, j in cfg], dtype=np.int32).repeat(N, axis=0).T
    k, u, a, b, g, d, e1, e2 = f
    t, fc, ft = e
    S = np.tile(np.arange(N, dtype=np.int32), K)
    kb = np.arange(K, dtype=np.int64).repeat(N) * N
    lin, prod = k == 0, k == 1
    ln, ls = np.log(0.972), np.log(0.028)

    def einv(cv, s):
        return (fc * cv + ft * U[t, s]) % N

    def step(s, x, cv):
        return np.where(lin, (a * U[u, s] + b * x + g * cv + d) % N,
                        np.where(prod, (s + e1) * (x + e2) % N, (s + e1) * (cv + e2) % N))

    V = np.zeros(K * N)
    prev = -1
    for ci in c:
        Vn = np.full(K * N, -np.inf)
        x0 = einv(ci, S)
        np.maximum.at(Vn, kb + step(S, x0, ci), V + logp[x0] + ln)
        if prev >= 0:
            xs = einv(prev, S)
            s1 = step(S, xs, prev)
            ok = (einv(ci, s1) == xs) & np.isfinite(V)
            np.maximum.at(Vn, (kb + step(s1, xs, ci))[ok], (V + logp[xs] + ls)[ok])
        V, prev = Vn, ci
    return V.reshape(K, N).max(axis=1)


def avoid_repeat_runes(n, rng, keep=0.18):
    out, prev = [], -1
    for _ in range(n):
        y = rng.randrange(N)
        while y == prev and rng.random() >= keep:
            y = rng.randrange(N)
        out.append(y)
        prev = y
    return out


def main_viterbi():
    """--viterbi: the machines WITH memory (they do not resynchronise after a skip), scored by English rune log-likelihood"""
    F, E = machines()
    cfg = [(i, j) for i, f in enumerate(F) if not (f[0] == 0 and f[2] == 0) for j in range(len(E))]
    eng = np.bincount(sim.english_runes(), minlength=N) / len(sim.english_runes())
    logp = np.log(eng)
    secs = sections()
    rng = random.Random(1033)

    def run(label, ss):
        tot = sum(viterbi(c, F, E, cfg, logp) for _, c in ss)
        n = sum(len(c) for _, c in ss)
        o = np.argsort(tot)[::-1][:3]
        return tot / n, [f"{label}: best {tot[o[0]] / n:.4f} nats per rune; next "
                         + ", ".join(f"{tot[x] / n:.4f} ({f_name(F[cfg[x][0]])} {e_name(E[cfg[x][1]])})" for x in o[:3])]

    out = [f"H10 with the anti-repeat skip modelled: {len(cfg)} machines with memory (a != 0 or a product) x 29 states, "
           f"Viterbi on each LP2 section, English rune log-likelihood (English text: {float(eng @ logp):.4f} nats per rune; "
           f"uniform runes: {float(np.log(eng).mean()):.4f})", ""]
    lp2, lines = run("LP2", secs)
    out += lines
    null, lines = run("null (random runes with LP2's avoid-repeat rate, same section lengths)",
                      [(n, avoid_repeat_runes(len(c), rng)) for n, c in secs])
    out += lines
    plain = [int(x) for line in open(os.path.join(HERE, "phpmt", "data", "english.txt"), encoding="utf-8")
             if line.startswith("R ") for x in line.split()[1:]]
    ok = True
    for r in range(3):
        ci = rng.randrange(len(cfg))
        fi, ei = cfg[ci]
        enc = encrypt(plain, F[fi], E[ei], rng.randrange(N), 0.18, rng)
        sc = viterbi(enc, F, E, cfg, logp) / len(enc)
        good = sc.argmax() == ci or sc.max() - sc[ci] < 1e-9
        ok &= bool(good) and sc[ci] > null.max() + 0.2
        out.append(f"  {'PASS' if good else 'FAIL'}  planted with skips (keep 0.18) {f_name(F[fi])} {e_name(E[ei])}: "
                   f"{sc[ci]:.4f} nats per rune, best {sc.max():.4f}")
    verdict = "CANDIDATE - inspect" if lp2.max() > null.max() + 0.1 else "NULL"
    out += ["", f"controls {'PASSED' if ok else 'FAILED'}; LP2 best {lp2.max():.4f} against null {null.max():.4f}; verdict: {verdict}"]
    text = "\n".join(out) + "\n"
    print(text)
    with open(os.path.join(os.path.dirname(HERE), "results", "analysis", "state_machines_skip.txt"), "w", newline="\n",
              encoding="utf-8") as fh:
        fh.write(text)
    return 0 if ok else 1


def main():
    if "--viterbi" in sys.argv:
        return main_viterbi()
    F, E = machines()
    prm = tables(F, E)
    secs = sections()
    out = [f"H10 29-state machines: {len(F)} state updates x {len(E)} cipher rules x 29 start states, "
           f"{len(F) * len(E) * N:,} decodes per section, {len(secs)} LP2 sections ({sum(len(c) for _, c in secs)} runes)", ""]
    lines, mean, per = report_best("LP2", secs, F, E, prm)
    out += lines
    rng = random.Random(3301)
    nulls = []
    for r in range(2):
        shuf = [(n, rng.sample(c, len(c))) for n, c in secs]
        lines, m, pr = report_best(f"null {r + 1} (LP2 runes shuffled inside sections)", shuf, F, E, prm, top=1)
        out += lines
        nulls.append((m.max(), pr.max()))
    eng = sim.english_runes()
    pos, ok = 0, True
    plain = []
    for _, c in secs:
        plain.append(eng[pos:pos + len(c)])
        pos += len(c)
    cases = [("no skip", None, 1.0), ("no skip", None, 1.0), ("no skip", None, 1.0),
             ("skip, memoryless (a = 0)", "memoryless", 0.18), ("skip, with memory", "memory", 0.18)]
    out.append("")
    out.append("Positive controls (English sections enciphered with a machine of the family, random S0 per section):")
    for name, kind, keep in cases:
        while True:
            fi, ei = rng.randrange(len(F)), rng.randrange(len(E))
            f = F[fi]
            if kind == "memoryless" and not (f[0] == 0 and f[2] == 0 and f[3] == 0 and f[4] != 0):
                continue                                         # S' = g*c + d: driven by the ciphertext only, self-synchronising
            if kind == "memory" and not (f[0] == 0 and f[2] != 0):
                continue
            break
        enc = [(n, encrypt(p, F[fi], E[ei], rng.randrange(N), keep, rng)) for (n, _), p in zip(secs, plain)]
        mean_c, per_c = score(enc, F, E, prm)
        bf, be = np.unravel_index(mean_c.argmax(), mean_c.shape)
        found = (bf, be) == (fi, ei) or mean_c[bf, be] - mean_c[fi, ei] < 1e-9
        good = found and mean_c[fi, ei] >= 1.6
        if kind != "memory":
            ok &= good
        out.append(f"  {'PASS' if good else ('info' if kind == 'memory' else 'FAIL')}  {name}: planted {f_name(F[fi])} {e_name(E[ei])}: "
                   f"its mean IoC {mean_c[fi, ei]:.3f}; best {mean_c.max():.3f} ({f_name(F[bf])} {e_name(E[be])})")
    nm = max(x for x, _ in nulls)
    verdict = "CANDIDATE - inspect" if mean.max() > max(nm + 0.05, 1.3) else "NULL (LP2 is inside the shuffled-null range)"
    out += ["", f"controls {'PASSED' if ok else 'FAILED'}; LP2 best mean {mean.max():.4f} against shuffled nulls "
                f"{', '.join(f'{x:.4f}' for x, _ in nulls)}; verdict: {verdict}"]
    text = "\n".join(out) + "\n"
    print(text)
    path = os.path.join(os.path.dirname(HERE), "results", "analysis", "state_machines.txt")
    with open(path, "w", newline="\n", encoding="utf-8") as fh:
        fh.write(text)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
