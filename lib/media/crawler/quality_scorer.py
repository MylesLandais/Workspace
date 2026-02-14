"""Quality scoring for images with screenshot detection."""

import cv2
import numpy as np
from PIL import Image
from typing import Optional
import pytesseract


class QualityScorer:
    """Calculates quality scores for images with screenshot detection."""

    def __init__(self):
        """Initialize quality scorer."""
        pass

    def calculate_quality_score(self, img: Image.Image, url: str) -> int:
        """
        Calculate quality score for an image.

        Args:
            img: PIL Image
            url: Image URL

        Returns:
            Quality score (higher is better)
        """
        score = 0
        width, height = img.size

        megapixels = (width * height) / 1_000_000
        score += megapixels * 100

        aspect = width / height

        if 0.45 <= aspect <= 0.47:
            score -= 150

        img_array = np.array(img.convert("RGB"))

        top_slice = img_array[:int(height * 0.05), :]
        if np.mean(top_slice) < 15:
            score -= 100

        bottom_slice = img_array[int(height * 0.92):, :]
        if self._detect_text_region(bottom_slice):
            score -= 200

        try:
            text = pytesseract.image_to_string(img)
            word_count = len(text.split())
            if word_count > 3:
                score -= 50 * word_count
        except Exception:
            pass

        if hasattr(img, "info") and "quality" in img.info:
            score += img.info["quality"]

        if "cdn" in url or "media" in url:
            score += 50
        if "thumbnail" in url or "preview" in url:
            score -= 100

        return max(score, 0)

    def _detect_text_region(self, image_slice: np.ndarray) -> bool:
        """
        Detect horizontal text bars using edge detection.

        Args:
            image_slice: Image slice array

        Returns:
            True if text region detected
        """
        try:
            gray = cv2.cvtColor(image_slice, cv2.COLOR_RGB2GRAY)
            edges = cv2.Canny(gray, 50, 150)

            horizontal_edges = np.sum(edges, axis=1)
            return np.max(horizontal_edges) > edges.shape[1] * 0.3
        except Exception:
            return False

    def is_screenshot(self, img: Image.Image) -> bool:
        """
        Detect if image is likely a screenshot.

        Args:
            img: PIL Image

        Returns:
            True if likely a screenshot
        """
        width, height = img.size
        aspect = width / height

        if 0.45 <= aspect <= 0.47:
            return True

        img_array = np.array(img.convert("RGB"))

        top_slice = img_array[:int(height * 0.05), :]
        if np.mean(top_slice) < 15:
            return True

        bottom_slice = img_array[int(height * 0.92):, :]
        if self._detect_text_region(bottom_slice):
            return True

        return False








