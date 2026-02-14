"""Voice cloning evaluation framework."""

from .base import VoiceCloningBackend, VoiceCloneResult, VoicePrompt

__all__ = [
    "VoiceCloningBackend",
    "VoiceCloneResult",
    "VoicePrompt",
    "VoiceCloneEvaluator",
    "EvaluationResult",
    "AudioStreamer",
]


def __getattr__(name: str):
    """Lazy import for optional dependencies."""
    if name == "VoiceCloneEvaluator":
        from .evaluation import VoiceCloneEvaluator

        return VoiceCloneEvaluator
    elif name == "EvaluationResult":
        from .evaluation import EvaluationResult

        return EvaluationResult
    elif name == "AudioStreamer":
        from .streamer import AudioStreamer

        return AudioStreamer
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
