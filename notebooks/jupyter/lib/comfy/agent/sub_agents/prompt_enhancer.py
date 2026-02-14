"""
Prompt Enhancement Sub-Agent

Uses Z-Image Turbo prompt engineering methodology to enhance
user prompts for optimal image generation with Qwen 3.4B CLIP model.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from ..config import MODEL_NAME, OPENROUTER_API_KEY
from ..prompts import ZIT_PROMPT_TEMPLATE


prompt_enhancer_agent = LlmAgent(
    name="zit_prompt_enhancer",
    model=LiteLlm(
        model=MODEL_NAME,
        api_key=OPENROUTER_API_KEY
    ),
    description="Enhances image prompts using Z-Image Turbo methodology",
    instruction=ZIT_PROMPT_TEMPLATE,
    tools=[],  # No tools needed - pure LLM reasoning
    output_key="enhanced_prompt"
)


__all__ = ["prompt_enhancer_agent"]

