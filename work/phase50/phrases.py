"""Phase 50 item (iii): solved-page phrases and headings as Vigenere keywords (repeating keys) with the skip rule.

    python work/phase50/phrases.py run [--threads 12]

Keys: every clause (text between '.' / '&' marks) of the solved plaintext, its sliding 3-5 word phrases, whole solved
sections and the headings below; each as the plaintext runes themselves ("direct") and with digraph runes spelled letter
by letter ("spelled"). The ordinary screen then tries every phase of every key, both signs, skip and coin models on the
first 300 runes of the eight LP2 section windows (data/segments.txt): a keyword starting at the section start is one
phase, the offset sweep also covers a start elsewhere. The library already holds single words (>= 4 letters) and
two-word phrases of the solved text (kw:...); these are the longer ones.
"""
import argparse
import os
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reorder as R  # noqa: E402
import lp  # noqa: E402
import prime_check  # noqa: E402

KEEP = 2000
SINGLE = {l: i for i, l in enumerate(lp.LATIN) if len(l) == 1}
ALIAS = {"V": 1, "K": 5, "Z": 15, "Q": 5}
HEADINGS = ["WELCOME PILGRIM", "WELCOME", "A WARNING", "SOME WISDOM", "A KOAN", "LOSS OF DIVINITY", "THE LOSS OF DIVINITY",
            "AN INSTRUCTION", "AN END", "A PARABLE", "THE PARABLE", "THE INSTAR EMERGENCE", "INSTAR EMERGENCE", "LIBER PRIMUS",
            "THE PRIMES ARE SACRED", "THE TOTIENT FUNCTION IS SACRED", "DIVINITY", "CIRCUMFERENCE", "INSTAR", "FIRFUMFERENFE",
            "A KOAN WILL SERVE", "THE CIRCUMFERENCE", "DIVINITY CIRCUMFERENCE", "CIRCUMFERENCE DIVINITY", "DIVINITY INSTAR",
            "PILGRIM", "THE PILGRIM", "THE GREAT JOURNEY", "TRUTH", "THE TRUTH", "ENLIGHTENMENT", "CONSUMPTION", "PRESERVATION"]


def spelled(runes):
    return [SINGLE.get(ch, ALIAS.get(ch)) for r in runes for ch in lp.LATIN[r]]


def build():
    segs = lp.load_segments()
    out = {}

    def add(kind, text, runes):
        for form, key in (("direct", list(runes)), ("spelled", spelled(runes))):
            if len(key) >= 3 and tuple(key) not in seen:
                seen.add(tuple(key))
                out[f"{kind}:{form}:{text[:60]}"] = key

    seen = set()
    for h in HEADINGS:
        add("heading", h, lp.word_to_key(h.replace(" ", "")))
    allplain = []
    for i, (title, f) in lp.KNOWN.items():
        plain = f(lp.runes_of(segs[i]))
        allplain += plain
        add("section", f"0.{i} {title}", plain)
        spans = [(w, a, b) for w, a, b in lp.word_spans(segs[i], plain)]
        for a, b in prime_check.clause_spans(segs[i]):
            ws = [s for s in spans if s[1] >= a and s[2] <= b]
            add("clause", " ".join(w for w, _, _ in ws), plain[a:b])
            for n in (3, 4, 5):
                for k in range(len(ws) - n + 1):
                    add(f"ngram{n}", " ".join(w for w, _, _ in ws[k:k + n]), plain[ws[k][1]:ws[k + n - 1][2]])
    add("all", "all solved text", allplain)
    return out


