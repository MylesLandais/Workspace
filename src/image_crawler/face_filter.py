"""Face recognition filtering using InsightFace."""

import numpy as np
from typing import Optional, List, Dict
from PIL import Image

try:
    from insightface.app import FaceAnalysis
    INSIGHTFACE_AVAILABLE = True
except ImportError:
    INSIGHTFACE_AVAILABLE = False
    FaceAnalysis = None


class FaceFilter:
    """Filters images based on face recognition."""

    def __init__(
        self,
        target_face_embedding: Optional[np.ndarray] = None,
        similarity_threshold: float = 0.65,
        ctx_id: int = 0,
    ):
        """
        Initialize face filter.

        Args:
            target_face_embedding: Target person's face embedding
            similarity_threshold: Minimum cosine similarity for match
            ctx_id: GPU device ID (-1 for CPU)
        """
        if not INSIGHTFACE_AVAILABLE:
            raise ImportError(
                "insightface is not installed. "
                "Install it with: pip install insightface"
            )

        self.app = FaceAnalysis()
        self.app.prepare(ctx_id=ctx_id)
        self.target_embedding = target_face_embedding
        self.similarity_threshold = similarity_threshold

    def cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity (0-1)
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return dot_product / (norm1 * norm2)

    def is_target_person(self, img: Image.Image) -> bool:
        """
        Verify image contains target person.

        Args:
            img: PIL Image

        Returns:
            True if target person detected
        """
        if self.target_embedding is None:
            return True

        img_array = np.array(img)
        faces = self.app.get(img_array)

        if not faces:
            return False

        largest_face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
        similarity = self.cosine_similarity(
            largest_face.embedding,
            self.target_embedding
        )

        return similarity > self.similarity_threshold

    def get_faces(self, img: Image.Image) -> List[Dict]:
        """
        Get all faces detected in image.

        Args:
            img: PIL Image

        Returns:
            List of face records with embeddings
        """
        img_array = np.array(img)
        faces = self.app.get(img_array)

        return [
            {
                "bbox": face.bbox.tolist(),
                "embedding": face.embedding.tolist(),
                "age": face.age,
                "gender": face.gender,
            }
            for face in faces
        ]

    def extract_target_embedding(self, img: Image.Image) -> Optional[np.ndarray]:
        """
        Extract face embedding from image (for initial setup).

        Args:
            img: PIL Image

        Returns:
            Face embedding or None
        """
        img_array = np.array(img)
        faces = self.app.get(img_array)

        if not faces:
            return None

        largest_face = max(faces, key=lambda x: x.bbox[2] * x.bbox[3])
        return largest_face.embedding








