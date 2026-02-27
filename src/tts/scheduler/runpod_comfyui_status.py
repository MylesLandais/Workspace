import os
import runpod
from dotenv import load_dotenv

load_dotenv()
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
if not RUNPOD_API_KEY:
    raise ValueError("RUNPOD_API_KEY environment variable not set.")
runpod.api_key = RUNPOD_API_KEY

def find_comfyui_pod():
    pods = runpod.get_pods()
    for pod in pods:
        name = pod.get('name', '').lower()
        image = pod.get('image_name', '').lower()
        if 'comfyui' in name or 'comfyui' in image:
            return pod
    return None

def get_comfyui_status():
    pod = find_comfyui_pod()
    if not pod:
        print("No ComfyUI pod found.")
        return None
    status = pod.get('desiredStatus', 'UNKNOWN')
    public_url = None
    ports_info = pod.get('ports', {})
    if isinstance(ports_info, str):
        import json
        try:
            ports_info = json.loads(ports_info)
        except Exception:
            ports_info = {}
    if isinstance(ports_info, dict):
        for port, info in ports_info.items():
            if 'comfyui' in port or '80' in port:
                public_url = info.get('publicUrl', None)
    print(f"ComfyUI Pod Status: {status}")
    print(f"ComfyUI Public URL: {public_url}")
    return status, public_url

if __name__ == "__main__":
    get_comfyui_status()
