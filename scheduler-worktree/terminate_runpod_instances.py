#!/usr/bin/env python3
"""
Script to terminate all running RunPod instances to save budget.
"""
import os
import sys
from dotenv import load_dotenv
import runpod

# Add the project root directory to the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.infra.runpod_manager import RunPodManager

def main():
    """Main function to terminate all running RunPod instances."""
    print("🔍 Checking RunPod instances...")
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
            print(f"   Created: {pod.get('createdAt', 'N/A')}")
            print()
        
        # Automatically terminate all active pods
        print("🛑 Terminating all active pods to save budget...")
        terminated_ids = manager.cleanup_all_pods()
        
        if terminated_ids:
            print(f"✅ Successfully terminated {len(terminated_ids)} pod(s):")
            for pod_id in terminated_ids:
                print(f"  - {pod_id}")
        else:
            print("ℹ️  No pods were terminated.")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return 1
    
    print("\n🎉 Cleanup process completed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())