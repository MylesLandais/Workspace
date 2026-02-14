"""
ComfyUI Workflow Loader and Management Utilities
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..config import WORKFLOW_DIR


def list_available_workflows() -> List[str]:
    """
    List all available ComfyUI workflow JSON files.
    
    Returns:
        List of workflow filenames
    """
    if not WORKFLOW_DIR.exists():
        raise FileNotFoundError(f"Workflow directory not found: {WORKFLOW_DIR}")
    
    workflows = [f.name for f in WORKFLOW_DIR.glob("*.json")]
    return sorted(workflows)


def load_workflow(name: str) -> Dict[str, Any]:
    """
    Load a ComfyUI workflow from JSON file.
    
    Args:
        name: Workflow filename (e.g., "Basic Z-image turbo -Icekiub.json")
    
    Returns:
        Workflow dictionary
    
    Raises:
        FileNotFoundError: If workflow file doesn't exist
        json.JSONDecodeError: If JSON is invalid
    """
    workflow_path = WORKFLOW_DIR / name
    
    if not workflow_path.exists():
        available = list_available_workflows()
        raise FileNotFoundError(
            f"Workflow '{name}' not found. Available workflows: {', '.join(available)}"
        )
    
    with open(workflow_path, 'r', encoding='utf-8') as f:
        workflow = json.load(f)
    
    return workflow


def get_modifiable_nodes(workflow: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Extract key nodes that are commonly modified in workflows.
    
    Args:
        workflow: ComfyUI workflow dictionary
    
    Returns:
        Dictionary mapping node IDs to their configurations
    """
    nodes = workflow.get("nodes", [])
    modifiable = {}
    
    # Node types we commonly modify
    target_types = {
        "CLIPTextEncode": "prompt",
        "RandomNoise": "seed",
        "EmptyLatentImage": "dimensions",
        "EmptySD3LatentImage": "dimensions",
        "UNETLoader": "model",
        "LoraLoaderModelOnly": "lora",
        "KSampler": "sampler_settings",
        "BasicScheduler": "scheduler_settings"
    }
    
    for node in nodes:
        node_type = node.get("type")
        node_id = str(node.get("id"))
        
        if node_type in target_types:
            modifiable[node_id] = {
                "type": node_type,
                "purpose": target_types[node_type],
                "current_widgets": node.get("widgets_values", []),
                "inputs": node.get("inputs", [])
            }
    
    return modifiable




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
    
    Args:
        prompt: Text prompt for image generation
        seed: Random seed (None = random)
        width: Image width in pixels (default: 1152)
        height: Image height in pixels (default: 2048)
        steps: Number of generation steps (default: 4)
        cfg: Guidance scale (default: 1.0)
    
    Returns:
        Workflow ready for RunPod API in the format: {"input": {"workflow": {...}}}
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

