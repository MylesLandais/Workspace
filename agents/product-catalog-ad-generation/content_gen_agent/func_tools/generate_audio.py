# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Generates background audio and voiceovers using Google Cloud services."""

import asyncio
import base64
import logging
import os
import re
import time
from typing import Any, Dict, List, Optional

import aiohttp
import google.auth
import google.auth.transport.requests
from google.adk.tools import ToolContext
from google.cloud import texttospeech
from google.genai import types

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

MAX_RETRIES = 3
STATIC_AUDIO_FALLBACK = "static/audio/audio_track_1.mp3"
TTS_MODEL_NAME = "gemini-2.5-flash-preview-tts"
TTS_VOICE_NAME = "Schedar"
LYRIA_MODEL_NAME = "lyria-002"


async def _send_google_api_request(
    api_endpoint: str, data: Optional[Dict[str, Any]] = None
) -> Optional[Dict[str, Any]]:
    """Sends an authenticated HTTP request to a Google API endpoint.

    Args:
        api_endpoint (str): The URL of the Google API endpoint.
        data (Optional[Dict[str, Any]]): A dictionary of data to send in the request body.
          Defaults to None.

    Returns:
        The JSON response from the API, or None on failure.
    """
    try:
        creds, _ = google.auth.default()
        auth_req = google.auth.transport.requests.Request()
        creds.refresh(auth_req)
        access_token = creds.token

        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

        async with aiohttp.ClientSession() as session:
            for attempt in range(MAX_RETRIES):
                try:
                    async with session.post(
                        api_endpoint, headers=headers, json=data
                    ) as response:
                        response.raise_for_status()
                        return await response.json()
                except aiohttp.ClientResponseError as e:
                    if e.status == 400 and attempt < MAX_RETRIES - 1:
                        await asyncio.sleep(1)
                    else:
                        raise e
    except Exception as e:
        logging.error(
            f"Request to {api_endpoint} failed: {e}", exc_info=True
        )
    return None


async def generate_audio(
    audio_query: str, tool_context: ToolContext
) -> Optional[Dict[str, str]]:
    """Generates an audio clip using the Lyria model.

    Args:
        audio_query (str): The prompt describing the desired audio content.
        tool_context (ToolContext): The context for artifact management.

    Returns:
        A dictionary with the generated audio artifact name, or a fallback.
    """
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        logging.error("GOOGLE_CLOUD_PROJECT environment variable not set.")
        return {"name": STATIC_AUDIO_FALLBACK}

    endpoint = (
        f"https://us-central1-aiplatform.googleapis.com/v1/projects/{project_id}"
        f"/locations/us-central1/publishers/google/models/{LYRIA_MODEL_NAME}:predict"
    )
    payload = {"instances": [{"prompt": audio_query}], "parameters": {}}

    try:
        response = await _send_google_api_request(endpoint, payload)
        if not response or "predictions" not in response:
            raise ValueError("Invalid response from Lyria model.")

        prediction = response["predictions"][0]
        bytes_b64 = prediction.get("bytesBase64Encoded")
        if not bytes_b64:
            raise ValueError("No audio data in prediction.")

        audio_data = base64.b64decode(bytes_b64)
        filename = f"audio_{int(time.time())}.wav"
        await tool_context.save_artifact(
            filename,
            types.Part.from_bytes(data=audio_data, mime_type="audio/wav"),
        )
        return {"name": filename}
    except Exception as e:
        logging.error(f"Error generating audio: {e}", exc_info=True)
        logging.warning(f"Falling back to static audio: {STATIC_AUDIO_FALLBACK}")
        return {"name": STATIC_AUDIO_FALLBACK}


async def _generate_voiceover_content(
    prompt: str, text: str, model_name: str, voice_name: str
) -> Optional[bytes]:
    """Synthesizes speech using Gemini-TTS.

    Args:
        prompt (str): Styling instructions for the voice.
        text (str): The text to be spoken.
        model_name (str): The Gemini-TTS model to use.
        voice_name (str): The name of the prebuilt voice.

    Returns:
        The audio content as bytes, or None on failure.
    """
    try:
        client = texttospeech.TextToSpeechAsyncClient()
        synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)
        voice = texttospeech.VoiceSelectionParams(
            language_code="en-US", model_name=model_name, name=voice_name
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3
        )
        response = await client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content
    except Exception as e:
        logging.error(
            f"Failed to generate voiceover content: {e}", exc_info=True
        )
        return None


