"""Phase 50, row solved-phrase-keys: Cicada's demonstrated key habits as single-layer Vigenere keys (layer2 engine, no outer layer).

    python work/phase50/phrase_keys.py run [--threads 12]

Keys (<= 24 runes, layer2's MAXM): every word (>= 3 runes), clause, 2-3 word phrase, title and first / last printed line of the solved pages
0.0-0.6, 0.16, 0.17, and the words / lines of the 2014 signed messages (results/outguess payload_10..13). Spelling variants, all 8
combinations of: C written as F (FIRFUMFERENFE); NG as N,G instead of the ING rune; IA as I,O (IA/IO). U/V is already one letter in this
repo's alphabet (V -> U), so DIVINITY = DIUINITY needs no variant. Each key is screened with both inner signs and with the literal-F rule
off and on (a plaintext F stays F and does not advance the key, as on the solved pages), every phase, in the first 300 runes of the eight
section windows, mode=known (IoC of the decoded letters, any language). The outer layer is a stream of zeros (one offset).
Control: English planted with an LP1 phrase key (variant spellings, literal F on and off). Null: random keywords of the same lengths.
"""
import argparse
import glob
import os
import random
import re
import struct
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import reorder as R  # noqa: E402  (puts work/ and work/kscreen on sys.path)
import lp  # noqa: E402
import prime_check  # noqa: E402
import lang_checks  # noqa: E402

L2 = os.path.join(R.WORK, "layer2")
BIN = os.path.join(L2, "target", "release", "layer2" + (".exe" if os.name == "nt" else ""))
TD = os.path.join(R.KS, "data", "phase50")
SOLVED = [0, 1, 2, 3, 4, 5, 6, 16, 17]
MAXM = 24
IDX = {l: i for i, l in enumerate(lp.LATIN)}
SINGLE = {l: i for i, l in enumerate(lp.LATIN) if len(l) == 1}


def variants(runes):
    """runes -> the 8 spellings: C->F, ING->N,G, IA->I,O"""
    out = set()
    for mask in range(8):
        v = []
        for r in runes:
            if mask & 1 and r == IDX["C"]:
                v.append(IDX["F"])
            elif mask & 2 and r == IDX["ING"]:
                v += [IDX["I"] if False else SINGLE["N"], SINGLE["G"]]
            elif mask & 4 and r == IDX["IA"]:
                v += [SINGLE["I"], SINGLE["O"] if "O" in SINGLE else IDX["O"]]
            else:
                v.append(r)
        out.add(tuple(v))
    return out


def sources():
    segs = lp.load_segments()
    texts = []                                  # (kind, text, runes)
    for i in SOLVED:
        title, f = lp.KNOWN[i]
        plain = f(lp.runes_of(segs[i]))
        spans = lp.word_spans(segs[i], plain)
        texts.append(("title", title, lp.word_to_key(re.sub(r"[^A-Z]", "", title.upper()))))
        for w, a, b in spans:
            texts.append(("word", w, plain[a:b]))
        for a, b in prime_check.clause_spans(segs[i]):
            ws = [s for s in spans if s[1] >= a and s[2] <= b]
            texts.append(("clause", f"0.{i} {a}", plain[a:b]))
            for n in (2, 3):
                for k in range(len(ws) - n + 1):
                    texts.append(("phrase", " ".join(s[0] for s in ws[k:k + n]), plain[ws[k][1]:ws[k + n - 1][2]]))
        lines, cur, k = [], [], 0                # printed lines as rune ranges
        for t in segs[i]:
            if isinstance(t, int):
                cur.append(plain[k])
                k += 1
            elif t in ("\n", "%") and cur:
                lines.append(cur)
                cur = []
        if cur:
            lines.append(cur)
        texts.append(("firstline", f"0.{i}", lines[0]))
        texts.append(("lastline", f"0.{i}", lines[-1]))
    for f in sorted(glob.glob(os.path.join(R.ROOT, "results", "outguess", "payload_1[0-3].txt"))):
        body = open(f, encoding="utf-8", errors="replace").read().split("-----BEGIN PGP SIGNATURE-----")[0]
        body = body.split("Hash: SHA1")[-1]
        for line in body.splitlines():
            ws = re.findall(r"[A-Za-z]+", line)
            if len(ws) >= 1 and not re.search(r"\d", line):
                for w in ws:
                    texts.append(("signed-word", w.upper(), lp.word_to_key(w.upper())))
                texts.append(("signed-line", line.strip()[:40], lp.word_to_key("".join(ws).upper())))
    return texts


def keyset():
    keys = {}
    for kind, text, runes in sources():
        for v in variants(runes):
            if 3 <= len(v) <= MAXM and v not in keys:
                keys[v] = f"{kind}:{text[:30].replace(' ', '_')}"
    return keys


