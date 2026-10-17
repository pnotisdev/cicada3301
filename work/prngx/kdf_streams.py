"""KDF / stream-cipher keystreams from passphrases, scanned through prngx's `seq` lane.

    python work/prngx/kdf_streams.py build <cands.txt> [--out data/kdf_seqs.txt]   # streams -> sequence library
    python work/prngx/kdf_streams.py plant <candidate> <tag> <map> <out_windows.txt> # planted control windows
    python work/prngx/kdf_streams.py run <cands.txt>                                # build, sweep, report
    python work/prngx/kdf_streams.py verify <lib.txt.tsv> [--top 20]                # whole-segment re-decode

For every candidate string s the keystream bytes of
    rc4(s), rc4-drop768(s)                       RC4 with the passphrase as key
    aes128-ctr(md5(s)), aes256-ctr(sha256(s))    zero nonce, keystream of zeros
    chacha20(sha256(s))                          zero nonce
    pbkdf2-hmac-{sha1,sha256,sha512}(s, salt b"", 1 / 1000 / 4096 iterations)
    scrypt(s, salt b"", N=1024, r=8, p=1)
are turned into key values by two maps (b % 29, and b < 232 rejected then % 29) and written as sequences for the `seq`
generator (values mod 29, one line per (candidate, stream, map), at most 200 values). The sweep uses start offset 0 only
(PRNGX_SEQ_OFFMAX=1), all 28 multipliers, both signs, Atbash, both anti-repeat models on windows_07.txt. The line index
maps back to (candidate, stream, map) through the `.index` file written next to the library.
"""
import argparse
import hashlib
import os
import subprocess
import sys
from multiprocessing import Pool

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "data")
PHP_DATA = os.path.join(ROOT, "work", "phpmt", "data")
NVAL = 200
TAGS = ["rc4", "rc4d768", "aes128ctr", "aes256ctr", "chacha20", "pbkdf2-sha1-1", "pbkdf2-sha1-1000", "pbkdf2-sha1-4096",
        "pbkdf2-sha256-1", "pbkdf2-sha256-1000", "pbkdf2-sha256-4096", "pbkdf2-sha512-1", "pbkdf2-sha512-1000",
        "pbkdf2-sha512-4096", "scrypt-1024"]


def rc4(key, n, drop=0):
    S = list(range(256))
    j = 0
    for i in range(256):
        j = (j + S[i] + key[i % len(key)]) & 255
        S[i], S[j] = S[j], S[i]
    i = j = 0
    out = bytearray()
    for _ in range(drop + n):
        i = (i + 1) & 255
        j = (j + S[i]) & 255
        S[i], S[j] = S[j], S[i]
        out.append(S[(S[i] + S[j]) & 255])
    return bytes(out[drop:])


def ctr_stream(cipher_cls, key, n):
    from cryptography.hazmat.primitives.ciphers import Cipher, modes
    enc = Cipher(cipher_cls(key), modes.CTR(bytes(16))).encryptor()
    return enc.update(bytes(n)) + enc.finalize()


def stream(tag, s, n=NVAL * 2):
    if tag == "rc4":
        return rc4(s, n)
    if tag == "rc4d768":
        return rc4(s, n, 768)
    if tag == "aes128ctr":
        from cryptography.hazmat.primitives.ciphers import algorithms
        return ctr_stream(algorithms.AES, hashlib.md5(s).digest(), n)
    if tag == "aes256ctr":
        from cryptography.hazmat.primitives.ciphers import algorithms
        return ctr_stream(algorithms.AES, hashlib.sha256(s).digest(), n)
    if tag == "chacha20":
        from cryptography.hazmat.primitives.ciphers import Cipher, algorithms
        enc = Cipher(algorithms.ChaCha20(hashlib.sha256(s).digest(), bytes(16)), mode=None).encryptor()
        return enc.update(bytes(n))
    if tag.startswith("pbkdf2-"):
        _, h, it = tag.split("-")
        return hashlib.pbkdf2_hmac(h, s, b"", int(it), n)
    if tag == "scrypt-1024":
        return hashlib.scrypt(s, salt=b"", n=1024, r=8, p=1, dklen=n, maxmem=64 * 1024 * 1024)
    raise ValueError(tag)


def to_keys(b, mp):
    if mp == 0:
        v = [x % 29 for x in b]
    else:
        v = [x % 29 for x in b if x < 232]
    return v[:NVAL]


def one(args):
    idx, cand = args
    s = cand.encode("utf-8")
    out = []
    for tag in TAGS:
        try:
            b = stream(tag, s)
        except Exception:
            continue
        for mp in (0, 1):
            out.append((f"{idx}:{tag}:{mp}", to_keys(b, mp)))
    return idx, cand, out


def build(cands_path, out_path):
    with open(cands_path, encoding="utf-8") as f:
        cands = [l.rstrip("\n") for l in f if l.strip()]
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    n = 0
    with open(out_path, "w", newline="\n") as lib, open(out_path + ".index", "w", newline="\n", encoding="utf-8") as ix, \
            Pool() as pool:
        for idx, cand, rows in pool.imap(one, list(enumerate(cands)), chunksize=64):
            for name, v in rows:
                lib.write(f"S{n} " + " ".join(map(str, v)) + "\n")
                ix.write(f"{n}\t{cand}\t{name.split(':', 1)[1]}\n")
                n += 1
    print(f"{len(cands)} candidates -> {n} sequences in {out_path}")
    return n