async def generate_voiceover(
    prompt: str,
    text: str,
    tool_context: ToolContext,
    model_name: str = TTS_MODEL_NAME,
    voice_name: str = TTS_VOICE_NAME,
) -> Optional[Dict[str, str]]:
    """Generates a voiceover and saves it as an artifact.

    Args:
        prompt (str): Styling instructions for the voice.
        text (str): The text to be spoken.
        tool_context (ToolContext): The context for artifact management.
        model_name (str): The Gemini-TTS model to use. Defaults to "gemini-2.5-flash-preview-tts".
        voice_name (str): The name of the prebuilt voice. Defaults to "Schedar".

    Returns:
        A dictionary with the generated voiceover artifact name.
    """
    audio_content = await _generate_voiceover_content(
        prompt, text, model_name, voice_name
    )
    if not audio_content:
        return None

    try:
        filename = f"voiceover_{int(time.time())}.mp3"
        await tool_context.save_artifact(
            filename,
            types.Part.from_bytes(data=audio_content, mime_type="audio/mp3"),
        )
        return {"name": filename}
    except Exception as e:
        logging.error(f"Error saving voiceover artifact: {e}", exc_info=True)
        return None


async def generate_audio_and_voiceover(
    tool_context: ToolContext,
    audio_query: str,
    voiceover_prompt: str,
    voiceover_text: str,
    model_name: str = TTS_MODEL_NAME,
    voice_name: str = TTS_VOICE_NAME,
    generation_mode: str = "both",
) -> Dict[str, Any]:
    """
    Generates a background audio track, a voiceover, or both in a single function call.
    This function can run generation processes concurrently for improved performance when generating both.

    Args:
        audio_query (str): The prompt describing the desired background audio content.
        voiceover_prompt (str): The prompt that sets the context for the voiceover. e.g. You are a professional announcer with a warm, friendly tone.
        tool_context (ToolContext): The context for the tool execution, used for artifact management.
        voiceover_text (str, optional): Explicit text for the voiceover to sell the product. Make it punny and mention the company name. Keep it short and sweet. e.g. FALL into great prices from {company name} - buy from a store near you!
        model_name (str, optional): The Gemini TTS model to use.
                                  Default is "gemini-2.5-flash-preview-tts".
        voice_name (str, optional): The voice name to use. Default is "Kore".
        generation_mode (str, optional): Specifies what to generate. Can be 'audio', 'voiceover', or 'both'.
                                         Defaults to 'both'.

    Returns:
        Optional[dict]: A dictionary containing the names of the generated audio and voiceover artifacts,
                        and a list of any failures, or None if the operation fails completely.
    """
    tasks = []
    if generation_mode in ["audio", "both"]:
        tasks.append(generate_audio(audio_query, tool_context))
    if generation_mode in ["voiceover", "both"]:
        tasks.append(
            generate_voiceover(
                voiceover_prompt,
                voiceover_text,
                tool_context,
                model_name,
                voice_name,
            )
        )

    if not tasks:
        return {"failures": [f"Invalid generation_mode: {generation_mode}"]}

    results = await asyncio.gather(*tasks, return_exceptions=True)
    response: Dict[str, Any] = {"failures": []}
    result_index = 0

    if generation_mode in ["audio", "both"]:
        audio_res = results[result_index]
        if isinstance(audio_res, Exception) or not audio_res:
            response["failures"].append(f"audio: {audio_res or 'Unknown error'}")
            response["audio_name"] = STATIC_AUDIO_FALLBACK
        else:
            response["audio_name"] = audio_res["name"]
        result_index += 1

    if generation_mode in ["voiceover", "both"]:
        vo_res = results[result_index]
        if isinstance(vo_res, Exception) or not vo_res:
            response["failures"].append(f"voiceover: {vo_res or 'Unknown error'}")
        else:
            response["voiceover_name"] = vo_res["name"]

    return response
