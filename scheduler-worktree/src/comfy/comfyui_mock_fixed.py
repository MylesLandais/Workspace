#!/usr/bin/env python3
import json
import os
import secrets
import time
from copy import deepcopy
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont
from IPython.display import display, HTML
import ipywidgets as widgets
from IPython.display import clear_output

# --- Configuration ---
WORKFLOW_PATH = os.getenv("WORKFLOW_PATH", "sdxl_simple_example.json")

# --- Enhanced Mock Implementations ---
def load_unet(unet_name, **kwargs):
    print(f"  - Loading UNET model: {unet_name}")
    return f"unet_model({unet_name})"

def load_quad_clip(clip_name1, **kwargs):
    print(f"  - Loading Quad CLIP models starting with: {clip_name1}")
    return "quad_clip_model"

def load_vae(vae_name, **kwargs):
    print(f"  - Loading VAE: {vae_name}")
    return f"vae_model({vae_name})"

def checkpoint_loader_simple(ckpt_name, **kwargs):
    print(f"  - Loading checkpoint: {ckpt_name}")
    return (f"model({ckpt_name})", f"clip({ckpt_name})", f"vae({ckpt_name})")

def model_sampling_sd3(model, shift, **kwargs):
    print(f"  - Applying ModelSamplingSD3 with shift: {shift} to {model}")
    return f"sampled_model_from({model})"

def empty_latent_image(width, height, batch_size=1, **kwargs):
    print(f"  - Creating placeholder image of size: {width}x{height}")
    # Create a more sophisticated base image
    img = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(img)
    
    # Create gradient background
    for i in range(height):
        color_val = int(255 * (1 - i / height * 0.3))
        blue_val = min(255, int(200 + i / height * 55))
        draw.line([(0, i), (width, i)], fill=(color_val, color_val + 20, blue_val))
    
    # Add grid pattern
    grid_size = 50
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill=(240, 240, 250), width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill=(240, 240, 250), width=1)
    
    return img

def clip_text_encode(text, clip, **kwargs):
    print(f"  - Encoding text: '{text[:50]}{'...' if len(text) > 50 else ''}' using {clip}")
    return f"encoded_text('{text[:20]}...')"

def ksampler(model, positive, negative, latent_image, seed=None, steps=20, cfg=7.0, 
            sampler_name="euler", scheduler="normal", denoise=1.0, noise_seed=None,
            start_at_step=0, end_at_step=10000, add_noise="enable", 
            return_with_leftover_noise="disable", **kwargs):
    
    # Use noise_seed if provided, otherwise use seed
    actual_seed = noise_seed if noise_seed is not None else seed
    
    print(f"  - KSampler: seed={actual_seed}, steps={steps}, cfg={cfg}")
    print(f"    sampler={sampler_name}, scheduler={scheduler}")
    print(f"    step range: {start_at_step}-{end_at_step}, denoise={denoise}")
    
    img = latent_image.copy()
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Simulate different sampling effects based on parameters
    if sampler_name == "dpmpp_2m":
        color = (255, 150, 50)  # Orange
    elif sampler_name == "euler":
        color = (50, 255, 150)  # Green
    else:
        color = (150, 50, 255)  # Purple
    
    # Add sampling visualization
    draw.rectangle([10, 10, img.width-10, 80], fill=(0, 0, 0, 128))
    draw.text((20, 20), f"KSampler: {sampler_name}", fill=color, font=font)
    draw.text((20, 35), f"Seed: {actual_seed}, Steps: {steps}", fill=(255, 255, 255), font=font)
    draw.text((20, 50), f"CFG: {cfg}, Schedule: {scheduler}", fill=(200, 200, 200), font=font)
    
    return img

def vae_decode(samples, vae, **kwargs):
    print(f"  - VAE Decode using: {vae}")
    img = samples.copy()
    draw = ImageDraw.Draw(img)
    
    try:
        font = ImageFont.truetype("arial.ttf", 14)
    except:
        font = ImageFont.load_default()
    
    # Add final processing indicator
    draw.rectangle([10, img.height-60, img.width-10, img.height-10], fill=(0, 50, 0, 128))
    draw.text((20, img.height-50), f"VAE Decoded: {vae}", fill=(100, 255, 100), font=font)
    draw.text((20, img.height-35), "Image Generation Complete", fill=(255, 255, 255), font=font)
    
    return img

def save_image(images, filename_prefix="ComfyUI", **kwargs):
    print(f"  - Saving/displaying image with prefix: {filename_prefix}")
    
    if images is None:
        print("Warning: No image to display")
        return "No image to display"
    
    try:
        display(images)
        timestamp = int(time.time())
        output_filename = f"{filename_prefix}_{timestamp}.png"
        images.save(output_filename)
        print(f"  - Image saved as: {output_filename}")
        return f"Image displayed and saved as {output_filename}"
    except Exception as e:
        print(f"Error displaying/saving image: {e}")
        return f"Error: {e}"

