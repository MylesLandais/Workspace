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
from google.cloud import storage
from google.genai import types
import logging
from typing import Optional

# --- Configuration ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

IMAGE_MIME_TYPE = "image/png"

async def _load_gcs_image(
    gcs_uri: str, storage_client: storage.Client
) -> Optional[types.Part]:
    """Loads an image from GCS and returns it as a Part object.

    Args:
        gcs_uri: The GCS URI of the image. Does not start with "gs://"
        storage_client: The GCS storage client.

    Returns:
        A Part object containing the image data, or None on failure.
    """
    try:
        bucket_name, blob_name = gcs_uri.split("/", 1)
        blob = storage_client.bucket(bucket_name).blob(blob_name)
        image_bytes = blob.download_as_bytes()
        return types.Part.from_bytes(data=image_bytes, mime_type=IMAGE_MIME_TYPE)
    except Exception as e:
        logging.error(f"Failed to load image from '{gcs_uri}': {e}")
        return None


