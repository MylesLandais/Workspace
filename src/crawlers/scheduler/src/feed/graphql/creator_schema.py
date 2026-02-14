"""Extended GraphQL schema for Creator/Handle/Media system."""

from typing import List, Optional
from datetime import datetime
import strawberry
from uuid import UUID

from ..storage.neo4j_connection import get_connection
from ..models.creator import Creator, CreatorWithHandles
from ..models.handle import Handle
from ..models.media import Media, VideoMedia, ImageMedia, TextMedia
from ..ontology.schema import HandleStatus, VerificationConfidence, MediaType as MediaTypeEnum


@strawberry.type
class Platform:
    """Platform type."""
    name: str
    slug: str
    icon_url: Optional[str] = None


@strawberry.type
class HandleType:
    """Handle type for GraphQL."""
    uuid: str
    username: str
    display_name: Optional[str] = None
    profile_url: str
    follower_count: Optional[int] = None
    verified_by_platform: bool = False
    platform: Optional[Platform] = None
    status: Optional[str] = None
    verified: Optional[bool] = None
    confidence: Optional[str] = None

    @classmethod
    def from_neo4j_record(cls, record: dict) -> "HandleType":
        """Create from Neo4j record."""
        return cls(
            uuid=record.get("uuid", ""),
            username=record.get("username", ""),
            display_name=record.get("display_name"),
            profile_url=record.get("profile_url", ""),
            follower_count=record.get("follower_count"),
            verified_by_platform=record.get("verified_by_platform", False),
            platform=Platform(
                name=record.get("platform_name", ""),
                slug=record.get("platform_slug", ""),
                icon_url=record.get("platform_icon_url"),
            ) if record.get("platform_name") else None,
            status=record.get("status"),
            verified=record.get("verified"),
            confidence=record.get("confidence"),
        )


@strawberry.type
class CreatorType:
    """Creator type for GraphQL."""
    uuid: str
    name: str
    slug: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    handles: List[HandleType] = strawberry.field(default_factory=list)

    @classmethod
    def from_neo4j_record(cls, record: dict) -> "CreatorType":
        """Create from Neo4j record."""
        return cls(
            uuid=record.get("uuid", ""),
            name=record.get("name", ""),
            slug=record.get("slug", ""),
            bio=record.get("bio"),
            avatar_url=record.get("avatar_url"),
            handles=[],
        )


@strawberry.type
class Media:
    """Media type for GraphQL (normalized)."""
    uuid: str
    title: Optional[str] = None
    source_url: str
    publish_date: str
    thumbnail_url: Optional[str] = None
    media_type: str
    platform_name: Optional[str] = None
    platform_slug: Optional[str] = None
    platform_icon_url: Optional[str] = None

    # Video-specific fields
    duration: Optional[int] = None
    view_count: Optional[int] = None
    aspect_ratio: Optional[str] = None
    resolution: Optional[str] = None

    # Image-specific fields
    width: Optional[int] = None
    height: Optional[int] = None

    # Text-specific fields
    body_content: Optional[str] = None
    word_count: Optional[int] = None

    @classmethod
    def from_neo4j_record(cls, record: dict) -> "Media":
        """Create from Neo4j record."""
        publish_date = record.get("publish_date")
        if isinstance(publish_date, datetime):
            publish_date_str = publish_date.isoformat()
        elif isinstance(publish_date, str):
            publish_date_str = publish_date
        else:
            publish_date_str = datetime.utcnow().isoformat()

        return cls(
            uuid=record.get("uuid", ""),
            title=record.get("title"),
            source_url=record.get("source_url", ""),
            publish_date=publish_date_str,
            thumbnail_url=record.get("thumbnail_url"),
            media_type=record.get("media_type", "Text"),
            platform_name=record.get("platform_name"),
            platform_slug=record.get("platform_slug"),
            platform_icon_url=record.get("platform_icon_url"),
            duration=record.get("duration"),
            view_count=record.get("view_count"),
            aspect_ratio=record.get("aspect_ratio"),
            resolution=record.get("resolution"),
            width=record.get("width"),
            height=record.get("height"),
            body_content=record.get("body_content"),
            word_count=record.get("word_count"),
        )


@strawberry.type
class CandidateHandle:
    """Candidate handle discovered by bio-crawler."""
    username: str
    platform: str
    profile_url: str
    confidence: str
    source_url: str
    context: Optional[str] = None


@strawberry.input
class FeedFilter:
    """Filter for omni-feed query."""
    exclude_platforms: Optional[List[str]] = None
    media_types: Optional[List[str]] = None
    limit: int = 20
    offset: int = 0


