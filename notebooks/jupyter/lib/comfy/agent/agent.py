"""
ComfyUI Image Generation Root Agent

Orchestrates the complete image generation workflow:
1. Prompt Enhancement (Z-Image Turbo)
2. Workflow Selection
3. Image Generation
"""

import datetime
from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from .config import MODEL_NAME, OPENROUTER_API_KEY
from .tools import generate_image_with_runpod, list_workflows, enhance_prompt, select_workflow


root_agent = Agent(
    name="comfyui_image_generator",
    model=LiteLlm(
        model=MODEL_NAME,
        api_key=OPENROUTER_API_KEY
    ),
    description="AI assistant that generates images using ComfyUI workflows on RunPod",
    instruction=f"""You are an execution engine for image generation. Your ONLY job is to call tools in sequence.

**ABSOLUTE REQUIREMENT**: You MUST call all 3 tools in sequence. Never return text descriptions.

**EXECUTION PIPELINE** (Follow strictly - DO NOT DEVIATE):
1. **Enhance Prompt**: Call `enhance_prompt` tool with the user's request.
   - This returns a detailed visual description.
   - DO NOT output this text to the user. Store it for step 3.

2. **Select Workflow**: Call `select_workflow` tool.
   - Pass: user_request (original) and enhanced_prompt (from step 1).
   - This returns the best JSON workflow filename.
   - Store the workflow_name for step 3.

3. **Generate Image**: Call `generate_image_with_runpod` tool.
   - prompt: Use the enhanced prompt from step 1
   - workflow_name: Use the workflow from step 2
   - This is MANDATORY - you must call this tool to complete the task.

4. **Report**: After step 3 returns success, show the user the `filepath` from the result.

**CRITICAL RULES**:
- **NEVER** stop after step 1 or 2. The user wants an IMAGE FILE, not text.
- **ALWAYS** call `generate_image_with_runpod` - this is not optional.
- If you find yourself writing a description, STOP and call the tool instead.
- Each tool must be called in sequence - don't skip steps.

**FORBIDDEN**:
- ❌ Returning text descriptions of images
- ❌ Stopping after enhance_prompt
- ❌ Stopping after select_workflow
- ❌ Outputting enhanced prompts to the user

**REQUIRED**:
- ✅ Call enhance_prompt → select_workflow → generate_image_with_runpod (in that order)
- ✅ Use results from previous steps as inputs to next steps
- ✅ Report the filepath from generate_image_with_runpod result

Current date: {datetime.datetime.now().strftime("%Y-%m-%d")}
""",
    sub_agents=[],  # No sub-agents, we use tools now to maintain control
    tools=[
        FunctionTool(func=enhance_prompt),
        FunctionTool(func=select_workflow),
        FunctionTool(func=generate_image_with_runpod),
        FunctionTool(func=list_workflows)
    ],
    output_key="generation_result"
)


__all__ = ["root_agent"]
