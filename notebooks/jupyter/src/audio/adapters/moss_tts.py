"""MOSS-TTS voice cloning backend.

Requires transformers>=5.0.0 and trust_remote_code=True.
The per-layer GenerationConfig is MOSS-TTS specific and must be built after
model load (channel count comes from model.channels).
"""

import gc
import time
from pathlib import Path

import numpy as np
import torch
import torchaudio
import soundfile as sf

from ..base import TTSResult, VoiceCloningBackend, VoicePrompt

# Keep audio_tokenizer on CPU to avoid OOM on 8 GB cards.
_AUDIO_TOKENIZER_CPU = True

# MOSS-TTS standard sample rate for reference audio preprocessing.
_MOSS_SAMPLE_RATE = 24000


def _load_audio_24k_mono(path: str) -> tuple[torch.Tensor, int]:
    """Load audio, convert to mono, resample to 24 kHz.

    MOSS-TTS requires 24 kHz mono input for its reference encoder.
    Uses soundfile to avoid torchaudio backend issues on NixOS.
    """
    data, sr = sf.read(path)
    if data.ndim > 1:
        data = data.mean(axis=1)
    tensor = torch.from_numpy(data).float()
    if sr != _MOSS_SAMPLE_RATE:
        tensor = torchaudio.functional.resample(tensor, sr, _MOSS_SAMPLE_RATE)
    return tensor.unsqueeze(0), _MOSS_SAMPLE_RATE


class MossTTSBackend(VoiceCloningBackend):
    """Local GPU voice cloning via MOSS-TTS (OpenMOSS-Team/MOSS-TTS-Local-Transformer).

    Uses bfloat16 + SDPA (FlashAttention-2 auto-detected if installed).
    The audio_tokenizer is kept on CPU to fit within 8 GB VRAM on RTX 3070.

    Requires transformers>=5.0.0 (pinned in pyproject.toml).
    """

    MODEL_ID = "OpenMOSS-Team/MOSS-TTS-Local-Transformer"

    def __init__(
        self,
        model_id: str = MODEL_ID,
        use_flash_attn: bool = False,
    ):
        self.model_id = model_id
        self.use_flash_attn = use_flash_attn
        self._model = None
        self._processor = None
        self._gen_config = None

    @property
    def name(self) -> str:
        short = self.model_id.split("/")[-1]
        attn = "flash" if self.use_flash_attn else "sdpa"
        return f"MOSS-TTS-{short}-{attn}"

    @property
    def is_local(self) -> bool:
        return True

    def _attn_impl(self) -> str:
        if self.use_flash_attn:
            try:
                import flash_attn  # noqa: F401
                return "flash_attention_2"
            except ImportError:
                pass
        return "sdpa"

    def load(self) -> None:
        if self._model is not None:
            return

        # Disable cuDNN SDP — prevents garbled output with MOSS-TTS decoder.
        torch.backends.cuda.enable_cudnn_sdp(False)
        torch.backends.cuda.enable_flash_sdp(True)
        torch.backends.cuda.enable_mem_efficient_sdp(True)
        torch.backends.cuda.enable_math_sdp(True)

        # Patch torchaudio.load so MOSS remote code gets 24 kHz mono tensors.
        torchaudio.load = _load_audio_24k_mono

        from transformers import AutoModel, AutoProcessor, GenerationConfig

        print(f"Loading {self.model_id}...")
        self._processor = AutoProcessor.from_pretrained(
            self.model_id, trust_remote_code=True
        )
        self._model = AutoModel.from_pretrained(
            self.model_id,
            trust_remote_code=True,
            dtype=torch.bfloat16,
            attn_implementation=self._attn_impl(),
        ).to("cuda")
        self._model.eval()

        if _AUDIO_TOKENIZER_CPU and hasattr(self._processor, "audio_tokenizer"):
            self._processor.audio_tokenizer = (
                self._processor.audio_tokenizer.to("cpu").eval()
            )

        if not hasattr(self._processor, "model_config") or self._processor.model_config is None:
            self._processor.model_config = self._model.config

        # DynamicCache in transformers 5.x calls decoder_config.num_hidden_layers.
        # MOSS-TTS splits its config into language_config + audio sub-configs;
        # only language_config has num_hidden_layers. Propagate it to the top-level
        # config and to any sub-configs that are missing it.
        lang_cfg = getattr(self._model.config, "language_config", None)
        if lang_cfg is not None and hasattr(lang_cfg, "num_hidden_layers"):
            n = lang_cfg.num_hidden_layers
            if not hasattr(self._model.config, "num_hidden_layers"):
                self._model.config.num_hidden_layers = n
            for attr in vars(self._model.config).values():
                if hasattr(attr, "__class__") and "Config" in type(attr).__name__:
                    if not hasattr(attr, "num_hidden_layers"):
                        attr.num_hidden_layers = n

        # Build per-layer GenerationConfig (MOSS-TTS specific).
        # Layer 0 is the language model head; layers 1+ are audio codec residual layers.
        gen_config = GenerationConfig.from_model_config(self._model.config)
        gen_config.do_samples = [True] * self._model.channels
        gen_config.eos_token_id = 151653
        gen_config.use_cache = True
        gen_config.max_new_tokens = 32768

        layer0 = {"temperature": 1.5, "top_p": 1.0, "repetition_penalty": 1.0}
        layer_rest = {"temperature": 1.0, "top_p": 0.95, "repetition_penalty": 1.1}
        gen_config.layers = [layer0] + [dict(layer_rest) for _ in range(self._model.channels - 1)]
        gen_config.n_vq_for_inference = self._model.channels - 1

        self._gen_config = gen_config
        self._model.generation_config = gen_config
        print(f"Loaded. Channels: {self._model.channels}")

    def unload(self) -> None:
        if self._model is not None:
            del self._model
            del self._processor
            del self._gen_config
            self._model = None
            self._processor = None
            self._gen_config = None
            torch.cuda.empty_cache()
            gc.collect()

    def synthesize(self, text: str, **kwargs) -> TTSResult:
        """Zero-shot synthesis without a reference audio."""
        return self.clone_voice(text, ref_audio=None)

    def clone_voice(
        self,
        text: str,
        ref_audio: str | Path | None,
        ref_text: str | None = None,
        language: str = "English",
    ) -> TTSResult:
        self.load()
        start = time.perf_counter()

        reference = [str(ref_audio)] if ref_audio is not None else None
        inputs = self._processor.build_user_message(text=text, reference=reference)
        batch = self._processor([[inputs]], mode="generation")

        input_ids = batch["input_ids"].to("cuda")
        attention_mask = batch["attention_mask"].to("cuda")

        with torch.inference_mode():
            outputs = self._model.generate(
                input_ids=input_ids,
                attention_mask=attention_mask,
                generation_config=self._gen_config,
            )

        decoded = self._processor.decode(outputs)
        audio_tensor = decoded[0].audio_codes_list[0]
        if audio_tensor.ndim > 1:
            audio_tensor = audio_tensor.squeeze()

        audio_np = audio_tensor.detach().cpu().float().numpy()
        sr = self._processor.model_config.sampling_rate
        elapsed_ms = (time.perf_counter() - start) * 1000

        return TTSResult(
            audio=audio_np,
            sample_rate=sr,
            model_name=self.name,
            generation_time_ms=elapsed_ms,
        )
