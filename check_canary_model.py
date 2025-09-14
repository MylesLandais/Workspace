#!/usr/bin/env python3
"""
Check if the Canary Qwen model exists and what the correct model ID should be.
"""

import requests
from huggingface_hub import list_models, model_info

def check_nvidia_models():
    """Check available NVIDIA models on HuggingFace."""
    print("Searching for NVIDIA Canary models on HuggingFace...")
    
    try:
        # Search for NVIDIA models containing "canary"
        models = list_models(author="nvidia", search="canary")
        
        canary_models = []
        for model in models:
            if "canary" in model.modelId.lower():
                canary_models.append(model.modelId)
        
        if canary_models:
            print(f"Found {len(canary_models)} Canary models:")
            for model_id in canary_models:
                print(f"  - {model_id}")
                
                # Get model info
                try:
                    info = model_info(model_id)
                    print(f"    Tags: {info.tags}")
                    print(f"    Pipeline: {getattr(info, 'pipeline_tag', 'N/A')}")
                    print()
                except Exception as e:
                    print(f"    Error getting info: {e}")
                    print()
        else:
            print("No Canary models found from NVIDIA")
            
        # Also search for any canary models
        print("\nSearching for all Canary models...")
        all_canary = list_models(search="canary")
        
        asr_canary_models = []
        for model in all_canary:
            if any(tag in getattr(model, 'tags', []) for tag in ['automatic-speech-recognition', 'speech', 'asr']):
                asr_canary_models.append(model.modelId)
        
        if asr_canary_models:
            print(f"Found {len(asr_canary_models)} ASR Canary models:")
            for model_id in asr_canary_models[:10]:  # Limit to first 10
                print(f"  - {model_id}")
        
    except Exception as e:
        print(f"Error searching models: {e}")

def check_specific_model(model_id):
    """Check if a specific model exists and get its details."""
    print(f"\nChecking specific model: {model_id}")
    
    try:
        info = model_info(model_id)
        print(f"✅ Model exists!")
        print(f"  Tags: {info.tags}")
        print(f"  Pipeline: {getattr(info, 'pipeline_tag', 'N/A')}")
        print(f"  Library: {getattr(info, 'library_name', 'N/A')}")
        
        # Check if it has the required files
        files = [f.rfilename for f in info.siblings]
        print(f"  Files: {len(files)} total")
        
        required_files = ['config.json', 'preprocessor_config.json', 'tokenizer_config.json']
        for req_file in required_files:
            if req_file in files:
                print(f"    ✅ {req_file}")
            else:
                print(f"    ❌ {req_file} (missing)")
        
        return True
        
    except Exception as e:
        print(f"❌ Model not found or error: {e}")
        return False

if __name__ == "__main__":
    check_nvidia_models()
    
    # Check the specific model we're trying to use
    check_specific_model("nvidia/canary-qwen-2.5b")
    
    # Check some alternative model IDs
    alternatives = [
        "nvidia/canary-1b",
        "nvidia/parakeet-tdt-1.1b",
        "nvidia/parakeet-ctc-1.1b",
        "microsoft/speecht5_asr",
        "openai/whisper-large-v3"
    ]
    
    print(f"\nChecking alternative models:")
    for alt in alternatives:
        check_specific_model(alt)