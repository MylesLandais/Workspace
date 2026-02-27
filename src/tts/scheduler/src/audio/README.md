# Voice Cloning Framework

Local voice cloning using Qwen3-TTS on NixOS with RTX 3070 (8GB VRAM).

## Quick Start

```bash
# Must use steam-run for library compatibility on NixOS
steam-run bash -c '
cd /home/warby/Workspace/jupyter
source .venv/bin/activate
export PYTHONPATH=src:$PYTHONPATH
export PATH=/nix/store/gv9wa277hjwc1rdxbw26bxg3qzchx645-sox-unstable-2021-05-09/bin:$PATH
export HF_HOME=/home/warby/Workspace/jupyter/.hf_cache

python -c "
from audio.adapters.qwen_tts import Qwen3TTSBackend
import soundfile as sf

backend = Qwen3TTSBackend(use_nf4=False, use_flash_attn=False)
backend.load()

wavs, sr = backend._model.generate_voice_clone(
    text=\"Hello, this is a test.\",
    language=\"English\",
    ref_audio=\"comfyui_projects/reference_audio/maya.wav\",
    x_vector_only_mode=True,
)

sf.write(\"output.wav\", wavs[0], sr)
"
'
```

## Why steam-run?

NixOS uses isolated library paths. The Python venv packages (torch, etc.) are linked against standard FHS libraries (libstdc++, etc.) that don't exist at expected paths on NixOS. `steam-run` provides an FHS-compatible environment.

**Do not try to fix this with:**
- LD_LIBRARY_PATH hacks in shell.nix (breaks other things)
- nix-shell python packages (missing ML deps)
- Direct venv activation without steam-run (library errors)

## Reference Audio Requirements

| Voice | File | Duration | Status |
|-------|------|----------|--------|
| Maya | maya.wav | 10s | Works |
| Selena | selena.wav | 8s | Works |
| Emma | Emma_8s.wav | 8s | Works (trimmed from 28s) |
| Kirk | kirk.wav | 9s | Works |
| Lexie | lexie_8s.wav | 8s | Works (trimmed from 11s) |
| Larry | larry.wav | 10s | Works |

**VRAM constraints:**
- Reference audio > 10s may cause OOM
- Use `x_vector_only_mode=True` (no transcript needed)
- Chunk long scripts into ~200 char segments

## Generation Parameters

```python
wavs, sr = backend._model.generate_voice_clone(
    text="Your text here",
    language="English",
    ref_audio="path/to/reference.wav",
    x_vector_only_mode=True,  # Required without transcript
)
```

## Chunked Generation for Long Scripts

```python
import numpy as np
import torch

chunks = ["First paragraph.", "Second paragraph.", ...]
all_audio = []

for chunk in chunks:
    torch.cuda.empty_cache()
    wavs, sr = backend._model.generate_voice_clone(
        text=chunk,
        language="English",
        ref_audio="reference.wav",
        x_vector_only_mode=True,
    )
    all_audio.append(wavs[0])

# Join with pauses
pause = np.zeros(int(sr * 0.5))
combined = []
for i, audio in enumerate(all_audio):
    combined.append(audio)
    if i < len(all_audio) - 1:
        combined.append(pause)

final = np.concatenate(combined)
sf.write("output.wav", final, sr)
```

## Performance (RTX 3070 8GB, bf16)

| Metric | Value |
|--------|-------|
| RTF | ~1.25 (slower than real-time) |
| VRAM | ~4.3GB model + activations |
| Max ref audio | ~10s before OOM |

## Known Issues

1. **Python 3.13 + bitsandbytes**: Quantization (NF4) fails due to deepcopy bug. Use `use_nf4=False`.

2. **flash-attn**: Build fails on NixOS. Use `use_flash_attn=False`.

3. **sox not found**: Add sox to PATH: `/nix/store/gv9wa277hjwc1rdxbw26bxg3qzchx645-sox-unstable-2021-05-09/bin`

4. **HF cache permissions**: Use local cache: `export HF_HOME=/home/warby/Workspace/jupyter/.hf_cache`
