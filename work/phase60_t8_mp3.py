"""Phase 60 T8 helper: strip an MP3 file to its frame payload bytes. Removes the ID3v2 tag at the head, the ID3v1 tag ('TAG', 128 bytes) at the tail, and in every MPEG audio frame the 4-byte header
(and the 2-byte CRC when the protection bit says it is present); keeps side information and main data. Frames are found by walking the header-given frame lengths from the first sync word; a lost
sync is re-found by scanning for the next valid header (the bytes skipped are reported)."""
import numpy as np

BR = {1: {1: [0, 32, 64, 96, 128, 160, 192, 224, 256, 288, 320, 352, 384, 416, 448], 2: [0, 32, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320, 384], 3: [0, 32, 40, 48, 56, 64, 80, 96, 112, 128, 160, 192, 224, 256, 320]},
      2: {1: [0, 32, 48, 56, 64, 80, 96, 112, 128, 144, 160, 176, 192, 224, 256], 2: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160], 3: [0, 8, 16, 24, 32, 40, 48, 56, 64, 80, 96, 112, 128, 144, 160]}}
SR = {3: [44100, 48000, 32000], 2: [22050, 24000, 16000], 0: [11025, 12000, 8000]}


def header(b, i):
    """-> (frame length, header size incl. CRC) or None"""
    if i + 4 > len(b) or b[i] != 0xFF or (b[i + 1] & 0xE0) != 0xE0:
        return None
    ver = (b[i + 1] >> 3) & 3          # 3 = MPEG1, 2 = MPEG2, 0 = MPEG2.5
    lay = (b[i + 1] >> 1) & 3          # 1 = layer III, 2 = II, 3 = I (bit pattern)
    if ver == 1 or lay == 0:
        return None
    layer = 4 - lay
    bri, sri = b[i + 2] >> 4, (b[i + 2] >> 2) & 3
    if bri in (0, 15) or sri == 3:
        return None
    mp = 1 if ver == 3 else 2
    kbps = BR[mp][layer][bri]
    sr = SR[ver][sri]
    pad = (b[i + 2] >> 1) & 1
    if layer == 1:
        n = (12 * kbps * 1000 // sr + pad) * 4
    elif layer == 3 and mp == 2:
        n = 72 * kbps * 1000 // sr + pad
    else:
        n = 144 * kbps * 1000 // sr + pad
    return n, 4 + (0 if (b[i + 1] & 1) else 2)


def strip(data):
    b = bytes(data)
    i = 0
    if b[:3] == b'ID3':
        i = 10 + ((b[6] << 21) | (b[7] << 14) | (b[8] << 7) | b[9])
    end = len(b) - 128 if b[-128:-125] == b'TAG' else len(b)
    out, frames, skipped = [], 0, 0
    while i < end - 4:
        h = header(b, i)
        if h is None or i + h[0] > end:
            j = i + 1
            while j < end - 4 and header(b, j) is None:
                j += 1
            skipped += j - i
            i = j
            continue
        n, hs = h
        out.append(b[i + hs:i + n]); frames += 1; i += n
    return np.frombuffer(b''.join(out), np.uint8), dict(frames=frames, skipped=skipped, total=len(b), payload=sum(len(x) for x in out))
