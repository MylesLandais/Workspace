"""CLIP embedding computation for semantic similarity."""

from typing import Optional
import numpy as np
from io import BytesIO
from PIL import Image

try:
    from sentence_transformers import SentenceTransformer
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False


class CLIPEmbedder:
    """Computes CLIP embeddings for semantic image similarity."""

    MODEL_NAME = "clip-ViT-B-32"
    THRESHOLD = 0.95  # Cosine similarity threshold

    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize CLIP embedder.

        Args:
            model_name: CLIP model name (default: 'clip-ViT-B-32')
        """
        if not CLIP_AVAILABLE:
            raise ImportError(
                "sentence-transformers is required for CLIP. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name or self.MODEL_NAME
        self.model = SentenceTransformer(self.model_name)
        self.threshold = self.THRESHOLD

    def compute_embedding(self, image_bytes: bytes) -> Optional[np.ndarray]:
        """
        Compute CLIP embedding for an image.

        Args:
            image_bytes: Raw image bytes

        Returns:
            CLIP embedding vector (numpy array) or None on error
        """
        try:
            img = Image.open(BytesIO(image_bytes))
            # Convert to RGB if needed
            if img.mode != "RGB":
                img = img.convert("RGB")

            # Compute embedding
            embedding = self.model.encode(img, convert_to_numpy=True)

            return embedding
        except Exception:
            return None

    def cosine_similarity(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> float:
        """
        Compute cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity score (0-1)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Cosine similarity
        dot_product = np.dot(embedding1, embedding2)
        similarity = dot_product / (norm1 * norm2)

        # Ensure result is in [0, 1] range (CLIP embeddings should already be normalized)
        return float(max(0.0, min(1.0, similarity)))

    def is_similar(
        self, embedding1: np.ndarray, embedding2: np.ndarray
    ) -> tuple[bool, float]:
        """
        Check if two embeddings are similar based on threshold.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Tuple of (is_similar: bool, similarity_score: float)
        """
        similarity = self.cosine_similarity(embedding1, embedding2)
        is_similar = similarity >= self.threshold

        return is_similar, similarity







