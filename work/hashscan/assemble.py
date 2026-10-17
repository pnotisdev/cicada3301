"""Assemble src/main.rs from src/part_*.rs and the decoder copied verbatim from work/phpmt/src/main.rs
(data loading, dictionary, decode_fast, decode_full). Regenerate with:  python work/hashscan/assemble.py"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "..", "phpmt", "src", "main.rs"), encoding="utf-8").read().splitlines(keepends=True)
a = next(i for i, l in enumerate(src) if l.startswith("// ------------------------------------------------------------------ data"))
b = next(i for i, l in enumerate(src) if l.startswith("// ------------------------------------------------------------------ modes"))
shared = "".join(src[a:b])
shared = re.sub(r"#\[inline\]\nfn md\(x: i32\) -> i32 \{\n    \(\(x % MOD\) \+ MOD\) % MOD\n\}\n", "", shared)
assert "fn md(" not in shared and "fn decode_fast" in shared and "fn decode_full" in shared
parts = {p: open(os.path.join(HERE, "src", f"part_{p}.rs"), encoding="utf-8").read() for p in ("head", "hash", "modes")}
text = (parts["head"] + parts["hash"] + "\n// ---- decoder: verbatim copy from work/phpmt/src/main.rs (do not edit here) ----\n\n" + shared
        + parts["modes"])
with open(os.path.join(HERE, "src", "main.rs"), "w", newline="\n", encoding="utf-8") as f:
    f.write(text)
print("wrote src/main.rs,", len(text.splitlines()), "lines")
