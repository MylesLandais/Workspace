#!/usr/bin/env python3
"""Simple script to run TTS on a text file using Qwen3-TTS or MOSS-TTS."""

import sys
import time
import argparse
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import soundfile as sf
from src.audio.adapters.qwen_tts import Qwen3TTSBackend
from src.audio.adapters.moss_tts import MossTTSBackend


def run_tts_on_file(text_file: str, ref_audio: str, backend_type: str = "moss", output_name: str | None = None):
    """Run TTS on a text file.
    
    Args:
        text_file: Path to text file to synthesize
        ref_audio: Path to reference audio for voice cloning
        backend_type: 'qwen' or 'moss'
        output_name: Base name for output file (defaults to text file name)
    """
    # Read text file
    text_path = Path(text_file)
    with open(text_path, 'r') as f:
        text = f.read()
    
    # Determine output name
    if output_name is None:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_name = f"{backend_type}_{text_path.stem}_{timestamp}"
    
    output_path = Path("/home/warby/Workspace/outputs/audio") / f"{output_name}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading {backend_type} model...")
    if backend_type == "moss":
        backend = MossTTSBackend(model_size="1.7B")
    else:
        backend = Qwen3TTSBackend(model_size="1.7B", use_nf4=False, use_flash_attn=False)
        
    backend.load()
    
    print(f"Generating TTS for: {text_file}")
    print(f"Using reference audio: {ref_audio}")
    print(f"Text length: {len(text)} characters")
    
    # Generate voice clone
    # Note: MossTTSBackend doesn't need x_vector_only_mode arg in clone_voice interface
    if backend_type == "qwen":
        result = backend.clone_voice(
            text=text,
            ref_audio=ref_audio,
            ref_text=None,
            language="English",
            x_vector_only_mode=True,
        )
    else:
        result = backend.clone_voice(
            text=text,
            ref_audio=ref_audio,
            ref_text=None,
            language="English",
        )
    
    # Save output
    sf.write(output_path, result.audio, result.sample_rate)
    
    duration_s = len(result.audio) / result.sample_rate
    rtf = (result.generation_time_ms / 1000) / duration_s if duration_s > 0 else float("inf")
    
    print(f"\n✓ Generated: {output_path}")
    print(f"  Duration: {duration_s:.1f}s")
    print(f"  Generation time: {result.generation_time_ms:.1f}ms")
    print(f"  RTF: {rtf:.3f}")
    
    backend.unload()
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Run TTS on a text file')
    parser.add_argument('text_file', help='Path to text file')
    parser.add_argument('ref_audio', help='Path to reference audio')
    parser.add_argument('--backend', choices=['qwen', 'moss'], default='moss', help='TTS backend to use')
    parser.add_argument('--output', help='Output filename (without extension)')
    
    args = parser.parse_args()
    
    run_tts_on_file(args.text_file, args.ref_audio, args.backend, args.output)


if __name__ == "__main__":
    main()
