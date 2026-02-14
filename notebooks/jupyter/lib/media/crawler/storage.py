"""Neo4j graph storage for images and relationships."""

from datetime import datetime
from typing import Optional, Dict, List
from uuid import UUID, uuid4

from ..feed.storage.neo4j_connection import Neo4jConnection


class ImageStorage:
    """Manages image storage in Neo4j graph database."""

    def __init__(self, neo4j: Neo4jConnection):
        """
        Initialize image storage.

        Args:
            neo4j: Neo4j connection instance
        """
        self.neo4j = neo4j
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        """Create Neo4j schema constraints and indexes if they don't exist."""
        constraints = [
            "CREATE CONSTRAINT image_uuid IF NOT EXISTS FOR (i:Image) REQUIRE i.uuid IS UNIQUE",
            "CREATE INDEX image_dhash IF NOT EXISTS FOR (i:Image) ON (i.dhash)",
            "CREATE INDEX image_quality IF NOT EXISTS FOR (i:Image) ON (i.quality_score)",
            "CREATE INDEX image_url IF NOT EXISTS FOR (i:Image) ON (i.url)",
        ]

        for constraint in constraints:
            try:
                self.neo4j.execute_write(constraint)
            except Exception:
                pass

    def create_image(
        self,
        url: str,
        dhash: str,
        quality_score: int,
        width: int,
        height: int,
        embedding_id: Optional[str] = None,
        parent_id: Optional[UUID] = None,
    ) -> UUID:
        """
        Create a new image node in Neo4j.

        Args:
            url: Image URL
            dhash: Perceptual hash (dHash)
            quality_score: Quality score
            width: Image width in pixels
            height: Image height in pixels
            embedding_id: Optional embedding ID for vector search
            parent_id: Optional parent image UUID if this is a derivative

        Returns:
            Created image UUID
        """
        image_uuid = uuid4()
        now = datetime.utcnow()

        if parent_id:
            query = """
            MATCH (parent:Image {uuid: $parent_id})
            CREATE (img:Image {
                uuid: $uuid,
                url: $url,
                dhash: $dhash,
                quality_score: $quality_score,
                width: $width,
                height: $height,
                embedding_id: $embedding_id,
                created_at: datetime(),
                updated_at: datetime()
            })
            CREATE (img)-[:DERIVATIVE_OF]->(parent)
            RETURN img.uuid as uuid
            """
            result = self.neo4j.execute_write(
                query,
                parameters={
                    "uuid": str(image_uuid),
                    "url": url,
                    "dhash": dhash,
                    "quality_score": quality_score,
                    "width": width,
                    "height": height,
                    "embedding_id": embedding_id,
                    "parent_id": str(parent_id),
                }
            )
        else:
            query = """
            CREATE (img:Image {
                uuid: $uuid,
                url: $url,
                dhash: $dhash,
                quality_score: $quality_score,
                width: $width,
                height: $height,
                embedding_id: $embedding_id,
                created_at: datetime(),
                updated_at: datetime()
            })
            RETURN img.uuid as uuid
            """
            result = self.neo4j.execute_write(
                query,
                parameters={
                    "uuid": str(image_uuid),
                    "url": url,
                    "dhash": dhash,
                    "quality_score": quality_score,
                    "width": width,
                    "height": height,
                    "embedding_id": embedding_id,
                }
            )

        if result:
            return UUID(result[0]["uuid"])
        return image_uuid

    def get_image(self, image_uuid: UUID) -> Optional[Dict]:
        """
        Get image by UUID.

        Args:
            image_uuid: Image UUID

        Returns:
            Image record or None
        """
        query = """
        MATCH (img:Image {uuid: $uuid})
        RETURN img
        LIMIT 1
        """
        result = self.neo4j.execute_read(
            query,
            parameters={"uuid": str(image_uuid)}
        )

        if result:
            img_node = result[0]["img"]
            return dict(img_node)
        return None

    def find_images_by_dhash(self, dhash: str, limit: int = 10) -> List[Dict]:
        """
        Find images by dHash (exact match).

        Args:
            dhash: Perceptual hash
            limit: Maximum results

        Returns:
            List of image records
        """
        query = """
        MATCH (img:Image {dhash: $dhash})
        RETURN img
        ORDER BY img.quality_score DESC
        LIMIT $limit
        """
        result = self.neo4j.execute_read(
            query,
            parameters={"dhash": dhash, "limit": limit}
        )

        return [dict(record["img"]) for record in result]

    def get_parent_image(self, image_uuid: UUID) -> Optional[Dict]:
        """
        Get parent image for a derivative.

        Args:
            image_uuid: Derivative image UUID

        Returns:
            Parent image record or None
        """
        query = """
        MATCH (img:Image {uuid: $uuid})-[:DERIVATIVE_OF]->(parent:Image)
        RETURN parent
        LIMIT 1
        """
        result = self.neo4j.execute_read(
            query,
            parameters={"uuid": str(image_uuid)}
        )

        if result:
            return dict(result[0]["parent"])
        return None

    def get_derivatives(self, image_uuid: UUID, limit: int = 100) -> List[Dict]:
        """
        Get all derivative images for a parent.

        Args:
            image_uuid: Parent image UUID
            limit: Maximum results

        Returns:
            List of derivative image records
        """
        query = """
        MATCH (parent:Image {uuid: $uuid})<-[:DERIVATIVE_OF]-(deriv:Image)
        RETURN deriv
        ORDER BY deriv.quality_score DESC
        LIMIT $limit
        """
        result = self.neo4j.execute_read(
            query,
            parameters={"uuid": str(image_uuid), "limit": limit}
        )

        return [dict(record["deriv"]) for record in result]

    def promote_to_parent(self, image_uuid: UUID, old_parent_uuid: UUID) -> None:
        """
        Promote a derivative image to become the parent.

        Args:
            image_uuid: Image UUID to promote
            old_parent_uuid: Old parent UUID
        """
        query = """
        MATCH (new_parent:Image {uuid: $new_parent_uuid})
        MATCH (old_parent:Image {uuid: $old_parent_uuid})
        MATCH (deriv:Image)-[:DERIVATIVE_OF]->(old_parent)
        WHERE deriv.uuid <> $new_parent_uuid
        
        DELETE (new_parent)-[:DERIVATIVE_OF]->(old_parent)
        CREATE (old_parent)-[:DERIVATIVE_OF]->(new_parent)
        FOREACH (d IN deriv | 
            DELETE (d)-[:DERIVATIVE_OF]->(old_parent)
            CREATE (d)-[:DERIVATIVE_OF]->(new_parent)
        )
        """
        self.neo4j.execute_write(
            query,
            parameters={
                "new_parent_uuid": str(image_uuid),
                "old_parent_uuid": str(old_parent_uuid),
            }
        )

    def add_as_derivative(self, image_uuid: UUID, parent_uuid: UUID) -> None:
        """
        Add an image as derivative of another.

        Args:
            image_uuid: Derivative image UUID
            parent_uuid: Parent image UUID
        """
        query = """
        MATCH (img:Image {uuid: $uuid})
        MATCH (parent:Image {uuid: $parent_uuid})
        MERGE (img)-[:DERIVATIVE_OF]->(parent)
        """
        self.neo4j.execute_write(
            query,
            parameters={
                "uuid": str(image_uuid),
                "parent_uuid": str(parent_uuid),
            }
        )

    def update_image_quality(self, image_uuid: UUID, quality_score: int) -> None:
        """
        Update image quality score.

        Args:
            image_uuid: Image UUID
            quality_score: New quality score
        """
        query = """
        MATCH (img:Image {uuid: $uuid})
        SET img.quality_score = $quality_score,
            img.updated_at = datetime()
        """
        self.neo4j.execute_write(
            query,
            parameters={
                "uuid": str(image_uuid),
                "quality_score": quality_score,
            }
        )

    def mark_url_crawled(self, url: str, image_uuid: Optional[UUID] = None) -> None:
        """
        Mark a URL as crawled.

        Args:
            url: Normalized URL
            image_uuid: Optional associated image UUID
        """
        query = """
        MERGE (url:CrawlUrl {url: $url})
        SET url.last_crawled_at = datetime(),
            url.updated_at = datetime()
        """
        params = {"url": url}

        if image_uuid:
            query += """
            WITH url
            MATCH (img:Image {uuid: $uuid})
            MERGE (url)-[:LINKS_TO]->(img)
            """
            params["uuid"] = str(image_uuid)

        self.neo4j.execute_write(query, parameters=params)

    def get_crawl_url(self, url: str) -> Optional[Dict]:
        """
        Get crawl URL record.

        Args:
            url: Normalized URL

        Returns:
            CrawlUrl record or None
        """
        query = """
        MATCH (url:CrawlUrl {url: $url})
        RETURN url
        LIMIT 1
        """
        result = self.neo4j.execute_read(
            query,
            parameters={"url": url}
        )

        if result:
            return dict(result[0]["url"])
        return None








