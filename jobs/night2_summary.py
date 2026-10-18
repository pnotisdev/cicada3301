"""Summary of the H5 flat-library campaign after the overnight queue (jobs/queues/night2.txt). Read-only on the sweep outputs.

    python jobs/night2_summary.py [--blocks b1.tsv b2.tsv ...] [--null null.tsv] [--out summary.txt]

Applies the candidate rule of work/h5rs/CAMPAIGN.md with the CAMPAIGN-SIZE null: a real cell is a CANDIDATE (UNVERIFIED) iff its periodic IoC >= max(1.6, null max + 0.15),
the null max being the largest IoC of the 581-stream null for the same (window, model). Nothing in LP2 is solved: a candidate still needs the whole-window re-decode
(work/h5slice) and the whole-section verification of docs/CAMPAIGNS.md. Real and null have the same size, so counts of cells above 1.5 are directly comparable.
"""
import argparse
import collections
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")


def parse(path):
    """-> (rows, bests); rows = (stream, offset, L, model, window, ioc), bests the same from the `best` section"""
    rows, bests = [], []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line or line.startswith("#"):
                continue
            p = line.split("\t")
            if p[0] == "best":
                n, off, L, m, w, ioc = p[1:]
                bests.append((n, int(off), int(L), int(m), w, float(ioc)))
            else:
                n, off, L, m, w, ioc = p
                rows.append((n, int(off), int(L), int(m), w, float(ioc)))
    return rows, bests


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--blocks", nargs="*", default=[os.path.join(RES, f"h5rs_flat_block{i}.tsv") for i in range(1, 6)])
    ap.add_argument("--null", default=os.path.join(RES, "h5rs_flat_null581.tsv"))
    ap.add_argument("--out", default=os.path.join(RES, "h5rs_flat_summary.txt"))
    a = ap.parse_args()
    out = ["H5 flat-library campaign summary (UNVERIFIED; nothing in LP2 is solved)", ""]
    have = [b for b in a.blocks if os.path.exists(b)]
    out.append(f"real blocks present: {len(have)} of {len(a.blocks)}" + ("" if len(have) == len(a.blocks) else "  (INCOMPLETE: " + ", ".join(os.path.basename(b) for b in a.blocks if b not in have) + " missing)"))
    if not have:
        open(a.out, "w", encoding="utf-8", newline="\n").write("\n".join(out + ["no real block found"]) + "\n")
        print("\n".join(out))
        return 1
    real, rbest = [], []
    for b in have:
        r, bs = parse(b)
        real += r
        rbest += bs
    null, nbest = ([], [])
    if os.path.exists(a.null):
        null, nbest = parse(a.null)
    else:
        out.append("null file missing: " + os.path.basename(a.null) + " (no candidate rule can be applied)")
    nullmax = collections.defaultdict(float)
    for n, off, L, m, w, ioc in nbest:
        if off >= 0:
            nullmax[(w, m)] = max(nullmax[(w, m)], ioc)
    realbest = collections.defaultdict(float)
    for n, off, L, m, w, ioc in rbest:
        if off >= 0:
            realbest[(w, m)] = max(realbest[(w, m)], ioc)
    out += ["", f"cells >= 1.5: real {len(real)}, null {len(null)}   cells >= 1.6: real {sum(r[5] >= 1.6 for r in real)}, null {sum(r[5] >= 1.6 for r in null)}", "",
            "per (window, model): real best | 581-stream null max | candidate floor = max(1.6, null max + 0.15)"]
    floors = {}
    for key in sorted(set(realbest) | set(nullmax)):
        fl = max(1.6, nullmax[key] + 0.15) if key in nullmax else None
        floors[key] = fl
        out.append(f"  {key[0]:8s} model {key[1]}: {realbest.get(key, float('nan')):.4f} | {nullmax.get(key, float('nan')):.4f} | {('%.4f' % fl) if fl else 'n/a'}")
    cands = sorted((r for r in real if floors.get((r[4], r[3])) and r[5] >= floors[(r[4], r[3])]), key=lambda r: -r[5])
    out += ["", f"CANDIDATES (UNVERIFIED) at or above their floor: {len(cands)}"]
    for n, off, L, m, w, ioc in cands[:40]:
        out.append(f"  IoC {ioc:.4f}  stream {n!r}  offset {off}  L {L}  model {m}  window {w}")
    out += ["", "top 15 real cells overall"]
    for n, off, L, m, w, ioc in sorted(real, key=lambda r: -r[5])[:15]:
        out.append(f"  IoC {ioc:.4f}  stream {n!r}  offset {off}  L {L}  model {m}  window {w}")
    text = "\n".join(out) + "\n"
    with open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
