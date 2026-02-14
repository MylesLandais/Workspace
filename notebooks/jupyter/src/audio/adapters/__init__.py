"""Voice cloning backend adapters."""

__all__ = [
    "Qwen3TTSBackend",
    "VibeVoiceBackend",
]


def __getattr__(name: str):
    """Lazy import adapters to avoid loading heavy dependencies."""
    if name == "Qwen3TTSBackend":
        from .qwen_tts import Qwen3TTSBackend

        return Qwen3TTSBackend
    elif name == "VibeVoiceBackend":
        from .vibe_voice import VibeVoiceBackend

        return VibeVoiceBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
