# run from work/kscreen
K=target/release/kscreen.exe; R=../../results/kscreen
$K screen data/segments.txt file:data/signed.ksb $R/signed_mults_segments.tsv mults=all threads=2 > $R/signed_mults_segments.log 2>&1
$K screen data/segments.txt rand:37:1 $R/signed_mults_null_1.tsv mults=all threads=2 > $R/signed_mults_null_1.log 2>&1
$K screen data/segments.txt rand:37:2 $R/signed_mults_null_2.tsv mults=all threads=2 > $R/signed_mults_null_2.log 2>&1
