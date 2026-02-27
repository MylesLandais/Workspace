
import sys
import time
import torch
import soundfile as sf
from pathlib import Path

# Add src/tts/scheduler to Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from lib.tts.adapters import get_adapter

WORKSPACE = Path(__file__).resolve().parent.parent.parent
REF_AUDIO = WORKSPACE / "data" / "inputs" / "voices" / "26-emma-jayshettypodcast.wav"
OUTPUT_DIR = WORKSPACE / "data" / "outputs" / "tts"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TEXT = "Hello world. This is a test."

def generate_moss(timestamp):
    print(f"\n--- Generating MOSS-TTS ({timestamp}) ---")
    try:
        backend = get_adapter("moss-tts") # Auto-detects device
        print(f"Loading {backend.name} on {backend.device}...")
        backend.load()
        
        start = time.perf_counter()
        result = backend.clone_voice(text=TEXT, ref_audio=str(REF_AUDIO))
        duration = time.perf_counter() - start
        
        output_file = OUTPUT_DIR / f"{timestamp}-moss-emma-vaporeon.wav"
        sf.write(str(output_file), result.audio, result.sample_rate)
        
        print(f"MOSS Generation took: {duration:.2f}s")
        print(f"Saved to {output_file}")
        
        backend.unload()
        del backend
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            
    except Exception as e:
        print(f"MOSS-TTS failed: {e}")
        import traceback
        traceback.print_exc()

def generate_qwen(timestamp):
    print(f"\n--- Generating Qwen3-TTS ({timestamp}) ---")
    try:
        # Check if we can import qwen_tts
        try:
            import qwen_tts
        except ImportError:
            print("qwen_tts not installed. Skipping Qwen generation.")
            return

        # Force CPU if CUDA not available (Qwen backend patched to support device arg)
        device = "cuda" if torch.cuda.is_available() else "cpu"
        # Disable NF4/FlashAttn on CPU
        use_nf4 = False if device == "cpu" else True
        use_flash_attn = False if device == "cpu" else True
        
        backend = get_adapter(
            "qwen3tts",
            model_size="1.7B", # Use smaller model for test
            use_nf4=use_nf4,
            use_flash_attn=use_flash_attn,
            device=device
        )
        print(f"Loading {backend.name} on {backend.device}...")
        backend.load()
        
        start = time.perf_counter()
        # x_vector_only_mode=False for better cloning? Demo used True. Let's use False for better quality if possible, or True if faster/stable.
        # Actually demo used True. Let's stick to default (False) or True?
        # Demo comment: "qwen_result = qwen.clone_voice(test_text, larry_voice, x_vector_only_mode=True)"
        # I'll use True to match demo.
        result = backend.clone_voice(text=TEXT, ref_audio=str(REF_AUDIO), x_vector_only_mode=True)
        duration = time.perf_counter() - start
        
        output_file = OUTPUT_DIR / f"{timestamp}-qwen-emma-vaporeon.wav"
        sf.write(str(output_file), result.audio, result.sample_rate)
        
        print(f"Qwen Generation took: {duration:.2f}s")
        print(f"Saved to {output_file}")
        
        backend.unload()
        del backend
        if torch.cuda.is_available():
            torch.cuda.empty_cache()

    except Exception as e:
        print(f"Qwen3-TTS failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    if not REF_AUDIO.exists():
        print(f"Error: Reference audio not found at {REF_AUDIO}")
        return

    timestamp = time.strftime("%Y%m%d%H%M")
    
    if len(sys.argv) > 1:
        target = sys.argv[1].lower()
        if target == "moss":
            generate_moss(timestamp)
        elif target == "qwen":
            generate_qwen(timestamp)
        else:
            print(f"Unknown target: {target}")
    else:
        generate_moss(timestamp)
        generate_qwen(timestamp)

if __name__ == "__main__":
    main()
