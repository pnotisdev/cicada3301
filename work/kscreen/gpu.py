#!/usr/bin/env python3
"""CUDA port of the kscreen screen (CuPy + NVRTC). The Rust engine (src/main.rs) stays the reference: this
reproduces its decodes bit for bit (see tests/test_kscreen_gpu.py) and writes the same TSV.

    python work/kscreen/gpu.py screen <windows.txt> <family> <out.tsv> [key=value ...]   (as the Rust `screen`)
    python work/kscreen/gpu.py trace  <windows.txt> <family> <out.txt>  [key=value ...]  (as the Rust `trace`)
    python work/kscreen/gpu.py probe                 # is CUDA usable? (prints one line, exit 0 if so)
    python work/kscreen/gpu.py selfcheck             # decode-by-decode comparison with the CPU engine; exit 0 if equal

Run from work/kscreen (the paths in the arguments are relative to it, as for the Rust engine). `threads=` is accepted
and ignored. Needs: pip install cupy-cuda12x, an NVIDIA driver, and the NVRTC library (CUDA Toolkit 12.x or
nvidia-cuda-nvrtc-cu12).
"""
import math
import os
import struct
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import gpu_common  # noqa: E402
from gpu_common import NVRTC_OPTIONS, device_info  # noqa: E402
os.environ.setdefault("CUPY_CACHE_DIR", str(HERE / "target" / "cupy_cache"))   # git-ignored build folder
Q = 29
HBINS = 400
BLOCK = 32                  # one warp per block: the fast path's shared-memory counts are per lane
HCAP = 1 << 23              # hit records per launch; chunks are sized so that this can never overflow
TARGET_S = 0.3              # seconds per kernel launch: short enough for Windows' display watchdog (TDR, ~2 s)
KERNEL = HERE / "kscreen.cu"
BIN = HERE / "target" / "release" / ("kscreen.exe" if os.name == "nt" else "kscreen")


# ------------------------------------------------------------------ inputs (same formats as the Rust engine)

def load_windows(path):
    wins = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if line.startswith("W "):
            p = line[2:].split()
            wins.append({"name": p[0], "prev": int(p[1]) if len(p) > 1 else -1, "runes": np.zeros(0, np.uint8), "pv": None})
        elif line.startswith("R "):
            wins[-1]["runes"] = np.array(line[2:].split(), dtype=np.uint8)
        elif line.startswith("P "):
            wins[-1]["pv"] = np.array(line[2:].split(), dtype=np.int8)
        elif line.startswith("G "):
            raise SystemExit(f"{path}: G lines (self-key guard) are only supported by the Rust engine")
        elif line.startswith("S "):
            raise SystemExit(f"{path}: S lines (per-rune key signs) are only supported by the Rust engine")
    for w in wins:
        assert (w["runes"] < Q).all(), f"{w['name']}: rune out of range"
        if w["pv"] is None:                       # default: compare with the previous rune (as the Rust engine)
            w["pv"] = np.concatenate([[w["prev"]], w["runes"][:-1]]).astype(np.int8)
        assert len(w["pv"]) == len(w["runes"]), f"{w['name']}: P line length"
    return wins


def load_ksb(path):
    b = Path(path).read_bytes()
    assert b[:4] == b"KSB1", f"{path}: not a KSB1 keystream file"
    (n,), p, out = struct.unpack_from("<I", b, 4), 8, []
    for _ in range(n):
        (ln,) = struct.unpack_from("<H", b, p)
        name = b[p + 2:p + 2 + ln].decode("utf-8")
        p += 2 + ln
        (kl,) = struct.unpack_from("<I", b, p)
        v = np.frombuffer(b, np.uint8, kl, p + 4)
        p += 4 + kl
        assert (v < Q).all(), f"{name}: key value out of range"
        out.append((name, v))
    return out


