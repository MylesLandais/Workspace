"""
Unit tests for CanaryQwenAdapter.
"""

import pytest
import tempfile
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import torch

# Handle optional dependencies gracefully
try:
    import soundfile as sf
    HAS_SOUNDFILE = True
except ImportError:
    HAS_SOUNDFILE = False
    sf = None

from asr_evaluation.adapters.canary_qwen_adapter import CanaryQwenAdapter
from asr_evaluation.core.interfaces import TranscriptionResult, ModelInfo


class TestCanaryQwenAdapterInitialization:
    """Test CanaryQwenAdapter initialization and configuration."""
    
    def test_default_initialization(self):
        """Test adapter creation with default parameters."""
        adapter = CanaryQwenAdapter()
        
        assert adapter.model_name == "nvidia/canary-qwen-2.5b"
        assert adapter.device in ["cpu", "cuda"]
        assert adapter._model is None
        assert adapter._processor is None
        
        # Check model info
        info = adapter.get_model_info()
        assert isinstance(info, ModelInfo)
        assert info.name == "canary-qwen"
        assert info.version == "2.5b"
        assert info.model_type == "local"
        assert info.supports_confidence is True
        assert info.supports_timestamps is False
        assert info.max_audio_length == 3600
    
    def test_custom_model_initialization(self):
        """Test adapter creation with custom model name."""
        custom_model = "custom/canary-model"
        adapter = CanaryQwenAdapter(model_name=custom_model)
        
        assert adapter.model_name == custom_model
    
    def test_device_selection(self):
        """Test device selection logic."""
        # Test explicit CPU
        adapter_cpu = CanaryQwenAdapter(device="cpu")
        assert adapter_cpu.device == "cpu"
        
        # Test explicit CUDA
        adapter_cuda = CanaryQwenAdapter(device="cuda")
        assert adapter_cuda.device == "cuda"
        
        # Test auto selection
        adapter_auto = CanaryQwenAdapter(device="auto")
        expected_device = "cuda" if torch.cuda.is_available() else "cpu"
        assert adapter_auto.device == expected_device
    
    def test_model_info_properties(self):
        """Test model info properties are correctly set."""
        adapter = CanaryQwenAdapter()
        info = adapter.get_model_info()
        
        assert info.name == "canary-qwen"
        assert info.version == "2.5b"
        assert info.model_type == "local"
        assert info.supports_confidence is True
        assert info.supports_timestamps is False
        assert info.max_audio_length == 3600


class TestCanaryQwenAdapterAvailability:
    """Test model availability detection and error handling."""
    
    def test_availability_with_missing_packages(self):
        """Test availability check when required packages are missing."""
        adapter = CanaryQwenAdapter()
        
        # Mock missing transformers
        with patch('builtins.__import__', side_effect=ImportError("No module named 'transformers'")):
            assert adapter.is_available() is False
    
    def test_availability_with_model_loading_failure(self):
        """Test availability check when model loading fails."""
        adapter = CanaryQwenAdapter()
        
        # Mock model loading failure
        with patch.object(adapter, '_load_model', side_effect=RuntimeError("Model loading failed")):
            assert adapter.is_available() is False
    
    @patch('asr_evaluation.adapters.canary_qwen_adapter.torch')
    @patch('asr_evaluation.adapters.canary_qwen_adapter.torchaudio')
    def test_availability_success(self, mock_torchaudio, mock_torch):
        """Test successful availability check."""
        adapter = CanaryQwenAdapter()
        
        # Mock successful imports and model loading
        with patch.object(adapter, '_load_model', return_value=None):
            assert adapter.is_available() is True
    
    def test_transformers_version_check(self):
        """Test that transformers version is checked during availability."""
        adapter = CanaryQwenAdapter()
        
        with patch('transformers.__version__', '4.30.0'):
            with patch.object(adapter, '_load_model', return_value=None):
                # Should not raise an error with compatible version
                result = adapter.is_available()
                assert isinstance(result, bool)


