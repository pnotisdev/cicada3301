"""Does LP2's key restart at typographic marks? (cicadanotebook.com sessions 17-20 and 55-63;
work/log/research_cicadanotebook_2026-10-17.md, section 5; log work/log/typo_restarts_2026-10-17.md)

Already tested: the keystream library restarted AT each red heading and page start (campaign kscreen-restarts) and a
key-agnostic restart at every page, paragraph, line, clause and word (restart_columns.py). New here:

  list      the numbered list of 0.14 (items 1-5 at offsets 754, 893, 984, 1082, 1178; the closing 10-dot mark at 1307):
            each item alone (the key offset is free, so label-based counters are covered), the whole list from its
            opening mark, and the text after the closing mark;
  dots      the five three-dot marks (images 22, 28, 37, 55, 63; confirmed by work/tmp/hyp/page_seam_dots.py);
  body      the text right after each red heading (the kscreen-restarts windows start AT the heading).

Modes:
    python work/typo_restarts.py export   # kscreen windows -> work/kscreen/data/typo.txt, English twins -> typo_plain.txt
    python work/typo_restarts.py known    # solved sections: the true key continuous vs restarted at their three-dot marks
    python work/typo_restarts.py pooled   # one keystream restarted at EVERY list item (pooled decode), plants + null
    python work/typo_restarts.py plants   # planted library keys in English twins of the windows, against the matched null
    python work/typo_restarts.py summary  # -> results/kscreen/typo_summary.txt (needs the kscreen-typo campaign's screens)
"""
import json
import os
import re
import sys


HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import attack  # noqa: E402
import lp  # noqa: E402
import stats  # noqa: E402

N = lp.N
S = stats.SEGS
KS = os.path.join(HERE, "kscreen")
DATA = os.path.join(KS, "data")
RES = os.path.join(ROOT, "results", "kscreen")
LIST = [754, 893, 984, 1082, 1178]          # 0.14 offsets of list items 1-5 (the numerals #1-#5)
LIST_END = 1307                             # the closing 10-dot mark (cicadanotebook sessions 17-18)
DOTS = [(8, 588), (9, 1036), (11, 1355), (14, 1149), (15, 1689)]
# solved sections with three-dot marks (rune offsets of the first rune after the mark) and their known keys
KNOWN_DOTS = {5: [110, 286], 16: [19]}


def red_bodies():
    """first rune after each red heading (consecutive red runs merged), LP2 sections only"""
    with open(os.path.join(HERE, "tmp", "phase4", "red_runs.json"), encoding="utf-8") as f:
        runs = sorted((d["seg"], d["start"], d["end"]) for d in json.load(f))
    merged = []
    for seg, a, b in runs:
        if merged and merged[-1][0] == seg and a <= merged[-1][2] + 1:
            merged[-1][2] = max(merged[-1][2], b)
        else:
            merged.append([seg, a, b])
    out = []
    for seg, a, b in merged:
        n = len(lp.runes_of(S[seg]))
        if seg in stats.UNSOLVED and seg != 10 and b + 1 < n:
            out.append((seg, b + 1))
    return out


def points():
    """[(name, seg, start, end)] of every new restart window (end exclusive)"""
    assert [p for p, _ in lp.numeral_positions(S[14])] == LIST, "list numerals moved"
    n14 = len(lp.runes_of(S[14]))
    pts = [(f"item{k + 1}_0.14@{s}", 14, s, (LIST + [LIST_END])[k + 1]) for k, s in enumerate(LIST)]
    pts.append(("list_0.14@754", 14, LIST[0], LIST_END))
    pts.append((f"afterlist_0.14@{LIST_END}", 14, LIST_END, n14))
    pts += [(f"dots_0.{seg}@{s}", seg, s, len(lp.runes_of(S[seg]))) for seg, s in DOTS]
    pts += [(f"body_0.{seg}@{s}", seg, s, len(lp.runes_of(S[seg]))) for seg, s in red_bodies()]
    return pts


