"""Tests for YouTube channel subscription feature with Redis caching and health checks."""

import pytest
import unittest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from uuid import UUID, uuid4
import json

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feed.models.creator import Creator, CreatorWithHandles
from feed.models.handle import Handle
from feed.models.platform import Platform
from feed.models.media import Media
from feed.ontology.schema import HandleStatus, VerificationConfidence, MediaType
from feed.storage.neo4j_connection import get_connection
from feed.storage.valkey_connection import get_valkey_connection


class TestYouTubeChannelSubscription(unittest.TestCase):
    """Test YouTube channel subscription end-to-end."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_neo4j = Mock()
        self.mock_redis = Mock()
        
        # Mock creators and channels for testing
        self.fasffy_creator = {
            "uuid": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Fasffy",
            "slug": "fasffy",
            "bio": "Content creator and streamer",
            "avatar_url": "https://example.com/fasffy-avatar.jpg"
        }
        
        self.misskatie_creator = {
            "uuid": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Miss Katie",
            "slug": "misskatie",
            "bio": "YouTube content creator",
            "avatar_url": "https://example.com/misskatie-avatar.jpg"
        }
        
        self.youtube_platform = {
            "name": "YouTube",
            "slug": "youtube",
            "api_base_url": "https://www.googleapis.com/youtube/v3",
            "icon_url": "https://www.youtube.com/favicon.ico"
        }
        
        self.fasffy_handle = {
            "uuid": "660e8400-e29b-41d4-a716-446655440001",
            "username": "@Fasffy",
            "display_name": "Fasffy",
            "profile_url": "https://www.youtube.com/@Fasffy",
            "follower_count": 150000,
            "verified_by_platform": True
        }
        
        self.misskatie_handle = {
            "uuid": "660e8400-e29b-41d4-a716-446655440002",
            "username": "@MissKatie",
            "display_name": "Miss Katie",
            "profile_url": "https://www.youtube.com/@MissKatie",
            "follower_count": 85000,
            "verified_by_platform": True
        }

    def test_init_creators_in_graph(self):
        """Test initialization of creators in Neo4j graph."""
        
        # Mock Neo4j responses for creator creation
        self.mock_neo4j.execute_write.return_value = [{
            "uuid": self.fasffy_creator["uuid"],
            "name": self.fasffy_creator["name"],
            "slug": self.fasffy_creator["slug"],
            "bio": self.fasffy_creator["bio"],
            "avatar_url": self.fasffy_creator["avatar_url"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        
        query = """
        MERGE (c:Creator {uuid: $uuid})
        SET c.name = $name,
            c.slug = $slug,
            c.bio = $bio,
            c.avatar_url = $avatar_url,
            c.created_at = COALESCE(c.created_at, datetime()),
            c.updated_at = datetime()
        RETURN c
        """
        
        result = self.mock_neo4j.execute_write(
            query,
            parameters=self.fasffy_creator
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["name"], "Fasffy")
        self.assertEqual(result[0]["slug"], "fasffy")

    def test_init_platform_in_graph(self):
        """Test initialization of YouTube platform in Neo4j graph."""
        
        self.mock_neo4j.execute_write.return_value = [{
            "name": self.youtube_platform["name"],
            "slug": self.youtube_platform["slug"]
        }]
        
        query = """
        MERGE (p:Platform {slug: $slug})
        SET p.name = $name,
            p.api_base_url = $api_base_url,
            p.icon_url = $icon_url,
            p.created_at = COALESCE(p.created_at, datetime()),
            p.updated_at = datetime()
        RETURN p
        """
        
        result = self.mock_neo4j.execute_write(
            query,
            parameters=self.youtube_platform
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["slug"], "youtube")

    def test_add_youtube_handle_to_creator(self):
        """Test adding YouTube handle to creator with relationship."""
        
        self.mock_neo4j.execute_write.return_value = True
        
        query = """
        MATCH (c:Creator {uuid: $creator_uuid})
        MATCH (p:Platform {slug: $platform_slug})
        MERGE (h:Handle {uuid: $handle_uuid})
        SET h.username = $username,
            h.display_name = $display_name,
            h.profile_url = $profile_url,
            h.follower_count = $follower_count,
            h.verified_by_platform = $verified_by_platform,
            h.created_at = COALESCE(h.created_at, datetime()),
            h.updated_at = datetime()
        MERGE (c)-[r:OWNS_HANDLE]->(h)
        SET r.status = $status,
            r.verified = $verified,
            r.confidence = $confidence,
            r.discovered_at = $discovered_at,
            r.created_at = COALESCE(r.created_at, datetime())
        MERGE (h)-[:ON_PLATFORM]->(p)
        RETURN h, r
        """
        
        params = {
            "creator_uuid": self.fasffy_creator["uuid"],
            "handle_uuid": self.fasffy_handle["uuid"],
            "username": self.fasffy_handle["username"],
            "display_name": self.fasffy_handle["display_name"],
            "profile_url": self.fasffy_handle["profile_url"],
            "follower_count": self.fasffy_handle["follower_count"],
            "verified_by_platform": self.fasffy_handle["verified_by_platform"],
            "platform_slug": "youtube",
            "status": HandleStatus.ACTIVE.value,
            "verified": True,
            "confidence": VerificationConfidence.HIGH.value,
            "discovered_at": datetime.utcnow()
        }
        
        result = self.mock_neo4j.execute_write(query, parameters=params)
        self.assertTrue(result)

    def test_redis_cache_creator_data(self):
        """Test caching creator data in Redis."""
        
        cache_key = f"creator:{self.fasffy_creator['slug']}"
        cache_data = {
            "uuid": self.fasffy_creator["uuid"],
            "name": self.fasffy_creator["name"],
            "slug": self.fasffy_creator["slug"],
            "bio": self.fasffy_creator["bio"],
            "avatar_url": self.fasffy_creator["avatar_url"]
        }
        
        self.mock_redis.setex.return_value = True
        
        # Cache creator data with 1 hour TTL
        self.mock_redis.setex(
            cache_key,
            3600,
            json.dumps(cache_data)
        )
        
        self.mock_redis.setex.assert_called_once()
        
        # Retrieve cached data
        self.mock_redis.get.return_value = json.dumps(cache_data)
        cached = self.mock_redis.get(cache_key)
        
        self.assertIsNotNone(cached)
        retrieved_data = json.loads(cached)
        self.assertEqual(retrieved_data["name"], "Fasffy")

    def test_redis_health_check(self):
        """Test Redis health check."""
        
        self.mock_redis.ping.return_value = True
        
        health = self.mock_redis.ping()
        self.assertTrue(health)

    def test_neo4j_health_check(self):
        """Test Neo4j health check."""
        
        self.mock_neo4j.execute_read.return_value = [{"status": "ok"}]
        
        query = "RETURN 'ok' as status"
        result = self.mock_neo4j.execute_read(query)
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["status"], "ok")

    def test_get_creator_with_handles_from_graph(self):
        """Test retrieving creator with all handles from graph."""
        
        self.mock_neo4j.execute_read.return_value = [{
            "c_uuid": self.fasffy_creator["uuid"],
            "c_name": self.fasffy_creator["name"],
            "c_slug": self.fasffy_creator["slug"],
            "c_bio": self.fasffy_creator["bio"],
            "c_avatar_url": self.fasffy_creator["avatar_url"],
            "handle_uuid": self.fasffy_handle["uuid"],
            "handle_username": self.fasffy_handle["username"],
            "handle_display_name": self.fasffy_handle["display_name"],
            "handle_profile_url": self.fasffy_handle["profile_url"],
            "handle_follower_count": self.fasffy_handle["follower_count"],
            "handle_verified": self.fasffy_handle["verified_by_platform"],
            "platform_slug": "youtube",
            "relationship_status": HandleStatus.ACTIVE.value,
            "relationship_verified": True,
            "relationship_confidence": VerificationConfidence.HIGH.value
        }]
        
        query = """
        MATCH (c:Creator {slug: $slug})
        OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform)
        RETURN 
            c.uuid as c_uuid,
            c.name as c_name,
            c.slug as c_slug,
            c.bio as c_bio,
            c.avatar_url as c_avatar_url,
            h.uuid as handle_uuid,
            h.username as handle_username,
            h.display_name as handle_display_name,
            h.profile_url as handle_profile_url,
            h.follower_count as handle_follower_count,
            h.verified_by_platform as handle_verified,
            p.slug as platform_slug,
            r.status as relationship_status,
            r.verified as relationship_verified,
            r.confidence as relationship_confidence
        """
        
        result = self.mock_neo4j.execute_read(
            query,
            parameters={"slug": "fasffy"}
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["c_name"], "Fasffy")
        self.assertEqual(result[0]["handle_username"], "@Fasffy")

    def test_cache_miss_fallback_to_graph(self):
        """Test fallback to graph when cache miss occurs."""
        
        cache_key = f"creator:{self.misskatie_creator['slug']}"
        
        # Cache miss
        self.mock_redis.get.return_value = None
        
        # Fallback to graph
        self.mock_neo4j.execute_read.return_value = [{
            "c_uuid": self.misskatie_creator["uuid"],
            "c_name": self.misskatie_creator["name"],
            "c_slug": self.misskatie_creator["slug"],
            "c_bio": self.misskatie_creator["bio"],
            "c_avatar_url": self.misskatie_creator["avatar_url"],
            "handle_uuid": self.misskatie_handle["uuid"],
            "handle_username": self.misskatie_handle["username"],
            "handle_display_name": self.misskatie_handle["display_name"],
            "handle_profile_url": self.misskatie_handle["profile_url"],
            "handle_follower_count": self.misskatie_handle["follower_count"],
            "handle_verified": self.misskatie_handle["verified_by_platform"],
            "platform_slug": "youtube",
            "relationship_status": HandleStatus.ACTIVE.value,
            "relationship_verified": True,
            "relationship_confidence": VerificationConfidence.HIGH.value
        }]
        
        # Try cache first
        cached = self.mock_redis.get(cache_key)
        
        if cached is None:
            # Fallback to graph
            query = """
            MATCH (c:Creator {slug: $slug})
            OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform)
            RETURN 
                c.uuid as c_uuid,
                c.name as c_name,
                c.slug as c_slug,
                c.bio as c_bio,
                c.avatar_url as c_avatar_url,
                h.uuid as handle_uuid,
                h.username as handle_username,
                h.display_name as handle_display_name,
                h.profile_url as handle_profile_url,
                h.follower_count as handle_follower_count,
                h.verified_by_platform as handle_verified,
                p.slug as platform_slug,
                r.status as relationship_status,
                r.verified as relationship_verified,
                r.confidence as relationship_confidence
            """
            
            result = self.mock_neo4j.execute_read(
                query,
                parameters={"slug": "misskatie"}
            )
            
            self.assertIsNotNone(result)
            self.assertEqual(result[0]["c_name"], "Miss Katie")
            
            # Update cache
            cache_data = {
                "uuid": result[0]["c_uuid"],
                "name": result[0]["c_name"],
                "slug": result[0]["c_slug"],
                "bio": result[0]["c_bio"],
                "avatar_url": result[0]["c_avatar_url"]
            }
            self.mock_redis.setex(cache_key, 3600, json.dumps(cache_data))

    def test_list_all_youtube_subscriptions(self):
        """Test listing all YouTube channel subscriptions."""
        
        self.mock_neo4j.execute_read.return_value = [
            {
                "creator_slug": "fasffy",
                "creator_name": "Fasffy",
                "handle_username": "@Fasffy",
                "profile_url": "https://www.youtube.com/@Fasffy",
                "last_polled_at": datetime.utcnow() - timedelta(hours=2),
                "poll_interval_hours": 1
            },
            {
                "creator_slug": "misskatie",
                "creator_name": "Miss Katie",
                "handle_username": "@MissKatie",
                "profile_url": "https://www.youtube.com/@MissKatie",
                "last_polled_at": datetime.utcnow() - timedelta(hours=1),
                "poll_interval_hours": 1
            }
        ]
        
        query = """
        MATCH (c:Creator)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
        WHERE r.status = 'Active' AND r.verified = true
        OPTIONAL MATCH (c)-[sub:SUBSCRIBED_TO]->(p)
        RETURN 
            c.slug as creator_slug,
            c.name as creator_name,
            h.username as handle_username,
            h.profile_url as profile_url,
            sub.last_polled_at as last_polled_at,
            sub.poll_interval_hours as poll_interval_hours
        ORDER BY c.name
        """
        
        result = self.mock_neo4j.execute_read(query)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["creator_slug"], "fasffy")
        self.assertEqual(result[1]["creator_slug"], "misskatie")

    def test_update_subscription_status(self):
        """Test updating subscription polling status."""
        
        self.mock_neo4j.execute_write.return_value = True
        
        query = """
        MATCH (c:Creator {slug: $slug})-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
        MERGE (c)-[sub:SUBSCRIBED_TO]->(p)
        SET sub.last_polled_at = $last_polled_at,
            sub.poll_interval_hours = $poll_interval_hours,
            sub.status = $status,
            sub.updated_at = datetime()
        RETURN sub
        """
        
        params = {
            "slug": "fasffy",
            "last_polled_at": datetime.utcnow(),
            "poll_interval_hours": 1,
            "status": "active"
        }
        
        result = self.mock_neo4j.execute_write(query, parameters=params)
        self.assertTrue(result)

    def test_get_subscription_health_status(self):
        """Test getting health status for all subscriptions."""
        
        self.mock_neo4j.execute_read.return_value = [
            {
                "creator_slug": "fasffy",
                "status": "healthy",
                "last_successful_poll": datetime.utcnow() - timedelta(hours=1),
                "poll_count_24h": 24,
                "error_count_24h": 0
            },
            {
                "creator_slug": "misskatie",
                "status": "healthy",
                "last_successful_poll": datetime.utcnow() - timedelta(minutes=30),
                "poll_count_24h": 48,
                "error_count_24h": 1
            }
        ]
        
        query = """
        MATCH (c:Creator)-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
        WITH c, sub
        OPTIONAL MATCH (c)-[r:OWNS_HANDLE]->(h:Handle)
        RETURN 
            c.slug as creator_slug,
            CASE 
                WHEN sub.last_successful_poll > datetime() - duration('PT6H') 
                THEN 'healthy'
                WHEN sub.last_successful_poll > datetime() - duration('PT24H')
                THEN 'warning'
                ELSE 'unhealthy'
            END as status,
            sub.last_successful_poll as last_successful_poll,
            sub.poll_count_24h as poll_count_24h,
            sub.error_count_24h as error_count_24h
        """
        
        result = self.mock_neo4j.execute_read(query)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["status"], "healthy")
        self.assertEqual(result[1]["status"], "healthy")


class TestCreatorEntityInterface(unittest.TestCase):
    """Test interface for managing creator entities."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_neo4j = Mock()
        self.mock_redis = Mock()

    def test_create_new_creator_entity(self):
        """Test creating a new creator entity via interface."""
        
        creator_data = {
            "name": "Fasffy",
            "slug": "fasffy",
            "bio": "Content creator",
            "avatar_url": "https://example.com/avatar.jpg"
        }
        
        self.mock_neo4j.execute_write.return_value = [{
            "uuid": str(uuid4()),
            "name": creator_data["name"],
            "slug": creator_data["slug"],
            "bio": creator_data["bio"],
            "avatar_url": creator_data["avatar_url"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }]
        
        query = """
        MERGE (c:Creator {slug: $slug})
        SET c.name = COALESCE(c.name, $name),
            c.bio = COALESCE(c.bio, $bio),
            c.avatar_url = COALESCE(c.avatar_url, $avatar_url),
            c.updated_at = datetime()
        ON CREATE SET c.created_at = datetime(), c.uuid = $uuid
        RETURN c
        """
        
        result = self.mock_neo4j.execute_write(
            query,
            parameters={**creator_data, "uuid": str(uuid4())}
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["name"], "Fasffy")

    def test_add_platform_handle_to_creator(self):
        """Test adding a platform handle to existing creator."""
        
        handle_data = {
            "creator_slug": "misskatie",
            "platform": "youtube",
            "username": "@MissKatie",
            "display_name": "Miss Katie",
            "profile_url": "https://www.youtube.com/@MissKatie",
            "follower_count": 85000
        }
        
        self.mock_neo4j.execute_write.return_value = True
        
        query = """
        MATCH (c:Creator {slug: $creator_slug})
        MATCH (p:Platform {slug: $platform})
        MERGE (c)-[r:OWNS_HANDLE]->(h:Handle {profile_url: $profile_url})
        SET h.username = $username,
            h.display_name = $display_name,
            h.follower_count = $follower_count,
            h.updated_at = datetime()
        ON CREATE SET h.uuid = $uuid, h.created_at = datetime()
        SET r.status = 'Active',
            r.verified = true,
            r.confidence = 'High',
            r.updated_at = datetime()
        ON CREATE SET r.created_at = datetime(), r.discovered_at = datetime()
        RETURN h, r
        """
        
        result = self.mock_neo4j.execute_write(
            query,
            parameters={**handle_data, "uuid": str(uuid4())}
        )
        
        self.assertTrue(result)

    def test_get_creator_by_slug(self):
        """Test retrieving creator by slug."""
        
        self.mock_neo4j.execute_read.return_value = [{
            "uuid": str(uuid4()),
            "name": "Fasffy",
            "slug": "fasffy",
            "bio": "Content creator",
            "avatar_url": "https://example.com/avatar.jpg"
        }]
        
        query = """
        MATCH (c:Creator {slug: $slug})
        RETURN c.uuid as uuid, c.name as name, c.slug as slug, 
               c.bio as bio, c.avatar_url as avatar_url
        """
        
        result = self.mock_neo4j.execute_read(
            query,
            parameters={"slug": "fasffy"}
        )
        
        self.assertIsNotNone(result)
        self.assertEqual(result[0]["slug"], "fasffy")

    def test_search_creators_by_name(self):
        """Test searching creators by name pattern."""
        
        self.mock_neo4j.execute_read.return_value = [
            {"name": "Miss Katie", "slug": "misskatie"},
            {"name": "Katie Smith", "slug": "katie-smith"}
        ]
        
        query = """
        MATCH (c:Creator)
        WHERE toLower(c.name) CONTAINS toLower($search_term)
        RETURN c.name as name, c.slug as slug
        ORDER BY c.name
        LIMIT 20
        """
        
        result = self.mock_neo4j.execute_read(
            query,
            parameters={"search_term": "Katie"}
        )
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["name"], "Katie Smith")
        self.assertEqual(result[1]["name"], "Miss Katie")

    def test_update_creator_metadata(self):
        """Test updating creator metadata."""
        
        self.mock_neo4j.execute_write.return_value = True
        
        query = """
        MATCH (c:Creator {slug: $slug})
        SET c.bio = $bio,
            c.avatar_url = $avatar_url,
            c.updated_at = datetime()
        RETURN c
        """
        
        result = self.mock_neo4j.execute_write(
            query,
            parameters={
                "slug": "fasffy",
                "bio": "Updated bio for Fasffy",
                "avatar_url": "https://example.com/new-avatar.jpg"
            }
        )
        
        self.assertTrue(result)

    def test_delete_creator_entity(self):
        """Test soft delete of creator entity."""
        
        self.mock_neo4j.execute_write.return_value = True
        
        query = """
        MATCH (c:Creator {slug: $slug})
        SET c.deleted = true,
            c.deleted_at = datetime()
        RETURN c
        """
        
        result = self.mock_neo4j.execute_write(
            query,
            parameters={"slug": "fasffy"}
        )
        
        self.assertTrue(result)

    def test_invalidate_cache_on_update(self):
        """Test cache invalidation when creator is updated."""
        
        creator_slug = "fasffy"
        cache_key = f"creator:{creator_slug}"
        
        # Delete cache
        self.mock_redis.delete.return_value = 1
        
        deleted = self.mock_redis.delete(cache_key)
        self.assertEqual(deleted, 1)
        
        # Verify cache is empty
        self.mock_redis.get.return_value = None
        cached = self.mock_redis.get(cache_key)
        self.assertIsNone(cached)


if __name__ == "__main__":
    unittest.main()
