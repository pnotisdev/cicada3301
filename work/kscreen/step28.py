#!/usr/bin/env python3
"""Keystream screen for the relative-rank (step-domain) chain cipher over 28 classes.

Model (research note C1, work/log/research_2026-10-17.md section 4): the ciphertext rune is the previous one plus a step
that is never zero,    D_i = c_i - c_{i-1}  (mod 29),   D_i in 1..28,
and the plaintext enters the STEP, keyed mod 28:
    variant A (additive):        D_i = 1 + ((q_i + m*K_j) mod 28)           q_i = plaintext class 0..27
    variant B (multiplicative):  D_i = 2^((q_i + m*L_j) mod 28) mod 29      L_j = log2(K_j), key values 0 have no log
                                 and are dropped from the stream (2 is a primitive root mod 29)
    variant C (rank):            c_i is the r_i-th of the 28 runes other than c_{i-1}, in alphabet order,
                                 r_i = (q_i + m*K_j) mod 28 (the cipher "never repeat the previous rune" built as a rank)
m runs over the units of Z28. A zero step (the 0.66% doublets) is the "ditto": it consumes no key value (mode `drop`) or
one key value (mode `keep`). The decoder is therefore a plain subtraction, no beam: for a window of steps the
class histogram of (J_t - m*K[o + idx_t]) mod 28 is counted at every (stream, offset), and a true key makes it
English-shaped (index of coincidence about 1.8 against 1.0). Every earlier screen worked in the c domain, where the
plaintext's random walk hides this family.

    python work/kscreen/step28.py screen  <library.ksb|rand:N:seed> <out.tsv> [--n 300] [--engine cuda|cpu]
    python work/kscreen/step28.py verify  <out.tsv> --out <verify.txt> [--top 5]
    python work/kscreen/step28.py selftest [--engine cuda|cpu]
    python work/kscreen/step28.py windows           # print the windows

Run from anywhere. Needs CuPy for --engine cuda (the CPU engine is the reference and the control).
"""
import argparse
import itertools
import math
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
WORK = HERE.parent
ROOT = WORK.parent
sys.path.insert(0, str(WORK))
sys.path.insert(0, str(HERE))
os.environ.setdefault("CUPY_CACHE_DIR", str(HERE / "target" / "cupy_cache"))
Q = 29
NC = 28
UNITS = [m for m in range(1, NC) if math.gcd(m, NC) == 1]          # 12 multipliers
LOG2 = np.zeros(Q, np.int64)                                       # discrete log base 2 mod 29 (index 0 unused)
for _e in range(NC):
    LOG2[pow(2, _e, Q)] = _e
POW2 = np.array([pow(2, e, Q) for e in range(NC)])
TPB = 128
NMAX = 512                                                         # longest window in steps

KERNEL = r"""
#define NB 28
#define TPB 128
extern "C" __global__ void step_kernel(const unsigned char* __restrict__ lib, const long long* __restrict__ sstart,
        const int* __restrict__ slen, const unsigned char* __restrict__ Jv, const short* __restrict__ Idx,
        int T, int need, int s0, int thr, unsigned long long* best, unsigned int* nhits,
        unsigned long long* hits, int maxhits)
{
    __shared__ unsigned char sJ[512];
    __shared__ short sI[512];
    __shared__ unsigned short h[NB][TPB];
    int tid = threadIdx.x;
    int s = s0 + blockIdx.y;
    int o = blockIdx.x * TPB + tid;
    for (int t = tid; t < T; t += TPB) { sJ[t] = Jv[t]; sI[t] = Idx[t]; }
    __syncthreads();
    if (o + need > slen[s]) return;
    for (int b = 0; b < NB; b++) h[b][tid] = 0;
    const unsigned char* k = lib + sstart[s] + o;
    for (int t = 0; t < T; t++) {
        int j = sJ[t];
        if (j == 255) continue;
        int d = j - (int)k[sI[t]];
        if (d < 0) d += NB;
        h[d][tid]++;
    }
    unsigned int ss = 0;
    for (int b = 0; b < NB; b++) { unsigned int v = h[b][tid]; ss += v * v; }
    unsigned long long packed = ((unsigned long long)ss << 40) | ((unsigned long long)s << 24) | (unsigned long long)o;
    atomicMax(best, packed);
    if ((int)ss >= thr) {
        unsigned int i = atomicAdd(nhits, 1u);
        if ((int)i < maxhits) hits[i] = packed;
    }
}
"""


