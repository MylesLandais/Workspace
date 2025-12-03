from google.adk.agents import Agent
from google.genai.types import (
    GenerateContentConfig,
    HarmBlockThreshold,
    HarmCategory,
    SafetySetting,
)

from .prompts import AGENT_INSTRUCTION

genai_config = GenerateContentConfig(
    temperature=0.5
)

root_agent = Agent(
   name="example_agent",
   model="gemini-live-2.5-flash-preview-native-audio",
   description="A helpful AI assistant.",
   instruction=AGENT_INSTRUCTION
)