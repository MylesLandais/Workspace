
import sys
import os
import logging
from pathlib import Path
import asyncio

# Setup paths similar to the notebook
cwd = Path.cwd()
project_root = cwd.parent
sys.path.insert(0, str(project_root))

from dotenv import load_dotenv
load_dotenv(project_root / ".env")

# Enable LiteLLM debug
import litellm
litellm.set_verbose = True
logging.getLogger("LiteLLM").setLevel(logging.DEBUG)
logging.basicConfig(level=logging.DEBUG)

from agents.comfy import root_agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

async def run_test():
    print("Agent imported successfully")
    
    prompt = "A cyberpunk gopher astronaut floating in space, digital art"
    
    session_service = InMemorySessionService()
    await session_service.create_session(
        user_id="demo_user",
        session_id="demo_session",
        app_name="comfyui_gen"
    )
    
    runner = Runner(
        agent=root_agent,
        app_name="comfyui_gen",
        session_service=session_service
    )
    
    content = types.Content(
        role="user",
        parts=[types.Part(text=prompt)]
    )
    
    print(f"Running agent with prompt: {prompt}")
    
    async for event in runner.run_async(
        user_id="demo_user",
        session_id="demo_session",
        new_message=content
    ):
        if hasattr(event, 'content') and event.content:
             print(f"Event content: {event.content}")

if __name__ == "__main__":
    asyncio.run(run_test())

