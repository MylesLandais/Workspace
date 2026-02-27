#!/usr/bin/env python3
import os
import sys
import runpod
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Load environment variables
load_dotenv()
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
if not RUNPOD_API_KEY:
    raise ValueError("RUNPOD_API_KEY environment variable not set.")
runpod.api_key = RUNPOD_API_KEY

def list_gpus():
    """List all available GPUs from RunPod."""
    try:
        gpus = runpod.get_gpus()
        print("Available GPUs:")
        print("=" * 50)
        for gpu in gpus:
            print(f"ID: {gpu.get('id')}")
            print(f"Name: {gpu.get('name')}")
            print(f"VRAM: {gpu.get('vram')} GB")
            print(f"Price: ${gpu.get('pricePerHour', 'N/A')}/hour")
            print("-" * 30)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    list_gpus()