# ------------------------------------------------------------------ model: encryption (controls) and the windows

def step_classes(c, prev, variant):
    """J_t (0..27, or 255 for a zero step) of the ciphertext steps D_t = c_t - c_{t-1} (c_{-1} = prev)."""
    c = np.asarray(c, np.int64)
    before = np.concatenate([[prev], c[:-1]])
    D = (c - before) % Q
    J = np.full(len(c), 255, np.int64)
    nz = D != 0
    if variant == "C":
        J[nz] = c[nz] - (c[nz] > before[nz])                         # rank among the runes other than the previous one
    else:
        J[nz] = (D[nz] - 1) if variant == "A" else LOG2[D[nz]]
    if prev < 0:
        J[0] = 255
    return J


def key_index(J, mode):
    """key index of every step: the number of key values consumed before it"""
    consumed = (J != 255) if mode == "drop" else np.ones(len(J), bool)
    return np.concatenate([[0], np.cumsum(consumed)[:-1]])


def key_arrays(streams, variant):
    """the key values the decoder reads, per stream: K mod 28 (A) or log2 K with the zeros removed (B)"""
    out = []
    for name, v in streams:
        v = np.asarray(v, np.int64)
        out.append((name, LOG2[v[v != 0]] if variant == "B" else v % NC))
    return out


def encrypt(q, key, variant, mode, m, o0, ditto, prev=3):
    """q: plaintext classes 0..27; ditto: bool per symbol (the symbol repeats the previous ciphertext rune)."""
    c, cur, j = [], prev, o0
    for qi, dit in zip(q, ditto):
        if dit:
            D = 0
            if mode == "keep":
                j += 1
        else:
            s = (int(qi) + m * int(key[j])) % NC
            j += 1
            if variant == "C":
                cur = s if s < cur else s + 1                           # the s-th rune other than the previous one
                c.append(cur)
                continue
            D = 1 + s if variant == "A" else int(POW2[s])
        cur = (cur + D) % Q
        c.append(cur)
    return np.array(c), prev


# ------------------------------------------------------------------ the screen (CPU reference and CUDA)

def ioc(ss, n):
    return NC * (ss - n) / (n * (n - 1)) if n > 1 else 0.0


def cpu_best(lib, J, idx, need, thr=None):
    """lib: [(name, K)] already multiplied; returns (best sum of squares, stream, offset, hits)"""
    best, hits = (-1, -1, -1), []
    valid = np.nonzero(J != 255)[0]
    for s, (_, K) in enumerate(lib):
        no = len(K) - need + 1
        if no <= 0:
            continue
        h = np.zeros((no, NC), np.int32)
        ar = np.arange(no)
        for t in valid:
            d = (J[t] - K[ar + idx[t]]) % NC
            h[ar, d] += 1
        ss = (h.astype(np.int64) ** 2).sum(1)
        o = no - 1 - int(np.argmax(ss[::-1]))                    # the last maximum, as atomicMax on the packed value
        if ss[o] > best[0] or (ss[o] == best[0] and (s, o) > (best[1], best[2])):
            best = (int(ss[o]), s, o)
        if thr is not None:
            for o2 in np.nonzero(ss >= thr)[0]:
                hits.append((int(ss[o2]), s, int(o2)))
    return best, hits


