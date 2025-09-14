#!/usr/bin/env python3
"""
Health check script for VibeVoice ComfyUI container
"""

import os
import sys
import requests
import time
from pathlib import Path

def check_comfyui_api():
    """Check if ComfyUI API is responding"""
    try:
        response = requests.get("http://localhost:8188/", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_custom_nodes():
    """Check if VibeVoice custom node is installed"""
    try:
        response = requests.get("http://localhost:8188/object_info", timeout=5)
        if response.status_code == 200:
            object_info = response.json()
            vibe_voice_nodes = [key for key in object_info.keys() if 'vibe' in key.lower() or 'voice' in key.lower()]
            return len(vibe_voice_nodes) > 0
        return False
    except:
        return False

def check_model_files():
    """Check if required model files exist"""
    model_dir = Path("/workspace/ComfyUI/models/vibe_voice")
    if not model_dir.exists():
        return False
    
    # Check for VibeVoice-Large model files
    model_files = list(model_dir.glob("*.bin")) + list(model_dir.glob("*.pt")) + list(model_dir.glob("*.safetensors"))
    return len(model_files) > 0

def check_disk_space():
    """Check if there's sufficient disk space"""
    try:
        stat = os.statvfs("/workspace")
        free_space_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
        return free_space_gb > 5  # At least 5GB free
    except:
        return True  # Assume OK if we can't check

def main():
    """Run all health checks"""
    print("Running VibeVoice ComfyUI health checks...")
    
    checks = [
        ("ComfyUI API", check_comfyui_api),
        ("Custom Nodes", check_custom_nodes),
        ("Model Files", check_model_files),
        ("Disk Space", check_disk_space)
    ]
    
    all_passed = True
    
    for check_name, check_func in checks:
        try:
            result = check_func()
            status = "✓ PASS" if result else "✗ FAIL"
            print(f"  {check_name}: {status}")
            if not result:
                all_passed = False
        except Exception as e:
            print(f"  {check_name}: ✗ ERROR - {e}")
            all_passed = False
    
    if all_passed:
        print("\n🎉 All health checks passed!")
        sys.exit(0)
    else:
        print("\n❌ Some health checks failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()