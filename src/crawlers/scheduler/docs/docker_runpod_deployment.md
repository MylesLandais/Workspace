# Using the Modular RunPod Deployment System in Docker

This guide explains how to use the new modular RunPod deployment system within the Nebula Jupyter Docker environment.

## Prerequisites

1. Docker Desktop installed on your system
2. RunPod API key (set in `.env` file)
3. Network volume ID (optional, for persistent storage)

## Setting Up the Environment

### 1. Configure Environment Variables

Create a `.env` file in the project root with your RunPod credentials:

```bash
RUNPOD_API_KEY=rpa_your_api_key_here
RUNPOD_NETWORK_VOLUME_ID=your_volume_id_here  # Optional
HUGGINGFACE_TOKEN=your_hf_token_here  # Optional
```

### 2. Start the Development Environment

```bash
# Using the provided start script
./start.sh

# Or using Docker Compose directly
docker compose up --build -d
```

### 3. Access the Environment

```bash
# Access the container shell
docker compose exec jupyterlab bash

# Or access via JupyterLab at http://localhost:8888
```

## Using the Deployment System

Once inside the container, you can use the new deployment system in several ways:

### 1. Command Line Scripts

```bash
# List available deployment options
python scripts/deploy_pod_cli.py --list

# Deploy with preset configuration
python scripts/deploy_pod_cli.py --config comfyui-default --name my-comfyui-pod

# Deploy for specific use case with budget constraints
python scripts/deploy_pod_cli.py --use-case comfyui-large --name large-pod --budget low

# Interactive mode
python scripts/deploy_pod_cli.py
```

### 2. Python API

```python
from src.infra.runpod_manager import RunPodManager
from src.infra.runpod_config import list_favorite_images, get_gpu_details

# Initialize manager
manager = RunPodManager()

# Deploy using preset configuration
pod = manager.create_pod_from_config(
    name="my-pod",
    config_name="comfyui-default"
)

# Deploy optimized for use case
pod = manager.create_pod_for_use_case(
    name="budget-pod",
    use_case="comfyui-large",
    budget_level="low",
    required_vram_gb=20
)
```

## GPU Selection Guidelines

The system automatically recommends GPUs based on your requirements:

### High VRAM Workloads (96GB)
For workloads requiring maximum resources:
```python
manager.create_pod_for_use_case(
    name="high-vram-pod",
    use_case="large-models",
    required_vram_gb=80
)
```

### Large Models (RTX 5090)
For large model workloads:
```python
manager.create_pod_from_config(
    name="large-model-pod",
    config_name="comfyui-large"  # Uses RTX 5090 by default
)
```

### Cost-Effective Default (RTX 3090)
For general purpose workloads:
```python
manager.create_pod_from_config(
    name="general-pod",
    config_name="comfyui-default"  # Uses RTX 3090 by default
)
```

## Jupyter Notebook Usage

Open `notebooks/runpod_deployments/01_initialize_runpod_comfy.ipynb` in JupyterLab to use the interactive deployment interface.

## Testing Deployments

Use the test script to verify the system works correctly:

```bash
python scripts/test_runpod_deployment.py
```

## Troubleshooting

### Missing Dependencies
If you encounter import errors, install missing packages:

```bash
pip install runpod python-dotenv
```

### API Key Issues
Ensure your `.env` file is properly configured and contains a valid RunPod API key.

### Network Volume Problems
If using network volumes, verify the volume ID exists in your RunPod account.

## Best Practices

1. **Always set budget levels** when deploying to optimize costs
2. **Specify VRAM requirements** for better GPU recommendations
3. **Use preset configurations** for consistent deployments
4. **Terminate pods** when not in use to avoid unnecessary charges
5. **Use network volumes** for persistent storage across sessions

## Next Steps

1. Explore the `notebooks/runpod_deployments/` directory for more examples
2. Review `docs/runpod_modular_deployment.md` for detailed API documentation
3. Customize favorite images and GPU configurations in `src/infra/runpod_config.py`
