# TTS Development & Testing

## Quick Start

We use a specific Nix shell configuration to handle Python C-extension dependencies (numpy, torch) that require `libstdc++` and `zlib`.

To run the TTS comparison tests (MOSS-TTS vs Qwen3-TTS):

```bash
cd src/tts
chmod +x run_tests.sh
./run_tests.sh
```

You can also target a specific backend:

```bash
./run_tests.sh moss
./run_tests.sh qwen
```

## Environment Setup

If setting up for the first time:

1.  Enter the TTS directory: `cd src/tts`
2.  Create virtual environment: `uv venv .venv`
3.  Activate: `source .venv/bin/activate`
4.  Install dependencies:
    ```bash
    uv pip install torch torchaudio transformers soundfile accelerate bitsandbytes numpy huggingface-hub
    uv pip install git+https://github.com/QwenLM/Qwen3-TTS.git
    ```

## Directory Structure

*   `run_tests.sh`: Helper script to run python scripts with correct LD_LIBRARY_PATH.
*   `compare_tts.py`: Main entry point for generating audio.
*   `scheduler/`: Legacy path (being refactored to `lib/tts/`).
