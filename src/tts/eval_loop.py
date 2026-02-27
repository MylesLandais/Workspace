"""TTS evaluation loop with VRAM and timing metrics."""

import sys
import os
import time
import json
import gc
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime

WORKSPACE = Path(__file__).resolve().parent.parent.parent
env_file = WORKSPACE / ".env"
if env_file.exists():
    for line in env_file.read_text().strip().split("\n"):
        if "=" in line and not line.startswith("#"):
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

import torch
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.tts.adapters import get_adapter, list_adapter_info


WORKSPACE = Path(__file__).resolve().parent.parent.parent
REF_AUDIO = WORKSPACE / "data" / "inputs" / "voices" / "26-emma-jayshettypodcast.wav"
TEXT_FILE = WORKSPACE / "data" / "inputs" / "vaporeon_copypasta.txt"
OUTPUT_DIR = WORKSPACE / "data" / "outputs" / "tts_eval"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class EvalResult:
    backend: str
    display_name: str
    vram_baseline_mb: float
    vram_peak_mb: float
    vram_delta_mb: float
    generation_time_ms: float
    audio_duration_s: float
    rtf: float
    output_path: str
    error: str | None = None


def get_vram_mb() -> float:
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.memory_allocated() / 1024 / 1024


def get_vram_peak_mb() -> float:
    if not torch.cuda.is_available():
        return 0.0
    return torch.cuda.max_memory_allocated() / 1024 / 1024


def reset_vram_stats():
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
        torch.cuda.empty_cache()


def clear_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.synchronize()


def run_eval(
    backend_name: str,
    text: str,
    ref_audio: Path,
    timestamp: str,
) -> EvalResult:
    adapter_info = list_adapter_info().get(backend_name)
    display_name = adapter_info.display_name if adapter_info else backend_name

    print(f"\n{'='*60}")
    print(f"Backend: {display_name}")
    print(f"{'='*60}")

    reset_vram_stats()
    vram_baseline = get_vram_mb()

    try:
        backend = get_adapter(backend_name)
        print(f"Loading {backend.name} on {backend.device}...")

        load_start = time.perf_counter()
        backend.load()
        load_time = time.perf_counter() - load_start
        print(f"Load time: {load_time:.2f}s")

        vram_after_load = get_vram_mb()
        print(f"VRAM after load: {vram_after_load:.1f} MB (delta: +{vram_after_load - vram_baseline:.1f} MB)")

        reset_vram_stats()
        vram_before_gen = get_vram_mb()

        print(f"Generating audio...")
        gen_start = time.perf_counter()
        result = backend.clone_voice(text=text, ref_audio=str(ref_audio))
        gen_time = time.perf_counter() - gen_start

        vram_peak = get_vram_peak_mb()
        vram_delta = vram_peak - vram_before_gen

        audio_duration = len(result.audio) / result.sample_rate
        rtf = gen_time / audio_duration if audio_duration > 0 else float("inf")

        output_file = OUTPUT_DIR / f"{timestamp}-{backend_name}-emma-vaporeon.wav"
        sf.write(str(output_file), result.audio, result.sample_rate)

        print(f"Generation time: {gen_time:.2f}s")
        print(f"Audio duration: {audio_duration:.2f}s")
        print(f"RTF: {rtf:.3f} ({'faster' if rtf < 1 else 'slower'} than real-time)")
        print(f"VRAM peak: {vram_peak:.1f} MB (delta: +{vram_delta:.1f} MB)")
        print(f"Saved: {output_file}")

        backend.unload()
        del backend

        return EvalResult(
            backend=backend_name,
            display_name=display_name,
            vram_baseline_mb=round(vram_baseline, 1),
            vram_peak_mb=round(vram_peak, 1),
            vram_delta_mb=round(vram_delta, 1),
            generation_time_ms=round(gen_time * 1000, 1),
            audio_duration_s=round(audio_duration, 2),
            rtf=round(rtf, 3),
            output_path=str(output_file),
        )

    except Exception as e:
        import traceback
        print(f"FAILED: {e}")
        traceback.print_exc()
        return EvalResult(
            backend=backend_name,
            display_name=display_name,
            vram_baseline_mb=round(vram_baseline, 1),
            vram_peak_mb=0,
            vram_delta_mb=0,
            generation_time_ms=0,
            audio_duration_s=0,
            rtf=0,
            output_path="",
            error=str(e),
        )
    finally:
        clear_memory()


def print_summary(results: list[EvalResult]):
    print("\n" + "=" * 80)
    print("TTS EVALUATION SUMMARY")
    print("=" * 80)

    success = [r for r in results if not r.error]
    failed = [r for r in results if r.error]

    if success:
        print("\n{:<15} {:>12} {:>12} {:>10} {:>8}".format(
            "Backend", "Time (s)", "VRAM (MB)", "RTF", "Status"
        ))
        print("-" * 60)
        for r in success:
            print("{:<15} {:>12.2f} {:>12.1f} {:>10.3f} {:>8}".format(
                r.backend,
                r.generation_time_ms / 1000,
                r.vram_peak_mb,
                r.rtf,
                "OK"
            ))

    if failed:
        print("\nFAILED:")
        for r in failed:
            err_short = r.error[:100] + "..." if r.error and len(r.error) > 100 else r.error
            print(f"  {r.backend}: {err_short}")

    print("\n" + "=" * 80)


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="TTS Evaluation")
    parser.add_argument("--backends", "-b", nargs="+", help="Specific backends to run (e.g., moss-tts qwen3tts)")
    parser.add_argument("--text", "-t", help="Text file to use (default: vaporeon_copypasta.txt)")
    args = parser.parse_args()

    if not REF_AUDIO.exists():
        print(f"Error: Reference audio not found at {REF_AUDIO}")
        return 1

    text = TEXT_FILE.read_text().strip()
    if args.text:
        custom_text = Path(args.text)
        if custom_text.exists():
            text = custom_text.read_text().strip()
            print(f"Using custom text file: {args.text}")
    
    if not text:
        print(f"Error: No text found in {TEXT_FILE}")
        return 1

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    print(f"Evaluation timestamp: {timestamp}")
    print(f"Reference audio: {REF_AUDIO}")
    print(f"Text length: {len(text)} chars")

    # Check CUDA
    print(f"\nCUDA available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"GPU: {torch.cuda.get_device_name(0)}")
        print(f"CUDA version: {torch.version.cuda}")

    # Only run local backends (skip cloud/gated)
    if args.backends:
        backends = args.backends
    else:
        backends = ["qwen3tts", "moss-tts"]

        # Add CSM if HF token is available
        if os.getenv("HF_TOKEN") or os.getenv("HUGGING_FACE_HUB_TOKEN"):
            backends.append("csm")
        else:
            print("\nSkipping CSM (no HF_TOKEN set)")

        # Add VibeVoice if RunPod is configured
        if os.getenv("RUNPOD_POD_ID"):
            backends.append("vibevoice")
        else:
            print("Skipping VibeVoice (no RUNPOD_POD_ID set)")

    print(f"\nBackends to evaluate: {', '.join(backends)}")

    results: list[EvalResult] = []

    for backend_name in backends:
        result = run_eval(backend_name, text, REF_AUDIO, timestamp)
        results.append(result)
        clear_memory()
        time.sleep(2)

    results_file = OUTPUT_DIR / f"{timestamp}-eval_results.json"
    with open(results_file, "w") as f:
        json.dump([asdict(r) for r in results], f, indent=2)
    print(f"\nResults saved to: {results_file}")

    print_summary(results)

    return 0


if __name__ == "__main__":
    sys.exit(main())