class TestCanaryQwenAdapterModelLoading:
    """Test model loading functionality and fallback mechanisms."""
    
    def test_nemo_model_loading_success(self):
        """Test successful NeMo model loading."""
        adapter = CanaryQwenAdapter()
        
        # Mock NeMo import and model
        mock_nemo_asr = Mock()
        mock_model = Mock()
        mock_nemo_asr.models.EncDecRNNTBPEModel.from_pretrained.return_value = mock_model
        
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'nemo.collections.asr':
                    return mock_nemo_asr
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            adapter._load_model()
            
            assert adapter._model == mock_model
            assert adapter._processor is None  # NeMo handles preprocessing internally
    
    def test_transformers_fallback_loading(self):
        """Test fallback to transformers when NeMo fails."""
        adapter = CanaryQwenAdapter()
        
        # Mock transformers components
        mock_processor = Mock()
        mock_model = Mock()
        
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if 'nemo' in name:
                    raise ImportError("No module named 'nemo'")
                elif name == 'transformers':
                    mock_transformers = Mock()
                    mock_transformers.AutoProcessor.from_pretrained.return_value = mock_processor
                    mock_transformers.AutoModelForSpeechSeq2Seq.from_pretrained.return_value = mock_model
                    return mock_transformers
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            with patch('transformers.AutoProcessor') as mock_proc_class:
                with patch('transformers.AutoModelForSpeechSeq2Seq') as mock_model_class:
                    mock_proc_class.from_pretrained.return_value = mock_processor
                    mock_model_class.from_pretrained.return_value = mock_model
                    
                    adapter._load_model()
                    
                    assert adapter._processor == mock_processor
                    assert adapter._model == mock_model
                    mock_model.to.assert_called_once_with(adapter.device)
    
    def test_canary_model_fallback_to_whisper(self):
        """Test fallback to Whisper when Canary model is incompatible."""
        adapter = CanaryQwenAdapter(model_name="nvidia/canary-qwen-2.5b")
        
        # Mock transformers components
        mock_processor = Mock()
        mock_model = Mock()
        
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if 'nemo' in name:
                    raise ImportError("No module named 'nemo'")
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            with patch('transformers.AutoProcessor') as mock_proc_class:
                with patch('transformers.AutoModelForSpeechSeq2Seq') as mock_model_class:
                    mock_proc_class.from_pretrained.return_value = mock_processor
                    mock_model_class.from_pretrained.return_value = mock_model
                    
                    adapter._load_model()
                    
                    # Should fallback to Whisper Large v3
                    assert adapter.model_name == "openai/whisper-large-v3"
                    assert adapter._model_info.name == "whisper-large-v3-fallback"
                    assert adapter._model_info.version == "large-v3"
    
    def test_model_loading_error_handling(self):
        """Test error handling during model loading."""
        adapter = CanaryQwenAdapter()
        
        # Mock import error for transformers
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if name == 'transformers':
                    raise ImportError("Missing package")
                elif 'nemo' in name:
                    raise ImportError("No module named 'nemo'")
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            with pytest.raises(ImportError, match="Required packages not installed"):
                adapter._load_model()
        
        # Mock general loading error
        with patch('builtins.__import__') as mock_import:
            def import_side_effect(name, *args, **kwargs):
                if 'nemo' in name:
                    raise ImportError("No module named 'nemo'")
                return __import__(name, *args, **kwargs)
            
            mock_import.side_effect = import_side_effect
            
            with patch('transformers.AutoProcessor') as mock_proc:
                mock_proc.from_pretrained.side_effect = RuntimeError("Loading failed")
                
                with pytest.raises(RuntimeError, match="Failed to load model"):
                    adapter._load_model()


