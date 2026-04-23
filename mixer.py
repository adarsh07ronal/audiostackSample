import numpy as np


## “This module converts PCM byte streams into numerical arrays, 
# performs weighted mixing in float domain to avoid overflow, 
# normalizes total gain, and clips the result before converting back to PCM for playback.”


# Number of frames processed per cycle
# This defines buffer size and latency (similar to ALSA period size)
CHUNK = 1024


def to_array(data, channels=1, sampwidth=2):
    """
    Convert raw PCM byte data into a fixed-size NumPy array.

    Args:
        data (bytes): Raw audio data from HAL
        channels (int): Number of audio channels (1=mono, 2=stereo)
        sampwidth (int): Sample width in bytes (2=16-bit, 4=32-bit)

    Returns:
        np.ndarray: Fixed-size array of audio samples
    """

    # If no data received, return silence buffer
    if not data:
        return np.zeros(CHUNK * channels, dtype=np.int16)

    # Determine data type based on sample width
    # 2 bytes → 16-bit audio, 4 bytes → 32-bit audio
    dtype = np.int16 if sampwidth == 2 else np.int32

    # Convert raw bytes into numeric samples
    arr = np.frombuffer(data, dtype=dtype)

    # Expected number of samples (frames × channels)
    expected = CHUNK * channels

    # If we received fewer samples than expected (e.g., end of file)
    if len(arr) < expected:
        # Create a zero-filled buffer (silence)
        padded = np.zeros(expected, dtype=arr.dtype)

        # Copy available data into buffer
        padded[:len(arr)] = arr

        arr = padded
    else:
        # Trim extra samples to match expected size
        arr = arr[:expected]

    return arr


def mix3(m, n, c, wm, wn, wc, channels=1, sampwidth=2):
    """
    Mix three audio streams using weighted sum.

    Args:
        m (bytes): Music stream
        n (bytes): Navigation stream
        c (bytes): Call stream
        wm, wn, wc (float): Weights (volume levels)
        channels (int): Number of channels
        sampwidth (int): Sample width in bytes

    Returns:
        bytes: Mixed PCM audio data ready for playback
    """

    # Convert byte streams to NumPy arrays and move to float domain
    # Float prevents overflow during multiplication and addition
    a1 = to_array(m, channels, sampwidth).astype(np.float32)
    a2 = to_array(n, channels, sampwidth).astype(np.float32)
    a3 = to_array(c, channels, sampwidth).astype(np.float32)

    # Perform weighted mixing (core DSP operation)
    # Each stream is scaled by its respective weight
    out = (a1 * wm + a2 * wn + a3 * wc)

    # Calculate total gain applied
    total = wm + wn + wc

    # Normalize if total gain exceeds safe level
    # Prevents distortion due to excessive amplitude
    if total > 1.0:
        out = out / total

    # Clip output to int16 range to avoid overflow distortion
    out = np.clip(out, -32768, 32767)

    # Convert back to int16 PCM format and return as bytes
    return out.astype(np.int16).tobytes()