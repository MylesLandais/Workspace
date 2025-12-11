#!/usr/bin/env python3
"""
Comfy Agent Benchmark Script

Benchmarks the legacy img_zurbo workflow against the new Comfy ADK agent
using 16 gopher prompts with extended A/B testing.

Test Matrix:
- A: Legacy workflow with raw prompt
- B: Agent (full pipeline) with enhanced prompt
- C: Legacy workflow with enhanced prompt (from B)

This isolates whether output differences come from prompt enhancement vs workflow execution.
"""

import sys
import json
import time
import random
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from io import BytesIO

import requests
from PIL import Image

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import modules directly to avoid agent dependency (__init__.py imports agent)
# We need to set up the package structure for relative imports to work
import importlib.util
import types

# Add agents/comfy to path so relative imports work
comfy_path = project_root / "agents" / "comfy"
if str(comfy_path) not in sys.path:
    sys.path.insert(0, str(comfy_path.parent))

# Import config (no relative imports, so this should work)
config_path = project_root / "agents" / "comfy" / "config.py"
spec = importlib.util.spec_from_file_location("agents.comfy.config", config_path)
config_module = importlib.util.module_from_spec(spec)
# Set __package__ so relative imports work
config_module.__package__ = "agents.comfy"
spec.loader.exec_module(config_module)
RUNPOD_API_KEY = config_module.RUNPOD_API_KEY
RUNPOD_ENDPOINT_ID = config_module.RUNPOD_ENDPOINT_ID

# Import debug (no relative imports in debug.py itself)
debug_path = project_root / "agents" / "comfy" / "debug.py"
spec = importlib.util.spec_from_file_location("agents.comfy.debug", debug_path)
debug_module = importlib.util.module_from_spec(spec)
debug_module.__package__ = "agents.comfy"
spec.loader.exec_module(debug_module)
get_logger = debug_module.get_logger

# Import callbacks (uses relative import from debug)
callbacks_path = project_root / "agents" / "comfy" / "callbacks.py"
spec = importlib.util.spec_from_file_location("agents.comfy.callbacks", callbacks_path)
callbacks_module = importlib.util.module_from_spec(spec)
callbacks_module.__package__ = "agents.comfy"
# Inject the debug module so relative import works
callbacks_module.debug = debug_module
spec.loader.exec_module(callbacks_module)
FileLoggingCallback = callbacks_module.FileLoggingCallback

# Import tools module (uses relative imports from config, workflows, debug)
tools_path = project_root / "agents" / "comfy" / "tools.py"
spec = importlib.util.spec_from_file_location("agents.comfy.tools", tools_path)
tools_module = importlib.util.module_from_spec(spec)
tools_module.__package__ = "agents.comfy"
# Inject dependencies for relative imports
tools_module.config = config_module
tools_module.debug = debug_module
# We'll need to handle workflows import too
workflows_path = project_root / "agents" / "comfy" / "workflows" / "__init__.py"
workflows_spec = importlib.util.spec_from_file_location("agents.comfy.workflows", workflows_path)
workflows_module = importlib.util.module_from_spec(workflows_spec)
workflows_module.__package__ = "agents.comfy.workflows"
# Set up workflows dependencies
workflows_module.config = config_module
workflows_spec.loader.exec_module(workflows_module)
tools_module.workflows = types.ModuleType("workflows")
tools_module.workflows.load_workflow = workflows_module.load_workflow
tools_module.workflows.prepare_workflow_for_api = workflows_module.prepare_workflow_for_api
tools_module.workflows.create_z_image_turbo_workflow = workflows_module.create_z_image_turbo_workflow
spec.loader.exec_module(tools_module)
enhance_prompt = tools_module.enhance_prompt
generate_image_with_runpod = tools_module.generate_image_with_runpod

