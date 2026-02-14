#!/usr/bin/env python3
"""
Comfy Agent Benchmark Script

Benchmarks the legacy img_zurbo workflow against the new Comfy ADK agent
using gopher prompts with 4-way comparison.

Test Matrix:
- A: Legacy workflow with raw prompt
- B: Agent (full pipeline) with enhanced prompt
- C: Legacy workflow with enhanced prompt (from B)
- D: Agent workflow with raw prompt (no enhancement)

This creates a 2x2 matrix to isolate effects:
- A vs D: Workflow differences (legacy vs agent) on identical raw prompts
- B vs D: Enhancement effect within agent pipeline
- A vs C: Enhancement effect within legacy workflow
- B vs C: Should be identical (same enhanced prompt, same seed, same workflow)
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
# Expose OPENROUTER key for diagnostics (may be None if missing)
OPENROUTER_API_KEY = getattr(config_module, "OPENROUTER_API_KEY", None)

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
    # Original set
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
    # Female gophers (bias check)
    "A female gopher engineer coding at a standing desk, digital art",
    "A female gopher botanist in a greenhouse, watercolor style",
    "A female gopher CEO leading a boardroom meeting, cinematic lighting",
    "A female gopher surgeon performing delicate surgery, medical illustration style",
    "A female gopher architect designing a skyscraper, architectural drawing style",
    # Go gopher mascot
    "The iconic Go gopher mascot high-fiving a developer, vector art style",
    "The Go gopher mascot riding a cloud, cartoon style",
    "The Go gopher mascot debugging code, pixel art style",
    # Pop culture / Anime styles
    "A gopher dressed as Goku powering up, anime style",
    "A gopher warrior in Saiyan armor, manga style",
    "A cute gopher with Eevee-like fluffy ears, pokemon style",
    "A gopher with electric cheeks like Pikachu, nintendo style",
    "A gopher wearing a Charizard costume, pokemon style",
    "A gopher in Naruto's orange jumpsuit with headband, anime style",
    "A gopher as a One Piece pirate with straw hat, manga style",
    # Additional diverse styles
    "A gopher DJ mixing beats at a neon-lit club, cyberpunk style",
    "A gopher yoga instructor in a zen garden, minimalist style",
]


def generate_prompts(count: int = 32, seed: int = 42) -> List[str]:
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


def run_agent_workflow_raw(
    prompt: str,
    seed: int,
    output_dir: Path,
    filename_prefix: str,
    trace_log_file: Path
) -> Dict[str, Any]:
    """
    Run the agent workflow with raw prompt (no enhancement).
    This is Condition D: Agent with raw prompt to isolate workflow effects.
    
    Args:
        prompt: Raw user prompt (not enhanced)
        seed: Random seed
        output_dir: Directory to save output image
        filename_prefix: Prefix for output filename
        trace_log_file: Path to save agent traces
    
    Returns:
        Result dictionary
    """
    start_time = time.time()
    
    try:
        # Set up trace logging
        trace_callback = FileLoggingCallback(trace_log_file)
        
        logger.info(f"[Agent Raw] Generating image with raw prompt (length: {len(prompt)})")
        logger.debug(f"[Agent Raw] Full raw prompt: {prompt}")
        
        # Generate image using the agent's tool directly with raw prompt (skip enhancement)
        result = generate_image_with_runpod(
            prompt=prompt,
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
        
        # Add prompt info to result
        result["prompt"] = prompt
        result["prompt_length"] = len(prompt)
        
        # Log trace manually
        trace_callback.on_agent_start("comfyui_image_generator", prompt)
        trace_callback.on_tool_call("generate_image_with_runpod", {
            "prompt": prompt,
            "seed": seed
        })
        trace_callback.on_tool_result("generate_image_with_runpod", result, result.get("elapsed_seconds", 0))
        
        if result.get("status") == "success":
            trace_callback.on_agent_complete("comfyui_image_generator", result.get("filepath", ""), time.time() - start_time)
        else:
            trace_callback.on_agent_error("comfyui_image_generator", Exception(result.get("error", "Unknown")), time.time() - start_time)
        
        return result
        
    except Exception as e:
        logger.exception(f"[Agent Raw] Unexpected error: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {e}",
            "error": str(e),
            "elapsed_seconds": time.time() - start_time
        }


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


def find_existing_baseline(output_base_dir: Path) -> Optional[Path]:
    """
    Find the most recent baseline directory to resume from.
    """
    if not output_base_dir.exists():
        return None
    baseline_dirs = []
    for item in output_base_dir.iterdir():
        if item.is_dir() and item.name.startswith("baseline_"):
            ts = item.name.replace("baseline_", "")
            baseline_dirs.append((ts, item))
    if not baseline_dirs:
        return None
    baseline_dirs.sort(key=lambda t: t[0], reverse=True)
    return baseline_dirs[0][1]


def load_existing_results(baseline_dir: Path) -> Optional[Dict[str, Any]]:
    """
    Load existing benchmark results from a baseline directory.
    """
    manifest_file = baseline_dir / "manifest.json"
    if not manifest_file.exists():
        logger.warning(f"No manifest.json found in {baseline_dir}, cannot resume")
        return None
    try:
        with open(manifest_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        required = {"baseline_dir", "timestamp", "prompts", "summary"}
        if not required.issubset(data.keys()):
            logger.warning(f"Invalid manifest structure in {baseline_dir}")
            return None
        return data
    except Exception as e:
        logger.warning(f"Failed to load manifest from {baseline_dir}: {e}")
        return None


def run_benchmark(output_base_dir: Path = None, resume_from: Optional[Path] = None) -> Dict[str, Any]:
    """
    Run the complete benchmark suite, with optional resume support.
    """
    if output_base_dir is None:
        output_base_dir = project_root / "outputs" / "benchmark"

    existing_results = None
    prompts: Optional[List[str]] = None
    baseline_dir = None
    images_dir = None
    logs_dir = None
    timestamp = None

    if resume_from:
        logger.info(f"Attempting to resume from {resume_from}")
        existing_results = load_existing_results(resume_from)
        if existing_results:
            baseline_dir = Path(existing_results["baseline_dir"])
            images_dir = baseline_dir / "images"
            logs_dir = baseline_dir / "logs"
            timestamp = existing_results["timestamp"]
            prompts = [p["raw_prompt"] for p in existing_results["prompts"]]
        else:
            logger.error("Resume requested but manifest could not be loaded; starting fresh.")

    if existing_results is None:
        # Pre-flight check to ensure prompt enhancement is working (auth OK)
        logger.info("Pre-flight check for enhance_prompt...")
        try:
            test_prompt = "test prompt"
            enhanced = enhance_prompt(test_prompt)
            if enhanced == test_prompt:
                logger.warning("enhance_prompt returned original text; auth or model may be failing.")
            else:
                logger.info("✓ enhance_prompt OK")
        except Exception as e:
            raise RuntimeError(f"Pre-flight check failed: {e}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        baseline_dir = output_base_dir / f"baseline_{timestamp}"
        images_dir = baseline_dir / "images"
        logs_dir = baseline_dir / "logs"
        images_dir.mkdir(parents=True, exist_ok=True)
        logs_dir.mkdir(parents=True, exist_ok=True)
        prompts = generate_prompts(count=32, seed=42)
        existing_results = {
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
        logger.info(f"Starting benchmark - baseline: {baseline_dir}")
        logger.info(f"Generated {len(prompts)} prompts")
    else:
        logger.info("Resuming existing benchmark")

    completed_ids = {p["prompt_id"] for p in existing_results["prompts"]}
    logger.info(f"Already completed prompts: {sorted(completed_ids)}")

    for idx, raw_prompt in enumerate(prompts, 1):
        prompt_id = f"{idx:03d}"
        # Skip if prompt already fully successful
        if prompt_id in completed_ids:
            existing_prompt = next(p for p in existing_results["prompts"] if p["prompt_id"] == prompt_id)
            done = all(cond.get("status") == "success" for cond in existing_prompt["conditions"].values())
            if done:
                logger.info(f"Skipping prompt {prompt_id} (already successful)")
                continue
            # If partial, remove and re-run
            existing_results["prompts"] = [p for p in existing_results["prompts"] if p["prompt_id"] != prompt_id]

        logger.info(f"\n{'='*60}")
        logger.info(f"Processing prompt {idx}/{len(prompts)}: {prompt_id}")
        logger.info(f"Raw prompt (length: {len(raw_prompt)}): {raw_prompt}")
        logger.info(f"{'='*60}")

        prompt_seed = hash(raw_prompt) % (2**32)
        prompt_result = {
            "prompt_id": prompt_id,
            "raw_prompt": raw_prompt,
            "raw_prompt_length": len(raw_prompt),
            "seed": prompt_seed,
            "conditions": {},
            "workflow_payloads": {}
        }

        # Condition B: Agent
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

        # Condition A: Legacy raw
        logger.debug(f"[Condition A] Full prompt: {raw_prompt}")
        legacy_raw_result = run_legacy_workflow(
            prompt=raw_prompt,
            seed=prompt_seed,
            output_dir=images_dir,
            filename_prefix=f"{prompt_id}_A_legacy_raw"
        )
        prompt_result["conditions"]["A"] = legacy_raw_result
        if "workflow_payload" in legacy_raw_result:
            prompt_result["workflow_payloads"]["A"] = legacy_raw_result["workflow_payload"]
        if legacy_raw_result.get("status") != "success":
            logger.error(f"[Condition A] Failed: {legacy_raw_result.get('message')}")

        # Condition C: Legacy enhanced
        if enhanced_prompt:
            logger.debug(f"[Condition C] Full enhanced prompt: {enhanced_prompt}")
            legacy_enhanced_result = run_legacy_workflow(
                prompt=enhanced_prompt,
                seed=prompt_seed,
                output_dir=images_dir,
                filename_prefix=f"{prompt_id}_C_legacy_enhanced"
            )
            prompt_result["conditions"]["C"] = legacy_enhanced_result
            if "workflow_payload" in legacy_enhanced_result:
                prompt_result["workflow_payloads"]["C"] = legacy_enhanced_result["workflow_payload"]
            if legacy_enhanced_result.get("status") != "success":
                logger.error(f"[Condition C] Failed: {legacy_enhanced_result.get('message')}")

        # Condition D: Agent raw (no enhancement)
        trace_log_file_raw = logs_dir / f"{prompt_id}_agent_raw_traces.log"
        agent_raw_result = run_agent_workflow_raw(
            prompt=raw_prompt,
            seed=prompt_seed,
            output_dir=images_dir,
            filename_prefix=f"{prompt_id}_D_agent_raw",
            trace_log_file=trace_log_file_raw
        )
        prompt_result["conditions"]["D"] = agent_raw_result
        if "workflow_payload" in agent_raw_result:
            prompt_result["workflow_payloads"]["D"] = agent_raw_result.get("workflow_payload")
        if agent_raw_result.get("status") != "success":
            logger.error(f"[Condition D] Failed: {agent_raw_result.get('message')}")

        # Similarities
        if IMAGEHASH_AVAILABLE:
            sims = {}
            if legacy_raw_result.get("status") == "success" and agent_result.get("status") == "success":
                sims["A_vs_B"] = compute_image_similarity(Path(legacy_raw_result["filepath"]), Path(agent_result["filepath"]))
            if enhanced_prompt and agent_result.get("status") == "success" and prompt_result["conditions"].get("C", {}).get("status") == "success":
                sims["B_vs_C"] = compute_image_similarity(Path(agent_result["filepath"]), Path(prompt_result["conditions"]["C"]["filepath"]))
            if enhanced_prompt and legacy_raw_result.get("status") == "success" and prompt_result["conditions"].get("C", {}).get("status") == "success":
                sims["A_vs_C"] = compute_image_similarity(Path(legacy_raw_result["filepath"]), Path(prompt_result["conditions"]["C"]["filepath"]))
            # New similarity pairs for Condition D
            if legacy_raw_result.get("status") == "success" and agent_raw_result.get("status") == "success":
                sims["A_vs_D"] = compute_image_similarity(Path(legacy_raw_result["filepath"]), Path(agent_raw_result["filepath"]))
            if agent_result.get("status") == "success" and agent_raw_result.get("status") == "success":
                sims["B_vs_D"] = compute_image_similarity(Path(agent_result["filepath"]), Path(agent_raw_result["filepath"]))
            prompt_result["similarities"] = sims
            prompt_result["within_threshold"] = all(
                v is not None and v < existing_results["summary"]["similarity_threshold"]
                for v in sims.values()
            )

        all_success = all(cond.get("status") == "success" for cond in prompt_result["conditions"].values())
        if all_success:
            existing_results["summary"]["successful"] += 1
        else:
            existing_results["summary"]["failed"] += 1

        existing_results["prompts"] = [p for p in existing_results["prompts"] if p["prompt_id"] != prompt_id]
        existing_results["prompts"].append(prompt_result)

        # Save progress after each prompt
        manifest_file = baseline_dir / "manifest.json"
        with open(manifest_file, "w", encoding="utf-8") as f:
            json.dump(existing_results, f, indent=2)
        logger.info(f"[Prompt {prompt_id}] Complete - progress saved")

    # Save final prompt details
    prompts_file = baseline_dir / "prompts.json"
    prompts_data = {
        "timestamp": timestamp,
        "prompts": [
            {
                "prompt_id": p["prompt_id"],
                "raw_prompt": p["raw_prompt"],
                "raw_prompt_length": p.get("raw_prompt_length", len(p.get("raw_prompt", ""))),
                "enhanced_prompt": p.get("enhanced_prompt"),
                "enhanced_prompt_length": len(p.get("enhanced_prompt", "")) if p.get("enhanced_prompt") else 0,
                "seed": p["seed"],
                "workflow_payloads": p.get("workflow_payloads", {})
            }
            for p in existing_results["prompts"]
        ]
    }
    with open(prompts_file, "w", encoding="utf-8") as f:
        json.dump(prompts_data, f, indent=2, ensure_ascii=False)

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

    logger.info(f"\n{'='*60}")
    logger.info("BENCHMARK SUMMARY")
    logger.info(f"{'='*60}")
    logger.info(f"Total prompts: {existing_results['summary']['total']}")
    logger.info(f"Successful: {existing_results['summary']['successful']}")
    logger.info(f"Failed: {existing_results['summary']['failed']}")
    logger.info(f"Baseline directory: {baseline_dir}")
    logger.info(f"{'='*60}\n")
    return existing_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Benchmark Comfy Agent vs Legacy Workflow")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output directory (default: outputs/benchmark)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from the most recent baseline directory"
    )
    parser.add_argument(
        "--resume-from",
        type=Path,
        default=None,
        help="Resume from a specific baseline directory path"
    )
    parser.add_argument(
        "--list-baselines",
        action="store_true",
        help="List available baseline directories and exit"
    )
    
    args = parser.parse_args()
    
    # Handle list baselines
    if args.list_baselines:
        output_dir = args.output_dir or (project_root / "outputs" / "benchmark")
        if output_dir.exists():
            baselines = [p for p in sorted(output_dir.iterdir(), reverse=True) if p.is_dir() and p.name.startswith("baseline_")]
            if baselines:
                print(f"Available baseline directories in {output_dir}:")
                for b in baselines:
                    print(f"  {b.name}")
            else:
                print("No baseline directories found.")
        else:
            print(f"Output directory {output_dir} does not exist.")
        sys.exit(0)

    resume_from = None
    if args.resume_from:
        resume_from = args.resume_from
    elif args.resume:
        output_dir = args.output_dir or (project_root / "outputs" / "benchmark")
        resume_from = find_existing_baseline(output_dir)
        if resume_from:
            print(f"Resuming from most recent baseline: {resume_from}")
        else:
            print("No existing baseline found to resume from.")
            sys.exit(1)

    try:
        results = run_benchmark(output_base_dir=args.output_dir, resume_from=resume_from)
        sys.exit(0 if results["summary"]["failed"] == 0 else 1)
    except KeyboardInterrupt:
        logger.error("\nBenchmark interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Benchmark failed: {e}")
        sys.exit(1)

