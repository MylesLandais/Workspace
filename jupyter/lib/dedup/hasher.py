"""Image hashing utilities for duplicate detection."""

import hashlib
from typing import Optional
from io import BytesIO
from PIL import Image

try:
    import imagehash
    IMAGEHASH_AVAILABLE = True
except ImportError:
    IMAGEHASH_AVAILABLE = False

from .models import ImageHashes


class ImageHasher:
    """Computes various hash types for image duplicate detection."""

    HASH_SIZE = 8  # 8x8 = 64 bits

    def __init__(self):
        """Initialize image hasher."""
        if not IMAGEHASH_AVAILABLE:
            raise ImportError(
                "imagehash library is required. Install with: pip install imagehash"
            )

    def compute_sha256(self, image_bytes: bytes) -> str:
        """
        Compute SHA-256 hash of image bytes for exact duplicate detection.

        Args:
            image_bytes: Raw image bytes

        Returns:
            SHA-256 hash as hex string
        """
        return hashlib.sha256(image_bytes).hexdigest()

    def compute_phash(self, image_bytes: bytes) -> Optional[int]:
        """
        Compute 64-bit perceptual hash (pHash) for near-duplicate detection.
        pHash is robust to JPEG compression, resizing, and minor edits.

        Args:
            image_bytes: Raw image bytes

        Returns:
            64-bit pHash as integer, or None on error
        """
        try:
            img = Image.open(BytesIO(image_bytes))
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
            hash_value = imagehash.phash(img, hash_size=self.HASH_SIZE)
            # Convert to integer, ensuring it fits in 64-bit signed range
            hash_int = int(str(hash_value), 16)
            # Neo4j integers are 64-bit signed, so clamp to valid range
            max_int = 2**63 - 1
            if hash_int > max_int:
                hash_int = hash_int - (2**64)
            return hash_int
        except Exception:
            return None

    def compute_dhash(self, image_bytes: bytes) -> Optional[int]:
        """
        Compute 64-bit difference hash (dHash) for near-duplicate detection.
        dHash is fast and good for gradient-based similarity.

        Args:
            image_bytes: Raw image bytes

        Returns:
            64-bit dHash as integer, or None on error
        """
        try:
            img = Image.open(BytesIO(image_bytes))
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")
            hash_value = imagehash.dhash(img, hash_size=self.HASH_SIZE)
            # Convert to integer, ensuring it fits in 64-bit signed range
            hash_int = int(str(hash_value), 16)
            # Neo4j integers are 64-bit signed, so clamp to valid range
            max_int = 2**63 - 1
            if hash_int > max_int:
                hash_int = hash_int - (2**64)
            return hash_int
        except Exception:
            return None

    def compute_all_hashes(self, image_bytes: bytes) -> ImageHashes:
        """
        Compute all hash types for an image.

        Args:
            image_bytes: Raw image bytes

        Returns:
            ImageHashes object with all computed hashes
        """
        sha256 = self.compute_sha256(image_bytes)
        phash = self.compute_phash(image_bytes)
        dhash = self.compute_dhash(image_bytes)

        return ImageHashes(sha256=sha256, phash=phash, dhash=dhash)

    def get_image_info(self, image_bytes: bytes) -> tuple[Optional[int], Optional[int], Optional[str]]:
        """
        Get image dimensions and MIME type.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Tuple of (width, height, mime_type) or (None, None, None) on error
        """
        try:
            img = Image.open(BytesIO(image_bytes))
            width, height = img.size
            mime_type = img.format.lower() if img.format else None
            if mime_type:
                mime_type = f"image/{mime_type}"
            return width, height, mime_type
        except Exception:
            return None, None, None

