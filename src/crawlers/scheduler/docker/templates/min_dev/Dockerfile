# Minimal VibeVoice Development Docker Template
# This template is for local development with minimal dependencies

FROM python:3.10-slim

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV COMFYUI_PORT=8188
ENV COMFYUI_HOST=0.0.0.0

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip setuptools wheel

# Install UV for fast Python dependency management
RUN pip install --no-cache-dir uv

# Create working directory
WORKDIR /workspace

# Clone ComfyUI from stable release
RUN git clone https://github.com/comfyanonymous/ComfyUI.git /workspace/ComfyUI

# Set up ComfyUI
WORKDIR /workspace/ComfyUI

# Install ComfyUI requirements using UV for faster installation
RUN uv pip install --system -r requirements.txt

# Install minimal dependencies for VibeVoice development
RUN uv pip install --system \
    torch>=2.0.0 \
    transformers>=4.30.0 \
    numpy>=1.21.0

# Install ComfyUI Manager for custom node management
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git /workspace/ComfyUI/custom_nodes/ComfyUI-Manager

# Create directories for models and workflows
RUN mkdir -p /workspace/ComfyUI/models/checkpoints && \
    mkdir -p /workspace/ComfyUI/models/vae && \
    mkdir -p /workspace/ComfyUI/models/loras && \
    mkdir -p /workspace/ComfyUI/models/vibe_voice && \
    mkdir -p /workspace/ComfyUI/input && \
    mkdir -p /workspace/ComfyUI/output && \
    mkdir -p /workspace/ComfyUI/workflows

# Expose ComfyUI port
EXPOSE 8188

# Set environment variables
ENV PYTHONPATH=/workspace/ComfyUI

# Start ComfyUI
CMD ["python3", "main.py", "--port", "8188", "--host", "0.0.0.0"]