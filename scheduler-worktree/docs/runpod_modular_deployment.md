# Modular RunPod Deployment System

This document describes the new modular, functional approach to RunPod deployments that has been implemented in the Nebula Jupyter System.

## Overview

The new deployment system provides a more structured and reusable approach to deploying workloads on RunPod. It includes:

1. **Configuration Management**: Centralized tracking of favorite Docker images and GPU configurations
2. **Functional Deployment Methods**: Multiple approaches to pod creation based on different needs
3. **Use Case Optimization**: Automatic recommendation of configurations based on use case and budget

## Key Components

### 1. RunPod Configuration System (`src/infra/runpod_config.py`)

This module manages all deployment configurations:

- **Favorite Images**: Predefined Docker images for common use cases
- **GPU Configurations**: Standardized GPU options with characteristics
- **Default Deployments**: Preset configurations for common scenarios

#### Favorite Images

The system tracks these favorite images:
- `comfyui`: ComfyUI with common nodes and dependencies
- `comfyui-videorealistic`: ComfyUI optimized for video and realistic image generation
- `jupyter-ml`: Jupyter notebook with ML libraries
- `vllm`: vLLM inference server

#### GPU Configurations

Common GPU configurations include:
- **NVIDIA RTX 96GB**: High VRAM GPU for maximum resources
- **NVIDIA RTX 5090**: Powerful GPU for large models
- **NVIDIA RTX 3090**: Cost-effective default option
- **NVIDIA RTX 4090**: High-performance GPU
- **NVIDIA A100**: Enterprise-class GPU
- **NVIDIA H100**: Top-tier enterprise GPU

### 2. RunPod Manager (`src/infra/runpod_manager.py`)

Extended version of the RunPod manager with new deployment methods:

#### New Deployment Methods

1. **`create_pod_from_config()`**: Deploy using predefined configurations
2. **`create_pod_for_use_case()`**: Deploy optimized for specific use cases with budget constraints

## Usage Examples

### 1. Deploy Using Preset Configuration

```python
from src.infra.runpod_manager import RunPodManager

manager = RunPodManager()
pod = manager.create_pod_from_config(
    name="my-comfyui-pod",
    config_name="comfyui-default"
)
```

### 2. Deploy Optimized for Use Case

```python
from src.infra.runpod_manager import RunPodManager

manager = RunPodManager()
pod = manager.create_pod_for_use_case(
    name="budget-comfyui",
    use_case="comfyui-large",
    budget_level="low",
    required_vram_gb=20
)
```

### 3. Deploy with Custom Overrides

```python
from src.infra.runpod_manager import RunPodManager

manager = RunPodManager()
pod = manager.create_pod_from_config(
    name="custom-jupyter",
    config_name="jupyter-ml",
    volume_in_gb=200,  # Override default
    env={
        "CUSTOM_VAR": "value"
    }
)
```

## GPU Selection Logic

The system automatically recommends GPUs based on:

1. **VRAM Requirements**: Minimum VRAM needed for the workload
2. **Budget Constraints**: 
   - `low`: Most cost-effective options
   - `moderate`: Balanced options (default)
   - `high`: High-performance options
3. **Use Case Requirements**: Specific needs of the workload

## Common Deployment Patterns

### 96GB VRAM
Used when no budget is set and maximum resources are needed:
```python
# For workloads requiring maximum VRAM
manager.create_pod_for_use_case(
    name="high-vram-workload",
    use_case="large-models",
    required_vram_gb=80
)
```

### RTX 5090
Sometimes used for large models ("-large" tag):
```python
# For large model workloads
manager.create_pod_from_config(
    name="large-model-pod",
    config_name="comfyui-large"  # Uses RTX 5090 by default
)
```

### RTX 3090
Cost-effective default option:
```python
# For general purpose workloads
manager.create_pod_from_config(
    name="general-pod",
    config_name="comfyui-default"  # Uses RTX 3090 by default
)
```

## Command Line Tools

Two CLI scripts are provided for deployment management:

### 1. Functional Deployment Script (`scripts/deploy_pod_functional.py`)

Demonstrates the functional approach with multiple deployment examples.

### 2. Interactive CLI (`scripts/deploy_pod_cli.py`)

User-friendly command-line interface for interactive deployments:
```bash
# List available options
python scripts/deploy_pod_cli.py --list

# Deploy with preset configuration
python scripts/deploy_pod_cli.py --config comfyui-default --name my-pod

# Deploy for specific use case
python scripts/deploy_pod_cli.py --use-case comfyui-large --name large-pod

# Interactive mode
python scripts/deploy_pod_cli.py
```

## Notebooks

The updated `notebooks/runpod_deployments/01_initialize_runpod_comfy.ipynb` demonstrates all the new features in an interactive Jupyter environment.

## Benefits

1. **Consistency**: Standardized configurations ensure reproducible deployments
2. **Flexibility**: Multiple deployment approaches for different needs
3. **Cost Optimization**: Budget-aware GPU selection
4. **Maintainability**: Centralized configuration management
5. **Extensibility**: Easy to add new images, GPUs, and configurations