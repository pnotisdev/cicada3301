"""Hashing + variants for the An End hunt (phase 52). Data only: files are read as bytes, never executed."""
import hashlib, re, html, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
TARGET = "36367763ab73783c7af284446c59466b4cd653239a311cb7116d4618dee09a8425893dc7500b464fdaf1672d7bef5e891c6e2274568926a49fb4f45132c2a8b4"
FAST = {"sha512": lambda b: hashlib.sha512(b).hexdigest(),
        "sha3_512": lambda b: hashlib.sha3_512(b).hexdigest(),
        "blake2b": lambda b: hashlib.blake2b(b).hexdigest()}
SLOW = {}
from whirlpool_pure import whirlpool_fast
SLOW["whirlpool"] = lambda b: whirlpool_fast(b).hex()
try:
    import gostcrypto
    SLOW["streebog512"] = lambda b: gostcrypto.gosthash.new("streebog512", data=b).hexdigest()
except Exception:
    pass
SLOW_CAP = 30_000       # bytes; pure-Python whirlpool/streebog are slow, so only small candidates get them
VAR_CAP = 4_000_000     # text variants only below this size
TAG = re.compile(rb"<script.*?</script>|<style.*?</style>|<!--.*?-->|<[^>]+>", re.S | re.I)
def visible(b):
    t = TAG.sub(b" ", b)
    t = html.unescape(t.decode("utf-8", "replace")).encode("utf-8")
    return t
def variants(b):
    """Return {name: bytes}, deduplicated by content (first name wins)."""
    v = {}
    def add(n, x):
        if x not in v.values(): v[n] = x
    add("raw", b)
    if len(b) > VAR_CAP: return v
    body = b
    m = re.match(rb"HTTP/\d\.\d \d+[^\r\n]*\r?\n.*?\r?\n\r?\n", b, re.S)
    if m: body = b[m.end():]; add("body_no_headers", body)
    for tag, x in (("", body),):
        lf = x.replace(b"\r\n", b"\n")
        crlf = lf.replace(b"\n", b"\r\n")
        add("lf", lf); add("crlf", crlf)
        for nm, y in (("raw", x), ("lf", lf), ("crlf", crlf)):
            if y.endswith(b"\n"):
                add(nm + "_no_trailing_nl", y.rstrip(b"\r\n"))
                add(nm + "_one_trailing_nl", y.rstrip(b"\r\n") + (b"\r\n" if nm == "crlf" else b"\n"))
            else:
                add(nm + "_plus_nl", y + (b"\r\n" if nm == "crlf" else b"\n"))
    vt = visible(body)
    for nm, y in (("text", vt), ("text_stripped", vt.strip()), ("text_ws_collapsed", re.sub(rb"\s+", b" ", vt).strip()),
                  ("text_nl_lines", b"\n".join(l.strip() for l in vt.splitlines() if l.strip()))):
        add(nm, y); add(nm + "_plus_nl", y + b"\n")
    return v
def digest_all(b, allow_slow=None):
    """Return list of (func, hex)."""
    out = [(n, f(b)) for n, f in FAST.items()]
    if (allow_slow if allow_slow is not None else len(b) <= SLOW_CAP):
        out += [(n, f(b)) for n, f in SLOW.items()]
    return out
def check(label, b, stats, hits):
    """Hash all variants of b, update stats and hits."""
    for vn, vb in variants(b).items():
        for fn, hx in digest_all(vb):
            stats["digests"] += 1
            if hx == TARGET: hits.append((label, vn, fn, "FULL"))
            elif hx[:12] == TARGET[:12] or hx[-12:] == TARGET[-12:]: hits.append((label, vn, fn, "PREFIX/SUFFIX12"))
    stats["candidates"] += 1
