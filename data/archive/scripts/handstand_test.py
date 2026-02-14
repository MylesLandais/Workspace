import json
import os
import requests
import time
from datetime import datetime

# Load prompts
with open("/home/jovyan/workspace/data/Prompts/shay_handstand_orbital_360_prompts.json", "r") as f:
    data = json.load(f)

prompts = data.get("prompts", [])
print(f"Loaded {len(prompts)} prompts")

# Get first prompt
test_prompt = prompts[0]
print(f"\nTest: {test_prompt['id']}")
print(f"Name: {test_prompt['name']}")

# Check API key
api_key = os.getenv("RUNPOD_API_KEY")
endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "a48mrbdsbzg35n")

if not api_key:
    print("ERROR: RUNPOD_API_KEY not found")
    exit(1)

print(f"API Key: {'*' * 15}")

# Load workflow
with open("/home/jovyan/workspace/data/Comfy_Workflow/api_google_gemini_image.json", "r") as f:
    workflow = json.load(f)

# Update workflow
seed = int(datetime.now().timestamp() % (2**32))
for node_id, node_data in workflow.items():
    if isinstance(node_data, dict) and node_data.get("class_type") == "NanoBananaAIO":
        node_data["inputs"]["prompt"] = test_prompt["prompt"]
        node_data["inputs"]["seed"] = seed
        node_data["inputs"]["image_count"] = 2
        node_data["inputs"]["aspect_ratio"] = "1:1"
        node_data["inputs"]["image_size"] = "2K"
        node_data["inputs"]["use_search"] = False
        node_data["inputs"]["temperature"] = 1.0
        print(f"Updated node {node_id} with seed {seed}")
        break

# Wrap and submit
wrapped = {"input": {"workflow": workflow}}

run_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
headers = {
    "Authorization": f"Bearer {api_key}",
    "Content-Type": "application/json"
}

print(f"\nSubmitting to RunPod...")
response = requests.post(run_url, headers=headers, json=wrapped, timeout=30)

if response.status_code == 200:
    result = response.json()
    job_id = result.get("id")
    print(f"Job submitted: {job_id}")
else:
    print(f"ERROR: {response.status_code}")
    print(response.text)
