"""Pre-launch plants (a)/(b)/(c) through the REAL library file, planted in Python with the
exact h5slice semantics, then sanity-decoded in Python (the same decode the Rust engine
port is bit-identical to) before the Rust sweeps run.

Plants (see CAMPAIGN.md "Pre-launch controls"):
  (a) library stream 'primes'            (p_n mod 29, 20000 values, NON-totient)
      keyword FIRFUMFERENFE (L=13), offset 1300, window seg0.8 (prev 7)
  (b) library stream 'primes'            keyword CIRCUMFERENCE (L=13), offset 1600,
      window seg0.11 (prev 24)
  (c) library stream 'primes-1 (totient)' keyword DIVINITY (L=8), DEEP offset 1422,
      window seg0.14 (prev 20)
  (c1500) SAME as (c) but offset 1500 as first specified: the campaign's init abort
      (120, 0.9) kills the truth cell there (documented finding; the no-abort decode
      recovers wcol=DIVINITY exactly, IoC 1.6984). The sweep record for this window is
      kept in prelaunch_controls.txt as the negative documentation; control (c) uses the
      closest deep offset whose truth cell survives the abort as a clean argmax (1422).

Plant semantics: work/h5slice.h5slice.plant EXACTLY as called (model 0 = skip, keep 0.19,
litf False, b 0, seed 42, plaintext = Self-Reliance runes 3000:3300 via work/sim.py).
The keyword indices come from work/lp.py word_to_key (greedy digraph mapping; V -> U):
FIRFUMFERENFE = [0,10,4,0,1,19,0,18,4,18,9,0,18], CIRCUMFERENCE = [5,10,4,5,1,19,0,18,4,18,9,5,18],
DIVINITY = [23,10,1,10,9,10,16,26] (matches work/h5slice.h5slice.DIVINITY).

Stream verification before planting: the library 'primes' values must equal the independent
prime sieve mod 29 (work/h5slice sieve_primes and work/keystreams.py), i.e. the values
h5slice would generate; the plant then uses the library's EXACT bytes, so the plant is what
the Rust file: path reads. Writes the three single-window files in the h5rs window format
(W name prev / R runes, first 300 runes), then sanity-decodes each plant at its truth cell
and at wrong cells with h5slice.decode(fast_init=True, beam 24, max_em 5, beam_a 12,
abort_at 120, abort_margin 0.9) - the exact settings of the Rust sweep driver.
"""
import os
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for p in (os.path.join(ROOT, "work"), os.path.join(ROOT, "work", "h5slice")):
    if p not in sys.path:
        sys.path.insert(0, p)

import h5slice as H
import lp
import sim

LIB = os.path.join(ROOT, "work", "kscreen", "data", "library_flat.ksb")
OUT_A = os.path.join(HERE, "data", "plant_a_seg0.8.txt")
OUT_B = os.path.join(HERE, "data", "plant_b_seg0.11.txt")
OUT_C = os.path.join(HERE, "data", "plant_c_seg0.14.txt")

FIRFUM = lp.word_to_key("FIRFUMFERENFE")
CIRCUM = lp.word_to_key("CIRCUMFERENCE")
assert FIRFUM == [0, 10, 4, 0, 1, 19, 0, 18, 4, 18, 9, 0, 18] and len(FIRFUM) == 13
assert CIRCUM == [5, 10, 4, 5, 1, 19, 0, 18, 4, 18, 9, 5, 18] and len(CIRCUM) == 13
assert H.DIVINITY == [23, 10, 1, 10, 9, 10, 16, 26] and len(H.DIVINITY) == 8


def parse_ksb(path):
    b = open(path, "rb").read()
    assert b[:4] == b"KSB1"
    n = struct.unpack_from("<I", b, 4)[0]
    p = 8
    out = {}
    for _ in range(n):
        l = struct.unpack_from("<H", b, p)[0]
        p += 2
        name = b[p:p + l].decode("utf-8")
        p += l
        ln = struct.unpack_from("<I", b, p)[0]
        p += 4
        out[name] = list(b[p:p + ln])
        p += ln
    return out


