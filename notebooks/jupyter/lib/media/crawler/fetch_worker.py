"""Image fetching worker with pre-download checks and perceptual hashing."""

import requests
from io import BytesIO
from typing import Optional, Dict
from PIL import Image
import numpy as np
from uuid import uuid4

from .storage import ImageStorage
from .vector_store import VectorStore
from .deduplication import ImageDeduplicator
from .quality_scorer import QualityScorer
from .face_filter import FaceFilter


class FetchWorker:
    """Fetches and processes images with real-time deduplication."""

    MIN_IMAGE_SIZE = 50_000
    TIMEOUT = 10

    def __init__(
        self,
        storage: ImageStorage,
        vector_store: VectorStore,
        deduplicator: ImageDeduplicator,
        quality_scorer: QualityScorer,
        face_filter: Optional[FaceFilter] = None,
        min_image_size: int = MIN_IMAGE_SIZE,
        timeout: int = TIMEOUT,
    ):
        """
        Initialize fetch worker.

        Args:
            storage: Image storage instance
            vector_store: Vector store instance
            deduplicator: Image deduplicator instance
            quality_scorer: Quality scorer instance
            face_filter: Optional face filter instance
            min_image_size: Minimum image size in bytes
            timeout: Request timeout in seconds
        """
        self.storage = storage
        self.vector_store = vector_store
        self.deduplicator = deduplicator
        self.quality_scorer = quality_scorer
        self.face_filter = face_filter
        self.min_image_size = min_image_size
        self.timeout = timeout

    def process_url(self, url: str) -> Optional[Dict]:
        """
        Process a single image URL.

        Args:
            url: Image URL

        Returns:
            Image record or None if skipped
        """
        try:
            head_response = requests.head(url, timeout=5, allow_redirects=True)
            content_type = head_response.headers.get("Content-Type", "")
            content_length = int(head_response.headers.get("Content-Length", 0))

            if "image" not in content_type.lower():
                return None

            if content_length > 0 and content_length < self.min_image_size:
                return None

            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()

            img = Image.open(BytesIO(response.content))
            img.load()

            dhash = self.deduplicator.compute_dhash(img)

            similar_dhash = self.deduplicator.find_similar_dhash(dhash, limit=1)
            if similar_dhash:
                existing_record = similar_dhash[0]
                new_quality = self.quality_scorer.calculate_quality_score(img, url)
                parent_id, is_new = self.deduplicator.handle_duplicate(
                    new_img=img,
                    new_url=url,
                    new_quality=new_quality,
                    existing_record=existing_record,
                )
                from uuid import UUID
                try:
                    parent_uuid = UUID(parent_id) if isinstance(parent_id, str) else parent_id
                except (ValueError, AttributeError):
                    parent_uuid = parent_id
                self.storage.mark_url_crawled(url, parent_uuid)
                return {
                    "image_id": parent_id,
                    "is_duplicate": True,
                    "is_new_parent": is_new,
                }

            embedding = self._compute_clip_embedding(img)

            if embedding is not None:
                similar_vectors = self.vector_store.search_similar(
                    embedding,
                    limit=1,
                    threshold=0.92
                )
                if similar_vectors:
                    from uuid import UUID
                    existing_id_str = similar_vectors[0]["image_id"]
                    try:
                        existing_id = UUID(existing_id_str) if isinstance(existing_id_str, str) else existing_id_str
                    except (ValueError, AttributeError):
                        existing_id = existing_id_str
                    existing_image = self.storage.get_image(existing_id)
                    if existing_image:
                        new_quality = self.quality_scorer.calculate_quality_score(img, url)
                        existing_quality = existing_image.get("quality_score", 0)
                        if new_quality > existing_quality:
                            image_id = self.storage.create_image(
                                url=url,
                                dhash=dhash,
                                quality_score=new_quality,
                                width=img.width,
                                height=img.height,
                                embedding_id=str(existing_id),
                            )
                            self.vector_store.store_embedding(str(image_id), embedding)
                            self.deduplicator.store_dhash(str(image_id), dhash)
                            self.storage.promote_to_parent(image_id, existing_id)
                            self.storage.mark_url_crawled(url, image_id)
                            return {
                                "image_id": str(image_id),
                                "is_duplicate": True,
                                "is_new_parent": True,
                            }
                        else:
                            image_id = self.storage.create_image(
                                url=url,
                                dhash=dhash,
                                quality_score=new_quality,
                                width=img.width,
                                height=img.height,
                                parent_id=existing_id,
                            )
                            self.deduplicator.store_dhash(str(image_id), dhash)
                            self.storage.add_as_derivative(image_id, existing_id)
                            self.storage.mark_url_crawled(url, existing_id)
                            return {
                                "image_id": existing_id,
                                "is_duplicate": True,
                                "is_new_parent": False,
                            }

            if self.face_filter and not self.face_filter.is_target_person(img):
                return None

            quality_score = self.quality_scorer.calculate_quality_score(img, url)

            image_id = self.storage.create_image(
                url=url,
                dhash=dhash,
                quality_score=quality_score,
                width=img.width,
                height=img.height,
                embedding_id=str(uuid4()) if embedding is not None else None,
            )

            if embedding is not None:
                self.vector_store.store_embedding(str(image_id), embedding)

            self.deduplicator.store_dhash(str(image_id), dhash)
            self.storage.mark_url_crawled(url, image_id)

            return {
                "image_id": str(image_id),
                "is_duplicate": False,
                "is_new_parent": False,
            }

        except Exception as e:
            return None

    def _compute_clip_embedding(self, img: Image.Image) -> Optional[np.ndarray]:
        """
        Compute CLIP embedding for image.

        Args:
            img: PIL Image

        Returns:
            CLIP embedding vector or None
        """
        try:
            from sentence_transformers import SentenceTransformer

            if not hasattr(self, "_clip_model"):
                self._clip_model = SentenceTransformer("clip-ViT-B-32")

            embedding = self._clip_model.encode(img)
            return embedding
        except Exception:
            return None

