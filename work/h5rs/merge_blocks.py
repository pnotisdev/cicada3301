"""Merge the per-block sweep TSVs of the h5rs flat-library campaign into one TSV.

The campaign runs in 5 offset blocks of 400 (launch_campaign_blocks.bat); each block writes
its own TSV (columns: stream<TAB>offset<TAB>L<TAB>model<TAB>window<TAB>IoC for cells with
IoC >= the hit threshold, rows sorted within the block by (stream, offset, L, model,
window)) plus a `best` section (best cell per (stream, window, model), off=-1 when a
stream had no decoded cells in that block).

This script concatenates the blocks and re-sorts:
  * data rows re-sorted into the engine's canonical order: chunks of `chunk` offsets
    (offset // chunk), inside a chunk by (stream, offset, L, model, window) with stream
    and window in the engine's order (from the blocks' best sections) - this reproduces a
    monolithic sweep's output exactly;
  * duplicate (stream, offset, L, model, window) keys across blocks are an ERROR;
  * the per-block `best` sections are re-merged per (stream, window, model): the max IoC
    across blocks (blocks whose best is off=-1 contribute nothing);
  * with `--expect <monolithic.tsv>` the merged file is compared against a monolithic
    sweep over the whole range: data rows (exact sequence) and best rows (exact sequence)
    must be identical.

Usage:  python work/h5rs/merge_blocks.py <merged.tsv> <block1.tsv> [<block2.tsv> ...]
                 [--expect <monolithic.tsv>]
Run from the repo root. Exit code 0 on success, 1 on any check failure.
"""
import os
import re
import sys


def parse_tsv(path):
    """Returns (off0, off1, chunk, rows, bests) for one block TSV."""
    off0 = off1 = chunk = None
    rows = []      # (stream, offset, L, model, window, ioc)
    bests = []     # (stream, off, L, model, window, ioc)
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if line.startswith("#"):
                m = re.search(r"offs (\d+)\.\.(\d+)", line)
                if m:
                    off0, off1 = int(m.group(1)), int(m.group(2))
                m = re.search(r"chunk=(\d+)", line)
                if m:
                    chunk = int(m.group(1))
                continue
            if not line:
                continue
            parts = line.split("\t")
            if parts[0] == "best":
                name, off, L, m, win, ioc = parts[1:]
                bests.append((name, int(off), int(L), int(m), win, float(ioc)))
            else:
                name, off, L, m, win, ioc = parts
                rows.append((name, int(off), int(L), int(m), win, float(ioc)))
    if off0 is None or off1 is None:
        raise SystemExit(f"ERROR: {path}: no 'offs X..Y' header line found")
    if chunk is None:
        chunk = 10
    return off0, off1, chunk, rows, bests


