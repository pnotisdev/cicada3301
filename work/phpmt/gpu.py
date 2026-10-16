#!/usr/bin/env python3
"""CUDA port of the phpmt seed sweep (CuPy + NVRTC). The Rust engine (src/main.rs) stays the reference: this reproduces
its scores decode for decode (see tests/test_phpmt_gpu.py) and writes the same TSV.

    python work/phpmt/gpu.py sweep  <gen> <windows.txt> <dict.txt> <lo> <hi> <out.tsv> [threads]   (as the Rust `sweep`)
    python work/phpmt/gpu.py raw    <gen> <lo> <hi> <out.txt>                                        (as the Rust `raw`; php/glibc/net)
    python work/phpmt/gpu.py keys   <gen> <lo> <hi> <out.txt>                                        (as the Rust `keys`; every generator)
    python work/phpmt/gpu.py scores <gen> <windows.txt> <dict.txt> <lo> <hi> <out.txt>               (as the Rust `scores`)
    python work/phpmt/gpu.py probe | selfcheck

gen is php (mt_rand before PHP 7.1), glibc (random() / PHP 5 rand() on Linux), net (.NET System.Random), py3 (CPython
random.seed(n)), mt32 (std::mt19937 / PHP >= 7.1), mt31, java (java.util.Random), msvc (rand()), drand48 (drand48 / Perl) or
ruby (Ruby <= 2.7): the rules are in work/phpmt/src/gens.rs.
`threads` is accepted and ignored. Needs cupy-cuda12x, an NVIDIA driver and NVRTC (see requirements-gpu.txt).
"""
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
os.environ.setdefault("CUPY_CACHE_DIR", str(HERE / "target" / "cupy_cache"))      # git-ignored build folder
import gpu_common  # noqa: E402
from gpu_common import NVRTC_OPTIONS  # noqa: E402

WLEN, WMAX, HB = 60, 64, 64
BLOCK = 128
CCAP = 1 << 22                  # candidate records per launch
TARGET_S = 0.3                  # seconds per launch (Windows' display watchdog resets the GPU after ~2 s)
TOPK = 4000
THR0 = 8                        # lowest score recorded at first; raised to the 4000th best once there are 4000
KERNEL = HERE / "phpmt.cu"
BIN = HERE / "target" / "release" / ("phpmt.exe" if os.name == "nt" else "phpmt")
GENS = {"php": 0, "glibc": 1, "net": 2, "py3": 3, "mt32": 4, "mt31": 5, "java": 6, "msvc": 7, "drand48": 8, "ruby": 9}


def load_windows(path):
    """As the Rust load_windows: W/R/L triples; n = word-aligned cut at <= 60 runes, abort1/abort2 early-exit points."""
    lines, out, i = Path(path).read_text(encoding="utf-8").splitlines(), [], 0
    while i < len(lines):
        if not lines[i].startswith("W "):
            i += 1
            continue
        f = lines[i].split()
        r = [int(x) for x in lines[i + 1][2:].split()]
        ln = [int(x) for x in lines[i + 2][2:].split()]
        i += 3
        end, pos = [False] * len(r), 0
        for x in ln:
            pos += x
            end[pos - 1] = True
        assert pos == len(r)
        n = abort1 = abort2 = long_words = start = 0
        for k in range(len(r)):
            if end[k]:
                if k + 1 <= WLEN:
                    n = k + 1
                if k + 1 - start >= 3:
                    long_words += 1
                    if long_words == 2 and abort1 == 0:
                        abort1 = k + 1
                if abort2 == 0 and k + 1 >= 30:
                    abort2 = k + 1
                start = k + 1
        out.append({"name": f[1], "prev": int(f[2]), "runes": r, "end": end, "n": n, "a1": abort1, "a2": abort2})
    return out


def load_dict(path):
    by_len = [[] for _ in range(13)]
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        a, b = line.split()
        if int(a) < 13:
            by_len[int(a)].append(int(b))
    start = np.cumsum([0] + [len(v) for v in by_len]).astype(np.uint32)
    codes = np.array([c for v in by_len for c in sorted(v)] or [0], np.uint64)
    return codes, start


def variant_parts(v):
    return (v >> 3) & 1, (v >> 2) & 1, 1 if (v >> 1) & 1 == 0 else -1, v & 1       # model, map, sign, atbash