# --- Node Mapping ---
NODE_CLASS_MAPPING = {
    "UNETLoader": load_unet,
    "QuadrupleCLIPLoader": load_quad_clip,
    "VAELoader": load_vae,
    "CheckpointLoaderSimple": checkpoint_loader_simple,
    "ModelSamplingSD3": model_sampling_sd3,
    "EmptySD3LatentImage": empty_latent_image,
    "EmptyLatentImage": empty_latent_image,
    "CLIPTextEncode": clip_text_encode,
    "KSampler": ksampler,
    "VAEDecode": vae_decode,
    "SaveImage": save_image
}

# --- Workflow Execution Engine ---
def execute_node(node_id, workflow, executed_nodes):
    if node_id in executed_nodes:
        return executed_nodes[node_id]

    if node_id not in workflow:
        raise ValueError(f"Node {node_id} not found in workflow")

    node_info = workflow[node_id]
    print(f"Executing Node {node_id} ({node_info['class_type']})...")

    inputs = node_info.get("inputs", {})
    resolved_inputs = {}

    for key, value in inputs.items():
        if isinstance(value, list) and len(value) == 2 and str(value[0]) in workflow:
            input_node_id = str(value[0])
            output_index = value[1]
            node_result = execute_node(input_node_id, workflow, executed_nodes)
            
            if isinstance(node_result, tuple) and output_index < len(node_result):
                resolved_inputs[key] = node_result[output_index]
            else:
                resolved_inputs[key] = node_result
        else:
            resolved_inputs[key] = value
    
    class_type = node_info["class_type"]
    if class_type in NODE_CLASS_MAPPING:
        function_to_call = NODE_CLASS_MAPPING[class_type]
        result = function_to_call(**resolved_inputs)
        executed_nodes[node_id] = result
        print(f"Finished Node {node_id}.\n")
        return result
    else:
        raise ValueError(f"No implementation found for class_type: {class_type}")

# --- Advanced Workflow Manipulation (from friend's code) ---
def set_text(wf: Dict[str, Any], node_id: str, text: str):
    """Set text input for a node"""
    wf.setdefault(node_id, {}).setdefault("inputs", {})
    wf[node_id]["inputs"]["text"] = text

def maybe_set(wf: Dict[str, Any], node_id: str, key: str, val: Any):
    """Set a parameter only if value is not None"""
    if val is None:
        return
    wf.setdefault(node_id, {}).setdefault("inputs", {})
    wf[node_id]["inputs"][key] = val

def inject_prompts_and_tuning(
    workflow: Dict[str, Any],
    prompt: str,
    negative: Optional[str] = None,
    cfg: Optional[float] = None,
    steps: Optional[int] = None,
    sampler_name: Optional[str] = None,
    scheduler: Optional[str] = None,
    seed: Optional[int] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    randomize_seed: bool = False,
) -> Dict[str, Any]:
    """Enhanced workflow injection with comprehensive parameter control"""
    
    wf = deepcopy(workflow)
    
    # Handle seed logic (priority: randomize > user seed > keep original)
    seed_to_apply = None
    if randomize_seed:
        seed_to_apply = secrets.randbits(32)
        print(f"Generated random seed: {seed_to_apply}")
    elif isinstance(seed, (int, float)) and seed >= 0:
        seed_to_apply = int(seed)
    
    # Find and update text encoding nodes (common patterns)
    text_nodes = []
    sampler_nodes = []
    latent_nodes = []
    
    for node_id, node_info in wf.items():
        class_type = node_info.get("class_type", "")
        if class_type == "CLIPTextEncode":
            text_nodes.append(node_id)
        elif class_type == "KSampler":
            sampler_nodes.append(node_id)
        elif class_type in ["EmptyLatentImage", "EmptySD3LatentImage"]:
            latent_nodes.append(node_id)
    
    # Update text prompts (positive and negative)
    positive_nodes = []
    negative_nodes = []
    
    for node_id in text_nodes:
        current_text = wf[node_id]["inputs"].get("text", "").lower()
        # Heuristic: negative prompts often contain words like "bad", "blurry", etc.
        if any(word in current_text for word in ["bad", "blurry", "deformed", "worst", "low"]):
            negative_nodes.append(node_id)
        else:
            positive_nodes.append(node_id)
    
    # Set prompts
    for node_id in positive_nodes:
        set_text(wf, node_id, prompt)
        print(f"Set positive prompt in node {node_id}")
    
    if negative:
        for node_id in negative_nodes:
            set_text(wf, node_id, negative)
            print(f"Set negative prompt in node {node_id}")
    
    # Update sampler parameters
    for node_id in sampler_nodes:
        maybe_set(wf, node_id, "cfg", cfg)
        maybe_set(wf, node_id, "steps", steps)
        maybe_set(wf, node_id, "sampler_name", sampler_name)
        maybe_set(wf, node_id, "scheduler", scheduler)
        
        if seed_to_apply is not None:
            # Try both common seed parameter names
            maybe_set(wf, node_id, "seed", seed_to_apply)
            maybe_set(wf, node_id, "noise_seed", seed_to_apply)
    
    # Update image dimensions
    for node_id in latent_nodes:
        maybe_set(wf, node_id, "width", width)
        maybe_set(wf, node_id, "height", height)
    
    return wf

