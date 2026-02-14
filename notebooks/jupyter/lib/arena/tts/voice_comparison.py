#!/usr/bin/env python3
"""Voice comparison script - run TTS with multiple reference voices."""

import sys
import time
import gc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audio.adapters.qwen_tts import Qwen3TTSBackend
import soundfile as sf
import numpy as np


def chunk_text(text: str, max_chars: int = 800) -> list:
    """Split text into chunks at sentence boundaries."""
    chunks = []
    current_chunk = ""
    
    sentences = text.replace('\n', ' ').split('. ')
    
    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue
        if not sentence.endswith('.'):
            sentence += '.'
        
        if len(current_chunk) + len(sentence) + 1 <= max_chars:
            current_chunk += sentence + ' '
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + ' '
    
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks


def generate_with_voice(backend, text: str, ref_audio: str, voice_name: str, output_dir: str = "eval_output", max_chunk: int = 800):
    """Generate TTS for a text file using a specific voice with pre-loaded backend."""
    
    output_path = Path(output_dir) / f"essay_{voice_name}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Generating with voice: {voice_name}")
    print(f"Reference: {ref_audio}")
    print(f"{'='*60}")
    
    chunks = chunk_text(text, max_chunk)
    print(f"Split into {len(chunks)} chunks (max {max_chunk} chars each)")
    
    all_audio = []
    total_gen_time = 0
    sample_rate = 24000  # Default sample rate for Qwen3-TTS
    result = None
    
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)} ({len(chunk)} chars)...", end=" ", flush=True)
        start = time.time()
        
        import torch
        torch.cuda.empty_cache()
        
        result = backend.clone_voice(
            text=chunk,
            ref_audio=ref_audio,
            ref_text=None,
            language="English",
            x_vector_only_mode=True,
        )
        
        # Update sample rate from result if needed
        if hasattr(result, 'sample_rate') and result.sample_rate != sample_rate:
            sample_rate = result.sample_rate
        
        gen_time = time.time() - start
        total_gen_time += gen_time
        all_audio.append(result.audio)
        
        print(f"Done in {gen_time:.1f}s")
    
    if not all_audio:
        print("No audio generated!")
        return None
    
    # Join with pauses
    pause = np.zeros(int(sample_rate * 0.3))
    combined = []
    for i, audio in enumerate(all_audio):
        combined.append(audio)
        if i < len(all_audio) - 1:
            combined.append(pause)
    
    final = np.concatenate(combined)
    sf.write(output_path, final, sample_rate)
    
    duration_s = len(final) / sample_rate
    rtf = total_gen_time / duration_s if duration_s > 0 else float("inf")
    
    print(f"\n✓ Saved: {output_path}")
    print(f"  Duration: {duration_s:.1f}s ({duration_s/60:.1f}min)")
    print(f"  Total gen time: {total_gen_time:.1f}s ({total_gen_time/60:.1f}min)")
    print(f"  RTF: {rtf:.2f}")
    
    return {
        'voice': voice_name,
        'file': str(output_path),
        'duration_s': duration_s,
        'gen_time_s': total_gen_time,
        'rtf': rtf,
        'chunks': len(chunks)
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python voice_comparison.py <text_file> [max_chunk_size]")
        print("\nGenerates audio for all 5 voices:")
        print("  - maya (maya.wav)")
        print("  - selena (selena.wav)")
        print("  - emma (Emma_8s.wav)")
        print("  - kirk (kirk.wav)")
        print("  - lexie (lexie_8s.wav)")
        sys.exit(1)
    
    text_file = sys.argv[1]
    max_chunk = int(sys.argv[2]) if len(sys.argv) > 2 else 800
    
    # Read text once
    text_path = Path(text_file)
    with open(text_path, 'r') as f:
        text = f.read()
    
    voices = {
        'maya': 'comfyui_projects/reference_audio/maya.wav',
        'selena': 'comfyui_projects/reference_audio/selena.wav',
        'emma': 'comfyui_projects/reference_audio/Emma_8s.wav',
        'kirk': 'comfyui_projects/reference_audio/kirk.wav',
        'lexie': 'comfyui_projects/reference_audio/lexie_8s.wav',
    }
    
    print(f"Voice Comparison - Full Essay Test")
    print(f"Text file: {text_file}")
    print(f"Text length: {len(text)} characters, {len(text.split())} words")
    print(f"Max chunk size: {max_chunk} chars")
    print(f"\nVoices to test: {', '.join(voices.keys())}")
    
    # Load model once
    print(f"\n{'='*60}")
    print("Loading Qwen3-TTS model (bf16, no flash-attn)...")
    print(f"{'='*60}")
    backend = Qwen3TTSBackend(model_size="1.7B", use_nf4=False, use_flash_attn=False)
    backend.load()
    print("Model loaded successfully!")
    
    results = []
    total_start = time.time()
    
    for voice_name, ref_path in voices.items():
        try:
            result = generate_with_voice(backend, text, ref_path, voice_name, max_chunk=max_chunk)
            results.append(result)
        except Exception as e:
            print(f"\n✗ Error with {voice_name}: {e}")
            import traceback
            traceback.print_exc()
    
    # Unload model
    print(f"\n{'='*60}")
    print("Unloading model...")
    print(f"{'='*60}")
    backend.unload()
    gc.collect()
    
    total_time = time.time() - total_start
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Total time: {total_time/60:.1f} minutes\n")
    
    print(f"{'Voice':<10} {'Duration':<10} {'Gen Time':<10} {'RTF':<6}")
    print("-" * 40)
    for r in results:
        print(f"{r['voice']:<10} {r['duration_s']/60:>6.1f}min   {r['gen_time_s']/60:>6.1f}min   {r['rtf']:<6.2f}")
    
    print(f"\nOutput files in: eval_output/")
    for r in results:
        print(f"  - {Path(r['file']).name}")


if __name__ == "__main__":
    main()
