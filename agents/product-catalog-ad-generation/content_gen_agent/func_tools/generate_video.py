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
"""Generates video clips from images using Google's Vertex AI services."""

import asyncio
import logging
import os
import re
from typing import Any, Dict, List, Optional, Tuple

from google import genai
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai.types import GenerateVideosConfig, Image as GenImage

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

VIDEO_MODEL = "veo-3.0-fast-generate-001"
GCS_TEMPLATE_IMAGE_FOLDER = "template_images/"
ALLOWED_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg")
VIDEO_ASPECT_RATIO = "9:16"
VIDEO_FPS = 24


def _get_gcs_files(folder_prefix: str) -> List[str]:
    """Fetches all image files from a specified GCS folder.

    Args:
        folder_prefix (str): The GCS folder to search for images.

    Returns:
        A list of GCS URIs for the found images.
    """
    project_id = os.getenv("GCP_PROJECT")
    if not project_id:
        logging.error("GCP_PROJECT environment variable not set.")
        return []

    bucket_name = f"{project_id}-contentgen-static"
    try:
        storage_client = storage.Client()
        blobs = storage_client.list_blobs(bucket_name, prefix=folder_prefix)
        return [
            f"gs://{bucket_name}/{blob.name}"
            for blob in blobs
            if blob.name.lower().endswith(ALLOWED_IMAGE_EXTENSIONS)
        ]
    except Exception as e:
        logging.error(f"Failed to fetch files from GCS: {e}", exc_info=True)
        return []


async def _monitor_video_operation(
    operation: Any, image_identifier: str, vertex_client: genai.Client
) -> Tuple[Optional[GenImage], Optional[str]]:
    """Monitors a video generation operation until completion.

    Args:
        operation (Any): The video generation operation to monitor.
        image_identifier (str): An identifier for the image being processed.
        vertex_client (genai.Client): The Vertex AI client.

    Returns:
        A tuple containing the generated video object and an error message.
    """
    logging.info(
        f"Submitted video generation request for image {image_identifier}. Operation:"
        f" {operation.name}"
    )
    while not operation.done:
        await asyncio.sleep(15)
        operation = vertex_client.operations.get(operation)
        logging.info(
            f"Operation status for {image_identifier}: {operation.name} - Done:"
            f" {operation.done}"
        )

    if operation.error:
        error_message = operation.error.get("message", str(operation.error))
        logging.error(
            f"Operation for {image_identifier} failed with error: {error_message}"
        )
        return None, error_message
    if not (operation.result and hasattr(operation.result, "generated_videos")):
        logging.warning(
            f"No generated videos found in the response for {image_identifier}."
        )
        return None, "No videos found in the response."
    return operation.result.generated_videos[0], None


def _round_to_nearest_veo_duration(duration: int) -> int:
    """Rounds the desired duration to the nearest supported VEO duration.

    Args:
        duration (int): The desired duration of the video in seconds.
    """
    if duration <= 4:
        return 4
    if duration <= 6:
        return 6
    return 8


async def _generate_single_video(
    video_query: str,
    tool_context: ToolContext,
    vertex_client: genai.Client,
    input_image: GenImage,
    image_identifier: str,
    duration: int,
) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """Generates a single video from a given image and prompt.

    Args:
        video_query (str): The prompt for video generation.
        tool_context (ToolContext): The context for artifact management.
        vertex_client (genai.Client): The Vertex AI client.
        input_image (GenImage): The input image for video generation.
        image_identifier (str): An identifier for the image.
        duration (int): The desired duration of the video in seconds.

    Returns:
        A tuple containing the video result and an error message.
    """
    try:
        request = {
            "model": VIDEO_MODEL,
            "source": {"prompt": video_query, "image": input_image},
            "config": GenerateVideosConfig(
                aspect_ratio=VIDEO_ASPECT_RATIO,
                generate_audio=False,
                number_of_videos=1,
                duration_seconds=_round_to_nearest_veo_duration(duration),
                fps=VIDEO_FPS,
                person_generation="allow_all",
                enhance_prompt=True,
            ),
        }
        operation = vertex_client.models.generate_videos(**request)
        video, error = await _monitor_video_operation(
            operation, image_identifier, vertex_client
        )

        if error or not (video and video.video and video.video.video_bytes):
            return None, error or "Generated video has no content."

        filename = f"{image_identifier}.mp4"
        await tool_context.save_artifact(
            filename,
            genai.types.Part.from_bytes(
                data=video.video.video_bytes, mime_type="video/mp4"
            ),
        )
        return {"name": filename}, None
    except Exception as e:
        logging.error(
            f"Error in _generate_single_video for {image_identifier}: {e}",
            exc_info=True,
        )
        return None, str(e)


