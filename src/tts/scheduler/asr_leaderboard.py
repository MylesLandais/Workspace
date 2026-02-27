#!/usr/bin/env python3
"""
ASR Model Leaderboard Generator and Evaluator
"""

import sys
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
import torch

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.providers.asr.adapters.faster_whisper_adapter import FasterWhisperAdapter
from src.providers.asr.adapters.olmoasr_adapter import OLMoASRAdapter
from src.providers.asr.adapters.canary_qwen_adapter import CanaryQwenAdapter
from src.providers.asr.storage.postgres_storage import PostgreSQLStorage
from src.providers.asr.core.config import ConfigManager


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Calculate Word Error Rate (WER)."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()

    if len(ref_words) == 0:
        return 1.0 if len(hyp_words) > 0 else 0.0

    # Simple Levenshtein distance for words
    d = [[0] * (len(hyp_words) + 1) for _ in range(len(ref_words) + 1)]

    for i in range(len(ref_words) + 1):
        d[i][0] = i
    for j in range(len(hyp_words) + 1):
        d[0][j] = j

    for i in range(1, len(ref_words) + 1):
        for j in range(1, len(hyp_words) + 1):
            if ref_words[i-1] == hyp_words[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = min(d[i-1][j], d[i][j-1], d[i-1][j-1]) + 1

    return d[len(ref_words)][len(hyp_words)] / len(ref_words)


def calculate_cer(reference: str, hypothesis: str) -> float:
    """Calculate Character Error Rate (CER)."""
    ref_chars = list(reference.lower())
    hyp_chars = list(hypothesis.lower())

    if len(ref_chars) == 0:
        return 1.0 if len(hyp_chars) > 0 else 0.0

    # Simple Levenshtein distance for characters
    d = [[0] * (len(hyp_chars) + 1) for _ in range(len(ref_chars) + 1)]

    for i in range(len(ref_chars) + 1):
        d[i][0] = i
    for j in range(len(hyp_chars) + 1):
        d[0][j] = j

    for i in range(1, len(ref_chars) + 1):
        for j in range(1, len(hyp_chars) + 1):
            if ref_chars[i-1] == hyp_chars[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = min(d[i-1][j], d[i][j-1], d[i-1][j-1]) + 1

    return d[len(ref_chars)][len(hyp_chars)] / len(ref_chars)

def load_reference_text() -> str:
    """Load the reference transcription."""
    # Use project root relative path for better portability
    project_root = Path(__file__).resolve().parent
    ref_file = project_root / "evaluation_datasets" / "vaporeon" / "reference_transcript.txt"

    if ref_file.exists():
        with open(ref_file, 'r') as f:
            return f.read().strip()
    else:
        print(f"ERROR: Reference file not found: {ref_file}")
        return ""

def test_model(adapter, model_name: str, audio_file: str, reference: str,
               storage: Optional[PostgreSQLStorage], experiment_id: str, debug: bool = False) -> Dict[str, Any]:
    """Test a single model and return results."""
    print(f"\nTesting {model_name}...")

    try:
        if debug:
            print(f"  - Adapter: {adapter.__class__.__name__}")
            print(f"  - Audio file: {audio_file}")

        # Check availability
        if not adapter.is_available():
            return {
                "model_name": model_name,
                "status": "UNAVAILABLE",
                "error": "Model not available"
            }

        # Transcribe
        start_time = time.time()
        result = adapter.transcribe(audio_file)
        total_time = time.time() - start_time

        # Calculate metrics
        wer = calculate_wer(reference, result.text)
        cer = calculate_cer(reference, result.text)

        # Calculate processing speed
        audio_duration = result.metadata.get("audio_duration", 164)
        speed_ratio = result.processing_time / (audio_duration / 60) if audio_duration > 0 else 0

        model_info = adapter.get_model_info()

        if storage:
            try:
                storage.save_response(
                    experiment_id=experiment_id,
                    model_name=model_info.name,
                    model_version=model_info.version,
                    model_type=model_info.model_type,
                    predicted_text=result.text,
                    wer=wer,
                    cer=cer,
                    processing_time=result.processing_time,
                    audio_duration=audio_duration,
                    audio_file=audio_file,
                    device=result.metadata.get("device", "unknown"),
                    confidence_scores=result.confidence_scores,
                    model_parameters=result.metadata,
                    metadata={
                        "speed_ratio": speed_ratio,
                        "word_count": len(result.text.split()),
                        "char_count": len(result.text),
                        "total_time": total_time
                    }
                )
            except Exception as e:
                if debug:
                    print(f"  - DB Save Error: {e}")

        return {
            "model_name": model_name,
            "status": "SUCCESS",
            "transcription": result.text,
            "wer": wer,
            "cer": cer,
            "processing_time": result.processing_time,
            "total_time": total_time,
            "speed_ratio": speed_ratio,
            "word_count": len(result.text.split()),
            "char_count": len(result.text),
            "confidence_available": result.confidence_scores is not None,
            "metadata": result.metadata
        }

    except Exception as e:
        if debug:
            import traceback
            print(traceback.format_exc())
        return {
            "model_name": model_name,
            "status": "ERROR",
            "error": str(e)
        }

# --- Mode-specific logic ---

def run_full_mode(audio_file: str, reference: str, debug: bool):
    """Run the full, comprehensive ASR evaluation."""
    print("--- Running in FULL evaluation mode ---")
    # Database connection, etc. (similar to original main)
    storage = None # Simplified for now
    experiment_id = f"exp_{int(time.time())}"

    models_to_test = [
        ("canary-qwen-2.5b", lambda: CanaryQwenAdapter(model_name="nvidia/canary-qwen-2.5b")),
        ("faster-whisper-tiny", lambda: FasterWhisperAdapter(model_size="tiny")),
        ("faster-whisper-base", lambda: FasterWhisperAdapter(model_size="base")),
        ("hf-whisper-base", lambda: OLMoASRAdapter(model_name="openai/whisper-base")),
    ]

    results = []
    for model_name, adapter_factory in models_to_test:
        adapter = adapter_factory()
        result = test_model(adapter, model_name, audio_file, reference, storage, experiment_id, debug)
        results.append(result)

    print_leaderboard(results)
    save_results(results)

def run_fast_mode(audio_file: str, reference: str, debug: bool):
    """Run a fast, GPU-optimized ASR comparison."""
    print("--- Running in FAST evaluation mode (GPU-optimized) ---")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")

    # Simplified test function for direct model usage
    def test_fast(model_name, model_size):
        print(f"\nTesting {model_name}...")
        start_time = time.time()
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(model_size, device=device, compute_type="float16" if device == "cuda" else "int8")
            segments, _ = model.transcribe(audio_file, beam_size=1)
            text = " ".join([s.text for s in segments])
            processing_time = time.time() - start_time
            wer = calculate_wer(reference, text)
            return {"model_name": model_name, "status": "SUCCESS", "wer": wer, "processing_time": processing_time, "transcription": text}
        except Exception as e:
            if debug:
                import traceback
                print(traceback.format_exc())
            return {"model_name": model_name, "status": "ERROR", "error": str(e)}

    models_to_test = [
        ("faster-whisper-tiny", "tiny"),
        ("faster-whisper-base", "base"),
    ]

    results = [test_fast(name, size) for name, size in models_to_test]
    print_leaderboard(results)
    save_results(results)

def run_minimal_mode(audio_file: str, reference: str, debug: bool):
    """Run a minimal, CPU-only ASR comparison."""
    print("--- Running in MINIMAL evaluation mode (CPU-only) ---")

    def test_minimal(model_name, model_size):
        print(f"\nTesting {model_name}...")
        start_time = time.time()
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel(model_size, device="cpu")
            segments, _ = model.transcribe(audio_file, beam_size=1)
            text = " ".join([s.text for s in segments])
            processing_time = time.time() - start_time
            wer = calculate_wer(reference, text)
            return {"model_name": model_name, "status": "SUCCESS", "wer": wer, "processing_time": processing_time, "transcription": text}
        except Exception as e:
            if debug:
                import traceback
                print(traceback.format_exc())
            return {"model_name": model_name, "status": "ERROR", "error": str(e)}

    models_to_test = [
        ("faster-whisper-tiny", "tiny"),
    ]

    results = [test_minimal(name, size) for name, size in models_to_test]
    print_leaderboard(results)
    save_results(results)

def print_leaderboard(results: List[Dict[str, Any]]):
    """Print a formatted leaderboard table."""
    print("\n" + "="*100)
    print("ASR MODEL LEADERBOARD - CURRENT RUN")
    print("="*100)

    successful_results = [r for r in results if r.get("status") == "SUCCESS"]

    if not successful_results:
        print("No successful transcriptions to rank!")
        return

    successful_results.sort(key=lambda x: x.get("wer", 1.0))

    print(f"{'Rank':<4} {'Model':<25} {'WER':<8} {'Time':<8} {'Status'}")
    print("-" * 100)

    for i, result in enumerate(successful_results, 1):
        model_name = result["model_name"][:24]
        wer = f"{result.get('wer', 0):.2%}"
        proc_time = f"{result.get('processing_time', 0):.1f}s"
        print(f"{i:<4} {model_name:<25} {wer:<8} {proc_time:<8} SUCCESS")

    failed_results = [r for r in results if r.get("status") != "SUCCESS"]
    if failed_results:
        print("\nFAILED MODELS:")
        for result in failed_results:
            print(f"- {result['model_name']}: {result.get('error', 'Unknown')}")

def save_results(results: List[Dict[str, Any]], output_file: str = "leaderboard_results.json"):
    """Save detailed results to a JSON file."""
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\nDetailed results saved to: {output_file}")

def main():
    """Main CLI for ASR evaluation."""
    parser = argparse.ArgumentParser(description="ASR Model Leaderboard Generator and Evaluator")
    parser.add_argument(
        "--mode",
        type=str,
        choices=["full", "fast", "minimal"],
        default="full",
        help="Evaluation mode: 'full' (comprehensive), 'fast' (GPU-optimized), or 'minimal' (CPU-only)."
    )
    parser.add_argument(
        "--audio-file",
        type=str,
        default="evaluation_datasets/vaporeon/-EWMgB26bmU_Vaporeon copypasta (animated).mp3",
        help="Path to the audio file to evaluate."
    )
    parser.add_argument("--debug", action="store_true", help="Enable detailed debug logging.")
    args = parser.parse_args()

    print(f"ASR Evaluator | Mode: {args.mode} | Debug: {args.debug}")

    # Basic setup
    audio_file = Path(args.audio_file)
    if not audio_file.exists():
        print(f"ERROR: Audio file not found: {audio_file}")
        # Here we would call the dataset manager to download it
        # For now, we'll just exit.
        sys.exit(1)

    reference = load_reference_text()
    if not reference:
        sys.exit(1)

    # Run selected mode
    if args.mode == "full":
        run_full_mode(str(audio_file), reference, args.debug)
    elif args.mode == "fast":
        run_fast_mode(str(audio_file), reference, args.debug)
    elif args.mode == "minimal":
        run_minimal_mode(str(audio_file), reference, args.debug)

    print("\nEvaluation complete!")


if __name__ == "__main__":
    main()