def prepare_workflow_for_api(
    workflow: Dict[str, Any],
    prompt: str,
    seed: Optional[int] = None,
    width: int = 1280,
    height: int = 1440
) -> Dict[str, Any]:
    """
    Prepare a workflow for RunPod API submission.
    
    This function handles both API-format (dict) and UI-format (list) workflows.
    For UI-format, it attempts to convert to API-format using heuristics for common nodes.
    
    Args:
        workflow: ComfyUI workflow dictionary
        prompt: Text prompt for image generation
        seed: Random seed (None = random)
        width: Image width
        height: Image height
    
    Returns:
        Workflow ready for RunPod API
    """
    import random
    
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    # Helper to convert UI inputs list to API inputs dict
    def convert_ui_inputs(ui_inputs):
        api_inputs = {}
        if isinstance(ui_inputs, list):
            for inp in ui_inputs:
                name = inp.get("name")
                link = inp.get("link")
                if name and link is not None:
                    # API format for links: [link_id, slot_index]
                    api_inputs[name] = [str(link), 0]
        elif isinstance(ui_inputs, dict):
            return ui_inputs.copy()
        return api_inputs

    # Extract nodes from workflow
    if "nodes" in workflow:
        # UI export format - convert to API format
        workflow_nodes = {}
        for node in workflow["nodes"]:
            node_id = str(node["id"])
            node_type = node.get("type")
            
            # Convert inputs (links)
            inputs_dict = convert_ui_inputs(node.get("inputs", []))
            
            # Heuristic mapping of widgets_values to inputs
            widgets = node.get("widgets_values", [])
            
            # Map common node widgets to inputs
            if node_type == "CLIPTextEncode" and len(widgets) >= 1:
                inputs_dict["text"] = widgets[0]
                
            elif node_type == "VAELoader" and len(widgets) >= 1:
                inputs_dict["vae_name"] = widgets[0]
                
            elif node_type == "CheckpointLoaderSimple" and len(widgets) >= 1:
                inputs_dict["ckpt_name"] = widgets[0]
                
            elif node_type in ["EmptyLatentImage", "EmptySD3LatentImage"] and len(widgets) >= 2:
                inputs_dict["width"] = widgets[0]
                inputs_dict["height"] = widgets[1]
                if len(widgets) >= 3:
                    inputs_dict["batch_size"] = widgets[2]
            
            elif node_type == "RandomNoise" and len(widgets) >= 1:
                inputs_dict["noise_seed"] = widgets[0]
                
            elif node_type == "KSampler" and len(widgets) >= 4:
                # KSampler widgets: seed, control_after_generate, steps, cfg, sampler_name, scheduler, denoise
                inputs_dict["seed"] = widgets[0]
                inputs_dict["steps"] = widgets[2]
                inputs_dict["cfg"] = widgets[3]
                if len(widgets) >= 5: inputs_dict["sampler_name"] = widgets[4]
                if len(widgets) >= 6: inputs_dict["scheduler"] = widgets[5]
                if len(widgets) >= 7: inputs_dict["denoise"] = widgets[6]

            workflow_nodes[node_id] = {
                "inputs": inputs_dict,
                "class_type": node_type,
                "_meta": {"title": node_type}
            }
    else:
        # Already in API format (mostly)
        workflow_nodes = workflow.copy()
    
    # Apply overrides
    overrides = {}
    
    # Find and update prompt nodes (CLIPTextEncode)
    for node_id, node_data in workflow_nodes.items():
        node_type = node_data.get("class_type")
        
        if node_type == "CLIPTextEncode":
            if "inputs" not in overrides.get(node_id, {}):
                overrides[node_id] = {"inputs": {}}
            overrides[node_id]["inputs"]["text"] = prompt
        
        elif node_type == "RandomNoise":
            if "inputs" not in overrides.get(node_id, {}):
                overrides[node_id] = {"inputs": {}}
            overrides[node_id]["inputs"]["noise_seed"] = seed
        
        elif node_type == "KSampler":
            if "inputs" not in overrides.get(node_id, {}):
                overrides[node_id] = {"inputs": {}}
            overrides[node_id]["inputs"]["seed"] = seed
        
        elif node_type in ["EmptyLatentImage", "EmptySD3LatentImage"]:
            if "inputs" not in overrides.get(node_id, {}):
                overrides[node_id] = {"inputs": {}}
            overrides[node_id]["inputs"]["width"] = width
            overrides[node_id]["inputs"]["height"] = height
    
    # Apply overrides
    for node_id, override_data in overrides.items():
        if node_id in workflow_nodes:
            if "inputs" in override_data:
                # Ensure inputs is a dict before updating
                if "inputs" not in workflow_nodes[node_id] or not isinstance(workflow_nodes[node_id]["inputs"], dict):
                    workflow_nodes[node_id]["inputs"] = {}
                
                workflow_nodes[node_id]["inputs"].update(override_data["inputs"])
    
    # Wrap in RunPod API format
    return {
        "input": {
            "workflow": workflow_nodes
        }
    }


__all__ = [
    "list_available_workflows",
    "load_workflow",
    "get_modifiable_nodes",
    "prepare_workflow_for_api",
    "create_z_image_turbo_workflow"
]
