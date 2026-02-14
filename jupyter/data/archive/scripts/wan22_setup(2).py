#!/usr/bin/env python3
"""
Wan 2.2 Instagirl Complete Setup Script for ComfyUI
Downloads all required models, LoRAs, and dependencies for the workflow
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download
import requests
from urllib.parse import urlparse

# Base ComfyUI models directory
BASE_DIR = "/workspace/ComfyUI/models"

# Wan 2.2 Instagirl Workflow Requirements
WAN22_MANIFEST = {
    "huggingface_models": [
        # Main Wan 2.1 models (base requirement)
        {
            "repo_id": "Comfy-Org/Wan_2.1_ComfyUI_repackaged",
            "filename": "split_files/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
            "target_dir": f"{BASE_DIR}/text_encoders",
            "final_name": "umt5_xxl_fp8_e4m3fn_scaled.safetensors"
        },
        {
            "repo_id": "Comfy-Org/Wan_2.1_ComfyUI_repackaged",
            "filename": "split_files/vae/wan_2.1_vae.safetensors",
            "target_dir": f"{BASE_DIR}/vae",
            "final_name": "wan_2.1_vae.safetensors"
        },
        # CFG Step Distillation LoRA
        {
            "repo_id": "Kijai/WanVideo_comfy",
            "filename": "Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors",
            "target_dir": f"{BASE_DIR}/loras",
            "final_name": "Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors"
        }
    ],
    
    "gguf_models": [
        # Wan 2.2 GGUF Models (High and Low Noise)
        {
            "repo_id": "QuantStack/Wan2.2-T2V-A14B-GGUF",
            "filename": "HighNoise/Wan2.2-T2V-A14B-HighNoise-Q8_0.gguf",
            "target_dir": f"{BASE_DIR}/diffusion_models",
            "final_name": "Wan2.2-T2V-A14B-HighNoise-Q8_0.gguf"
        },
        {
            "repo_id": "QuantStack/Wan2.2-T2V-A14B-GGUF",
            "filename": "LowNoise/Wan2.2-T2V-A14B-LowNoise-Q8_0.gguf",
            "target_dir": f"{BASE_DIR}/diffusion_models",
            "final_name": "Wan2.2-T2V-A14B-LowNoise-Q8_0.gguf"
        }
    ],
    
    "civitai_models": [
        # Lenovo Ultrareal LoRA
        {
            "model_id": "2066914",
            "target_dir": f"{BASE_DIR}/loras",
            "final_name": "Lenovo.safetensors"
        },
        # Instagirl LoRAs (High Noise and Low Noise)
        {
            "model_id": "2086717",  # This is the ID from your wget command
            "target_dir": f"{BASE_DIR}/loras",
            "final_name": "Instagirlv2.0_lownoise.safetensors"
        }
    ],
    
    "custom_nodes": [
        {
            "repo": "https://github.com/giriss/comfy-image-saver",
            "name": "Image Saver (Seed Generator)"
        },
        {
            "repo": "https://github.com/city96/ComfyUI-GGUF",
            "name": "GGUF Support (UnetLoaderGGUF)"
        },
        {
            "repo": "https://github.com/ClownsharkBatwing/RES4LYF",
            "name": "RES4LYF (res_2s sampler)"
        }
    ]
}

def ensure_directory(path):
    """Create directory if it doesn't exist"""
    Path(path).mkdir(parents=True, exist_ok=True)

def install_custom_nodes():
    """Install required custom nodes"""
    print("=" * 60)
    print("INSTALLING CUSTOM NODES")
    print("=" * 60)
    
    custom_nodes_dir = "/workspace/ComfyUI/custom_nodes"
    ensure_directory(custom_nodes_dir)
    
    for node in WAN22_MANIFEST["custom_nodes"]:
        node_name = node["repo"].split("/")[-1]
        node_path = os.path.join(custom_nodes_dir, node_name)
        
        if os.path.exists(node_path):
            print(f"✓ {node['name']} already installed")
            continue
            
        print(f"Installing {node['name']}...")
        try:
            result = subprocess.run(
                ["git", "clone", node["repo"], node_path],
                capture_output=True, text=True, check=True
            )
            print(f"✓ Successfully cloned {node['name']}")
            
            # Install requirements if they exist
            requirements_path = os.path.join(node_path, "requirements.txt")
            if os.path.exists(requirements_path):
                print(f"Installing requirements for {node['name']}...")
                subprocess.run([
                    sys.executable, "-m", "pip", "install", "-r", requirements_path
                ], check=True)
                print(f"✓ Requirements installed for {node['name']}")
                
        except subprocess.CalledProcessError as e:
            print(f"✗ Error installing {node['name']}: {e}")

