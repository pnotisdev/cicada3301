# F-frequency at word positions >= 6 in English prose (Gutenberg, committed data? no: git-ignored corpora on this PC).
# Compare with the lag-6 echo excess rate 0.0272 +/- 0.0047 (35.1/1290) observed in LP2.
import os, re, glob

corpus = []
for path in glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "ref", "corpora", "pg*.txt")):
    with open(path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    # strip Gutenberg header/footer roughly: take text between *** START and *** END if present
    m = re.search(r"\*\*\* ?START.*?\*\*\*(.*)\*\*\* ?END", text, re.S)
    if m:
        text = m.group(1)
    corpus.append(text)
text = " ".join(corpus)
words = re.findall(r"[A-Za-z']+", text)
words = [w.upper().replace("'", "") for w in words]
words = [w for w in words if 2 <= len(w) <= 40]

tot = tot6 = 0
f6 = 0
for w in words:
    tot += len(w)
    for j, ch in enumerate(w):
        if j >= 6:
            tot6 += 1
            if ch == "F":
                f6 += 1
f_all = sum(w.count("F") for w in words)
print(f"words={len(words)} letters={tot} positions>=6={tot6}")
print(f"F overall: {f_all/tot:.4f}")
print(f"F at positions>=6: {f6/tot6:.4f}  (n={tot6}, sd~{(f6/tot6*(1-f6/tot6)/tot6)**0.5:.4f})")
print(f"LP2 echo excess rate 0.0272 +/- 0.0047 for comparison")
