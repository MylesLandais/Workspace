"""
RunPod Workflow Runner for Jupyter Notebooks
A portable solution for running ComfyUI workflows on RunPod infrastructure
"""

import requests
import base64
import json
import time
from pathlib import Path
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv 
import os

# --- Configuration ---
load_dotenv()

api_key = os.getenv("RUNPOD_API_KEY")
if not api_key:
    raise ValueError("API key not found. Please create a .env file and add RUNPOD_API_KEY=your_key")

endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID", "a48mrbdsbzg35n")


class RunPodWorkflowRunner:
    """
    A class to handle RunPod workflow execution in Jupyter notebooks.
    
    Example:
        runner = RunPodWorkflowRunner()
        results = runner.run('chroma_workflow.json', seed=12345)
    """
    
    def __init__(self, api_key=None, endpoint_id=None):
        """
        Initialize the workflow runner.
        
        Args:
            api_key: RunPod API key (defaults to env var)
            endpoint_id: RunPod endpoint ID (defaults to env var)
        """
        self.api_key = api_key or os.getenv("RUNPOD_API_KEY")
        self.endpoint_id = endpoint_id or os.getenv("RUNPOD_ENDPOINT_ID", "a48mrbdsbzg35n")
        
        if not self.api_key:
            raise ValueError("API key required. Set RUNPOD_API_KEY in .env or pass to constructor")
        
        self.run_url = f"https://api.runpod.ai/v2/{self.endpoint_id}/run"
        self.status_url_template = f"https://api.runpod.ai/v2/{self.endpoint_id}/status/"
        
        print(f"[INIT] RunPod runner initialized with endpoint: {self.endpoint_id}")
    
    def load_workflow(self, workflow_path):
        """Load workflow from JSON file."""
        try:
            with open(workflow_path, 'r') as f:
                workflow_data = json.load(f)
            print(f"[OK] Loaded workflow from: {workflow_path}")
            return workflow_data
        except FileNotFoundError:
            raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in workflow file: {e}")
    
    def update_seed(self, workflow, seed=None):
        """Update the seed in the workflow."""
        if seed is None:
            seed = int(time.time() * 1000) % (2**32)
        
        # Find nodes in workflow
        if "workflow" in workflow.get("input", {}):
            nodes = workflow["input"]["workflow"]
        else:
            nodes = workflow
        
        seed_updated = False
        for node_id, node_data in nodes.items():
            if isinstance(node_data, dict):
                # RandomNoise node (Chroma workflow style)
                if node_data.get("class_type") == "RandomNoise":
                    node_data["inputs"]["noise_seed"] = seed
                    print(f"[OK] Updated RandomNoise seed to: {seed}")
                    seed_updated = True
                
                # KSampler node (Flux workflow style)
                elif node_data.get("class_type") == "KSampler":
                    # Check inputs.seed first (API format)
                    if "inputs" in node_data and "seed" in node_data["inputs"]:
                        node_data["inputs"]["seed"] = seed
                        print(f"[OK] Updated KSampler seed to: {seed}")
                        seed_updated = True
                    # Fall back to widgets_values (UI format)
                    elif "widgets_values" in node_data and len(node_data["widgets_values"]) > 0:
                        node_data["widgets_values"][0] = seed
                        print(f"[OK] Updated KSampler seed to: {seed}")
                        seed_updated = True
        
        if not seed_updated:
            print(f"[WARN] No seed node found in workflow")
        
        return workflow
    
    def wrap_workflow(self, workflow):
        """Wrap workflow in RunPod API format if needed."""
        if "input" in workflow and "workflow" in workflow["input"]:
            return workflow
        
        return {
            "input": {
                "workflow": workflow
            }
        }
    
    def submit_job(self, workflow_data):
        """Send job to RunPod API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print("[SUBMIT] Sending request to RunPod...")
        response = requests.post(self.run_url, headers=headers, json=workflow_data)
        
        if response.status_code == 200:
            response_data = response.json()
            job_id = response_data.get('id')
            
            if not job_id:
                print("[ERROR] API response did not include a job ID")
                print("Response:", json.dumps(response_data, indent=2))
                return None
            
            print(f"[OK] Job started with ID: {job_id}")
            return job_id
        else:
            print(f"[ERROR] API request failed with status {response.status_code}")
            print("Response:", response.text)
            return None
    
    def poll_status(self, job_id, max_polls=120, poll_interval=5):
        """Poll for job completion."""
        status_url = self.status_url_template + job_id
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"[POLL] Checking job status (timeout: {max_polls * poll_interval}s)...")
        
        for poll_count in range(max_polls):
            if poll_count > 0 and poll_count % 10 == 0:
                print(f"[POLL] Still waiting... ({poll_count}/{max_polls})")
            
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            job_status = status_data.get('status')

            if job_status == 'COMPLETED':
                print("[OK] Job completed successfully!")
                return status_data
            
            elif job_status in ['IN_QUEUE', 'IN_PROGRESS']:
                time.sleep(poll_interval)
            
            else:
                print(f"[ERROR] Job failed with status: {job_status}")
                if 'output' in status_data:
                    print("\n[ERROR] Error details:")
                    print(json.dumps(status_data['output'], indent=2))
                else:
                    print("\n[ERROR] Full response:")
                    print(json.dumps(status_data, indent=2))
                return status_data  # Return data so caller can inspect
        
        print("[ERROR] Job timed out")
        return None
    
    def save_images(self, status_data, output_dir="outputs"):
        """Save generated images from job output."""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        try:
            images = status_data['output']['images']
            saved_files = []
            
            for idx, img_data in enumerate(images):
                image_base64 = img_data['data'] 
                filename = img_data.get('filename', f'output_{idx}.png')
                
                image_bytes = base64.b64decode(image_base64)
                image = Image.open(BytesIO(image_bytes))
                
                filepath = output_path / filename
                image.save(filepath)
                saved_files.append(str(filepath))
                print(f"[SAVE] Image saved: {filepath}")
            
            return saved_files
        
        except (KeyError, IndexError, TypeError) as e:
            print(f"[ERROR] Could not parse image data: {e}")
            return []
    
    def run(self, workflow_path, seed=None, output_dir='outputs', timeout=600, poll_interval=5):
        """
        Run a workflow end-to-end.
        
        Args:
            workflow_path: Path to workflow JSON file
            seed: Random seed for generation (None = random)
            output_dir: Directory to save output images
            timeout: Maximum wait time in seconds
            poll_interval: How often to check job status (seconds)
        
        Returns:
            dict: {
                'success': bool,
                'job_id': str,
                'files': list of saved file paths,
                'status_data': full API response
            }
        """
        print(f"\n{'='*60}")
        print(f"Running workflow: {workflow_path}")
        print(f"{'='*60}\n")
        
        # Load and prepare workflow
        workflow = self.load_workflow(workflow_path)
        workflow = self.update_seed(workflow, seed)
        workflow = self.wrap_workflow(workflow)
        
        # Submit job
        job_id = self.submit_job(workflow)
        if not job_id:
            return {
                'success': False,
                'job_id': None,
                'files': [],
                'status_data': None
            }
        
        # Poll for completion
        max_polls = timeout // poll_interval
        status_data = self.poll_status(job_id, max_polls, poll_interval)
        
        if not status_data:
            return {
                'success': False,
                'job_id': job_id,
                'files': [],
                'status_data': status_data
            }
        
        # Save images
        saved_files = self.save_images(status_data, output_dir)
        
        success = len(saved_files) > 0
        print(f"\n{'='*60}")
        if success:
            print(f"[SUCCESS] Generated {len(saved_files)} image(s)")
        else:
            print("[FAILED] No images generated")
        print(f"{'='*60}\n")
        
        return {
            'success': success,
            'job_id': job_id,
            'files': saved_files,
            'status_data': status_data
        }


# Convenience function for quick usage
def run_workflow(workflow_path, seed=None, output_dir='outputs', timeout=600, poll_interval=5):
    """
    Quick function to run a workflow without creating a runner object.
    
    Example:
        results = run_workflow('chroma_workflow.json', seed=12345)
        print(results['files'])
    """
    runner = RunPodWorkflowRunner()
    return runner.run(workflow_path, seed, output_dir, timeout, poll_interval)


# Display usage info when imported
print("\n" + "="*60)
print("RunPod Workflow Runner - Notebook Mode")
print("="*60)
print("\nQuick Start:")
print("  results = run_workflow('workflow.json')")
print("  results = run_workflow('workflow.json', seed=12345)")
print("\nAdvanced Usage:")
print("  runner = RunPodWorkflowRunner()")
print("  results = runner.run('workflow.json', output_dir='my_images')")
print("\nResults structure:")
print("  results['success']     - True/False")
print("  results['job_id']      - RunPod job ID")
print("  results['files']       - List of saved image paths")
print("  results['status_data'] - Full API response")
print("="*60 + "\n")