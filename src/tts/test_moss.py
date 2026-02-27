"""Minimal MOSS-TTS test: generate one sentence, save to WAV."""

import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

# Ensure root workspace is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.tts.adapters import get_adapter

WORKSPACE = Path(__file__).resolve().parent.parent.parent
REF_AUDIO = WORKSPACE / "data" / "inputs" / "voices" / "larry.wav"
OUTPUT_DIR = WORKSPACE / "data" / "outputs" / "tts"


def main():
    timestamp = time.strftime("%Y%m%d%H%M")
    OUTPUT_FILE = OUTPUT_DIR / f"{timestamp}-moss-larry-vaporeon.wav"
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    backend = get_adapter("moss-tts")
    print(f"Loading {backend.name}...")
    t0 = time.perf_counter()
    backend.load()
    load_time = time.perf_counter() - t0
    print(f"Model loaded in {load_time:.1f}s")

    text = (
        "Hey guys, did you know that in terms of water-based Pokemon, "
        "Vaporeon is the most cool? It's the smoothest, the most huggable, "
        "and literally the best water type to bring to the beach. "
        "What other Pokemon can learn both Surf and Ice Beam while looking that good? None."
    )
    print(f"Generating: {text!r}")

    result = backend.clone_voice(text=text, ref_audio=str(REF_AUDIO))
    print(f"Generation: {result.generation_time_ms:.0f}ms")
    print(f"Audio shape: {result.audio.shape}, sample rate: {result.sample_rate}")

    sf.write(str(OUTPUT_FILE), result.audio, result.sample_rate)
    print(f"Saved to {OUTPUT_FILE}")

    backend.unload()


if __name__ == "__main__":
    main()