def rand_streams(count, seed):
    """The Rust `rand:<count>:<seed>` family: splitmix64 is a counter, so the whole stream is one array expression."""
    n = count * 20000
    with np.errstate(over="ignore"):
        z = np.uint64(seed ^ 0x05EE_D5EE_D5EE_D5EE) + np.arange(1, n + 1, dtype=np.uint64) * np.uint64(0x9E37_79B9_7F4A_7C15)
        z = (z ^ (z >> np.uint64(30))) * np.uint64(0xBF58_476D_1CE4_E5B9)
        z = (z ^ (z >> np.uint64(27))) * np.uint64(0x94D0_49BB_1331_11EB)
        z = z ^ (z >> np.uint64(31))
        v = (((z >> np.uint64(32)) * np.uint64(Q)) >> np.uint64(32)).astype(np.uint8)
    return [(f"RANDOM {i}", v[i * 20000:(i + 1) * 20000]) for i in range(count)]


class Fam:
    def __init__(self, spec):
        kind, _, arg = spec.partition(":")
        self.kind, self.d, self.ks = kind, 0, []
        if kind == "file":
            self.kind, self.ks = "ks", load_ksb(arg)
        elif kind == "rand":
            cnt, _, seed = arg.partition(":")
            self.kind, self.ks = "ks", rand_streams(int(cnt), int(seed or 1))
        elif kind in ("lin", "poly"):
            self.d = int(arg)
            assert 1 <= self.d <= 4
        else:
            raise SystemExit(f"unknown family {spec}")

    def items(self):
        return len(self.ks) if self.kind == "ks" else 28 * Q ** (self.d - 1) if self.kind == "lin" else Q ** self.d - 1

    def offsets(self, item, need):
        if self.kind == "ks":
            return max(0, len(self.ks[item][1]) + 1 - need)
        return Q ** self.d - 1 if self.kind == "lin" else Q

    def coeffs(self, item):
        d = self.d
        if self.kind == "lin":
            a, x = [0] * d, item // 28
            a[d - 1] = item % 28 + 1
            for e in range(d - 1):
                a[e], x = x % Q, x // Q
            return a
        if self.kind == "poly":
            a, x = [], item + 1
            for _ in range(d):
                a.append(x % Q)
                x //= Q
            return a
        return []

    def item_name(self, item):
        if self.kind == "ks":
            return self.ks[item][0]
        return f"{self.kind}{self.d}:" + ",".join(map(str, self.coeffs(item)))

    def offset_name(self, off):
        if self.kind != "lin":
            return str(off)
        x, s = off + 1, []
        for _ in range(self.d):
            s.append(x % Q)
            x //= Q
        return "state=" + ",".join(map(str, s))

    def find_item(self, name):
        for i in range(self.items()):
            if self.item_name(i) == name:
                return i
        raise SystemExit(f"no keystream named {name!r}")


def opts(args):
    o = dict(a.split("=", 1) for a in args)
    if o.get("clock", "none") != "none":
        raise SystemExit("clock= (clocked key pointer) is only supported by the Rust engine")
    if o.get("nulledge", "0") != "0":
        raise SystemExit("nulledge= (word-edge keyless nulls) is only supported by the Rust engine")
    return o


def list_u8(s):
    return list(range(1, Q)) if s == "all" else [int(x) for x in s.split(",")]


def abort_of(spec):
    if spec == "0":
        return 0, 0
    a, b = spec.split(":")
    at = int(a)
    return at, math.ceil(float(b) * at * (at - 1.0) / Q)


# ------------------------------------------------------------------ GPU setup