class Sweep:
    def __init__(self, gen, windows_path, dict_path, dump=0):
        import cupy as cp
        self.cp, self.gen = cp, gen
        self.wins = load_windows(windows_path)
        nw = len(self.wins)
        defs = {"GEN": GENS[gen], "NW": nw, "DUMP": dump}
        src = "".join(f"#define {k} {v}\n" for k, v in defs.items()) + KERNEL.read_text(encoding="utf-8")
        self.kernel = cp.RawModule(code=src, options=NVRTC_OPTIONS).get_function("sweep_kernel")
        runes = np.zeros((nw, WMAX), np.uint8)
        end = np.zeros((nw, WMAX), np.uint8)
        meta = np.zeros((nw, 4), np.int32)
        for k, w in enumerate(self.wins):
            m = min(len(w["runes"]), WMAX)
            runes[k, :m] = w["runes"][:m]
            end[k, :m] = w["end"][:m]
            meta[k] = (w["prev"], w["n"], w["a1"], w["a2"])
        codes, start = load_dict(dict_path)
        self.d = [cp.asarray(runes.ravel()), cp.asarray(end.ravel()), cp.asarray(meta.ravel()), cp.asarray(codes),
                  cp.asarray(start)]
        self.hist = cp.zeros(HB, cp.uint64)
        self.cand = cp.zeros(2 * CCAP, cp.uint32)
        self.ccount = cp.zeros(1, cp.uint32)

    def launch(self, seed0, n, thr, dump=None):
        cp = self.cp
        self.ccount[:] = 0
        self.kernel(((n + BLOCK - 1) // BLOCK,), (BLOCK,), (
            *self.d, np.uint64(seed0), np.uint64(n), np.uint32(thr), self.hist, self.cand, self.ccount, np.uint32(CCAP),
            dump if dump is not None else self.cand))
        cp.cuda.Stream.null.synchronize()
        return int(self.ccount[0])


def mode_sweep(a):
    gen, win, dic, lo, hi, out = a[0], a[1], a[2], int(a[3]), int(a[4]), a[5]
    S = Sweep(gen, win, dic)
    cp = S.cp
    info = gpu_common.device_info()
    print(f"phpmt: {gen} sweep of {hi - lo} seeds, {len(S.wins)} windows x 16 variants on CUDA {info['name']}",
          file=sys.stderr, flush=True)
    cand = np.zeros((0, 2), np.uint32)
    hist = np.zeros(HB, np.uint64)
    t_start = last = time.time()
    done, chunk, thr = 0, 1 << 14, THR0
    total = hi - lo
    while done < total:
        n = min(chunk, total - done)
        while True:
            S.hist[:] = 0
            t1 = time.time()
            cnt = S.launch(lo + done, n, thr)
            dt = time.time() - t1
            if cnt <= CCAP:
                break
            thr += 1                                              # too many candidates for the buffer: raise the floor, redo
        hist += S.hist.get()
        if cnt:
            cand = np.concatenate([cand, S.cand[:2 * cnt].get().reshape(cnt, 2)])
            if len(cand) > 4 * TOPK:
                score = cand[:, 1] >> 16
                keep = np.argpartition(-score.astype(np.int64), TOPK - 1)[:TOPK]
                kth = int(np.sort(score[keep])[0])
                cand = cand[score >= kth]                           # keeps every candidate tied with the TOPK-th
            if len(cand) >= TOPK:
                thr = max(thr, int(np.sort(cand[:, 1] >> 16)[-TOPK]))
        done += n
        chunk = int(min(max(chunk * min(2.0, TARGET_S / max(dt, 1e-3)), 1 << 10), 1 << 24))
        if time.time() - last >= 20:
            last = time.time()
            el, frac = last - t_start, done / total
            print(f"{100 * frac:.2f}% ({done} seeds) {done / el:.0f} seeds/s, eta {el * (1 - frac) / max(frac, 1e-9):.0f} s",
                  file=sys.stderr, flush=True)
    secs = time.time() - t_start
    # best TOPK by score; ties in a deterministic order (seed, window, variant)
    order = np.lexsort((cand[:, 1] & 0xFFFF, cand[:, 0], -(cand[:, 1] >> 16).astype(np.int64)))[:TOPK]
    rows = ["score\tseed\twindow\tmodel\tmap\tsign\tatbash"]
    for seed, packed in cand[order]:
        s, wi, v = int(packed) >> 16, (int(packed) >> 8) & 0xFF, int(packed) & 0xFF
        model, mp, sign, atb = variant_parts(v)
        rows.append(f"{s}\t{int(seed)}\t{S.wins[wi]['name']}\t{model}\t{mp}\t{sign}\t{atb}")
    Path(out).write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    best = int(cand[order[0], 1] >> 16) if len(order) else 0
    print(f"swept {total} seeds in {secs:.0f} s; best score {best}", file=sys.stderr, flush=True)
    print("hist " + " ".join(f"{b}:{int(c)}" for b, c in enumerate(hist) if c), file=sys.stderr, flush=True)


