# VibeVoice Specialized Docker Template for RunPod
# This template will be used with RunPod's CUDA-enabled base images

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
    ffmpeg \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libglib2.0-0 \
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

# Install HuggingFace CLI and authentication tools
RUN uv pip install --system huggingface_hub

# Install additional dependencies for VibeVoice
RUN uv pip install --system \
    torch>=2.0.0 \
    torchaudio>=2.0.0 \
    transformers>=4.30.0 \
    soundfile>=0.12.1 \
    numpy>=1.21.0 \
    scipy>=1.10.0 \
    librosa>=0.10.0 \
    gradio>=3.0.0 \
    accelerate>=0.20.0

# Install ComfyUI Manager for custom node management
RUN git clone https://github.com/ltdrdata/ComfyUI-Manager.git /workspace/ComfyUI/custom_nodes/ComfyUI-Manager

# Pre-install VibeVoice custom node
RUN git clone https://github.com/wildminder/ComfyUI-VibeVoice.git /workspace/ComfyUI/custom_nodes/ComfyUI-VibeVoice
RUN cd /workspace/ComfyUI/custom_nodes/ComfyUI-VibeVoice && \
    uv pip install --system -r requirements.txt

# Create directories for models and workflows
RUN mkdir -p /workspace/ComfyUI/models/checkpoints && \
    mkdir -p /workspace/ComfyUI/models/vae && \
    mkdir -p /workspace/ComfyUI/models/loras && \
    mkdir -p /workspace/ComfyUI/models/controlnet && \
    mkdir -p /workspace/ComfyUI/models/upscale_models && \
    mkdir -p /workspace/ComfyUI/models/embeddings && \
    mkdir -p /workspace/ComfyUI/models/vibe_voice && \
    mkdir -p /workspace/ComfyUI/input && \
    mkdir -p /workspace/ComfyUI/output && \
    mkdir -p /workspace/ComfyUI/workflows

# Copy health check and startup scripts
COPY health_check.py /workspace/health_check.py
COPY startup.sh /workspace/startup.sh
RUN chmod +x /workspace/startup.sh

# Expose ComfyUI port
EXPOSE 8188

# Set environment variables
ENV PYTHONPATH=/workspace/ComfyUI
ENV HF_HOME=/workspace/huggingface

# Start ComfyUI
CMD ["/workspace/startup.sh"]