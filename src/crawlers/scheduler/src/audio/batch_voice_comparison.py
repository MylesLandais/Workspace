#!/usr/bin/env python3
"""Batch voice comparison - process each voice separately to avoid OOM."""

import sys
import time
import gc
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.audio.adapters.qwen_tts import Qwen3TTSBackend
import soundfile as sf
import numpy as np
import torch


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


def generate_voice(text_file: str, ref_audio: str, voice_name: str, output_dir: str = "eval_output", max_chunk: int = 800):
    """Generate TTS for one voice, loading/unloading model for each voice."""
    
    text_path = Path(text_file)
    with open(text_path, 'r') as f:
        text = f.read()
    
    output_path = Path(output_dir) / f"essay_{voice_name}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Voice: {voice_name}")
    print(f"Reference: {ref_audio}")
    print(f"{'='*60}")
    
    # Load model fresh for this voice
    print("Loading model...")
    backend = Qwen3TTSBackend(model_size="1.7B", use_nf4=False, use_flash_attn=False)
    backend.load()
    
    chunks = chunk_text(text, max_chunk)
    print(f"Processing {len(chunks)} chunks...")
    
    all_audio = []
    total_gen_time = 0
    sample_rate = 24000
    
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        start = time.time()
        
        torch.cuda.empty_cache()
        
        result = backend.clone_voice(
            text=chunk,
            ref_audio=ref_audio,
            ref_text=None,
            language="English",
            x_vector_only_mode=True,
        )
        
        sample_rate = result.sample_rate
        gen_time = time.time() - start
        total_gen_time += gen_time
        all_audio.append(result.audio)
        
        print(f"{gen_time:.1f}s")
    
    # Unload model
    backend.unload()
    del backend
    gc.collect()
    torch.cuda.empty_cache()
    
    # Join audio
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
    
    print(f"✓ Saved: {output_path.name} ({duration_s/60:.1f}min, RTF: {rtf:.2f})")
    
    return {
        'voice': voice_name,
        'file': str(output_path),
        'duration_s': duration_s,
        'gen_time_s': total_gen_time,
        'rtf': rtf,
        'chunks': len(chunks)
    }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch Voice Comparison')
    parser.add_argument('text_file', help='Path to text file')
    parser.add_argument('max_chunk', nargs='?', type=int, default=800, help='Max chars per chunk')
    parser.add_argument('--voices', help='Comma-separated list of voices to run (default: all)')
    
    args = parser.parse_args()
    
    text_file = args.text_file
    max_chunk = args.max_chunk
    
    all_voices = [
        ('maya', 'comfyui_projects/reference_audio/maya.wav'),
        ('selena', 'comfyui_projects/reference_audio/selena.wav'),
        ('emma', 'comfyui_projects/reference_audio/Emma_8s.wav'),
        ('kirk', 'comfyui_projects/reference_audio/kirk.wav'),
        ('lexie', 'comfyui_projects/reference_audio/lexie_8s.wav'),
        ('larry', 'comfyui_projects/reference_audio/larry.wav'),
    ]
    
    if args.voices:
        selected_names = [v.strip().lower() for v in args.voices.split(',')]
        voices = [v for v in all_voices if v[0] in selected_names]
        
        # Preserve order of user selection
        voices.sort(key=lambda x: selected_names.index(x[0]) if x[0] in selected_names else 999)
        
        if not voices:
            print(f"No valid voices found matching: {args.voices}")
            print(f"Available: {[v[0] for v in all_voices]}")
            sys.exit(1)
    else:
        voices = all_voices
    
    print(f"Batch Voice Comparison - Full Essay Test")
    print(f"Text file: {text_file}")
    print(f"Max chunk size: {max_chunk} chars")
    print(f"Selected voices: {[v[0] for v in voices]}")
    print(f"\nProcessing {len(voices)} voices sequentially...")
    
    results = []
    total_start = time.time()
    
    for voice_name, ref_path in voices:
        try:
            result = generate_voice(text_file, ref_path, voice_name, max_chunk=max_chunk)
            results.append(result)
        except Exception as e:
            print(f"\n✗ Error with {voice_name}: {e}")
            import traceback
            traceback.print_exc()
    
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
