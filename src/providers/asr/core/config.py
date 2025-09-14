"""
Configuration management for ASR evaluation system.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
import os
import yaml
import json
from pathlib import Path


@dataclass
class ModelConfig:
    """Configuration for a single ASR model."""
    name: str
    model_id: str
    adapter_class: str
    wer_target: float
    use_case: str
    chunk_length: int = 30
    parameters: Dict[str, Any] = field(default_factory=dict)
    device_requirements: Dict[str, Any] = field(default_factory=dict)
    languages: Optional[List[str]] = None


@dataclass
class EvaluationConfig:
    """Configuration for evaluation runs."""

    # Model settings
    model_name: str = "faster-whisper"
    model_size: str = "base"

    # Evaluation settings
    batch_size: int = 1
    timeout_seconds: int = 300
    retry_attempts: int = 3

    # Output settings
    output_dir: str = "results"
    save_transcriptions: bool = True
    save_detailed_results: bool = True

    # Audio processing
    supported_formats: List[str] = field(default_factory=lambda: [".mp3", ".wav", ".m4a", ".webm"])
    max_audio_length: int = 3600  # seconds

    # Custom parameters
    custom_params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DatasetConfig:
    """Configuration for evaluation datasets."""

    name: str
    path: str
    reference_format: str = "json"  # "json", "txt", "csv"
    audio_dir: Optional[str] = None

    # Validation settings
    validate_audio: bool = True
    validate_references: bool = True


class ConfigManager:
    """Manages configuration loading and validation."""

    def __init__(self, config_path: Optional[str] = None, models_config_path: Optional[str] = None):
        self.config_path = config_path or "evaluation_config.json"
        self.models_config_path = models_config_path or "config/asr_models.yaml"
        self.evaluation_config = EvaluationConfig()
        self.datasets: Dict[str, DatasetConfig] = {}
        self.models: Dict[str, ModelConfig] = {}
        self._load_models_config()

    def _load_models_config(self) -> None:
        """Load ASR models configuration from YAML file."""
        try:
            if os.path.exists(self.models_config_path):
                with open(self.models_config_path, 'r') as f:
                    config_data = yaml.safe_load(f)

                # Load model configurations
                models_data = config_data.get('models', {})
                for model_key, model_data in models_data.items():
                    self.models[model_key] = ModelConfig(
                        name=model_data['name'],
                        model_id=model_data['model_id'],
                        adapter_class=model_data['adapter_class'],
                        wer_target=model_data['wer_target'],
                        use_case=model_data['use_case'],
                        chunk_length=model_data.get('chunk_length', 30),
                        parameters=model_data.get('parameters', {}),
                        device_requirements=model_data.get('device_requirements', {}),
                        languages=model_data.get('languages')
                    )

                # Store additional config sections
                self.processing_modes = config_data.get('processing_modes', {})
                self.model_selection = config_data.get('model_selection', {})
                self.evaluation_settings = config_data.get('evaluation', {})

                print(f"Loaded {len(self.models)} model configurations from {self.models_config_path}")
            else:
                print(f"Warning: Models config file not found: {self.models_config_path}")

        except Exception as e:
            print(f"Error loading models configuration: {e}")

    def load_config(self) -> EvaluationConfig:
        """Load configuration from file or return defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)

                # Update evaluation config with loaded values
                for key, value in config_data.items():
                    if hasattr(self.evaluation_config, key):
                        setattr(self.evaluation_config, key, value)

                print(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                print(f"Warning: Failed to load config from {self.config_path}: {e}")
                print("Using default configuration")

        return self.evaluation_config

    def get_model_config(self, model_key: str) -> Optional[ModelConfig]:
        """Get model configuration by key."""
        return self.models.get(model_key)

    def list_models(self) -> List[str]:
        """List all configured model keys."""
        return list(self.models.keys())

    def get_models_by_use_case(self, use_case: str) -> List[str]:
        """Get model keys filtered by use case."""
        return [key for key, config in self.models.items() if config.use_case == use_case]

    def get_preferred_models(self, use_case: str) -> List[str]:
        """Get preferred models for a specific use case."""
        preferences = self.model_selection.get(use_case, [])
        return [model for model in preferences if model in self.models]

    def get_fallback_models(self) -> List[str]:
        """Get fallback model order."""
        fallbacks = self.model_selection.get('fallback_order', [])
        return [model for model in fallbacks if model in self.models]

    def add_dataset(self, name: str, path: str, **kwargs) -> None:
        """Add a dataset configuration."""
        self.datasets[name] = DatasetConfig(name=name, path=path, **kwargs)

    def get_dataset(self, name: str) -> Optional[DatasetConfig]:
        """Get dataset configuration by name."""
        return self.datasets.get(name)

    def list_datasets(self) -> List[str]:
        """List all configured dataset names."""
        return list(self.datasets.keys())

    def get_benchmark_datasets(self) -> Dict[str, Any]:
        """Get benchmark dataset configurations."""
        return self.evaluation_settings.get('benchmark_datasets', {})
