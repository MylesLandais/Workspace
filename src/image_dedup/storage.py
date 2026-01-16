"""Image filesystem storage for deduplicated images."""

import os
import uuid
from pathlib import Path
from typing import Optional, Tuple
import mimetypes
from PIL import Image
from io import BytesIO

from .hasher import ImageHasher


class ImageStorage:
    """Manages local filesystem storage for images."""

    def __init__(self, storage_path: str):
        """
        Initialize image storage.

        Args:
            storage_path: Base directory for storing images
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.hasher = ImageHasher()

    def _get_image_directory(self, sha256: str) -> Path:
        """
        Get storage directory for an image based on SHA-256.
        Uses first 2 hex characters for directory structure.

        Args:
            sha256: SHA-256 hash (hex string)

        Returns:
            Path to image directory
        """
        prefix = sha256[:2]
        return self.storage_path / prefix

    def _get_image_path(self, sha256: str, extension: Optional[str] = None) -> Path:
        """
        Get full path to stored image file.

        Args:
            sha256: SHA-256 hash (hex string)
            extension: File extension (e.g., 'jpg', 'png'). Auto-detected if None.

        Returns:
            Path to image file
        """
        directory = self._get_image_directory(sha256)
        directory.mkdir(parents=True, exist_ok=True)

        if extension:
            filename = f"{sha256}.{extension}"
        else:
            filename = sha256

        return directory / filename

    def store_image(
        self,
        image_bytes: bytes,
        sha256: Optional[str] = None,
    ) -> Tuple[str, str, int, int, int, str]:
        """
        Store image and return metadata.

        Args:
            image_bytes: Raw image bytes
            sha256: Pre-computed SHA-256 hash (computed if not provided)

        Returns:
            Tuple of (sha256, file_path, width, height, size_bytes, mime_type)
        """
        if sha256 is None:
            sha256 = self.hasher.compute_sha256(image_bytes)

        # Detect MIME type and extension
        img = Image.open(BytesIO(image_bytes))
        width, height = img.size
        format_name = img.format.lower() if img.format else "jpg"
        extension = format_name
        mime_type = f"image/{format_name}"

        # Get file path
        file_path = self._get_image_path(sha256, extension)

        # Store image if it doesn't exist
        if not file_path.exists():
            file_path.write_bytes(image_bytes)

        size_bytes = len(image_bytes)

        return sha256, str(file_path), width, height, size_bytes, mime_type

    def get_image_path(self, sha256: str) -> Optional[Path]:
        """
        Get path to stored image.

        Args:
            sha256: SHA-256 hash

        Returns:
            Path to image file if exists, None otherwise
        """
        directory = self._get_image_directory(sha256)

        # Try common extensions
        for ext in ["jpg", "jpeg", "png", "webp", "gif"]:
            path = directory / f"{sha256}.{ext}"
            if path.exists():
                return path

        # Try without extension
        path = directory / sha256
        if path.exists():
            return path

        return None

    def get_image_bytes(self, sha256: str) -> Optional[bytes]:
        """
        Retrieve image bytes.

        Args:
            sha256: SHA-256 hash

        Returns:
            Image bytes if found, None otherwise
        """
        path = self.get_image_path(sha256)
        if path and path.exists():
            return path.read_bytes()
        return None

    def delete_image(self, sha256: str) -> bool:
        """
        Delete stored image.

        Args:
            sha256: SHA-256 hash

        Returns:
            True if deleted, False if not found
        """
        path = self.get_image_path(sha256)
        if path and path.exists():
            path.unlink()
            return True
        return False

    def image_exists(self, sha256: str) -> bool:
        """
        Check if image exists in storage.

        Args:
            sha256: SHA-256 hash

        Returns:
            True if image exists, False otherwise
        """
        return self.get_image_path(sha256) is not None







