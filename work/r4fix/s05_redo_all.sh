python -B work/r4fix/s05_power_map.py redo --variants base --ns 100,150,200,300 --workers 3
for v in nu030 nu055; do python -B work/r4fix/s05_power_map.py redo --variants $v --ns 100,150,200 --workers 3; done
for v in q070 q095; do python -B work/r4fix/s05_power_map.py redo --variants $v --ns 100,150 --workers 3; done
echo done > work/r4fix/s05_stage3.done
