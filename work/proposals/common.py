"""Shared helpers for the proposal gates under work/proposals/.

Self-contained: standard library + the repository's own work/lp.py. Each test folder's
run.py imports this module after the run script has placed this folder on sys.path.

Conventions (CLAUDE.md):
- every claim is a planted-control gate: the plant is made by the plain encryptor and the
  recovery by the decoder; they share no code path;
- every positive has a null (random settings under identical code);
- nothing in LP2 is solved; these tests make no claim about LP2.
"""
import math
import os
import random
import sys

_REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(_REPO, "work"))
import lp  # noqa: E402

N = lp.N
LATIN = lp.LATIN     # latin spellings in Gematria Primus order
PRIME = lp.PRIME     # GP primes in Gematria Primus order
DIGRAPHS = ["ING", "TH", "EO", "IA", "EA", "AE", "OE"]

# ---------------------------------------------------------------- corpus

# CORPUS_A trains the bigram table; CORPUS_B is held out and used as plant plaintext.
CORPUS_A = (
    "The master spoke to the student about truth and the long road toward wisdom. A voice "
    "inside your head is only the echo of the self. Question all things, discover what you "
    "know, and follow it without fear. The pilgrim who seeks the end of all struggle must "
    "first lose the illusions of the world. Consumption and preservation are the two errors "
    "that bind the mind. To emerge like the instar, tunneling to the surface, one must shed "
    "the old circumference. Words carry numbers and numbers carry direction. Trust what you "
    "can test, believe only what you know to be true. The primes are sacred, the totient "
    "function is sacred, all things should be encrypted. We shape ourselves by the questions "
    "we refuse to answer. A man came to study with a master who asked who he was. "
    "Morning light fell on the river and the town below began to stir. Farmers walked the "
    "muddy road with baskets of grain on their backs. The market opened and the smell of "
    "bread drifted between the houses. Children ran past the well, shouting names to one "
    "another, and a dog followed them with a stick in its mouth. An old woman sat by her "
    "door and watched the day begin. She remembered when the square was small and the "
    "streets were made of dirt, when every face was known and every door was open. "
    "The mountain stood behind the valley with snow on its highest ridge. Rivers cut deep "
    "lines into the stone and carried cold water down to the fields. Wind moved through the "
    "pine trees and made a sound like distant voices. A bird crossed the sky and vanished "
    "behind the clouds. The weather changed slowly here, as if the seasons could not agree "
    "on what to bring. Winter held the ground for months and spring arrived in a single "
    "week. Summer was short and hot, and autumn painted the hills in red and gold. "
    "They built the tower over seven summers and the bell could be heard for miles. Stone "
    "by stone the walls rose until the roof was set against the sky. The workers sang while "
    "they lifted the beams and their voices carried over the fields. When the last stone was "
    "placed the whole town gathered in the square. The bell rang once and the sound stayed "
    "in the air for a long time. People said it would guard the valley from harm. "
    "She wrote letters every week and sent them down the river by boat. The boatman knew "
    "her by name and always stopped at the wooden dock below the mill. Her letters spoke of "
    "small things, of gardens and weather and the price of cloth, but the words between the "
    "lines told a longer story. He read them twice and kept each one in a box under his bed. "
    "The war had taken many men from the valley and not all of them returned. Those who came "
    "back spoke little of what they had seen. They worked the fields as before but their "
    "eyes looked past the horizon. The children of the town grew up with stories of fathers "
    "who were brave and distant, like figures in an old song. "
    "Science moves by small steps and honest doubt. A theory stands until a better one "
    "explains what the first could not. The stars are far and their light is old, yet we "
    "measure them with patience and glass. Number is the language in which the world is "
    "written, and those who read it find order beneath the noise. Chance also has its laws, "
    "and what looks like luck is often structure wearing a mask. The patient student learns "
    "to tell the difference. Every measurement carries error and every instrument has a "
    "limit, but the average of many careful trials approaches the truth. "
    "The city never slept and its lights washed the darkness from the sky. Trains ran under "
    "the streets and carried thousands to work before dawn. Above ground the offices stood "
    "in rows of glass and steel. In the park a small group gathered to play music on the "
    "grass. Their notes mixed with the traffic and the shouting of vendors selling fruit. "
    "A runner circled the lake and counted her steps in silence. On a bench an old man read "
    "the newspaper and shook his head at the news. The day moved fast and the night came "
    "suddenly, as it does in places where the light never really goes away."
)