@strawberry.type
class CreatorQuery:
    """Creator-related queries."""

    @strawberry.field
    def creator(self, slug: str) -> Optional[CreatorType]:
        """Get creator by slug with all handles."""
        try:
            neo4j = get_connection()

            query = """
            MATCH (c:Creator {slug: $slug})
            OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
            OPTIONAL MATCH (h)-[:ON_PLATFORM]->(p:Platform)
            RETURN c.uuid as uuid,
                   c.name as name,
                   c.slug as slug,
                   c.bio as bio,
                   c.avatar_url as avatar_url,
                   collect({
                       handle_uuid: h.uuid,
                       username: h.username,
                       display_name: h.display_name,
                       profile_url: h.profile_url,
                       follower_count: h.follower_count,
                       verified_by_platform: h.verified_by_platform,
                       platform_name: p.name,
                       platform_slug: p.slug,
                       platform_icon_url: p.icon_url,
                       status: r.status,
                       verified: r.verified,
                       confidence: r.confidence
                   }) as handles
            """

            result = neo4j.execute_read(query, parameters={"slug": slug})
            if not result:
                return None

            record = result[0]
            creator = CreatorType(
                uuid=record.get("uuid", ""),
                name=record.get("name", ""),
                slug=record.get("slug", ""),
                bio=record.get("bio"),
                avatar_url=record.get("avatar_url"),
                handles=[
                    HandleType.from_neo4j_record(h) for h in record.get("handles", []) if h.get("handle_uuid")
                ],
            )

            return creator
        except Exception as e:
            print(f"Error getting creator: {e}")
            return None

    @strawberry.field
    def creators(self, limit: int = 20, offset: int = 0) -> List[CreatorType]:
        """Get list of creators."""
        try:
            neo4j = get_connection()

            query = """
            MATCH (c:Creator)
            RETURN c.uuid as uuid,
                   c.name as name,
                   c.slug as slug,
                   c.bio as bio,
                   c.avatar_url as avatar_url
            ORDER BY c.created_at DESC
            SKIP $offset
            LIMIT $limit
            """

            result = neo4j.execute_read(
                query, parameters={"offset": offset, "limit": limit}
            )

            return [
                CreatorType.from_neo4j_record(dict(record)) for record in result
            ]
        except Exception as e:
            print(f"Error getting creators: {e}")
            return []


@strawberry.type
class FeedQuery:
    """Omni-feed aggregation queries."""

    @strawberry.field
    def feed(
        self,
        creator_id: str,
        filter: Optional[FeedFilter] = None,
    ) -> List[Media]:
        """
        Get aggregated omni-feed for a creator across all verified handles.

        Args:
            creator_id: Creator UUID or slug
            filter: Optional filter for platforms and media types
        """
        try:
            neo4j = get_connection()

            filter_obj = filter or FeedFilter()

            # Build WHERE clause for platform exclusion
            where_clauses = [
                "r.verified = true",
                "r.status = 'Active'",
                "m.publish_date IS NOT NULL",
            ]

            params = {
                "creator_id": creator_id,
                "limit": filter_obj.limit,
                "offset": filter_obj.offset,
            }

            if filter_obj.exclude_platforms:
                where_clauses.append("NOT p.slug IN $exclude_platforms")
                params["exclude_platforms"] = filter_obj.exclude_platforms

            if filter_obj.media_types:
                where_clauses.append("m.media_type IN $media_types")
                params["media_types"] = filter_obj.media_types

            where_clause = " AND ".join(where_clauses)

            # Try UUID first, then slug
            query = f"""
            MATCH (c:Creator)
            WHERE c.uuid = $creator_id OR c.slug = $creator_id
            MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
            MATCH (h)-[:ON_PLATFORM]->(p:Platform)
            MATCH (h)-[:PUBLISHED]->(m:Media)
            MATCH (m)-[:SOURCED_FROM]->(p)
            WHERE {where_clause}
            RETURN m.uuid as uuid,
                   m.title as title,
                   m.source_url as source_url,
                   m.publish_date as publish_date,
                   m.thumbnail_url as thumbnail_url,
                   m.media_type as media_type,
                   p.name as platform_name,
                   p.slug as platform_slug,
                   p.icon_url as platform_icon_url,
                   m.duration as duration,
                   m.view_count as view_count,
                   m.aspect_ratio as aspect_ratio,
                   m.resolution as resolution,
                   m.width as width,
                   m.height as height,
                   m.body_content as body_content,
                   m.word_count as word_count
            ORDER BY m.publish_date DESC
            SKIP $offset
            LIMIT $limit
            """

            result = neo4j.execute_read(query, parameters=params)

            return [Media.from_neo4j_record(dict(record)) for record in result]
        except Exception as e:
            print(f"Error getting feed: {e}")
            return []