class Setup:
    """Windows, family and options -> device arrays and the compiled kernel."""

    def __init__(self, win_path, fam_spec, o, dump=False):
        import cupy as cp
        self.cp = cp
        all_wins = load_windows(win_path)
        self.fam = fam = Fam(fam_spec)
        n_req, self.beam = int(o.get("n", 300)), int(o.get("beam", 16))
        self.mults = list_u8(o.get("mults", "1,28"))
        self.models = list_u8(o.get("models", "0,1"))
        assert all(m <= 1 for m in self.models) and all(1 <= m < Q for m in self.mults)
        self.top = int(o.get("top", 2000))
        self.spec_abort = o.get("abort", "150:1.2")
        abort_at, self.abort_s = abort_of(self.spec_abort)
        self.wins = [w for w in all_wins if len(w["runes"]) >= int(o.get("minlen", 50))]
        self.wn = [min(len(w["runes"]), n_req) for w in self.wins]
        self.nmax = max(self.wn)
        self.need = self.nmax + self.nmax // 4 + 8
        wab = [abort_at if 0 < abort_at < n else 0 for n in self.wn]
        if "only" in o:
            self.items = [fam.find_item(o["only"])]
        elif "items" in o:
            a, b = o["items"].split(":")
            self.items = list(range(int(a), min(int(b), fam.items())))
        else:
            self.items = list(range(fam.items()))
        self.dpt = len(self.models) * len(self.wins)              # decodes per task
        defs = {"NEED": self.need, "BEAM": self.beam, "NW": len(self.wins), "NMODEL": len(self.models),
                "NMULT": len(self.mults), "MODE": {"ks": 0, "lin": 1, "poly": 2}[fam.kind], "ORD": fam.d,
                "HBINS": HBINS, "DUMP": int(dump), "SBLK": BLOCK, "BACK": int(o.get("dir") == "back")}
        src = "".join(f"#define {k} {v}\n" for k, v in defs.items()) + KERNEL.read_text(encoding="utf-8")
        self.module = cp.RawModule(code=src, options=NVRTC_OPTIONS)
        self.kernel = self.module.get_function("screen_kernel")
        self.fallback = self.module.get_function("fallback_kernel")
        u8, u32, i32 = (lambda a: cp.asarray(np.ascontiguousarray(a, np.uint8)),
                        lambda a: cp.asarray(np.ascontiguousarray(a, np.uint32)),
                        lambda a: cp.asarray(np.ascontiguousarray(a, np.int32)))
        self.d_runes = u8(np.concatenate([w["runes"][:n] for w, n in zip(self.wins, self.wn)]))
        self.d_wstart = u32(np.concatenate([[0], np.cumsum(self.wn)[:-1]]))
        self.d_wn, self.d_wab = u32(self.wn), u32(wab)
        self.d_pv = cp.asarray(np.ascontiguousarray(np.concatenate([w["pv"][:n] for w, n in zip(self.wins, self.wn)]), np.int8))
        self.d_mults, self.d_models = u8(self.mults), u8(self.models)
        if fam.kind == "ks":
            lib = np.concatenate([v for _, v in fam.ks]) if fam.ks else np.zeros(1, np.uint8)
            base = np.concatenate([[0], np.cumsum([len(v) for _, v in fam.ks])]).astype(np.uint64)
            self.d_lib, self.ibase = u8(lib), base
        else:
            self.d_lib, self.ibase = u8(np.zeros(1)), None
        coef = np.zeros((len(self.items), 4), np.uint8)
        if fam.kind != "ks":
            for k, it in enumerate(self.items):
                coef[k, :fam.d] = fam.coeffs(it)
        self.d_coef = u8(coef)

    def plan(self, offs=None):
        """Per item: first offset and offset count (offs=(a, b) restricts them, as the Rust trace does)."""
        o0, cnt = [], []
        for it in self.items:
            n = self.fam.offsets(it, self.need)
            a, b = (0, n) if offs is None else (offs[0], min(offs[1], n))
            o0.append(a)
            cnt.append(max(0, b - a))
        cnt = np.array(cnt, np.int64)
        pre = np.concatenate([[0], np.cumsum(cnt)])
        return np.array(o0, np.uint32), pre, int(pre[-1])

    def new_bufs(self):
        cp = self.cp
        return {"hist": cp.zeros(HBINS, cp.uint64), "wbest": cp.zeros(len(self.wins), cp.uint64),
                "hcount": cp.zeros(1, cp.uint32), "hits": cp.zeros(3 * HCAP, cp.uint32), "ab": cp.zeros(1, cp.uint64),
                "fb": cp.zeros(2 * HCAP, cp.uint32), "fbcount": cp.zeros(1, cp.uint32)}

    def launch(self, ntasks, t0, pre, ioff0, thr, bufs, dump=None):
        """Fast kernel over tasks t0 .. t0+ntasks, then the fallback kernel over the decodes it queued. Returns their number."""
        cp = self.cp
        if "pre" not in bufs:                                     # per-run arrays, indexed by position in the item list
            bufs["pre"] = cp.asarray(pre[:-1].astype(np.uint64))
            bufs["ioff"] = cp.asarray(ioff0)
            pos = [self.ibase[i] for i in self.items] if self.fam.kind == "ks" else [0] * len(self.items)
            bufs["ibase"] = cp.asarray(np.array(pos, np.uint64))
        common = (self.d_lib, bufs["ibase"], bufs["pre"], bufs["ioff"], self.d_coef, np.int32(len(self.items)), np.uint64(t0))
        data = (self.d_runes, self.d_wstart, self.d_wn, self.d_pv, self.d_wab, self.d_mults, self.d_models,
                np.uint32(self.abort_s), np.float32(thr))
        outs = (bufs["hist"], bufs["wbest"], bufs["hcount"], bufs["hits"], np.uint32(HCAP), bufs["ab"],
                dump if dump is not None else bufs["hits"])
        bufs["fbcount"][:] = 0
        self.kernel(((ntasks + BLOCK - 1) // BLOCK,), (BLOCK,),
                    common + (np.uint64(ntasks),) + data + outs + (bufs["fb"], bufs["fbcount"], np.uint32(HCAP)))
        nfb = int(bufs["fbcount"][0])
        assert nfb <= HCAP, "fallback queue overflow (cannot happen: chunks are sized to the buffer)"
        if nfb:
            self.fallback(((nfb + 127) // 128,), (128,), common + data + outs + (bufs["fb"], np.uint32(nfb)))
        return nfb

    def locate(self, tasks, pre, ioff0):
        """Global task numbers -> (absolute item, offset, multiplier)."""
        tasks = np.asarray(tasks, np.uint64)
        mi, io = tasks % len(self.mults), tasks // len(self.mults)
        k = np.searchsorted(pre[:-1], io.astype(np.int64), side="right") - 1
        off = ioff0[k].astype(np.int64) + (io.astype(np.int64) - pre[k])
        return np.array(self.items)[k], off, np.array(self.mults)[mi.astype(np.int64)]


# ------------------------------------------------------------------ screen

def mode_screen(args):
    o = opts(args[3:])
    S = Setup(args[0], args[1], o)
    cp, fam = S.cp, S.fam
    ioff0, pre, n_off = S.plan()
    total_tasks = n_off * len(S.mults)
    if total_tasks * 2 >= 2 ** 32:
        raise SystemExit(f"{total_tasks} tasks are too many for one run; split it with items=a:b")
    total_runs = total_tasks * S.dpt
    info = device_info()
    print(f"kscreen: {len(S.items)} items, {len(S.wins)} windows (n<={S.nmax}), mults {S.mults}, models {S.models}, "
          f"{total_runs} decodes, CUDA {info['name']}", file=sys.stderr, flush=True)
    bufs = S.new_bufs()
    hb, ht, hw = np.zeros(0, np.uint32), np.zeros(0, np.uint32), np.zeros(0, np.uint32)
    t_start = last = time.time()
    done, chunk, thr = 0, 1 << 12, 0.0
    max_chunk = max(1, HCAP // S.dpt)
    while done < total_tasks:
        n = min(chunk, total_tasks - done, max_chunk)
        bufs["hcount"][:] = 0
        t1 = time.time()
        S.launch(n, done, pre, ioff0, thr, bufs)
        cp.cuda.Stream.null.synchronize()
        dt = time.time() - t1
        hc = int(bufs["hcount"][0])
        assert hc <= HCAP, "hit buffer overflow (cannot happen: chunks are sized to the buffer)"
        if hc:
            h = bufs["hits"][:3 * hc].get().reshape(hc, 3)
            hb, ht, hw = np.concatenate([hb, h[:, 0]]), np.concatenate([ht, h[:, 1]]), np.concatenate([hw, h[:, 2]])
            if len(hb) > 4 * S.top:
                keep = np.argpartition(-hb.view(np.float32), S.top - 1)[:S.top]
                hb, ht, hw = hb[keep], ht[keep], hw[keep]
            if len(hb) >= S.top:
                thr = float(np.partition(hb.view(np.float32), len(hb) - S.top)[len(hb) - S.top])
        done += n
        chunk = int(min(max(chunk * min(2.0, TARGET_S / max(dt, 1e-3)), 1 << 10), 1 << 24))
        if time.time() - last >= 20:
            last = time.time()
            el, frac = last - t_start, done / total_tasks
            print(f"{100 * frac:6.2f}% ({done * S.dpt} decodes) {done * S.dpt / el:.0f} decodes/s, "
                  f"eta {el * (1 - frac) / max(frac, 1e-9):.0f} s", file=sys.stderr, flush=True)
    secs = time.time() - t_start
    hist, wbest, aborted = bufs["hist"].get(), bufs["wbest"].get(), int(bufs["ab"][0])
    order = np.argsort(-hb.view(np.float32), kind="stable")[:S.top]
    hb, ht, hw = hb[order], ht[order], hw[order]
    items, offs, mults = S.locate(ht, pre, ioff0)
    best = float(hb.view(np.float32)[0]) if len(hb) else 0.0
    out = [f"# kscreen screen family={args[1]} windows={args[0]} n={S.nmax} beam={S.beam} mults={','.join(map(str, S.mults))} "
           f"models={','.join(map(str, S.models))} abort={S.spec_abort} runs={total_runs} aborted={aborted} secs={secs:.0f} "
           f"dir={'back' if o.get('dir') == 'back' else 'fwd'} device=cuda", f"# best {best:.4f}"]
    for wi, w in enumerate(S.wins):
        key = int(wbest[wi])
        if key == 0:
            out.append(f"# window {w['name']} best 0.0000 item=- offset={fam.offset_name(0)} mult=0 model=0")
            continue
        f = np.uint32(key >> 32).view(np.float32)
        task, model = (key & 0xFFFFFFFF) >> 1, key & 1
        it, off, m = S.locate([task], pre, ioff0)
        out.append(f"# window {w['name']} best {float(f):.4f} item={fam.item_name(int(it[0]))} "
                   f"offset={fam.offset_name(int(off[0]))} mult={int(m[0])} model={model}")
    out.append("# hist " + " ".join(f"{b / 100:.2f}:{int(c)}" for b, c in enumerate(hist) if c))
    out.append("ioc\titem\toffset\tmult\tmodel\twindow\tn")
    f32 = hb.view(np.float32)
    for r in range(len(hb)):
        wi = int(hw[r]) >> 8
        out.append(f"{float(f32[r]):.4f}\t{fam.item_name(int(items[r]))}\t{fam.offset_name(int(offs[r]))}\t{int(mults[r])}\t"
                   f"{int(hw[r]) & 0xFF}\t{S.wins[wi]['name']}\t{S.wn[wi]}")
    Path(args[2]).write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print(f"kscreen: {total_runs} decodes ({aborted} aborted early) in {secs:.0f} s; best IoC {best:.4f}; wrote {args[2]}",
          file=sys.stderr, flush=True)


# ------------------------------------------------------------------ trace

def mode_trace(args):
    o = opts(args[3:])
    S = Setup(args[0], args[1], o, dump=True)
    cp = S.cp
    offs = None
    if "offs" in o:
        a, b = o["offs"].split(":")
        offs = (int(a), int(b))
    ioff0, pre, n_off = S.plan(offs)
    total = n_off * len(S.mults)
    bufs = S.new_bufs()
    step = max(1, (1 << 21) // S.dpt)
    lines, nfb = [], 0
    for t0 in range(0, total, step):
        n = min(step, total - t0)
        dump = cp.zeros(n * S.dpt * 2, cp.uint32)
        nfb += S.launch(n, t0, pre, ioff0, 1e30, bufs, dump)
        cp.cuda.Stream.null.synchronize()
        d = dump.get().reshape(n, len(S.models), len(S.wins), 2)
        items, offs_, mults = S.locate(np.arange(t0, t0 + n), pre, ioff0)
        for g in range(n):
            for mi, model in enumerate(S.models):
                for wi in range(len(S.wins)):
                    lines.append(f"{items[g]} {offs_[g]} {mults[g]} {model} {wi} {d[g, mi, wi, 0]} {d[g, mi, wi, 1]}")
    Path(args[2]).write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8", newline="\n")
    return nfb


# ------------------------------------------------------------------ probe / selfcheck

SELFCHECKS = [("data/segments.txt", "file:data/library.ksb", "items=40:44 offs=0:150 mults=1,28"),
              ("data/chain/segments_a5.txt", "file:data/library.ksb", "items=30:33 offs=0:100 mults=1,28"),    # P lines (chain windows)
              ("data/chain/segments_a5_rev.txt", "file:data/library.ksb", "items=30:33 offs=0:100 mults=1,28 dir=back"),  # reversed + backward key
              ("data/heads.txt", "lin:2", "items=0:3 offs=0:120 mults=1"),
              ("data/pages.txt", "poly:2", "items=0:4 mults=1 models=1"),
              ("data/segments.txt", "rand:3:7", "offs=0:100 mults=3,28")]


def mode_selfcheck():
    """Decode-by-decode comparison with the CPU engine on small ranges of every family kind."""
    import subprocess
    import tempfile
    if not BIN.exists():
        print("selfcheck needs the CPU engine: cargo build --release in work/kscreen")
        return 1
    os.chdir(HERE)                                  # the SELFCHECKS paths are relative to work/kscreen
    import chain_windows
    if not os.path.exists("data/chain/segments_a5.txt"):
        chain_windows.make(5, "segments")
    if not os.path.exists("data/chain/segments_a5_rev.txt"):
        chain_windows.make(5, "segments", reverse=True)
    fallbacks = 0
    with tempfile.TemporaryDirectory() as d:
        for win, fam, extra in SELFCHECKS:
            ca, cb = os.path.join(d, "cpu.txt"), os.path.join(d, "gpu.txt")
            subprocess.run([str(BIN), "trace", win, fam, ca, *extra.split()], cwd=HERE, check=True)
            fallbacks += mode_trace([win, fam, cb, *extra.split()])
            a, b = Path(ca).read_text(), Path(cb).read_text()
            n = a.count("\n")
            if a != b or n == 0:
                bad = next((i for i, (x, y) in enumerate(zip(a.splitlines(), b.splitlines())) if x != y), None)
                print(f"MISMATCH on {fam} {extra}: {n} CPU decodes, first difference at line {bad}")
                return 1
            print(f"identical: {n} decodes of {fam} {extra}")
    if fallbacks == 0:
        print("MISMATCH: the generic fallback kernel was never exercised, so it is not covered by this check")
        return 1
    print(f"GPU selfcheck passed (the fallback kernel ran {fallbacks} of these decodes)")
    return 0


def main():
    a = sys.argv[1:]
    if not a:
        print(__doc__)
        return 2
    if a[0] == "probe":
        return gpu_common.probe()
    if a[0] == "selfcheck":
        return mode_selfcheck()
    if a[0] in ("screen", "trace") and len(a) >= 4:
        (mode_screen if a[0] == "screen" else mode_trace)(a[1:])
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