def execute_enhanced_workflow(
    workflow: Dict[str, Any],
    prompt: str,
    negative: str = "",
    cfg: float = 7.0,
    steps: int = 20,
    sampler_name: str = "euler",
    scheduler: str = "normal",
    seed: Optional[int] = None,
    width: int = 512,
    height: int = 512,
    randomize_seed: bool = False,
    final_node_id: str = "9"
):
    """Execute workflow with enhanced parameter control"""
    
    print("=== Enhanced ComfyUI Mock Execution ===")
    print(f"Prompt: {prompt}")
    print(f"Negative: {negative}")
    print(f"Parameters: cfg={cfg}, steps={steps}, sampler={sampler_name}")
    print(f"Size: {width}x{height}")
    print("=" * 40)
    
    # Inject parameters into workflow
    enhanced_wf = inject_prompts_and_tuning(
        workflow, prompt, negative, cfg, steps, sampler_name, 
        scheduler, seed, width, height, randomize_seed
    )
    
    # Execute workflow
    execution_cache = {}
    print("\n--- Starting Enhanced Workflow Execution ---")
    try:
        final_result = execute_node(final_node_id, enhanced_wf, execution_cache)
        print("--- Workflow Execution Complete ---")
        return final_result
    except Exception as e:
        print(f"--- Execution Failed: {e} ---")
        return None

# --- Interactive Jupyter Interface ---
class ComfyUIController:
    def __init__(self, workflow_path=None):
        self.workflow_path = workflow_path or WORKFLOW_PATH
        self.base_workflow = self.load_workflow()
        self.create_interface()
    
    def load_workflow(self):
        """Load workflow with fallback options"""
        if os.path.exists(self.workflow_path):
            try:
                with open(self.workflow_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading {self.workflow_path}: {e}")
        
        # Fallback to sample SDXL workflow
        return self.create_sample_sdxl_workflow()
    
    def create_sample_sdxl_workflow(self):
        """Create a sample SDXL-style workflow"""
        return {
            "3": {
                "class_type": "KSampler",
                "inputs": {
                    "cfg": 8,
                    "denoise": 1,
                    "latent_image": ["5", 0],
                    "model": ["4", 0],
                    "negative": ["7", 0],
                    "positive": ["6", 0],
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "seed": 123456,
                    "steps": 20
                }
            },
            "4": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {"ckpt_name": "sdxl_base_1.0.safetensors"}
            },
            "5": {
                "class_type": "EmptyLatentImage",
                "inputs": {"batch_size": 1, "height": 1024, "width": 1024}
            },
            "6": {
                "class_type": "CLIPTextEncode",
                "inputs": {"clip": ["4", 1], "text": "masterpiece, best quality"}
            },
            "7": {
                "class_type": "CLIPTextEncode",
                "inputs": {"clip": ["4", 1], "text": "bad hands, blurry"}
            },
            "8": {
                "class_type": "VAEDecode",
                "inputs": {"samples": ["3", 0], "vae": ["4", 2]}
            },
            "9": {
                "class_type": "SaveImage",
                "inputs": {"filename_prefix": "SDXL", "images": ["8", 0]}
            }
        }
    
    def create_interface(self):
        """Create interactive Jupyter widgets"""
        style = {'description_width': '120px'}
        layout = widgets.Layout(width='500px')
        
        self.prompt_widget = widgets.Textarea(
            value="masterpiece, best quality, beautiful landscape, detailed",
            description='Prompt:',
            style=style,
            layout=widgets.Layout(width='600px', height='80px')
        )
        
        self.negative_widget = widgets.Textarea(
            value="bad hands, blurry, deformed, worst quality",
            description='Negative:',
            style=style,
            layout=widgets.Layout(width='600px', height='60px')
        )
        
        self.cfg_widget = widgets.FloatSlider(
            value=7.0, min=1.0, max=20.0, step=0.5,
            description='CFG Scale:', style=style, layout=layout
        )
        
        self.steps_widget = widgets.IntSlider(
            value=20, min=1, max=100, step=1,
            description='Steps:', style=style, layout=layout
        )
        
        self.sampler_widget = widgets.Dropdown(
            options=['euler', 'euler_a', 'dpmpp_2m', 'dpmpp_2m_sde', 'ddim'],
            value='euler', description='Sampler:', style=style, layout=layout
        )
        
        self.scheduler_widget = widgets.Dropdown(
            options=['normal', 'karras', 'exponential', 'sgm_uniform'],
            value='normal', description='Scheduler:', style=style, layout=layout
        )
        
        self.seed_widget = widgets.IntText(
            value=42, description='Seed:', style=style, layout=layout
        )
        
        self.randomize_seed_widget = widgets.Checkbox(
            value=False, description='Randomize Seed', style=style
        )
        
        self.width_widget = widgets.Dropdown(
            options=[512, 768, 1024, 1280], value=1024,
            description='Width:', style=style, layout=layout
        )
        
        self.height_widget = widgets.Dropdown(
            options=[512, 768, 1024, 1280], value=1024,
            description='Height:', style=style, layout=layout
        )
        
        self.generate_button = widgets.Button(
            description='🎨 Generate Image',
            button_style='primary',
            layout=widgets.Layout(width='200px', height='40px')
        )
        
        self.output = widgets.Output()
        
        # Button click handler
        self.generate_button.on_click(self.on_generate_click)
        
        # Display interface
        display(HTML("<h2>🎨 Enhanced ComfyUI Mock Generator</h2>"))
        display(widgets.VBox([
            self.prompt_widget,
            self.negative_widget,
            widgets.HBox([self.cfg_widget, self.steps_widget]),
            widgets.HBox([self.sampler_widget, self.scheduler_widget]),
            widgets.HBox([self.seed_widget, self.randomize_seed_widget]),
            widgets.HBox([self.width_widget, self.height_widget]),
            self.generate_button,
            self.output
        ]))
    
    def on_generate_click(self, button):
        """Handle generate button click"""
        with self.output:
            clear_output(wait=True)
            
            # Get parameters from widgets
            params = {
                'prompt': self.prompt_widget.value,
                'negative': self.negative_widget.value,
                'cfg': self.cfg_widget.value,
                'steps': self.steps_widget.value,
                'sampler_name': self.sampler_widget.value,
                'scheduler': self.scheduler_widget.value,
                'seed': self.seed_widget.value if not self.randomize_seed_widget.value else None,
                'width': self.width_widget.value,
                'height': self.height_widget.value,
                'randomize_seed': self.randomize_seed_widget.value
            }
            
            # Execute workflow
            result = execute_enhanced_workflow(
                self.base_workflow, **params
            )
            
            if result:
                print(f"\n✅ Generation completed successfully!")
            else:
                print(f"\n❌ Generation failed!")