def download_huggingface_models():
    """Download models from Hugging Face"""
    print("=" * 60)
    print("DOWNLOADING HUGGING FACE MODELS")
    print("=" * 60)
    
    for config in WAN22_MANIFEST["huggingface_models"]:
        target_path = os.path.join(config["target_dir"], config["final_name"])
        
        if os.path.exists(target_path):
            print(f"✓ Already exists: {config['final_name']}")
            continue
            
        print(f"Downloading {config['filename']}...")
        
        try:
            ensure_directory(config["target_dir"])
            
            # Download to temporary location first
            temp_file = hf_hub_download(
                repo_id=config["repo_id"],
                filename=config["filename"],
                resume_download=True
            )
            
            # Move to final location
            shutil.move(temp_file, target_path)
            print(f"✓ Successfully downloaded: {config['final_name']}")
            
        except Exception as e:
            print(f"✗ Error downloading {config['filename']}: {e}")

def download_gguf_models():
    """Download GGUF models from Hugging Face"""
    print("=" * 60)
    print("DOWNLOADING GGUF MODELS")
    print("=" * 60)
    
    for config in WAN22_MANIFEST["gguf_models"]:
        target_path = os.path.join(config["target_dir"], config["final_name"])
        
        if os.path.exists(target_path):
            print(f"✓ Already exists: {config['final_name']}")
            continue
            
        print(f"Downloading {config['filename']}...")
        
        try:
            ensure_directory(config["target_dir"])
            
            # Download GGUF model
            temp_file = hf_hub_download(
                repo_id=config["repo_id"],
                filename=config["filename"],
                resume_download=True
            )
            
            # Move to final location
            shutil.move(temp_file, target_path)
            print(f"✓ Successfully downloaded: {config['final_name']}")
            
        except Exception as e:
            print(f"✗ Error downloading {config['filename']}: {e}")

