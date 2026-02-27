"""
RunPod handler for Qwen3-TTS voice cloning.

This handler accepts text and reference audio, generates speech using Qwen3-TTS,
and returns the audio file as base64.

Input format:
{
    "input": {
        "text": "Text to synthesize",
        "reference_audio": "base64_encoded_audio_or_url",
        "reference_text": "optional transcript of reference",
        "language": "English",
        "model_size": "1.7B",
        "use_nf4": true
    }
}

Output format:
{
    "audio_base64": "base64_encoded_wav",
    "sample_rate": 24000,
    "duration_seconds": 12.5,
    "generation_time_ms": 2500
}
"""

import os
import sys
import base64
import tempfile
import time
from pathlib import Path
from io import BytesIO

def handler(event):
    """Main handler function for RunPod serverless."""
    
    # Parse input
    input_data = event.get("input", {})
    text = input_data.get("text", "")
    reference_audio_b64 = input_data.get("reference_audio", "")
    reference_text = input_data.get("reference_text", None)
    language = input_data.get("language", "English")
    model_size = input_data.get("model_size", "1.7B")
    use_nf4 = input_data.get("use_nf4", True)
    
    if not text:
        return {"error": "No text provided"}
    
    if not reference_audio_b64:
        return {"error": "No reference audio provided"}
    
    try:
        # Decode reference audio
        audio_bytes = base64.b64decode(reference_audio_b64)
        
        # Save to temp file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            tmp.write(audio_bytes)
            ref_audio_path = tmp.name
        
        # Import TTS backend
        from qwen_tts import Qwen3TTSModel
        import torch
        import numpy as np
        import soundfile as sf
        
        # Load model
        model_id = f"Qwen/Qwen3-TTS-12Hz-{model_size}-Base"
        
        if use_nf4:
            try:
                from transformers import BitsAndBytesConfig
                quantization_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.bfloat16,
                    bnb_4bit_use_double_quant=True,
                )
                model = Qwen3TTSModel.from_pretrained(
                    model_id,
                    quantization_config=quantization_config,
                    device_map="cuda:0",
                )
            except:
                model = Qwen3TTSModel.from_pretrained(
                    model_id,
                    torch_dtype=torch.bfloat16,
                    device_map="cuda:0",
                )
        else:
            model = Qwen3TTSModel.from_pretrained(
                model_id,
                torch_dtype=torch.bfloat16,
                device_map="cuda:0",
            )
        
        # Generate speech
        start = time.perf_counter()
        wavs, sr = model.generate_voice_clone(
            text=text,
            language=language,
            ref_audio=ref_audio_path,
            ref_text=reference_text,
            x_vector_only_mode=True,
        )
        elapsed_ms = (time.perf_counter() - start) * 1000
        
        # Clean up temp file
        os.unlink(ref_audio_path)
        
        # Convert to base64
        audio_array = np.array(wavs[0])
        buffer = BytesIO()
        sf.write(buffer, audio_array, sr, format="WAV")
        audio_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        duration_seconds = len(audio_array) / sr
        
        return {
            "audio_base64": audio_base64,
            "sample_rate": sr,
            "duration_seconds": duration_seconds,
            "generation_time_ms": elapsed_ms,
            "model_used": model_id,
        }
        
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    # Test locally
    import json
    
    test_event = {
        "input": {
            "text": "This is a test of the Qwen3-TTS voice cloning system.",
            "reference_audio": "",  # Would need actual base64 here
            "language": "English",
        }
    }
    
    result = handler(test_event)
    print(json.dumps(result, indent=2))
