#“I implemented an audio HAL that reads PCM frames from a source and guarantees 
#fixed-size buffers by looping and padding at end-of-stream, 
#ensuring continuous playback and stable downstream processing.”

import wave

class AudioHAL:
    """
    AudioHAL (Hardware Abstraction Layer)

    This class simulates the behavior of an audio hardware interface.
    It reads PCM audio data from a WAV file and provides it as a
    continuous stream to the audio pipeline.

    In real systems, this would interface with:
    - ALSA (Linux)
    - Audio HAL (Android)
    - Audio drivers / DSP hardware
    """

    def __init__(self, file):
        # Open WAV file in read-binary mode
        self.wf = wave.open(file, 'rb')

        # Extract audio parameters from file
        self.channels = self.wf.getnchannels()     # 1 = mono, 2 = stereo
        self.sampwidth = self.wf.getsampwidth()    # bytes per sample (2 = 16-bit)
        self.rate = self.wf.getframerate()         # sample rate (e.g., 44100 Hz)


    def read(self, chunk):
        """
        Read a fixed number of audio frames from the file.

        Ensures:
        - Always returns EXACT buffer size required by ALSA
        - Loops audio seamlessly when EOF is reached
        - Avoids infinite loops / partial reads

        Args:
            chunk (int): Number of frames to read

        Returns:
            bytes: PCM audio data (exact size)
        """

        # 🔢 Calculate expected buffer size
        # frames × channels × bytes_per_sample
        expected_bytes = chunk * self.channels * self.sampwidth

        # 📥 Read initial chunk
        data = self.wf.readframes(chunk)

        # 🧠 If we didn't get enough data (EOF case)
        if len(data) < expected_bytes:

            # 🔁 Loop file to fill remaining buffer
            remaining = expected_bytes - len(data)

            # Safety counter (avoid infinite loop)
            max_loops = 5
            loops = 0

            while remaining > 0 and loops < max_loops:
                self.wf.rewind()  # go to start

                more = self.wf.readframes(chunk)

                if not more:
                    break  # safety: no more data

                data += more
                remaining = expected_bytes - len(data)
                loops += 1

        # 🛠 Final safety: enforce exact size
        if len(data) < expected_bytes:
            # pad with silence (important!)
            data += b'\x00' * (expected_bytes - len(data))

        # ✂️ Trim if oversized (rare but safe)
        return data[:expected_bytes]


    def get_params(self):
        """
        Return audio format parameters.

        Returns:
            tuple: (channels, sample_width, sample_rate)
        """
        return self.channels, self.sampwidth, self.rate