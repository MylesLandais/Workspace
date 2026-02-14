"""
Workflow Selector Sub-Agent

Analyzes user requests and selects the appropriate ComfyUI workflow template.
"""

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools import FunctionTool

from ..config import MODEL_NAME, OPENROUTER_API_KEY
from ..prompts import WORKFLOW_SELECTOR_INSTRUCTION
from ..tools import list_workflows


workflow_selector_agent = LlmAgent(
    name="workflow_selector",
    model=LiteLlm(
        model=MODEL_NAME,
        api_key=OPENROUTER_API_KEY
    ),
    description="Selects appropriate ComfyUI workflow based on user requirements",
    instruction=WORKFLOW_SELECTOR_INSTRUCTION,
    tools=[
        FunctionTool(func=list_workflows)
    ],
    output_key="workflow_config"
)


__all__ = ["workflow_selector_agent"]

