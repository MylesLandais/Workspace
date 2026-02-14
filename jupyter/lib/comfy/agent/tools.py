"""
ComfyUI Image Generation Tools

Tools for generating images using RunPod ComfyUI workers.
"""

import os
import sys
import time
import base64
import random
import json
from pathlib import Path
from typing import Dict, Any, Optional

# Add notebooks/comfy to path to import RunPodWorkflowRunner
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "notebooks" / "comfy"))

from runpod_runner import RunPodWorkflowRunner
from .config import RUNPOD_API_KEY, RUNPOD_ENDPOINT_ID, OUTPUT_DIR, MODEL_NAME, OPENROUTER_API_KEY
from .workflows import load_workflow, prepare_workflow_for_api, create_z_image_turbo_workflow
from .debug import get_logger, Timer
from .prompts import ZIT_PROMPT_TEMPLATE, WORKFLOW_SELECTOR_INSTRUCTION

# Module logger
logger = get_logger(__name__)


def generate_image_with_runpod(
    prompt: str,
    workflow_name: Optional[str] = None,
    width: int = 1280,
    height: int = 1440,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Generate an image using RunPod ComfyUI workflow.
    
    This tool:
    1. Loads the specified workflow template
    2. Injects the prompt and parameters
    3. Submits to RunPod
    4. Polls for completion
    5. Saves the image locally
    
    Args:
        prompt: Text prompt for image generation (should be Chinese for Z-Image Turbo)
        workflow_name: Name of workflow JSON file in Datasets/Comfy_Workflow/
        width: Image width in pixels
        height: Image height in pixels
        seed: Random seed (None = random)
    
    Returns:
        Dictionary with status, filepath, seed, and metadata.
        Note: Does NOT return image data to avoid token overflow.
    """
    logger.info(f"Starting image generation with workflow: {workflow_name}")
    logger.debug(f"Parameters: width={width}, height={height}, seed={seed}")
    
    with Timer("total_generation", logger) as total_timer:
        try:
            # Validate inputs
            if not prompt or not prompt.strip():
                logger.error("Empty prompt provided")
                return {
                    "status": "error",
                    "message": "Prompt cannot be empty",
                    "error": "INVALID_INPUT"
                }
            
            # Generate seed if not provided
            if seed is None:
                seed = random.randint(0, 2**32 - 1)
                logger.debug(f"Generated random seed: {seed}")
            
            # Load or create workflow
            with Timer("load_workflow", logger):
                if workflow_name is None:
                    # Use programmatic Z-Image Turbo workflow
                    logger.info("Using programmatic Z-Image Turbo workflow")
                    workflow_payload = create_z_image_turbo_workflow(
                        prompt=prompt,
                        seed=seed,
                        width=width,
                        height=height
                    )
                    logger.debug("Created programmatic workflow")
                else:
                    # Load workflow from JSON file
                    try:
                        workflow = load_workflow(workflow_name)
                        logger.debug(f"Loaded workflow: {workflow_name}")
                        
                        # Prepare workflow with parameters
                        with Timer("prepare_workflow", logger):
                            workflow_payload = prepare_workflow_for_api(
                                workflow=workflow,
                                prompt=prompt,
                                seed=seed,
                                width=width,
                                height=height
                            )
                            logger.debug("Workflow payload prepared")
                    except FileNotFoundError as e:
                        logger.error(f"Workflow not found: {workflow_name}")
                        return {
                            "status": "error",
                            "message": f"Workflow not found: {workflow_name}",
                            "error": str(e)
                        }
            
            # Initialize RunPod runner
            runner = RunPodWorkflowRunner(
                api_key=RUNPOD_API_KEY,
                endpoint_id=RUNPOD_ENDPOINT_ID
            )
            
            # Submit job
            logger.info(f"Submitting to RunPod (endpoint: {RUNPOD_ENDPOINT_ID})")
            logger.info(f"Prompt: {prompt[:100]}..." if len(prompt) > 100 else f"Prompt: {prompt}")
            logger.info(f"Seed: {seed}")
            
            with Timer("submit_job", logger):
                job_id = runner.submit_job(workflow_payload)
                if not job_id:
                    logger.error("RunPod job submission failed")
                    return {
                        "status": "error",
                        "message": "Failed to submit job to RunPod",
                        "error": "SUBMISSION_FAILED"
                    }
                logger.info(f"Job submitted: {job_id}")
            
            # Poll for completion
            logger.info(f"Polling for completion (max 10 minutes)...")
            with Timer("poll_status", logger):
                status_data = runner.poll_status(job_id, max_polls=120, poll_interval=5)
        
            if not status_data or status_data.get("status") != "COMPLETED":
                error_msg = status_data.get("error", "Unknown error") if status_data else "Timeout"
                logger.error(f"Image generation failed: {error_msg}")
                return {
                    "status": "error",
                    "message": "Image generation failed",
                    "error": error_msg,
                    "job_id": job_id
                }
            
            logger.info("Generation completed, processing image...")
            
            # Extract and save image
            try:
                with Timer("save_image", logger):
                    images = status_data["output"]["images"]
                    image_data = images[0]["data"]
                    
                    # Decode base64 image
                    image_bytes = base64.b64decode(image_data)
                    logger.debug(f"Image size: {len(image_bytes)} bytes")
                    
                    # Save to outputs directory
                    OUTPUT_DIR.mkdir(exist_ok=True)
                    filename = f"comfyui_{int(time.time())}_{seed}.png"
                    filepath = OUTPUT_DIR / filename
                    
                    with open(filepath, "wb") as f:
                        f.write(image_bytes)
                    
                    logger.info(f"Image saved: {filepath}")
                
                # Return metadata only (NO base64 data to avoid token overflow)
                result = {
                    "status": "success",
                    "message": f"Image generated successfully in {total_timer.elapsed:.1f}s",
                    "filepath": str(filepath),
                    "filename": filename,
                    "seed": seed,
                    "width": width,
                    "height": height,
                    "workflow": workflow_name,
                    "prompt_length": len(prompt),
                    "job_id": job_id,
                    "elapsed_seconds": total_timer.elapsed
                }
                logger.info(f"Generation complete! Elapsed: {total_timer.elapsed:.1f}s")
                return result
                
            except (KeyError, IndexError, TypeError) as e:
                logger.error(f"Failed to parse RunPod response: {e}")
                return {
                    "status": "error",
                    "message": "Failed to parse image data from RunPod response",
                    "error": str(e),
                    "job_id": job_id
                }
        
        except Exception as e:
            logger.exception(f"Unexpected error during image generation: {e}")
            return {
                "status": "error",
                "message": "Unexpected error during image generation",
                "error": str(e)
            }


def list_workflows() -> Dict[str, Any]:
    """
    List available ComfyUI workflow templates.
    
    Returns:
        Dictionary with workflow names and descriptions
    """
    from .workflows import list_available_workflows
    
    try:
        logger.debug("Listing available workflows")
        workflows = list_available_workflows()
        logger.info(f"Found {len(workflows)} workflows")
        return {
            "status": "success",
            "workflows": workflows,
            "count": len(workflows)
        }
    except Exception as e:
        logger.error(f"Failed to list workflows: {e}")
        return {
            "status": "error",
            "message": "Failed to list workflows",
            "error": str(e)
        }


def enhance_prompt(user_request: str) -> str:
    """
    Enhance the user's prompt using Z-Image Turbo methodology via LLM.
    
    Args:
        user_request: The original user request/prompt
        
    Returns:
        The enhanced prompt (usually in Chinese) optimized for the model.
    """
    import litellm
    import sys
    import io
    
    logger.info(f"Enhancing prompt: {user_request[:50]}...")
    
    try:
        messages = [
            {"role": "system", "content": ZIT_PROMPT_TEMPLATE},
            {"role": "user", "content": user_request}
        ]
        
        # Suppress litellm stderr output (provider list messages)
        original_stderr = sys.stderr
        null_stderr = io.StringIO()
        sys.stderr = null_stderr
        try:
            response = litellm.completion(
                model=MODEL_NAME,
                messages=messages,
                api_key=OPENROUTER_API_KEY
            )
        finally:
            sys.stderr = original_stderr
        
        enhanced = response.choices[0].message.content
        logger.info("Prompt enhanced successfully")
        return enhanced
        
    except Exception as e:
        logger.error(f"Failed to enhance prompt: {e}")
        # Fallback to original
        return user_request


def select_workflow(user_request: str, enhanced_prompt: str) -> Dict[str, Any]:
    """
    Select the best workflow based on request and prompt.
    
    By default, returns None to use the programmatic Z-Image Turbo workflow
    (proven to work from img_zurbo.ipynb). Can also select from JSON workflows.
    
    Args:
        user_request: Original request
        enhanced_prompt: The detailed prompt
        
    Returns:
        Dictionary with 'workflow_name' (None for programmatic) and 'reasoning'.
    """
    # Default to programmatic workflow (proven to work from img_zurbo.ipynb)
    logger.info("Using programmatic Z-Image Turbo workflow (from img_zurbo.ipynb)")
    return {
        "workflow_name": None,  # None means use programmatic workflow
        "reasoning": "Using proven programmatic Z-Image Turbo workflow from img_zurbo.ipynb"
    }


__all__ = [
    "generate_image_with_runpod",
    "list_workflows",
    "enhance_prompt",
    "select_workflow"
]
