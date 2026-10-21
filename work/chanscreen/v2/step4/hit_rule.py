"""Phase 24 hit rule for the edge arc (PRE-REGISTERED here, before any LP2 ciphertext is scored by it).

A cell is (stream, sign, channel, kind, offset). A TIER-1 EDGE HIT needs ALL of:
  1. S_guard(edge cell) >= T (T300 = 29.799 for the n300 scan; a family-wise T must count 3 kinds x 8 passes = 24 passes per window, i.e. ln(3) = +1.1 nats over the
     four-channel base threshold if the cell count triples);
  2. it reproduces in a fresh recomputation (the engine shows rare transient faults, see phase24 log);
  3. EDGE vs BASE: S_edge(cell) - max(S_base over the same stream, sign, all four base channels, offsets within +-3 of the cell) >= MARGIN_NATS (20.0). Measured
     on plants: events present -> edge minus base >= +50 (hold) to > +200 nats (other channels); no events ('none' plants) -> edge minus base about -30. A hit that the base engine
     scores about as well does not support the keyless-insertion / extra-advance reading, only the base hypothesis;
  4. key-sequence aliases are collapsed: hits of the same stream and sign whose key windows (the key values the cell would read, n * channel_factor + 16 values) are equal
     are ONE hit, and the reported cell is the best member. 
Report for every plant or hit: 'true cell within 3 nats of the global best' (band score >= winner score - 3), not 'winner is the true offset'.
"""
MARGIN_NATS = 20.0
EXT = {'hold': 1, 'spend': 1, 'skip5': 6, 'coin': 3}


def collapse_hits(hits, keys, n):
    """hits: list of dict(stream, sign, channel, offset, score); keys: {stream: key list}. Returns one best hit per (stream, sign, channel, key window)."""
    best = {}
    for h in hits:
        ext = EXT[h['channel']] * n + 16
        win = tuple(keys[h['stream']][h['offset']:h['offset'] + ext])
        k = (h['stream'], h['sign'], h['channel'], win)
        if k not in best or h['score'] > best[k]['score']:
            best[k] = h
    return list(best.values())


def beats_base(s_edge, s_base_band, margin=MARGIN_NATS):
    return s_edge - s_base_band >= margin
