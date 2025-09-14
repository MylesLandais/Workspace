#!/bin/bash

# Minimal startup script for VibeVoice ComfyUI development

echo "Starting VibeVoice ComfyUI development environment..."

# Set default values for environment variables if not set
export COMFYUI_PORT=${COMFYUI_PORT:-8188}
export COMFYUI_HOST=${COMFYUI_HOST:-0.0.0.0}

# Start ComfyUI
echo "Starting ComfyUI on $COMFYUI_HOST:$COMFYUI_PORT..."
cd /workspace/ComfyUI
python3 main.py --port $COMFYUI_PORT --host $COMFYUI_HOST