class Gpu:
    def __init__(self):
        import cupy as cp
        self.cp = cp
        self.kernel = cp.RawModule(code=KERNEL, options=("--std=c++14",)).get_function("step_kernel")
        self.cache = {}

    def upload(self, key, lib):
        cp = self.cp
        if key not in self.cache:
            flat = np.concatenate([v for _, v in lib]).astype(np.uint8)
            lens = np.array([len(v) for _, v in lib], np.int32)
            starts = np.concatenate([[0], np.cumsum(lens)[:-1]]).astype(np.int64)
            self.cache = {key: (cp.asarray(flat), cp.asarray(starts), cp.asarray(lens), lens)}
        return self.cache[key]

    def best(self, key, lib, J, idx, need, thr=None, max_hits=1 << 16):
        cp = self.cp
        d_lib, d_start, d_len, lens = self.upload(key, lib)
        T = len(J)
        dJ = cp.asarray(np.where(J == 255, 255, J).astype(np.uint8))
        dI = cp.asarray(idx.astype(np.int16))
        best = cp.zeros(1, cp.uint64)
        nh = cp.zeros(1, cp.uint32)
        hits = cp.zeros(max_hits, cp.uint64)
        gx = int(math.ceil(max(1, int(lens.max()) - need + 1) / TPB))
        chunk = 256                                                    # streams per launch: ~0.2 s at n = 300
        for s0 in range(0, len(lens), chunk):
            self.kernel((gx, min(chunk, len(lens) - s0)), (TPB,),
                        (d_lib, d_start, d_len, dJ, dI, np.int32(T), np.int32(need), np.int32(s0),
                         np.int32(thr if thr is not None else 1 << 30), best, nh, hits, np.int32(max_hits)))
        cp.cuda.Stream.null.synchronize()
        b = int(best.get()[0])
        hl = [int(x) for x in hits[:min(int(nh.get()[0]), max_hits)].get()]
        dec = lambda p: (p >> 40, (p >> 24) & 0xFFFF, p & 0xFFFFFF)
        return dec(b), [dec(p) for p in hl]


def windows_of(n):
    """non-overlapping windows of n steps over every unsolved section: (name, previous rune, runes)"""
    import lp
    import stats
    out = []
    for i in stats.UNSOLVED:
        c = np.array(lp.runes_of(stats.SEGS[i]))
        prev = int(lp.runes_of(stats.SEGS[i - 1])[-1]) if i > 7 else -1
        full = np.concatenate([[prev], c])
        for a in range(0, len(c) - n + 1, n):
            out.append((f"sec0.{i}@{a}", int(full[a]), c[a:a + n]))
    return out


def screen(lib_raw, wins, engine="cuda", variants=("A", "B", "C"), modes=("drop", "keep"), log=None, thr_ioc=None):
    """returns rows (window, variant, mode, m, ioc, stream name, offset) of the best (stream, offset) per setting"""
    gpu = Gpu() if engine == "cuda" else None
    rows = []
    for variant in variants:
        base = key_arrays(lib_raw, variant)
        for m in UNITS:
            lib = [(nm, ((m * K) % NC).astype(np.uint8)) for nm, K in base]
            for name, prev, runes in wins:
                for mode in modes:
                    J = step_classes(runes, prev, variant)
                    idx = key_index(J, mode)
                    n = int((J != 255).sum())
                    need = int(idx[J != 255].max()) + 1 if n else 1
                    thr = None if thr_ioc is None else int(math.ceil(thr_ioc * n * (n - 1) / NC + n))
                    if engine == "cuda":
                        (ss, s, o), hits = gpu.best((variant, m), lib, J, idx, need, thr)
                    else:
                        (ss, s, o), hits = cpu_best(lib, J, idx, need, thr)
                    rows.append((name, variant, mode, m, ioc(ss, n), lib[s][0] if s >= 0 else "-", o, hits, s))
            if log:
                log(f"variant {variant} m={m} done")
    return rows


def summarize(rows, wins):
    best = {}
    for r in rows:
        if r[0] not in best or r[4] > best[r[0]][4]:
            best[r[0]] = r
    return best


# ------------------------------------------------------------------ CLI

def load_library(spec):
    import gpu as kg
    if spec.startswith("rand:"):
        _, cnt, seed = spec.split(":")
        return kg.rand_streams(int(cnt), int(seed))
    return kg.load_ksb(spec)


