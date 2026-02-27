#!/usr/bin/env python3
"""Batch voice comparison - process each voice separately to avoid OOM."""

import sys
import time
import gc
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import soundfile as sf
import numpy as np
import torch

from src.audio.adapters.qwen_tts import Qwen3TTSBackend
from src.audio.adapters.moss_tts import MossTTSBackend


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


def generate_voice(text_file: str, ref_audio: str, voice_name: str, backend_type: str = "qwen", output_dir: str = "/home/warby/Workspace/outputs/audio", max_chunk: int = 400):
    """Generate TTS for one voice, loading/unloading model for each voice."""
    
    text_path = Path(text_file)
    with open(text_path, 'r') as f:
        text = f.read()
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    output_path = Path(output_dir) / f"{backend_type}_{voice_name}_{timestamp}.wav"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print(f"Backend: {backend_type}")
    print(f"Voice: {voice_name}")
    print(f"Reference: {ref_audio}")
    print(f"{'='*60}")
    
    # Load model fresh for this voice
    print(f"Loading {backend_type} model...")
    if backend_type == "moss":
        # MOSS 8B is huge, 1.7B is safer for 8GB VRAM
        backend = MossTTSBackend(model_size="1.7B")
    else:
        # Enable NF4 for Qwen to save memory
        backend = Qwen3TTSBackend(model_size="1.7B", use_nf4=True, use_flash_attn=False)
    
    backend.load()
    
    chunks = chunk_text(text, max_chunk)
    print(f"Processing {len(chunks)} chunks...")
    
    all_audio = []
    total_gen_time = 0
    sample_rate = 24000
    
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1}/{len(chunks)}...", end=" ", flush=True)
        start = time.time()
        
        if torch.cuda.is_available():
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
    if torch.cuda.is_available():
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
        'backend': backend_type,
        'voice': voice_name,
        'file': str(output_path),
        'duration_s': duration_s,
        'gen_time_s': total_gen_time,
        'rtf': rtf,
        'chunks': len(chunks)
    }


def main():
    parser = argparse.ArgumentParser(description='Batch Voice Comparison')
    parser.add_argument('text_file', help='Path to text file')
    parser.add_argument('max_chunk', nargs='?', type=int, default=400, help='Max chars per chunk')
    parser.add_argument('--voices', help='Comma-separated list of voices to run (default: all)')
    parser.add_argument('--backend', choices=['qwen', 'moss', 'both'], default='both', help='TTS backend to use')
    
    args = parser.parse_args()
    
    text_file = args.text_file
    max_chunk = args.max_chunk
    
    # Updated paths to point to data/inputs/voices/
    voice_dir = Path("data/inputs/voices")
    all_voices = [
        ('larry', str(voice_dir / 'larry.wav')),
        ('maya', str(voice_dir / 'maya.wav')),
        ('selena', str(voice_dir / 'selena.wav')),
        ('emma', str(voice_dir / 'Emma_8s.wav')),
        ('kirk', str(voice_dir / 'kirk.wav')),
        ('lexie', str(voice_dir / 'lexie_8s.wav')),
    ]
    
    # Filter by existing files
    existing_voices = []
    for name, path in all_voices:
        if Path(path).exists():
            existing_voices.append((name, path))
        else:
            print(f"Warning: Voice file not found for {name}: {path}")

    if args.voices:
        selected_names = [v.strip().lower() for v in args.voices.split(',')]
        voices = [v for v in existing_voices if v[0] in selected_names]
        
        # Preserve order of user selection
        voices.sort(key=lambda x: selected_names.index(x[0]) if x[0] in selected_names else 999)
        
        if not voices:
            print(f"No valid voices found matching: {args.voices}")
            print(f"Available: {[v[0] for v in existing_voices]}")
            sys.exit(1)
    else:
        voices = existing_voices
    
    backends = ['qwen', 'moss'] if args.backend == 'both' else [args.backend]
    
    print(f"Batch Voice Comparison - Full Essay Test")
    print(f"Text file: {text_file}")
    print(f"Max chunk size: {max_chunk} chars")
    print(f"Selected backends: {backends}")
    print(f"Selected voices: {[v[0] for v in voices]}")
    
    results = []
    total_start = time.time()
    
    for backend_type in backends:
        for voice_name, ref_path in voices:
            try:
                result = generate_voice(text_file, ref_path, voice_name, backend_type=backend_type, max_chunk=max_chunk)
                results.append(result)
            except Exception as e:
                print(f"\n✗ Error with {backend_type}/{voice_name}: {e}")
                import traceback
                traceback.print_exc()
    
    total_time = time.time() - total_start
    
    # Summary
    print(f"\n{'='*80}")
    print(f"{'BACKEND':<10} {'VOICE':<10} {'DURATION':<12} {'GEN TIME':<12} {'RTF':<6}")
    print("-" * 60)
    for r in results:
        print(f"{r['backend']:<10} {r['voice']:<10} {r['duration_s']/60:>6.2f} min   {r['gen_time_s']/60:>6.2f} min   {r['rtf']:<6.2f}")
    
    print(f"\nTotal elapsed: {total_time/60:.1f} minutes")
    print(f"Output files in: /home/warby/Workspace/outputs/audio/")


if __name__ == "__main__":
    main()
