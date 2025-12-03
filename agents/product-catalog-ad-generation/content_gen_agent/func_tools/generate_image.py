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
"""Handles the generation of images based on storyline prompts."""

import asyncio
import json
import logging
import os
from typing import Any, Dict, List, Optional

import vertexai
from dotenv import load_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types
from google.genai.types import HarmBlockThreshold, HarmCategory
from vertexai.preview.vision_models import ImageGenerationModel

from content_gen_agent.utils.evaluate_media import (
    calculate_evaluation_score,
    evaluate_media,
)
from content_gen_agent.utils.images import (
    IMAGE_MIME_TYPE,
    _load_gcs_image
)

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()

GCP_PROJECT = os.environ.get("GCP_PROJECT")
if GCP_PROJECT:
    vertexai.init(project=GCP_PROJECT, location="us-central1")
else:
    logging.warning(
        "GCP_PROJECT environment variable not set. Imagen 4 generation will fail."
    )

IMAGE_GEN_MODEL_GEMINI = "gemini-2.5-flash-image-preview"
IMAGE_GEN_MODEL_IMAGEN = "imagen-4.0-generate-001"
STORYLINE_MODEL = "gemini-2.5-pro"
MAX_RETRIES = 3
ASSET_SHEET_FILENAME = "asset_sheet.png"
LOGO_GCS_URI_BASE = "branding_logos/logo.png"

SAFETY_SETTINGS = [
    types.SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HATE_SPEECH,
        threshold=HarmBlockThreshold.OFF,
    ),
    types.SafetySetting(
        category=HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
        threshold=HarmBlockThreshold.OFF,
    ),
    types.SafetySetting(
        category=HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
        threshold=HarmBlockThreshold.OFF,
    ),
    types.SafetySetting(
        category=HarmCategory.HARM_CATEGORY_HARASSMENT,
        threshold=HarmBlockThreshold.OFF,
    ),
]

GENERATE_CONTENT_CONFIG = types.GenerateContentConfig(
    temperature=1.0,
    top_p=0.95,
    max_output_tokens=8192,
    safety_settings=SAFETY_SETTINGS,
)


def get_bucket() -> str:
    """Retrieves the GCS bucket name from environment variables.

    Returns:
        The GCS bucket name.

    Raises:
        RuntimeError: If neither GCS_BUCKET nor GCP_PROJECT are set.
    """
    try:
        return os.environ["GCS_BUCKET"]
    except KeyError:
        if GCP_PROJECT:
            bucket = f"{GCP_PROJECT}-contentgen-static"
            logging.warning(
                f"GCS_BUCKET environment variable not set; defaulting to {bucket}"
            )
            return bucket
        raise RuntimeError(
            "Neither GCS_BUCKET nor GCP_PROJECT environment variables are set"
        )


GCS_BUCKET = get_bucket()
LOGO_GCS_URI = f"{GCS_BUCKET}/{LOGO_GCS_URI_BASE}"

try:
    client = genai.Client()
except Exception as e:
    client = None
    logging.error(f"Failed to initialize Gemini client: {e}", exc_info=True)


async def _call_gemini_image_api(
    contents: List[Any], image_prompt: str
) -> Dict[str, Any]:
    """Calls the Gemini image generation API and evaluates the result.

    Args:
        contents (List[Any]): The content to send to the model.
        image_prompt (str): The prompt used for image generation.

    Returns:
        A dictionary with the image bytes, evaluation, and MIME type.
    """
    if not client:
        return {}

    try:
        response = await client.aio.models.generate_content(
            model=IMAGE_GEN_MODEL_GEMINI,
            contents=contents,
            config=GENERATE_CONTENT_CONFIG,
        )
        if (
            response.candidates
            and response.candidates[0].content
            and response.candidates[0].content.parts
        ):
            for part in response.candidates[0].content.parts:
                if part.inline_data and part.inline_data.data:
                    image_bytes = part.inline_data.data
                    evaluation = await evaluate_media(
                        image_bytes, IMAGE_MIME_TYPE, image_prompt
                    )
                    return {
                        "image_bytes": image_bytes,
                        "evaluation": evaluation,
                        "mime_type": IMAGE_MIME_TYPE,
                    }
    except Exception as e:
        logging.error(
            f"Error calling Gemini image API for prompt '{image_prompt}': {e}",
            exc_info=True,
        )
    return {}


async def _call_imagen_api(
    prompt: str, filename_prefix: str
) -> Dict[str, Any]:
    """Calls the Imagen 4 image generation API.

    Args:
        prompt (str): The prompt for image generation.
        filename_prefix (str): The prefix for the output filename.

    Returns:
        A dictionary with the status, filename, and image bytes.
    """
    try:
        model = ImageGenerationModel.from_pretrained(IMAGE_GEN_MODEL_IMAGEN)
        images = model.generate_images(
            prompt=prompt,
            number_of_images=1,
            aspect_ratio="9:16",
            negative_prompt="",
            person_generation="allow_all",
            safety_filter_level="block_few",
            add_watermark=True,
        )
        filename = f"{filename_prefix}.png"
        return {
            "status": "success",
            "detail": f"Image generated successfully for {filename}.",
            "filename": filename,
            "image_bytes": images[0]._image_bytes,
        }
    except Exception as e:
        logging.error(
            f"Error calling Imagen 4 API for prompt '{prompt}': {e}",
            exc_info=True,
        )
        return {
            "status": "failed",
            "detail": f"Error generating image for prompt '{prompt}': {e}",
        }


