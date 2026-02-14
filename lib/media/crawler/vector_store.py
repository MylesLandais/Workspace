"""Valkey vector search for CLIP embeddings."""

import numpy as np
from typing import List, Dict, Optional
import redis
from redis.commands.search.field import VectorField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query

from ..feed.storage.valkey_connection import ValkeyConnection


class VectorStore:
    """Manages CLIP embeddings in Valkey with vector similarity search."""

    INDEX_NAME = "clip_embeddings_idx"
    DOC_PREFIX = "image:embedding:"
    VECTOR_DIM = 512

    def __init__(self, valkey: ValkeyConnection):
        """
        Initialize vector store.

        Args:
            valkey: Valkey connection instance
        """
        self.valkey = valkey
        self.client = valkey.client
        self._ensure_index()

    def _ensure_index(self) -> None:
        """Create ValkeySearch index if it doesn't exist."""
        try:
            self.client.ft(self.INDEX_NAME).info()
        except redis.exceptions.ResponseError:
            schema = (
                TagField("image_id"),
                VectorField(
                    "embedding",
                    "HNSW",
                    {
                        "TYPE": "FLOAT32",
                        "DIM": self.VECTOR_DIM,
                        "DISTANCE_METRIC": "COSINE",
                        "INITIAL_CAP": 10000,
                    }
                ),
            )
            definition = IndexDefinition(
                prefix=[self.DOC_PREFIX],
                index_type=IndexType.HASH
            )
            self.client.ft(self.INDEX_NAME).create_index(schema, definition=definition)

    def store_embedding(
        self,
        image_id: str,
        embedding: np.ndarray,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Store CLIP embedding for an image.

        Args:
            image_id: Image UUID or identifier
            embedding: CLIP embedding vector (512-dim)
            metadata: Optional metadata to store
        """
        if embedding.shape[0] != self.VECTOR_DIM:
            raise ValueError(f"Embedding must be {self.VECTOR_DIM}-dimensional")

        key = f"{self.DOC_PREFIX}{image_id}"
        embedding_bytes = embedding.astype(np.float32).tobytes()

        mapping = {
            "image_id": image_id,
            "embedding": embedding_bytes,
        }

        if metadata:
            for k, v in metadata.items():
                if isinstance(v, (str, int, float)):
                    mapping[k] = str(v)

        self.client.hset(key, mapping=mapping)

    def search_similar(
        self,
        query_embedding: np.ndarray,
        limit: int = 5,
        threshold: float = 0.92
    ) -> List[Dict]:
        """
        Search for similar images using vector similarity.

        Args:
            query_embedding: Query embedding vector (512-dim)
            limit: Maximum results
            threshold: Minimum cosine similarity (0-1)

        Returns:
            List of similar image records with scores
        """
        if query_embedding.shape[0] != self.VECTOR_DIM:
            raise ValueError(f"Embedding must be {self.VECTOR_DIM}-dimensional")

        query_bytes = query_embedding.astype(np.float32).tobytes()

        query = (
            Query(f"*=>[KNN {limit} @embedding $vec AS score]")
            .sort_by("score")
            .return_fields("image_id", "score")
            .paging(0, limit)
            .dialect(2)
        )

        try:
            results = self.client.ft(self.INDEX_NAME).search(
                query,
                query_params={"vec": query_bytes}
            )

            similar = []
            for doc in results.docs:
                score = float(doc.score)
                if score >= threshold:
                    similar.append({
                        "image_id": doc.image_id,
                        "similarity": score,
                    })

            return similar
        except Exception as e:
            return []

    def get_embedding(self, image_id: str) -> Optional[np.ndarray]:
        """
        Get embedding for an image.

        Args:
            image_id: Image UUID or identifier

        Returns:
            Embedding vector or None
        """
        key = f"{self.DOC_PREFIX}{image_id}"
        embedding_bytes = self.client.hget(key, "embedding")

        if embedding_bytes:
            return np.frombuffer(embedding_bytes, dtype=np.float32)
        return None

    def delete_embedding(self, image_id: str) -> None:
        """
        Delete embedding for an image.

        Args:
            image_id: Image UUID or identifier
        """
        key = f"{self.DOC_PREFIX}{image_id}"
        self.client.delete(key)

    def batch_store(
        self,
        embeddings: Dict[str, np.ndarray],
        metadata: Optional[Dict[str, Dict]] = None
    ) -> None:
        """
        Batch store multiple embeddings.

        Args:
            embeddings: Dictionary mapping image_id to embedding
            metadata: Optional dictionary mapping image_id to metadata
        """
        pipeline = self.client.pipeline()

        for image_id, embedding in embeddings.items():
            if embedding.shape[0] != self.VECTOR_DIM:
                continue

            key = f"{self.DOC_PREFIX}{image_id}"
            embedding_bytes = embedding.astype(np.float32).tobytes()

            mapping = {
                "image_id": image_id,
                "embedding": embedding_bytes,
            }

            if metadata and image_id in metadata:
                for k, v in metadata[image_id].items():
                    if isinstance(v, (str, int, float)):
                        mapping[k] = str(v)

            pipeline.hset(key, mapping=mapping)

        pipeline.execute()








