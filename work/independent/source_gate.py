"""Cheap human-run preflight for a locally supplied Z5 (or other) text.

No downloads, no quoted book contents, no decryption, no third-party code imports.
Tests ONLY the unwhitened additive-running-key marginal prediction.
"""
import argparse
from collections import Counter
import math
import random
import re

from audit import convolution, population_ioc
from manual_common import execute, lp_module, reference_model, relative, repo_path, sha256


def frequencies(values):
    counts = Counter(values)
    return [counts[i] / len(values) for i in range(29)]


def preflight(run, args):
    path = repo_path(args.text)
    if path.stat().st_size > 20_000_000:
        raise ValueError("Use a plain UTF-8 text of at most 20 MB, not a PDF/binary")
    text = path.read_text(encoding="utf-8")
    if "\x00" in text:
        raise ValueError("NUL bytes: not an ordinary UTF-8 text")
    words = re.findall(r"[A-Za-z]+", text)
    if sum(map(len, words)) < 1000:
        raise ValueError("Too little text for a book-source preflight")
    lp = lp_module()
    logs, corpus = reference_model()
    p = [math.exp(x) for x in logs[29]]
    uniform = [1 / 29] * 29
    constant = [1.0] + [0.0] * 28
    assert abs(population_ioc(convolution(p, uniform)) - 1) < 1e-12
    assert abs(population_ioc(convolution(p, constant)) - population_ioc(p)) < 1e-12
    # A lowercase/uppercase choice is not used to create extra key families here.
    single = {latin: i for i, (_, latin, _) in enumerate(lp.GP) if len(latin) == 1}
    aliases = {"V": "U", "K": "C", "Q": "C", "Z": "S"}
    letter_stream = [single[aliases.get(ch, ch)] for w in words for ch in w.upper()]
    greedy_stream = [r for w in words for r in lp.word_to_key(w.upper().replace("IO", "IA"))]
    rows = []
    for name, stream in (("single-letter", letter_stream), ("greedy-GP-digraphs", greedy_stream)):
        k = frequencies(stream)
        for sign in (1, -1):
            dist = convolution(p, k, sign)
            prediction = population_ioc(dist)
            rng = random.Random(3301)
            shuffled = stream.copy()
            rng.shuffle(shuffled)
            assert frequencies(shuffled) == k
            assert population_ioc(convolution(p, frequencies(shuffled), sign)) == prediction
            # Positive simulation of the stated INDEPENDENT-marginals model, not
            # an anti-repeat simulator and not a decryptor.
            ps = rng.choices(range(29), weights=p, k=20000)
            ks = rng.choices(range(29), weights=k, k=20000)
            synthetic = [(a + sign * b) % 29 for a, b in zip(ps, ks)]
            null_keys = [rng.randrange(29) for _ in ps]
            null_cipher = [(a + sign * b) % 29 for a, b in zip(ps, null_keys)]
            row = dict(convention=name, key_sign=sign, source_runes=len(stream),
                       source_ioc=lp.ioc(stream), independent_population_prediction=prediction,
                       simulated_ioc=lp.ioc(synthetic), uniform_key_null_ioc=lp.ioc(null_cipher),
                       shuffled_source_prediction=prediction)
            rows.append(row)
            run.log(row)
            run.check()
    run.save("source_preflight.json", dict(source=relative(path), source_sha256=sha256(path),
                                          ascii_words=len(words), corpus=corpus, rows=rows,
                                          provenance_verified=False, lp2_searched=False,
                                          limitations="Independence and unwhitened addition only. No skip correction, book-code, hash, tableau, or source authenticity inference."))
    run.log("LP2's reported IoC is approximately 1.000. Compare predictions as a triage aid, NOT a formal exclusion.")
    run.log("An English book as a plain additive running key is already a low-priority family in this repository.")
    run.log("Hashing, indexing, a book code, or a non-additive construction is NOT tested here.")
    run.log("Provenance, publication date, edition and any primary Cicada link still need human verification.")
    run.log("Do not commit the source text. No book text has been copied into these outputs.")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", required=True, help="repository-relative local UTF-8 text, preferably in sources/")
    args = ap.parse_args()
    raise SystemExit(execute("source-preflight", lambda run: preflight(run, args)))
