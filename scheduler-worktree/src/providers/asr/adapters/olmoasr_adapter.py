"""
OLMoASR model adapter for ASR evaluation.
"""

import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import torch
import torchaudio

from asr_evaluation.core.interfaces import ASRModelAdapter, TranscriptionResult, ModelInfo


class OLMoASRAdapter(ASRModelAdapter):
    """Adapter for OLMoASR models from HuggingFace."""

    def __init__(self, model_name: str = "fixie-ai/ultravox-v0_3", device: str = "auto"):
        """
        Initialize OLMoASR adapter.

        Args:
            model_name: HuggingFace model name for OLMoASR
            device: Device to run on (auto, cpu, cuda)
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self._model = None
        self._processor = None
        self._model_info = ModelInfo(
            name="olmoasr",
            version=model_name.split("/")[-1],
            model_type="local",
            supports_confidence=False,  # Will update based on model capabilities
            supports_timestamps=False,
            max_audio_length=3600
        )

    def _get_device(self, device: str) -> str:
        """Determine the best device to use."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device

    def _load_model(self):
        """Load the OLMoASR model and processor if not already loaded."""
        if self._model is None:
            try:
                from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq

                print(f"Loading OLMoASR model: {self.model_name}")

                # Load processor and model
                self._processor = AutoProcessor.from_pretrained(self.model_name)
                self._model = AutoModelForSpeechSeq2Seq.from_pretrained(
                    self.model_name,
                    torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                    low_cpu_mem_usage=True,
                    use_safetensors=True
                )

                # Move model to device
                self._model.to(self.device)

                print(f"SUCCESS: OLMoASR model {self.model_name} loaded successfully on {self.device}")

            except ImportError as e:
                raise ImportError(
                    "transformers not installed. Install with: pip install transformers torch torchaudio"
                ) from e
            except Exception as e:
                raise RuntimeError(f"Failed to load OLMoASR model: {e}") from e

    def _load_audio(self, audio_path: str) -> torch.Tensor:
        """Load and preprocess audio file."""
        try:
            # Load audio file
            waveform, sample_rate = torchaudio.load(audio_path)

            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)

            # Resample to 16kHz if needed (common for ASR models)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)

            return waveform.squeeze()

        except Exception as e:
            raise RuntimeError(f"Failed to load audio file {audio_path}: {e}") from e

    def transcribe(self, audio_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe audio file using OLMoASR.

        Args:
            audio_path: Path to audio file
            **kwargs: Additional parameters

        Returns:
            TranscriptionResult with transcription and metadata
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        self._load_model()

        start_time = time.time()

        try:
            # Load and preprocess audio
            audio = self._load_audio(audio_path)

            # Process audio with the processor (for Whisper models)
            # Convert numpy array to proper format
            audio_array = audio.numpy() if hasattr(audio, 'numpy') else audio

            inputs = self._processor(
                audio_array,
                sampling_rate=16000,
                return_tensors="pt"
            )

            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}

            # Generate transcription with better parameters
            with torch.no_grad():
                generated_ids = self._model.generate(
                    **inputs,
                    language="en",  # Force English
                    task="transcribe",  # Transcribe instead of translate
                    max_length=448,  # Allow longer transcriptions
                    num_beams=5,  # Better quality
                    do_sample=False  # Deterministic output
                )

            # Decode the transcription
            transcription = self._processor.batch_decode(
                generated_ids,
                skip_special_tokens=True
            )[0]

            processing_time = time.time() - start_time

            return TranscriptionResult(
                text=transcription.strip(),
                confidence_scores=None,  # OLMoASR doesn't provide confidence scores
                processing_time=processing_time,
                metadata={
                    "model_name": self.model_name,
                    "device": self.device,
                    "audio_duration": len(audio) / 16000,  # Duration in seconds
                    "sample_rate": 16000
                }
            )

        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}") from e

    def get_model_info(self) -> ModelInfo:
        """Return model information."""
        return self._model_info

    def is_available(self) -> bool:
        """Check if OLMoASR model is available and can be loaded."""
        try:
            # Check if required packages are installed
            import transformers
            import torch
            import torchaudio

            # Try to load the model (this will download if needed)
            self._load_model()
            return True

        except ImportError as e:
            print(f"ERROR: Required packages not installed: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Model loading failed: {e}")
            return False
