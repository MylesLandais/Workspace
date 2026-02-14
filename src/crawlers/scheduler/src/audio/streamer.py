"""Audio playback utilities."""

from pathlib import Path

import numpy as np


class AudioStreamer:
    """Simple audio playback wrapper."""

    def __init__(self, sample_rate: int = 24000):
        self.sample_rate = sample_rate
        self._sd = None

    def _ensure_sounddevice(self):
        if self._sd is None:
            import sounddevice as sd

            self._sd = sd

    def play(
        self,
        audio: np.ndarray | str | Path,
        sample_rate: int | None = None,
        blocking: bool = True,
    ):
        """Play audio from array or file path.

        Args:
            audio: Audio data as numpy array or path to audio file.
            sample_rate: Sample rate. Uses instance default if None.
            blocking: Wait for playback to complete.
        """
        self._ensure_sounddevice()
        sr = sample_rate or self.sample_rate

        if isinstance(audio, (str, Path)):
            import soundfile as sf

            audio_data, sr = sf.read(audio)
        else:
            audio_data = audio

        self._sd.play(audio_data, sr)
        if blocking:
            self._sd.wait()

    def stop(self):
        """Stop current playback."""
        self._ensure_sounddevice()
        self._sd.stop()
