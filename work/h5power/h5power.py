"""Power map of the H5 flat-library sweep: independent plants through the REAL h5rs sweep path, recall by keyword length, model, key kind and offset.

For each plant (stream t + unknown keyword w of period L, skip or coin anti-repeat, 300 plaintext runes) the engine sweeps the planted stream over the TRUE offset +-1,
every L = 2..20 and both models, exactly as the campaign sweep does (fast engine, campaign abort, default window handling), and we ask whether the true cell clears
the candidate floor. Restricting the offsets to +-1 does not change a cell's score; it only removes the other offsets' chance cells, which the campaign null covers.
Nothing in LP2 is solved; this measures what a NEGATIVE sweep could and could not have excluded.

    python work/h5power/h5power.py [--per-stratum 50] [--workers 4]
"""
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import random
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "work", "m04"))
import m04 as M  # noqa: E402  (plaintext pools, KSB writer, library reader; independent of the decoders)

BIN = os.path.join(ROOT, "work", "h5rs", "target", "release", "h5rs.exe" if os.name == "nt" else "h5rs")
Q = 29
STREAM_LEN = 2500
KEEP = 0.19
LENGTHS = [2, 3, 4, 5, 6, 8, 10, 13, 16, 20]
OUT = os.path.join(ROOT, "results", "analysis")


def plant(plain, t, off, w, model, rng, keep=KEEP):
    """c_i = p_i + t_j + w_((j-off) mod L) with the key pointer j advancing by the repository's skip (model 0) or coin (model 1) convention"""
    L, j, out = len(w), off, []

    def key(j):
        return (t[j] + w[(j - off) % L]) % Q

    for p in plain:
        x = (p + key(j)) % Q
        j += 1
        if model == 0:
            tries = 0
            while out and x == out[-1] and rng.random() >= keep and tries < 5:
                x = (p + key(j)) % Q
                j += 1
                tries += 1
        elif out and x == out[-1]:
            j += 1
            if rng.random() >= keep:
                x = (p + key(j)) % Q
                j += 1
        out.append(x)
    return out


_POOLS = {}
_LONG = []


def pool(src):
    if src not in _POOLS:
        _POOLS[src] = M.cicada_pool([1, 3]) if src == "cicada" else M.english_pool(0.6, 1.0)
    return _POOLS[src]


def long_streams():
    if not _LONG:
        _LONG.extend(x for x in M.library() if len(x[1]) >= STREAM_LEN)
    return _LONG


def seed_of(*parts):
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "big")


