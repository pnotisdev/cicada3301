"""Planted controls for the outer-alphabet relabelling front-end (work/kscreen/relabel_export.py).

Model under test (STATUS left-item 1 / docs/NEGATIVE_SPACE.md section 0 item 5):

    c_i = sigma(p_i + k_i)  mod 29     (no anti-repeat events are planted: the skip/coin
                                       machinery is covered by the engine's own selftest;
                                       this control isolates the relabelling transformation)

Python cells (a)-(d) decode with the KNOWN key, k_i = i mod 29 (uniform period-29 keystream);
p = the solved section 0.1 (Welcome), first 300 runes; sigma = the keyword-mixed outer alphabet
for DIVINITY (and, as a second plant, Atbash).

Cells (the numbers in work/tmp/relabel_control.txt):
  (a) UNrelabelled ciphertext decoded with the true key: p' = c - k is noise (sigma then a
      per-position shift), IoC ~ 1.0  -> every previous screen was blind to this family;
  (b) sigma_inv-relabelled ciphertext decoded with the true key: p' == p exactly, IoC >= 1.5
      on 300 runes (the rule in docs/CAMPAIGNS.md is IoC >= 1.40; planted keys score 1.6-2.1);
  (c) null: i.i.d. uniform plaintext through the same sigma and key, relabelled decode ~ 1.0;
  (d) wrong sigma: relabelled with a different permutation, decode ~ 1.0.

The engine pass replants the DIVINITY model with an i.i.d. uniform splitmix64 key (600 values)
and replays the four windows through the real Rust engine on a one-stream family containing the
key. A period-29 ramp k_i = i mod 29 would NOT do for the offset search: every offset of a
period-29 ramp is the same key up to a constant shift, which the screen's D/b invariance
absorbs, so all 218 offsets would decode to the same shifted plaintext (verified: 1.6721 at
every offset). A uniform key has exactly one true offset (0).

Transcript -> work/tmp/relabel_control.txt
"""
import os
import struct
import subprocess
import sys

import numpy as np

sys.stdout.reconfigure(encoding="utf-8")

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
KS = os.path.join(ROOT, "work", "kscreen")
sys.path.insert(0, KS)
sys.path.insert(0, os.path.join(ROOT, "work"))

import lp  # noqa: E402
import relabel_export as rx  # noqa: E402

BIN = os.path.join(KS, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
TMP = os.path.join(ROOT, "work", "tmp")
OUT = os.path.join(TMP, "relabel_control.txt")
N = lp.N
WINDOW = 300
RNG = np.random.default_rng(20261017)
LINES = []


def log(s=""):
    print(s)
    LINES.append(s)


def splitmix_stream(n, seed=3301):
    """Deterministic i.i.d. uniform key values 0..28 (same generator family as the engine's controls)."""
    x = seed & 0xFFFFFFFFFFFFFFFF
    out = []
    for _ in range(n):
        x = (x + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = x
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        out.append(((z ^ (z >> 31)) >> 32) % N)
    return out


def write_ksb(path, streams):
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(streams)))
        for name, v in streams:
            nb = name.encode("utf-8")
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(v))


def write_window(path, runes, lens):
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        f.write(f"W win -1\nR {' '.join(map(str, runes))}\nL {' '.join(map(str, lens))}\n")


def engine_screen(winfile, ksb, tsv):
    cmd = [BIN, "screen", winfile, "file:" + ksb, tsv,
           "n=300", "beam=16", "mults=1", "models=0,1", "threads=4", "top=100", "abort=0"]
    r = subprocess.run(cmd, cwd=KS, capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"kscreen failed: {r.stderr}")
    best = None
    top_row = None
    with open(tsv, encoding="utf-8") as f:
        for line in f.read().splitlines():
            if line.startswith("# window ") and " best " in line:
                best = line.split("best ")[1].split(" ")[0]
            elif top_row is None and line and line[0].isdigit():
                top_row = line
    return best, top_row


