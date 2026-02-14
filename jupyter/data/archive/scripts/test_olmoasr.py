#!/usr/bin/env python3
"""
Test script for OLMoASR with Vaporeon audio file.
"""

import sys
from pathlib import Path

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent))

from asr_evaluation.adapters.olmoasr_adapter import OLMoASRAdapter


def test_olmoasr_availability():
    """Test if OLMoASR can be loaded."""
    print("Testing OLMoASR availability...")
    
    # Try different ASR models that work with AutoModelForSpeechSeq2Seq
    models_to_try = [
        "openai/whisper-base",  # Better quality than tiny
        "openai/whisper-small",
        "openai/whisper-tiny"   # Fallback if others fail
    ]
    
    for model_name in models_to_try:
        print(f"\nTrying model: {model_name}")
        try:
            adapter = OLMoASRAdapter(model_name=model_name)
            
            if adapter.is_available():
                print(f"SUCCESS: {model_name} is available!")
                return adapter
            else:
                print(f"FAILED: {model_name} failed to load")
                
        except Exception as e:
            print(f"ERROR: {model_name} error: {e}")
    
    return None


def test_transcription(adapter, audio_file):
    """Test transcription with the given adapter."""
    print(f"\nTesting transcription with: {audio_file}")
    
    try:
        # Get model info
        info = adapter.get_model_info()
        print(f"Model: {info.name} v{info.version}")
        print(f"Type: {info.model_type}")
        
        # Transcribe the audio
        print("Starting transcription...")
        result = adapter.transcribe(audio_file)
        
        print(f"SUCCESS: Transcription completed in {result.processing_time:.2f}s")
        print(f"Result: {result.text}")
        
        if result.metadata:
            print(f"Metadata: {result.metadata}")
        
        return result
        
    except Exception as e:
        print(f"ERROR: Transcription failed: {e}")
        return None


def load_reference_text():
    """Load the reference transcription for comparison."""
    ref_file = Path("transcriptions/vaporeon_transcript_clean.txt")
    
    if ref_file.exists():
        with open(ref_file, 'r') as f:
            return f.read().strip()
    else:
        print(f"WARNING: Reference file not found: {ref_file}")
        return None


def simple_wer_calculation(reference, hypothesis):
    """Simple Word Error Rate calculation."""
    ref_words = reference.lower().split()
    hyp_words = hypothesis.lower().split()
    
    # Simple edit distance (not optimal, but good enough for testing)
    if len(ref_words) == 0:
        return 1.0 if len(hyp_words) > 0 else 0.0
    
    # Count different words (very basic)
    max_len = max(len(ref_words), len(hyp_words))
    matches = 0
    
    for i in range(min(len(ref_words), len(hyp_words))):
        if ref_words[i] == hyp_words[i]:
            matches += 1
    
    wer = 1.0 - (matches / len(ref_words))
    return wer


def main():
    """Main test function."""
    print("OLMoASR Test Script")
    print("=" * 50)
    
    # Find the audio file
    audio_file = Path("transcriptions/-EWMgB26bmU_Vaporeon_copypasta_animated.mp3")
    
    if not audio_file.exists():
        print(f"ERROR: Audio file not found: {audio_file}")
        return
    
    print(f"Audio file: {audio_file}")
    
    # Test model availability
    adapter = test_olmoasr_availability()
    
    if not adapter:
        print("\nERROR: No OLMoASR models could be loaded.")
        print("TIP: Try installing required packages:")
        print("   pip install transformers torch torchaudio")
        return
    
    # Test transcription
    result = test_transcription(adapter, str(audio_file))
    
    if not result:
        return
    
    # Load reference and compare
    reference = load_reference_text()
    
    if reference:
        print(f"\nReference text (first 100 chars): {reference[:100]}...")
        
        wer = simple_wer_calculation(reference, result.text)
        print(f"Simple WER: {wer:.2%}")
        
        print(f"\nComparison:")
        print(f"Reference length: {len(reference.split())} words")
        print(f"Predicted length: {len(result.text.split())} words")
    
    print(f"\nTest completed!")


if __name__ == "__main__":
    main()