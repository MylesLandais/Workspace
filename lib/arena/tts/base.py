"""Abstract base class for voice cloning backends."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import numpy as np


@dataclass
class VoiceCloneResult:
    """Standardized output from any voice cloning backend."""

    audio: np.ndarray
    sample_rate: int
    model_name: str
    generation_time_ms: float
    metadata: dict = field(default_factory=dict)


@dataclass
class VoicePrompt:
    """Cached voice embedding for reuse across generations."""

    embedding: Any  # Backend-specific format
    ref_audio_path: str
    ref_text: str | None
    backend: str


class VoiceCloningBackend(ABC):
    """Abstract interface for voice cloning backends."""

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
    def clone_voice(
        self,
        text: str,
        ref_audio: str | Path,
        ref_text: str | None = None,
        language: str = "English",
    ) -> VoiceCloneResult:
        """Generate speech in cloned voice."""

    @abstractmethod
    def create_voice_prompt(
        self,
        ref_audio: str | Path,
        ref_text: str | None = None,
    ) -> VoicePrompt:
        """Create reusable voice embedding."""

    @abstractmethod
    def generate_with_prompt(
        self,
        texts: list[str],
        voice_prompt: VoicePrompt,
        languages: list[str] | None = None,
    ) -> list[VoiceCloneResult]:
        """Batch generate with cached voice prompt."""
