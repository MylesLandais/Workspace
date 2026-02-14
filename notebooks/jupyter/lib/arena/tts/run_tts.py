#!/usr/bin/env python3
"""Simple script to run TTS on a text file using Qwen3-TTS."""

import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audio.adapters.qwen_tts import Qwen3TTSBackend
import soundfile as sf


def run_tts_on_file(text_file: str, ref_audio: str, output_name: str = None):
    """Run TTS on a text file using Qwen3-TTS.
    
    Args:
        text_file: Path to text file to synthesize
        ref_audio: Path to reference audio for voice cloning
        output_name: Base name for output file (defaults to text file name)
    """
    # Read text file
    text_path = Path(text_file)
    with open(text_path, 'r') as f:
        text = f.read()
    
    # Determine output name
    if output_name is None:
        output_name = text_path.stem
    
    output_path = Path("eval_output") / f"{output_name}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Loading Qwen3-TTS model...")
    backend = Qwen3TTSBackend(model_size="1.7B", use_nf4=False, use_flash_attn=False)
    backend.load()
    
    print(f"Generating TTS for: {text_file}")
    print(f"Using reference audio: {ref_audio}")
    print(f"Text length: {len(text)} characters")
    
    # Generate voice clone (using x_vector mode to avoid needing ref_text)
    result = backend.clone_voice(
        text=text,
        ref_audio=ref_audio,
        ref_text=None,
        language="English",
        x_vector_only_mode=True,
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


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python src/audio/run_tts.py <text_file> <ref_audio> [output_name]")
        print("\nExample:")
        print("  python src/audio/run_tts.py hermione_slytherin_script.txt comfyui_projects/reference_audio/Emma.wav hermione_test")
        sys.exit(1)
    
    text_file = sys.argv[1]
    ref_audio = sys.argv[2]
    output_name = sys.argv[3] if len(sys.argv) > 3 else None
    
    run_tts_on_file(text_file, ref_audio, output_name)
