import alsaaudio
import time
from hal import AudioHAL
from mixer import mix3
from router import AudioRouter

CHUNK = 8192

# Load audio streams
music = AudioHAL("streams/music_16.wav")
nav = AudioHAL("streams/nav_16.wav")
call = AudioHAL("streams/call_16.wav")

router = AudioRouter()

# Get audio parameters
channels, width, rate = music.get_params()

# Create ALSA PCM device
pcm = alsaaudio.PCM(
    type=alsaaudio.PCM_PLAYBACK,
    device='default'   # IMPORTANT: use plughw for auto conversion
)

pcm.setchannels(channels)
pcm.setrate(rate)
pcm.setformat(alsaaudio.PCM_FORMAT_S16_LE)
pcm.setperiodsize(CHUNK)
pcm.setperiods(4)

print("Starting ALSA Audio Stack...")

try:
    for i in range(2000):

        # Read audio chunks
        m = music.read(CHUNK)
        n = nav.read(CHUNK)
        c = call.read(CHUNK)

        # Routing decision
        router.update_mode(i)
        wm, wn, wc = router.get_weights()

        # Mix audio
        out = mix3(m, n, c, wm, wn, wc)

        # Write to ALSA
        while pcm.write(out) == 0:
            pass

        # Debug print (not too frequent)
        if i % 500 == 0:
            print(f"Mode: {router.mode}")
            print(len(out))

        # Real-time pacing
        time.sleep(CHUNK / rate * 1.5)

except KeyboardInterrupt:
    print("\nStopping audio...")

print("Playback finished.")