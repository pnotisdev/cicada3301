"""Layout-number rules for the kscreen engine (phase 36): 'their numbers are the direction' (2016) read as the PAGE, LINE and POSITION numbers of the layout rather than the numbers of the words.

Per-rune key signs (engine S lines, 'signs') or native directions (engine D lines, 'pdir') are decided by the layout number of the rune: parity, mod 3 (three shifts of the residue classes, because the page / line numbering origin is unknown), first / second half of the page (by runes or by
lines), and one combination (page + line parity). New file next to signrules.py (that file and its data are untouched; the campaigns import it).

Layout of a rune (from the master's separators, carried across the '$' segment boundaries because a section can start mid-page and mid-line):
  page_abs   1 + number of '%' before it in the whole master (the first page of the master is 1; a different origin is a shift: parity flips = the multiplier 28, mod-3 shifts are kept as three rules)
  page_sec   1 + number of '%' before it inside its section (a section that does not start with '%' starts on page 1 of the section)
  line_pg    1 + number of '/' since the last '%' (carried over a section boundary)
  line_sec   1 + number of '/' before it inside its section
  pos_ln     its 1-based position in the line (carried over a section boundary)
  page_runes / page_lines   the totals of its page in the master
A word that crosses a line or a page break is NOT kept together: each rune takes the layout number of where it sits (the hypothesis is about the layout, not the words). Section-number rules (parity or mod 3 of 0.7 .. 0.15) are constant inside every window, so
they equal the multiplier 28 per window and are not built. The rules use only the layout (known to the encryptor when the text is typeset), no ciphertext at all: they are causal in the sense of signrules.py.

    python work/kscreen/layoutrules.py     # -> data/layout_signs/<rule>.txt (S lines), data/layout_dirs/<rule>.txt (D lines), layout_rules.txt (tracked)
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
WORK = os.path.dirname(HERE)
sys.path.insert(0, WORK)
sys.path.insert(0, HERE)
import stats  # noqa: E402
import signrules as R  # noqa: E402

SIGN_OUT = os.path.join(HERE, "data", "layout_signs")
DIR_OUT = os.path.join(HERE, "data", "layout_dirs")


def layout_features():
    """list per master segment (index as lp.load_segments) of per-rune dicts"""
    out, page, line, pos = [], 1, 1, 0
    for toks in stats.SEGS:
        feats, psec, lsec = [], 1, 1
        for t in toks:
            if isinstance(t, int):
                pos += 1
                feats.append(dict(page_abs=page, page_sec=psec, line_pg=line, line_sec=lsec, pos_ln=pos))
            elif t == "%":
                page += 1
                psec += 1
                line, pos = 1, 0
            elif t == "\n":
                line += 1
                lsec += 1
                pos = 0
        out.append(feats)
    runes, lines = {}, {}
    for feats in out:
        for f in feats:
            runes[f["page_abs"]] = runes.get(f["page_abs"], 0) + 1
            lines[f["page_abs"]] = max(lines.get(f["page_abs"], 0), f["line_pg"])
    r_in = {}
    for feats in out:
        for f in feats:
            r_in[f["page_abs"]] = r_in.get(f["page_abs"], 0) + 1
            f["rune_pg"] = r_in[f["page_abs"]]
            f["page_runes"], f["page_lines"] = runes[f["page_abs"]], lines[f["page_abs"]]
    return out


def par(q):
    return 1 if q % 2 == 0 else -1


def m3(q, s):
    return 1 if (q + s) % 3 <= 1 else -1


def build_rules():
    """name -> fn(feature dict) -> +1 / -1"""
    rules = {"Pa_par": lambda f: par(f["page_abs"]), "Ps_par": lambda f: par(f["page_sec"]), "Ln_par": lambda f: par(f["line_pg"]), "Ls_par": lambda f: par(f["line_sec"]),
             "Po_par": lambda f: par(f["pos_ln"]), "PL_xor": lambda f: par(f["page_abs"] + f["line_pg"]),
             "Pg_half_runes": lambda f: 1 if 2 * f["rune_pg"] <= f["page_runes"] else -1, "Pg_half_lines": lambda f: 1 if 2 * f["line_pg"] <= f["page_lines"] else -1}
    for key, src in (("Pa", "page_abs"), ("Ps", "page_sec"), ("Ln", "line_pg"), ("Ls", "line_sec"), ("Po", "pos_ln")):
        for s in range(3):
            rules[f"{key}_m3_{s}"] = (lambda src, s: lambda f: m3(f[src], s))(src, s)
    return rules


def window_tables():
    """(head, runes, lens line, per-rune features) for the 8 windows of data/segments.txt"""
    feats = layout_features()
    out = []
    for head, runes, lens, spans, words in R.section_tables():
        seg = int(head.split()[1].split(".")[1])
        assert len(feats[seg]) == len(runes), f"{head}: layout and window differ in length"
        out.append((head, runes, lens, feats[seg], spans))
    return out


def vector(fn, feats):
    return [fn(f) for f in feats]


def word_vector(fn, feats, spans, n):
    """pdir directions are per WORD (the engine rejects a D line that changes inside a word): the layout number of the word's FIRST rune decides the direction of the whole word (a word that wraps keeps the direction of where it starts)"""
    d = []
    for a, b in spans:
        d += [fn(feats[a])] * (b - a)
    return d[:n] + [1] * max(0, n - len(d))


def main():
    os.makedirs(SIGN_OUT, exist_ok=True)
    os.makedirs(DIR_OUT, exist_ok=True)
    tabs = window_tables()
    kept, seen, rows = [], {}, []
    for name, fn in build_rules().items():
        vec = tuple(x for (_, _, _, fe, _) in tabs for x in vector(fn, fe))
        neg = tuple(-x for x in vec)
        if len(set(vec)) == 1:
            rows.append((name, "dropped: constant"))
            continue
        if vec in seen or neg in seen:
            rows.append((name, f"dropped: same as {seen.get(vec) or seen.get(neg)}"))
            continue
        seen[vec] = name
        kept.append(name)
        for root, letter in ((SIGN_OUT, "S"), (DIR_OUT, "D")):
            with open(os.path.join(root, name + ".txt"), "w", newline="\n", encoding="utf-8") as f:
                for head, runes, lens, fe, spans in tabs:
                    v = vector(fn, fe) if letter == "S" else word_vector(fn, fe, spans, len(runes))
                    f.write(f"{head}\nR {' '.join(map(str, runes))}\n{lens}\n{letter} {' '.join(map(str, v))}\n")
    with open(os.path.join(HERE, "layout_rules.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(kept) + "\n")
    print(f"{len(build_rules())} layout rules built, {len(kept)} kept")
    for n, s in rows:
        print("   ", n, s)
    return kept


if __name__ == "__main__":
    main()
