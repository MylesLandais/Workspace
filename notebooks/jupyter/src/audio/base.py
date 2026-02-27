"""Abstract base classes for TTS backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class TTSResult:
    """Standardized output from any TTS backend."""

    audio: np.ndarray
    sample_rate: int
    model_name: str
    generation_time_ms: float
    metadata: dict = field(default_factory=dict)


# Alias so existing code referencing VoiceCloneResult keeps working.
VoiceCloneResult = TTSResult


@dataclass
class VoicePrompt:
    """Cached voice embedding for reuse across generations."""

    embedding: Any  # Backend-specific format
    ref_audio_path: str
    ref_text: str | None
    backend: str


class TTSBackend(ABC):
    """Minimal interface that every TTS model must implement.

    Sufficient for pure zero-shot models that generate speech from text alone.
    Extend VoiceCloningBackend for models that require a reference audio.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable backend name."""

    @property
    @abstractmethod
    def is_local(self) -> bool:
        """True if runs on local GPU, False if cloud/remote."""

    @abstractmethod
    def load(self) -> None:
        """Load model into memory."""

    @abstractmethod
    def unload(self) -> None:
        """Release model from memory."""

    @abstractmethod
    def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Generate speech for text.

        kwargs are model-specific (language, speaker_id, etc.).
        This is the primary entry point for the evaluation harness.
        """


class VoiceCloningBackend(TTSBackend):
    """TTSBackend extended with reference-audio voice conditioning.

    Implement clone_voice() at minimum. Override synthesize() if the model
    also supports zero-shot synthesis without a reference. Override
    create_voice_prompt() and generate_with_prompt() if the model supports
    prompt caching (avoids re-encoding the reference on each call).
    """

    @abstractmethod
    def clone_voice(
        self,
        text: str,
        ref_audio: str | Path | None,
        ref_text: str | None = None,
        language: str = "English",
    ) -> TTSResult:
        """Generate speech conditioned on reference audio."""

    def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Default: delegate to clone_voice with no reference (zero-shot).

        Override this if the model requires a reference to produce any output.
        """
        return self.clone_voice(text, ref_audio=None, **kwargs)

    def create_voice_prompt(
        self,
        ref_audio: str | Path,
        ref_text: str | None = None,
    ) -> VoicePrompt:
        """Create reusable voice embedding.

        Override if the model supports caching the reference encoding.
        """
        raise NotImplementedError(
            f"{self.name} does not support cached voice prompts. "
            "Use clone_voice() per request."
        )

    def generate_with_prompt(
        self,
        texts: list[str],
        voice_prompt: VoicePrompt,
        languages: list[str] | None = None,
    ) -> list[TTSResult]:
        """Batch generate with a cached voice prompt.

        Override if the model supports prompt caching.
        """
        raise NotImplementedError(
            f"{self.name} does not support cached voice prompts. "
            "Use clone_voice() per request."
        )
