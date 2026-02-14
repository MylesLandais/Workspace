"""Image deduplication using dHash and CLIP embeddings."""

import imagehash
from PIL import Image
from typing import Optional, List, Dict, Tuple
import numpy as np

from .storage import ImageStorage
from .vector_store import VectorStore
from ..feed.storage.valkey_connection import ValkeyConnection


class ImageDeduplicator:
    """Detects duplicate images using perceptual hashing and CLIP embeddings."""

    DHASH_KEY_PREFIX = "image:dhash:"
    DHASH_THRESHOLD = 5

    def __init__(
        self,
        storage: ImageStorage,
        vector_store: VectorStore,
        valkey: ValkeyConnection,
        dhash_threshold: int = DHASH_THRESHOLD,
    ):
        """
        Initialize image deduplicator.

        Args:
            storage: Image storage instance
            vector_store: Vector store instance
            valkey: Valkey connection for dHash cache
            dhash_threshold: Hamming distance threshold for dHash matching
        """
        self.storage = storage
        self.vector_store = vector_store
        self.client = valkey.client
        self.dhash_threshold = dhash_threshold

    def compute_dhash(self, img: Image.Image) -> str:
        """
        Compute dHash for an image.

        Args:
            img: PIL Image

        Returns:
            dHash string
        """
        hash_value = imagehash.dhash(img)
        return str(hash_value)

    def hamming_distance(self, hash1: str, hash2: str) -> int:
        """
        Calculate Hamming distance between two hashes.

        Args:
            hash1: First hash string
            hash2: Second hash string

        Returns:
            Hamming distance
        """
        return imagehash.hex_to_hash(hash1) - imagehash.hex_to_hash(hash2)

    def find_similar_dhash(
        self,
        target_hash: str,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find images with similar dHash within threshold.

        Args:
            target_hash: Target dHash
            limit: Maximum results

        Returns:
            List of similar image records
        """
        similar = []

        stored_hashes = self.client.keys(f"{self.DHASH_KEY_PREFIX}*")

        for hash_key in stored_hashes[:1000]:
            stored_hash = hash_key.decode().replace(self.DHASH_KEY_PREFIX, "")
            distance = self.hamming_distance(target_hash, stored_hash)

            if distance <= self.dhash_threshold:
                image_id_str = self.client.get(hash_key)
                if image_id_str:
                    from uuid import UUID
                    try:
                        image_id = UUID(image_id_str.decode())
                        image_data = self.storage.get_image(image_id)
                        if image_data:
                        similar.append({
                            "image_id": str(image_id),
                            "dhash": stored_hash,
                            "distance": distance,
                            "image": image_data,
                        })
                    except (ValueError, AttributeError):
                        pass

                if len(similar) >= limit:
                    break

        return sorted(similar, key=lambda x: x["distance"])

    def store_dhash(self, image_id: str, dhash: str) -> None:
        """
        Store dHash mapping in Valkey.

        Args:
            image_id: Image UUID
            dhash: Perceptual hash
        """
        key = f"{self.DHASH_KEY_PREFIX}{dhash}"
        self.client.set(key, image_id)

    def find_duplicate(
        self,
        img: Image.Image,
        embedding: Optional[np.ndarray] = None
    ) -> Optional[Dict]:
        """
        Find duplicate image using dHash and optionally CLIP.

        Args:
            img: PIL Image
            embedding: Optional CLIP embedding

        Returns:
            Duplicate image record or None
        """
        dhash = self.compute_dhash(img)

        similar_dhash = self.find_similar_dhash(dhash, limit=5)
        if similar_dhash:
            return similar_dhash[0]

        if embedding is not None:
            similar_vectors = self.vector_store.search_similar(
                embedding,
                limit=5,
                threshold=0.92
            )
            if similar_vectors:
                image_id_str = similar_vectors[0]["image_id"]
                from uuid import UUID
                try:
                    image_id = UUID(image_id_str)
                    image_data = self.storage.get_image(image_id)
                    if image_data:
                        return {
                            "image_id": str(image_id),
                            "similarity": similar_vectors[0]["similarity"],
                            "method": "clip",
                            "image": image_data,
                        }
                except (ValueError, AttributeError):
                    pass

        return None

    def handle_duplicate(
        self,
        new_img: Image.Image,
        new_url: str,
        new_quality: int,
        existing_record: Dict,
        new_embedding: Optional[np.ndarray] = None
    ) -> Tuple[str, bool]:
        """
        Handle duplicate image by comparing quality and updating relationships.

        Args:
            new_img: New image
            new_url: New image URL
            new_quality: New image quality score
            existing_record: Existing duplicate record
            new_embedding: Optional new CLIP embedding

        Returns:
            Tuple of (parent_image_id, is_new_parent)
        """
        from uuid import UUID
        existing_id_str = existing_record["image_id"]
        try:
            existing_id = UUID(existing_id_str) if isinstance(existing_id_str, str) else existing_id_str
        except (ValueError, AttributeError):
            existing_id = existing_id_str
        existing_image = existing_record.get("image", {})

        existing_quality = existing_image.get("quality_score", 0) if existing_image else 0

        if new_quality > existing_quality:
            new_image_id = self.storage.create_image(
                url=new_url,
                dhash=self.compute_dhash(new_img),
                quality_score=new_quality,
                width=new_img.width,
                height=new_img.height,
                embedding_id=str(existing_id) if new_embedding is not None else None,
            )

            if new_embedding is not None:
                self.vector_store.store_embedding(str(new_image_id), new_embedding)

            self.storage.promote_to_parent(new_image_id, existing_id)
            self.store_dhash(str(new_image_id), self.compute_dhash(new_img))

            return (str(new_image_id), True)
        else:
            new_image_id = self.storage.create_image(
                url=new_url,
                dhash=self.compute_dhash(new_img),
                quality_score=new_quality,
                width=new_img.width,
                height=new_img.height,
                parent_id=existing_id,
            )

            self.storage.add_as_derivative(new_image_id, existing_id)
            self.store_dhash(str(new_image_id), self.compute_dhash(new_img))

            return (str(existing_id), False)

