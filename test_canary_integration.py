#!/usr/bin/env python3
"""
Test script for Canary Qwen integration with ASR evaluation system.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from asr_evaluation.adapters.canary_qwen_adapter import CanaryQwenAdapter
from asr_evaluation.core.config import ConfigManager

def test_canary_qwen_integration():
    """Test Canary Qwen integration with the ASR evaluation system."""
    print('Testing Canary Qwen integration...')
    
    # Test config manager
    try:
        config_manager = ConfigManager()
        canary_config = config_manager.get_model_config('canary_qwen')
        
        if canary_config:
            print(f'✅ Canary Qwen config loaded successfully:')
            print(f'  Model ID: {canary_config.model_id}')
            print(f'  WER Target: {canary_config.wer_target}%')
            print(f'  Use Case: {canary_config.use_case}')
            print(f'  Adapter Class: {canary_config.adapter_class}')
        else:
            print('❌ ERROR: Canary Qwen config not found')
            return False
            
    except Exception as e:
        print(f'❌ ERROR loading config: {e}')
        return False
    
    # Test adapter creation (without loading model)
    try:
        adapter = CanaryQwenAdapter()
        model_info = adapter.get_model_info()
        print(f'✅ Adapter created successfully:')
        print(f'  Name: {model_info.name}')
        print(f'  Version: {model_info.version}')
        print(f'  Model Type: {model_info.model_type}')
        print(f'  Supports confidence: {model_info.supports_confidence}')
        print(f'  Max audio length: {model_info.max_audio_length}s')
        
    except Exception as e:
        print(f'❌ ERROR creating adapter: {e}')
        return False
    
    # Test model availability check (without actually loading)
    print(f'\n🔍 Testing model availability...')
    try:
        # This will check dependencies but not load the full model
        import transformers
        import torch
        import torchaudio
        print(f'✅ Required dependencies available:')
        print(f'  transformers: {transformers.__version__}')
        print(f'  torch: {torch.__version__}')
        print(f'  CUDA available: {torch.cuda.is_available()}')
        
    except ImportError as e:
        print(f'❌ Missing dependencies: {e}')
        return False
    
    print(f'\n✅ Integration test completed successfully!')
    print(f'🎯 Canary Qwen is ready for Vaporeon evaluation')
    return True

if __name__ == "__main__":
    success = test_canary_qwen_integration()
    sys.exit(0 if success else 1)