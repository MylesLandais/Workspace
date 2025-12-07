# ComfyUI Image Generation Agent

A production-ready Google ADK agent for generating images using RunPod ComfyUI workflows with Z-Image Turbo prompt enhancement.

## Architecture

```
agents/comfy/
├── __init__.py              # Package exports
├── agent.py                 # Root agent orchestration
├── config.py                # Environment and model configuration
├── prompts.py               # Z-Image Turbo PE template
├── tools.py                 # Image generation tools
├── workflows/               # Workflow loader utilities
│   └── __init__.py
└── sub_agents/              # Specialized sub-agents
    ├── __init__.py
    ├── prompt_enhancer.py   # ZIT prompt enhancement
    └── workflow_selector.py # Workflow selection
```

## Features

### ✨ Key Capabilities

- **Z-Image Turbo Prompt Enhancement**: Automatically optimizes prompts using official ZIT methodology (outputs Chinese for Qwen 3.4B CLIP)
- **Workflow Management**: Loads and manages ComfyUI workflow templates from `Datasets/Comfy_Workflow/`
- **Token Efficiency**: Returns only metadata (no base64 image data) to avoid context overflow
- **Clean Logging**: LiteLLM debug output suppressed by default
- **Modular Architecture**: Follows Google ADK best practices with sub-agents

### 🔄 Workflow

```
User Request
    ↓
[Root Agent]
    ↓
[Prompt Enhancer Sub-Agent]
    - Input: English user prompt
    - Output: Enhanced Chinese prompt (ZIT-optimized)
    ↓
[Workflow Selector Sub-Agent]
    - Input: User request + enhanced prompt
    - Output: Selected workflow + node overrides
    ↓
[Image Generator Tool]
    - Loads workflow template
    - Applies prompt + parameters
    - Submits to RunPod
    - Polls for completion
    - Saves image locally
    ↓
[Root Agent Response]
    - Filepath, seed, dimensions
    - Generation details
```

## Quick Start

### Installation

Ensure you have the required packages:

```bash
pip install python-dotenv litellm google-adk
```

### Configuration

Create a `.env` file in your workspace root:

```env
OPENROUTER_API_KEY=sk-or-v1-...
RUNPOD_API_KEY=rpa_...
RUNPOD_ENDPOINT_ID=a48mrbdsbzg35n
```

### Usage

#### In a Notebook

```python
import sys
from pathlib import Path

# Add agents to path
sys.path.insert(0, str(Path.cwd().parent))

# Import agent
from agents.comfy import root_agent

# Use with ADK Runner
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def generate():
    session_service = InMemorySessionService()
    await session_service.create_session(
        user_id="user1",
        session_id="session1",
        app_name="comfyui"
    )
    
    runner = Runner(
        agent=root_agent,
        app_name="comfyui",
        session_service=session_service
    )
    
    content = types.Content(
        role="user",
        parts=[types.Part(text="Generate a cyberpunk cityscape at sunset")]
    )
    
    async for event in runner.run_async(
        user_id="user1",
        session_id="session1",
        new_message=content
    ):
        if event.is_final_response():
            print(event.content.parts[0].text)
            break

await generate()
```

#### Direct Tool Usage

```python
from agents.comfy.tools import generate_image_with_runpod

result = generate_image_with_runpod(
    prompt="一个赛博朋克风格的城市景观，在日落时分",  # Chinese prompt
    workflow_name="Basic Z-image turbo -Icekiub.json",
    width=1280,
    height=1440,
    seed=12345
)

if result["status"] == "success":
    print(f"Image saved: {result['filepath']}")
    print(f"Seed: {result['seed']}")
```

## Available Workflows

| Workflow | Description | Use Case |
|----------|-------------|----------|
| `Basic Z-image turbo -Icekiub.json` | Standard bf16 workflow | High-quality general scenes |
| `kombitz_z_image_turbo_gguf.json` | GGUF quantized variant | Faster generation, lower memory |
| `Z_Image_Turbo (GGUF).json` | Alternative GGUF workflow | Speed-optimized |
| `1GIRL (STAND-ALONE) V3.json` | Character-focused workflow | Portrait/character generation |
| `1GIRL (+SAMSUNG by Danrisi) V3.json` | Samsung style variant | Specific style preset |

Workflows are stored in `Datasets/Comfy_Workflow/` and loaded automatically.

## Configuration

### Model Settings

Default model: `openrouter/google/gemini-2.5-flash`

To change, edit `agents/comfy/config.py`:

```python
MODEL_NAME = "openrouter/anthropic/claude-3.5-sonnet"
```

### Output Directory

Images are saved to `outputs/` by default. To change:

```python
OUTPUT_DIR = Path("my_images")
```

## Troubleshooting

### Token Overflow Error

**Fixed!** The tool now returns only metadata (filepath, seed) instead of base64 image data.

### LiteLLM Debug Noise

**Fixed!** Debug logging is suppressed in the notebook setup cell:

```python
import litellm
litellm.set_verbose = False
logging.getLogger("LiteLLM").setLevel(logging.WARNING)
```

### Workflow Not Found

Check available workflows:

```python
from agents.comfy.workflows import list_available_workflows
print(list_available_workflows())
```

### Prompt Not Enhanced

The prompt enhancer outputs Chinese by default (optimized for Qwen 3.4B CLIP). This is expected behavior for Z-Image Turbo workflows.

## Development

### Adding New Workflows

1. Export your ComfyUI workflow as JSON (API format)
2. Save to `Datasets/Comfy_Workflow/`
3. The agent will automatically detect it

### Customizing Prompt Enhancement

Edit `agents/comfy/prompts.py` to modify the `ZIT_PROMPT_TEMPLATE`.

### Adding New Sub-Agents

Follow the pattern in `agents/comfy/sub_agents/`:

```python
from google.adk.agents import LlmAgent
from ..config import MODEL_NAME, OPENROUTER_API_KEY

my_agent = LlmAgent(
    name="my_agent",
    model=LiteLlm(model=MODEL_NAME, api_key=OPENROUTER_API_KEY),
    instruction="...",
    tools=[...]
)
```

## Credits

- **Z-Image Turbo**: [Tongyi-MAI/Z-Image-Turbo](https://huggingface.co/spaces/Tongyi-MAI/Z-Image-Turbo)
- **Google ADK**: [google/adk-docs](https://google.github.io/adk-docs/)
- **RunPod**: [runpod.io](https://runpod.io)

## License

Follows the same license as the parent project.

