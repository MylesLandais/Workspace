"""
Core interfaces and abstract base classes for the ASR evaluation system.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from datetime import datetime


@dataclass
class TranscriptionResult:
    """Result of a transcription operation."""
    text: str
    confidence_scores: Optional[List[float]] = None
    processing_time: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ModelInfo:
    """Information about an ASR model."""
    name: str
    version: str
    model_type: str  # "local", "cloud", "ollama", "vllm"
    supports_confidence: bool = False
    supports_timestamps: bool = False
    max_audio_length: Optional[int] = None  # seconds


class ASRModelAdapter(ABC):
    """Abstract base class for all ASR model adapters."""
    
    @abstractmethod
    def transcribe(self, audio_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe audio file and return structured result.
        
        Args:
            audio_path: Path to audio file
            **kwargs: Additional model-specific parameters
            
        Returns:
            TranscriptionResult with text and metadata
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> ModelInfo:
        """Return model metadata and capabilities."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if model is available and ready for use."""
        pass


@dataclass
class EvaluationResult:
    """Result of evaluating a model on a single audio file."""
    experiment_id: str
    model_name: str
    model_version: str
    audio_file: str
    reference_text: str
    predicted_text: str
    
    # Metrics
    wer: float
    cer: float
    processing_time: float
    
    # Metadata
    audio_duration: float
    timestamp: datetime
    confidence_scores: Optional[List[float]] = None
    custom_metrics: Optional[Dict[str, float]] = None