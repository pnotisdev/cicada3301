"""Phase 4 item 3: crib-driven constraint solver.

A key model says which rune positions share a key value (periodic key: positions i and i+L;
key reuse: position i of text A and i+d of text B). Each word must decrypt to a dictionary word
of its length (one-rune words: A or I). The solver assigns words in most-constrained-first
order, propagates the implied key values to every other word that shares them, prunes words
left with no dictionary candidate (forward checking), and does depth-first branch-and-bound on
total word log-probability.

    python cribsolve.py validate   # synthetic periodic-key and key-reuse ciphertexts
"""
import random
import sys
import time
from collections import defaultdict

import lp
import crib

N = lp.N


class Problem:
    """words: list of (positions, cipher runes); var_of: position -> key variable."""

    def __init__(self, words, var_of, atbash=False, wildcard=-9.0):
        """wildcard: log-probability per rune for leaving a word unexplained (None = forbid)."""
        self.words = words
        self.var_of = var_of
        self.atbash = atbash
        self.wildcard = wildcard
        self.dict = crib.one_rune_only_ai()
        self.cands = {L: sorted(d.items(), key=lambda kv: -kv[1]) for L, d in self.dict.items()}
        self.best_lp = {L: c[0][1] for L, c in self.cands.items()}
        self.var_words = defaultdict(set)
        for w, (pos, _) in enumerate(words):
            for p in pos:
                self.var_words[var_of[p]].add(w)
        # words with no shared key variable carry no constraint
        self.linked = [w for w, (pos, _) in enumerate(words)
                       if any(len(self.var_words[var_of[p]]) > 1 for p in pos)]
        self._cache = {}

    def plain_rune(self, c, k):
        t = (c - k) % N
        return N - 1 - t if self.atbash else t

    def key_for(self, c, p):
        t = N - 1 - p if self.atbash else p
        return (c - t) % N

    def consistent(self, w, assign):
        """Dictionary candidates for word w given current key assignment."""
        pos, cw = self.words[w]
        L = len(cw)
        if L not in self.cands:
            return []
        fixed = []
        local = {}
        for x, (p, c) in enumerate(zip(pos, cw)):
            v = self.var_of[p]
            if v in assign:
                fixed.append((x, self.plain_rune(c, assign[v])))
            else:
                local.setdefault(v, []).append((x, c))
        rep = tuple((x, c) for v, lst in local.items() if len(lst) > 1 for x, c in lst)
        key = (L, tuple(fixed), self._shape(local))
        if key in self._cache:
            base = self._cache[key]
        else:
            base = [(t, s) for t, s in self.cands[L] if all(t[x] == r for x, r in fixed)]
            self._cache[key] = base
        if not rep:
            return base
        # positions sharing an unassigned variable inside the word must imply the same key
        out = []
        for t, s in base:
            ok = True
            for v, lst in local.items():
                if len(lst) > 1:
                    ks = {self.key_for(c, t[x]) for x, c in lst}
                    if len(ks) > 1:
                        ok = False
                        break
            if ok:
                out.append((t, s))
        return out

    @staticmethod
    def _shape(local):
        return tuple(sorted(tuple(x for x, _ in lst) for lst in local.values() if len(lst) > 1))

    def solve(self, node_limit=200000, time_limit=60):
        t0 = time.time()
        best = {"score": -1e18, "assign": None, "words": None}
        nodes = [0]
        linked = self.linked

        def bound(chosen_score, done):
            return chosen_score + sum(self.best_lp.get(len(self.words[w][1]), -30) for w in linked if w not in done)

        def rec(assign, done, score):
            nodes[0] += 1
            if nodes[0] > node_limit or time.time() - t0 > time_limit:
                return
            if bound(score, done) <= best["score"]:
                return
            # most constrained unassigned linked word
            pick, pick_c = None, None
            for w in linked:
                if w in done:
                    continue
                cs = self.consistent(w, assign)
                if not cs:
                    if self.wildcard is None:
                        return
                    # forced wildcard: no dictionary word fits, leave it unexplained (no branching)
                    cs = [(None, self.wildcard * len(self.words[w][1]))]
                if pick is None or len(cs) < len(pick_c):
                    pick, pick_c = w, cs
                    if len(cs) == 1:
                        break
            if pick is None:
                if score > best["score"]:
                    best.update(score=score, assign=dict(assign), words=dict(done))
                return
            pos, cw = self.words[pick]
            for t, s in pick_c[:400]:
                if t is None:  # wildcard: word left unexplained, constrains nothing
                    d2 = dict(done)
                    d2[pick] = None
                    rec(assign, d2, score + s)
                    continue
                new = dict(assign)
                for p, c, r in zip(pos, cw, t):
                    new[self.var_of[p]] = self.key_for(c, r)
                d2 = dict(done)
                d2[pick] = t
                rec(new, d2, score + s)

        rec({}, {}, 0.0)
        best["nodes"] = nodes[0]
        best["seconds"] = time.time() - t0
        return best

    def solve_beam(self, width=200, per_state=25, time_limit=None):
        """Beam search: at each depth every state assigns its own most-constrained word; states
        at the same depth have the same number of assigned words, so scores are comparable."""
        t0 = time.time()
        beam = [(0.0, {}, {})]  # score, assign, done
        linked = self.linked
        for depth in range(len(linked)):
            nxt = []
            for score, assign, done in beam:
                pick, pick_c = None, None
                for w in linked:
                    if w in done:
                        continue
                    cs = self.consistent(w, assign)
                    if not cs:
                        cs = [(None, (self.wildcard or -30.0) * len(self.words[w][1]))]
                    if pick is None or len(cs) < len(pick_c):
                        pick, pick_c = w, cs
                        if len(cs) == 1:
                            break
                pos, cw = self.words[pick]
                for t, s in pick_c[:per_state]:
                    new = dict(assign)
                    if t is not None:
                        for p, c, r in zip(pos, cw, t):
                            new[self.var_of[p]] = self.key_for(c, r)
                    d2 = dict(done)
                    d2[pick] = t
                    nxt.append((score + s, new, d2))
            nxt.sort(key=lambda x: -x[0])
            # drop duplicate key assignments
            seen, beam = set(), []
            for st in nxt:
                sig = tuple(sorted(st[1].items()))
                if sig not in seen:
                    seen.add(sig)
                    beam.append(st)
                if len(beam) >= width:
                    break
            if time_limit is not None and time.time() - t0 > time_limit:
                break
        score, assign, done = beam[0]
        return {"score": score, "assign": assign, "words": done, "nodes": depth, "seconds": time.time() - t0,
                "complete": len(done) == len(linked)}

    def quality(self, res):
        """(score per decided rune, share of decided linked words left unexplained, share decided).
        Only words the search actually decided count, so truncated runs are not flattered."""
        done = res["words"] or {}
        dec = [w for w in self.linked if w in done]
        runes = sum(len(self.words[w][1]) for w in dec)
        wild = sum(1 for w in dec if done[w] is None)
        return res["score"] / max(1, runes), wild / max(1, len(dec)), len(dec) / max(1, len(self.linked))

    def render(self, assign, word_ids=None):
        out = []
        for w, (pos, cw) in enumerate(self.words):
            if word_ids is not None and w not in word_ids:
                continue
            out.append("".join(lp.LATIN[self.plain_rune(c, assign[self.var_of[p]])] if self.var_of[p] in assign
                               else "?" for p, c in zip(pos, cw)))
        return " ".join(out)