async def generate_one_image(
    prompt: str,
    input_images: Optional[List[types.Part]],
    filename_prefix: str,
) -> Dict[str, Any]:
    """Generates a single image, handling retries and model selection.

    Args:
        prompt (str): The prompt for image generation.
        input_images (Optional[List[types.Part]]): A list of input images as Part objects.
        filename_prefix (str): The prefix for the output filename.

    Returns:
        A dictionary containing the result of the image generation.
    """
    if not input_images:
        logging.info("No input image provided; using Imagen 4 for generation.")
        return await _call_imagen_api(prompt, filename_prefix)

    contents = [prompt, *input_images]
    tasks = [
        _call_gemini_image_api(contents, prompt) for _ in range(MAX_RETRIES)
    ]
    results = await asyncio.gather(*tasks)
    successful_attempts = [res for res in results if res]

    if not successful_attempts:
        return {
            "status": "failed",
            "detail": f"All image generation attempts failed for prompt: '{prompt}'.",
        }

    best_attempt = max(
        successful_attempts,
        key=lambda x: calculate_evaluation_score(x.get("evaluation")),
    )

    if best_attempt.get("evaluation").decision != "Pass":
        score = calculate_evaluation_score(best_attempt["evaluation"])
        logging.warning(
            f"No image passed evaluation for '{prompt}'. Best score: {score}"
        )

    filename = f"{filename_prefix}.png"
    return {
        "status": "success",
        "detail": f"Image generated successfully for {filename}.",
        "filename": filename,
        "image_bytes": best_attempt["image_bytes"],
    }


async def generate_images_from_storyline(
    prompts: List[str],
    tool_context: ToolContext,
    scene_numbers: Optional[List[int]] = None,
    logo_prompt_present: bool = True,
) -> List[str]:
    """Generates images for a commercial storyboard based on a visual style guide.

    Args:
        prompts (List[str]): a list of prompts in the order of the scene numbers, one prompt for each scene's image.
            - If logo_prompt_present is true, the last prompt is for the logo background.
            - Make sure to split up each scene's prompt and make them independent of each other.
            - Make sure to mention that each image should fill the space and not have empty whitespace around it.
            - Never include children.
        tool_context (ToolContext): Context for saving artifacts.
        scene_numbers (Optional[List[int]]): A list of scene numbers to generate images for.
                                                   If None or empty, images will be generated for all scenes.
                                                   Note that scene numbers are 0-based. Defaults to None.
        logo_prompt_present (bool): Whether the prompts list contains a prompt for the logo scene. If true, the logo prompt must be last. Defaults to True.

    Returns:
        A list of JSON strings with the status of each image generation.
    """
    if not client:
        return [
            json.dumps(
                {"status": "failed", "detail": "Gemini client not initialized."}
            )
        ]

    storage_client = storage.Client()
    logo_image = await _load_gcs_image(LOGO_GCS_URI, storage_client)
    if not logo_image:
        return [
            json.dumps(
                {
                    "status": "failed",
                    "detail": f"Failed to load logo from '{LOGO_GCS_URI}'.",
                }
            )
        ]

    try:
        asset_sheet_image = await tool_context.load_artifact(
            ASSET_SHEET_FILENAME
        )
        if not asset_sheet_image:
            raise ValueError("Asset sheet artifact is empty.")
    except Exception as e:
        return [
            json.dumps(
                {
                    "status": "failed",
                    "detail": f"Failed to load asset sheet: {e}",
                }
            )
        ]

    tasks = []
    scenes_to_generate = (
        scene_numbers if scene_numbers is not None else range(len(prompts))
    )

    for i, scene_num in enumerate(scenes_to_generate):
        if not (0 <= i < len(prompts)):
            continue

        prompt = prompts[i]
        is_logo_scene = logo_prompt_present and scene_num == len(prompts) - 1
        filename_prefix = f"{scene_num}_"

        if is_logo_scene:
            logo_prompt = f"Place the company logo centered on the following background: {prompt}"
            tasks.append(
                generate_one_image(logo_prompt, [logo_image], filename_prefix)
            )
        else:
            tasks.append(
                generate_one_image(
                    prompt, [asset_sheet_image], filename_prefix
                )
            )

    results = await asyncio.gather(*tasks)
    results.sort(key=lambda r: r.get("filename", ""))

    save_tasks = []
    for result in results:
        if result.get("status") == "success" and result.get("image_bytes"):
            filename = result["filename"]
            image_bytes = result["image_bytes"]
            save_tasks.append(
                tool_context.save_artifact(
                    filename,
                    types.Part.from_bytes(
                        data=image_bytes, mime_type=IMAGE_MIME_TYPE
                    ),
                )
            )
            result["detail"] = f"Image stored as {filename}."
            del result["image_bytes"]

    await asyncio.gather(*save_tasks)
    return [json.dumps(res) for res in results]