# Copy workflow creation function to avoid agent dependency
def create_z_image_turbo_workflow(
    prompt: str,
    seed: Optional[int] = None,
    width: int = 1152,
    height: int = 2048,
    steps: int = 4,
    cfg: float = 1.0
) -> Dict[str, Any]:
    """
    Create a Z-Image Turbo workflow programmatically (based on img_zurbo.ipynb).
    
    This creates the exact workflow structure that was proven to work in img_zurbo.ipynb.
    """
    import random
    
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    # This is the exact workflow structure from img_zurbo.ipynb
    workflow = {
        "9": {
            "inputs": {
                "filename_prefix": "Z-Image\\ComfyUI",
                "images": ["43", 0]
            },
            "class_type": "SaveImage",
            "_meta": {"title": "Save Image"}
        },
        "39": {
            "inputs": {
                "clip_name": "qwen_3_4b.safetensors",
                "type": "lumina2",
                "device": "default"
            },
            "class_type": "CLIPLoader",
            "_meta": {"title": "Load CLIP"}
        },
        "40": {
            "inputs": {
                "vae_name": "ae.safetensors"
            },
            "class_type": "VAELoader",
            "_meta": {"title": "Load VAE"}
        },
        "41": {
            "inputs": {
                "width": width,
                "height": height,
                "batch_size": 1
            },
            "class_type": "EmptySD3LatentImage",
            "_meta": {"title": "EmptySD3LatentImage"}
        },
        "42": {
            "inputs": {
                "conditioning": ["45", 0]
            },
            "class_type": "ConditioningZeroOut",
            "_meta": {"title": "ConditioningZeroOut"}
        },
        "43": {
            "inputs": {
                "samples": ["44", 0],
                "vae": ["40", 0]
            },
            "class_type": "VAEDecode",
            "_meta": {"title": "VAE Decode"}
        },
        "44": {
            "inputs": {
                "seed": seed,
                "steps": steps,
                "cfg": cfg,
                "sampler_name": "res_multistep",
                "scheduler": "simple",
                "denoise": 1,
                "model": ["48", 0],
                "positive": ["45", 0],
                "negative": ["42", 0],
                "latent_image": ["41", 0]
            },
            "class_type": "KSampler",
            "_meta": {"title": "KSampler"}
        },
        "45": {
            "inputs": {
                "text": prompt,
                "clip": ["39", 0]
            },
            "class_type": "CLIPTextEncode",
            "_meta": {"title": "CLIP Text Encode (Prompt)"}
        },
        "48": {
            "inputs": {
                "unet_name": "z_image_turbo_bf16.safetensors",
                "weight_dtype": "fp8_e4m3fn"
            },
            "class_type": "UNETLoader",
            "_meta": {"title": "Unet Loader"}
        }
    }
    
    return {
        "input": {
            "workflow": workflow
        }
    }

# Try to import imagehash for similarity comparison
try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False
    print("WARNING: imagehash not available. Install with: pip install imagehash")
    print("Similarity comparison will be disabled.")

logger = get_logger(__name__)


# Gopher prompt templates
GOPHER_PROMPTS = [
    "A cyberpunk gopher astronaut floating in space, digital art",
    "A steampunk gopher mechanic repairing a clockwork machine, digital art",
    "A medieval gopher knight in shining armor, fantasy art",
    "A gopher chef preparing gourmet meals in a futuristic kitchen, digital art",
    "A gopher detective solving mysteries in a noir city, digital art",
    "A gopher pirate sailing the high seas, adventure art",
    "A gopher wizard casting spells in a magical forest, fantasy art",
    "A gopher scientist in a laboratory with glowing beakers, sci-fi art",
    "A gopher musician playing a grand piano in a concert hall, digital art",
    "A gopher artist painting a masterpiece, artistic style",
    "A gopher superhero flying over a cityscape, comic book style",
    "A gopher ninja in a bamboo forest, martial arts style",
    "A gopher cowboy riding through the desert, western art",
    "A gopher samurai with a katana, traditional Japanese art",
    "A gopher astronaut exploring an alien planet, space art",
    "A gopher time traveler in a steampunk time machine, sci-fi art",
]


