<?php
// Reference vectors for PHP's legacy (pre-7.1) Mersenne Twister, reproduced by MT_RAND_PHP mode.
// Output per line: mode seed kind v0 v1 ... v1999
$seeds = [0, 1, 2, 7, 29, 1033, 3301, 123456789, 2147483647, 2147483648, 4294967295, 35563892];
foreach (["php" => MT_RAND_PHP, "mt" => MT_RAND_MT19937] as $name => $mode) {
    foreach ($seeds as $s) {
        mt_srand($s, $mode);
        $raw = [];
        for ($i = 0; $i < 2000; $i++) $raw[] = mt_rand();
        echo "$name $s raw " . implode(" ", $raw) . "\n";
        mt_srand($s, $mode);
        $rng = [];
        for ($i = 0; $i < 2000; $i++) $rng[] = mt_rand(0, 28);
        echo "$name $s range " . implode(" ", $rng) . "\n";
    }
}
