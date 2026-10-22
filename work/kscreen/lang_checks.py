"""Language-independent checks for a decoded window (phase 50): the A/I oracle (phase 48) and the prime-sum
check of short clauses (work/prime_check.py). Both read the decoded plaintext only; neither is a gate.

    window_where(name)  -> (section, start) for 'seg0.7', 'page16_0.7@262', 'head0.8@119'; None otherwise
    checks(name, plain) -> dict(ai_k, ai_n, ai_p, cl, cl_prime, short, short_prime, llr) or None
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import lp  # noqa: E402
import prime_check  # noqa: E402

_AI = (lp.LATIN.index("A"), lp.LATIN.index("I"))
_segs = None


def window_where(name):
    m = re.fullmatch(r"(?:seg|page\d+_|head)(0\.\d+)(?:@(\d+))?", name)
    return (int(m.group(1).split(".")[1]), int(m.group(2) or 0)) if m else None


def applies(meta):
    """only windows in LP's own reading order with a plain decode aligned to the rune positions: forward key, no keyless nulls,
    data/segments.txt, pages.txt, heads.txt and the sign-rule windows of data/signs/"""
    w = meta.get("windows", "").replace("\\", "/")
    return meta.get("dir") != "back" and meta.get("nulledge", "0") == "0" and (
        os.path.basename(w) in ("segments.txt", "pages.txt", "heads.txt") or "data/signs/" in w)


def checks(name, plain):
    global _segs
    where = window_where(name)
    if not where:
        return None
    _segs = _segs or lp.load_segments()
    sec, start = where
    toks = _segs[sec]
    one = [a for _, a, b in lp.word_spans(toks, lp.runes_of(toks)) if b - a == 1 and start <= a < start + len(plain)]
    k = sum(plain[a - start] in _AI for a in one)
    p = prime_check.check(toks, start, plain)
    return dict(ai_k=k, ai_n=len(one), ai_p=prime_check.binom_tail(len(one), k, 2 / 29) if one else 1.0,
                cl=p["clauses"], cl_prime=p["prime"], short=p["short"], short_prime=p["short_prime"], llr=p["short_llr"])


def fmt(c):
    if c is None:
        return "A/I n/a; prime n/a"
    return (f"A/I {c['ai_k']}/{c['ai_n']} (p {c['ai_p']:.2g}, null 2/29); prime short clauses {c['short_prime']}/{c['short']} "
            f"(chance 15%, solved 60%), evidence {c['llr']:+.1f} nats")