def generate_prompts(count: int = 16, seed: int = 42) -> List[str]:
    """
    Generate random gopher prompts for benchmarking.
    
    Args:
        count: Number of prompts to generate
        seed: Random seed for reproducibility
    
    Returns:
        List of prompt strings
    """
    random.seed(seed)
    prompts = random.sample(GOPHER_PROMPTS, min(count, len(GOPHER_PROMPTS)))
    return prompts


def run_legacy_workflow(
    prompt: str,
    seed: int,
    output_dir: Path,
    filename_prefix: str
) -> Dict[str, Any]:
    """
    Run the legacy workflow (extracted from img_zurbo.ipynb).
    
    Args:
        prompt: Text prompt for image generation
        seed: Random seed
        output_dir: Directory to save output image
        filename_prefix: Prefix for output filename
    
    Returns:
        Dictionary with status, filepath, timing, etc.
    """
    start_time = time.time()
    
    try:
        # Create workflow payload using the same structure as img_zurbo.ipynb
        workflow_payload = create_z_image_turbo_workflow(
            prompt=prompt,
            seed=seed,
            width=1152,
            height=2048,
            steps=4,
            cfg=1.0
        )
        
        # Store the full payload for review (extract prompt from workflow for verification)
        workflow_prompt_text = None
        if "input" in workflow_payload and "workflow" in workflow_payload["input"]:
            workflow_nodes = workflow_payload["input"]["workflow"]
            # Find the CLIPTextEncode node (usually "45")
            for node_id, node_data in workflow_nodes.items():
                if isinstance(node_data, dict) and node_data.get("class_type") == "CLIPTextEncode":
                    if "inputs" in node_data and "text" in node_data["inputs"]:
                        workflow_prompt_text = node_data["inputs"]["text"]
                        break
        
        # API URLs
        run_url = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/run"
        status_url_template = f"https://api.runpod.ai/v2/{RUNPOD_ENDPOINT_ID}/status/"
        
        # Headers
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Submit job
        logger.info(f"[Legacy] Submitting job with seed {seed}")
        response = requests.post(run_url, headers=headers, json=workflow_payload)
        
        if response.status_code != 200:
            return {
                "status": "error",
                "message": f"API request failed: {response.status_code}",
                "error": response.text,
                "elapsed_seconds": time.time() - start_time
            }
        
        response_data = response.json()
        job_id = response_data.get('id')
        
        if not job_id:
            return {
                "status": "error",
                "message": "No job ID in response",
                "error": response_data,
                "elapsed_seconds": time.time() - start_time
            }
        
        logger.info(f"[Legacy] Job started: {job_id}")
        
        # Poll for completion
        status_url = status_url_template + job_id
        poll_count = 0
        max_polls = 120
        poll_interval = 5
        
        while poll_count < max_polls:
            poll_count += 1
            if poll_count % 10 == 0:
                logger.info(f"[Legacy] Polling... ({poll_count}/{max_polls})")
            
            status_response = requests.get(status_url, headers=headers)
            status_data = status_response.json()
            job_status = status_data.get('status')
            
            if job_status == 'COMPLETED':
                logger.info("[Legacy] Job completed")
                
                # Extract and save image
                try:
                    output_image_data = status_data['output']['images'][0]
                    image_base64 = output_image_data['data']
                    
                    image_bytes = base64.b64decode(image_base64)
                    image = Image.open(BytesIO(image_bytes))
                    
                    # Save image
                    output_dir.mkdir(parents=True, exist_ok=True)
                    filename = f"{filename_prefix}.png"
                    filepath = output_dir / filename
                    image.save(filepath)
                    
                    elapsed = time.time() - start_time
                    logger.info(f"[Legacy] Image saved: {filepath} ({elapsed:.1f}s)")
                    
                    return {
                        "status": "success",
                        "filepath": str(filepath),
                        "filename": filename,
                        "seed": seed,
                        "job_id": job_id,
                        "elapsed_seconds": elapsed,
                        "prompt": prompt,  # Save full prompt in result
                        "prompt_length": len(prompt),
                        "workflow_payload": workflow_payload,  # Save full workflow payload for review
                        "workflow_prompt_verified": workflow_prompt_text == prompt if workflow_prompt_text else None
                    }
                    
                except (KeyError, IndexError, TypeError) as e:
                    return {
                        "status": "error",
                        "message": f"Failed to parse image data: {e}",
                        "error": str(e),
                        "job_id": job_id,
                        "elapsed_seconds": time.time() - start_time
                    }
            
            elif job_status in ['IN_QUEUE', 'IN_PROGRESS']:
                time.sleep(poll_interval)
            else:
                return {
                    "status": "error",
                    "message": f"Job failed with status: {job_status}",
                    "error": status_data.get('error', 'Unknown error'),
                    "job_id": job_id,
                    "elapsed_seconds": time.time() - start_time
                }
        
        return {
            "status": "error",
            "message": "Job timed out",
            "error": "TIMEOUT",
            "job_id": job_id,
            "elapsed_seconds": time.time() - start_time
        }
        
    except Exception as e:
        logger.exception(f"[Legacy] Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}",
            "error": str(e),
            "elapsed_seconds": time.time() - start_time
        }