def window_lens(seg, a, b):
    """word lengths inside runes [a, b) of a section; words cut by the window edges are truncated"""
    out = []
    for _, x, y in lp.word_spans(S[seg], lp.runes_of(S[seg])):
        lo, hi = max(x, a), min(y, b)
        if lo < hi:
            out.append(hi - lo)
    assert sum(out) == b - a
    return out


def english_twin(n, start):
    """(runes, word lengths) of exactly n runes of Emerson from word index `start` (the last word is cut to fit;
    Emerson has about 75,000 words, so start + n/3 must stay below that)"""
    toks = attack.synthetic_tokens(n + 40, start=start)
    runes, lens, cur = [], [], 0
    for t in toks:
        if isinstance(t, int):
            if len(runes) == n:
                break
            runes.append(t)
            cur += 1
        elif cur:
            lens.append(cur)
            cur = 0
    if cur:
        lens.append(cur)
    assert len(runes) == n and sum(lens) == n, (n, start)
    return runes, lens


def write_windows(path, items):
    with open(path, "w", newline="\n", encoding="utf-8") as f:
        for name, prev, runes, lens in items:
            assert sum(lens) == len(runes)
            f.write(f"W {name} {prev}\nR {' '.join(map(str, runes))}\nL {' '.join(map(str, lens))}\n")


def export():
    os.makedirs(DATA, exist_ok=True)
    items, plain = [], []
    for k, (name, seg, a, b) in enumerate(points()):
        c = lp.runes_of(S[seg])
        items.append((name, c[a - 1] if a > 0 else -1, c[a:b], window_lens(seg, a, b)))
        # an English twin of exactly the scored length (kscreen scores the first 300 runes) for the planted controls
        plain.append((name, -1) + english_twin(min(b - a, 300), start=30000 + 1200 * k))
    write_windows(os.path.join(DATA, "typo.txt"), items)
    write_windows(os.path.join(DATA, "typo_plain.txt"), plain)
    for name, prev, runes, lens in items:
        print(f"{name:24s} {len(runes):5d} runes, {len(lens):4d} words")
    print(f"wrote {len(items)} windows to work/kscreen/data/typo.txt and English twins to typo_plain.txt")


# ---------------------------------------------------------------- known answers on the solved sections

def known():
    lines = ["Known answers: the solved sections' keys run straight through their three-dot marks?",
             "(wrong runes against the published decryption when the key index restarts at the mark, or skips one position there)"]
    fir, pr = lp.word_to_key("FIRFUMFERENFE"), lp.primes(2000)
    keys = {5: ("FIRFUMFERENFE, literal F at 49 and 58", lambda j: fir[j % len(fir)], {49, 58}),
            16: ("primes-1, literal F at 56", lambda j: pr[j] - 1, {56})}
    for seg, (label, kf, lit) in keys.items():
        c = lp.runes_of(S[seg])
        truth = lp.KNOWN[seg][1](c)
        assert truth == lp.keyed(c, kf, lit)
        for m in KNOWN_DOTS[seg]:
            used = sum(1 for i in range(m) if i not in lit)      # key positions consumed before the mark
            for rule, start in (("restart", 0), ("skip one", used + 1)):
                p = c[:m] + lp.keyed(c[m:], lambda j, s=start: kf(s + j), {i - m for i in lit if i >= m})
                wrong = sum(x != y for x, y in zip(p[m:], truth[m:]))
                lines.append(f"   0.{seg} ({label}), mark before rune {m}: {rule:8s} -> {wrong} of {len(c) - m} runes wrong")
        lines.append(f"   0.{seg}: continuous key -> 0 wrong (the published decryption)")
    return lines


# ---------------------------------------------------------------- one keystream restarted at every list item

