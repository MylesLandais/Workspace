"""
RunPod Infrastructure Manager
A centralized class for managing RunPod resources like GPUs and Pods.
"""
import os
import time
import runpod
from dotenv import load_dotenv
from typing import Dict, Optional, List
from .runpod_config import (
    get_image_config,
    get_gpu_config,
    get_deployment_config,
    recommend_deployment_config,
    GPU_CONFIGURATIONS,
    FAVORITE_IMAGES
)

class RunPodManager:
    """
    Handles interactions with the RunPod API to manage infrastructure.
    """

    def __init__(self, api_key: str = None):
        """
        Initializes the RunPodManager and authenticates with the API.
        """
        load_dotenv()
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        if not self.api_key:
            raise ValueError("RUNPOD_API_KEY not found in .env file or arguments.")
        runpod.api_key = self.api_key

    def list_gpus(self):
        """Returns a list of all available GPU types."""
        return runpod.get_gpus()

    def list_pods(self):
        """Returns a list of all active pods for the current API key."""
        return runpod.get_pods()

    def get_active_pods(self):
        """Returns a list of pods that are not terminated."""
        pods = self.list_pods()
        return [p for p in pods if p.get("desiredStatus") not in ("TERMINATED", "DELETED")]

    def terminate_pod(self, pod_id: str):
        """Terminates a specific pod by its ID."""
        return runpod.terminate_pod(pod_id)

    def cleanup_all_pods(self):
        """Terminates all active pods."""
        active_pods = self.get_active_pods()
        if not active_pods:
            print("No active pods to clean up.")
            return []

        terminated_ids = []
        for pod in active_pods:
            pod_id = pod.get("id")
            print(f"Terminating pod: {pod.get('name')} (ID: {pod_id})...")
            try:
                self.terminate_pod(pod_id)
                terminated_ids.append(pod_id)
            except Exception as e:
                print(f"  - Error terminating pod {pod_id}: {e}")
        return terminated_ids

    def create_pod_from_config(self, name: str, config_name: str, **overrides):
        """
        Creates a new pod using a predefined deployment configuration.

        Args:
            name (str): The name of the pod.
            config_name (str): The name of the deployment configuration to use.
            **overrides: Additional parameters to override the configuration.
        """
        config = get_deployment_config(config_name)
        if not config:
            raise ValueError(f"Configuration '{config_name}' not found.")

        # Apply overrides
        final_config = {**config, **overrides}

        # Resolve image name from key
        image_config = get_image_config(final_config["image"])
        if not image_config:
            raise ValueError(f"Image '{final_config['image']}' not found in favorite images.")
        image_name = image_config.name

        # Get GPU type ID
        gpu_config = get_gpu_config(final_config["gpu"])
        if not gpu_config:
            raise ValueError(f"GPU '{final_config['gpu']}' not found in configurations.")
        gpu_type_id = gpu_config.id

        # Build the creation parameters
        creation_params = {
            "name": name,
            "image_name": image_name,
            "gpu_type_id": gpu_type_id,
            **{k: v for k, v in final_config.items() if k not in ["image", "gpu"]}
        }

        return runpod.create_pod(**creation_params)

    def create_pod_for_use_case(
        self,
        name: str,
        use_case: str,
        budget_level: str = "moderate",
        required_vram_gb: Optional[int] = None,
        **overrides
    ):
        """
        Creates a new pod optimized for a specific use case.

        Args:
            name (str): The name of the pod.
            use_case (str): The intended use case.
            budget_level (str): "low", "moderate", or "high".
            required_vram_gb (int, optional): Minimum VRAM requirement.
            **overrides: Additional parameters to override the recommendation.
        """
        config = recommend_deployment_config(use_case, budget_level, required_vram_gb)

        # Apply overrides
        final_config = {**config, **overrides}

        # Resolve image name from key
        image_config = get_image_config(final_config["image"])
        if not image_config:
            raise ValueError(f"Image '{final_config['image']}' not found in favorite images.")
        image_name = image_config.name

        # Get GPU type ID
        gpu_config = get_gpu_config(final_config["gpu"])
        if not gpu_config:
            raise ValueError(f"GPU '{final_config['gpu']}' not found in configurations.")
        gpu_type_id = gpu_config.id

        # Build the creation parameters
        creation_params = {
            "name": name,
            "image_name": image_name,
            "gpu_type_id": gpu_type_id,
            **{k: v for k, v in final_config.items() if k not in ["image", "gpu"]}
        }

        return runpod.create_pod(**creation_params)

    def create_pod(self, name: str, image_name: str, gpu_type_id: str, **kwargs):
        """
        Creates a new pod with the specified configuration.

        Args:
            name (str): The name of the pod.
            image_name (str): The Docker image to use.
            gpu_type_id (str): The ID of the GPU to use.
            **kwargs: Additional parameters for pod creation (e.g., gpu_count,
                      volume_in_gb, ports, env).
        """
        config = {
            "name": name,
            "image_name": image_name,
            "gpu_type_id": gpu_type_id,
            **kwargs
        }
        return runpod.create_pod(**config)

    def wait_for_pod_running(self, pod_id: str, timeout: int = 300):
        """
        Waits for a pod to enter the 'RUNNING' state.

        Args:
            pod_id (str): The ID of the pod to monitor.
            timeout (int): The maximum time to wait in seconds.

        Returns:
            dict: The pod details once it's running, or None if it times out.
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            pod = runpod.get_pod(pod_id)
            if pod and pod.get('desiredStatus') == 'RUNNING':
                return pod
            time.sleep(5)
        return None