def write_kw(path, items):
    with open(path, "w", newline="\n") as f:
        for n, (name, v) in enumerate(items):
            f.write(f"k{n}_{name} {' '.join(map(str, v))}\n")


def l2(args):
    r = subprocess.run([BIN] + args, cwd=L2, capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError(r.stderr[-400:])
    return r.stdout


def l2rel(p):
    return os.path.relpath(p, L2).replace("\\", "/")


def best(tsv):
    return {m.group(1): (float(m.group(2)), m.group(3)) for m in re.finditer(r"# window (\S+) best ([\d.]+) item=\S.*? offset=\d+ mult=\d+ model=\d+ (.*)", open(tsv, encoding="utf-8").read())}


def run(threads):
    os.makedirs(TD, exist_ok=True)
    os.makedirs(R.OUT, exist_ok=True)
    keys = keyset()
    items = [(n, list(v)) for v, n in keys.items()]
    kw = os.path.join(TD, "phrase_keys.txt")
    write_kw(kw, items)
    zero = os.path.join(TD, "zero.ksb")
    with open(zero, "wb") as f:
        f.write(b"KSB1" + struct.pack("<I", 1) + struct.pack("<H", 4) + b"zero" + struct.pack("<I", 20000) + bytes(20000))
    fam = "file:" + l2rel(zero)
    seg = l2rel(os.path.join(R.KS, "data", "segments.txt"))
    common = ["mode=known", "isigns=1,28", "litf=0,1", "mults=1", "models=0", "offs=0:1", f"threads={threads}"]
    print(f"{len(items)} keys (lengths {min(len(v) for _, v in items)}..{max(len(v) for _, v in items)})", flush=True)
    # control: LP1 phrase key, spelled with C->F, literal F on / off
    eng = os.path.join(L2, "data", "plain.txt")
    res, ok = [], True
    ctl_keys = [("CIRCUMFERENCE C->F", lp.word_to_key("FIRFUMFERENFE"), 1),
                ("WELCOME PILGRIM", lp.word_to_key("WELCOMEPILGRIM"), 0),
                ("DIVINITY", lp.word_to_key("DIVINITY"), 1)]
    for ci, (cname, kv, litf) in enumerate(ctl_keys):
        plant = os.path.join(TD, f"pk_ctl{ci}.txt")
        tsv = os.path.join(R.OUT, f"phrase_keys_control{ci}.tsv")
        l2(["plant", l2rel(eng), fam, "zero", "0", "1", "0", "0.18", str(40 + ci), ",".join(map(str, kv)), "3", "1", str(litf), "0", l2rel(plant)])
        kwc = os.path.join(TD, f"pk_ctl{ci}_kw.txt")
        write_kw(kwc, [(cname.replace(" ", "_"), kv)] + random.Random(ci).sample(items, 200))
        l2(["screen", l2rel(plant), fam, l2rel(tsv), f"kw={l2rel(kwc)}"] + common)
        for w, (sc, inner) in best(tsv).items():
            good = sc >= 1.40 and cname.replace(" ", "_") in inner
            ok &= good
            res.append(f"{'PASS' if good else 'FAIL'} plant {cname} litf={litf} {w}: IoC {sc:.3f} {inner[:50]}")
    # null: random keywords of the same lengths
    rng = random.Random(77)
    nulls = [("r", [rng.randrange(29) for _ in v]) for _, v in items]
    nkw = os.path.join(TD, "phrase_keys_null.txt")
    write_kw(nkw, nulls)
    out_n, out_r = os.path.join(R.OUT, "phrase_keys_null.tsv"), os.path.join(R.OUT, "phrase_keys.tsv")
    l2(["screen", seg, fam, l2rel(out_n), f"kw={l2rel(nkw)}"] + common)
    l2(["screen", seg, fam, l2rel(out_r), f"kw={l2rel(kw)}"] + common)
    bn, br = best(out_n), best(out_r)
    head = (f"solved-phrase-keys ({len(items)} keys x 2 signs x litf 0/1): control {'PASS' if ok else 'FAIL'} "
            f"({sum('PASS' in x for x in res)}/{len(res)}); keys best IoC {max(v[0] for v in br.values()):.4f}, "
            f"random same-length keys best {max(v[0] for v in bn.values()):.4f}")
    lines = [head] + res + [f"{w}: keys {v[0]:.4f} ({v[1][:40]}); random {bn[w][0]:.4f}" for w, v in br.items()]
    top = max(v[0] for v in br.values())
    lines.append("hits >= 1.40: " + ("none" if top < 1.40 else "see tsv; verify with layer2/verify.py + lang_checks"))
    text = "\n".join(lines)
    print(text)
    open(os.path.join(R.OUT, "summary_phrase_keys.txt"), "w", encoding="utf-8", newline="\n").write(text + "\n")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--threads", type=int, default=12)
    run(ap.parse_args().threads)
