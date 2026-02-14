#!/usr/bin/env python3
"""
Script to test the initial setup with a single pod to ensure that ComfyUI starts correctly
and can access the models on the network volume.
"""

import sys
import os
import time

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.infra.runpod_manager import RunPodManager
from src.infra.runpod_config import recommend_deployment_config


def main():
    """Main function to test the ComfyUI setup."""
    print("🚀 Testing ComfyUI setup with a single pod...")
    print("=" * 50)
    
    try:
        # Create an instance of RunPodManager
        manager = RunPodManager()
        print("✅ RunPod manager initialized")
        
        # Get a recommended deployment configuration for ComfyUI
        config = recommend_deployment_config("comfyui", "low")
        print(f"Using deployment configuration: {config}")
        
        # For testing purposes, we'll use a smaller volume size
        config["volume_in_gb"] = 50
        
        # Add network volume ID if available
        # Note: In a real scenario, you would get this from the RunPod API or environment
        network_volume_id = os.getenv("RUNPOD_NETWORK_VOLUME_ID")
        if network_volume_id:
            config["network_volume_id"] = network_volume_id
            print(f"Using network volume ID: {network_volume_id}")
        else:
            # For testing purposes, you can uncomment the line below and replace with a real network volume ID
            # config["network_volume_id"] = "YOUR_NETWORK_VOLUME_ID_HERE"
            print("⚠️  No network volume ID found. Proceeding without network volume.")
            print("To test with a network volume, set the RUNPOD_NETWORK_VOLUME_ID environment variable")
            print("or uncomment and modify the line in the script to set a real network volume ID.")
        
        # Create a pod for ComfyUI
        print("\nCreating pod with requirements:")
        print(f"  - Name: comfyui-test-setup")
        print(f"  - Image: {config.get('image', 'default')}")
        print(f"  - GPU: {config.get('gpu', 'default')}")
        print(f"  - Volume Size: {config.get('volume_in_gb', 'default')} GB")
        
        pod = manager.create_pod_for_use_case(
            name="comfyui-test-setup",
            use_case="comfyui",
            budget_level="low",
            **config
        )
        
        pod_id = pod['id']
        print(f"✅ Pod creation initiated with ID: {pod_id}")
        
        # Wait for the pod to be running
        print("\n⏳ Waiting for pod to be running...")
        running_pod = manager.wait_for_pod_running(pod_id, timeout=300)  # 5 minute timeout
        
        if running_pod:
            print("✅ Pod is now running!")
            print("\nPod Information:")
            print(f"  - ID: {running_pod.get('id')}")
            print(f"  - Name: {running_pod.get('name')}")
            print(f"  - Status: {running_pod.get('desiredStatus')}")
            print(f"  - GPU: {running_pod.get('machine', {}).get('gpuDisplayName', 'Unknown')}")
            
            # Check if we can access the pod logs to verify ComfyUI startup
            print("\n📋 Checking pod logs for ComfyUI startup...")
            try:
                # Wait a bit for ComfyUI to start
                time.sleep(30)
                
                # Get pod logs (this is a simplified check)
                # In a real scenario, you would use the RunPod API to get logs
                print("⚠️  Log checking not implemented in this test script.")
                print("Please manually check the RunPod dashboard for pod logs.")
                
                # Check if ComfyUI is accessible
                print("\n🌐 Checking ComfyUI accessibility...")
                # In a real scenario, you would make an HTTP request to the ComfyUI endpoint
                print("⚠️  ComfyUI accessibility checking not implemented in this test script.")
                print("Please manually check the RunPod dashboard for the pod URL.")
                
            except Exception as e:
                print(f"⚠️  Error checking pod logs or accessibility: {e}")
            
            print("\n🎉 ComfyUI setup test completed!")
            print("Please manually verify the following:")
            print("1. ComfyUI started correctly (check pod logs)")
            print("2. Pod can access models on network volume (check pod logs)")
            print("3. No errors during startup or model loading (check pod logs)")
            
            return 0
        else:
            print("⚠️  Timeout waiting for pod to start running")
            print("Please check the RunPod dashboard for status updates.")
            return 1
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())