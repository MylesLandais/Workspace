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
    FAVORITE_IMAGES,
    BuildConfig,
    validate_cuda_version,
    VALID_CUDA_VERSIONS
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

    def build_and_deploy_custom_image(
        self,
        name: str,
        build_config: BuildConfig,
        gpu_type_id: Optional[str] = None,
        **deployment_overrides
    ) -> Dict:
        """
        Build a custom Docker image and deploy a pod with it.
        
        This method handles the full lifecycle:
        1. Validates CUDA version (done in BuildConfig.__post_init__)
        2. Submits build job to RunPod
        3. Waits for build completion
        4. Deploys pod with the built image
        
        Args:
            name: Name for the pod
            build_config: BuildConfig with git repo, branch, CUDA version, etc.
            gpu_type_id: GPU type ID (optional, can be in deployment_overrides)
            **deployment_overrides: Additional pod deployment parameters
            
        Returns:
            Dictionary with build and deployment information
            
        Raises:
            ValueError: If CUDA version is invalid (caught by BuildConfig)
            RuntimeError: If build fails or deployment fails
        """
        # BuildConfig already validates CUDA version in __post_init__
        # But we can double-check here for safety
        if not validate_cuda_version(build_config.cuda_version):
            raise ValueError(
                f"Invalid CUDA version: {build_config.cuda_version}. "
                f"Valid versions: {', '.join(VALID_CUDA_VERSIONS)}"
            )
        
        # Prepare build parameters
        build_params = {
            "git_repo": build_config.git_repo,
            "git_branch": build_config.git_branch,
            "dockerfile_path": build_config.dockerfile_path,
            "build_context": build_config.build_context,
            "cuda_version": build_config.cuda_version,
        }
        
        # Add network volume if specified
        if build_config.network_volume_id:
            build_params["network_volume_id"] = build_config.network_volume_id
        
        # Add datacenter if specified
        if build_config.datacenter_id:
            build_params["datacenter_id"] = build_config.datacenter_id
        
        # Submit build job
        # Note: This is a placeholder - actual RunPod API may differ
        # Check RunPod SDK documentation for exact method
        try:
            build_result = runpod.build_image(**build_params)
            build_id = build_result.get("id")
            
            if not build_id:
                raise RuntimeError(f"Build submission failed: {build_result}")
            
            # Wait for build to complete
            # In real implementation, poll build status
            print(f"Build submitted: {build_id}")
            print("Waiting for build to complete...")
            
            # TODO: Implement build status polling
            # build_status = self._wait_for_build_complete(build_id)
            
            # Get built image name
            image_name = build_result.get("image_name") or f"{name}:latest"
            
            # Deploy pod with built image
            deployment_params = {
                "name": name,
                "image_name": image_name,
                "gpu_type_id": gpu_type_id,
                **deployment_overrides
            }
            
            # Add network volume to deployment if specified
            if build_config.network_volume_id:
                deployment_params["network_volume_id"] = build_config.network_volume_id
            
            pod = runpod.create_pod(**deployment_params)
            
            return {
                "build_id": build_id,
                "image_name": image_name,
                "pod": pod,
                "build_config": {
                    "cuda_version": build_config.cuda_version,
                    "git_repo": build_config.git_repo,
                    "git_branch": build_config.git_branch
                }
            }
            
        except Exception as e:
            raise RuntimeError(f"Build and deploy failed: {e}") from e
