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
"""Handles the generation of storylines, visual style guides, and asset sheets."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types
from google.genai.types import HarmBlockThreshold, HarmCategory

from content_gen_agent.utils.storytelling import STORYTELLING_INSTRUCTIONS
from content_gen_agent.func_tools.select_product import select_product_from_bq
from content_gen_agent.utils.evaluate_media import (
    calculate_evaluation_score,
    evaluate_media,
)
from content_gen_agent.utils.images import (
    IMAGE_MIME_TYPE,
    _load_gcs_image
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

load_dotenv()

# Initialize Gemini client
try:
    client = genai.Client()
except Exception as e:
    client = None
    logging.error(f"Failed to initialize Gemini client: {e}", exc_info=True)

# --- Configuration ---
STORYLINE_MODEL = "gemini-2.5-pro"
IMAGE_GEN_MODEL = "gemini-2.5-flash-image-preview"
MAX_RETRIES = 3

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


async def generate_storyline(
    product: str,
    target_demographic: str,
    tool_context: ToolContext,
    company_name: str,
    num_images: int = 5,
    product_photo_filename: Optional[str] = None,
    style_preference: str = "photorealistic",
    user_provided_asset_sheet_gcs_uri: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates a storyline, visual style guide, and asset sheet.

    Args:
        product (str): The company's product to be featured. This is used to search
          a product database. Just include the product name.
        target_demographic (str): The target audience for the commercial.
        tool_context (ToolContext): The context for saving artifacts.
        company_name (str): The name of the company to be featured.
        num_images (int): The number of images to generate. Defaults to 5.
        product_photo_filename (Optional[str]): The filename of the product photo
          artifact. Defaults to None.
        style_preference (str): The desired visual style of the ad.
          Defaults to "photorealistic".
        user_provided_asset_sheet_gcs_uri (Optional[str]): The GCS URI of the
          user-provided asset sheet. Defaults to None.

    Returns:
        A dictionary containing the generated content and status.
    """
    if not client:
        logging.error("Gemini client not initialized. Check credentials.")
        return {"status": "failed", "detail": "Gemini client not initialized."}

    style_guide = (
        f"The style must be cohesive, professional, high-quality, with "
        f"minimal whitespace and a '{style_preference}' effect."
    )

    # If we're using a user provided asset sheet, load this before the storyline text step
    image_part = None
    if user_provided_asset_sheet_gcs_uri:
        # Load asset sheet from storage and save to tool context
        storage_client = storage.Client()
        if user_provided_asset_sheet_gcs_uri.startswith("gs://"):
            user_provided_asset_sheet_gcs_uri = user_provided_asset_sheet_gcs_uri[5:]
        image_part = await _load_gcs_image(user_provided_asset_sheet_gcs_uri, storage_client)
        asset_sheet_filename = "asset_sheet.png"
        await tool_context.save_artifact(
            asset_sheet_filename,
            image_part
        )
        logging.info(f"Saved user-provided asset sheet image to {asset_sheet_filename}")

    story_data = _generate_storyline_text(
        product,
        target_demographic,
        num_images,
        style_guide,
        company_name,
        image_part,
    )
    if "error" in story_data:
        return {"status": "failed", "detail": story_data["error"]}


    # Generate the asset sheet from scratch using the generated storyline text
    if not user_provided_asset_sheet_gcs_uri:
        # Grab the product photo from BQ based on the product name the agent extracted from the user query
        product_photo_filename = await _ensure_product_photo_artifact(
            product, tool_context, product_photo_filename
        )
        if not product_photo_filename:
            return {
                "status": "failed",
                "detail": "Failed to populate product photos.",
            }

        asset_sheet_filename = await _generate_asset_sheet_image(
            story_data, product_photo_filename, tool_context, style_guide
        )

    vsg_filename = await _save_json_artifact(
        tool_context,
        "visual_style_guide",
        story_data["visual_style_guide"],
    )
    storyline_filename = await _save_json_artifact(
        tool_context, "storyline", {"storyline": story_data.get("storyline")}
    )

    return {
        "storyline": story_data.get("storyline"),
        "asset_sheet_filename": asset_sheet_filename,
        "visual_style_guide_filename": vsg_filename,
        "storyline_filename": storyline_filename,
        "status": "success",
    }