def write_ksb(path, ks):
    with open(path, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", len(ks)))
        for name, key in ks.items():
            v = (key * (KEEP // len(key) + 2))[:len(key) + KEEP] if len(key) < 8000 else key
            nb = name.encode("utf-8")[:300]
            f.write(struct.pack("<H", len(nb)) + nb + struct.pack("<I", len(v)) + bytes(x % 29 for x in v))


def run(threads, control_only=False):
    ks = build()
    lib = os.path.join(R.TMP, "phrases.ksb")
    write_ksb(lib, ks)
    fam = "file:" + R.rel(lib)
    print(f"{len(ks)} keys; lengths {min(map(len, ks.values()))}..{max(map(len, ks.values()))}", flush=True)
    seg = "data/segments.txt"
    # control: English planted under one clause key and under a heading key, found by item at the true offset
    eng = [int(x) for l in open(os.path.join(R.WORK, "phpmt", "data", "english.txt")) if l.startswith("R ") for x in l[2:].split()]
    plain = os.path.join(R.TMP, "phr_ctl_plain.txt")
    R.write(plain, [(f"w{k}", eng[400 * k:400 * k + 400]) for k in range(3)])
    ctl, ok = [], True
    pick = [n for n in ks if n.startswith("heading:direct:WELCOME PILGRIM")][:1] + [n for n in ks if n.startswith("clause:direct")][5:6] + \
           [n for n in ks if n.startswith("ngram4:spelled")][3:4]
    for ci, item in enumerate(pick):
        for model in (0, 1):
            plant = os.path.join(R.TMP, f"phr_ctl_plant{ci}{model}.txt")
            tsv = os.path.join(R.OUT, f"phrases_control{ci}{model}.tsv")
            R.kscreen(["plant", R.rel(plain), fam, item, "321", "1", str(model), "0.18", str(20 + ci), "0", R.rel(plant)])
            R.kscreen(["screen", R.rel(plant), fam, R.rel(tsv), f"only={item}", f"models={model}", "mults=1", f"threads={threads}"])
            truth = re.findall(r"# truth (\S+) item=.*? offset=(\d+)", open(plant).read())
            b = R.best(tsv)
            for w, t in truth:
                ioc, bi, bo = b[w]
                P = len(ks[item])          # a repeating key: offsets equal modulo its period
                good = bi == item and abs((int(bo) - int(t) + P // 2) % P - P // 2) <= 10 and ioc >= 1.40
                ok &= good
                ctl.append(f"{'PASS' if good else 'FAIL'} plant {item[:40]!r} model {model} {w}: best {ioc:.3f} at {bo} (truth {t})")
    if control_only:
        print(f"control {'PASS' if ok else 'FAIL'}", *ctl, sep=chr(10))
        return
    nul = os.path.join(R.OUT, "phrases_null.tsv")
    res = os.path.join(R.OUT, "phrases_library.tsv")
    ndraw = max(50, (sum(len(v) for v in ks.values()) + KEEP * len(ks)) // 20000 + 1)
    if not os.path.exists(nul):
        R.kscreen(["screen", seg, f"rand:{ndraw}:5052", R.rel(nul), "mults=1,28", "models=0,1", f"threads={threads}"])
    if not os.path.exists(res):
        R.kscreen(["screen", seg, fam, R.rel(res), "mults=1,28", "models=0,1", f"threads={threads}"])
    bl, bn = R.best(res), R.best(nul)
    head = (f"phrases ({len(ks)} keys): control {'PASS' if ok else 'FAIL'} ({sum('PASS' in x for x in ctl)}/{len(ctl)}); library best "
            f"{max(v[0] for v in bl.values()):.4f}, null ({ndraw} random streams) best {max(v[0] for v in bn.values()):.4f}")
    v = subprocess.run([sys.executable, os.path.join(R.KS, "verify.py"), res, "--top", "10", "--controls", "20", "--out",
                        os.path.join(R.OUT, "phrases_library_verify.txt")], capture_output=True, text=True)
    out = "\n".join([head] + ctl + [v.stdout.strip().splitlines()[-1]])
    print(out, flush=True)
    with open(os.path.join(R.OUT, "summary_phrases.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(out + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--threads", type=int, default=12)
    ap.add_argument("--control-only", action="store_true")
    a = ap.parse_args()
    run(a.threads, a.control_only)
