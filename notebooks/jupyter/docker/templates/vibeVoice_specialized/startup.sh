#!/bin/bash

# Startup script for VibeVoice ComfyUI container

echo "Starting VibeVoice ComfyUI container..."

# Set default values for environment variables if not set
export COMFYUI_PORT=${COMFYUI_PORT:-8188}
export COMFYUI_HOST=${COMFYUI_HOST:-0.0.0.0}
export HF_HOME=${HF_HOME:-/workspace/huggingface}

# Create HuggingFace directory if it doesn't exist
mkdir -p $HF_HOME

# Check if HuggingFace token is provided
if [ -n "$HUGGINGFACE_TOKEN" ]; then
    echo "Configuring HuggingFace token..."
    python3 -c "from huggingface_hub import HfFolder; HfFolder.save_token('$HUGGINGFACE_TOKEN')"
fi

# Install any additional requirements if requirements.txt exists
if [ -f "/workspace/requirements.txt" ]; then
    echo "Installing additional requirements..."
    pip install --no-cache-dir -r /workspace/requirements.txt
fi

# Run health check
echo "Running health check..."
python3 /workspace/health_check.py

# Start ComfyUI
echo "Starting ComfyUI on $COMFYUI_HOST:$COMFYUI_PORT..."
cd /workspace/ComfyUI
python3 main.py --port $COMFYUI_PORT --host $COMFYUI_HOST