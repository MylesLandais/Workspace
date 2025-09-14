"""
RunPod Infrastructure Manager
A centralized class for managing RunPod resources like GPUs and Pods.
"""
import os
import time
import runpod
from dotenv import load_dotenv

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
