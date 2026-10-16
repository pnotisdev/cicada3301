#!/usr/bin/env bash
# Key-free search for an outer alphabet D behind a per-word additive key (work/walk/src/dsearch.rs),
# on LP2 and on structure-free surrogates with LP2's exact word lengths and anti-repeat rule.
# A real signal = LP2's best G clearly above every surrogate's best G under identical settings.
set -euo pipefail
cd "$(dirname "$0")/.."
BIN=work/walk/target/release/walk
THREADS=${THREADS:-$(nproc)}
ITERS=${ITERS:-1000000}
RESTARTS=${RESTARTS:-$((THREADS * 8))}
NSUR=${NSUR:-5}
OUT=results/walk
mkdir -p "$OUT" work/walk/data/sur
for s in $(seq 1 "$NSUR"); do
  $BIN surrogate work/walk/data/lp2.txt "work/walk/data/sur/sur$s.txt" "$s" 0.18 > /dev/null
done
for m in ${MS:-1 2 3 4 5 6 7 8}; do
  for gaps in ${GAPSETS:-1 1,2}; do
    {
      echo "### m=$m gaps=$gaps"
      $BIN dsearch work/walk/data/lp2.txt "$m" "$gaps" "$ITERS" "$RESTARTS" "$THREADS" | head -1 | sed 's/^/LP2: /'
      for s in $(seq 1 "$NSUR"); do
        $BIN dsearch "work/walk/data/sur/sur$s.txt" "$m" "$gaps" "$ITERS" "$RESTARTS" "$THREADS" | head -1 \
          | sed "s/^/surrogate $s: /"
      done
    } | tee -a "$OUT/dsearch.txt"
  done
done