# A first version decoded the first 30 runes of each item directly and pooled them; it failed its own plant control (the
# anti-repeat skips derail a direct decode after about 20 runes, and 150 pooled runes cannot beat the null maximum). This
# version lets kscreen's beam decoder (which follows the skips) screen each item alone, keeps each item's top 2,000
# decodes, and asks whether one (keystream, multiplier, model, offset) recurs in 3 or more of the 5 lists: a shared
# key that decodes every item should, chance almost never does (2,000 of ~10^8 decodes per list).

ITEM_RES = os.path.join(RES, "typo_items")
POOL_PLANTS = [("primes-1 (totient)", 1234, 1, 0, 0), ("pi digits (base 29)", 777, 28, 1, 1),
               ("sha256-ctr reject :3301", 4321, 1, 0, 1)]   # stream, offset, mult, model, d (item k from offset + d*k)


def rel_ks(path):
    return os.path.relpath(path, KS).replace("\\", "/")      # result headers must not show this PC's folders


def list_bounds():
    return list(zip(LIST, LIST[1:] + [LIST_END]))


def item_lists(family, tag):
    """each list item screened alone with the whole family: {k: [(ioc, stream, offset, mult, model)]}, its top 2,000"""
    os.makedirs(ITEM_RES, exist_ok=True)
    tmp = os.path.join(HERE, "tmp", "typo")
    os.makedirs(tmp, exist_ok=True)
    c14 = lp.runes_of(S[14])
    out = {}
    for k, (a, b) in enumerate(list_bounds()):
        win = os.path.join(tmp, f"item{k + 1}.txt")
        write_windows(win, [(f"item{k + 1}_0.14@{a}", c14[a - 1], c14[a:b], window_lens(14, a, b))])
        tsv = os.path.join(ITEM_RES, f"{tag}_item{k + 1}.tsv")
        if not os.path.exists(tsv):
            kscreen(["screen", rel_ks(win), family, rel_ks(tsv), "top=2000"])
        rows = []
        with open(tsv, encoding="utf-8") as f:
            for line in f:
                if line.startswith("#") or line.startswith("ioc\t"):
                    continue
                ioc, stream, off, mult, model = line.rstrip("\n").split("\t")[:5]
                rows.append((float(ioc), stream, int(off), int(mult), int(model)))
        out[k] = rows
    return out


def shared(lists, d):
    """(stream, mult, model, base offset) -> the list items whose top list holds it at offset base + d*k"""
    hits = {}
    for k, rows in lists.items():
        for _, stream, off, mult, model in rows:
            hits.setdefault((stream, mult, model, off - d * k), set()).add(k)
    return hits


def plant_items(stream, off, mult, model, d, seed):
    """IoC of the true decode of each list item when one keystream restarts at every item (English twins of the items'
    exact lengths, anti-repeat rule with keep 0.18)"""
    tmp = os.path.join(HERE, "tmp", "typo")
    out = []
    for k, (a, b) in enumerate(list_bounds()):
        plain, planted = (os.path.join(tmp, f"pool_{x}{seed}_{k}.txt") for x in ("plain", "planted"))
        runes, lens = english_twin(b - a, start=8000 + 6000 * seed + 400 * k)
        write_windows(plain, [(f"item{k + 1}", -1, runes, lens)])
        kscreen(["plant", rel_ks(plain), "file:data/library.ksb", stream, str(off + d * k), str(mult), str(model), "0.18",
                 str(300 + 10 * seed + k), "0", rel_ks(planted)])
        v = kscreen(["verify", rel_ks(planted), "file:data/library.ksb", stream, str(off + d * k), str(mult), str(model), "all"])
        out.append(float(re.search(r"ioc ([\d.]+)", v).group(1)))
    return out


