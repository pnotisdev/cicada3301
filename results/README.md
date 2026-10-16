# Results of long runs

| File | Produced by | Notes |
|---|---|---|
| `prng/php_07.tsv`, `.log` | `phpmt sweep php` on segment 0.7 | top 4,000 (seed, variant) candidates of all 2^32 PHP<7.1 mt_rand seeds |
| `prng/glibc_07.tsv`, `.log` | `phpmt sweep glibc` on segment 0.7 | glibc random() / PHP 5 rand() on Linux |
| `prng/net_07.tsv`, `.log` | `phpmt sweep net` on segment 0.7 | .NET System.Random, seeds 0..2^31 |
| `walk/dsearch.txt` | `jobs/walk_dsearch.sh` | key-free D-search on LP2 vs surrogates |
| `overnight/REPORT.md` | `jobs/overnight.py` | verdict per campaign; logs in `overnight/logs/` |
| `kscreen/*.tsv`, `*_verify.txt` | `work/kscreen` | IoC screen hits (top 2,000), per-window bests, IoC histogram; re-decoded top hits |
| `kscreen/selftest.txt` | `work/kscreen/selftest.py` | planted-key recovery and random-key null for the IoC screen |
| `analysis/drift_period.*` | `work/drift_period.py` | drift-aware periodic-key scan (Z per period) with power curve |
| `analysis/wordlen.txt` | `work/wordlen.py` | LP2 word-length histogram against English conventions |
| `screens/` | `attack.py`, `rev_screen.py`, `heading_screen.py` | dictionary screens rerun with the corrected segmentation |
| `payload/` | `grid60.py` | hash and passphrase-decryption tests on the corrected 256-byte payload |
| `prng/*_all.*` | `phpmt sweep` on all 8 sections | fresh seed per section |

TSV columns: screening score (runes in dictionary words of length >= 3 within the first ~60 runes), seed,
window, model (0 skip / 1 coin), map (0 language range call / 1 raw % 29), sign, atbash.
A planted true key scores about 35-44; random seeds top out around 14-16 per million seeds.

kscreen TSV columns: IoC of the decoded letters over the first n runes (English ≈ 1.8, random 1.0), keystream,
start offset (for `lin` families the start state), key multiplier (28 = minus), anti-repeat model (0 skip /
1 coin), window, runes used. Header lines starting with `#` give the run settings, each window's best hit and
a histogram of all decodes.
