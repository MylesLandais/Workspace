"""
Test model availability and basic functionality.
"""

import pytest
import tempfile
import numpy as np
import soundfile as sf
from pathlib import Path

from asr_evaluation.adapters.faster_whisper_adapter import FasterWhisperAdapter
from asr_evaluation.core.interfaces import TranscriptionResult, ModelInfo


class TestModelAvailability:
    """Test that models are available and can be loaded."""
    
    def test_faster_whisper_import(self):
        """Test that faster-whisper can be imported."""
        try:
            import faster_whisper
            assert True, "faster-whisper imported successfully"
        except ImportError:
            pytest.skip("faster-whisper not installed")
    
    def test_faster_whisper_adapter_creation(self):
        """Test that FasterWhisperAdapter can be created."""
        adapter = FasterWhisperAdapter(model_size="tiny")  # Use tiny for faster testing
        assert adapter is not None
        assert adapter.model_size == "tiny"
        assert adapter.device == "cpu"
    
    def test_model_info(self):
        """Test that model info is returned correctly."""
        adapter = FasterWhisperAdapter(model_size="tiny")
        info = adapter.get_model_info()
        
        assert isinstance(info, ModelInfo)
        assert info.name == "faster-whisper"
        assert info.version == "tiny"
        assert info.model_type == "local"
        assert info.supports_confidence is True
        assert info.supports_timestamps is True
    
    def test_model_availability_check(self):
        """Test that model availability can be checked."""
        adapter = FasterWhisperAdapter(model_size="tiny")
        
        # This will download the model if not available
        is_available = adapter.is_available()
        
        # Should be True if faster-whisper is installed
        if is_available:
            assert True, "Model is available"
        else:
            pytest.skip("Model not available - check installation")
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a temporary audio file for testing."""
        # Generate 3 seconds of sine wave at 16kHz
        sample_rate = 16000
        duration = 3.0
        frequency = 440  # A4 note
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            yield tmp_file.name
        
        # Cleanup
        Path(tmp_file.name).unlink(missing_ok=True)
    
    def test_basic_transcription(self, sample_audio_file):
        """Test basic transcription functionality."""
        adapter = FasterWhisperAdapter(model_size="tiny")
        
        # Skip if model not available
        if not adapter.is_available():
            pytest.skip("Model not available")
        
        # Transcribe the sample audio
        result = adapter.transcribe(sample_audio_file)
        
        # Verify result structure
        assert isinstance(result, TranscriptionResult)
        assert isinstance(result.text, str)
        assert result.processing_time > 0
        assert result.metadata is not None
        
        # The sine wave won't produce meaningful text, but should not crash
        print(f"Transcription result: '{result.text}'")
        print(f"Processing time: {result.processing_time:.2f}s")
    
    def test_file_not_found_error(self):
        """Test that FileNotFoundError is raised for missing files."""
        adapter = FasterWhisperAdapter(model_size="tiny")
        
        with pytest.raises(FileNotFoundError):
            adapter.transcribe("nonexistent_file.wav")


class TestConfigurationValidation:
    """Test configuration and interface validation."""
    
    def test_different_model_sizes(self):
        """Test that different model sizes can be configured."""
        sizes = ["tiny", "base", "small"]
        
        for size in sizes:
            adapter = FasterWhisperAdapter(model_size=size)
            assert adapter.model_size == size
            
            info = adapter.get_model_info()
            assert info.version == size
    
    def test_device_configuration(self):
        """Test device configuration options."""
        # Test CPU
        adapter_cpu = FasterWhisperAdapter(device="cpu")
        assert adapter_cpu.device == "cpu"
        
        # Test CUDA (if available)
        adapter_cuda = FasterWhisperAdapter(device="cuda")
        assert adapter_cuda.device == "cuda"
    
    def test_compute_type_configuration(self):
        """Test compute type configuration."""
        compute_types = ["int8", "float16", "float32"]
        
        for compute_type in compute_types:
            adapter = FasterWhisperAdapter(compute_type=compute_type)
            assert adapter.compute_type == compute_type


if __name__ == "__main__":
    # Run basic availability check
    print("Testing model availability...")
    
    adapter = FasterWhisperAdapter(model_size="tiny")
    
    print(f"Model info: {adapter.get_model_info()}")
    
    if adapter.is_available():
        print("✅ Model is available and ready!")
    else:
        print("❌ Model not available - check installation")