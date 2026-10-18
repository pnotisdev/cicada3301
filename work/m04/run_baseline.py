"""M04 baseline orchestrator: fit q, calibrate the null threshold, then the held-out run. Design: work/m04/README.md (frozen first).

    python work/m04/run_baseline.py fit | calibrate | heldout
"""
import hashlib
import json
import os
import random
import statistics
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import m04 as M  # noqa: E402

OUT = os.path.join(M.ROOT, "results", "analysis")
QFIT = os.path.join(OUT, "m04_q_fit.json")
CALIB = os.path.join(OUT, "m04_calibration.json")
STRATA = [(s, k) for s in ("cicada", "english") for k in ("iid", "lib")]
TRAIN_CICADA, HELD_CICADA = [4, 5, 0, 2, 6, 16, 17], [1, 3]
_POOLS = {}


def pool(split, src):
    key = (split, src)
    if key not in _POOLS:
        if src == "cicada":
            _POOLS[key] = M.cicada_pool(TRAIN_CICADA if split == "train" else HELD_CICADA)
        else:
            _POOLS[key] = M.english_pool(0.0, 0.4) if split == "train" else M.english_pool(0.6, 1.0)
    return _POOLS[key]


def seed_of(*parts):
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode()).digest()[:8], "big")


def window(split, src, rng):
    p = pool(split, src)
    s = rng.randrange(len(p) - M.N_RUNES + 1)
    return p[s:s + M.N_RUNES], s


def encrypt(channel, plain, key, off, q, rng):
    if channel == "m04":
        return M.enc_m04(plain, key, off, q, rng)
    if channel == "spend":
        return M.enc_spend(plain, key, off, q, rng)
    if channel == "skip":
        return M.enc_skip(plain, key, off, rng)
    return M.enc_coin(plain, key, off, rng)


# ------------------------------------------------------------------ fit q on training plants

def fit():
    res = {}
    for channel in ("m04", "spend"):
        for src, kind in STRATA:
            q = 1 - 29 * M.TARGET_DOUBLET
            for it in range(4):
                rng = random.Random(seed_of("fit", channel, src, kind, it))
                d = t = 0
                for _ in range(2000):
                    plain, _s = window("train", src, rng)
                    key = M.draw_stream(rng, kind)[1]
                    out = encrypt(channel, plain, key, rng.randrange(M.OFFSETS), q, rng)[0]
                    d += M.doublets(out)
                    t += len(out) - 1
                rate = d / t
                print(f"  {channel:5s} {src:8s} {kind}  iteration {it}: q={q:.4f}  doublet rate {rate:.5f}  (target {M.TARGET_DOUBLET:.5f}; {d} doublets)", flush=True)
                if it < 3:
                    q = min(1.0, max(0.0, 1 - (1 - q) * M.TARGET_DOUBLET / rate))
            res[f"{channel}|{src}|{kind}"] = dict(q=q, rate_at_q=rate, doublets=d, transitions=t)
    json.dump(dict(target=M.TARGET_DOUBLET, fits=res, note="q refined multiplicatively (rate ~ (1-q)); the last iteration's q is the frozen value"),
              open(QFIT, "w"), indent=1)
    print("wrote", os.path.relpath(QFIT, M.ROOT))


def qfit():
    return {k: v["q"] for k, v in json.load(open(QFIT))["fits"].items()}


# ------------------------------------------------------------------ one search

def one(scratch, tag, channel, src, kind, seed, split, q, with_key, verify_cells):
    """encrypt a plant, search its bank (with the key when with_key, else a bank of distractors only), return a record"""
    rng = random.Random(seed)
    plain, start = window(split, src, rng)
    drawn = [M.draw_stream(rng, kind) for _ in range(8)]
    true_i, off = rng.randrange(8), rng.randrange(M.OFFSETS)
    out, used, rep = encrypt(channel, plain, drawn[true_i][1], off, q, rng)
    bank_streams = drawn if with_key else [M.draw_stream(rng, kind) for _ in range(8)]
    names = [f"k{i}" for i in range(8)]
    bank, win, tsv = (os.path.join(scratch, f"{tag}.{x}") for x in ("ksb", "txt", "tsv"))
    M.write_ksb(bank, [(n, s[1]) for n, s in zip(names, bank_streams)])
    M.write_window(win, "w", out)
    best, rows = M.screen(win, bank, tsv)
    rec = dict(tag=tag, channel=channel, src=src, kind=kind, with_key=with_key, seed=seed, window_start=start, offset=off,
               true_stream=drawn[true_i][0], period=M.period_of(drawn[true_i][1]), doublets=M.doublets(out), repairs=sum(rep),
               best=best, listed=len(rows))
    top = max(rows) if rows else None
    rec["argmax"] = None if top is None else dict(stream=top[1], offset=top[2], mult=top[3], model=top[4], ioc=top[0])
    rec["identified"] = bool(with_key and top and top[1] == f"k{true_i}" and abs(top[2] - off) <= 3)
    if with_key:
        cell = [r for r in rows if r[1] == f"k{true_i}" and r[2] == off and r[3] == 1]
        rec["true_listed"] = bool(cell)
        rec["true_ioc"] = max((r[0] for r in cell), default=None)
        ranked = sorted(rows, reverse=True)
        rec["true_rank"] = next((i + 1 for i, r in enumerate(ranked) if r[1] == f"k{true_i}" and r[2] == off and r[3] == 1), None)
        if verify_cells:
            vs = []
            for model in (0, 1):
                ioc, plain_dec, ptr = M.verify(win, bank, f"k{true_i}", off, 1, model, "w")
                if plain_dec:
                    acc = sum(a == b for a, b in zip(plain_dec, plain)) / len(plain)
                    keep = [i for i in range(min(len(ptr), len(used))) if not rep[i]]
                    pacc = sum(ptr[i] == used[i] - off for i in keep) / max(1, len(keep))
                    vs.append(dict(model=model, ioc=ioc, plain_acc=acc, ptr_acc=pacc))
            rec["verify"] = max(vs, key=lambda v: v["ioc"]) if vs else None
    return rec


