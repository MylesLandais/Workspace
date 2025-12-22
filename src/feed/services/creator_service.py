"""Service for managing Creator entities and relationships."""

from typing import Optional, List, Dict
from datetime import datetime
from uuid import UUID, uuid4
import re

from ..models.creator import Creator
from ..models.handle import Handle
from ..models.platform import Platform
from ..ontology.schema import HandleStatus, VerificationConfidence
from ..storage.neo4j_connection import get_connection
from .bio_crawler import BioCrawler, CandidateHandle
from .verification import VerificationService


class CreatorService:
    """Service for managing creators, handles, and their relationships."""

    def __init__(self):
        self.bio_crawler = BioCrawler()
        self.verification_service = VerificationService()

    def create_creator(
        self,
        name: str,
        slug: Optional[str] = None,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional[Creator]:
        """
        Create a new creator.

        Args:
            name: Creator name
            slug: Optional slug (auto-generated if not provided)
            bio: Optional bio
            avatar_url: Optional avatar URL

        Returns:
            Creator object or None if creation failed
        """
        if not slug:
            slug = self._generate_slug(name)

        # Ensure slug is unique
        slug = self._ensure_unique_slug(slug)

        creator = Creator(
            uuid=uuid4(),
            name=name,
            slug=slug,
            bio=bio,
            avatar_url=avatar_url,
        )

        neo4j = get_connection()

        query = """
        CREATE (c:Creator)
        SET c = $props
        RETURN c.uuid as uuid,
               c.name as name,
               c.slug as slug,
               c.bio as bio,
               c.avatar_url as avatar_url,
               c.created_at as created_at,
               c.updated_at as updated_at
        """

        try:
            result = neo4j.execute_write(
                query,
                parameters={"props": creator.to_neo4j_dict()},
            )
            if result:
                record = result[0]
                return Creator(
                    uuid=UUID(record["uuid"]),
                    name=record["name"],
                    slug=record["slug"],
                    bio=record.get("bio"),
                    avatar_url=record.get("avatar_url"),
                    created_at=record.get("created_at"),
                    updated_at=record.get("updated_at"),
                )
        except Exception as e:
            print(f"Error creating creator: {e}")
            return None

        return None

    def add_handle_to_creator(
        self,
        creator_uuid: UUID,
        handle: Handle,
        platform: Platform,
        confidence: VerificationConfidence = VerificationConfidence.MEDIUM,
        status: HandleStatus = HandleStatus.UNVERIFIED,
    ) -> bool:
        """
        Add a handle to a creator.

        Args:
            creator_uuid: Creator UUID
            handle: Handle object
            platform: Platform object
            confidence: Verification confidence
            status: Handle status

        Returns:
            True if successful
        """
        neo4j = get_connection()

        # Ensure platform exists
        self._ensure_platform_exists(platform)

        # Create handle if it doesn't exist
        handle_query = """
        MERGE (h:Handle {uuid: $handle_uuid})
        SET h = $handle_props
        RETURN h
        """
        neo4j.execute_write(
            handle_query,
            parameters={
                "handle_uuid": str(handle.uuid),
                "handle_props": handle.to_neo4j_dict(),
            },
        )

        # Create relationship
        rel_query = """
        MATCH (c:Creator {uuid: $creator_uuid})
        MATCH (h:Handle {uuid: $handle_uuid})
        MATCH (p:Platform {slug: $platform_slug})
        MERGE (c)-[r:OWNS_HANDLE]->(h)
        SET r = $rel_props
        MERGE (h)-[:ON_PLATFORM]->(p)
        RETURN r
        """

        rel_props = {
            "status": status.value,
            "verified": False,
            "confidence": confidence.value,
            "discovered_at": datetime.utcnow(),
            "verified_at": None,
            "created_at": datetime.utcnow(),
        }

        try:
            result = neo4j.execute_write(
                rel_query,
                parameters={
                    "creator_uuid": str(creator_uuid),
                    "handle_uuid": str(handle.uuid),
                    "platform_slug": platform.slug,
                    "rel_props": rel_props,
                },
            )
            return len(result) > 0
        except Exception as e:
            print(f"Error adding handle to creator: {e}")
            return False

    def discover_handles_from_url(
        self, creator_uuid: UUID, anchor_url: str
    ) -> List[CandidateHandle]:
        """
        Discover handles from an anchor URL using bio-crawler.

        Args:
            creator_uuid: Creator UUID
            anchor_url: URL to scan (e.g., YouTube About page)

        Returns:
            List of CandidateHandle objects
        """
        candidates = self.bio_crawler.discover_handles(anchor_url)

        # Optionally infer confidence from username matching
        for candidate in candidates:
            inferred = self.verification_service.infer_confidence_from_username_match(
                candidate.username, candidate.platform, creator_uuid
            )
            if inferred:
                candidate.confidence = inferred

        return candidates

    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[-\s]+", "-", slug)
        return slug.strip("-")

    def _ensure_unique_slug(self, slug: str) -> str:
        """Ensure slug is unique by appending suffix if needed."""
        neo4j = get_connection()

        query = """
        MATCH (c:Creator {slug: $slug})
        RETURN c.slug as slug
        LIMIT 1
        """

        result = neo4j.execute_read(query, parameters={"slug": slug})
        if not result:
            return slug

        # Slug exists, try variations
        counter = 1
        while True:
            new_slug = f"{slug}-{counter}"
            result = neo4j.execute_read(query, parameters={"slug": new_slug})
            if not result:
                return new_slug
            counter += 1

    def _ensure_platform_exists(self, platform: Platform) -> None:
        """Ensure platform node exists in graph."""
        neo4j = get_connection()

        query = """
        MERGE (p:Platform {slug: $slug})
        SET p.name = $name,
            p.slug = $slug,
            p.api_base_url = $api_base_url,
            p.icon_url = $icon_url,
            p.created_at = coalesce(p.created_at, datetime())
        RETURN p
        """

        neo4j.execute_write(
            query,
            parameters={
                "name": platform.name,
                "slug": platform.slug,
                "api_base_url": platform.api_base_url,
                "icon_url": platform.icon_url,
            },
        )

