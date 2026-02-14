#!/usr/bin/env python3
"""
Generate Handstand Orbital 360° Images using Nano Banana AIO Workflow

This script:
1. Loads orbital handstand prompts from JSON file
2. Uses Nano Banana AIO workflow with Gemini 3 Pro
3. Generates images via RunPod API
4. Saves outputs to organized directory structure

Usage (Docker):
    docker compose exec jupyterlab python run_handstand_orbital_generations.py

Usage (Local):
    python run_handstand_orbital_generations.py
"""

import json
import time
import base64
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import requests

# Configuration
WORKFLOW_PATH = Path(__file__).parent / "data" / "Comfy_Workflow" / "api_google_gemini_image.json"
PROMPTS_PATH = Path(__file__).parent / "data" / "Prompts" / "shay_handstand_orbital_360_prompts.json"
OUTPUT_DIR = Path(__file__).parent / "outputs" / "handstand_orbital_360"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Environment variables (load from .env or environment)
import os
from dotenv import load_dotenv

load_dotenv()

RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID")

if not RUNPOD_API_KEY:
    print("ERROR: RUNPOD_API_KEY not found in environment or .env file")
    print("Please set RUNPOD_API_KEY and RUNPOD_ENDPOINT_ID in your .env file")
    sys.exit(1)