def one(job):
    tag, L, model, kind, src, seed, scratch = job
    rng = random.Random(seed)
    p_ = pool(src)
    s = rng.randrange(len(p_) - M.N_RUNES + 1)
    plain = p_[s:s + M.N_RUNES]
    if kind == "lib":
        v = long_streams()[rng.randrange(len(long_streams()))][1]
        st = rng.randrange(len(v) - STREAM_LEN + 1)
        t = bytes(v[st:st + STREAM_LEN])
    else:
        t = bytes(rng.randrange(Q) for _ in range(STREAM_LEN))
    off = rng.randrange(2000)
    w = [rng.randrange(Q) for _ in range(L)]
    out = plant(plain, t, off, w, model, rng)
    bank, win, tsv = (os.path.join(scratch, f"{tag}.{x}") for x in ("ksb", "txt", "tsv"))
    M.write_ksb(bank, [("k0", t)])
    M.write_window(win, "w", out)
    r = subprocess.run([BIN, "sweep", win, "file:" + bank, str(max(0, off - 1)), str(off + 2), "2", "20", "2", "1", tsv, "--hits", "0"], capture_output=True, text=True)
    if r.returncode != 0:
        return dict(tag=tag, error=r.stderr[-200:])
    rows = []
    with open(tsv, encoding="utf-8") as f:
        for line in f:
            if line.startswith("#") or not line.strip():
                continue
            p = line.rstrip("\n").split("\t")
            rows.append((int(p[1]), int(p[2]), int(p[3]), float(p[5])))
    true_cell = max((r[3] for r in rows if r[0] == off and r[1] == L), default=None)
    anyl = max((r[3] for r in rows), default=None)
    for fn in (bank, win, tsv):
        try:
            os.remove(fn)
        except OSError:
            pass
    return dict(tag=tag, L=L, model=model, kind=kind, src=src, offset=off, true_ioc=true_cell, any_ioc=anyl, cells=len(rows))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--per-stratum", type=int, default=50, help="plants per (L, model, key kind) cell, split over the two plaintext sources")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default=os.path.join(OUT, "h5_power_map"))
    a = ap.parse_args()
    if not os.path.exists(BIN):
        sys.exit("h5rs is not built")
    jobs = []
    with tempfile.TemporaryDirectory(dir=M.scratch_dir()) as scratch:
        for L in LENGTHS:
            for model in (0, 1):
                for kind in ("iid", "lib"):
                    for i in range(a.per_stratum):
                        src = "cicada" if i % 2 == 0 else "english"
                        jobs.append((f"p{len(jobs)}", L, model, kind, src, seed_of("h5pow", L, model, kind, i), scratch))
        with cf.ThreadPoolExecutor(a.workers) as ex:
            recs = list(ex.map(one, jobs))
    bad = [r for r in recs if "error" in r]
    recs = [r for r in recs if "error" not in r]
    json.dump(recs, open(a.out + ".json", "w"), indent=0)
    lines = [f"H5 flat-library sweep: recall of independent plants through the real engine (n = {len(recs)}; {len(bad)} failed). Nothing in LP2 is solved.",
             "A plant is recovered at threshold X when its TRUE cell (offset, L, either model) has IoC >= X: 1.6 is the campaign's fixed floor, 1.8 about the campaign-size null floor (1.77-1.83 on seg0.8).",
             f"300-rune windows, fast engine, campaign abort, keyword uniform, keep {KEEP}; 95% Wilson intervals.", ""]

    def row(label, rs):
        n = len(rs)
        c16 = sum((r["true_ioc"] or 0) >= 1.6 for r in rs)
        c18 = sum((r["true_ioc"] or 0) >= 1.8 for r in rs)
        lo16, hi16 = wilson(c16, n)
        lo18, hi18 = wilson(c18, n)
        return f"{label:34s} n={n:4d}  >=1.6: {c16:4d} ({100 * c16 / max(n, 1):5.1f}%, {100 * lo16:4.0f}-{100 * hi16:3.0f})   >=1.8: {c18:4d} ({100 * c18 / max(n, 1):5.1f}%, {100 * lo18:4.0f}-{100 * hi18:3.0f})"
    lines.append("by keyword length L")
    for L in LENGTHS:
        lines.append(row(f"  L = {L}", [r for r in recs if r["L"] == L]))
    lines += ["", "by anti-repeat model"]
    for m in (0, 1):
        lines.append(row(f"  model {m} ({'skip' if m == 0 else 'coin'})", [r for r in recs if r["model"] == m]))
    lines += ["", "by key kind"]
    for k in ("iid", "lib"):
        lines.append(row(f"  {k}", [r for r in recs if r["kind"] == k]))
    lines += ["", "by true offset band"]
    for b in range(5):
        lines.append(row(f"  offsets {400 * b}-{400 * b + 399}", [r for r in recs if 400 * b <= r["offset"] < 400 * (b + 1)]))
    lines += ["", "L x model (>= 1.6)"]
    for L in LENGTHS:
        cells = []
        for m in (0, 1):
            rs = [r for r in recs if r["L"] == L and r["model"] == m]
            cells.append(f"m{m} {sum((r['true_ioc'] or 0) >= 1.6 for r in rs) / max(len(rs), 1) * 100:5.1f}%")
        lines.append(f"  L = {L:2d}: " + "   ".join(cells))
    text = "\n".join(lines) + "\n"
    open(a.out + ".txt", "w", encoding="utf-8", newline="\n").write(text)
    print(text)


if __name__ == "__main__":
    main()
