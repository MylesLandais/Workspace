"""Service interface for managing YouTube channel subscriptions."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from datetime import datetime, timedelta
from typing import Optional, List, Dict
from uuid import UUID, uuid4
import json

from feed.storage.neo4j_connection import get_connection
from feed.storage.valkey_connection import get_valkey_connection
from feed.models.creator import Creator
from feed.models.handle import Handle
from feed.models.platform import Platform
from feed.ontology.schema import HandleStatus, VerificationConfidence


class YouTubeSubscriptionService:
    """Service for managing YouTube channel subscriptions."""

    def __init__(self):
        self.neo4j = get_connection()
        self.valkey = get_valkey_connection()
        self.redis = self.valkey.client

    def create_creator(
        self,
        name: str,
        slug: str,
        bio: Optional[str] = None,
        avatar_url: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create a new creator entity.

        Args:
            name: Creator name
            slug: URL-friendly slug
            bio: Optional bio
            avatar_url: Optional avatar URL

        Returns:
            Creator data or None
        """
        query = """
        MERGE (c:Creator {slug: $slug})
        ON CREATE SET c.created_at = datetime(),
                      c.name = $name,
                      c.bio = $bio,
                      c.avatar_url = $avatar_url,
                      c.uuid = $uuid,
                      c.updated_at = datetime()
        ON MATCH SET c.name = COALESCE(c.name, $name),
                     c.bio = COALESCE(c.bio, $bio),
                     c.avatar_url = COALESCE(c.avatar_url, $avatar_url),
                     c.updated_at = datetime()
        RETURN c
        """

        try:
            result = self.neo4j.execute_write(
                query,
                parameters={
                    "name": name,
                    "slug": slug,
                    "bio": bio,
                    "avatar_url": avatar_url,
                    "uuid": str(uuid4())
                }
            )
            if result:
                creator_node = result[0]['c']
                return {
                    "uuid": creator_node.get('uuid'),
                    "name": creator_node.get('name'),
                    "slug": creator_node.get('slug'),
                    "bio": creator_node.get('bio'),
                    "avatar_url": creator_node.get('avatar_url')
                }
        except Exception as e:
            print(f"Error creating creator: {e}")

        return None

    def add_youtube_handle(
        self,
        creator_slug: str,
        handle: str,
        display_name: str,
        profile_url: str,
        follower_count: Optional[int] = None,
        verified: bool = False
    ) -> bool:
        """
        Add YouTube handle to creator.

        Args:
            creator_slug: Creator slug
            handle: YouTube handle (@username)
            display_name: Display name
            profile_url: Full profile URL
            follower_count: Optional follower count
            verified: Whether verified by platform

        Returns:
            True if successful
        """
        query = """
        MATCH (c:Creator {slug: $creator_slug})
        MATCH (p:Platform {slug: 'youtube'})
        MERGE (c)-[r:OWNS_HANDLE]->(h:Handle {profile_url: $profile_url})
        ON CREATE SET h.created_at = datetime(),
                      h.username = $handle,
                      h.display_name = $display_name,
                      h.follower_count = $follower_count,
                      h.verified_by_platform = $verified,
                      h.uuid = $uuid,
                      h.updated_at = datetime(),
                      r.created_at = datetime(),
                      r.discovered_at = datetime()
        ON MATCH SET h.username = $handle,
                     h.display_name = $display_name,
                     h.follower_count = $follower_count,
                     h.verified_by_platform = $verified,
                     h.updated_at = datetime()
        SET r.status = $status,
            r.verified = $verified,
            r.confidence = $confidence,
            r.updated_at = datetime()
        MERGE (h)-[:ON_PLATFORM]->(p)
        RETURN h, r
        """

        try:
            self.neo4j.execute_write(
                query,
                parameters={
                    "creator_slug": creator_slug,
                    "handle": handle,
                    "display_name": display_name,
                    "profile_url": profile_url,
                    "follower_count": follower_count,
                    "verified": verified,
                    "uuid": str(uuid4()),
                    "status": HandleStatus.ACTIVE.value,
                    "confidence": VerificationConfidence.HIGH.value
                }
            )
            return True
        except Exception as e:
            print(f"Error adding YouTube handle: {e}")

        return False

    def create_subscription(
        self,
        creator_slug: str,
        poll_interval_hours: int = 1
    ) -> bool:
        """
        Create YouTube subscription for creator.

        Args:
            creator_slug: Creator slug
            poll_interval_hours: Polling interval in hours

        Returns:
            True if successful
        """
        query = """
        MATCH (c:Creator {slug: $creator_slug})
        MATCH (p:Platform {slug: 'youtube'})
        MERGE (c)-[sub:SUBSCRIBED_TO]->(p)
        ON CREATE SET sub.created_at = datetime()
        SET sub.status = 'active',
            sub.poll_interval_hours = $poll_interval_hours,
            sub.last_polled_at = datetime(),
            sub.last_successful_poll = datetime(),
            sub.poll_count_24h = 0,
            sub.error_count_24h = 0,
            sub.updated_at = datetime()
        RETURN sub
        """

        try:
            self.neo4j.execute_write(
                query,
                parameters={
                    "creator_slug": creator_slug,
                    "poll_interval_hours": poll_interval_hours
                }
            )
            return True
        except Exception as e:
            print(f"Error creating subscription: {e}")

        return False

    def get_creator_by_slug(
        self,
        slug: str,
        use_cache: bool = True
    ) -> Optional[Dict]:
        """
        Get creator by slug (with Redis caching).

        Args:
            slug: Creator slug
            use_cache: Whether to use cache

        Returns:
            Creator data or None
        """
        cache_key = f"creator:{slug}"

        # Try cache first
        if use_cache:
            cached = self.redis.get(cache_key)
            if cached:
                return json.loads(cached)

        # Fallback to graph
        query = """
        MATCH (c:Creator {slug: $slug})
        OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform)
        RETURN 
            c.uuid as uuid,
            c.name as name,
            c.slug as slug,
            c.bio as bio,
            c.avatar_url as avatar_url,
            collect({handle: h.username, platform: p.slug}) as handles
        """

        try:
            result = self.neo4j.execute_read(
                query,
                parameters={"slug": slug}
            )
            if result:
                record = result[0]
                creator_data = {
                    "uuid": record.get('uuid'),
                    "name": record.get('name'),
                    "slug": record.get('slug'),
                    "bio": record.get('bio'),
                    "avatar_url": record.get('avatar_url'),
                    "handles": record.get('handles', [])
                }

                # Update cache
                if use_cache:
                    self.redis.setex(cache_key, 3600, json.dumps(creator_data))

                return creator_data
        except Exception as e:
            print(f"Error getting creator: {e}")

        return None

    def invalidate_creator_cache(self, slug: str) -> bool:
        """
        Invalidate cache for creator.

        Args:
            slug: Creator slug

        Returns:
            True if cache was deleted
        """
        cache_key = f"creator:{slug}"
        try:
            deleted = self.redis.delete(cache_key)
            return deleted > 0
        except Exception as e:
            print(f"Error invalidating cache: {e}")
            return False

    def list_all_subscriptions(self) -> List[Dict]:
        """
        List all YouTube channel subscriptions.

        Returns:
            List of subscription data
        """
        query = """
        MATCH (c:Creator)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
        WHERE r.status = 'Active' AND r.verified = true
        OPTIONAL MATCH (c)-[sub:SUBSCRIBED_TO]->(p)
        RETURN 
            c.slug as creator_slug,
            c.name as creator_name,
            h.username as handle_username,
            h.profile_url as profile_url,
            h.follower_count as followers,
            sub.status as subscription_status,
            sub.poll_interval_hours as poll_interval_hours,
            sub.last_polled_at as last_polled_at
        ORDER BY c.name
        """

        try:
            result = self.neo4j.execute_read(query)
            return [
                {
                    "creator_slug": record.get('creator_slug'),
                    "creator_name": record.get('creator_name'),
                    "handle_username": record.get('handle_username'),
                    "profile_url": record.get('profile_url'),
                    "followers": record.get('followers'),
                    "subscription_status": record.get('subscription_status'),
                    "poll_interval_hours": record.get('poll_interval_hours'),
                    "last_polled_at": record.get('last_polled_at')
                }
                for record in result
            ]
        except Exception as e:
            print(f"Error listing subscriptions: {e}")
            return []

    def get_subscription_health(self) -> List[Dict]:
        """
        Get health status for all subscriptions.

        Returns:
            List of health status data
        """
        query = """
        MATCH (c:Creator)-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
        OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
        WITH c, sub, h
        RETURN 
            c.slug as creator_slug,
            c.name as creator_name,
            h.username as youtube_handle,
            CASE 
                WHEN sub.last_successful_poll > datetime() - duration('PT6H') 
                THEN 'healthy'
                WHEN sub.last_successful_poll > datetime() - duration('PT24H')
                THEN 'warning'
                ELSE 'unhealthy'
            END as status,
            sub.last_successful_poll as last_successful_poll,
            sub.last_polled_at as last_polled_at,
            sub.poll_interval_hours as poll_interval_hours,
            sub.poll_count_24h as poll_count_24h,
            sub.error_count_24h as error_count_24h
        ORDER BY c.name
        """

        try:
            result = self.neo4j.execute_read(query)
            return [
                {
                    "creator_slug": record.get('creator_slug'),
                    "creator_name": record.get('creator_name'),
                    "youtube_handle": record.get('youtube_handle'),
                    "status": record.get('status'),
                    "last_successful_poll": record.get('last_successful_poll'),
                    "last_polled_at": record.get('last_polled_at'),
                    "poll_interval_hours": record.get('poll_interval_hours'),
                    "poll_count_24h": record.get('poll_count_24h'),
                    "error_count_24h": record.get('error_count_24h')
                }
                for record in result
            ]
        except Exception as e:
            print(f"Error getting subscription health: {e}")
            return []

    def update_subscription_status(
        self,
        creator_slug: str,
        last_successful_poll: Optional[datetime] = None,
        increment_poll_count: bool = False,
        increment_error_count: bool = False
    ) -> bool:
        """
        Update subscription polling status.

        Args:
            creator_slug: Creator slug
            last_successful_poll: Last successful poll timestamp
            increment_poll_count: Increment 24h poll count
            increment_error_count: Increment 24h error count

        Returns:
            True if successful
        """
        query = """
        MATCH (c:Creator {slug: $slug})-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
        SET sub.last_polled_at = datetime(),
            sub.updated_at = datetime()
        """

        params = {"slug": creator_slug}

        if last_successful_poll:
            query += ", sub.last_successful_poll = $last_successful_poll"
            params["last_successful_poll"] = last_successful_poll

        if increment_poll_count:
            query += ", sub.poll_count_24h = COALESCE(sub.poll_count_24h, 0) + 1"

        if increment_error_count:
            query += ", sub.error_count_24h = COALESCE(sub.error_count_24h, 0) + 1"

        try:
            self.neo4j.execute_write(query, parameters=params)
            return True
        except Exception as e:
            print(f"Error updating subscription status: {e}")
            return False

    def search_creators(
        self,
        search_term: str,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search creators by name.

        Args:
            search_term: Search term
            limit: Max results

        Returns:
            List of creators
        """
        query = """
        MATCH (c:Creator)
        WHERE toLower(c.name) CONTAINS toLower($search_term)
        RETURN c.uuid as uuid, c.name as name, c.slug as slug
        ORDER BY c.name
        LIMIT $limit
        """

        try:
            result = self.neo4j.execute_read(
                query,
                parameters={"search_term": search_term, "limit": limit}
            )
            return [
                {
                    "uuid": record.get('uuid'),
                    "name": record.get('name'),
                    "slug": record.get('slug')
                }
                for record in result
            ]
        except Exception as e:
            print(f"Error searching creators: {e}")
            return []

    def health_check_redis(self) -> Dict:
        """
        Check Redis health.

        Returns:
            Health status dict
        """
        try:
            ping = self.redis.ping()
            info = self.redis.info()
            db_size = self.redis.dbsize()

            return {
                "status": "healthy" if ping else "unhealthy",
                "ping": ping,
                "version": info.get('redis_version'),
                "connected_clients": info.get('connected_clients'),
                "used_memory": info.get('used_memory_human'),
                "database_size": db_size
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def health_check_neo4j(self) -> Dict:
        """
        Check Neo4j health.

        Returns:
            Health status dict
        """
        try:
            result = self.neo4j.execute_read("RETURN 'ok' as status")
            
            labels_result = self.neo4j.execute_read(
                "CALL db.labels() YIELD label RETURN count(label) as count"
            )
            labels_count = labels_result[0]['count'] if labels_result else 0
            
            relationships_result = self.neo4j.execute_read(
                "CALL db.relationshipTypes() YIELD relationshipType RETURN count(relationshipType) as count"
            )
            relationships_count = relationships_result[0]['count'] if relationships_result else 0

            nodes_result = self.neo4j.execute_read("MATCH (n) RETURN count(n) as count")
            nodes_count = nodes_result[0]['count'] if nodes_result else 0

            return {
                "status": "healthy",
                "node_labels": labels_count,
                "relationship_types": relationships_count,
                "total_nodes": nodes_count
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }

    def get_overall_health(self) -> Dict:
        """
        Get overall system health.

        Returns:
            Health status dict
        """
        redis_health = self.health_check_redis()
        neo4j_health = self.health_check_neo4j()
        subscription_health = self.get_subscription_health()

        return {
            "redis": redis_health,
            "neo4j": neo4j_health,
            "subscriptions": subscription_health,
            "overall_status": "healthy" if (
                redis_health.get('status') == 'healthy' and 
                neo4j_health.get('status') == 'healthy'
            ) else "degraded"
        }
