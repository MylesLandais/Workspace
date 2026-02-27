"""Voice cloning backend adapters."""

from typing import Type

from ..base import VoiceCloningBackend

__all__ = [
    "MossTTSBackend",
    "Qwen3TTSBackend",
    "VibeVoiceBackend",
    "get_adapter",
    "list_adapters",
]

_ADAPTER_REGISTRY = {
    "MossTTSBackend": ".moss_tts",
    "Qwen3TTSBackend": ".qwen_tts",
    "VibeVoiceBackend": ".vibe_voice",
}


def get_adapter(name: str) -> Type[VoiceCloningBackend]:
    """Lazy load and return a backend adapter class by name."""
    if module_path := _ADAPTER_REGISTRY.get(name):
        import importlib

        # Import relative to this package (e.g. .moss_tts)
        module = importlib.import_module(module_path, package=__package__)
        return getattr(module, name)
    
    available = ", ".join(list_adapters())
    raise ValueError(f"Unknown adapter: {name}. Available: {available}")


def list_adapters() -> list[str]:
    """List available backend adapter names."""
    return list(_ADAPTER_REGISTRY.keys())


def __getattr__(name: str):
    """Lazy import adapters via registry to avoid loading heavy dependencies."""
    # Check if the requested attribute is a known adapter
    if name in _ADAPTER_REGISTRY:
        return get_adapter(name)
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
