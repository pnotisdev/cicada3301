#!/usr/bin/env bash
# Seeded-PRNG pads (PHP<7.1 mt_rand, glibc random()/PHP5 rand() on Linux, .NET System.Random) over every
# seed, all 16 cipher variants, skip-aware decoder.  WINDOWS=07 tests a single whole-book pad starting
# on LP2 page 0; WINDOWS=all also tests a fresh seed per section (8 windows, ~8x the time).
# Throughput reference: ~0.9 M seeds/s for one window on 16 threads (2026 desktop).
set -euo pipefail
cd "$(dirname "$0")/.."
BIN=work/phpmt/target/release/phpmt
THREADS=${THREADS:-$(nproc)}
WINDOWS=${WINDOWS:-all}
GENS=${GENS:-"php glibc net"}
OUT=results/prng
mkdir -p "$OUT"
WIN=work/phpmt/data/windows.txt
[ "$WINDOWS" = "07" ] && WIN=work/phpmt/data/windows_07.txt
for gen in $GENS; do
  hi=4294967296
  [ "$gen" = "net" ] && hi=2147483648    # System.Random(int) uses |seed|
  echo "== $gen windows=$WINDOWS"
  $BIN sweep "$gen" "$WIN" work/phpmt/data/dict.txt 0 "$hi" "$OUT/${gen}_${WINDOWS}.tsv" "$THREADS" \
      2> "$OUT/${gen}_${WINDOWS}.log"
  tail -1 "$OUT/${gen}_${WINDOWS}.log"
done
python3 work/phpmt/verify_top.py "$OUT"/*_"$WINDOWS".tsv
