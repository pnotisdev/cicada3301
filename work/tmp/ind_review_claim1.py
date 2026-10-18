"""Independent review, claim 1: is an affine OUTER alphabet sigma(x)=a*x+b redundant
for the IoC screen after the all-28-multiplier screen?

Rewritten from scratch (does not import or run work/independent code).
Model (per work/kscreen/RELABEL.md and MATH.md):
  inner  y_i = p_i + m0*k_{j_i}   (skip/coin anti-repeat on y)
  page   c_i = sigma(y_i) = a*y_i + b
Screen A: decode cA = sigma_inv(c) with multiplier m'  -> residual tA
Screen B: decode c           with multiplier m = a*m'  -> residual tB
Claim:   tB == sigma(tA) elementwise with identical pointer paths and arc
weights (all collision checks are equality tests, invariant under the bijection),
hence identical IoC, identical beam/Viterbi decisions, for every (a,b,m').
Counter-control: a non-affine permutation has no such multiplier for all (p,k).
"""
import random

Q = 29
Q_SKIP = 0.81


def arcs_of(ci, prev, key, j, mult, q):
    """Inverse-arcs of the skip/coin encryptor (same semantics as the kscreen
    engine: candidate ciphertext = p + mult*k_t; a draw equal to prev is
    re-drawn with probability q, otherwise accepted)."""
    import math
    accept = math.log1p(-q) if ci == prev else 0.0
    out = [(j + 1, (ci - mult * key[j]) % Q, accept)]
    if prev < 0 or q == 0:
        return out
    raw = (prev - mult * key[j]) % Q
    prob = math.log(q)
    for t in range(j + 1, len(key)):
        trial = (raw + mult * key[t]) % Q
        if trial == ci:
            out.append((t + 1, raw, prob + accept))
        if trial != prev:
            break
        prob += math.log(q)
    return out


def decode_path(cipher, key, mult, q=Q_SKIP):
    """Greedy max-weight single path: (plaintext per position, pointers)."""
    j, plain, ptrs = 0, [], []
    for i, ci in enumerate(cipher):
        prev = cipher[i - 1] if i else -1
        nj, p, w = max(arcs_of(ci, prev, key, j, mult, q), key=lambda a: a[2])
        plain.append(p)
        ptrs.append(nj)
        j = nj
    return plain, ptrs


def ioc(values):
    n = len(values)
    counts = [0] * Q
    for v in values:
        counts[v] += 1
    return sum(c * (c - 1) for c in counts) / (n * (n - 1) / Q)


def main():
    rng = random.Random(73301)
    plain = [rng.randrange(Q) for _ in range(150)]
    key = [rng.randrange(Q) for _ in range(1000)]
    m0 = 7  # inner multiplier, fixed at 7 here; also checked =1 earlier

    # forward encryptor: y = p + m0*k, skip rule on y vs previous output
    inner, j = [], 0
    for p in plain:
        while True:
            k = key[j]
            j += 1
            y = (p + m0 * k) % Q
            if not inner or y != inner[-1] or rng.random() >= Q_SKIP:
                break
        inner.append(y)

    # for every affine sigma and screen multiplier m' (1..28), compare screens
    checked = 0
    for a in range(1, Q):
        inv = pow(a, -1, Q)
        for b in range(Q):
            sigma = [(a * x + b) % Q for x in range(Q)]
            page = [sigma[y] for y in inner]
            relabelled = [inv * (c - b) % Q for c in page]  # = sigma_inv(page)
            assert relabelled == inner
            for mp in range(1, Q):
                m = (a * mp) % Q
                tA, ptrA = decode_path(relabelled, key, mp)
                tB, ptrB = decode_path(page, key, m)
                assert ptrA == ptrB, (a, b, mp)
                assert tB == [sigma[x] for x in tA], (a, b, mp)
                assert abs(ioc(tA) - ioc(tB)) < 1e-12
                # arc weights coincide pairwise (collision probabilities equal)
                for i in range(len(inner)):
                    pA = relabelled[i - 1] if i else -1
                    pB = page[i - 1] if i else -1
                    wA = sorted((nj, p, round(w, 12)) for nj, p, w in
                                arcs_of(relabelled[i], pA, key, ptrA[i - 1] if i else 0, mp, Q_SKIP))
                    wB = sorted((nj, p, round(w, 12)) for nj, p, w in
                                arcs_of(page[i], pB, key, ptrB[i - 1] if i else 0, m, Q_SKIP))
                    assert len(wA) == len(wB) and all(
                        wA[k][0] == wB[k][0] and wA[k][2] == wB[k][2] for k in range(len(wA)))
                checked += 1
    print(f"OK: tB == sigma(tA) elementwise, identical pointers and arc weights, "
          f"identical IoC for {checked} = 28*29*28 (a,b,m') settings (m0={m0})")

    # Atbash coverage by the two ordinary key signs {1,28}: a=28, m'=1 -> m=28;
    # m'=28 -> m=1.  (already included above; state it)
    print("OK: Atbash (a=28) is covered by screen multipliers {1,28} on the "
          "unrelabelled ciphertext (m = 28*m' mod 29 maps {1,28}->{28,1})")

    # Counter-control: bijective but non-affine swap of 0<->1.
    sigma = list(range(Q))
    sigma[0], sigma[1] = sigma[1], sigma[0]
    increments = {(sigma[(p + 1) % Q] - sigma[p]) % Q for p in range(Q)}
    works = [m for m in range(1, Q)
             if all((sigma[(p + k) % Q] - m * k) % Q == sigma[p]
                    for p in range(Q) for k in range(Q))]
    assert len(increments) > 1 and not works
    print(f"OK counter-control: swap sigma has increments {sorted(increments)}; "
          f"no m in 1..28 satisfies sigma(p+k) - m*k == sigma(p) for all p,k")
    print("CLAIM 1 CHECK PASSED")


if __name__ == "__main__":
    main()