def pooled():
    lines = ["One keystream restarted at EVERY item of the 0.14 list (items 1-5, 91-139 runes): each item screened alone by "
             "kscreen with the 1,439-keystream library (beam decoding through the anti-repeat skips), its top 2,000 decodes "
             "kept; a shared key shows as one (keystream, multiplier, model, offset) in 3 or more of the 5 lists, at the same "
             "offset (d = 0) or at offset + k for item k (d = 1, a counter from the item label)."]
    fams = {"library": item_lists("file:data/library.ksb", "library"), "null": item_lists("rand:1439:23", "null")}
    cut = {k: min(r[0] for r in rows) for k, rows in fams["library"].items()}
    lines.append("top-2,000 cut-off IoC per item (library): " + ", ".join(f"item {k + 1} {cut[k]:.3f}" for k in sorted(cut)))
    for tag, lists in fams.items():
        for d in (0, 1):
            h = shared(lists, d)
            many = sorted(((len(v), key) for key, v in h.items() if len(v) >= 2), reverse=True)
            n2 = sum(1 for n, _ in many if n == 2)
            n3 = sum(1 for n, _ in many if n >= 3)
            top = f"; most shared: {many[0][1][0]!r} offset {many[0][1][3]} in {many[0][0]} items" if many else ""
            lines.append(f"   {tag:7s} d={d}: candidates in 2 lists {n2}, in 3 or more {n3}{top}")
    for ci, (stream, off, mult, model, d) in enumerate(POOL_PLANTS):
        iocs = plant_items(stream, off, mult, model, d, seed=ci + 1)
        enter = sum(i >= cut[k] for k, i in enumerate(iocs))
        lines.append(f"{'PASS' if enter >= 3 else 'FAIL'}  plant {stream!r} offset {off} mult {mult} model {model} d {d}: "
                     f"true-key IoC per item {', '.join(f'{i:.3f}' for i in iocs)}; above the item's cut-off in {enter} of 5 "
                     f"(3 needed)")
    return lines


# ---------------------------------------------------------------- summary of the kscreen screens

def tsv_bests(path):
    """window -> (best IoC, item, offset, mult, model) from the '# window' lines of a kscreen screen TSV"""
    best = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r"# window (\S+) best ([\d.]+) item=(.*) offset=(\S+) mult=(\d+) model=(\d+)", line)
            if m:
                best[m.group(1)] = (float(m.group(2)), m.group(3), m.group(4), m.group(5), m.group(6))
    return best


PLANTS = [("primes-1 (totient)", "1234", 1, 0, 0), ("pi digits (base 29)", "777", 28, 1, 1),
          ("sha256-ctr reject :3301", "4321", 1, 0, 1)]


def kscreen(args):
    import subprocess
    exe = os.path.join(KS, "target", "release", "kscreen" + (".exe" if os.name == "nt" else ""))
    r = subprocess.run([exe] + args, cwd=KS, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"kscreen {' '.join(args)} failed:\n{r.stderr}")
    return r.stdout