def plant(cand, tag, mp, out_windows):
    """English windows (phpmt/data/english.txt) enciphered with the candidate's stream under the skip rule"""
    import random
    mp = int(mp)
    b = stream(tag, cand.encode("utf-8"), 4000)          # 400-rune windows need ~420 key values; NVAL is only for the library
    keys = [x % 29 for x in b] if mp == 0 else [x % 29 for x in b if x < 232]
    rng = random.Random(1)
    out, j = [], 0
    with open(os.path.join(PHP_DATA, "english.txt"), encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    for k in range(0, len(lines), 3):
        head, r, l = lines[k], lines[k + 1], lines[k + 2]
        runes = [int(x) for x in r[2:].split()]
        j = 0
        prev, c = -1, []
        for t in runes:
            y = (t + keys[j]) % 29
            j += 1
            while y == prev and rng.random() < 0.82:
                y = (t + keys[j]) % 29
                j += 1
            c.append(y)
            prev = y
        out += [head.replace("W ", "W planted_", 1), "R " + " ".join(map(str, c)), l]
    with open(out_windows, "w", newline="\n") as f:
        f.write("\n".join(out) + "\n")
    print("planted", cand, tag, mp)


def sweep(lib, windows, out_tsv, threads=None):
    exe = os.path.join(HERE, "target", "release", "prngx" + (".exe" if os.name == "nt" else ""))
    if not os.path.exists(exe):
        exe = os.path.join(HERE, "target_seq", "release", "prngx" + (".exe" if os.name == "nt" else ""))
    n = sum(1 for _ in open(lib, "rb"))
    env = dict(os.environ, PRNGX_SEQ=lib, PRNGX_SEQ_OFFMAX="1")
    cmd = [exe, "sweep", "seq", windows, os.path.join(PHP_DATA, "dict.txt"), "0", str(n * 128), out_tsv]
    if threads:
        cmd.append(str(threads))
    subprocess.run(cmd, env=env, check=True)


def verify(tsv, top=20, controls=20):
    """Re-decode the best (candidate, stream, map, variant) rows over the WHOLE section with long streams and compare with
    random candidate strings run through the same stream and map."""
    import random
    import statistics
    import string
    lib = tsv[:-4]
    index = {}
    with open(lib + ".index", encoding="utf-8") as f:
        for line in f:
            n, cand, tm = line.rstrip("\n").split("\t")
            index[int(n)] = (cand, tm)
    with open(tsv, encoding="utf-8") as f:
        rows = [l.rstrip("\n").split("\t") for l in f.read().splitlines()[1:]]
    exe = os.path.join(HERE, "target", "release", "prngx" + (".exe" if os.name == "nt" else ""))
    if not os.path.exists(exe):
        exe = os.path.join(HERE, "target_seq", "release", "prngx" + (".exe" if os.name == "nt" else ""))
    windows = os.path.join(PHP_DATA, "windows_07.txt")
    rng = random.Random(3301)
    picked, seen = [], set()
    for r in rows:
        score, seed, win, model, mp, sign, atb = r[:7]
        cand, tm = index[int(seed) // 128]
        key = (cand, tm, model, mp, sign, atb)
        if key not in seen:
            seen.add(key)
            picked.append((score, cand, tm, model, mp, sign, atb))
        if len(picked) >= top:
            break
    out_lines = []
    mini = os.path.join(DATA, "kdf_verify_lib.txt")
    for score, cand, tm, model, mult, sign, atb in picked:
        tag, mpi = tm.rsplit(":", 1)
        entries = [cand] + ["".join(rng.choice(string.ascii_lowercase) for _ in range(rng.randrange(5, 12))) for _ in range(controls)]
        with open(mini, "w", newline="\n") as f:
            for k, c in enumerate(entries):
                b = stream(tag, c.encode("utf-8"), 8000)
                v = [x % 29 for x in b] if mpi == "0" else [x % 29 for x in b if x < 232]
                f.write(f"V{k} " + " ".join(map(str, v[:3000])) + "\n")
        env = dict(os.environ, PRNGX_SEQ=mini)
        vals = []
        for k in range(len(entries)):
            r = subprocess.run([exe, "verify", "seq", windows, os.path.join(PHP_DATA, "dict.txt"), str(k * 128), "seg0.7", mult,
                                model, sign, atb], env=env, capture_output=True, text=True, encoding="utf-8")
            vals.append(float(r.stdout.split("\t")[0]) if r.stdout.strip() else 0.0)
        mu, sd = statistics.mean(vals[1:]), statistics.pstdev(vals[1:]) or 1e-9
        flag = "  <-- CHECK" if vals[0] > max(mu + 6 * sd, 0.25) else ""
        out_lines.append(f"  screen {score:>3} {cand[:26]!r:28s} {tag} map {mpi} mult {int(mult) + 1} model {model} sign {sign:>2} atb {atb}: "
                         f"full {vals[0]:.3f} (random strings {mu:.3f} +- {sd:.3f}, z {(vals[0] - mu) / sd:+.1f}){flag}")
        print(out_lines[-1], flush=True)
    return out_lines


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["build", "plant", "run", "verify"])
    ap.add_argument("args", nargs="*")
    ap.add_argument("--out", default=os.path.join(DATA, "kdf_seqs.txt"))
    ap.add_argument("--threads", type=int, default=None)
    a = ap.parse_args()
    if a.action == "build":
        build(a.args[0], a.out)
    elif a.action == "plant":
        plant(*a.args)
    elif a.action == "verify":
        print(f"== {os.path.basename(a.args[0])}")
        verify(a.args[0])
    else:
        build(a.args[0], a.out)
        sweep(a.out, os.path.join(PHP_DATA, "windows_07.txt"), a.out + ".tsv", a.threads)


if __name__ == "__main__":
    sys.exit(main())
