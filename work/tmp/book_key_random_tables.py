"""Quantiles of the predicted LP2-length IoC excess (in null sd 0.00051) for a book key under RANDOM letter->rune tables."""
import glob, os, sys
import numpy as np
sys.path.insert(0, "work")
from book_key_flatness import HERE, dist, gutenberg_body, to_runes
rng = np.random.default_rng(1)
P = to_runes(open(os.path.join(HERE, "ref", "emerson_essays1.txt"), encoding="utf-8", errors="ignore").read())
Fp = np.abs(np.fft.fft(dist(P))) ** 2
SD, MU = 0.00051, 0.99986
print("book                quantiles of z over 20,000 random tables: 0.01%   0.1%    1%    50%")
for path in sorted(glob.glob(os.path.join(HERE, "ref", "corpora", "*.txt"))):
    K = dist(to_runes(gutenberg_body(path)))
    perms = np.argsort(rng.random((20000, 29)), axis=1)
    ioc = (Fp * np.abs(np.fft.fft(K[perms], axis=1)) ** 2).sum(1)
    z = (ioc - MU) / SD
    print(f"{os.path.basename(path):18s} " + " ".join(f"{q:7.1f}" for q in np.percentile(z, [0.01, 0.1, 1, 50])))
