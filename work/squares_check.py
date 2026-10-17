"""Verification of number facts about the two magic squares of the book (0.2 grid, constant 1033; 0.6 / page 14 square, constant 3301), claimed by an outside LLM on 2026-10-17. Facts only; what they mean is
in work/log/phase10_squares.md.

    python work/squares_check.py          # -> results/analysis/squares_check.txt
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import lp  # noqa: E402

OUT = []


def say(s=""):
    print(s)
    OUT.append(s)


def sieve(n):
    s = bytearray([1]) * (n + 1)
    s[0:2] = b"\x00\x00"
    for i in range(2, int(n ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    return [i for i in range(n + 1) if s[i]]


P = sieve(60000)


def phi(n):
    r, m = n, n
    for p in P:
        if p * p > m:
            break
        if m % p == 0:
            while m % p == 0:
                m //= p
            r -= r // p
    return r - r // m if m > 1 else r


def grid(v):
    return [v[i * 5:(i + 1) * 5] for i in range(5)]


def main():
    segs = lp.load_segments()

    def nums(seg):
        return [int(t[1:]) for t in segs[seg] if isinstance(t, str) and t.startswith("#") and t[1:].isdigit()]

    sq6 = nums(6)[:25]
    vals, cur = [], []
    for t in segs[2] + [" "]:
        if isinstance(t, int):
            cur.append(t)
        else:
            if cur:
                vals.append(sum(lp.PRIME[x] for x in cur))
                cur = []
            if t.startswith("#"):
                vals.append(int(t[1:]))
    sq2 = vals[-25:]
    say("The two squares (0.2: the last 25 values of the page, Gematria sums of words and numbers as the library reads them; 0.6: the 25 numbers after AN INSTRUCTION):")
    for name, v in (("0.2 grid", sq2), ("0.6 square", sq6)):
        g = grid(v)
        say(f"{name}: rows {[sum(r) for r in g]}, columns {[sum(c) for c in zip(*g)]}, diagonals {sum(g[i][i] for i in range(5))}, {sum(g[i][4 - i] for i in range(5))}; "
            f"centro-symmetric c[i][j] = c[4-i][4-j]: {all(g[i][j] == g[4 - i][4 - j] for i in range(5) for j in range(5))}; distinct values {len(set(v))} (12 pairs and the centre)")
        for r in g:
            say(f"    {r}")
    say("")
    pi = lambda x: sum(1 for p in P if p <= x)
    say(f"pi(1033) = {pi(1033)} = 29 x {pi(1033) // 29}; pi(3301) = {pi(3301)} = 29 x {pi(3301) // 29}; the 140th prime = {P[139]}; the 464th prime = {P[463]}")
    say(f"phi(278) = {phi(278)}, phi(626) = {phi(626)}, sigma(139) = 140; 139 + 313 + 467 + 809 = {139 + 313 + 467 + 809} = 12^3; 3301 - 1728 = {3301 - 1728} = 11 x 11 x 13")
    gp = [p for p in P if p <= 109]
    notsmooth = []
    for v in sorted(set(sq6)):
        m = v
        for p in gp:
            while m % p == 0:
                m //= p
        if m != 1:
            notsmooth.append(v)
    say(f"values of the 0.6 square with a prime factor above 109 (not a product of Gematria Primus primes): {notsmooth}")
    cnt = [p for p in P if 1000 <= p <= 4000 and pi(p) % 29 == 0]
    tot = sum(1 for p in P if 1000 <= p <= 4000)
    say(f"base rate: primes in 1000..4000 whose index is a multiple of 29: {len(cnt)} of {tot} ({100 * len(cnt) / tot:.1f}%, chance 1/29 = 3.4%)")
    d = [a - b for a, b in zip(sq6, sq2)]
    say(f"position-wise difference 0.6 - 0.2 (row by row): {grid(d)}")
    with open(os.path.join(HERE, "..", "results", "analysis", "squares_check.txt"), "w", newline="\n", encoding="utf-8") as fh:
        fh.write("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