def run_agent_workflow(
    prompt: str,
    seed: int,
    output_dir: Path,
    filename_prefix: str,
    trace_log_file: Path
) -> Tuple[Dict[str, Any], Optional[str]]:
    """
    Run the agent workflow (full pipeline with prompt enhancement).
    
    Args:
        prompt: Raw user prompt
        seed: Random seed (will be used by agent)
        output_dir: Directory to save output image
        filename_prefix: Prefix for output filename
        trace_log_file: Path to save agent traces
    
    Returns:
        Tuple of (result_dict, enhanced_prompt)
    """
    start_time = time.time()
    
    try:
        # Set up trace logging
        trace_callback = FileLoggingCallback(trace_log_file)
        
        # Note: The agent doesn't directly support callbacks in the current implementation
        # We'll manually trace the tool calls by calling them directly
        # This gives us more control and better traceability
        
        logger.info(f"[Agent] Enhancing prompt (length: {len(prompt)})")
        logger.debug(f"[Agent] Full raw prompt: {prompt}")
        enhanced_prompt = enhance_prompt(prompt)
        logger.info(f"[Agent] Enhanced prompt length: {len(enhanced_prompt)}")
        logger.debug(f"[Agent] Full enhanced prompt: {enhanced_prompt}")
        
        # Generate image using the agent's tool
        logger.info(f"[Agent] Generating image with seed {seed}")
        logger.debug(f"[Agent] Full enhanced prompt being sent to generate_image_with_runpod: {enhanced_prompt}")
        result = generate_image_with_runpod(
            prompt=enhanced_prompt,
            workflow_name=None,  # Use programmatic workflow
            width=1152,
            height=2048,
            seed=seed
        )
        
        # Extract workflow payload from result if available (for review)
        if "workflow_payload" in result:
            result["workflow_payload_saved"] = True
        
        # Move image to benchmark output directory if needed
        if result.get("status") == "success":
            original_filepath = Path(result["filepath"])
            if original_filepath.parent != output_dir:
                # Copy to benchmark directory with new name
                output_dir.mkdir(parents=True, exist_ok=True)
                new_filepath = output_dir / f"{filename_prefix}.png"
                import shutil
                shutil.copy2(original_filepath, new_filepath)
                result["filepath"] = str(new_filepath)
                result["filename"] = new_filepath.name
        
        # Add enhanced prompt to result (ensure full prompts are saved)
        result["enhanced_prompt"] = enhanced_prompt
        result["original_prompt"] = prompt
        result["original_prompt_length"] = len(prompt)
        result["enhanced_prompt_length"] = len(enhanced_prompt) if enhanced_prompt else 0
        
        # Log trace manually
        trace_callback.on_agent_start("comfyui_image_generator", prompt)
        trace_callback.on_tool_call("enhance_prompt", {"user_request": prompt})
        trace_callback.on_tool_result("enhance_prompt", enhanced_prompt, 0.0)
        trace_callback.on_tool_call("generate_image_with_runpod", {
            "prompt": enhanced_prompt,
            "seed": seed
        })
        trace_callback.on_tool_result("generate_image_with_runpod", result, result.get("elapsed_seconds", 0))
        
        if result.get("status") == "success":
            trace_callback.on_agent_complete("comfyui_image_generator", result.get("filepath", ""), time.time() - start_time)
        else:
            trace_callback.on_agent_error("comfyui_image_generator", Exception(result.get("error", "Unknown")), time.time() - start_time)
        
        return result, enhanced_prompt
        
    except Exception as e:
        logger.exception(f"[Agent] Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}",
            "error": str(e),
            "elapsed_seconds": time.time() - start_time
        }, None