def _generate_storyline_text(
    product: str,
    target_demographic: str,
    num_images: int,
    style_guide: str,
    company_name: str,
    image_part: Optional[genai.types.Part] = None,
) -> Dict[str, Any]:
    """Generates the storyline and visual style guide text.

    Args:
        product (str): The product to be featured.
        target_demographic (str): The target audience.
        num_images (int): The number of images to generate.
        style_guide (str): The visual style description.
        company_name (str): The name of the company to be featured.
        image_part (Optional[genai.types.Part]): An optional user-provided asset sheet.
          Defaults to None.

    Returns:
        A dictionary containing the storyline and visual style guide.
    """
    generation_prompt = f"""
    You are a creative assistant for {company_name}. Your task is to generate a compelling storyline
    and a detailed visual style guide for a short commercial about the '{product}' for the
    '{target_demographic}' demographic.

    The storyline should have a before, purchasing, and after narrative. If generating more
    than 3 scenes, make the first scene a slow flyover aerial shot of the location without
    any characters.

    Make sure the storyline matches the following style guide: '{style_guide}'

    Your final scene should always be a shot with a logo in front and a beautiful, moving
    background. Keep the {company_name} logo prominent in the center frame and animate the background
    to make it feel dynamic.

    The visual style guide must describe the necessary imagery. Provide detailed descriptions
    of characters (with gender and age, adults only), each scene's locations, and a short
    list of critical props and assets (excluding the {product}).

    {STORYTELLING_INSTRUCTIONS}

    Please return the output as a single JSON object with two keys: "storyline" and "visual_style_guide".
    The "storyline" key must contain a single string narrative with {num_images} scenes.
     - Do not refer to other scenes in a scene description; be explicit about what each scene is about.
     - For each Scene, structure it as follows:
         # Scene _: `Title`
         ## `Description`
    The "visual_style_guide" should contain "characters", "locations", and "asset_sheet".
    """
    try:
        logging.info("Generating storyline and visual style guide...")
        contents = []
        if image_part:
            contents.append(image_part)
            generation_prompt += """
    IMPORTANT: Write the storyline based on the attached asset sheet image.  The asset sheet contains
    the character(s) that should appear in the story.  Make sure your story is based on these characters.
            """
        contents.append(generation_prompt)

        response = client.models.generate_content(
            model=STORYLINE_MODEL,
            contents=contents,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            ),
        )
        if response.text:
            story_data = json.loads(response.text)
            logging.info(
                "Successfully generated storyline and visual style guide."
            )
            return story_data
        return {"error": "Received an empty response from the model."}
    except Exception as e:
        logging.error(f"Error generating storyline text: {e}", exc_info=True)
        return {"error": f"Error generating storyline text: {e}"}


async def _ensure_product_photo_artifact(
    product: str, tool_context: ToolContext, product_photo_filename: Optional[str]
) -> Optional[str]:
    """Ensures the product photo artifact exists, creating it if necessary.

    If a `product_photo_filename` is provided, it will be used directly.
    Otherwise, it fetches the product's image URI from BigQuery, downloads it
    from GCS, and saves it as an artifact.

    Args:
        product (str): The product name to look up if no filename is provided.
        tool_context (ToolContext): The context for accessing and saving artifacts.
        product_photo_filename (Optional[str]): The filename of an existing product
          photo artifact. Defaults to None.

    Returns:
        The filename of the product photo artifact, or None on failure.
    """
    if product_photo_filename:
        if product_photo_filename.startswith("gs://"):
            try:
                storage_client = storage.Client()
                gcs_uri = product_photo_filename.replace("gs://", "")
                product_photo_part = await _load_gcs_image(gcs_uri, storage_client)
                if product_photo_part:
                    artifact_filename = gcs_uri.split("/")[-1]
                    await tool_context.save_artifact(artifact_filename, product_photo_part)
                    logging.info(f"Saved product photo from GCS URI '{gcs_uri}' as artifact '{artifact_filename}'")
                    return artifact_filename
                else:
                    raise ValueError("Failed to load image from GCS.")
            except Exception as e:
                logging.warning(f"Failed to process GCS URI '{product_photo_filename}': {e}. Will attempt to fetch from BigQuery.", exc_info=True)
        else:
            try:
                # Verify the artifact exists by trying to load it.
                await tool_context.load_artifact(product_photo_filename)
                logging.info(
                    f"Using existing product photo artifact: {product_photo_filename}"
                )
                return product_photo_filename
            except Exception as e:
                logging.warning(
                    f"Could not load provided artifact '{product_photo_filename}': {e}."
                    " Will attempt to fetch from BigQuery."
                )

    product_details = select_product_from_bq(product)
    if not product_details or "image_gcs_uri" not in product_details:
        logging.error(f"Product '{product}' not found in BigQuery.")
        return None

    gcs_uri = product_details["image_gcs_uri"]
    try:
        storage_client = storage.Client()
        bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(blob_name)
        image_bytes = blob.download_as_bytes()

        # Use the blob name as the artifact filename
        artifact_filename = blob_name.split("/")[-1]
        product_photo_part = genai.types.Part.from_bytes(
            data=image_bytes, mime_type=IMAGE_MIME_TYPE
        )
        await tool_context.save_artifact(artifact_filename, product_photo_part)
        logging.info(f"Saved product photo '{gcs_uri}' as artifact '{artifact_filename}'")
        return artifact_filename
    except Exception as e:
        logging.error(f"Failed to download or save product photo from GCS: {e}", exc_info=True)
        return None