def cmd_screen(a):
    wins = windows_of(a.n)
    lib = load_library(a.library)
    pairs = sum(max(0, len(v) - a.n) for _, v in lib)
    t0 = time.time()
    rows = screen(lib, wins, a.engine, variants=tuple(a.variants), log=lambda s: print(f"[{time.time() - t0:6.0f}s] {s}", file=sys.stderr, flush=True),
                  thr_ioc=a.thr)
    best = summarize(rows, wins)
    lib_label = os.path.relpath(a.library, ROOT).replace(os.sep, "/") if os.path.exists(a.library) else a.library
    lines = [f"# step28 library={lib_label} streams={len(lib)} pairs~{pairs} n={a.n} windows={len(wins)} engine={a.engine} "
             f"variants={','.join(a.variants)} modes=drop,keep multipliers={len(UNITS)}",
             "# window\tvariant\tmode\tm\tioc\tstream\toffset\tstream_index"]
    for r in rows:
        lines.append(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]:.4f}\t{r[5]}\t{r[6]}\t{r[8]}")
    for name, r in best.items():
        lines.append(f"# window {name} best {r[4]:.4f} variant={r[1]} mode={r[2]} m={r[3]} stream={r[5]} offset={r[6]} index={r[8]}")
    for r in rows:
        for ss, s, o in r[7]:
            lines.append(f"# hit {r[0]} {r[1]} {r[2]} m={r[3]} ss={ss} stream_index={s} offset={o}")
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    top = sorted(best.values(), key=lambda r: -r[4])[:5]
    print(f"{len(rows)} settings x windows; best per window, top 5: " + "; ".join(f"{r[0]} {r[4]:.3f}" for r in top))
    return 0


def cmd_verify(a):
    """Decode the section from the start of each of the best windows to its end with the winning setting: a true key keeps an
    index of coincidence near 1.8 beyond the window that selected it; a chance maximum falls back to 1.0."""
    import re
    import lp
    import stats
    head = Path(a.tsv).read_text(encoding="utf-8").split("\n")      # not splitlines(): stream names can hold control characters
    meta = dict(kv.split("=", 1) for kv in head[0].split()[2:] if "=" in kv)
    spec = meta["library"]
    lib = load_library(spec if spec.startswith("rand:") else str(ROOT / spec))
    pat = re.compile(r"# window (\S+) best ([\d.]+) variant=(\w) mode=(\w+) m=(\d+) stream=.* offset=(\d+) index=(\d+)")
    best = []
    for line in head:
        m = pat.match(line)
        if m:
            best.append((float(m.group(2)), m.group(1), m.group(3), m.group(4), int(m.group(5)), int(m.group(6)), int(m.group(7))))
    best.sort(reverse=True)

    def ioc_of(d):
        d = d[d >= 0]
        return ioc(int((np.bincount(d, minlength=NC) ** 2).sum()), len(d)) if len(d) > 1 else float("nan")

    out = [f"# step28 verification of the {a.top} best windows of {os.path.relpath(a.tsv, ROOT).replace(os.sep, '/')}: "
           "IoC of the decoded classes inside the window / beyond it, to the end of the section "
           "(a true key stays near 1.8, a chance maximum falls to 1.0)"]
    for _, name, variant, mode, m, o, si in best[:a.top]:
        sec, start = map(int, re.match(r"sec0\.(\d+)@(\d+)", name).groups())
        c = np.array(lp.runes_of(stats.SEGS[sec]))
        prev = int(c[start - 1]) if start else (int(lp.runes_of(stats.SEGS[sec - 1])[-1]) if sec > 7 else -1)
        J = step_classes(c[start:], prev, variant)
        idx = key_index(J, mode) + o
        K = key_arrays([lib[si]], variant)[0][1]
        okk = (J != 255) & (idx < len(K))
        dec = np.full(len(J), -1)
        dec[okk] = (J[okk] - m * K[idx[okk]]) % NC
        out.append(f"{name} {variant}/{mode} m={m} stream #{si} {lib[si][0]!r} offset {o}: window {ioc_of(dec[:a.n]):.3f}, "
                   f"beyond ({int((dec[a.n:] >= 0).sum())} steps) {ioc_of(dec[a.n:]):.3f}")
    Path(a.out).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("\n".join(out[:3]))
    return 0


