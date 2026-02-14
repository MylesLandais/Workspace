"""
Configuration for ComfyUI Image Generation Agent
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# Suppress litellm verbose output globally
logging.getLogger("LiteLLM").setLevel(logging.ERROR)

# Suppress litellm provider list messages via environment variable
os.environ.setdefault("LITELLM_LOG", "ERROR")

# Load environment variables from .env file
# Try project root first, then default locations
project_root = Path(__file__).parent.parent.parent
env_paths = [
    project_root / ".env",  # Project root .env
    Path.home() / "workspace" / ".env",  # Docker container default
    Path("/home/jovyan/workspace/.env"),  # Absolute Docker path
]

# Try to load from one of the possible locations
for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=False)  # Don't override if already set
        break
else:
    # Fallback to default behavior (current directory)
    load_dotenv()

# Model Configuration
MODEL_NAME = "openrouter/google/gemini-2.5-flash"

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY")
RUNPOD_ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "a48mrbdsbzg35n")

# Workflow Configuration
WORKFLOW_DIR = Path(__file__).parent.parent.parent / "Datasets" / "Comfy_Workflow"

# Output Configuration
# Use project root so outputs are accessible from host system (workspace mount)
OUTPUT_DIR = project_root / "outputs"
OUTPUT_DIR.mkdir(exist_ok=True)

# Validation
if not RUNPOD_API_KEY:
    raise ValueError("RUNPOD_API_KEY environment variable is required")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable is required")

