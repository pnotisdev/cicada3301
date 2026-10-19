# The exact LR theorem, and the null-law issue

Nothing in LP2 is solved. This proof document is written before the proof-gate
execution. Numerical counterexample expressions below are algebraic predictions,
not reported experimental results. The gate independently checks them.

## 1. What normalization really proves

Fix ONE key, offset, channel and length. Let U_c and L_c denote its unconditioned
successful-output masses. Missing probability is carried by termination/failure
outcomes. For U_c>0 define R_c=L_c/U_c and S_c=ln R_c. Failure and U=0 observations
are rejected, not assigned infinite scores. Uniform plaintext has full support,
so every L-supported successful output is also U-supported.

For any real r>0,

    P_(U_cell)(R >= r)
      = sum_(c: L_c >= r U_c, U_c>0) U_c
      <= (1/r) sum_(same c) L_c
      <= (1/r) sum_(all successful c) L_c
      <= 1/r.

Equivalently P_(U_cell)(S>=t)<=exp(-t). Also E_(U_cell)[R]=sum_c L_c<=1.
These statements are EXACT for skip5 and coin too, not only hold/spend. They
use the particular finite-key channel null for that cell, including failure.
They do NOT automatically apply after conditioning on successful length n:
that changes the probability measure and adds a survival normalization factor.

## 2. The extra condition needed for a campaign union bound

To conclude P_W(any of N scores >=ln(N/alpha))<=alpha, all per-cell inequalities
must hold under the SAME law W of the observed ciphertext. Different inequalities
under different U_cell laws cannot simply be added as if they used a common W.

Under any W, the actual expectation is

    E_W[R_cell] = sum_(U_c>0) W_c * L_c/U_c,

not sum_c L_c unless W=U_cell on the relevant observations. If W/U_cell <=B_cell
uniformly, a bound B_cell/r follows; no B=1 assumption is free. Support gaps and
conditioning also matter. A pointwise gap measurement on tiny keys does not
establish a bound for the whole library.

For the common anti-repeat Markov output law (uniform first rune), write

    d=(1-q)/Q,
    b=(Q-1+q)/(Q*(Q-1)).

Each repeat has probability d, each particular nonrepeat b. This is not iid
output, but is the law obtained from fresh iid-uniform plaintext in unlimited
hold/spend channels. With at least n remaining key values, hold/spend cannot
exhaust, and U_cell=W, independent of key contents. Spend cells with fewer than
n values cannot emit n outputs and are rejected.

Finite hold is different: it can emit n outputs with only two values remaining,
by repeatedly holding the last slot. Its U depends on the finite remaining length
and observation pattern, even though it is independent of the actual key VALUES.
Key-content independence alone does not make U_cell=W across all offsets.
The inventory includes these suffix offsets, as the user required.

Skip5/coin additionally depend on actual key patterns, even with enough values
for worst-case consumption. Their own-U theorem remains exact, but substitution
of W is unproved, not an approximation with a known error bar. The gate measures
some exact toy density gaps; real-bank gaps remain unknown if this prerequisite
fails. Using the word approximate cannot certify a .001 error guarantee.

## 3. A small finite-hold counterexample to the common-W claim

Q=3, n=3, key=(0,0), offset0, sign+, q=3/5. Take initial plaintext0 with
probability1 and a deterministic constant-plaintext transition matrix (identity).
To emit three outputs with two keys, the second output must be a hold repair.
The only successful L outputs are (0,1,0) and (0,2,0), each with mass3/10.

For each of these outputs:

    U_cell(c) = (1/3)*(q/(3*2))*b = 13/900,
    L(c)/U_cell(c) = (3/10)/(13/900) = 270/13 >20.

No other output has positive L. Therefore, at t=ln20:

    P_(U_cell)(S>=t) = 2*(13/900) = 13/450 <=1/20,
    P_W(S>=t) = 2*(1/3)*(13/30)^2 = 169/1350 >1/20.

The cell-matched theorem PASSES while the common anti-repeat null assertion FAILS.
This uses exactly the unchanged finite-key failure semantics, not a broken DP.

## 4. Long-window family: test the proposed campaign threshold too

Choose a set D of d nonzero plaintext increments. Let pi uniform and
L(r,p)=1/d when (p-r) mod Q belongs to D, zero otherwise. This is a valid
normalized bigram model, not the production English model. Choose key=(a,0)
with a in D, offset0, sign+. Consider event A:

- first n-2 ciphertext transitions have increments in D;
- final ciphertext transition repeats.

With two available key values, the first emission spends the first key. To
survive to length n, every intermediate output must hold the second key. The
last repeat can only be a kept collision. There is one plaintext path for each
ciphertext in A. A first transition p0 -> p1 has increment a; later plaintext
transitions follow the previous ciphertext increments. Thus

    L(c) = (1/Q) * [q/(d*(Q-1))]^(n-2) * (1-q)/d,
    U(c) = (1/Q) * [q/(Q*(Q-1))]^(n-2) * (1-q)/Q,
    L(c)/U(c) = (Q/d)^(n-1),
    P_W(A) = (d*b)^(n-2) * (1-q)/Q.

These are exact rational expressions. One representative ciphertext is checked
against the unchanged v1 rational DP; the event mass follows by counting all
Q*d^(n-2) compatible prefixes. The event mass is a LOWER bound on the full tail.
If R_event >= N_cells/alpha AND P_W(A)>alpha/N_cells, it refutes the proposed
per-cell campaign-threshold guarantee under W. It does NOT alone prove that
the aggregate actual-library FWER exceeds .001.

Predeclared checks: Q3, D={1,2}, key(1,0), q81/100, n300 and600; Q29,
D={3,4,...,28}, key(3,0), q81/100, n300. Exact fractions, no Monte Carlo or
seed search. If a check does not refute at the proposed T, say so; do not infer
it from a violation at some other threshold. These generic normalized LMs test
the normalization-only proof, not measured false positives of the English LM.

## 5. Wrong offsets of a plant are not automatically null cells

Even if every cell were tested under one valid null law, a tail probability
bound implies E[count(S>=t)]<=N*exp(-t), not a deterministic bound on the observed
count. Dependence does not prevent summing expectations, but there remains
sampling variation. More importantly, near offsets on a planted stream may
encode nearly the same plaintext; periodic streams can have EXACT offset aliases.
They are not independent wrong-key null draws. The requested empirical count
check will be followed literally if reached, with aliases included, but its
failure need not imply a decoder bug or invalid cell-matched LR normalization.
A Markov bound with an additional significance factor, or matched-null count
calibration, would be a different protocol requiring authorization.

## 6. Synthetic sanity null is a third law

The v1 wrong-key nulls encrypt English, not iid uniform plaintext. Under M04 a
held key is revealed by a collision and then reused; the next attempted output
depends on the next plaintext difference. Matching the doublet rate does not
prove the full output law is W. Passing eight sanity windows is useful but does
not prove a .001 campaign false-positive bound. No such claim is permitted.
