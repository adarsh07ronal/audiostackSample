import pyaudio
import time
from hal import AudioHAL
from mixer import mix3
from router import AudioRouter

# Number of frames processed per cycle (buffer size)
CHUNK = 1024

# Initialize audio sources (HAL layer)
music = AudioHAL("streams/music_16.wav")
nav = AudioHAL("streams/nav_16.wav")
call = AudioHAL("streams/call_16.wav")

# Initialize routing logic (policy layer)
router = AudioRouter()

# Create PyAudio instance (audio system interface)
p = pyaudio.PyAudio()

# Get audio format parameters from source
channels, width, rate = music.get_params()

# Open audio output stream (similar to ALSA PCM open)
stream = p.open(format=p.get_format_from_width(width),
                channels=channels,
                rate=rate,
                output=True,
                frames_per_buffer=CHUNK)

print("Starting Mini Automotive Audio Stack...")

try:
    # Main real-time audio loop
    for i in range(1000):

        m = music.read(CHUNK)
        n = nav.read(CHUNK)
        c = call.read(CHUNK)

        router.update_mode(i)

        wm, wn, wc = router.get_weights()

        out = mix3(m, n, c, wm, wn, wc)

        # 🔒 Hard enforce correct size (keep this)
        EXPECTED = CHUNK * channels * width
        if len(out) != EXPECTED:
            if len(out) < EXPECTED:
                out += b'\x00' * (EXPECTED - len(out))
            else:
                out = out[:EXPECTED]

        stream.write(out, exception_on_underflow=False)

        if i % 50 == 0:
            print(f"Mode: {router.mode}")

except KeyboardInterrupt:
    print("\nStopping audio...")

finally:
    # Clean up audio resources
    stream.stop_stream()
    stream.close()
    p.terminate()
    print("Clean exit.")