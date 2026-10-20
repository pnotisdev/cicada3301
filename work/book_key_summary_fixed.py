"""Phase 23: sentinel-safe re-reader of the booknight chunks (does not touch the queue's files or book_key_screen.py's summary).

A beam that runs out of key returns -1e18 (-1.37e15 per rune); it lands in the chunk's `stats` sums and wrecks the per-window mean, sd and own z (see work/log/phase23_review.md).
The chunk files hold only sums, so the sentinel cannot be subtracted: a (chunk, window) stats row whose mean is below -1 is DROPPED from the mean/sd (its `top` and `HIT` lines are
kept: they come from individual scores and are not affected) and the number of dropped offsets is reported. The proper repair is to rerun the final chunk of each book with a
patched scan() once the queue is finished.

    python work/book_key_summary_fixed.py [machine]       # -> results/analysis/book_key_screen_<machine>_fixed.txt
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import book_key_screen as S  # noqa: E402


def main(machine=None):
    machine = machine or S.machine()
    root = os.path.join(S.ROOT, "results", "book_key_screen", machine)
    out = [f"Phase 23 LP2 screen, stage 1, sentinel-safe re-read; machine {machine}. Nothing in LP2 is solved; a stage-1 hit is unverified.",
           f"Thresholds (frozen): digraph {S.THR['digraph']}, letters {S.THR['letters']}. Stats rows with a mean below -1 (sentinel) are dropped from mean/sd and counted.", ""]
    for book in S.BOOKS:
        for spell in ("digraph", "letters"):
            d = os.path.join(root, book)
            files = sorted(f for f in os.listdir(d) if f.startswith(spell) and f.endswith(".tsv")) if os.path.isdir(d) else []
            n_all = len(S.grid_of(S.key_of(book, spell)))
            need = -(-n_all // S.chunk_size(n_all))
            st, dropped, top, hits = {}, {}, {}, []
            for f in files:
                for line in open(os.path.join(d, f), encoding="utf-8"):
                    p = line.rstrip("\n").split("\t")
                    if p[0] == "stats":
                        n, s1, s2 = int(p[2]), float(p[3]), float(p[4])
                        if s1 / n < -1:
                            dropped[p[1]] = dropped.get(p[1], 0) + n
                            continue
                        a = st.setdefault(p[1], [0, 0.0, 0.0])
                        a[0] += n; a[1] += s1; a[2] += s2
                    elif p[0] == "top":
                        top.setdefault(p[1], []).append((float(p[3]), int(p[2])))
                    elif p[0] == "HIT":
                        hits.append((p[1], int(p[2]), float(p[3])))
            mu0, sd0 = S.GATE_TAIL[spell]
            out.append(f"{book} / {spell}: {len(files)}/{need} chunks done; stage-1 hits {len(hits)}")
            for w in sorted(top):
                best = max(top[w])
                if w in st:
                    n, s1, s2 = st[w]
                    mu = s1 / n
                    sd = max(s2 / n - mu * mu, 0) ** 0.5
                    own = f"own z {(best[0] - mu) / sd:+.1f} (mean {mu:+.4f} sd {sd:.4f}, {n} offsets, {dropped.get(w, 0)} dropped)"
                else:
                    own = "own z n/a (no clean stats row)"
                out.append(f"    {w}: best {best[0]:+.4f} at offset {best[1]} (gate z {(best[0] - mu0) / sd0:+.1f}); {own}")
            for h in sorted(hits, key=lambda x: -x[2])[:50]:
                out.append(f"    HIT {h[0]} offset {h[1]} score {h[2]:+.4f}  -> python work/book_key_verify.py hit {book} {spell} {h[1]} {h[0]}")
    text = "\n".join(out) + "\n"
    path = os.path.join(S.ROOT, "results", "analysis", f"book_key_screen_{machine}_fixed.txt")
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
