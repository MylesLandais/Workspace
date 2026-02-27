"""TTS evaluation framework.

Supports any TTSBackend (zero-shot or voice cloning) via synthesize().
Voice-clone-specific evaluation uses clone_voice() when ref_audio is provided.
WER scoring via AudioQualityChecker requires the eval optional deps:
    uv add --optional eval 'nemo_toolkit[asr]' jiwer
"""

import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import soundfile as sf

from .base import TTSBackend, VoiceCloningBackend


# Standard regression prompts covering failure modes: garble, truncation,
# number handling, punctuation rhythm, and proper noun articulation.
# Run these against every new model to catch regressions before human review.
GOLDEN_PROMPTS: list[str] = [
    "The quick brown fox jumps over the lazy dog.",
    "The meeting is at 2:30 PM on March 15th in room 404.",
    "Wait—are you serious? I can't believe it!",
    "Dr. Smith visited MIT and Stanford last Tuesday to discuss the findings.",
    (
        "In a rapidly evolving landscape of artificial intelligence, "
        "the ability to synthesize natural-sounding speech remains "
        "one of the most compelling and challenging frontiers."
    ),
    "Yes.",
    "Call me at 555-867-5309 if anything changes.",
    "She said: \"I'll be there by noon, without fail.\"",
]


@dataclass
class EvaluationResult:
    """Metrics for a single backend/text generation."""

    backend_name: str
    text: str
    generation_time_ms: float
    audio_duration_s: float
    rtf: float  # Real-time factor (lower = faster)
    output_path: Path
    wer: float | None = field(default=None)  # Populated by AudioQualityChecker


