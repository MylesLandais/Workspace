#!/usr/bin/env python3
"""
Script to retrieve logs from RunPod pods.
"""
import os
import sys
import runpod
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.infra.runpod_manager import RunPodManager

def get_pod_logs(pod_id: str, max_lines: int = 100):
    """
    Retrieve logs from a specific pod.
    
    Args:
        pod_id (str): The ID of the pod to retrieve logs from.
        max_lines (int): Maximum number of log lines to retrieve.
        
    Returns:
        str: The pod logs or None if retrieval failed.
    """
    try:
        # Note: The runpod Python library doesn't have a direct method for retrieving logs
        # This would typically be done through the RunPod dashboard or API
        # For now, we'll provide instructions for accessing logs
        print(f"Pod logs for {pod_id}:")
        print("=" * 50)
        print("To view logs for this pod, you can:")
        print("1. Visit the RunPod dashboard at https://www.runpod.io/console/pods")
        print("2. Find the pod with ID:", pod_id)
        print("3. Click on the pod to expand it")
        print("4. Click the 'Logs' button to view real-time logs")
        print()
        print("Alternatively, if you have runpodctl installed, you can use:")
        print(f"   runpodctl pod logs {pod_id}")
        return None
    except Exception as e:
        print(f"Error retrieving logs for pod {pod_id}: {e}")
        return None

def main():
    """Main function to retrieve logs for ComfyUI pods."""
    print("🔍 Retrieving RunPod pod logs...")
    print("=" * 50)
    
    try:
        # Create an instance of RunPodManager
        manager = RunPodManager()
        print("✅ RunPod manager initialized")
        
        # List all active pods
        print("\n📋 Getting active pods...")
        active_pods = manager.get_active_pods()
        
        if not active_pods:
            print("✅ No active pods found.")
            return 0
        
        print(f"Found {len(active_pods)} active pod(s):")
        print("-" * 30)
        
        # Display pod information
        for i, pod in enumerate(active_pods, 1):
            print(f"{i}. Name: {pod.get('name', 'N/A')}")
            print(f"   ID: {pod.get('id', 'N/A')}")
            print(f"   Status: {pod.get('desiredStatus', 'N/A')}")
            print(f"   GPU: {pod.get('gpuTypeId', 'N/A')}")
            print(f"   Interruptible: {pod.get('interruptible', False)}")
            print()
        
        # If only one pod, show its logs directly
        if len(active_pods) == 1:
            pod_id = active_pods[0].get('id')
            if pod_id:
                get_pod_logs(pod_id)
        else:
            # Ask user which pod to check
            try:
                choice = int(input("Enter the number of the pod to check logs for (0 to skip): "))
                if 1 <= choice <= len(active_pods):
                    pod_id = active_pods[choice-1].get('id')
                    if pod_id:
                        get_pod_logs(pod_id)
                else:
                    print("Skipping log retrieval.")
            except ValueError:
                print("Invalid input. Skipping log retrieval.")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print("\n💡 Tip: For continuous log monitoring, use the RunPod dashboard or runpodctl")
    return 0

if __name__ == "__main__":
    sys.exit(main())