# --- Main Functions ---
def create_sample_workflows():
    """Create sample workflows for testing"""
    
    # Basic SDXL workflow
    sdxl_workflow = {
        "3": {"class_type": "KSampler", "inputs": {"cfg": 8, "denoise": 1, "latent_image": ["5", 0], "model": ["4", 0], "negative": ["7", 0], "positive": ["6", 0], "sampler_name": "euler", "scheduler": "normal", "seed": 123456, "steps": 20}},
        "4": {"class_type": "CheckpointLoaderSimple", "inputs": {"ckpt_name": "sdxl_base_1.0.safetensors"}},
        "5": {"class_type": "EmptyLatentImage", "inputs": {"batch_size": 1, "height": 1024, "width": 1024}},
        "6": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": "masterpiece, best quality"}},
        "7": {"class_type": "CLIPTextEncode", "inputs": {"clip": ["4", 1], "text": "bad hands, blurry"}},
        "8": {"class_type": "VAEDecode", "inputs": {"samples": ["3", 0], "vae": ["4", 2]}},
        "9": {"class_type": "SaveImage", "inputs": {"filename_prefix": "SDXL", "images": ["8", 0]}}
    }
    
    with open("sdxl_simple_example.json", "w") as f:
        json.dump(sdxl_workflow, f, indent=2)
    
    print("Created sample workflow: sdxl_simple_example.json")

def launch_interactive_controller():
    """Launch the interactive Jupyter controller"""
    return ComfyUIController()

# --- Usage Examples ---
if __name__ == "__main__":
    # Create sample workflows if they don't exist
    if not os.path.exists("sdxl_simple_example.json"):
        create_sample_workflows()
    
    print("Enhanced ComfyUI Mock with Jupyter Integration")
    print("=" * 50)
    print("Usage:")
    print("1. controller = launch_interactive_controller()  # Interactive widget interface")
    print("2. Or use execute_enhanced_workflow() directly for programmatic control")
    print("3. Sample workflows created if not found")
    print("\nNote: Install ipywidgets if not available: pip install ipywidgets")