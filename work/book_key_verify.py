"""Phase 23 STAGE 2 verifier for the booknight screen: whole-section decoding of a stage-1 hit (spec: work/log/phase23_book_key_decoder.md, decision rule step 2).

For a hit (book, spelling, offset, section) the WHOLE section is decoded from the hit's grid offset: table-free beam (book_key_decoder.beam_decode,
8 free starts so the true offset inside the grid cell is covered), then hard EM (book_key_decoder.decode: assignment-problem table + exact skip-rule
Viterbi). Verified only if ALL hold (spec 2a, 2b):
  a. the section-length beam score per rune beats the MAXIMUM of 200 beam scores of the same book at random offsets on the same section by >= 5 of their sd
  b. the EM decryption has IoC >= 1.40
Reported as well (not gates): the recovered table, the decrypted text, its bigram score per rune (Walden bigram model, nats against uniform), the prime-sum check of the
clauses (work/prime_check.py), matched nulls for the EM statistics (same book at 20 random offsets; uniform-key ciphers of the same length against the hit's offset),
and the end pointer (spec 2c: compare with the next section's hit). The decrypted text must be read by a human (2d).

    python work/book_key_verify.py gate [--quick]                     # plants through this file's own code path -> results/analysis/book_key_verify_gate.txt
    python work/book_key_verify.py hit <book> <digraph|letters> <offset> <section, e.g. 0.12>

Nothing in LP2 is solved; a verified hit is a candidate, never a solution. The queue's files are only imported, not changed.
"""
import os
import sys
import tempfile

os.environ.setdefault("NUMBA_CACHE_DIR", os.path.join(tempfile.gettempdir(), "lp_numba_cache"))   # never write into the queue's __pycache__

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lp  # noqa: E402
import prime_check  # noqa: E402
import book_key_screen as S  # noqa: E402
from book_key_decoder import LN_SKIP, beam_decode, decode, decrypt, encrypt_skip_ptr  # noqa: E402
from book_key_flatness import HERE, dist, flattest_table, gutenberg_body, to_runes  # noqa: E402

N = lp.N
SPREAD = 8
N_NULL_BEAM, N_NULL_EM, MARGIN_SD, IOC_MIN = 200, 20, 5.0, 1.40
_cache = {}


def bigram_model():
    """log(29 P(y | x)) from Walden (digraph runes), +0.5 smoothing: nats per rune against a uniform text"""
    if "B" not in _cache:
        w = to_runes(gutenberg_body(os.path.join(S.C, "pg205.txt")))
        B = np.full((N, N), 0.5)
        np.add.at(B, (w[:-1], w[1:]), 1)
        _cache["B"] = np.log(N * B / B.sum(1, keepdims=True))
    return _cache["B"]


def bigram_score(p):
    return float(bigram_model()[p[:-1], p[1:]].mean())


def em_stats(c, K, o, MT, prev0=-1):
    sb, se, path, s = decode(c, K, o, MT, prev0=prev0, spread=SPREAD)
    p = decrypt(c, K, path, s)
    return dict(beam=sb / len(c), em=se / len(c), ioc=lp.ioc(list(p)), bigram=bigram_score(p), path=path, s=s, plain=p)


def verify(c, K, o, MT, toks=None, rng=None, n_beam=N_NULL_BEAM, n_em=N_NULL_EM):
    """whole-section verification of one hit; returns a dict with the decisions and every number"""
    rng = rng or np.random.default_rng(3323)
    n = len(c)
    hit = em_stats(c, K, o, MT)
    nb = np.array([beam_decode(c, K, int(x), MT, 64, LN_SKIP, 8, SPREAD)[0] / n for x in rng.integers(0, len(K) - 3 * n, n_beam)])
    margin = (hit["beam"] - nb.max()) / nb.std(ddof=1)
    z_mean = (hit["beam"] - nb.mean()) / nb.std(ddof=1)
    near = [em_stats(c, K, int(x), MT) for x in rng.integers(0, len(K) - 3 * n, n_em)]
    cu = [encrypt_skip_ptr(hit["plain"], rng.integers(0, N, 3 * n), rng)[0] for _ in range(n_em)]   # same plaintext statistics, uniform key
    uni = [em_stats(x, K, o, MT) for x in cu]
    out = dict(n=n, hit=hit, null_beam=(nb.mean(), nb.std(ddof=1), nb.max()), margin_sd=float(margin), z_mean=float(z_mean),
               null_off=near, null_uni=uni, end_pointer=int(hit["path"][-1]) + 1)
    out["pass_a"] = bool(margin >= MARGIN_SD)
    out["pass_b"] = bool(hit["ioc"] >= IOC_MIN)
    out["verified"] = out["pass_a"] and out["pass_b"]
    if toks is not None:
        out["prime"] = prime_check.check(toks, 0, [int(x) for x in hit["plain"]])
    return out


