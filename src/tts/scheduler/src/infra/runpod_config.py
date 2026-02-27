"""
RunPod Deployment Configuration System
Modular, functional approach for managing favorite images and GPU configurations.
"""
from typing import Dict, List, Optional, NamedTuple
from dataclasses import dataclass, field
from enum import Enum

class GPUConfig(NamedTuple):
    """Configuration for a specific GPU type."""
    id: str
    name: str
    vram_gb: int
    cost_effectiveness: float  # Lower is more cost-effective
    use_cases: List[str]  # What this GPU is good for

class ImageConfig(NamedTuple):
    """Configuration for a Docker image."""
    name: str
    description: str
    default_gpu: str
    tags: List[str]

# Valid CUDA versions for RunPod builds
# CUDA 13.x does not exist - latest is 12.8.x
VALID_CUDA_VERSIONS = [
    "11.8.0",
    "12.1.0",
    "12.4.0",
    "12.6.0",
    "12.8.0"
]

def validate_cuda_version(version: str) -> bool:
    """
    Validate that a CUDA version is supported.
    
    Args:
        version: CUDA version string (e.g., "12.6.0")
        
    Returns:
        True if version is valid, False otherwise
    """
    return version in VALID_CUDA_VERSIONS

@dataclass
class BuildConfig:
    """Configuration for building custom Docker images on RunPod."""
    cuda_version: str  # Validated against VALID_CUDA_VERSIONS
    git_repo: str
    git_branch: str = "main"
    dockerfile_path: str = "Dockerfile.runpod"
    build_context: str = "."
    network_volume_id: Optional[str] = None
    datacenter_id: Optional[str] = None
    allowed_cuda_versions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate CUDA version after initialization."""
        if not validate_cuda_version(self.cuda_version):
            raise ValueError(
                f"Invalid CUDA version: {self.cuda_version}. "
                f"Valid versions: {', '.join(VALID_CUDA_VERSIONS)}"
            )
        if not self.allowed_cuda_versions:
            self.allowed_cuda_versions = VALID_CUDA_VERSIONS.copy()

# Favorite Docker images for different use cases
FAVORITE_IMAGES: Dict[str, ImageConfig] = {
    "comfyui": ImageConfig(
        name="ashleykleynhans/comfyui-docker",
        description="ComfyUI with common nodes and dependencies",
        default_gpu="NVIDIA RTX 3090",
        tags=["generative-ai", "image-generation", "stable-diffusion"]
    ),
    "comfyui-videorealistic": ImageConfig(
        name="ashleykleynhans/comfyui-docker:videorealistic",
        description="ComfyUI optimized for video and realistic image generation",
        default_gpu="NVIDIA RTX 5090",
        tags=["video-generation", "realistic", "high-vram"]
    ),
    "jupyter-ml": ImageConfig(
        name="quay.io/jupyter/base-notebook:python-3.11",
        description="Jupyter notebook with ML libraries",
        default_gpu="NVIDIA RTX 3090",
        tags=["ml", "data-science", "notebook"]
    ),
    "vllm": ImageConfig(
        name="vllm/vllm-openai:latest",
        description="vLLM inference server",
        default_gpu="NVIDIA RTX 5090",
        tags=["llm", "inference", "high-vram"]
    )
}

# Common GPU configurations
GPU_CONFIGURATIONS: Dict[str, GPUConfig] = {
    "NVIDIA RTX 96GB": GPUConfig(
        id="NVIDIA RTX 96GB",
        name="High VRAM GPU",
        vram_gb=96,
        cost_effectiveness=1.0,  # Most expensive but most powerful
        use_cases=["large-models", "high-vram", "professional"]
    ),
    "NVIDIA RTX 5090": GPUConfig(
        id="NVIDIA RTX 5090",
        name="RTX 5090 GPU",
        vram_gb=24,
        cost_effectiveness=1.5,  # Expensive but powerful
        use_cases=["large-models", "-large", "professional"]
    ),
    "NVIDIA RTX 3090": GPUConfig(
        id="NVIDIA RTX 3090",
        name="RTX 3090 GPU",
        vram_gb=24,
        cost_effectiveness=2.0,  # Cost-effective default
        use_cases=["default", "general-purpose", "cost-effective"]
    ),
    "NVIDIA RTX 4090": GPUConfig(
        id="NVIDIA RTX 4090",
        name="RTX 4090 GPU",
        vram_gb=24,
        cost_effectiveness=1.8,
        use_cases=["high-performance", "gaming", "content-creation"]
    ),
    "NVIDIA A100": GPUConfig(
        id="NVIDIA A100",
        name="A100 GPU",
        vram_gb=40,
        cost_effectiveness=1.2,
        use_cases=["enterprise", "ai-research", "data-center"]
    ),
    "NVIDIA H100": GPUConfig(
        id="NVIDIA H100",
        name="H100 GPU",
        vram_gb=80,
        cost_effectiveness=0.8,  # Most expensive
        use_cases=["enterprise", "ai-research", "data-center", "high-vram"]
    )
}

# Default deployment configurations based on use case
# Can include either "image" (pre-built) or "build_config" (custom build)
DEFAULT_DEPLOYMENT_CONFIGS: Dict[str, Dict] = {
    "comfyui-default": {
        "image": "comfyui",
        "gpu": "NVIDIA RTX 3090",
        "volume_in_gb": 100,
        "ports": "8188/tcp",
        "env": {
            "WEB_ENABLE_WS": "true"
        }
    },
    "comfyui-custom-build": {
        "build_config": {
            "cuda_version": "12.6.0",
            "git_repo": "https://github.com/MylesLandais/ComfyUI",
            "git_branch": "main",
            "dockerfile_path": "Dockerfile.runpod",
            "build_context": ".",
            "network_volume_id": None,  # Set via environment or override
            "datacenter_id": None  # Set via environment or override
        },
        "gpu": "NVIDIA RTX 3090",
        "volume_in_gb": 100,
        "ports": "8188/tcp",
        "env": {
            "WEB_ENABLE_WS": "true"
        }
    },
    "comfyui-large": {
        "image": "comfyui-videorealistic",
        "gpu": "NVIDIA RTX 5090",
        "volume_in_gb": 200,
        "ports": "8188/tcp",
        "env": {
            "WEB_ENABLE_WS": "true"
        }
    },
    "jupyter-ml": {
        "image": "jupyter-ml",
        "gpu": "NVIDIA RTX 3090",
        "volume_in_gb": 50,
        "ports": "8888/tcp",
        "env": {
            "JUPYTER_ENABLE_LAB": "yes"
        }
    },
    "vllm-inference": {
        "image": "vllm",
        "gpu": "NVIDIA RTX 5090",
        "volume_in_gb": 50,
        "ports": "8000/tcp",
        "env": {
            "VLLM_PORT": "8000"
        }
    }
}

def get_gpu_by_vram(required_vram_gb: int) -> Optional[GPUConfig]:
    """Get the most appropriate GPU based on VRAM requirements."""
    suitable_gpus = [
        gpu for gpu in GPU_CONFIGURATIONS.values()
        if gpu.vram_gb >= required_vram_gb
    ]

    if not suitable_gpus:
        return None

    # Sort by cost-effectiveness (lower is better) and VRAM (closer to requirement)
    suitable_gpus.sort(key=lambda x: (
        x.cost_effectiveness,
        abs(x.vram_gb - required_vram_gb)
    ))

    return suitable_gpus[0]

def get_image_config(image_key: str) -> Optional[ImageConfig]:
    """Get image configuration by key."""
    return FAVORITE_IMAGES.get(image_key)

def get_gpu_config(gpu_key: str) -> Optional[GPUConfig]:
    """Get GPU configuration by key."""
    return GPU_CONFIGURATIONS.get(gpu_key)

def get_deployment_config(config_name: str) -> Optional[Dict]:
    """Get a default deployment configuration."""
    return DEFAULT_DEPLOYMENT_CONFIGS.get(config_name)

def recommend_deployment_config(
    use_case: str,
    budget_level: str = "moderate",
    required_vram_gb: Optional[int] = None
) -> Dict:
    """
    Recommend a deployment configuration based on use case and budget.

    Args:
        use_case: The intended use case (e.g., "comfyui", "large-model", etc.)
        budget_level: "low", "moderate", or "high"
        required_vram_gb: Minimum VRAM requirement in GB

    Returns:
        Recommended deployment configuration
    """
    # Start with a base config
    if "comfyui" in use_case.lower():
        if "large" in use_case.lower() or required_vram_gb and required_vram_gb > 20:
            config = DEFAULT_DEPLOYMENT_CONFIGS["comfyui-large"].copy()
        else:
            config = DEFAULT_DEPLOYMENT_CONFIGS["comfyui-default"].copy()
    elif "jupyter" in use_case.lower() or "ml" in use_case.lower():
        config = DEFAULT_DEPLOYMENT_CONFIGS["jupyter-ml"].copy()
    elif "vllm" in use_case.lower() or "inference" in use_case.lower():
        config = DEFAULT_DEPLOYMENT_CONFIGS["vllm-inference"].copy()
    else:
        # Generic fallback
        config = DEFAULT_DEPLOYMENT_CONFIGS["comfyui-default"].copy()

    # Adjust based on budget
    if budget_level == "low":
        # Use most cost-effective GPU that meets requirements
        if required_vram_gb:
            gpu = get_gpu_by_vram(required_vram_gb)
            if gpu:
                config["gpu"] = gpu.id
        else:
            # Default to 3090 for low budget
            config["gpu"] = "NVIDIA RTX 3090"
    elif budget_level == "high":
        # Use high-end GPU
        if required_vram_gb and required_vram_gb > 40:
            config["gpu"] = "NVIDIA H100"
        elif required_vram_gb and required_vram_gb > 24:
            config["gpu"] = "NVIDIA A100"
        else:
            config["gpu"] = "NVIDIA RTX 5090"
    # moderate budget uses defaults

    return config

def list_favorite_images() -> List[str]:
    """List all favorite image keys."""
    return list(FAVORITE_IMAGES.keys())

def list_gpu_configs() -> List[str]:
    """List all GPU configuration keys."""
    return list(GPU_CONFIGURATIONS.keys())

def get_image_details(image_key: str) -> Dict:
    """Get detailed information about an image."""
    config = get_image_config(image_key)
    if not config:
        return {}

    return {
        "name": config.name,
        "description": config.description,
        "default_gpu": config.default_gpu,
        "tags": config.tags
    }

def get_gpu_details(gpu_key: str) -> Dict:
    """Get detailed information about a GPU."""
    config = get_gpu_config(gpu_key)
    if not config:
        return {}
    
    return {
        "id": config.id,
        "name": config.name,
        "vram_gb": config.vram_gb,
        "cost_effectiveness": config.cost_effectiveness,
        "use_cases": config.use_cases
    }

__all__ = [
    "GPUConfig",
    "ImageConfig",
    "BuildConfig",
    "VALID_CUDA_VERSIONS",
    "validate_cuda_version",
    "FAVORITE_IMAGES",
    "GPU_CONFIGURATIONS",
    "DEFAULT_DEPLOYMENT_CONFIGS",
    "get_gpu_by_vram",
    "get_image_config",
    "get_gpu_config",
    "get_deployment_config",
    "recommend_deployment_config",
    "list_favorite_images",
    "list_gpu_configs",
    "get_image_details",
    "get_gpu_details"
]
