#!/usr/bin/env python3
"""
Quick test: Generate single handstand orbital image

Tests the Nano Banana AIO workflow setup with one prompt.
"""

import sys
import json
import base64
from pathlib import Path
from datetime import datetime

# Add path for imports
sys.path.insert(0, str(Path(__file__).parent / "notebooks" / "comfy"))

# Check if we can import
try:
    from runpod_runner import RunPodWorkflowRunner
except ImportError as e:
    print(f"ERROR: Cannot import RunPodWorkflowRunner: {e}")
    print("Make sure docker container is running with GPU access")
    sys.exit(1)

# Check environment variables
import os

api_key = os.getenv("RUNPOD_API_KEY")
endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")

if not api_key:
    print("ERROR: RUNPOD_API_KEY not found")
    print("Please set in .env file or pass environment variable")
    sys.exit(1)

print(f"API Key: {'*' * 20}")  # Mask for security
print(f"Endpoint ID: {endpoint_id or 'default'}")

# Load handstand prompts
prompts_file = Path(__file__).parent / "data" / "Prompts" / "shay_handstand_orbital_360_prompts.json"

if not prompts_file.exists():
    print(f"ERROR: Prompts file not found: {prompts_file}")
    sys.exit(1)

with open(prompts_file, 'r') as f:
    data = json.load(f)

prompts = data.get("prompts", [])
print(f"\nLoaded {len(prompts)} handstand orbital prompts")

# Select first prompt for testing
test_prompt = prompts[0]
print(f"\nTest Prompt: {test_prompt['id']}")
print(f"Name: {test_prompt['name']}")
print(f"Pass: {test_prompt['pass']}")

# Display first 200 chars of prompt
prompt_preview = test_prompt['prompt'][:200]
print(f"\nPrompt preview:\n{prompt_preview}...")

# Initialize runner
runner = RunPodWorkflowRunner(api_key=api_key, endpoint_id=endpoint_id)

# Load Nano Banana workflow
workflow_file = Path(__file__).parent / "data" / "Comfy_Workflow" / "api_google_gemini_image.json"

if not workflow_file.exists():
    print(f"ERROR: Workflow not found: {workflow_file}")
    sys.exit(1)

print(f"\nWorkflow: {workflow_file.name}")

# Run the test
print("\n" + "="*60)
print("Starting single test generation...")
print("="*60 + "\n")

try:
    # For Nano Banana workflow, we need to directly submit the prepared workflow
    # Load workflow
    with open(workflow_file, 'r') as f:
        workflow_data = json.load(f)
    
    # Find NanoBananaAIO node and update it
    updated = False
    for node_id, node_data in workflow_data.items():
        if isinstance(node_data, dict) and node_data.get("class_type") == "NanoBananaAIO":
            node_data["inputs"]["prompt"] = test_prompt["prompt"]
            node_data["inputs"]["seed"] = int(datetime.now().timestamp() % (2**32))
            node_data["inputs"]["image_count"] = 2  # Generate 2 test images
            node_data["inputs"]["aspect_ratio"] = "1:1"
            node_data["inputs"]["image_size"] = "2K"
            node_data["inputs"]["use_search"] = False
            updated = True
            print(f"Updated Nano Banana AIO node: {node_id}")
            break
    
    if not updated:
        print("ERROR: Could not find NanoBananaAIO node in workflow")
        sys.exit(1)
    
    # Wrap in RunPod format
    wrapped_workflow = {"input": {"workflow": workflow_data}}
    
    # Submit job
    import time
    seed = int(time.time() * 1000) % (2**32)
    print(f"Seed: {seed}")
    
    # Manual submission using runner's methods
    from runpod_runner import run_workflow
    
    result = run_workflow(
        workflow_file.name,
        seed=seed,
        output_dir="outputs/handstand_test"
    )
    
    print("\n" + "="*60)
    print("TEST COMPLETE")
    print("="*60 + "\n")
    print(f"Success: {result['success']}")
    print(f"Job ID: {result['job_id']}")
    print(f"Images generated: {len(result['files'])}")
    print(f"Output directory: outputs/handstand_test/")
    
except Exception as e:
    print(f"\nERROR: Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