def report(name, v, toks=None, c=None):
    h = v["hit"]
    nm, ns, nx = v["null_beam"]
    L = [f"== {name}: {v['n']} runes, end pointer {v['end_pointer']}",
         f"  beam score per rune {h['beam']:+.4f}; 200 random offsets: mean {nm:+.4f} sd {ns:.4f} max {nx:+.4f}; z over mean {v['z_mean']:+.1f}; margin over the max {v['margin_sd']:+.1f} sd (need >= {MARGIN_SD}): {'PASS' if v['pass_a'] else 'fail'}",
         f"  EM decryption IoC {h['ioc']:.3f} (need >= {IOC_MIN}): {'PASS' if v['pass_b'] else 'fail'}; EM score per rune {h['em']:+.4f}; bigram {h['bigram']:+.3f} nats/rune",
         "  matched nulls (EM): " + "; ".join(f"{k} IoC {np.mean([x['ioc'] for x in nn]):.3f} (max {max(x['ioc'] for x in nn):.3f}), EM {np.mean([x['em'] for x in nn]):+.3f}, bigram {np.mean([x['bigram'] for x in nn]):+.3f}"
                                              for k, nn in (("random offsets", v["null_off"]), ("uniform key", v["null_uni"])))]
    if "prime" in v:
        p = v["prime"]
        L.append(f"  prime sums of the decoded clauses: {p['clauses']} clauses, {p['prime']} prime (chance tail P {p['p_chance']:.3f}); short clauses {p['short']}, prime {p['short_prime']}, evidence {p['short_llr']:+.1f} nats (not a gate; < 6 short clauses says nothing)")
    s = h["s"]
    L.append("  recovered table (key letter -> shift added to the plaintext rune): " + " ".join(f"{lp.LATIN[g]}={s[g]}" for g in range(N)))
    p = h["plain"]
    if toks is not None:
        r = lp.runes_of(toks)
        words = [(a, b) for _, a, b in lp.word_spans(toks, r)]
        txt = " ".join("".join(lp.LATIN[x] for x in p[a:b]) for a, b in words)
    else:
        txt = "".join(lp.LATIN[x] for x in p)
    L.append("  decrypted text (to be read by a human, spec 2d):\n  " + txt[:4000])
    L.append(f"  RESULT: {'VERIFIED CANDIDATE (read the text; not a solution)' if v['verified'] else 'NOT verified'}")
    return "\n".join(L)


def run_hit(book, spell, offset, section):
    i = int(section.split(".")[1])
    toks = lp.load_segments()[i]
    c = np.array(lp.runes_of(toks), dtype=np.int64)
    K = S.key_of(book, spell)
    v = verify(c, K, int(offset), S.model(), toks)
    text = report(f"{book}/{spell} offset {offset} section {section}", v, toks)
    print(text)
    return v


# ------------------------------------------------------------------------------------------------------------- gate
def gate(quick=False):
    """plants (flattening table, skip rule q = 0.81, whole-section lengths, both key spellings): table / plaintext recovery and verification; nulls must not verify"""
    rng = np.random.default_rng(2323)
    em = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    MT = S.model()
    out = []
    for spell in ("digraph", "letters"):
        K = S.key_of("liber_al", spell)
        for n, reps in ((1524, 3 if quick else 6), (3316, 2 if quick else 4)):
            for pl in ("digraph", "letters"):
                if quick and pl == "letters" and n == 3316:
                    continue
                P = to_runes(em, letters=pl == "letters")
                ok, acc, tab, null_off, null_uni, ioc = 0, [], [], 0, 0, []
                for r in range(reps):
                    _, pi = flattest_table(dist(P), dist(K), rng, restarts=3)
                    table = np.argsort(pi)
                    o = int(rng.integers(100, len(K) - 3 * n))
                    po = int(rng.integers(0, len(P) - n))
                    ptxt = P[po:po + n]
                    c, used = encrypt_skip_ptr(ptxt, table[K[o:o + 3 * n]], rng)
                    g = o - o % SPREAD
                    v = verify(c, K, g, MT, None, rng, n_beam=60, n_em=4)
                    ok += v["verified"]
                    acc.append(float(np.mean(v["hit"]["plain"] == ptxt)))
                    present = np.unique(K[o + used])
                    tab.append(float(np.mean(v["hit"]["s"][present] == table[present])))
                    ioc.append(v["hit"]["ioc"])
                    wo = int(rng.integers(0, len(K) - 3 * n))               # the same cipher against a wrong offset of the right book
                    null_off += verify(c, K, wo - wo % SPREAD, MT, None, rng, n_beam=60, n_em=4)["verified"]
                    cu = encrypt_skip_ptr(ptxt, rng.integers(0, N, 3 * n), rng)[0]   # a uniform-key cipher at a grid offset
                    null_uni += verify(cu, K, g, MT, None, rng, n_beam=60, n_em=4)["verified"]
                line = (f"key {spell:7s} plaintext {pl:7s} {n} runes: verified {ok}/{reps}; plaintext accuracy median {np.median(acc):.3f} (min {min(acc):.3f}); table agreement median {np.median(tab):.2f}; "
                        f"decrypted IoC median {np.median(ioc):.3f}; wrong-offset nulls verified {null_off}/{reps}; uniform-key nulls verified {null_uni}/{reps}")
                print(line, flush=True)
                out.append(line)
    path = os.path.join(S.ROOT, "results", "analysis", "book_key_verify_gate.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write("Phase 23 stage 2 verifier, gate on plants (Liber AL as the key, Emerson plaintext, flattening table, q = 0.81; 60 beam nulls and 4 EM nulls per verification here, 200 / 20 for a real hit)\n" + "\n".join(out) + "\n")
    return out


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "gate"
    if cmd == "gate":
        gate("--quick" in sys.argv)
    elif cmd == "hit":
        run_hit(*sys.argv[2:6])
    else:
        sys.exit(__doc__)