class TTSEvaluator:
    """Evaluate any TTSBackend.

    Calls synthesize() for every backend by default. When ref_audio is
    provided and the backend is a VoiceCloningBackend, calls clone_voice()
    instead so the reference audio is used for conditioning.
    """

    def __init__(self, output_dir: str | Path = "eval_output"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate(
        self,
        backends: list[TTSBackend],
        test_texts: list[str],
        ref_audio: str | Path | None = None,
        ref_text: str | None = None,
    ) -> list[EvaluationResult]:
        """Run evaluation across all backends and texts.

        Each backend is loaded, run against all texts, then unloaded before
        the next backend loads. This keeps VRAM free for AudioQualityChecker.

        Args:
            backends: Any TTSBackend implementations to compare.
            test_texts: Texts to synthesize. Use GOLDEN_PROMPTS for regression.
            ref_audio: Optional reference audio. Used only by VoiceCloningBackend.
            ref_text: Optional transcript of the reference audio.
        """
        results = []

        for backend in backends:
            backend.load()

            for i, text in enumerate(test_texts):
                if ref_audio is not None and isinstance(backend, VoiceCloningBackend):
                    result = backend.clone_voice(text, ref_audio, ref_text)
                else:
                    result = backend.synthesize(text)

                duration_s = len(result.audio) / result.sample_rate
                rtf = (
                    (result.generation_time_ms / 1000) / duration_s
                    if duration_s > 0
                    else float("inf")
                )

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
        """Evaluate voice cloning backends using cached voice prompts.

        Only applicable to VoiceCloningBackend subclasses that override
        create_voice_prompt(). Backends that don't support prompt caching
        will raise NotImplementedError.
        """
        results = []

        for backend in backends:
            backend.load()
            voice_prompt = backend.create_voice_prompt(ref_audio, ref_text)
            batch_results = backend.generate_with_prompt(test_texts, voice_prompt)

            for i, (text, result) in enumerate(zip(test_texts, batch_results)):
                duration_s = len(result.audio) / result.sample_rate
                rtf = (
                    (result.generation_time_ms / 1000) / duration_s
                    if duration_s > 0
                    else float("inf")
                )

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

    def print_summary(self, results: list[EvaluationResult]) -> None:
        """Print formatted summary including WER if scored."""
        by_backend: dict[str, list[EvaluationResult]] = defaultdict(list)
        for r in results:
            by_backend[r.backend_name].append(r)

        print("\n=== TTS Evaluation Summary ===\n")
        for backend, runs in by_backend.items():
            avg_time = sum(r.generation_time_ms for r in runs) / len(runs)
            avg_rtf = sum(r.rtf for r in runs) / len(runs)
            total_duration = sum(r.audio_duration_s for r in runs)
            scored = [r for r in runs if r.wer is not None]

            print(f"{backend}:")
            print(f"  Avg generation time: {avg_time:.1f}ms")
            print(
                f"  Avg RTF: {avg_rtf:.3f} "
                f"({'faster' if avg_rtf < 1 else 'slower'} than real-time)"
            )
            print(f"  Total audio: {total_duration:.1f}s across {len(runs)} samples")
            if scored:
                avg_wer = sum(r.wer for r in scored) / len(scored)
                failures = sum(1 for r in scored if r.wer > AudioQualityChecker.WER_THRESHOLD)
                print(
                    f"  Avg WER: {avg_wer:.1%} "
                    f"({failures}/{len(scored)} above "
                    f"{AudioQualityChecker.WER_THRESHOLD:.0%} threshold)"
                )
            print()


# Backward-compatible alias.
VoiceCloneEvaluator = TTSEvaluator


_PUNCT_RE = re.compile(r"[^\w\s]")


def _normalize(text: str) -> str:
    """Lowercase and strip punctuation for WER comparison."""
    return _PUNCT_RE.sub("", text.lower()).strip()


class AudioQualityChecker:
    """Score TTS outputs using Parakeet ASR and Word Error Rate.

    Call after all TTS backends have unloaded to avoid VRAM contention.
    Parakeet CTC 0.6B uses ~2 GB VRAM, well within headroom after unload.

    Install deps: uv add --optional eval 'nemo_toolkit[asr]' jiwer
    """

    WER_THRESHOLD = 0.15  # >15% error → garbled/broken audio

    def __init__(self, wer_threshold: float = WER_THRESHOLD):
        self.wer_threshold = wer_threshold
        self._asr_model = None

    def _ensure_loaded(self) -> None:
        if self._asr_model is not None:
            return
        try:
            import nemo.collections.asr as nemo_asr
        except ImportError:
            raise ImportError(
                "Install eval extras: uv add --optional eval 'nemo_toolkit[asr]' jiwer"
            )
        import torch

        print("Loading Parakeet ASR (nvidia/parakeet-ctc-0.6b)...")
        self._asr_model = nemo_asr.models.EncDecCTCModelBPE.from_pretrained(
            model_name="nvidia/parakeet-ctc-0.6b"
        )
        self._asr_model.eval()
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self._asr_model = self._asr_model.to(device)

    def unload(self) -> None:
        if self._asr_model is not None:
            import torch

            del self._asr_model
            self._asr_model = None
            torch.cuda.empty_cache()

    def score(self, results: list[EvaluationResult]) -> list[EvaluationResult]:
        """Transcribe generated audio and annotate results with WER.

        TTS backends must be unloaded before calling to free VRAM.
        Missing audio files are skipped (wer stays None).
        """
        try:
            from jiwer import wer as compute_wer
        except ImportError:
            raise ImportError(
                "Install eval extras: uv add --optional eval 'nemo_toolkit[asr]' jiwer"
            )

        self._ensure_loaded()

        valid = [(i, r) for i, r in enumerate(results) if r.output_path.exists()]
        if not valid:
            print("No audio files found to score.")
            return results

        audio_paths = [str(r.output_path) for _, r in valid]
        transcriptions = self._asr_model.transcribe(audio_paths)

        scored = list(results)
        for (i, original), actual in zip(valid, transcriptions):
            error_rate = compute_wer(_normalize(original.text), _normalize(actual))
            scored[i] = EvaluationResult(
                backend_name=original.backend_name,
                text=original.text,
                generation_time_ms=original.generation_time_ms,
                audio_duration_s=original.audio_duration_s,
                rtf=original.rtf,
                output_path=original.output_path,
                wer=error_rate,
            )

        return scored

    def print_wer_report(self, results: list[EvaluationResult]) -> bool:
        """Print per-sample WER and return True if all passed.

        Returns False if any sample exceeds wer_threshold, which indicates
        a model regression or dependency mismatch (garbled decode path).
        """
        scored = [r for r in results if r.wer is not None]
        if not scored:
            print("No WER scores available. Run score() first.")
            return True

        print("\n=== ASR Quality Report ===\n")
        failures = 0
        for r in scored:
            passed = r.wer <= self.wer_threshold
            status = "PASS" if passed else "FAIL"
            print(f"[{status}] {r.backend_name} | WER: {r.wer:.1%}")
            if not passed:
                failures += 1
                print(f"       expected: {r.text[:80]}")

        total = len(scored)
        print(
            f"\n{total - failures}/{total} passed "
            f"(threshold: {self.wer_threshold:.0%})"
        )
        if failures:
            print(
                "Possible causes: wrong transformers version, "
                "garbled decoder output, VRAM contention."
            )
        return failures == 0
