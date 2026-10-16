#!/usr/bin/env bash
# Waits for each window-0.7 sweep to finish, verifies its top candidates, copies results; then reruns the
# heading-restart screen (fixed word segmentation) once the CPU is free.
cd "$(dirname "$0")/../.."
D=work/phpmt/data
for pair in "php:sweep_07" "glibc:sweep_07_glibc" "net:sweep_07_net"; do
  gen=${pair%%:*}; base=${pair##*:}
  until [ -f "$D/$base.tsv" ]; do sleep 30; done
  sleep 5
  cp "$D/$base.tsv" "results/prng/${gen}_07.tsv"
  cp "$D/$base.log" "results/prng/${gen}_07.log"
  python work/phpmt/verify_top.py "results/prng/${gen}_07.tsv" --gen "$gen" --top 20 --controls 40 \
      > "results/prng/${gen}_07_verify.txt" 2>&1
  echo "$gen done: $(tail -1 results/prng/${gen}_07.log)"
done
cd work && python heading_screen.py > tmp/phase4_heading.log 2>&1
echo "heading screen done"