class HandstandOrbitalGenerator:
    """Generate handstand orbital images using Nano Banana AIO workflow."""
    
    def __init__(self, api_key: str, endpoint_id: str):
        self.api_key = api_key
        self.endpoint_id = endpoint_id
        self.run_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        self.status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/"
        
        print(f"[INIT] Handstand Orbital Generator initialized")
        print(f"[INIT] Endpoint: {endpoint_id}")
        print(f"[INIT] Output dir: {OUTPUT_DIR}")
    
    def load_prompts(self, prompts_path: Path) -> List[Dict[str, Any]]:
        """Load handstand orbital prompts from JSON file."""
        if not prompts_path.exists():
            raise FileNotFoundError(f"Prompts file not found: {prompts_path}")
        
        with open(prompts_path, 'r') as f:
            data = json.load(f)
        
        prompts = data.get("prompts", [])
        print(f"[LOAD] Loaded {len(prompts)} prompts from {prompts_path.name}")
        return prompts
    
    def load_workflow(self) -> Dict[str, Any]:
        """Load Nano Banana AIO workflow template."""
        if not WORKFLOW_PATH.exists():
            raise FileNotFoundError(f"Workflow not found: {WORKFLOW_PATH}")
        
        with open(WORKFLOW_PATH, 'r') as f:
            workflow = json.load(f)
        
        print(f"[LOAD] Loaded Nano Banana AIO workflow")
        return workflow
    
    def prepare_workflow(self, workflow: Dict, prompt_text: str, seed: int, 
                      image_count: int = 8, aspect_ratio: str = "1:1", 
                      image_size: str = "2K") -> Dict[str, Any]:
        """Inject prompt and parameters into Nano Banana workflow."""
        
        # Create a copy to modify
        workflow = json.loads(json.dumps(workflow))
        
        # Find and update the NanoBananaAIO node (node 38)
        for node_id, node_data in workflow.items():
            if isinstance(node_data, dict) and node_data.get("class_type") == "NanoBananaAIO":
                node_data["inputs"]["prompt"] = prompt_text
                node_data["inputs"]["seed"] = seed
                node_data["inputs"]["image_count"] = image_count
                node_data["inputs"]["aspect_ratio"] = aspect_ratio
                node_data["inputs"]["image_size"] = image_size
                node_data["inputs"]["use_search"] = False  # Use identity references
                node_data["inputs"]["temperature"] = 1.0
                
                print(f"[PREP] Updated Nano Banana node {node_id}")
                print(f"[PREP]   Seed: {seed}")
                print(f"[PREP]   Image count: {image_count}")
                print(f"[PREP]   Aspect ratio: {aspect_ratio}")
                print(f"[PREP]   Image size: {image_size}")
                
                return workflow
        
        raise ValueError("NanoBananaAIO node not found in workflow")
    
    def submit_job(self, workflow: Dict) -> Optional[str]:
        """Submit job to RunPod API."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        print(f"\n[SUBMIT] Sending job to RunPod...")
        try:
            response = requests.post(self.run_url, headers=headers, json=workflow, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("id")
                if job_id:
                    print(f"[OK] Job submitted: {job_id}")
                    return job_id
                else:
                    print(f"[ERROR] No job ID in response: {data}")
                    return None
            else:
                print(f"[ERROR] API error: {response.status_code}")
                print(f"[ERROR] Response: {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            print(f"[ERROR] Request failed: {e}")
            return None
    
    def poll_status(self, job_id: str, timeout: int = 600, poll_interval: int = 10) -> Optional[Dict]:
        """Poll job status until completion or timeout."""
        max_polls = timeout // poll_interval
        
        for poll_count in range(max_polls):
            if poll_count > 0 and poll_count % 5 == 0:
                print(f"[POLL] Waiting... ({poll_count * poll_interval}s elapsed)")
            
            try:
                response = requests.get(
                    f"{self.status_url}{job_id}",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status")
                    
                    if status == "COMPLETED":
                        print(f"[OK] Job completed: {job_id}")
                        return data
                    elif status in ["IN_QUEUE", "IN_PROGRESS"]:
                        time.sleep(poll_interval)
                        continue
                    else:
                        print(f"[ERROR] Job failed: {status}")
                        if "output" in data:
                            print(f"[ERROR] Output: {data['output']}")
                        return None
                else:
                    print(f"[ERROR] Status check failed: {response.status_code}")
                    time.sleep(poll_interval)
                    
            except requests.exceptions.RequestException as e:
                print(f"[ERROR] Polling error: {e}")
                time.sleep(poll_interval)
        
        print(f"[ERROR] Job timed out after {timeout}s")
        return None
    
    def save_images(self, status_data: Dict, prompt_id: str, prompt_name: str) -> List[str]:
        """Save generated images to organized directory structure."""
        output_dir = OUTPUT_DIR / prompt_id
        output_dir.mkdir(exist_ok=True)
        
        saved_files = []
        
        try:
            images = status_data.get("output", {}).get("images", [])
            
            for idx, img_data in enumerate(images):
                image_base64 = img_data.get("data")
                if not image_base64:
                    print(f"[WARN] No image data in image {idx}")
                    continue
                
                # Decode and save image
                image_bytes = base64.b64decode(image_base64)
                
                filename = f"{prompt_name}_{idx+1:02d}.png"
                filepath = output_dir / filename
                
                with open(filepath, 'wb') as f:
                    f.write(image_bytes)
                
                saved_files.append(str(filepath))
                print(f"[SAVE] Saved: {filename}")
            
            return saved_files
            
        except Exception as e:
            print(f"[ERROR] Failed to save images: {e}")
            return []
    
    def run_batch(self, prompt_ids: Optional[List[str]] = None, delay: int = 5):
        """
        Run batch of handstand orbital prompts.
        
        Args:
            prompt_ids: List of prompt IDs to run (None = all)
            delay: Delay between job submissions in seconds
        """
        # Load prompts
        prompts = self.load_prompts(PROMPTS_PATH)
        
        # Filter by IDs if specified
        if prompt_ids:
            prompts = [p for p in prompts if p["id"] in prompt_ids]
            print(f"[BATCH] Filtered to {len(prompts)} prompts")
        
        # Load workflow template
        workflow_template = self.load_workflow()
        
        # Results tracking
        results = {
            "timestamp": datetime.now().isoformat(),
            "total": len(prompts),
            "completed": 0,
            "failed": 0,
            "jobs": []
        }
        
        # Process each prompt
        for i, prompt in enumerate(prompts, 1):
            print(f"\n{'='*70}")
            print(f"PROMPT {i}/{len(prompts)}: {prompt['id']}")
            print(f"Name: {prompt['name']}")
            print(f"{'='*70}\n")
            
            # Generate seed
            seed = int(time.time() * 1000) % (2**32)
            
            try:
                # Prepare workflow with prompt
                workflow = self.prepare_workflow(
                    workflow_template,
                    prompt_text=prompt["prompt"],
                    seed=seed,
                    image_count=8,  # Generate 8 variations per prompt
                    aspect_ratio="1:1",
                    image_size="2K"
                )
                
                # Submit job
                job_id = self.submit_job(workflow)
                if not job_id:
                    results["failed"] += 1
                    results["jobs"].append({
                        "prompt_id": prompt["id"],
                        "status": "FAILED_TO_SUBMIT",
                        "seed": seed
                    })
                    continue
                
                # Poll for completion
                status_data = self.poll_status(job_id, timeout=600, poll_interval=10)
                
                if status_data and status_data.get("status") == "COMPLETED":
                    # Save images
                    saved_files = self.save_images(
                        status_data,
                        prompt_id=prompt["id"],
                        prompt_name=prompt["name"].replace(" ", "_").replace("/", "_")
                    )
                    
                    results["completed"] += 1
                    results["jobs"].append({
                        "prompt_id": prompt["id"],
                        "job_id": job_id,
                        "status": "COMPLETED",
                        "seed": seed,
                        "images_saved": len(saved_files),
                        "files": saved_files
                    })
                else:
                    results["failed"] += 1
                    results["jobs"].append({
                        "prompt_id": prompt["id"],
                        "job_id": job_id,
                        "status": "FAILED",
                        "seed": seed
                    })
                
                # Delay between submissions to avoid rate limiting
                if i < len(prompts):
                    print(f"\n[WAIT] Waiting {delay}s before next prompt...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"[ERROR] Exception processing prompt {prompt['id']}: {e}")
                results["failed"] += 1
                results["jobs"].append({
                    "prompt_id": prompt["id"],
                    "status": "EXCEPTION",
                    "error": str(e),
                    "seed": seed
                })
        
        # Save results summary
        results_file = OUTPUT_DIR / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n{'='*70}")
        print(f"BATCH COMPLETE")
        print(f"Total: {results['total']}")
        print(f"Completed: {results['completed']}")
        print(f"Failed: {results['failed']}")
        print(f"Results saved to: {results_file}")
        print(f"{'='*70}\n")
        
        return results


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate Handstand Orbital 360° images using Nano Banana AIO",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all 11 handstand prompts
  python run_handstand_orbital_generations.py
  
  # Run only first pass (7 prompts)
  python run_handstand_orbital_generations.py --prompt-ids HANDSTAND_ORBITAL_01,HANDSTAND_ORBITAL_02,HANDSTAND_ORBITAL_03,HANDSTAND_ORBITAL_04,HANDSTAND_ORBITAL_05,HANDSTAND_ORBITAL_06,HANDSTAND_ORBITAL_07
  
  # Run only second pass with props (4 prompts)
  python run_handstand_orbital_generations.py --prompt-ids HANDSTAND_PROP_01,HANDSTAND_PROP_02,HANDSTAND_PROP_03,HANDSTAND_PROP_04
  
  # Test single prompt
  python run_handstand_orbital_generations.py --prompt-ids HANDSTAND_ORBITAL_05
        """
    )
    
    parser.add_argument(
        "--prompt-ids",
        type=str,
        help="Comma-separated list of prompt IDs to run (e.g., HANDSTAND_ORBITAL_01,HANDSTAND_ORBITAL_02)"
    )
    parser.add_argument(
        "--delay",
        type=int,
        default=5,
        help="Delay between job submissions in seconds (default: 5)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Load and display prompts without submitting jobs"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = HandstandOrbitalGenerator(
        api_key=RUNPOD_API_KEY,
        endpoint_id=RUNPOD_ENDPOINT_ID
    )
    
    # Dry run mode
    if args.dry_run:
        prompts = generator.load_prompts(PROMPTS_PATH)
        print(f"\n[DRY RUN] Loaded {len(prompts)} prompts")
        print(f"\n[DRY RUN] Prompt IDs:")
        for p in prompts:
            print(f"  - {p['id']}: {p['name']}")
        return
    
    # Parse prompt IDs if provided
    prompt_ids = None
    if args.prompt_ids:
        prompt_ids = [pid.strip() for pid in args.prompt_ids.split(",")]
        print(f"[MAIN] Running specified prompts: {len(prompt_ids)}")
    
    # Run batch
    generator.run_batch(prompt_ids=prompt_ids, delay=args.delay)


if __name__ == "__main__":
    main()
