"""
NVIDIA Parakeet TDT model adapter for ASR evaluation.

Parakeet TDT is a state-of-the-art streaming ASR model from NVIDIA
optimized for real-time and low-latency applications.
"""

import time
from pathlib import Path
from typing import Optional, List, Dict, Any

from src.providers.asr.core.interfaces import ASRModelAdapter, TranscriptionResult, ModelInfo


class ParakeetTDTAdapter(ASRModelAdapter):
    """Adapter for NVIDIA Parakeet TDT ASR models."""

    def __init__(
        self,
        model_name: str = "nvidia/parakeet-tdt-0.6b-v2",
        device: str = "auto",
        streaming: bool = True,
        low_latency: bool = True
    ):
        """
        Initialize Parakeet TDT adapter.

        Args:
            model_name: HuggingFace model ID
            device: Device to run on (auto, cpu, cuda)
            streaming: Enable streaming mode for real-time processing
            low_latency: Optimize for low latency (reduces quality slightly)
        """
        self.model_name = model_name
        self.streaming = streaming
        self.low_latency = low_latency
        self._model = None
        self._processor = None
        self._pipe = None

        # Auto-detect device
        if device == "auto":
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        else:
            self.device = device

        self._model_info = ModelInfo(
            name="parakeet-tdt",
            version="0.6b-v2",
            model_type="local",
            supports_confidence=True,
            supports_timestamps=True,
            max_audio_length=3600
        )

    def _load_model(self):
        """Load Parakeet TDT model if not already loaded."""
        if self._model is None:
            try:
                from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor, pipeline
                import torch

                print(f"Loading Parakeet TDT model: {self.model_name}")

                # Load processor and model
                self._processor = AutoProcessor.from_pretrained(self.model_name)
                self._model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32
                )
                self._model.to(self.device)

                # Create pipeline for easier inference
                self._pipe = pipeline(
                    "automatic-speech-recognition",
                    model=self._model,
                    tokenizer=self._processor.tokenizer,
                    feature_extractor=self._processor.feature_extractor,
                    device=self.device,
                    return_timestamps=True,
                    chunk_length_s=15 if self.streaming else 30
                )

                print(f"✅ Parakeet TDT model loaded on {self.device}")

            except ImportError as e:
                raise ImportError(
                    "transformers not installed. Install with: pip install transformers"
                ) from e
            except Exception as e:
                raise RuntimeError(f"Failed to load Parakeet TDT model: {e}") from e

    def transcribe(self, audio_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe audio file using Parakeet TDT.

        Args:
            audio_path: Path to audio file
            **kwargs: Additional parameters (language, temperature, etc.)

        Returns:
            TranscriptionResult with transcription and metadata
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        start_time = time.time()

        # Set default parameters
        language = kwargs.get("language", "english")
        temperature = kwargs.get("temperature", 0.0)
        chunk_length = kwargs.get("chunk_length_s", 15 if self.streaming else 30)

        try:
            # Transcribe using pipeline
            result = self._pipe(
                audio_path,
                chunk_length_s=chunk_length,
                return_timestamps=True,
                generate_kwargs={
                    "task": "transcribe",
                    "language": language,
                    "temperature": temperature,
                }
            )

            # Process result
            text = result["text"].strip()
            confidence_scores = []
            segments_info = []

            if "chunks" in result:
                for chunk in result["chunks"]:
                    text_segment = chunk["text"].strip()
                    if text_segment:
                        segments_info.append({
                            "start": chunk["timestamp"][0] or 0,
                            "end": chunk["timestamp"][1] or chunk_length,
                            "text": text_segment
                        })
                        # Extract confidence if available
                        if "score" in chunk:
                            confidence_scores.append(chunk["score"])

            processing_time = time.time() - start_time

            return TranscriptionResult(
                text=text,
                confidence_scores=confidence_scores if confidence_scores else None,
                processing_time=processing_time,
                metadata={
                    "model_name": self.model_name,
                    "device": self.device,
                    "streaming": self.streaming,
                    "low_latency": self.low_latency,
                    "language": language,
                    "temperature": temperature,
                    "segments_count": len(segments_info),
                    "segments": segments_info
                }
            )

        except Exception as e:
            raise RuntimeError(f"Parakeet TDT transcription failed: {e}") from e

    def get_model_info(self) -> ModelInfo:
        """Return model information."""
        return self._model_info

    def is_available(self) -> bool:
        """Check if Parakeet TDT is available and model can be loaded."""
        try:
            # Check if transformers is installed
            from transformers import AutoModelForSpeechSeq2Seq, AutoProcessor

            # Try to load model (this will download if needed)
            self._load_model()
            return True

        except ImportError:
            print("❌ transformers not installed")
            return False
        except Exception as e:
            print(f"❌ Model loading failed: {e}")
            return False
