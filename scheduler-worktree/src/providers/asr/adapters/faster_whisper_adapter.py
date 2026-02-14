"""
Faster-Whisper model adapter for ASR evaluation.
"""

import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from asr_evaluation.core.interfaces import ASRModelAdapter, TranscriptionResult, ModelInfo


class FasterWhisperAdapter(ASRModelAdapter):
    """Adapter for faster-whisper ASR models."""
    
    def __init__(self, model_size: str = "base", device: str = "cpu", compute_type: str = "int8"):
        """
        Initialize faster-whisper adapter.
        
        Args:
            model_size: Model size (tiny, base, small, medium, large)
            device: Device to run on (cpu, cuda)
            compute_type: Compute type (int8, float16, float32)
        """
        self.model_size = model_size
        self.device = device
        self.compute_type = compute_type
        self._model = None
        self._model_info = ModelInfo(
            name="faster-whisper",
            version=model_size,
            model_type="local",
            supports_confidence=True,
            supports_timestamps=True,
            max_audio_length=3600
        )
    
    def _load_model(self):
        """Load the faster-whisper model if not already loaded."""
        if self._model is None:
            try:
                from faster_whisper import WhisperModel
                print(f"Loading faster-whisper model: {self.model_size}")
                self._model = WhisperModel(
                    self.model_size, 
                    device=self.device, 
                    compute_type=self.compute_type
                )
                print(f"✅ Model {self.model_size} loaded successfully")
            except ImportError as e:
                raise ImportError(
                    "faster-whisper not installed. Install with: pip install faster-whisper"
                ) from e
            except Exception as e:
                raise RuntimeError(f"Failed to load faster-whisper model: {e}") from e
    
    def transcribe(self, audio_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe audio file using faster-whisper.
        
        Args:
            audio_path: Path to audio file
            **kwargs: Additional parameters (beam_size, language, etc.)
            
        Returns:
            TranscriptionResult with transcription and metadata
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self._load_model()
        
        start_time = time.time()
        
        # Set default parameters
        beam_size = kwargs.get("beam_size", 5)
        language = kwargs.get("language", None)
        
        try:
            segments, info = self._model.transcribe(
                audio_path,
                beam_size=beam_size,
                language=language
            )
            
            # Collect segments and confidence scores
            text_segments = []
            confidence_scores = []
            
            for segment in segments:
                text_segments.append(segment.text)
                if hasattr(segment, 'avg_logprob'):
                    confidence_scores.append(segment.avg_logprob)
            
            full_text = " ".join(text_segments).strip()
            processing_time = time.time() - start_time
            
            return TranscriptionResult(
                text=full_text,
                confidence_scores=confidence_scores if confidence_scores else None,
                processing_time=processing_time,
                metadata={
                    "model_size": self.model_size,
                    "language": info.language if hasattr(info, 'language') else None,
                    "language_probability": info.language_probability if hasattr(info, 'language_probability') else None,
                    "segments_count": len(text_segments)
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}") from e
    
    def get_model_info(self) -> ModelInfo:
        """Return model information."""
        return self._model_info
    
    def is_available(self) -> bool:
        """Check if faster-whisper is available and model can be loaded."""
        try:
            # Check if faster-whisper is installed
            import faster_whisper
            
            # Try to load the model (this will download if needed)
            self._load_model()
            return True
            
        except ImportError:
            print("❌ faster-whisper not installed")
            return False
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return False