def main():
    args = sys.argv[1:]
    if "--expect" in args:
        i = args.index("--expect")
        expect = args[i + 1]
        args = args[:i] + args[i + 2:]
    else:
        expect = None
    if len(args) < 2:
        raise SystemExit(__doc__.splitlines()[-1])
    merged_path = args[0]
    block_paths = args[1:]

    blocks = [parse_tsv(p) for p in block_paths]
    blocks.sort(key=lambda b: b[0])

    # blocks must partition the range without overlap or gap, all with the same chunk size
    ranges = [(b[0], b[1]) for b in blocks]
    for (a0, a1), (b0, b1) in zip(ranges, ranges[1:]):
        if b0 != a1:
            print(f"ERROR: block ranges not contiguous: {a0}..{a1} then {b0}..{b1}")
            sys.exit(1)
    chunks = {b[2] for b in blocks}
    if len(chunks) != 1:
        print(f"ERROR: blocks disagree on chunk size: {sorted(chunks)}")
        sys.exit(1)
    chunk = blocks[0][2]
    print(f"blocks: {len(blocks)}, range {ranges[0][0]}..{ranges[-1][1]}, chunk {chunk}")

    # duplicate keys across blocks are an error (a cell decoded twice)
    seen = {}
    dup = 0
    for path, (_, _, _, rows, _) in zip(block_paths, blocks):
        for r in rows:
            key = r[:5]
            if key in seen:
                print(f"ERROR: duplicate cell {key} in {path} and {seen[key]}")
                dup += 1
            seen[key] = path
    if dup:
        sys.exit(1)

    # canonical stream / window order from the first block's best section (engine order)
    streams, windows = [], []
    for name, _, _, _, win, _ in blocks[0][4]:
        if name not in streams:
            streams.append(name)
        if win not in windows:
            windows.append(win)
    s_idx = {s: i for i, s in enumerate(streams)}
    w_idx = {w: i for i, w in enumerate(windows)}
    for _, _, _, rows, bests in blocks:
        for r in rows:
            if r[0] not in s_idx:
                s_idx[r[0]] = len(s_idx)
                streams.append(r[0])
            if r[4] not in w_idx:
                w_idx[r[4]] = len(w_idx)
                windows.append(r[4])
        for b in bests:
            if b[0] not in s_idx:
                s_idx[b[0]] = len(s_idx)
                streams.append(b[0])
            if b[4] not in w_idx:
                w_idx[b[4]] = len(w_idx)
                windows.append(b[4])

    all_rows = []
    for path, (_, _, _, rows, _) in zip(block_paths, blocks):
        all_rows.extend(rows)
        print(f"  {path}: {len(rows)} data rows")
    # the engine's canonical order: chunks of `chunk` offsets, inside a chunk sorted by
    # (stream, offset, L, model, window); re-sorting by (offset//chunk, stream, offset,
    # L, model, window) reproduces a monolithic sweep exactly
    all_rows.sort(key=lambda r: (r[1] // chunk, s_idx[r[0]], r[1], r[2], r[3], w_idx[r[4]]))

    # re-merge bests per (stream, window, model)
    best_map = {}
    models = []
    for _, _, _, _, bests in blocks:
        for name, off, L, m, win, ioc in bests:
            if m not in models:
                models.append(m)
            key = (name, win, m)
            if off == -1:
                continue
            if key not in best_map or ioc > best_map[key][5]:
                best_map[key] = (name, off, L, m, win, ioc)
    best_out = []
    for s in streams:
        for w in windows:
            for m in models:
                if (s, w, m) in best_map:
                    best_out.append(best_map[(s, w, m)])
                else:
                    best_out.append((s, -1, 0, m, w, 0.0))

    with open(merged_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"# merged by merge_blocks.py from {len(blocks)} blocks: "
                + ", ".join(os.path.basename(p) for p in block_paths) + "\n")
        f.write("# columns: stream offset L model window IoC; rows in engine chunk-major order\n")
        for r in all_rows:
            f.write(f"{r[0]}\t{r[1]}\t{r[2]}\t{r[3]}\t{r[4]}\t{r[5]:.6f}\n")
        f.write("# best per (stream, window, model); off=-1 means no cells decoded\n")
        for b in best_out:
            f.write(f"best\t{b[0]}\t{b[1]}\t{b[2]}\t{b[3]}\t{b[4]}\t{b[5]:.6f}\n")
    print(f"wrote {merged_path}: {len(all_rows)} data rows, {len(best_out)} best rows")

    if expect:
        e0, e1, _, erows, ebests = parse_tsv(expect)
        ok_rows = all_rows == erows
        ok_best = best_out == ebests
        print(f"--expect {expect} (offs {e0}..{e1}, {len(erows)} rows, {len(ebests)} bests): "
              f"data rows {'IDENTICAL' if ok_rows else 'DIFFER'}, "
              f"best rows {'IDENTICAL' if ok_best else 'DIFFER'}")
        if not ok_rows:
            for i, (a, b) in enumerate(zip(all_rows, erows)):
                if a != b:
                    print(f"  first row diff at {i}: merged {a} vs mono {b}")
                    break
            print(f"  merged {len(all_rows)} rows vs mono {len(erows)} rows")
            sys.exit(1)
        if not ok_best:
            sys.exit(1)
        print("MERGE CHECK: PASS (merged == monolithic)")


if __name__ == "__main__":
    main()