CORPUS_B = (
    "He gave his name, his work, his kind, but none of these were who he is. Then you are "
    "welcome, said the master. Do four unreasonable things each day. The voice that says you "
    "have no voice is the I. And the students were enlightened. The road has no end but the "
    "one you make. Test the knowledge, find your truth, experience your death. Do not edit "
    "or change this book or the message contained within. Either the words or their numbers, "
    "for all is sacred. Some wisdom is plain and some is hidden. We lose our primality by "
    "consuming what we do not need and by preserving what we should destroy. Adherence is "
    "death and the circumference is the only prison. Journey deep within and you will arrive "
    "outside. Like the instar, it is only through going within that we may emerge. "
    "The sea was calm the morning they set out, and the sails hung loose for the first hour. "
    "By noon a wind rose from the west and the ship leaned into the waves. The captain kept "
    "his hand on the wheel and his eyes on the clouds that gathered in the north. The crew "
    "moved along the deck with ropes and buckets, steady on their feet, speaking in low "
    "voices. A storm came on fast and the sky turned the color of iron. Rain struck the deck "
    "like stones and the lanterns went out one by one. The mate shouted orders above the "
    "noise and every hand held to something solid. When morning came the sea was flat and "
    "the sun rose over a coast nobody on board could name. They dropped anchor in a quiet "
    "bay and went ashore with fresh water and questions. The island had no roads and no "
    "marks of any recent visitor, only birds and a small spring under the trees. "
    "Learning a language is a long game of memory and courage. The first sentences come "
    "slowly and wrong, full of borrowed words and broken grammar. The ear adjusts before "
    "the tongue does, and one day a phrase arrives whole and correct without effort. After "
    "that the door is open and the country behind it grows wider every week. Its stories, "
    "its jokes, its songs, its arguments all become yours. You begin to dream in the new "
    "language and wake surprised. The old one never leaves, it simply shares the room. "
    "Markets clear when price and supply meet, but people are not always as rational as the "
    "models claim. Fear moves faster than data and habit slower than both. A bank can fall "
    "in a day on nothing but rumor, while a good policy takes years to show its worth. The "
    "wise investor studies history, keeps a margin of safety, and never borrows what she "
    "cannot repay in a bad season. Cycles turn and the patient are rewarded for sitting "
    "still when others run. What looks like profit is often the price of risk wearing a "
    "different suit. Trust in averages, but plan for the tail. "
    "She practiced the violin for an hour before breakfast and again after dark. Her "
    "teacher said the bow must breathe, that a phrase is a sentence and not a series of "
    "notes. For years the instrument felt like a stranger in her hands, a box of wood that "
    "resisted every intention. Then one winter night, alone in the empty hall, the sound "
    "came out warm and whole, and she understood what the teacher had meant. Music is time "
    "made visible, and practice is the slow work of learning to see it. She played the same "
    "line again and again until the motion became thought and the thought became sound."
)


def to_runes(text):
    """English text -> GP rune indices, digraph-aware (TH, ING, EA, IA, OE, AE, EO)."""
    t = text.upper()
    out, i = [], 0
    while i < len(t):
        hit = None
        for d in DIGRAPHS:
            if t.startswith(d, i):
                hit = d
                break
        if hit:
            out.append(LATIN.index(hit))
            i += len(hit)
        elif t[i] in LATIN:
            out.append(LATIN.index(t[i]))
            i += 1
        else:
            i += 1
    return out


def words_of(text):
    """[(rune list, is_clause_end)] for the words of an English text ('.!' ends a clause)."""
    words = []
    cur = []
    for ch in text.upper():
        if ch in ".!":
            if cur:
                words.append((cur, True))
                cur = []
        elif ch in " ,;\n":
            if cur:
                words.append((cur, False))
                cur = []
        elif ch in LATIN:
            cur.append(ch)
    if cur:
        words.append((cur, False))
    return [(to_runes("".join(raw)), end) for raw, end in words]


# ---------------------------------------------------------------- statistics

def cap_words(words, max_runes=600):
    """Truncate a word list to at most max_runes total runes (keeps gates fast)."""
    out, n = [], 0
    for w in words:
        if n + len(w[0]) > max_runes:
            break
        out.append(w)
        n += len(w[0])
    return out


def ioc(letters):
    """Index of coincidence of a list of rune indices (English runes about 1.8, flat 1.0)."""
    n = len(letters)
    if n < 2:
        return 1.0
    f = [0] * N
    for x in letters:
        f[x] += 1
    return N * sum(v * (v - 1) for v in f) / (n * (n - 1))


