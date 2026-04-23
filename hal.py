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

        Args:
            chunk (int): Number of frames to read

        Returns:
            bytes: PCM audio data of fixed size
        """

        # Read raw audio frames (PCM data)
        data = self.wf.readframes(chunk)

        # Calculate expected number of bytes for this chunk
        # Formula:
        # frames × channels × bytes_per_sample
        expected_bytes = chunk * self.channels * self.sampwidth

        # If we reach end of file and data is smaller than expected
        # we loop the file to maintain continuous playback
        while len(data) < expected_bytes:
            self.wf.rewind()  # Go back to beginning of file

            # Read more frames to fill the buffer
            more = self.wf.readframes(chunk)

            # Append additional data
            data += more

        # Ensure returned data is exactly the expected size
        return data[:expected_bytes]


    def get_params(self):
        """
        Return audio format parameters.

        Returns:
            tuple: (channels, sample_width, sample_rate)
        """
        return self.channels, self.sampwidth, self.rate