# ---------------------------------------------------------------- models

def words_from_tokens(toks, base=0, tag=0):
    c = lp.runes_of(toks)
    out = []
    for _, a, b in lp.word_spans(toks, c):
        out.append(([(tag, base + i) for i in range(a, b)], c[a:b]))
    return out


def periodic_problem(toks, L, atbash=False):
    words = words_from_tokens(toks)
    var_of = {p: p[1] % L for w in words for p in w[0]}
    return Problem(words, var_of, atbash)


def depth_problem(toks_a, toks_b, d, atbash=False, range_a=None, range_b=None):
    """Text B position j uses the same key as text A position j + d. Positions are absolute
    rune indices of each text; range_a / range_b (lo, hi) keep only words fully inside."""
    wa = words_from_tokens(toks_a, tag=0)
    wb = words_from_tokens(toks_b, tag=1)
    if range_a:
        wa = [w for w in wa if range_a[0] <= w[0][0][1] and w[0][-1][1] < range_a[1]]
    if range_b:
        wb = [w for w in wb if range_b[0] <= w[0][0][1] and w[0][-1][1] < range_b[1]]
    var_of = {}
    for pos, _ in wa:
        for p in pos:
            var_of[p] = p[1]
    for pos, _ in wb:
        for p in pos:
            var_of[p] = p[1] + d
    return Problem(wa + wb, var_of, atbash)


# ---------------------------------------------------------------- validation

def _encrypt(toks, key_at):
    out, i = [], 0
    for t in toks:
        if isinstance(t, int):
            out.append((t + key_at(i)) % N)
            i += 1
        else:
            out.append(t)
    return out


def accuracy(prob, assign, truth_tokens_list):
    truth = [x for toks in truth_tokens_list for x in lp.runes_of(toks)]
    got = []
    for pos, cw in prob.words:
        for p, c in zip(pos, cw):
            v = prob.var_of[p]
            got.append(prob.plain_rune(c, assign[v]) if v in assign else None)
    known = [(g, t) for g, t in zip(got, truth) if g is not None]
    return sum(g == t for g, t in known) / max(1, len(known)), len(known) / len(truth)


def validate():
    import attack
    R = random.Random(37)
    print("== periodic key, L=37, 600 runes of English, no skips")
    pt = attack.synthetic_tokens(600, start=12000)
    key = [R.randrange(N) for _ in range(37)]
    ct = _encrypt(pt, lambda i: key[i % 37])
    prob = periodic_problem(ct, 37)
    res = prob.solve(time_limit=120)
    acc, cov = accuracy(prob, res["assign"] or {}, [pt])
    print(f"  solved: accuracy {100 * acc:.1f}% on {100 * cov:.0f}% of runes, {res['nodes']} nodes, {res['seconds']:.1f}s")
    print("  " + prob.render(res["assign"] or {})[:160])
    wrong = periodic_problem(ct, 41).solve(time_limit=60)
    print(f"  wrong period 41: {'no consistent solution' if wrong['assign'] is None else 'score %.0f' % wrong['score']} "
          f"vs true {res['score']:.0f}")

    print("== key reuse (depth): two 300-rune English texts, same random key, offset 0")
    pa = attack.synthetic_tokens(300, start=15000)
    pb = attack.synthetic_tokens(300, start=25000)
    k = [R.randrange(N) for _ in range(400)]
    ca, cb = _encrypt(pa, lambda i: k[i]), _encrypt(pb, lambda i: k[i])
    prob = depth_problem(ca, cb, 0)
    res = prob.solve(time_limit=180)
    acc, cov = accuracy(prob, res["assign"] or {}, [pa, pb])
    print(f"  solved: accuracy {100 * acc:.1f}% on {100 * cov:.0f}% of runes, {res['nodes']} nodes, {res['seconds']:.1f}s")
    print("  A: " + prob.render(res["assign"] or {}, set(range(len(words_from_tokens(ca)))))[:150])


if __name__ == "__main__":
    {"validate": validate}[sys.argv[1]]()
