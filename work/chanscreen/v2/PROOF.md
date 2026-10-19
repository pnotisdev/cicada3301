# Why the sparse all-offset recursion is exact

Nothing in LP2 is solved. This is an algorithmic identity, not a cryptanalytic
negative. Symbols are mod Q, and the key and sign are fixed, not random.

## R1: bound on previous-plaintext classes

At layer i (i outputs emitted), pointer j is the NEXT key slot and r is the last
plaintext. Enumerate the possible LAST transition; earlier alignment history
cannot add another value of r:

| Channel / last event | Last plaintext r |
|---|---|
| Ordinary emission, including kept collisions when they spend one key | c[i-1] - s*k[j-1] |
| hold repair (no key spent) | c[i-2] - s*k[j] |
| spend repair | c[i-2] - s*k[j-1] |
| skip or skip5, however many retries | c[i-1] - s*k[j-1] |
| coin kept initial collision | c[i-2] - s*k[j-2] |
| coin redraw | c[i-1] - s*k[j-1] |

A successful skip emits with its LAST attempted key, including the cap-forced
emission in skip5. A coin redraw also emits with its last key. Each kernel
therefore has at most two r values at a pointer; skip variants have one.
The first output has only the ordinary class. Unavailable key indices are
omitted. Equal rune labels denote the same state and must be merged by summing
probability, not maximizing or counting their class labels twice.

These are sufficient-state sets, not assertions that every listed state is
reachable from each offset. Over-inclusion does not add probability: a start
state's weighted transitions only visit states reached by a valid emission.
The new Rust code keeps two value slots with distinct labels, and looks up the
actual plaintext label on every edge. The v1 forward tests verify support closure.

The Q3/m<=3 grid sees coin support at most1, but that is not the general bound:
key (0,1,0,1), cipher (0,0), sign+, q=3/5 permits last plaintexts0 and2 at next
pointer4 across initial offsets. The unit suite includes this longer-key case.

## R2: all offsets by one backward pass

Define B_i(j,r) as the conditional probability of the remaining observations
c[i:n] after emitting prefix length i, with next pointer j and previous plaintext
r. The observed previous ciphertext is c[i-1]. The Markov property of L and the
channel make this a sufficient state independently of initial offset o.

B_n(j,r)=1, including j=m. For i<n, B_i(m,r)=0. Else

    B_i(j,r) = sum_(p,h) L[r,p] K_i(c[i],h|p,j) B_(i+1)(h,p).

Each successful event emits exactly one output. Retry micro-events advance the
key; hold emits and advances i. Thus the full finite graph is acyclic even when
hold leaves j unchanged. Dynamic programming groups tree nodes without changing
the sum. Sparse lookup of p at layer i+1 is valid by the R1 last-event proof.

For n>0, the absent-predecessor first output has one plaintext at offset o:

    p0=(c[0]-s*k[o]) mod Q
    Z(o)=pi[p0] B_1(o+1,p0),    o<m
    Z(m)=0.

For n=0 all offsets including m have Z=1. The suffix B is reused, not recomputed
or maximized for each o. For U, each L and pi entry is1/Q, so B_i is independent
of r and needs only one value per j. This is not averaging the FIXED key values.

## Geometric skip tails without quadratic work

Let e(j) be the first slot after j with a different key value, or m. A collision
plaintext p=c[i-1]-s*k[j] continues to collide exactly on j..e(j)-1 (sign +/-1
is invertible mod Q).

If the observed next output differs from c[i-1], a repaired skip path must traverse
that whole equal-key run, then emit at e(j). Its weight is q**(e(j)-j); it is
zero if the key ends or that final output differs from c[i]. Ordinary noncollision
is a separate edge. Run ends are precomputed once in O(m).

If the next output repeats c[i-1], define T_i(j) as the collision-path suffix
sum before multiplying by L[r,p]. Within an equal-key run:

    T_i(j) = (1-q) B_(i+1)(j+1,p)
             + q * 1[j+1<m and k[j+1]=k[j]] * T_i(j+1).

Evaluate this right-to-left in O(m) per layer. U has the same recurrence without
r. At the finite run/key end, any remaining skip probability that cannot emit
the observed output contributes zero to its likelihood. It is a failure/other-
output event, NOT redistributed probability. This agrees with v1's explicit
failure atoms. Skip5 instead enumerates at most six attempts, with the sixth
emission unconditional; that fixed CHANNEL cap is not numerical truncation.

Per channel/sign/window, total work is O(n*m) and memory O(m), regardless of the
number of offsets requested. Small offset subsets may prefer another algorithm;
this engine intentionally computes every offset.

## Stable arithmetic across offsets

All Rust dynamic values are Float64 log probabilities, including U. Every sum
uses max(a,b)+log1p(exp(min(a,b)-max(a,b))) within the individual state. There is
NO shared row/stream scale. A rare offset is never divided by a different offset's
larger mass. q=0/1 uses negative-infinity support branches; log(q)*run length
avoids materializing an underflowed geometric power.

This prevents cross-offset scale underflow, not all floating-point error. The
E1 maximum score error was1.274e-11 nats on the fixed regression sets (limit1e-9).
One calibration cell lies at the v1 threshold and is explicitly marked within
the1e-9 ambiguity margin. Future decisions in that margin require higher-precision
checking, not a fabricated bit-identical guarantee. An adversarial example with
12,433.96 nats between offsets retained both finite log probabilities.

## Evidence and limitations

E0 exact Fractions: 340,800 forward/tree/backward comparisons, 34,080 normalized
trees, 405 extra finite-tail offset comparisons, seven mutant witnesses. Those
finite checks complement the structural proof; they are not an exhaustive test
of all possible n,m. E1 compares593,920 stored scores and100,020 fixed parity cells.
No approximation to the channel, language model, sign, key end or path sum was
needed. None of this proves library-scale statistical power or an English LP2
plaintext. Those require E3/E4, not algebra.
