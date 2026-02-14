#!/usr/bin/env python3
"""
Test script for ADK Comfy notebook functionality
Run this in the Jupyter container to validate the notebook works correctly.
"""

import sys
import os
import asyncio
from pathlib import Path

# Add project root to path
cwd = Path.cwd()
possible_roots = [
    cwd,
    cwd.parent,
    cwd / "workspace",
    Path("/home/jovyan/workspace"),
    Path("/home/jovyan/workspaces"),
    Path("/home/warby/Workspace/jupyter"),
]

project_root = None
for root in possible_roots:
    if root.exists() and (root / "agents").exists():
        project_root = root
        break

if project_root is None:
    current = cwd
    for _ in range(5):
        if (current / "agents").exists():
            project_root = current
            break
        current = current.parent

if project_root is None:
    raise RuntimeError(f"Could not find project root. Current dir: {cwd}")

if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

print(f"Project root: {project_root}")

# Load environment
from dotenv import load_dotenv
env_paths = [
    project_root / ".env",
    Path.home() / "workspace" / ".env",
    Path("/home/jovyan/workspace/.env"),
    Path("/home/jovyan/workspaces/.env"),
]

for env_path in env_paths:
    if env_path.exists():
        load_dotenv(env_path, override=True)
        print(f"Loaded environment from: {env_path}")
        break

# Silence LiteLLM
import litellm
litellm.set_verbose = False
import logging
logging.getLogger("LiteLLM").setLevel(logging.WARNING)

# Import agent
from agents.comfy import root_agent
print(f"\nAgent imported: {root_agent.name}")
print(f"  Sub-agents: {len(root_agent.sub_agents)}")
print(f"  Tools: {len(root_agent.tools)}")

# Test the generate_image function from the notebook
import re
from IPython.display import display, Image
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types


def display_generated_image(filepath: str):
    """Display a generated image."""
    try:
        path = Path(filepath)
        if path.exists():
            print(f"\n✅ Image generated successfully!")
            print(f"📁 Filepath: {filepath}")
            print(f"   Size: {path.stat().st_size} bytes")
            return True
        else:
            print(f"⚠️  Warning: Image file not found: {filepath}")
            return False
    except Exception as e:
        print(f"⚠️  Warning: Failed to display image: {e}")
        return False


async def generate_image(prompt: str, show_intermediate: bool = True):
    """Generate an image using the ComfyUI agent."""
    session_service = InMemorySessionService()
    await session_service.create_session(
        user_id="test_user",
        session_id="test_session",
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
    
    print(f"\n{'='*60}")
    print(f"User Request: {prompt}")
    print(f"{'='*60}\n")
    
    final_response = None
    generated_filepath = None
    event_count = 0
    
    try:
        async for event in runner.run_async(
            user_id="test_user",
            session_id="test_session",
            new_message=content
        ):
            event_count += 1
            
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'function_response') and part.function_response:
                            function_response = part.function_response
                            function_name = getattr(function_response, 'name', 'unknown')
                            response_data = getattr(function_response, 'response', None)
                            
                            if show_intermediate:
                                print(f"[Event {event_count}] Tool result: {function_name}")
                            
                            if function_name == "generate_image_with_runpod" and response_data:
                                if isinstance(response_data, dict):
                                    status = response_data.get('status')
                                    if status == 'success':
                                        filepath = response_data.get('filepath')
                                        if filepath:
                                            generated_filepath = filepath
                                            print(f"  ✅ Image generated: {filepath}")
                                    else:
                                        error_msg = response_data.get('message', 'Unknown error')
                                        print(f"  ❌ Image generation failed: {error_msg}")
                        
                        if hasattr(part, 'text') and part.text:
                            if show_intermediate:
                                text_preview = part.text[:150] + "..." if len(part.text) > 150 else part.text
                                print(f"[Event {event_count}] Text: {text_preview}")
            
            if event.is_final_response():
                if hasattr(event, 'content') and event.content:
                    if hasattr(event.content, 'parts') and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'text') and part.text:
                                final_response = part.text
                                break
                
                if final_response:
                    print(f"\n{'='*60}")
                    print("Agent Final Response:")
                    print(f"{'='*60}")
                    print(final_response)
                    print(f"{'='*60}\n")
                break
        
        # Check if image was generated
        if generated_filepath:
            success = display_generated_image(generated_filepath)
            return {
                'success': success,
                'response': final_response,
                'filepath': generated_filepath
            }
        else:
            print("⚠️  Warning: No image filepath found in tool results")
            return {
                'success': False,
                'response': final_response,
                'filepath': None
            }
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'error': str(e)
        }


async def main():
    """Main test function."""
    print("="*60)
    print("Testing ADK Comfy Image Generation")
    print("="*60)
    
    result = await generate_image(
        "A cyberpunk gopher astronaut floating in space, digital art",
        show_intermediate=True
    )
    
    print("\n" + "="*60)
    print("Test Results:")
    print("="*60)
    print(f"Success: {result.get('success', False)}")
    if result.get('filepath'):
        print(f"Filepath: {result['filepath']}")
    if result.get('error'):
        print(f"Error: {result['error']}")
    
    return result.get('success', False)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

