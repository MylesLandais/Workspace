import os
import sys
import subprocess

def get_comfyui_logs():
    """Get ComfyUI logs from the RunPod instance."""
    pod_id = "w0y8ceryf1zur9"
    
    # Try to get logs using runpodctl
    try:
        # First, let's try to set up SSH keys if they don't exist
        setup_cmd = ["runpodctl", "ssh", "setup"]
        subprocess.run(setup_cmd, check=True, capture_output=True)
        
        # Then try to get the logs
        log_cmd = ["runpodctl", "exec", "python", "--pod_id", pod_id, "cat /workspace/logs/comfyui.log"]
        result = subprocess.run(log_cmd, capture_output=True, text=True, check=True)
        print("ComfyUI Logs:")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error getting logs: {e}")
        print(f"stderr: {e.stderr}")
    except FileNotFoundError:
        print("runpodctl not found. Please install it first.")

if __name__ == "__main__":
    get_comfyui_logs()