def plant_case(rng, variant, mode, m, n=300):
    """a window of steps built from Emerson classes under a known library stream: returns (stream list, window, truth)"""
    import attack
    import lp
    toks = attack.synthetic_tokens(2 * n + 50, start=int(rng.integers(5000, 40000)))
    p = np.array(lp.runes_of(toks))
    p = np.where(p == 14, 6, p)                                  # the rarest rune (X) is the ditto symbol, never plaintext
    q = np.where(p > 14, p - 1, p)
    q = q[:n]
    ditto = rng.random(n) < 0.0066
    streams = [(f"RANDOM {i}", rng.integers(0, Q, 2500, dtype=np.int64).astype(np.uint8)) for i in range(5)]
    arr = dict(key_arrays(streams, variant))
    si = int(rng.integers(0, 5))
    key = arr[streams[si][0]]
    o0 = int(rng.integers(0, 1200))
    c, prev = encrypt(q, key, variant, mode, m, o0, ditto)
    return streams, ("plant", prev, c), (streams[si][0], o0)


def cmd_selftest(a):
    rng = np.random.default_rng(5)
    ok = True
    # control 1: CPU and CUDA agree on a random library and a real window (when CUDA is requested)
    wins = windows_of(300)[:2]
    lib = [(f"R{i}", rng.integers(0, Q, 1500, dtype=np.int64).astype(np.uint8)) for i in range(6)]
    cpu = screen(lib, wins, "cpu", variants=("A",), modes=("drop",))
    cpu_null = max(r[4] for r in cpu)
    if a.engine == "cuda":
        gpu = screen(lib, wins, "cuda", variants=("A",), modes=("drop",))
        same = all((x[0], x[1], x[2], x[3], round(x[4], 6), x[5], x[6]) == (y[0], y[1], y[2], y[3], round(y[4], 6), y[5], y[6])
                   for x, y in zip(cpu, gpu))
        print(f"CPU == CUDA on a random library ({len(cpu)} settings): {same}")
        ok &= same
    # control 2 (null): random keys on real windows stay far below a planted key
    print(f"null: best IoC of 6 random streams x 12 multipliers x 2 real windows = {cpu_null:.3f} (expect < 1.20)")
    ok &= cpu_null < 1.20
    # control 3 (positive): every variant/mode recovered at the exact stream and offset, for two multipliers
    for variant, mode in itertools.product(("A", "B", "C"), ("drop", "keep")):
        for m in (1, 5):
            streams, w, (sname, o0) = plant_case(rng, variant, mode, m)
            rows = screen(streams, [("plant", w[1], w[2])], a.engine, variants=(variant,), modes=(mode,))
            top = max(rows, key=lambda r: r[4])
            good = top[3] == m and top[5] == sname and top[6] == o0 and top[4] > 1.5
            print(f"plant {variant}/{mode} m={m}: recovered {top[5]} offset {top[6]} m={top[3]} IoC {top[4]:.3f}  "
                  f"(truth {sname} {o0}) {'OK' if good else 'FAIL'}")
            ok &= good
    # control 4 (blindness of the other family): the wrong variant does not see the key
    streams, w, (sname, o0) = plant_case(rng, "A", "drop", 1)
    rows = screen(streams, [("plant", w[1], w[2])], a.engine, variants=("B",), modes=("drop",))
    wrong = max(r[4] for r in rows)
    print(f"plant A read as B: best IoC {wrong:.3f} (expect < 1.3)")
    ok &= wrong < 1.3
    print("SELFTEST " + ("PASSED" if ok else "FAILED"))
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("screen")
    s.add_argument("library")
    s.add_argument("out")
    s.add_argument("--n", type=int, default=300)
    s.add_argument("--engine", choices=["cuda", "cpu"], default="cuda")
    s.add_argument("--variants", default="ABC", help="e.g. AC for a native mod-28 library (variant B reads logs of Z29 values)")
    s.add_argument("--thr", type=float, default=None, help="record every (stream, offset) with IoC >= thr")
    v = sub.add_parser("verify")
    v.add_argument("tsv")
    v.add_argument("--top", type=int, default=5)
    v.add_argument("--n", type=int, default=300)
    v.add_argument("--out", required=True)
    t = sub.add_parser("selftest")
    t.add_argument("--engine", choices=["cuda", "cpu"], default="cuda")
    sub.add_parser("windows")
    a = ap.parse_args()
    if a.cmd == "windows":
        for name, prev, runes in windows_of(300):
            print(name, prev, len(runes))
        return 0
    return {"screen": cmd_screen, "verify": cmd_verify, "selftest": cmd_selftest}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
