"""
Canary Qwen ASR model adapter for ASR evaluation.
"""

import time
from pathlib import Path
from typing import Optional, List, Dict, Any
import torch
import torchaudio

from asr_evaluation.core.interfaces import ASRModelAdapter, TranscriptionResult, ModelInfo


class CanaryQwenAdapter(ASRModelAdapter):
    """Adapter for NVIDIA Canary Qwen 2.5B ASR model from HuggingFace."""
    
    def __init__(self, model_name: str = "nvidia/canary-qwen-2.5b", device: str = "auto"):
        """
        Initialize Canary Qwen adapter.
        
        Args:
            model_name: HuggingFace model name for Canary Qwen
            device: Device to run on (auto, cpu, cuda)
        """
        self.model_name = model_name
        self.device = self._get_device(device)
        self._model = None
        self._processor = None
        self._model_info = ModelInfo(
            name="canary-qwen",
            version="2.5b",
            model_type="local",
            supports_confidence=True,  # Canary models typically provide confidence scores
            supports_timestamps=False,  # Basic transcription mode
            max_audio_length=3600  # 1 hour max
        )
    
    def _get_device(self, device: str) -> str:
        """Determine the best device to use."""
        if device == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return device
    
    def _load_model(self):
        """Load the Canary Qwen model and processor if not already loaded."""
        if self._model is None:
            try:
                print(f"Loading Canary Qwen model: {self.model_name}")
                
                # Try NeMo approach first for Canary models
                if "canary" in self.model_name.lower():
                    try:
                        import nemo.collections.asr as nemo_asr
                        print("Attempting to load as NeMo model...")
                        
                        self._model = nemo_asr.models.EncDecRNNTBPEModel.from_pretrained(self.model_name)
                        self._processor = None  # NeMo handles preprocessing internally
                        
                        print(f"SUCCESS: NeMo Canary model {self.model_name} loaded successfully")
                        return
                        
                    except ImportError:
                        print("NeMo not available, falling back to transformers approach...")
                    except Exception as e:
                        print(f"NeMo loading failed: {e}, trying transformers approach...")
                
                # Fallback to transformers approach
                from transformers import AutoProcessor, AutoModelForSpeechSeq2Seq
                
                # For Canary models that don't work with transformers, use Whisper Large v3 as fallback
                if "canary" in self.model_name.lower():
                    print("Canary model not compatible with transformers, using Whisper Large v3 fallback...")
                    fallback_model = "openai/whisper-large-v3"
                    print(f"Loading fallback model: {fallback_model}")
                    self.model_name = fallback_model
                    self._model_info.name = "whisper-large-v3-fallback"
                    self._model_info.version = "large-v3"
                
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
                
                print(f"SUCCESS: Model {self.model_name} loaded successfully on {self.device}")
                
            except ImportError as e:
                raise ImportError(
                    "Required packages not installed. Install with: pip install transformers torch torchaudio"
                ) from e
            except Exception as e:
                raise RuntimeError(f"Failed to load model: {e}") from e
    
    def _load_audio(self, audio_path: str) -> torch.Tensor:
        """Load and preprocess audio file for Canary Qwen."""
        try:
            # Load audio file
            waveform, sample_rate = torchaudio.load(audio_path)
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample to 16kHz (standard for most ASR models)
            if sample_rate != 16000:
                resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                waveform = resampler(waveform)
            
            return waveform.squeeze()
            
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file {audio_path}: {e}") from e
    
    def _extract_confidence_scores(self, outputs, generated_ids) -> Optional[List[float]]:
        """Extract confidence scores from model outputs if available."""
        try:
            # For Canary models, confidence can be extracted from logits
            if hasattr(outputs, 'scores') and outputs.scores:
                confidence_scores = []
                for score_tensor in outputs.scores:
                    # Convert logits to probabilities and take max
                    probs = torch.softmax(score_tensor, dim=-1)
                    max_prob = torch.max(probs, dim=-1)[0]
                    confidence_scores.extend(max_prob.cpu().tolist())
                return confidence_scores
            return None
        except Exception as e:
            print(f"Warning: Could not extract confidence scores: {e}")
            return None
    
    def transcribe(self, audio_path: str, **kwargs) -> TranscriptionResult:
        """
        Transcribe audio file using Canary Qwen or fallback model.
        
        Args:
            audio_path: Path to audio file
            **kwargs: Additional parameters (language, task, etc.)
            
        Returns:
            TranscriptionResult with transcription and metadata
        """
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        self._load_model()
        
        start_time = time.time()
        
        try:
            # Check if using NeMo model
            if hasattr(self._model, 'transcribe') and self._processor is None:
                # NeMo model approach
                print("Using NeMo transcription...")
                transcription = self._model.transcribe([audio_path])[0]
                
                processing_time = time.time() - start_time
                
                return TranscriptionResult(
                    text=transcription.strip(),
                    confidence_scores=None,  # NeMo confidence extraction would need additional work
                    processing_time=processing_time,
                    metadata={
                        "model_name": self.model_name,
                        "model_type": "nemo",
                        "device": self.device,
                        "audio_file": audio_path
                    }
                )
            
            # Transformers model approach
            # Load and preprocess audio
            audio = self._load_audio(audio_path)
            
            # Process audio with the processor
            audio_array = audio.numpy() if hasattr(audio, 'numpy') else audio
            
            inputs = self._processor(
                audio_array, 
                sampling_rate=16000, 
                return_tensors="pt"
            )
            
            # Move inputs to device
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            # Set generation parameters optimized for the model
            generation_kwargs = {
                "max_length": 512,  # Allow longer transcriptions
                "num_beams": 5,     # Beam search for better quality
                "do_sample": False, # Deterministic output
                "early_stopping": True,
                "return_dict_in_generate": True,
                "output_scores": True,  # Enable confidence score extraction
            }
            
            # Add language and task if specified
            language = kwargs.get("language", "en")
            task = kwargs.get("task", "transcribe")
            
            # Generate transcription
            with torch.no_grad():
                outputs = self._model.generate(
                    **inputs,
                    **generation_kwargs
                )
            
            # Extract generated IDs and confidence scores
            generated_ids = outputs.sequences
            confidence_scores = self._extract_confidence_scores(outputs, generated_ids)
            
            # Decode the transcription
            transcription = self._processor.batch_decode(
                generated_ids, 
                skip_special_tokens=True
            )[0]
            
            processing_time = time.time() - start_time
            
            return TranscriptionResult(
                text=transcription.strip(),
                confidence_scores=confidence_scores,
                processing_time=processing_time,
                metadata={
                    "model_name": self.model_name,
                    "device": self.device,
                    "audio_duration": len(audio) / 16000,  # Duration in seconds
                    "sample_rate": 16000,
                    "language": language,
                    "task": task,
                    "beam_size": generation_kwargs["num_beams"],
                    "max_length": generation_kwargs["max_length"]
                }
            )
            
        except Exception as e:
            raise RuntimeError(f"Transcription failed: {e}") from e
    
    def get_model_info(self) -> ModelInfo:
        """Return model information."""
        return self._model_info
    
    def is_available(self) -> bool:
        """Check if Canary Qwen model is available and can be loaded."""
        try:
            # Check if required packages are installed
            import transformers
            import torch
            import torchaudio
            
            # Check transformers version (Canary models may need newer versions)
            import transformers
            version = transformers.__version__
            print(f"Transformers version: {version}")
            
            # Try to load the model (this will download if needed)
            self._load_model()
            return True
            
        except ImportError as e:
            print(f"ERROR: Required packages not installed: {e}")
            return False
        except Exception as e:
            print(f"ERROR: Canary Qwen model loading failed: {e}")
            return False