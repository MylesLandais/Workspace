import os
from pathlib import Path
from huggingface_hub import hf_hub_download

# --- Configuration ---

# The Hugging Face repository ID
repo_id = "FoxBaze/Try_On_Qwen_Edit_Lora_Alpha"

# The ACTUAL filename in the repository that your workflow needs
filename_in_repo = "Multi_Ref_Try_on_qwen_edit_000002500.safetensors"

# We will keep the filename the same so ComfyUI can find it
output_filename = "Multi_Ref_Try_on_qwen_edit_000002500.safetensors"

# The destination directory for LoRA models
destination_dir = Path("/workspace/ComfyUI/models/loras")

# --- Main Script ---

print(f"Downloading required LoRA: {output_filename}...")

# 1. Ensure the destination directory exists
destination_dir.mkdir(parents=True, exist_ok=True)
output_path = destination_dir / output_filename

# 2. Check if the file already exists
if output_path.exists():
    print(f"Skipping download, file already exists: {output_path}")
else:
    try:
        # 3. Download the correct file
        hf_hub_download(
            repo_id=repo_id,
            filename=filename_in_repo,
            local_dir=destination_dir,
            local_filename=output_filename, # Save with the final name directly
        )
        print(f"\nSuccess! LoRA saved as: {output_path}")

    except TypeError:
        # Fallback for older huggingface_hub versions that don't have 'local_filename'
        try:
            print("Using legacy download method...")
            temp_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename_in_repo,
                local_dir=destination_dir
            )
            os.rename(temp_path, output_path)
            print(f"\nSuccess! LoRA saved as: {output_path} (legacy method)")
        except Exception as e_legacy:
            print(f"\nAn error occurred with the legacy method: {e_legacy}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")