def mode_scores(a):
    gen, win, dic, lo, hi, out = a[0], a[1], a[2], int(a[3]), int(a[4]), a[5]
    S = Sweep(gen, win, dic, dump=1)
    cp, nw = S.cp, len(S.wins)
    lines, step = [], 1 << 14
    for s0 in range(lo, hi, step):
        n = min(step, hi - s0)
        d = cp.zeros(n * nw * 16, cp.uint32)
        S.launch(s0, n, 1 << 30, d)
        d = d.get().reshape(n, nw, 16)
        for g in range(n):
            for wi in range(nw):
                lines.extend(f"{s0 + g} {wi} {v} {d[g, wi, v]}" for v in range(16))
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def mode_raw(a):
    gen, lo, hi, out = a[0], int(a[1]), int(a[2]), a[3]
    S = Sweep(gen, str(HERE / "data" / "windows.txt"), str(HERE / "data" / "dict.txt"), dump=2)
    cp, lines, step = S.cp, [], 1 << 14
    for s0 in range(lo, hi, step):
        n = min(step, hi - s0)
        d = cp.zeros(n * 160, cp.uint32)
        S.launch(s0, n, 1 << 30, d)
        d = d.get().reshape(n, 160)
        lines.extend(f"{s0 + g} " + " ".join(map(str, d[g])) for g in range(n))
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def mode_keys(a):
    gen, lo, hi, out = a[0], int(a[1]), int(a[2]), a[3]
    S = Sweep(gen, str(HERE / "data" / "windows.txt"), str(HERE / "data" / "dict.txt"), dump=3)
    cp, lines, step = S.cp, [], 1 << 13
    for s0 in range(lo, hi, step):
        n = min(step, hi - s0)
        d = cp.zeros(n * 2 * 160, cp.uint32)
        S.launch(s0, n, 1 << 30, d)
        d = d.get().reshape(n, 2 * 160)
        lines.extend(f"{s0 + g} " + " ".join(map(str, d[g])) for g in range(n))
    Path(out).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


# seed ranges for the generator checks: small seeds, the 2^31 and 2^32 edges
RAW_RANGES = [(0, 300), (2147483600, 2147483700), (4294967200, 4294967296)]
SCORE_RANGES = [(0, 500), (123456789, 123456989), (4294966800, 4294967296)]


def mode_selfcheck():
    import subprocess
    import tempfile
    if not BIN.exists():
        print("selfcheck needs the CPU engine: cargo build --release in work/phpmt")
        return 1
    win, dic = str(HERE / "data" / "windows.txt"), str(HERE / "data" / "dict.txt")
    with tempfile.TemporaryDirectory() as d:
        ca, cb = os.path.join(d, "cpu.txt"), os.path.join(d, "gpu.txt")
        for gen in GENS:
            for lo, hi in RAW_RANGES:
                if GENS[gen] <= 2:
                    subprocess.run([str(BIN), "raw", gen, str(lo), str(hi), ca], check=True)
                    mode_raw([gen, str(lo), str(hi), cb])
                    if Path(ca).read_text() != Path(cb).read_text():
                        print(f"MISMATCH: raw {gen} outputs of seeds {lo}..{hi}")
                        return 1
                subprocess.run([str(BIN), "keys", gen, str(lo), str(hi), ca], check=True)
                mode_keys([gen, str(lo), str(hi), cb])
                if Path(ca).read_text() != Path(cb).read_text():
                    print(f"MISMATCH: key values (both maps) of {gen} for seeds {lo}..{hi}")
                    return 1
            print(f"identical: key values of {gen} for {sum(h - l for l, h in RAW_RANGES)} seeds (incl. the 2^31/2^32 edges)")
            for lo, hi in SCORE_RANGES:
                subprocess.run([str(BIN), "scores", gen, win, dic, str(lo), str(hi), ca], check=True)
                mode_scores([gen, win, dic, str(lo), str(hi), cb])
                x, y = Path(ca).read_text(), Path(cb).read_text()
                if x != y or not x:
                    bad = next((i for i, (p, q) in enumerate(zip(x.splitlines(), y.splitlines())) if p != q), None)
                    print(f"MISMATCH: scores {gen} seeds {lo}..{hi}, first difference at line {bad}")
                    return 1
            n_dec = sum(h - l for l, h in SCORE_RANGES) * 128
            print(f"identical: {n_dec} decode scores of {gen}")
    print("GPU selfcheck passed")
    return 0


def main():
    a = sys.argv[1:]
    modes = {"sweep": (mode_sweep, 7), "scores": (mode_scores, 7), "raw": (mode_raw, 5), "keys": (mode_keys, 5)}
    if a and a[0] == "probe":
        return gpu_common.probe()
    if a and a[0] == "selfcheck":
        return mode_selfcheck()
    if a and a[0] in modes and len(a) >= modes[a[0]][1] - (1 if a[0] == "sweep" else 0):
        modes[a[0]][0](a[1:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
