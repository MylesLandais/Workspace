import os
from pathlib import Path
from huggingface_hub import hf_hub_download
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Configuration ---
# Define the base path for your ComfyUI models directory
COMFYUI_MODELS_BASE = Path("/workspace/ComfyUI/models")

# List of the missing models you need to download
MODELS_TO_DOWNLOAD = [
    {
        "repo_id": "Comfy-Org/Qwen-Image-Edit_ComfyUI",
        "repo_filename": "split_files/diffusion_models/qwen_image_edit_fp8_e4m3fn.safetensors",
        "destination_dir": COMFYUI_MODELS_BASE / "diffusion_models"
    },
    {
        "repo_id": "Comfy-Org/Qwen-Image_ComfyUI",
        "repo_filename": "split_files/vae/qwen_image_vae.safetensors",
        "destination_dir": COMFYUI_MODELS_BASE / "vae"
    },
    {
        "repo_id": "Comfy-Org/Qwen-Image_ComfyUI",
        "repo_filename": "split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors",
        "destination_dir": COMFYUI_MODELS_BASE / "text_encoders"
    }
]

# --- Worker Function (executed by each thread) ---
def download_model(dep):
    repo_id = dep["repo_id"]
    repo_filename = dep["repo_filename"]
    destination_dir = dep["destination_dir"]
    
    local_filename = Path(repo_filename).name
    output_path = destination_dir / local_filename

    # Ensure the destination directory exists (this is thread-safe)
    destination_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if the file already exists to avoid re-downloading
    if output_path.exists():
        return f"Skipped: {local_filename} already exists."

    try:
        # Download the file
        temp_path = hf_hub_download(
            repo_id=repo_id,
            filename=repo_filename,
            local_dir=destination_dir,
            local_dir_use_symlinks=False, # Essential for ephemeral containers
            resume_download=True
        )
        # Rename if the library downloaded it to a different final location
        if str(temp_path) != str(output_path):
            os.rename(temp_path, output_path)
        return f"Success: Downloaded {local_filename}"
        
    except Exception as e:
        return f"ERROR downloading {local_filename}: {e}"

# --- Main Script ---
print("Starting quick download of missing models...")

# Use a ThreadPoolExecutor to run all download jobs in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    # Submit all download tasks
    future_to_dep = {executor.submit(download_model, dep): dep for dep in MODELS_TO_DOWNLOAD}
    
    # Print results as each download completes
    for future in as_completed(future_to_dep):
        result = future.result()
        print(result)

print("\nScript finished. All specified models are processed.")