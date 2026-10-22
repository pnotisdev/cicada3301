"""Phase 60 test T3: "The key is all around you": the solved LP1 plaintext (forwards, backwards, read twice round) as a table-invariant running key.
Stage 1 of the frozen book-key rule (work/book_key_screen.py: table-free beam, first 729 runes of the 8 LP2 sections of >= 729 runes, offsets step 8, thresholds frozen), unchanged.
The text is short (about 3.4 k letters), so only offsets up to len - 770 exist; 'cyc' doubles the text so that offsets run through the wrap.
    python -B work/phase60_t3_lp1key.py control | run [workers] | summary
"""
import os
import re
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import book_key_screen as BS  # noqa: E402
import lp  # noqa: E402
from book_key_decoder import encrypt_skip_ptr  # noqa: E402
from book_key_flatness import dist, flattest_table, to_runes  # noqa: E402

BS.OUT = os.path.join(os.path.dirname(HERE), "results", "book_key_screen", BS.machine())
TEXT = []
for line in open(os.path.join(HERE, "ref", "lp_translation.txt"), encoding="utf-8"):
    m = re.match(r"0\.\d+\.\d+\.\d+\s+(.*)", line)
    if m:
        TEXT.append(m.group(1))
RAW = " ".join(TEXT)
VARIANTS = {"lp1_text": RAW, "lp1_rev": RAW[::-1], "lp1_cyc": RAW + " " + RAW}
for book, raw in VARIANTS.items():
    BS.BOOKS[book] = (None, False)
    for spell in ("digraph", "letters"):
        BS._cache[(book, spell)] = to_runes(raw, letters=spell == "letters")


def control(books=("lp1_text", "lp1_rev"), spells=("digraph", "letters"), n=6, seed=6003):
    rng = np.random.default_rng(seed)
    em = open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read()
    P = to_runes(em)
    lines, ok = [], True
    for book in books:
        for spell in spells:
            K = BS.key_of(book, spell)
            _, pi = flattest_table(dist(P), dist(K), rng, restarts=3)
            table = np.argsort(pi)
            found, null_hits = 0, 0
            for r in range(n):
                o = int(rng.integers(100, len(K) - 3 * BS.WIN)) if len(K) > 3 * BS.WIN + 100 else int(rng.integers(0, max(1, len(K) - BS.WIN - 60)))
                po = int(rng.integers(0, len(P) - BS.WIN))
                c, _ = encrypt_skip_ptr(P[po:po + BS.WIN], table[np.resize(K[o:], 3 * BS.WIN)], rng)
                cu, _ = encrypt_skip_ptr(P[po:po + BS.WIN], rng.integers(0, lp.N, 3 * BS.WIN), rng)
                g = o - o % BS.SPREAD
                offs = np.arange(max(0, g - 4 * BS.SPREAD), min(len(K) - BS.WIN - 40, g + 5 * BS.SPREAD), BS.SPREAD)
                rows = BS.scan([("plant", c), ("uniform", cu)], K, offs, BS.THR[spell])
                hit = any(abs(h - g) <= BS.SPREAD for h, _ in rows[0]["hits"])
                found += hit; null_hits += len(rows[1]["hits"])
            lines.append(f"{book} / {spell}: key {len(K)} runes; plants found {found}/{n}; uniform-key plants with a stage-1 hit {null_hits}")
            ok &= found >= 0.67 * n and null_hits == 0
    lines.append("T3 CONTROL " + ("PASS" if ok else "FAIL"))
    t = "\n".join(lines)
    print(t)
    open(os.path.join(os.path.dirname(HERE), "results", "analysis", "phase60_t3_control.txt"), "w", newline="\n").write(t + "\n")


def summary():
    out = [f"Phase 60 T3: the solved LP1 text as running key, stage 1 of the book-key rule (beam score per rune, first {BS.WIN} runes of 8 sections, step {BS.SPREAD}); thresholds frozen: "
           f"digraph {BS.THR['digraph']}, letters {BS.THR['letters']}. Nothing in LP2 is solved.", f"text: {len(RAW)} characters of the translation file", ""]
    for book in VARIANTS:
        for spell in ("digraph", "letters"):
            d = os.path.join(BS.OUT, book)
            files = sorted(f for f in os.listdir(d) if f.startswith(spell) and f.endswith(".tsv")) if os.path.isdir(d) else []
            n_all = len(BS.grid_of(BS.key_of(book, spell)))
            need = -(-n_all // BS.chunk_size(n_all))
            st, top, hits = {}, {}, []
            for f in files:
                for line in open(os.path.join(d, f), encoding="utf-8"):
                    p = line.rstrip("\n").split("\t")
                    if p[0] == "stats":
                        a = st.setdefault(p[1], [0, 0.0, 0.0]); a[0] += int(p[2]); a[1] += float(p[3]); a[2] += float(p[4])
                    elif p[0] == "top":
                        top.setdefault(p[1], []).append((float(p[3]), int(p[2])))
                    elif p[0] == "HIT":
                        hits.append((p[1], int(p[2]), float(p[3])))
            mu0, sd0 = BS.GATE_TAIL[spell]
            out.append(f"{book} / {spell}: {len(files)}/{need} chunks, {n_all} offsets; stage-1 hits {len(hits)}")
            for w in sorted(st):
                n, s1, s2 = st[w]; mu = s1 / n; sd = max(s2 / n - mu * mu, 0) ** 0.5; best = max(top[w])
                out.append(f"    {w}: mean {mu:+.4f} sd {sd:.4f}, best {best[0]:+.4f} at offset {best[1]} (gate z {(best[0] - mu0) / sd0:+.1f})")
            out += [f"    HIT {h[0]} offset {h[1]} score {h[2]:+.4f}" for h in sorted(hits, key=lambda x: -x[2])[:20]]
    t = "\n".join(out) + "\n"
    open(os.path.join(os.path.dirname(HERE), "results", "analysis", "phase60_t3_lp1key.txt"), "w", newline="\n", encoding="utf-8").write(t)
    print(t)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "control":
        control()
    elif cmd == "control12":
        control(("lp1_text",), ("digraph",), 12, 77)
    elif cmd == "run":
        for b in VARIANTS:
            BS.run(b, int(sys.argv[2]) if len(sys.argv) > 2 else 2)
    else:
        summary()
