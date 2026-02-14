import os
from pathlib import Path
from huggingface_hub import hf_hub_download

# --- Configuration ---

# The Hugging Face repository ID
repo_id = "FoxBaze/Try_On_Qwen_Edit_Lora_Alpha"

# The specific filename you need from the repository
filename = "Try_On_Qwen_Edit_Lora.safetensors"

# The destination directory for LoRA models
destination_dir = Path("/workspace/ComfyUI/models/loras")

# --- Main Script ---

print(f"Downloading required LoRA: {filename}...")

# 1. Ensure the destination directory exists
destination_dir.mkdir(parents=True, exist_ok=True)
output_path = destination_dir / filename

# 2. Check if the file already exists
if output_path.exists():
    print(f"Skipping download, file already exists: {output_path}")
else:
    try:
        # 3. Download the correct file
        hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            local_dir=destination_dir,
            local_dir_use_symlinks=False, # Good practice for containers
        )
        print(f"\nSuccess! LoRA saved as: {output_path}")

    except Exception as e:
        print(f"\nAn error occurred: {e}")
        print("Please check the repository URL and your network connection.")