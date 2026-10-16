# Results of long runs

| File | Produced by | Notes |
|---|---|---|
| `prng/php_07.tsv`, `.log` | `phpmt sweep php` on segment 0.7 | top 4,000 (seed, variant) candidates of all 2^32 PHP<7.1 mt_rand seeds |
| `prng/glibc_07.tsv`, `.log` | `phpmt sweep glibc` on segment 0.7 | glibc random() / PHP 5 rand() on Linux |
| `prng/net_07.tsv`, `.log` | `phpmt sweep net` on segment 0.7 | .NET System.Random, seeds 0..2^31 |
| `walk/dsearch.txt` | `jobs/walk_dsearch.sh` | key-free D-search on LP2 vs surrogates |

TSV columns: screening score (runes in dictionary words of length >= 3 within the first ~60 runes), seed,
window, model (0 skip / 1 coin), map (0 language range call / 1 raw % 29), sign, atbash.
A planted true key scores about 35-44; random seeds top out around 14-16 per million seeds.
