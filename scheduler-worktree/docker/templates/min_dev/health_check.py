#!/usr/bin/env python3
"""
Minimal health check script for VibeVoice ComfyUI development
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

def main():
    """Run health checks"""
    print("Running VibeVoice ComfyUI health checks...")
    
    checks = [
        ("ComfyUI API", check_comfyui_api),
        ("Custom Nodes", check_custom_nodes)
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