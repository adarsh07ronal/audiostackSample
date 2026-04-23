import numpy as np


## “This module converts PCM byte streams into numerical arrays, 
# performs weighted mixing in float domain to avoid overflow, 
# normalizes total gain, and clips the result before converting back to PCM for playback.”


# Number of frames processed per cycle
# This defines buffer size and latency (similar to ALSA period size)
CHUNK = 1024


def to_array(data, channels=1, sampwidth=2):
    dtype = np.int16 if sampwidth == 2 else np.int32
    return np.frombuffer(data, dtype=dtype)



def mix3(m, n, c, wm, wn, wc, channels=1, sampwidth=2):

    a1 = to_array(m, channels, sampwidth).astype(np.float32)
    a2 = to_array(n, channels, sampwidth).astype(np.float32)
    a3 = to_array(c, channels, sampwidth).astype(np.float32)

    # 🔥 Use MIN LENGTH (critical fix)
    min_len = min(len(a1), len(a2), len(a3))

    a1 = a1[:min_len]
    a2 = a2[:min_len]
    a3 = a3[:min_len]

    out = (a1 * wm + a2 * wn + a3 * wc)

    total = wm + wn + wc
    if total > 1.0:
        out = out / total

    out = np.clip(out, -32768, 32767)

    return out.astype(np.int16).tobytes()