async def _call_image_generation_api(
    contents: List[Any], image_prompt: str
) -> Dict[str, Any]:
    """Calls the image generation API and evaluates the result.

    Args:
        contents (List[Any]): The content to send to the model.
        image_prompt (str): The prompt used for image generation.

    Returns:
        A dictionary with the image bytes, evaluation result, and MIME type.
    """
    try:
        response = await client.aio.models.generate_content(
            model=IMAGE_GEN_MODEL,
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
            f"Error calling image generation API: {e}", exc_info=True
        )
    return {}


def _process_visual_style_guide(
    visual_style_guide: Dict[str, Any]
) -> Dict[str, str]:
    """Processes the visual style guide into formatted strings.

    Args:
        visual_style_guide (Dict[str, Any]): The visual style guide dictionary.

    Returns:
        A dictionary of processed descriptions.
    """

    def format_list(items: List[Any]) -> str:
        processed = []
        for item in items:
            if isinstance(item, dict):
                processed.append(" ".join(str(v) for v in item.values()))
            else:
                processed.append(str(item))
        return ", ".join(processed)

    asset_sheet_items = visual_style_guide.get("asset_sheet", [])
    characters = visual_style_guide.get("characters", [])
    locations = visual_style_guide.get("locations", [])

    return {
        "asset_sheet": format_list(asset_sheet_items),
        "characters": ". ".join(
            f"{item.get('name', '')}: {item.get('description', '')}"
            if isinstance(item, dict)
            else str(item)
            for item in characters
        ),
        "locations": format_list(locations),
    }


async def _generate_asset_sheet_image(
    story_data: Dict[str, Any],
    product_photo_filename: str,
    tool_context: ToolContext,
    style_guide: str,
) -> str:
    """Generates and evaluates asset sheet images, saving the best one.

    Args:
        story_data (Dict[str, Any]): The storyline and visual style guide data.
        product_photo_filename (str): The filename of the product photo.
        tool_context (ToolContext): The context for saving artifacts.
        style_guide (str): The visual style description.

    Returns:
        The filename of the generated asset sheet
    """
    visual_style_guide = story_data.get("visual_style_guide", {})
    processed_vsg = _process_visual_style_guide(visual_style_guide)

    image_prompt = f"""A visual asset sheet for a commercial.
    Instructions: Create a clean, organized collage displaying each of the following:
    1) Front and side profiles of each character
    2) Locations/settings for each scene
    3) The attached product image.
    {style_guide}

    Characters: {processed_vsg["characters"]}
    Locations: {processed_vsg["locations"]}
    Product: Attached image.
    """

    logging.info(f"Generating asset sheet image for prompt: '{image_prompt}'")

    try:
        contents = [image_prompt]
        product_photo_part = await tool_context.load_artifact(
            product_photo_filename
        )
        if product_photo_part:
            contents.append(product_photo_part)
    except Exception as e:
        logging.error(
            f"Failed to load product photo artifact '{product_photo_filename}': {e}",
            exc_info=True,
        )
        return {
            "status": "failed",
            "detail": f"Failed to load product photo: {e}",
        }

    tasks = [
        _call_image_generation_api(contents, image_prompt)
        for _ in range(MAX_RETRIES)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    generation_attempts = [
        res for res in results if isinstance(res, dict) and res
    ]
    if not generation_attempts:
        return {
            "status": "failed",
            "detail": "Failed to generate any asset sheet images.",
        }

    best_attempt = max(
        generation_attempts,
        key=lambda x: calculate_evaluation_score(x.get("evaluation")),
    )

    if best_attempt["evaluation"].decision != "Pass":
        score = calculate_evaluation_score(best_attempt["evaluation"])
        logging.warning(
            f"No image passed evaluation. Selecting best attempt with score: {score}"
        )

    asset_sheet_filename = "asset_sheet.png"
    await tool_context.save_artifact(
        asset_sheet_filename,
        genai.types.Part.from_bytes(
            data=best_attempt["image_bytes"], mime_type=best_attempt["mime_type"]
        ),
    )
    logging.info(f"Saved asset sheet image to {asset_sheet_filename}")

    return asset_sheet_filename

async def _save_json_artifact(
    tool_context: ToolContext, name: str, data: Dict[str, Any]
) -> str:
    """Saves a JSON object as a text artifact.

    Args:
        tool_context (ToolContext): The context for saving artifacts.
        name (str): The base name for the artifact file.
        data (Dict[str, Any]): The JSON-serializable data to save.

    Returns:
        The filename of the saved artifact.
    """
    idx = int(time.time() * 1000) % 100
    filename = f"{name}_{idx}.json"
    json_data = json.dumps(data)
    part = genai.types.Part(text=json_data)
    await tool_context.save_artifact(filename, part)
    logging.info(f"Saved {name} to artifacts as {filename}")
    return filename