def _initialize_vertex_client() -> genai.Client:
    """Initializes and returns the Vertex AI client.

    Raises:
        ValueError: If GCP_PROJECT or GCP_LOCATION are not set.
    """
    project_id = os.getenv("GCP_PROJECT")
    location = os.getenv("GCP_LOCATION")
    if not project_id or not location:
        raise ValueError("GCP_PROJECT or GCP_LOCATION not set.")
    return genai.Client(vertexai=True, project=project_id, location=location)


async def _load_image_bytes(
    source_type: str, source_path: str, tool_context: ToolContext
) -> Tuple[Optional[bytes], str, str]:
    """Loads image bytes from either a GCS path or a tool artifact.

    Args:
        source_type (str): The source of the image ('artifact' or 'gcs').
        source_path (str): The path to the image.
        tool_context (ToolContext): The context for artifact management.

    Returns:
        A tuple with the image bytes, identifier, and MIME type.
    """
    identifier = os.path.basename(source_path).split(".")[0]
    mime_suffix = "jpeg" if source_path.lower().endswith(".jpg") else "png"

    if source_type == "artifact":
        artifact = await tool_context.load_artifact(source_path)
        image_bytes = artifact.inline_data.data if artifact and artifact.inline_data else None
    else:
        gcs_uri = source_path[5:] if source_path.startswith("gs://") else source_path
        bucket_name, blob_name = gcs_uri.split("/", 1)
        storage_client = storage.Client()
        blob = storage_client.bucket(bucket_name).blob(blob_name)
        image_bytes = blob.download_as_bytes()

    return image_bytes, identifier, f"image/{mime_suffix}"


async def generate_video(
    video_queries: List[str],
    tool_context: ToolContext,
    num_images: int,
    scene_numbers: Optional[List[int]] = None,
    logo_prompt_present: bool = True,
) -> Dict[str, Any]:
    """Generates videos in parallel from a list of prompts and images.

    Args:
        video_queries (List[str]): A list of prompts for video generation.
            - Each video query should only describe a 4 second scene, so describe a quick scene.
            - Be VERY descriptive in what movements and camera angles you expect and what should not move in the scene. Describe who/what is causing the movement.
            - It will use the image as a starting point. Be clear about how the scene transitions and keep it on theme.
            - Character names won't be understood here, use pronouns + descriptions to detail actions.
            - Make sure to mention that there should be no text or logos added to the video, except for the logo video where you should ensure the logo is always present for the entire duration of the video.
            - Explicitly ground each of your prompts to follow the laws of physics.
        tool_context (ToolContext): The context for artifact management.
        num_images (int): The total number of images available.
        scene_numbers (Optional[List[int]]): A list of specific 0-indexed scene numbers to
            generate videos for. If None, generates for all images. Must be in
            ascending order. Defaults to None.
        logo_prompt_present (bool): If true, the logo scene number must be
            included in scene_numbers. Defaults to True.

    Returns:
        A dictionary with the status and results of the video generation.
    """
    if scene_numbers:
        image_filenames = [f"{i}_.png" for i in scene_numbers]
    else:
        image_filenames = [f"{i}_.png" for i in range(num_images)]

    image_sources = [("artifact", name) for name in image_filenames]
    if not image_sources:
        image_sources = [
            ("gcs", uri) for uri in _get_gcs_files(GCS_TEMPLATE_IMAGE_FOLDER)
        ]

    vertex_client = _initialize_vertex_client()
    tasks, failed_videos = [], []

    for i, (source_type, source_path) in enumerate(image_sources):
        if i >= len(video_queries):
            break
        try:
            image_bytes, identifier, mime_type = await _load_image_bytes(
                source_type, source_path, tool_context
            )
            if not image_bytes:
                failed_videos.append({"source": source_path, "reason": "Could not load image"})
                continue

            duration = 6 if logo_prompt_present and i == len(image_sources) - 1 else 4
            tasks.append(
                _generate_single_video(
                    video_queries[i],
                    tool_context,
                    vertex_client,
                    GenImage(image_bytes=image_bytes, mime_type=mime_type),
                    identifier,
                    duration,
                )
            )
        except Exception as e:
            failed_videos.append({"source": source_path, "reason": str(e)})

    successful_videos = []
    if tasks:
        results = await asyncio.gather(*tasks)
        for i, (res, error) in enumerate(results):
            if res:
                successful_videos.append(res)
            else:
                failed_videos.append(
                    {"source": image_sources[i][1], "reason": error or "Generation failed"}
                )

    successful_videos.sort(
        key=lambda v: int(re.match(r"(\d+)", v["name"]).group(1))
        if re.match(r"(\d+)", v["name"])
        else -1
    )

    return {
        "status": "success" if successful_videos else "failed",
        "detail": f"Generated {len(successful_videos)} video(s).",
        "videos": successful_videos,
        "failed_videos": failed_videos,
    }