def write_window(path, name, prev, runes, n=300):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"W {name} {prev}\n")
        f.write("R " + " ".join(str(r) for r in runes[:n]) + "\n")


print("== stream verification (library values == what h5slice/keystreams would generate) ==")
ksb = parse_ksb(LIB)
primes = ksb["primes"]
totient = ksb["primes-1 (totient)"]
print(f"library streams: primes len {len(primes)}, totient len {len(totient)}")

sieve20k = H.sieve_primes(20000)
h5_primes = [p % 29 for p in sieve20k]
h5_totient = [(p - 1) % 29 for p in sieve20k]
print("primes == h5slice sieve mod 29:", primes[:20000] == h5_primes)
print("totient == h5slice sieve (p-1) mod 29:", totient[:20000] == h5_totient)

import keystreams as K
ks = K.integer_sequences()
print("primes == keystreams.py 'primes':", primes[:20000] == list(ks["primes"][:20000]))
print("totient == keystreams.py 'primes-1 (totient)':",
      totient[:20000] == list(ks["primes-1 (totient)"][:20000]))
assert primes[:20000] == h5_primes and totient[:20000] == h5_totient, "stream mismatch"

print("\n== plants (h5slice.plant, model 0, keep 0.19, seed 42, litf False, b 0) ==")
plain_all = sim.english_runes()
plain = plain_all[3000:3300]          # Self-Reliance runes 3000:3300 (calib.py convention)
print(f"plaintext: Self-Reliance runes 3000:3300, IoC {H.overall_ioc(plain):.3f}, "
      f"F count {plain.count(0)}")

plants = [
    # id, stream values, kw, offset, window name, prev, out path
    ("a", primes, FIRFUM, 1300, "seg0.8", 7, OUT_A),
    ("b", primes, CIRCUM, 1600, "seg0.11", 24, OUT_B),
    ("c", totient, H.DIVINITY, 1422, "seg0.14", 20, OUT_C),
    ("c1500", totient, H.DIVINITY, 1500, "seg0.14", 20,
     os.path.join(HERE, "data", "plant_c1500_seg0.14.txt")),
]
ciphers = {}
for pid, tvals, kw, off, wname, prev, out in plants:
    c = H.plant(plain, tvals, off, kw, 0, keep=0.19, litf=False, b=0, seed=42)
    assert len(c) == 300
    write_window(out, wname, prev, c)
    ciphers[pid] = c
    print(f"({pid}) {wname} prev={prev} kw={kw} off={off}: cipher IoC "
          f"{H.overall_ioc(c):.3f}, doublets {sum(a == b for a, b in zip(c, c[1:]))} -> {out}")

print("\n== Python sanity decode (h5slice, fast_init, beam 24, max_em 5, beam_a 12, "
      "abort (120, 0.9) = the Rust sweep settings) ==")
logf = H.english_logf()
for pid, tvals, kw, off, wname, prev, _out in plants:
    L = len(kw)
    for desc, o2, L2 in [("truth", off, L), ("off-1", off - 1, L), ("off+1", off + 1, L),
                         ("L-1", off, L - 1), ("L+1", off, L + 1), ("model1", off, L)]:
        m2 = 1 if desc == "model1" else 0
        ioc, info = H.decode(ciphers[pid], prev, tvals, o2, L2, m2, litf=False, beam=24,
                             max_em=5, logf=logf, abort_at=120, abort_margin=0.9,
                             out_path=False, beam_a=12, fast_init=True)
        extra = ""
        if desc == "truth" and info is not None:
            extra = f" wcol={list(info) if not isinstance(info, dict) else info}"
            try:
                extra = f" wcol={info['wcol'] if isinstance(info, dict) else info} " \
                        f"kwmatch={list(info['wcol']) == kw if isinstance(info, dict) else info == kw}"
            except Exception:
                pass
        print(f"  ({pid}) {desc:7} off={o2} L={L2} m={m2}: ioc {ioc:.4f}{extra}")
print("\nprelaunch_plant done")