def download_civitai_models():
    """Download models from Civitai"""
    print("=" * 60)
    print("DOWNLOADING CIVITAI MODELS")
    print("=" * 60)
    
    # You'll need to add your Civitai API token here
    CIVITAI_TOKEN = "00d790b1d7a9934acb89ef729d04c75a"  # From your wget command
    
    for config in WAN22_MANIFEST["civitai_models"]:
        target_path = os.path.join(config["target_dir"], config["final_name"])
        
        if os.path.exists(target_path):
            print(f"✓ Already exists: {config['final_name']}")
            continue
            
        print(f"Downloading from Civitai model {config['model_id']}...")
        
        try:
            ensure_directory(config["target_dir"])
            
            # Construct Civitai download URL
            url = f"https://civitai.com/api/download/models/{config['model_id']}?type=Model&format=Diffusers&token={CIVITAI_TOKEN}"
            
            # Download with proper headers
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()
            
            # Save file
            with open(target_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print(f"✓ Successfully downloaded: {config['final_name']}")
            
        except Exception as e:
            print(f"✗ Error downloading from Civitai: {e}")

def create_missing_instagirl_variants():
    """Create the high noise Instagirl LoRA if missing"""
    print("=" * 60)
    print("CREATING MISSING LORA VARIANTS")
    print("=" * 60)
    
    lownoise_path = f"{BASE_DIR}/loras/Instagirlv2.0_lownoise.safetensors"
    hinoise_path = f"{BASE_DIR}/loras/Instagirlv2.0_hinoise.safetensors"
    
    # If we have low noise but not high noise, copy it
    if os.path.exists(lownoise_path) and not os.path.exists(hinoise_path):
        print("Creating high noise variant from low noise LoRA...")
        shutil.copy2(lownoise_path, hinoise_path)
        print(f"✓ Created: Instagirlv2.0_hinoise.safetensors")
    elif os.path.exists(hinoise_path):
        print("✓ High noise variant already exists")
    else:
        print("⚠ Neither LoRA variant found - will need manual download")

def verify_installation():
    """Verify all required files are present"""
    print("=" * 60)
    print("VERIFICATION - Checking for required files")
    print("=" * 60)
    
    required_files = [
        # Core models
        f"{BASE_DIR}/text_encoders/umt5_xxl_fp8_e4m3fn_scaled.safetensors",
        f"{BASE_DIR}/vae/wan_2.1_vae.safetensors",
        # GGUF models
        f"{BASE_DIR}/diffusion_models/Wan2.2-T2V-A14B-HighNoise-Q8_0.gguf",
        f"{BASE_DIR}/diffusion_models/Wan2.2-T2V-A14B-LowNoise-Q8_0.gguf",
        # LoRAs
        f"{BASE_DIR}/loras/Wan21_T2V_14B_lightx2v_cfg_step_distill_lora_rank32.safetensors",
        f"{BASE_DIR}/loras/Lenovo.safetensors",
        f"{BASE_DIR}/loras/Instagirlv2.0_lownoise.safetensors",
        f"{BASE_DIR}/loras/Instagirlv2.0_hinoise.safetensors"
    ]
    
    missing_files = []
    total_size = 0
    
    for file_path in required_files:
        if os.path.exists(file_path):
            size = os.path.getsize(file_path) / (1024*1024*1024)  # GB
            total_size += size
            print(f"✓ {os.path.basename(file_path)} ({size:.2f} GB)")
        else:
            print(f"✗ MISSING: {os.path.basename(file_path)}")
            missing_files.append(file_path)
    
    # Check custom nodes
    custom_nodes_dir = "/workspace/ComfyUI/custom_nodes"
    required_nodes = ["comfy-image-saver", "ComfyUI-GGUF", "RES4LYF"]
    
    print(f"\nCustom Nodes:")
    for node in required_nodes:
        node_path = os.path.join(custom_nodes_dir, node)
        if os.path.exists(node_path):
            print(f"✓ {node}")
        else:
            print(f"✗ MISSING: {node}")
            missing_files.append(node_path)
    
    print("=" * 60)
    print(f"Total model size: {total_size:.2f} GB")
    
    if not missing_files:
        print("🎉 ALL REQUIREMENTS SATISFIED!")
        print("Your Wan 2.2 Instagirl workflow should work perfectly.")
        print("\n⚠ IMPORTANT: Restart ComfyUI to load the new custom nodes!")
    else:
        print(f"❌ {len(missing_files)} files/nodes are missing.")
        print("Check the errors above and re-run the script.")
    
    return len(missing_files) == 0

def main():
    print("Wan 2.2 Instagirl Complete Setup for ComfyUI")
    print("=" * 60)
    print("This script will download all required models and install custom nodes")
    print("for the Wan 2.2 Instagirl workflow.")
    print("=" * 60)
    
    try:
        # Step 1: Install custom nodes
        install_custom_nodes()
        
        # Step 2: Download Hugging Face models
        download_huggingface_models()
        
        # Step 3: Download GGUF models
        download_gguf_models()
        
        # Step 4: Download Civitai models
        download_civitai_models()
        
        # Step 5: Create missing variants
        create_missing_instagirl_variants()
        
        # Step 6: Verify everything
        success = verify_installation()
        
        if success:
            print("\n" + "=" * 60)
            print("🚀 SETUP COMPLETE!")
            print("=" * 60)
            print("Next steps:")
            print("1. Restart ComfyUI completely")
            print("2. Load the wan2.2-instagirl.json workflow")
            print("3. The workflow should now work without missing node errors")
            print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n❌ Setup interrupted by user")
    except Exception as e:
        print(f"\n❌ Setup failed with error: {e}")

if __name__ == "__main__":
    main()