class TestCanaryQwenAdapterAudioProcessing:
    """Test audio loading and preprocessing functionality."""
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a temporary audio file for testing."""
        if not HAS_SOUNDFILE:
            pytest.skip("soundfile not available - install with: pip install soundfile")
        
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
    
    @pytest.fixture
    def stereo_audio_file(self):
        """Create a temporary stereo audio file for testing."""
        if not HAS_SOUNDFILE:
            pytest.skip("soundfile not available - install with: pip install soundfile")
        
        sample_rate = 16000
        duration = 2.0
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        # Create stereo audio (2 channels)
        left_channel = 0.3 * np.sin(2 * np.pi * frequency * t)
        right_channel = 0.3 * np.sin(2 * np.pi * frequency * 1.5 * t)
        stereo_audio = np.stack([left_channel, right_channel])
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            sf.write(tmp_file.name, stereo_audio.T, sample_rate)  # Transpose for soundfile
            yield tmp_file.name
        
        Path(tmp_file.name).unlink(missing_ok=True)
    
    def test_audio_loading_mono(self, sample_audio_file):
        """Test loading mono audio file."""
        adapter = CanaryQwenAdapter()
        
        waveform = adapter._load_audio(sample_audio_file)
        
        assert isinstance(waveform, torch.Tensor)
        assert waveform.dim() == 1  # Should be 1D for mono
        assert len(waveform) == 48000  # 3 seconds at 16kHz
    
    def test_audio_loading_stereo_to_mono(self, stereo_audio_file):
        """Test conversion of stereo audio to mono."""
        adapter = CanaryQwenAdapter()
        
        waveform = adapter._load_audio(stereo_audio_file)
        
        assert isinstance(waveform, torch.Tensor)
        assert waveform.dim() == 1  # Should be converted to mono
        assert len(waveform) == 32000  # 2 seconds at 16kHz
    
    @pytest.fixture
    def high_sample_rate_audio_file(self):
        """Create audio file with high sample rate for resampling test."""
        if not HAS_SOUNDFILE:
            pytest.skip("soundfile not available - install with: pip install soundfile")
        
        sample_rate = 44100  # CD quality
        duration = 1.0
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            yield tmp_file.name
        
        Path(tmp_file.name).unlink(missing_ok=True)
    
    def test_audio_resampling(self, high_sample_rate_audio_file):
        """Test audio resampling to 16kHz."""
        adapter = CanaryQwenAdapter()
        
        waveform = adapter._load_audio(high_sample_rate_audio_file)
        
        assert isinstance(waveform, torch.Tensor)
        assert len(waveform) == 16000  # 1 second at 16kHz (resampled from 44.1kHz)
    
    def test_audio_loading_file_not_found(self):
        """Test error handling for missing audio files."""
        adapter = CanaryQwenAdapter()
        
        with pytest.raises(RuntimeError, match="Failed to load audio file"):
            adapter._load_audio("nonexistent_file.wav")


class TestCanaryQwenAdapterTranscription:
    """Test transcription functionality and error handling."""
    
    @pytest.fixture
    def sample_audio_file(self):
        """Create a temporary audio file for testing."""
        if not HAS_SOUNDFILE:
            pytest.skip("soundfile not available - install with: pip install soundfile")
        
        sample_rate = 16000
        duration = 3.0
        frequency = 440
        
        t = np.linspace(0, duration, int(sample_rate * duration))
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t)
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            sf.write(tmp_file.name, audio_data, sample_rate)
            yield tmp_file.name
        
        Path(tmp_file.name).unlink(missing_ok=True)
    
    def test_transcribe_file_not_found(self):
        """Test transcription with missing file."""
        adapter = CanaryQwenAdapter()
        
        with pytest.raises(FileNotFoundError, match="Audio file not found"):
            adapter.transcribe("nonexistent_file.wav")
    
    def test_transcribe_with_nemo_model(self, sample_audio_file):
        """Test transcription using NeMo model."""
        adapter = CanaryQwenAdapter()
        
        # Mock NeMo model with transcribe method
        mock_model = Mock()
        mock_model.transcribe.return_value = ["This is a test transcription."]
        
        # Mock the model loading to use NeMo
        adapter._model = mock_model
        adapter._processor = None  # NeMo doesn't use processor
        
        result = adapter.transcribe(sample_audio_file)
        
        assert isinstance(result, TranscriptionResult)
        assert result.text == "This is a test transcription."
        assert result.processing_time > 0
        assert result.metadata["model_type"] == "nemo"
        assert result.metadata["model_name"] == adapter.model_name
        assert result.metadata["device"] == adapter.device
        assert result.metadata["audio_file"] == sample_audio_file
    
    def test_transcribe_with_transformers_model(self, sample_audio_file):
        """Test transcription using transformers model."""
        adapter = CanaryQwenAdapter()
        
        # Mock transformers components
        mock_processor = Mock()
        mock_model = Mock()
        
        # Mock processor inputs
        mock_inputs = {"input_features": torch.randn(1, 80, 3000)}
        mock_processor.return_value = mock_inputs
        mock_processor.batch_decode.return_value = ["This is a transformers transcription."]
        
        # Mock model outputs
        mock_outputs = Mock()
        mock_outputs.sequences = torch.tensor([[1, 2, 3, 4]])
        mock_outputs.scores = [torch.randn(1, 1000)]  # Mock logits for confidence
        mock_model.generate.return_value = mock_outputs
        
        # Set up the adapter with mocked components
        adapter._processor = mock_processor
        adapter._model = mock_model
        
        result = adapter.transcribe(sample_audio_file)
        
        assert isinstance(result, TranscriptionResult)
        assert result.text == "This is a transformers transcription."
        assert result.processing_time > 0
        assert result.metadata["device"] == adapter.device
        assert "audio_duration" in result.metadata
        assert "sample_rate" in result.metadata
        assert result.metadata["language"] == "en"
        assert result.metadata["task"] == "transcribe"
    
    def test_transcribe_with_custom_parameters(self, sample_audio_file):
        """Test transcription with custom language and task parameters."""
        adapter = CanaryQwenAdapter()
        
        # Mock the model loading and transcription
        with patch.object(adapter, '_load_model'):
            with patch.object(adapter, '_load_audio', return_value=torch.randn(48000)):
                mock_processor = Mock()
                mock_processor.return_value = {"input_features": torch.randn(1, 80, 3000)}
                mock_processor.batch_decode.return_value = ["Spanish transcription"]
                adapter._processor = mock_processor
                
                mock_model = Mock()
                mock_outputs = Mock()
                mock_outputs.sequences = torch.tensor([[1, 2, 3]])
                mock_outputs.scores = []
                mock_model.generate.return_value = mock_outputs
                adapter._model = mock_model
                
                result = adapter.transcribe(sample_audio_file, language="es", task="translate")
        
        assert result.metadata["language"] == "es"
        assert result.metadata["task"] == "translate"
    
    def test_confidence_score_extraction(self):
        """Test confidence score extraction from model outputs."""
        adapter = CanaryQwenAdapter()
        
        # Mock outputs with scores
        mock_outputs = Mock()
        mock_outputs.scores = [
            torch.tensor([[0.1, 0.8, 0.1]]),  # High confidence for token 1
            torch.tensor([[0.3, 0.4, 0.3]])   # Lower confidence for token 2
        ]
        
        confidence_scores = adapter._extract_confidence_scores(mock_outputs, None)
        
        assert confidence_scores is not None
        assert len(confidence_scores) == 2
        assert confidence_scores[0] > confidence_scores[1]  # First should be higher confidence
    
    def test_confidence_score_extraction_no_scores(self):
        """Test confidence score extraction when no scores available."""
        adapter = CanaryQwenAdapter()
        
        # Mock outputs without scores
        mock_outputs = Mock()
        mock_outputs.scores = None
        
        confidence_scores = adapter._extract_confidence_scores(mock_outputs, None)
        
        assert confidence_scores is None
    
    def test_transcription_error_handling(self, sample_audio_file):
        """Test error handling during transcription."""
        adapter = CanaryQwenAdapter()
        
        # Mock model loading failure
        with patch.object(adapter, '_load_model', side_effect=RuntimeError("Model loading failed")):
            with pytest.raises(RuntimeError, match="Model loading failed"):
                adapter.transcribe(sample_audio_file)
        
        # Mock audio loading failure
        with patch.object(adapter, '_load_model'):
            with patch.object(adapter, '_load_audio', side_effect=RuntimeError("Audio loading failed")):
                with pytest.raises(RuntimeError, match="Transcription failed"):
                    adapter.transcribe(sample_audio_file)


class TestCanaryQwenAdapterIntegration:
    """Integration tests for CanaryQwenAdapter with real Vaporeon dataset."""
    
    def test_vaporeon_audio_file_exists(self):
        """Test that Vaporeon audio file exists for integration testing."""
        vaporeon_audio = Path("evaluation_datasets/vaporeon/-EWMgB26bmU_Vaporeon copypasta (animated).mp3")
        
        if not vaporeon_audio.exists():
            pytest.skip(f"Vaporeon audio file not found: {vaporeon_audio}")
        
        assert vaporeon_audio.exists()
        assert vaporeon_audio.suffix == ".mp3"
    
    def test_vaporeon_reference_transcript_exists(self):
        """Test that Vaporeon reference transcript exists."""
        reference_file = Path("evaluation_datasets/vaporeon/reference_transcript.txt")
        
        if not reference_file.exists():
            pytest.skip(f"Vaporeon reference transcript not found: {reference_file}")
        
        assert reference_file.exists()
        
        with open(reference_file, 'r') as f:
            reference_text = f.read().strip()
        
        assert len(reference_text) > 0
        assert "Vaporeon" in reference_text
        print(f"Reference transcript length: {len(reference_text)} characters")
        print(f"Reference word count: {len(reference_text.split())} words")
    
    @pytest.mark.integration
    def test_canary_qwen_vaporeon_transcription(self):
        """Integration test: Transcribe Vaporeon audio with CanaryQwen."""
        vaporeon_audio = Path("evaluation_datasets/vaporeon/-EWMgB26bmU_Vaporeon copypasta (animated).mp3")
        reference_file = Path("evaluation_datasets/vaporeon/reference_transcript.txt")
        
        # Skip if files don't exist
        if not vaporeon_audio.exists():
            pytest.skip(f"Vaporeon audio file not found: {vaporeon_audio}")
        if not reference_file.exists():
            pytest.skip(f"Reference transcript not found: {reference_file}")
        
        # Load reference text
        with open(reference_file, 'r') as f:
            reference_text = f.read().strip()
        
        # Create adapter and test availability
        adapter = CanaryQwenAdapter()
        
        if not adapter.is_available():
            pytest.skip("CanaryQwen model not available - check installation")
        
        # Perform transcription
        result = adapter.transcribe(str(vaporeon_audio))
        
        # Validate result structure
        assert isinstance(result, TranscriptionResult)
        assert isinstance(result.text, str)
        assert len(result.text) > 0
        assert result.processing_time > 0
        assert result.metadata is not None
        
        # Calculate basic metrics for comparison
        predicted_words = result.text.lower().split()
        reference_words = reference_text.lower().split()
        
        # Simple word overlap check (not full WER calculation)
        common_words = set(predicted_words) & set(reference_words)
        word_overlap_ratio = len(common_words) / len(reference_words) if reference_words else 0
        
        print(f"\nCanary Qwen Vaporeon Transcription Results:")
        print(f"Reference length: {len(reference_text)} chars, {len(reference_words)} words")
        print(f"Predicted length: {len(result.text)} chars, {len(predicted_words)} words")
        print(f"Processing time: {result.processing_time:.2f}s")
        print(f"Word overlap ratio: {word_overlap_ratio:.2%}")
        print(f"Predicted text (first 100 chars): {result.text[:100]}...")
        
        # Basic quality checks
        assert len(predicted_words) > 10, "Transcription too short"
        assert word_overlap_ratio > 0.1, "Too few words match reference"
        
        # Check for key terms that should be present
        key_terms = ["vaporeon", "pokemon", "human", "breeding"]
        predicted_lower = result.text.lower()
        
        found_terms = [term for term in key_terms if term in predicted_lower]
        print(f"Key terms found: {found_terms}")
        
        # Should find at least some key terms
        assert len(found_terms) >= 1, f"Expected key terms not found in transcription"


if __name__ == "__main__":
    # Run basic tests
    print("Running CanaryQwen adapter tests...")
    
    # Test initialization
    adapter = CanaryQwenAdapter()
    print(f"✅ Adapter created: {adapter.model_name}")
    
    # Test model info
    info = adapter.get_model_info()
    print(f"✅ Model info: {info.name} v{info.version}")
    
    # Test availability
    if adapter.is_available():
        print("✅ Model is available!")
    else:
        print("❌ Model not available - check installation")
    
    print("Run with pytest for full test suite: pytest tests/test_canary_qwen_adapter.py -v")