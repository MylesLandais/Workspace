"""Verification and confidence system for handles."""

from typing import Optional, List
from datetime import datetime
from uuid import UUID

from ..ontology.schema import HandleStatus, VerificationConfidence
from ..models.handle import Handle
from ..storage.neo4j_connection import get_connection


class VerificationService:
    """Service for managing handle verification and confidence."""

    def verify_handle(
        self,
        creator_uuid: UUID,
        handle_uuid: UUID,
        confidence: VerificationConfidence = VerificationConfidence.MANUAL,
    ) -> bool:
        """
        Verify a handle (mark as verified).

        Args:
            creator_uuid: Creator UUID
            handle_uuid: Handle UUID
            confidence: Confidence level (default: Manual for admin confirmation)

        Returns:
            True if successful
        """
        neo4j = get_connection()

        query = """
        MATCH (c:Creator {uuid: $creator_uuid})-[r:OWNS_HANDLE]->(h:Handle {uuid: $handle_uuid})
        SET r.verified = true,
            r.confidence = $confidence,
            r.verified_at = datetime(),
            r.status = 'Active'
        RETURN r
        """

        try:
            result = neo4j.execute_write(
                query,
                parameters={
                    "creator_uuid": str(creator_uuid),
                    "handle_uuid": str(handle_uuid),
                    "confidence": confidence.value,
                },
            )
            return len(result) > 0
        except Exception as e:
            print(f"Error verifying handle: {e}")
            return False

    def unverify_handle(self, creator_uuid: UUID, handle_uuid: UUID) -> bool:
        """
        Unverify a handle (mark as unverified).

        Args:
            creator_uuid: Creator UUID
            handle_uuid: Handle UUID

        Returns:
            True if successful
        """
        neo4j = get_connection()

        query = """
        MATCH (c:Creator {uuid: $creator_uuid})-[r:OWNS_HANDLE]->(h:Handle {uuid: $handle_uuid})
        SET r.verified = false,
            r.status = 'Unverified'
        RETURN r
        """

        try:
            result = neo4j.execute_write(
                query,
                parameters={
                    "creator_uuid": str(creator_uuid),
                    "handle_uuid": str(handle_uuid),
                },
            )
            return len(result) > 0
        except Exception as e:
            print(f"Error unverifying handle: {e}")
            return False

    def update_handle_status(
        self,
        creator_uuid: UUID,
        handle_uuid: UUID,
        status: HandleStatus,
    ) -> bool:
        """
        Update handle status (Active, Suspended, Abandoned).

        Args:
            creator_uuid: Creator UUID
            handle_uuid: Handle UUID
            status: New status

        Returns:
            True if successful
        """
        neo4j = get_connection()

        query = """
        MATCH (c:Creator {uuid: $creator_uuid})-[r:OWNS_HANDLE]->(h:Handle {uuid: $handle_uuid})
        SET r.status = $status
        RETURN r
        """

        try:
            result = neo4j.execute_write(
                query,
                parameters={
                    "creator_uuid": str(creator_uuid),
                    "handle_uuid": str(handle_uuid),
                    "status": status.value,
                },
            )
            return len(result) > 0
        except Exception as e:
            print(f"Error updating handle status: {e}")
            return False

    def get_unverified_handles(self, creator_uuid: Optional[UUID] = None) -> List[dict]:
        """
        Get all unverified handles, optionally filtered by creator.

        Args:
            creator_uuid: Optional creator UUID to filter by

        Returns:
            List of handle dictionaries with creator info
        """
        neo4j = get_connection()

        if creator_uuid:
            query = """
            MATCH (c:Creator {uuid: $creator_uuid})-[r:OWNS_HANDLE {verified: false}]->(h:Handle)
            OPTIONAL MATCH (h)-[:ON_PLATFORM]->(p:Platform)
            RETURN c.uuid as creator_uuid,
                   c.name as creator_name,
                   c.slug as creator_slug,
                   h.uuid as handle_uuid,
                   h.username as username,
                   h.profile_url as profile_url,
                   p.name as platform_name,
                   r.confidence as confidence,
                   r.discovered_at as discovered_at
            ORDER BY r.discovered_at DESC
            """
            params = {"creator_uuid": str(creator_uuid)}
        else:
            query = """
            MATCH (c:Creator)-[r:OWNS_HANDLE {verified: false}]->(h:Handle)
            OPTIONAL MATCH (h)-[:ON_PLATFORM]->(p:Platform)
            RETURN c.uuid as creator_uuid,
                   c.name as creator_name,
                   c.slug as creator_slug,
                   h.uuid as handle_uuid,
                   h.username as username,
                   h.profile_url as profile_url,
                   p.name as platform_name,
                   r.confidence as confidence,
                   r.discovered_at as discovered_at
            ORDER BY r.discovered_at DESC
            """
            params = {}

        try:
            result = neo4j.execute_read(query, parameters=params)
            return [dict(record) for record in result]
        except Exception as e:
            print(f"Error getting unverified handles: {e}")
            return []

    def infer_confidence_from_username_match(
        self, username: str, platform: str, creator_uuid: UUID
    ) -> Optional[VerificationConfidence]:
        """
        Infer confidence by checking if username matches across verified handles.

        Args:
            username: Username to check
            platform: Platform name
            creator_uuid: Creator UUID

        Returns:
            VerificationConfidence if match found, None otherwise
        """
        neo4j = get_connection()

        # Normalize username (remove @, lowercase)
        normalized_username = username.lower().lstrip("@")

        query = """
        MATCH (c:Creator {uuid: $creator_uuid})-[r:OWNS_HANDLE {verified: true}]->(h:Handle)
        OPTIONAL MATCH (h)-[:ON_PLATFORM]->(p:Platform)
        WHERE toLower(h.username) = $normalized_username
           OR toLower(replace(h.username, '@', '')) = $normalized_username
        RETURN h.username as existing_username, p.name as platform_name
        LIMIT 5
        """

        try:
            result = neo4j.execute_read(
                query,
                parameters={
                    "creator_uuid": str(creator_uuid),
                    "normalized_username": normalized_username,
                },
            )
            if result:
                # Found matching username across platforms
                return VerificationConfidence.MEDIUM
        except Exception as e:
            print(f"Error inferring confidence: {e}")

        return None








