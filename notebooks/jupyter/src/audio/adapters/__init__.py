"""Voice cloning and TTS backend adapters.

Adding a new model of the week:
  1. Create adapters/<model_name>.py implementing TTSBackend or VoiceCloningBackend.
  2. Add a lazy import entry below.
  3. Run: python -m src.audio.run_eval --backend <model_name> --golden
"""

__all__ = [
    "MossTTSBackend",
    "Qwen3TTSBackend",
    "VibeVoiceBackend",
]


def __getattr__(name: str):
    """Lazy import adapters to avoid loading heavy dependencies at import time."""
    if name == "MossTTSBackend":
        from .moss_tts import MossTTSBackend

        return MossTTSBackend
    if name == "Qwen3TTSBackend":
        from .qwen_tts import Qwen3TTSBackend

        return Qwen3TTSBackend
    if name == "VibeVoiceBackend":
        from .vibe_voice import VibeVoiceBackend

        return VibeVoiceBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
