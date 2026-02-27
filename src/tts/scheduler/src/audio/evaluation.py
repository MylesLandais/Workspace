"""Voice cloning comparison framework."""

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import soundfile as sf

from .base import VoiceCloningBackend


@dataclass
class EvaluationResult:
    """Comparison metrics for a single test case."""

    backend_name: str
    text: str
    generation_time_ms: float
    audio_duration_s: float
    rtf: float  # Real-time factor (lower = faster)
    output_path: Path


class VoiceCloneEvaluator:
    """Compare voice cloning backends side-by-side."""

    def __init__(self, output_dir: str | Path = "/home/warby/Workspace/outputs/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(
        self,
        backends: list[VoiceCloningBackend],
        test_texts: list[str],
        ref_audio: str | Path,
        ref_text: str | None = None,
    ) -> list[EvaluationResult]:
        """Run evaluation across all backends and texts.

        Args:
            backends: List of voice cloning backends to compare.
            test_texts: List of texts to synthesize.
            ref_audio: Path to reference audio for voice cloning.
            ref_text: Optional transcript of reference audio.

        Returns:
            List of evaluation results for each backend/text combination.
        """
        results = []

        for backend in backends:
            backend.load()

            for i, text in enumerate(test_texts):
                result = backend.clone_voice(
                    text=text,
                    ref_audio=ref_audio,
                    ref_text=ref_text,
                )

                duration_s = len(result.audio) / result.sample_rate
                rtf = (result.generation_time_ms / 1000) / duration_s if duration_s > 0 else float("inf")

                safe_name = backend.name.replace(" ", "_").replace("/", "_")
                output_path = self.output_dir / f"{safe_name}_{i:03d}.wav"
                sf.write(output_path, result.audio, result.sample_rate)

                results.append(
                    EvaluationResult(
                        backend_name=backend.name,
                        text=text,
                        generation_time_ms=result.generation_time_ms,
                        audio_duration_s=duration_s,
                        rtf=rtf,
                        output_path=output_path,
                    )
                )

            backend.unload()

        return results

    def evaluate_with_prompt(
        self,
        backends: list[VoiceCloningBackend],
        test_texts: list[str],
        ref_audio: str | Path,
        ref_text: str | None = None,
    ) -> list[EvaluationResult]:
        """Run evaluation using cached voice prompts for efficiency.

        Args:
            backends: List of voice cloning backends to compare.
            test_texts: List of texts to synthesize.
            ref_audio: Path to reference audio for voice cloning.
            ref_text: Optional transcript of reference audio.

        Returns:
            List of evaluation results for each backend/text combination.
        """
        results = []

        for backend in backends:
            backend.load()
            voice_prompt = backend.create_voice_prompt(ref_audio, ref_text)
            batch_results = backend.generate_with_prompt(test_texts, voice_prompt)

            for i, (text, result) in enumerate(zip(test_texts, batch_results)):
                duration_s = len(result.audio) / result.sample_rate
                rtf = (result.generation_time_ms / 1000) / duration_s if duration_s > 0 else float("inf")

                safe_name = backend.name.replace(" ", "_").replace("/", "_")
                output_path = self.output_dir / f"{safe_name}_prompt_{i:03d}.wav"
                sf.write(output_path, result.audio, result.sample_rate)

                results.append(
                    EvaluationResult(
                        backend_name=backend.name,
                        text=text,
                        generation_time_ms=result.generation_time_ms,
                        audio_duration_s=duration_s,
                        rtf=rtf,
                        output_path=output_path,
                    )
                )

            backend.unload()

        return results

    def print_summary(self, results: list[EvaluationResult]):
        """Print formatted summary of evaluation results."""
        by_backend = defaultdict(list)
        for r in results:
            by_backend[r.backend_name].append(r)

        print("\n=== Voice Clone Evaluation Summary ===\n")
        for backend, runs in by_backend.items():
            avg_time = sum(r.generation_time_ms for r in runs) / len(runs)
            avg_rtf = sum(r.rtf for r in runs) / len(runs)
            total_duration = sum(r.audio_duration_s for r in runs)

            print(f"{backend}:")
            print(f"  Avg generation time: {avg_time:.1f}ms")
            print(f"  Avg RTF: {avg_rtf:.3f} ({'faster' if avg_rtf < 1 else 'slower'} than real-time)")
            print(f"  Total audio: {total_duration:.1f}s across {len(runs)} samples")
            print()