def compute_image_similarity(image1_path: Path, image2_path: Path) -> Optional[float]:
    """
    Compute perceptual hash similarity between two images.
    
    Args:
        image1_path: Path to first image
        image2_path: Path to second image
    
    Returns:
        Hash distance (0 = identical, higher = more different)
        Returns None if imagehash is not available
    """
    if not IMAGEHASH_AVAILABLE:
        return None
    
    try:
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)
        
        hash1 = imagehash.phash(img1)
        hash2 = imagehash.phash(img2)
        
        distance = hash1 - hash2
        return float(distance)
    except Exception as e:
        logger.error(f"Failed to compute similarity: {e}")
        return None


def run_benchmark(output_base_dir: Path = None) -> Dict[str, Any]:
    """
    Run the complete benchmark suite.
    
    Args:
        output_base_dir: Base directory for outputs (default: outputs/benchmark)
    
    Returns:
        Dictionary with benchmark results
    """
    if output_base_dir is None:
        output_base_dir = project_root / "outputs" / "benchmark"
    
    # Pre-flight check: Verify OpenRouter auth works
    logger.info("Performing pre-flight check for OpenRouter authentication...")
    try:
        test_prompt = "test"
        enhanced = enhance_prompt(test_prompt)
        if enhanced == test_prompt:
            logger.warning("WARNING: enhance_prompt returned original text. Auth might still be broken or prompt was not enhanced.")
            # We don't abort here because maybe the model decided not to enhance "test", 
            # but we log a strong warning.
        else:
            logger.info("✓ Pre-flight check passed: enhance_prompt is working")
    except Exception as e:
        logger.error(f"CRITICAL: Pre-flight check failed. enhance_prompt raised exception: {e}")
        # We should abort if the agent component is known broken
        raise RuntimeError(f"Agent component broken: {e}")

    # Create baseline directory with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    baseline_dir = output_base_dir / f"baseline_{timestamp}"
    images_dir = baseline_dir / "images"
    logs_dir = baseline_dir / "logs"
    
    images_dir.mkdir(parents=True, exist_ok=True)
    logs_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Starting benchmark - baseline: {baseline_dir}")
    
    # Generate prompts
    prompts = generate_prompts(count=16, seed=42)
    logger.info(f"Generated {len(prompts)} prompts")
    
    # Results storage
    results = {
        "baseline_dir": str(baseline_dir),
        "timestamp": timestamp,
        "prompts": [],
        "summary": {
            "total": len(prompts),
            "successful": 0,
            "failed": 0,
            "similarity_threshold": 10.0
        }
    }
    
    # Process each prompt
    for idx, raw_prompt in enumerate(prompts, 1):
        prompt_id = f"{idx:03d}"
        logger.info(f"\n{'='*60}")
        logger.info(f"Processing prompt {idx}/{len(prompts)}: {prompt_id}")
        logger.info(f"Raw prompt (length: {len(raw_prompt)}): {raw_prompt}")
        logger.info(f"{'='*60}")
        
        # Generate consistent seed for this prompt
        prompt_seed = hash(raw_prompt) % (2**32)
        
        prompt_result = {
            "prompt_id": prompt_id,
            "raw_prompt": raw_prompt,
            "raw_prompt_length": len(raw_prompt),
            "seed": prompt_seed,
            "conditions": {},
            "workflow_payloads": {}  # Store actual payloads sent to RunPod
        }
        
        # Condition B: Run Agent (full pipeline)
        logger.info(f"\n[Condition B] Running Agent workflow...")
        trace_log_file = logs_dir / f"{prompt_id}_agent_traces.log"
        agent_result, enhanced_prompt = run_agent_workflow(
            prompt=raw_prompt,
            seed=prompt_seed,
            output_dir=images_dir,
            filename_prefix=f"{prompt_id}_B_agent",
            trace_log_file=trace_log_file
        )
        prompt_result["conditions"]["B"] = agent_result
        prompt_result["enhanced_prompt"] = enhanced_prompt
        
        if agent_result.get("status") != "success":
            logger.error(f"[Condition B] Failed: {agent_result.get('message')}")
            results["summary"]["failed"] += 1
            results["prompts"].append(prompt_result)
            continue
        
        # Condition A: Legacy with raw prompt
        logger.info(f"\n[Condition A] Running Legacy workflow (raw prompt)...")
        logger.debug(f"[Condition A] Full prompt being sent: {raw_prompt}")
        legacy_raw_result = run_legacy_workflow(
            prompt=raw_prompt,
            seed=prompt_seed,
            output_dir=images_dir,
            filename_prefix=f"{prompt_id}_A_legacy_raw"
        )
        prompt_result["conditions"]["A"] = legacy_raw_result
        # Store workflow payload if available
        if "workflow_payload" in legacy_raw_result:
            prompt_result["workflow_payloads"]["A"] = legacy_raw_result["workflow_payload"]
        
        if legacy_raw_result.get("status") != "success":
            logger.error(f"[Condition A] Failed: {legacy_raw_result.get('message')}")
        
        # Condition C: Legacy with enhanced prompt
        if enhanced_prompt:
            logger.info(f"\n[Condition C] Running Legacy workflow (enhanced prompt)...")
            logger.debug(f"[Condition C] Full enhanced prompt being sent: {enhanced_prompt}")
            legacy_enhanced_result = run_legacy_workflow(
                prompt=enhanced_prompt,
                seed=prompt_seed,
                output_dir=images_dir,
                filename_prefix=f"{prompt_id}_C_legacy_enhanced"
            )
            prompt_result["conditions"]["C"] = legacy_enhanced_result
            # Store workflow payload if available
            if "workflow_payload" in legacy_enhanced_result:
                prompt_result["workflow_payloads"]["C"] = legacy_enhanced_result["workflow_payload"]
            
            if legacy_enhanced_result.get("status") != "success":
                logger.error(f"[Condition C] Failed: {legacy_enhanced_result.get('message')}")
        
        # Compute similarities
        if IMAGEHASH_AVAILABLE:
            similarities = {}
            
            # A vs B
            if (legacy_raw_result.get("status") == "success" and 
                agent_result.get("status") == "success"):
                sim_ab = compute_image_similarity(
                    Path(legacy_raw_result["filepath"]),
                    Path(agent_result["filepath"])
                )
                similarities["A_vs_B"] = sim_ab
                logger.info(f"[Similarity] A vs B: {sim_ab}")
            
            # B vs C
            if (enhanced_prompt and 
                agent_result.get("status") == "success" and 
                legacy_enhanced_result.get("status") == "success"):
                sim_bc = compute_image_similarity(
                    Path(agent_result["filepath"]),
                    Path(legacy_enhanced_result["filepath"])
                )
                similarities["B_vs_C"] = sim_bc
                logger.info(f"[Similarity] B vs C: {sim_bc}")
            
            # A vs C
            if (enhanced_prompt and
                legacy_raw_result.get("status") == "success" and 
                legacy_enhanced_result.get("status") == "success"):
                sim_ac = compute_image_similarity(
                    Path(legacy_raw_result["filepath"]),
                    Path(legacy_enhanced_result["filepath"])
                )
                similarities["A_vs_C"] = sim_ac
                logger.info(f"[Similarity] A vs C: {sim_ac}")
            
            prompt_result["similarities"] = similarities
            
            # Check if within threshold
            all_similar = all(
                v is not None and v < results["summary"]["similarity_threshold"]
                for v in similarities.values()
            )
            prompt_result["within_threshold"] = all_similar
        
        # Count success
        all_success = all(
            cond.get("status") == "success"
            for cond in prompt_result["conditions"].values()
        )
        if all_success:
            results["summary"]["successful"] += 1
        else:
            results["summary"]["failed"] += 1
        
        results["prompts"].append(prompt_result)
        
        logger.info(f"\n[Prompt {prompt_id}] Complete")
    
    # Save results
    manifest_file = baseline_dir / "manifest.json"
    prompts_file = baseline_dir / "prompts.json"
    
    with open(manifest_file, "w") as f:
        json.dump(results, f, indent=2)
    
    # Save prompts separately for easy inspection (with full prompts, no truncation)
    prompts_data = {
        "timestamp": timestamp,
        "prompts": [
            {
                "prompt_id": p["prompt_id"],
                "raw_prompt": p["raw_prompt"],  # Full prompt, no truncation
                "raw_prompt_length": p.get("raw_prompt_length", len(p.get("raw_prompt", ""))),
                "enhanced_prompt": p.get("enhanced_prompt"),  # Full enhanced prompt, no truncation
                "enhanced_prompt_length": len(p.get("enhanced_prompt", "")) if p.get("enhanced_prompt") else 0,
                "seed": p["seed"],
                "workflow_payloads": p.get("workflow_payloads", {})  # Include workflow payloads for review
            }
            for p in results["prompts"]
        ]
    }
    
    with open(prompts_file, "w", encoding="utf-8") as f:
        json.dump(prompts_data, f, indent=2, ensure_ascii=False)
    
    # Also save a separate file with just the prompts for easy copy-paste
    prompts_only_file = baseline_dir / "prompts_only.txt"
    with open(prompts_only_file, "w", encoding="utf-8") as f:
        f.write("=" * 80 + "\n")
        f.write("BENCHMARK PROMPTS - FULL TEXT (NO TRUNCATION)\n")
        f.write("=" * 80 + "\n\n")
        for p in prompts_data["prompts"]:
            f.write(f"Prompt ID: {p['prompt_id']}\n")
            f.write(f"Seed: {p['seed']}\n")
            f.write(f"\nRaw Prompt ({p['raw_prompt_length']} chars):\n")
            f.write(f"{p['raw_prompt']}\n")
            if p.get("enhanced_prompt"):
                f.write(f"\nEnhanced Prompt ({p['enhanced_prompt_length']} chars):\n")
                f.write(f"{p['enhanced_prompt']}\n")
            f.write("\n" + "-" * 80 + "\n\n")
    
    # Print summary
    logger.info(f"\n{'='*60}")
    logger.info("BENCHMARK SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total prompts: {results['summary']['total']}")
    logger.info(f"Successful: {results['summary']['successful']}")
    logger.info(f"Failed: {results['summary']['failed']}")
    logger.info(f"Baseline directory: {baseline_dir}")
    logger.info(f"{'='*60}\n")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Comfy Agent vs Legacy Workflow")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: outputs/benchmark)"
    )
    
    args = parser.parse_args()
    
    try:
        results = run_benchmark(output_base_dir=args.output_dir)
        sys.exit(0 if results["summary"]["failed"] == 0 else 1)
    except KeyboardInterrupt:
        logger.error("\nBenchmark interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Benchmark failed: {e}")
        sys.exit(1)