_BG = None
_CNT = None
_TOT = None


def bigram_counts():
    """Rune-bigram counts from CORPUS_A, add-1 smoothed. Cached."""
    global _CNT, _TOT
    if _CNT is None:
        seq = to_runes(CORPUS_A)
        cnt = [[1.0] * N for _ in range(N)]
        for a, b in zip(seq, seq[1:]):
            cnt[a][b] += 1.0
        _CNT = cnt
        _TOT = [sum(row) for row in cnt]
    return _CNT, _TOT


def bigram_table():
    """Rune-bigram log-probability table from CORPUS_A, add-1 smoothed. Cached."""
    global _BG
    if _BG is None:
        cnt, tot = bigram_counts()
        _BG = [[math.log(cnt[a][b] / tot[a]) for b in range(N)] for a in range(N)]
    return _BG


def markov(n, rng):
    """n runes of corpus-consistent pseudo-English (for long synthetic sections)."""
    cnt, tot = bigram_counts()
    out = [rng.randrange(N)]
    for _ in range(n - 1):
        r = rng.random() * tot[out[-1]]
        acc = 0
        for b in range(N):
            acc += cnt[out[-1]][b]
            if r < acc:
                out.append(b)
                break
    return out


# ---------------------------------------------------------------- cipher

def encrypt_anti(plain, key, rng=None, coin=0.81):
    """c_i = (p_i + key[j]) mod N with the anti-repeat rule: on a would-be adjacent
    repeat the encryptor draws the next key value (skip). key is indexable, cycled."""
    rng = rng or random.Random(0)
    c, j, prev = [], 0, -1
    for p in plain:
        x = (p + key[j % len(key)]) % N
        j += 1
        if x == prev and rng.random() < coin:
            x = (p + key[j % len(key)]) % N
            j += 1
        c.append(x)
        prev = x
    return c


def decode_beam(c, key, beam=64, bg=None):
    """Skip-tolerant Viterbi over the key pointer, bigram-scored. A redraw (skip) is
    allowed only where key and ciphertext are consistent with it (the kscreen skip
    check): key[j+1] - key[j] == c_i - c_{i-1}. Returns the best plaintext rune list."""
    bg = bg if bg is not None else bigram_table()
    L = len(key)
    states = {(0, -1): (0.0, [])}
    prev = -1
    for x in c:
        new = {}
        for (ptr, last), (lpv, letters) in states.items():
            # keep: the encryptor used key[ptr]
            p0 = (x - key[ptr % L]) % N
            s = lpv + (bg[last][p0] if last >= 0 else math.log(1.0 / N))
            k2 = (ptr + 1, p0)
            if k2 not in new or s > new[k2][0]:
                new[k2] = (s, letters + [p0])
            # skip: the encryptor redrew key[ptr+1] after a would-be doublet
            if prev >= 0 and (key[(ptr + 1) % L] - key[ptr % L]) % N == (x - prev) % N:
                p1 = (x - key[(ptr + 1) % L]) % N
                s = lpv + (bg[last][p1] if last >= 0 else math.log(1.0 / N)) + math.log(0.81)
                k2 = (ptr + 2, p1)
                if k2 not in new or s > new[k2][0]:
                    new[k2] = (s, letters + [p1])
        states = dict(sorted(new.items(), key=lambda kv: kv[1][0], reverse=True)[:beam])
        prev = x
    return max(states.values(), key=lambda v: v[0])[1]


def totient_key(n):
    """An End's stream: key_i = phi(prime_i) = prime_i - 1, mod N."""
    return [(p - 1) % N for p in _primes(n)]


_PRIMES = None


def _primes(n):
    """First n primes by sieve."""
    global _PRIMES
    if _PRIMES is not None and len(_PRIMES) >= n:
        return _PRIMES[:n]
    m = max(2000, int(n * (math.log(n) + math.log(math.log(n))) + 10))
    s = bytearray([1]) * (m + 1)
    s[0:2] = b"\x00\x00"
    for i in range(2, int(m ** 0.5) + 1):
        if s[i]:
            s[i * i::i] = bytearray(len(s[i * i::i]))
    _PRIMES = [i for i in range(m + 1) if s[i]]
    return _PRIMES[:n]


def print_verdict(name, ok, detail=""):
    print("[%s] GATE: %s  %s" % (name, "PASS" if ok else "FAIL", detail))
    return 0 if ok else 1