def main():
    segs = lp.load_segments()
    p = lp.KNOWN[1][1](lp.runes_of(segs[1]))
    p300 = p[:WINDOW]
    p_ioc = lp.ioc(p300)
    assert p_ioc >= 1.5, f"plaintext control failed to be English-like: {p_ioc}"
    spans = lp.word_spans(segs[1], p)
    lens = [b - a for _, a, b in spans]

    log("=" * 78)
    log("relabel_control: outer-alphabet front-end (work/kscreen/relabel_export.py)")
    log("model planted: c_i = sigma(p_i + k_i) mod 29, k_i = i mod 29, no anti-repeat events")
    log(f"plaintext: solved section 0.1 (Welcome), first {WINDOW} runes, IoC {p_ioc:.4f} (rule: >= 1.40)")
    log(f"null plaintext: np.random.default_rng(20261017), {WINDOW} i.i.d. uniform runes, 5 replicates")
    log("wrong sigmas: the other family's sigma + 4 random shuffles, 5 decodes")
    log("=" * 78)

    k = [i % N for i in range(WINDOW)]
    plants = [("atbash", rx.sigma_atbash()), ("kw:DIVINITY", rx.keyword_sigma("DIVINITY"))]
    wrong_pool = {
        "atbash": [rx.keyword_sigma("DIVINITY")],
        "kw:DIVINITY": [rx.sigma_atbash()],
    }

    for name, sigma in plants:
        log(f"\n--- sigma = {name}")
        log("mixed alphabet (sigma[x] = rune at tableau position x): " +
            " ".join(lp.LATIN[v] for v in sigma))
        inv = rx.sigma_inverse(sigma)
        c = [sigma[(p300[i] + k[i]) % N] for i in range(WINDOW)]
        # (a) unrelabelled
        dec_unrel = [(c[i] - k[i]) % N for i in range(WINDOW)]
        log(f"(a) unrelabelled  : IoC of c - k               = {lp.ioc(dec_unrel):.4f}   (noise expected, ~1.0)")
        # (b) relabelled through the front-end
        rel = rx.relabel_window(c, sigma)
        dec_rel = [(rel[i] - k[i]) % N for i in range(WINDOW)]
        assert dec_rel == p300, "front-end must decode to the exact plaintext"
        log(f"(b) relabelled    : IoC of sigma_inv(c) - k     = {lp.ioc(dec_rel):.4f}   (== plaintext IoC, >= 1.5)")
        # (c) null: uniform plaintext through the same sigma and key
        nulls = []
        for _ in range(5):
            r = RNG.integers(0, N, WINDOW)
            cn = [sigma[(int(r[i]) + k[i]) % N] for i in range(WINDOW)]
            dn = rx.relabel_window(cn, sigma)
            nulls.append(lp.ioc([(dn[i] - k[i]) % N for i in range(WINDOW)]))
        log(f"(c) null           : IoC over 5 replicates       = "
            f"{' '.join(f'{x:.3f}' for x in nulls)}  mean {np.mean(nulls):.3f} max {max(nulls):.3f}")
        # (d) wrong sigma
        wrongs = wrong_pool[name] + [list(RNG.permutation(N)) for _ in range(4)]
        vals = []
        for w in wrongs:
            dw = rx.relabel_window(c, w)
            vals.append(lp.ioc([(dw[i] - k[i]) % N for i in range(WINDOW)]))
        log(f"(d) wrong sigma    : IoC over 5 wrong sigmas     = "
            f"{' '.join(f'{x:.3f}' for x in vals)}  mean {np.mean(vals):.3f} max {max(vals):.3f}")

    # ---------------------------------------------------------------- engine pass
    sigma = rx.keyword_sigma("DIVINITY")
    inv = rx.sigma_inverse(sigma)
    k_eng = splitmix_stream(600, seed=3301)
    c = [sigma[(p300[i] + k_eng[i]) % N] for i in range(WINDOW)]
    r_null = RNG.integers(0, N, WINDOW)
    c_null = [sigma[(int(r_null[i]) + k_eng[i]) % N] for i in range(WINDOW)]
    ksb = os.path.join(TMP, "relabel_plant.ksb")
    write_ksb(ksb, [("relabel-plant", k_eng)])

    cases = [
        ("unrel", c, None),
        ("rel", c, sigma),
        ("null", c_null, sigma),
        ("wrong", c, rx.sigma_atbash()),
    ]
    log("\n" + "=" * 78)
    log("end-to-end: real Rust engine, family = the planted key (600 uniform splitmix64 values)")
    log("218 offsets x 2 models x 1 window per run; the true key sits at offset 0 only")
    log("=" * 78)
    for tag, runes, sig in cases:
        win = os.path.join(TMP, f"relabel_w_{tag}.txt")
        write_window(win, rx.relabel_window(runes, sig) if sig is not None else runes, lens)
        tsv = os.path.join(TMP, f"relabel_screen_{tag}.tsv")
        best, top = engine_screen(win, ksb, tsv)
        log(f"[{tag:>6}] window best IoC {best}   top hit: {top}")
    log(f"\nwindow files: work/tmp/relabel_w_{{unrel,rel,null,wrong}}.txt; key family: work/tmp/relabel_plant.ksb")

    # ---------------------------------------------------------------- batch CLI
    log("\n" + "=" * 78)
    log("batch relabelling of the real LP2 windows (front-end for a real run)")
    log("=" * 78)
    for spec in ("atbash", "kw:DIVINITY"):
        for dst in rx.batch(spec):
            log(f"  {os.path.relpath(dst, ROOT).replace(os.sep, '/')}")

    with open(OUT, "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(LINES) + "\n")
    log(f"\ntranscript -> work/tmp/relabel_control.txt")


if __name__ == "__main__":
    main()