def run(scratch, jobs):
    recs = []
    t0 = time.time()
    for n, args in enumerate(jobs):
        recs.append(one(scratch, f"p{n}", *args))
        if (n + 1) % 50 == 0:
            print(f"  {n + 1}/{len(jobs)}  {time.time() - t0:.0f}s", flush=True)
    return recs


def calibrate():
    q = qfit()
    jobs = []
    for src, kind in STRATA:
        for i in range(50):
            jobs.append(("m04", src, kind, seed_of("cal", src, kind, i), "train", q[f"m04|{src}|{kind}"], False, False))
    with tempfile.TemporaryDirectory(dir=M.scratch_dir()) as scratch:
        recs = run(scratch, jobs)
    bests = sorted((r["best"] for r in recs), reverse=True)
    T = bests[9]
    json.dump(dict(threshold=T, rule="10th largest of 200 matched-null best IoCs (about 95%)", null_bests=bests, q=q,
                   by_stratum={f"{s}|{k}": sorted((r["best"] for r in recs if r["src"] == s and r["kind"] == k), reverse=True)[:5] for s, k in STRATA}),
              open(CALIB, "w"), indent=1)
    print(f"threshold T = {T:.4f}; null maxima: max {bests[0]:.4f}, median {statistics.median(bests):.4f}; wrote {os.path.relpath(CALIB, M.ROOT)}")


# ------------------------------------------------------------------ held-out

def heldout():
    if not (os.path.exists(QFIT) and os.path.exists(CALIB)):
        sys.exit("refusing: run `fit` and `calibrate` first (they freeze q and the threshold)")
    q = qfit()
    T = json.load(open(CALIB))["threshold"]
    jobs = []
    plan = (("m04", 25, True), ("spend", 25, True), ("skip", 10, True), ("coin", 10, True), ("m04", 25, False))
    for channel, per, with_key in plan:
        for src, kind in STRATA:
            for i in range(per):
                jobs.append((channel, src, kind, seed_of("held", channel, src, kind, with_key, i), "held", q.get(f"{channel}|{src}|{kind}", 0.0), with_key, with_key))
    with tempfile.TemporaryDirectory(dir=M.scratch_dir()) as scratch:
        recs = run(scratch, jobs)
    with open(os.path.join(OUT, "m04_records.jsonl"), "w") as f:
        for r in recs:
            f.write(json.dumps(r) + "\n")
    lines = [f"M04 baseline, held-out run. Threshold T = {T:.4f} (matched nulls, frozen). Nothing in LP2 is solved.", ""]
    summary = {}
    def block(name, rs):
        n = len(rs)
        det = sum(r["best"] >= T for r in rs)
        row = dict(n=n, detected=det, identified=sum(r["identified"] for r in rs), reaches_1_40=sum(r["best"] >= 1.40 for r in rs),
                   median_best=statistics.median(r["best"] for r in rs), true_cell_listed=sum(bool(r.get("true_listed")) for r in rs))
        vs = [r["verify"] for r in rs if r.get("verify")]
        if vs:
            row["plain_acc_mean"] = statistics.mean(v["plain_acc"] for v in vs)
            row["plain_acc_ge_95"] = sum(v["plain_acc"] >= 0.95 for v in vs)
            row["ptr_acc_mean"] = statistics.mean(v["ptr_acc"] for v in vs)
        summary[name] = row
        lines.append(f"{name:26s} n={n:3d} detected(best>=T)={det:3d} identified={row['identified']:3d} best>=1.40={row['reaches_1_40']:3d} "
                     f"median best={row['median_best']:.3f} true cell listed={row['true_cell_listed']:3d}"
                     + (f"  plaintext acc mean={row['plain_acc_mean']:.3f} (>=0.95: {row['plain_acc_ge_95']}) pointer acc mean={row['ptr_acc_mean']:.3f}" if vs else ""))
    for channel, per, with_key in plan:
        rs = [r for r in recs if r["channel"] == channel and r["with_key"] == with_key]
        block(channel if with_key else "matched nulls (M04 ciphertext)", rs)
        if with_key:
            for src, kind in STRATA:
                block(f"  {channel} {src} {kind}", [r for r in rs if r["src"] == src and r["kind"] == kind])
            per_period = [r for r in rs if r["period"]]
            if per_period:
                block(f"  {channel} period<=8 streams", per_period)
    lines += ["", f"distinct held-out window starts per source: " + ", ".join(
        f"{s}={len({r['window_start'] for r in recs if r['src'] == s})}" for s in ("cicada", "english"))]
    open(os.path.join(OUT, "m04_baseline.txt"), "w").write("\n".join(lines) + "\n")
    json.dump(dict(threshold=T, q=q, summary=summary), open(os.path.join(OUT, "m04_baseline.json"), "w"), indent=1)
    print("\n".join(lines))


if __name__ == "__main__":
    {"fit": fit, "calibrate": calibrate, "heldout": heldout}[sys.argv[1]]()
