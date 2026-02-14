#!/usr/bin/env python3
"""
Script to check logs for RunPod pods using the RunPod API.
Note: The RunPod Python SDK doesn't currently have a direct method for retrieving pod logs.
This script provides information on how to access logs through alternative methods.
"""
import os
import sys
import runpod
from dotenv import load_dotenv

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.infra.runpod_manager import RunPodManager

def show_pod_logs_info(pod_id: str = None):
    """
    Show information about how to access logs for a specific pod or all pods.
    
    Args:
        pod_id (str, optional): Specific pod ID to check logs for.
    """
    try:
        # Create an instance of RunPodManager
        manager = RunPodManager()
        print("✅ RunPod manager initialized")
        
        # Get pod information
        if pod_id:
            # Try to get specific pod
            try:
                pod = runpod.get_pod(pod_id)
                if pod:
                    pods = [pod]
                else:
                    print(f"❌ Pod with ID {pod_id} not found.")
                    return
            except Exception as e:
                print(f"❌ Error retrieving pod {pod_id}: {e}")
                return
        else:
            # Get all active pods
            print("\n📋 Getting active pods...")
            pods = manager.get_active_pods()
        
        if not pods:
            print("✅ No active pods found.")
            return
        
        print(f"Found {len(pods)} pod(s):")
        print("=" * 50)
        
        # Display pod information and log access instructions
        for i, pod in enumerate(pods, 1):
            pod_name = pod.get('name', 'N/A')
            pod_id = pod.get('id', 'N/A')
            pod_status = pod.get('desiredStatus', 'N/A')
            pod_gpu = pod.get('gpuTypeId', 'N/A')
            
            print(f"{i}. Name: {pod_name}")
            print(f"   ID: {pod_id}")
            print(f"   Status: {pod_status}")
            print(f"   GPU: {pod_gpu}")
            
            print(f"\n   📋 To view logs for this pod:")
            print(f"      1. Visit: https://www.runpod.io/console/pods")
            print(f"      2. Find pod with ID: {pod_id}")
            print(f"      3. Click on the pod to expand it")
            print(f"      4. Click the 'Logs' button")
            
            if pod_id != 'N/A':
                print(f"      5. Or use runpodctl: runpodctl pod logs {pod_id}")
            
            print("-" * 50)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print("\n💡 Tip: For continuous log monitoring, use the RunPod dashboard or runpodctl")
    return 0

def main():
    """Main function to check pod logs."""
    print("🔍 RunPod Pod Log Access Information")
    print("=" * 50)
    
    # Check if a specific pod ID was provided as a command line argument
    pod_id = None
    if len(sys.argv) > 1:
        pod_id = sys.argv[1]
        print(f"Checking logs for pod ID: {pod_id}")
    else:
        print("Checking logs for all active pods")
    
    return show_pod_logs_info(pod_id)

if __name__ == "__main__":
    sys.exit(main())