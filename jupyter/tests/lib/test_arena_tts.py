"""Tests for lib.arena.tts module."""

import pytest

np = pytest.importorskip("numpy", reason="numpy not available in this environment")

from lib.arena.tts.base import VoiceCloningBackend, VoiceCloneResult, VoicePrompt


class TestVoicePrompt:
    """Test VoicePrompt dataclass."""

    def test_create_prompt(self):
        prompt = VoicePrompt(
            embedding=[0.1, 0.2],
            ref_audio_path="/audio/ref.wav",
            ref_text="Hello",
            backend="qwen",
        )
        assert prompt.ref_audio_path == "/audio/ref.wav"
        assert prompt.backend == "qwen"

    def test_ref_text_optional(self):
        prompt = VoicePrompt(
            embedding=None,
            ref_audio_path="/audio/ref.wav",
            ref_text=None,
            backend="vibe",
        )
        assert prompt.ref_text is None


class TestVoiceCloneResult:
    """Test VoiceCloneResult dataclass."""

    def test_create_result(self):
        audio = np.zeros(16000, dtype=np.float32)
        result = VoiceCloneResult(
            audio=audio,
            sample_rate=16000,
            model_name="qwen3-tts",
            generation_time_ms=150.0,
        )
        assert result.sample_rate == 16000
        assert result.model_name == "qwen3-tts"
        assert len(result.audio) == 16000

    def test_metadata_defaults_empty(self):
        audio = np.zeros(100, dtype=np.float32)
        result = VoiceCloneResult(
            audio=audio, sample_rate=24000,
            model_name="test", generation_time_ms=10.0,
        )
        assert result.metadata == {}


class TestVoiceCloningBackendABC:
    """Test that VoiceCloningBackend is abstract."""

    def test_is_abstract(self):
        with pytest.raises(TypeError):
            VoiceCloningBackend()

    def test_has_required_methods(self):
        assert hasattr(VoiceCloningBackend, "clone_voice")
        assert hasattr(VoiceCloningBackend, "create_voice_prompt")
        assert hasattr(VoiceCloningBackend, "load")
        assert hasattr(VoiceCloningBackend, "unload")
