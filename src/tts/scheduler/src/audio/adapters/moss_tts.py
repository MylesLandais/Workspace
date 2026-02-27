"""MOSS-TTS voice cloning backend."""

import time
import gc
import importlib.util
from pathlib import Path
from typing import Any

import numpy as np
import torch
import torchaudio

from ..base import VoiceCloningBackend, VoiceCloneResult, VoicePrompt


class MossTTSBackend(VoiceCloningBackend):
    """Local GPU voice cloning via MOSS-TTS (1.7B Local Transformer)."""

    def __init__(
        self,
        model_size: str = "1.7B",
        device: str = "cuda" if torch.cuda.is_available() else "cpu",
        dtype: str = "bfloat16",
    ):
        self.model_size = model_size
        self.device = device
        self.dtype = dtype
        self._model = None
        self._processor = None

    @property
    def name(self) -> str:
        return f"MOSS-TTS-{self.model_size}"

    @property
    def is_local(self) -> bool:
        return True

    def _get_attn_impl(self):
        if self.device == "cuda" and importlib.util.find_spec("flash_attn"):
            return "flash_attention_2"
        return "sdpa" if self.device == "cuda" else "eager"

    def load(self) -> None:
        if self._model is not None:
            return

        # === CRITICAL FOR STABLE OUTPUT (Fixes garbling) ===
        if self.device == "cuda":
            torch.backends.cuda.enable_cudnn_sdp(False)
            torch.backends.cuda.enable_flash_sdp(True)
            torch.backends.cuda.enable_mem_efficient_sdp(True)
            torch.backends.cuda.enable_math_sdp(True)

        import soundfile as sf
        # Monkeypatch torchaudio.load to use soundfile and ENSURE MONO + 24kHz
        def patched_load(uri, *args, **kwargs):
            data, samplerate = sf.read(uri)
            if len(data.shape) > 1 and data.shape[1] > 1:
                data = np.mean(data, axis=1) # Mono average
            
            tensor = torch.from_numpy(data).to(torch.float32)
            
            # Resample to 24000 if needed (MOSS-TTS standard)
            if samplerate != 24000:
                resampler = torchaudio.transforms.Resample(samplerate, 24000)
                tensor = resampler(tensor.unsqueeze(0)).squeeze(0)
                samplerate = 24000
                
            if len(tensor.shape) == 1:
                tensor = tensor.unsqueeze(0)
            return tensor, samplerate
        torchaudio.load = patched_load

        import transformers
        import transformers.processing_utils
        import transformers.configuration_utils

        # Fix for remote code compatibility
        if not hasattr(transformers.processing_utils, "MODALITY_TO_BASE_CLASS_MAPPING"):
            transformers.processing_utils.MODALITY_TO_BASE_CLASS_MAPPING = {}
        
        pt_config = getattr(transformers, "PretrainedConfig", None) or \
                   getattr(transformers.configuration_utils, "PretrainedConfig", None)
        if pt_config:
            if not hasattr(transformers, "PreTrainedConfig"):
                transformers.PreTrainedConfig = pt_config
            if not hasattr(transformers.configuration_utils, "PreTrainedConfig"):
                transformers.configuration_utils.PreTrainedConfig = pt_config

        # Aggressive patch for MOSS-TTS ProcessorMixin compatibility
        from transformers.processing_utils import ProcessorMixin
        orig_init = ProcessorMixin.__init__
        def patched_init(self, *args, **kwargs):
            if "audio_tokenizer" in kwargs and "feature_extractor" not in kwargs:
                kwargs["feature_extractor"] = kwargs["audio_tokenizer"]
            try:
                orig_init(self, *args, **kwargs)
            except Exception:
                for k, v in kwargs.items(): setattr(self, k, v)
        ProcessorMixin.__init__ = patched_init
        ProcessorMixin.check_argument_for_proper_class = lambda self, arg, val: val

        # Patch for MOSS 8B/1.7B remote code typos
        if not hasattr(transformers, "initialization"):
            class DummyInit:
                def __init__(self): pass
            transformers.initialization = DummyInit()

        from transformers import AutoModel, AutoProcessor

        model_id = "OpenMOSS-Team/MOSS-TTS-Local-Transformer" if self.model_size == "1.7B" else "OpenMOSS-Team/MOSS-TTS"
        print(f"Loading {model_id} on {self.device} ({self.dtype})...")

        torch_dtype = torch.bfloat16 if self.dtype == "bfloat16" and self.device == "cuda" else torch.float32

        self._model = AutoModel.from_pretrained(
            model_id,
            trust_remote_code=True,
            attn_implementation=self._get_attn_impl(),
            torch_dtype=torch_dtype,
        ).to(self.device)
        
        self._processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)
        if hasattr(self._processor, "audio_tokenizer"):
            self._processor.audio_tokenizer = self._processor.audio_tokenizer.to(self.device)
            self._processor.audio_tokenizer.eval()

        if not hasattr(self._processor, "model_config") or self._processor.model_config is None:
            self._processor.model_config = self._model.config
        
        if getattr(self._processor.model_config, "pad_token_id", None) is None:
            self._processor.model_config.pad_token_id = 151643
        
        if hasattr(self._model.config, "language_config") and not hasattr(self._model.config, "num_hidden_layers"):
            self._model.config.num_hidden_layers = self._model.config.language_config.num_hidden_layers

        # GenerationConfig per official MOSS-TTS HuggingFace example
        from transformers import GenerationConfig
        gen_config = GenerationConfig.from_model_config(self._model.config)
        gen_config.do_samples = [True] * self._model.channels
        gen_config.eos_token_id = 151653
        gen_config.use_cache = True
        gen_config.max_new_tokens = 32768

        # Layer 0: language model layer (higher temp, no repetition penalty)
        layer0 = {"temperature": 1.5, "top_p": 1.0, "repetition_penalty": 1.0}
        # Layers 1+: audio codec layers
        layer_rest = {"temperature": 1.0, "top_p": 0.95, "repetition_penalty": 1.1}
        gen_config.layers = [layer0] + [dict(layer_rest) for _ in range(self._model.channels - 1)]
        gen_config.n_vq_for_inference = self._model.channels - 1

        self._gen_config = gen_config
        self._model.generation_config = gen_config
        self._model.eval()

    def unload(self) -> None:
        if self._model is not None:
            del self._model
            del self._processor
            self._model = None
            self._processor = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
            gc.collect()

    def clone_voice(
        self,
        text: str,
        ref_audio: str | Path,
        ref_text: str | None = None,
        language: str = "English",
        **kwargs,
    ) -> VoiceCloneResult:
        self.load()
        start = time.perf_counter()
        
        inputs = self._processor.build_user_message(text=text, reference=[str(ref_audio)])
        batch = self._processor([[inputs]], mode="generation")

        input_ids = batch["input_ids"].to(self.device)
        attention_mask = batch["attention_mask"].to(self.device)

        with torch.inference_mode():
            outputs = self._model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                generation_config=self._gen_config,
            )

        decoded_messages = self._processor.decode(outputs)
        audio_tensor = decoded_messages[0].audio_codes_list[0]
        
        if len(audio_tensor.shape) > 1:
            audio_tensor = audio_tensor.squeeze()
        
        audio_np = audio_tensor.detach().cpu().float().numpy()
        sample_rate = self._processor.model_config.sampling_rate
        elapsed_ms = (time.perf_counter() - start) * 1000

        return VoiceCloneResult(
            audio=audio_np,
            sample_rate=sample_rate,
            model_name=self.name,
            generation_time_ms=elapsed_ms,
        )

    def create_voice_prompt(self, ref_audio: str | Path, ref_text: str | None = None) -> VoicePrompt:
        return VoicePrompt(
            embedding=str(ref_audio),
            ref_audio_path=str(ref_audio),
            ref_text=ref_text,
            backend=self.name,
        )

    def generate_with_prompt(self, texts: list[str], voice_prompt: VoicePrompt, languages: list[str] | None = None) -> list[VoiceCloneResult]:
        self.load()
        return [self.clone_voice(text, voice_prompt.ref_audio_path) for text in texts]