def plants():
    """library keys planted into the English twins of the 22 windows (anti-repeat rule, keep 0.18), screened with the true
    keystream at every offset: is the planted key its window's best at the true offset, and does its IoC clear the
    matched null maximum of the same LP2 window (null_typo.tsv)? Short windows show how much power the screen has."""
    pts = points()
    null = tsv_bests(os.path.join(RES, "null_typo.tsv")) if os.path.exists(os.path.join(RES, "null_typo.tsv")) else {}
    tmp = os.path.join(HERE, "tmp", "typo")
    os.makedirs(tmp, exist_ok=True)
    lines = ["Planted controls: a library key planted into English twins of the 22 windows (same scored length), screened "
             "with the true keystream at every offset; 'clears null' = its IoC beats the best of 1,439 random keystreams on the "
             "real LP2 window of that name."]
    rows = []
    for ci, (item, off, mult, model, subst) in enumerate(PLANTS):
        plant = os.path.join(tmp, f"plant{ci}.txt")
        tsv = os.path.join(tmp, f"plant{ci}.tsv")
        relp, relt = (os.path.relpath(p, KS).replace("\\", "/") for p in (plant, tsv))
        kscreen(["plant", "data/typo_plain.txt", "file:data/library.ksb", item, off, str(mult), str(model), "0.18",
                 str(200 + ci), str(subst), relp])
        kscreen(["screen", relp, "file:data/library.ksb", relt, f"only={item}"])
        truth = {}
        with open(plant, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"# truth (\S+) item=(.*) offset=(\S+) mult=", line)
                if m:
                    truth[m.group(1)] = m.group(3)
        best = tsv_bests(tsv)
        for wi, (name, seg, a, b) in enumerate(pts):
            w = f"plant_{wi}"
            ioc, _, boff, _, _ = best.get(w, (0.0, "-", "-", "-", "-"))
            nmax = null.get(name, (float("nan"),))[0]
            rows.append((name, min(b - a, 300), item, boff == truth.get(w), ioc, nmax))
    for name, n, item, hit, ioc, nmax in rows:
        lines.append(f"   {name:24s} {n:4d} runes  {item:26s} {'recovered' if hit else 'MISSED':9s} IoC {ioc:.3f}  "
                     f"null max {nmax:.3f}  {'clears null' if ioc > nmax else 'BELOW NULL'}")
    for lo, hi in ((0, 150), (150, 250), (250, 301)):
        sel = [r for r in rows if lo <= r[1] < hi]
        if sel:
            lines.append(f"windows of {lo}-{hi - 1} runes: recovered {sum(r[3] for r in sel)}/{len(sel)}, "
                         f"clear their null {sum(r[4] > r[5] for r in sel)}/{len(sel)}")
    return lines


def summary():
    lines = ["# work/typo_restarts.py summary: key restarts at typographic marks of LP2 (campaign kscreen-typo)", ""]
    lib, null = os.path.join(RES, "library_typo.tsv"), os.path.join(RES, "null_typo.tsv")
    if os.path.exists(lib) and os.path.exists(null):
        lb, nb = tsv_bests(lib), tsv_bests(null)
        lens = {name: min(b - a, 300) for name, _, a, b in points()}
        lines.append("Library (1,439 keystreams) against a random null of the same size (1,439 keystreams of 20,000), per window:")
        lines.append(f"{'window':24s} {'runes':>5s}  {'library best':>12s}  {'null best':>9s}  library item at best")
        above = 0
        for name in lens:
            l, n = lb.get(name), nb.get(name)
            if l is None or n is None:
                lines.append(f"{name:24s} {lens[name]:5d}  (missing)")
                continue
            above += l[0] > n[0]
            lines.append(f"{name:24s} {lens[name]:5d}  {l[0]:12.3f}  {n[0]:9.3f}  {l[1]} @ {l[2]} (mult {l[3]}, model {l[4]})")
        lines.append(f"windows where the library beats its matched null: {above} of {len(lens)} (about half expected by chance)")
        ver = os.path.join(RES, "library_typo_verify.txt")
        if os.path.exists(ver):
            with open(ver, encoding="utf-8") as f:
                tail = [x.rstrip() for x in f if "re-decoded" in x]
            lines += [f"verification: {x}" for x in tail[-1:]]
    for name in ("typo_plants.txt", "typo_known.txt", "typo_pooled.txt"):
        p = os.path.join(RES, name)
        if os.path.exists(p):
            with open(p, encoding="utf-8") as f:
                lines += ["", f"## {name}"] + [x.rstrip() for x in f]
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, "typo_summary.txt"), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print("\n".join(lines))


def write(name, lines, quiet=False):
    os.makedirs(RES, exist_ok=True)
    with open(os.path.join(RES, name), "w", newline="\n", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    if not quiet:
        print("\n".join(lines))


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    mode = argv[1] if len(argv) > 1 else "export"
    if mode == "export":
        export()
    elif mode == "known":
        write("typo_known.txt", known())
    elif mode == "pooled":
        write("typo_pooled.txt", pooled())
    elif mode == "plants":
        write("typo_plants.txt", plants())
    elif mode == "summary":
        summary()
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main(sys.argv)
