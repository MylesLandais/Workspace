"""Qwen3-TTS voice cloning backend."""

import time
from pathlib import Path

import numpy as np

from ..base import VoiceCloningBackend, VoiceCloneResult, VoicePrompt


class Qwen3TTSBackend(VoiceCloningBackend):
    """Local GPU voice cloning via Qwen3-TTS with NF4 quantization."""

    def __init__(
        self,
        model_size: str = "1.7B",
        use_nf4: bool = True,
        use_flash_attn: bool = True,
        device: str | None = None,
    ):
        import torch
        self.model_size = model_size
        self.use_nf4 = use_nf4
        self.use_flash_attn = use_flash_attn
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self._model = None

    @property
    def name(self) -> str:
        quant = "NF4" if self.use_nf4 else "bf16"
        return f"Qwen3-TTS-{self.model_size}-{quant}"

    @property
    def is_local(self) -> bool:
        return True

    def load(self) -> None:
        if self._model is not None:
            return

        import torch
        from qwen_tts import Qwen3TTSModel

        attn_impl = "flash_attention_2" if self.use_flash_attn else "sdpa"

        model_id = f"Qwen/Qwen3-TTS-12Hz-{self.model_size}-Base"

        if self.use_nf4:
            # Try pre-quantized model first, fall back to runtime quantization
            try:
                from transformers import BitsAndBytesConfig

                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                )
                self._model = Qwen3TTSModel.from_pretrained(
                    model_id,
                    quantization_config=quantization_config,
                    device_map=self.device,
                    attn_implementation=attn_impl,
                )
            except Exception as e:
                # Python 3.13 deepcopy bug with bitsandbytes or metadata issues
                print(f"Quantization failed ({type(e).__name__}: {e}), loading in bf16...")
                self._model = Qwen3TTSModel.from_pretrained(
                    model_id,
                    torch_dtype=torch.bfloat16,
                    device_map=self.device,
                    attn_implementation=attn_impl,
                )
        else:
            # Full precision bf16 (requires ~4GB VRAM for 1.7B)
            self._model = Qwen3TTSModel.from_pretrained(
                model_id,
                torch_dtype=torch.bfloat16,
                device_map=self.device,
                attn_implementation=attn_impl,
            )

    def unload(self) -> None:
        if self._model is not None:
            import torch

            del self._model
            self._model = None
            torch.cuda.empty_cache()

    def clone_voice(
        self,
        text: str,
        ref_audio: str | Path,
        ref_text: str | None = None,
        language: str = "English",
        x_vector_only_mode: bool = False,
    ) -> VoiceCloneResult:
        self.load()
        start = time.perf_counter()

        wavs, sr = self._model.generate_voice_clone(
            text=text,
            language=language,
            ref_audio=str(ref_audio),
            ref_text=ref_text,
            x_vector_only_mode=x_vector_only_mode,
        )

        elapsed_ms = (time.perf_counter() - start) * 1000

        return VoiceCloneResult(
            audio=np.array(wavs[0]),
            sample_rate=sr,
            model_name=self.name,
            generation_time_ms=elapsed_ms,
        )

    def create_voice_prompt(
        self,
        ref_audio: str | Path,
        ref_text: str | None = None,
    ) -> VoicePrompt:
        self.load()
        embedding = self._model.create_voice_clone_prompt(
            ref_audio=str(ref_audio),
            ref_text=ref_text,
        )
        return VoicePrompt(
            embedding=embedding,
            ref_audio_path=str(ref_audio),
            ref_text=ref_text,
            backend=self.name,
        )

    def generate_with_prompt(
        self,
        texts: list[str],
        voice_prompt: VoicePrompt,
        languages: list[str] | None = None,
    ) -> list[VoiceCloneResult]:
        self.load()
        if languages is None:
            languages = ["English"] * len(texts)

        start = time.perf_counter()
        wavs, sr = self._model.generate_voice_clone(
            text=texts,
            language=languages,
            voice_clone_prompt=voice_prompt.embedding,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        per_sample_ms = elapsed_ms / len(texts)

        return [
            VoiceCloneResult(
                audio=np.array(wav),
                sample_rate=sr,
                model_name=self.name,
                generation_time_ms=per_sample_ms,
            )
            for wav in wavs
        ]
