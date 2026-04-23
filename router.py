#“I implemented an audio routing module that simulates automotive audio policies,
#  where different audio sources are prioritized dynamically.
#  The router outputs mixing weights to enforce behaviors like 
# ducking and full override based on the active mode.”


class AudioRouter:
    """
    AudioRouter is responsible for deciding which audio stream
    should be audible at any given time.

    It simulates automotive audio behavior:
    - Music plays by default
    - Navigation interrupts with ducking
    - Call has highest priority (overrides everything)
    """

    def __init__(self):
        # Current active mode of the system
        # Possible values: "music", "nav", "call"
        self.mode = "music"


    def update_mode(self, i):
        """
        Update routing mode based on time/frame index.

        Args:
            i (int): Current loop/frame counter

        This simulates real-world events:
        - Navigation prompt occurs for a time window
        - Call occurs for a later time window
        """

        # Navigation event window
        if 100 < i < 300:
            self.mode = "nav"

        # Call event window (higher priority than navigation)
        elif 400 < i < 700:
            self.mode = "call"

        # Default state → music playback
        else:
            self.mode = "music"


    def get_weights(self):
        """
        Return mixing weights for each audio stream.

        Returns:
            tuple: (music_weight, nav_weight, call_weight)

        These weights control:
        - Volume of each stream
        - Priority between streams
        """

        # Call has highest priority → only call is audible
        if self.mode == "call":
            return (0.0, 0.0, 1.0)

        # Navigation plays over music (music is reduced/ducked)
        elif self.mode == "nav":
            return (0.3, 1.0, 0.0)

        # Default → only music plays
        else:
            return (1.0, 0.0, 0.0)