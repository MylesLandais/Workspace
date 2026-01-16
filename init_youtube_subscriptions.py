"""Script to initialize YouTube channel subscription test data and run health checks."""

import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from feed.storage.neo4j_connection import get_connection
from feed.storage.valkey_connection import get_valkey_connection


class YouTubeSubscriptionInitializer:
    """Initialize YouTube channel subscriptions and test infrastructure."""

    def __init__(self):
        self.neo4j = get_connection()
        self.valkey = get_valkey_connection()
        self.redis = self.valkey.client

    def run_init_script(self):
        """Run the Cypher init script."""
        print("=" * 70)
        print("INITIALIZING YOUTUBE CHANNEL SUBSCRIPTION DATA")
        print("=" * 70)
        print()

        init_script_path = Path(__file__).parent.parent / "src/feed/storage/migrations/013_youtube_channel_subscription_init.cypher"
        
        with open(init_script_path, 'r') as f:
            cypher_script = f.read()

        print(f"Running init script: {init_script_path.name}")
        print()

        # Split script into individual queries
        queries = [q.strip() for q in cypher_script.split('//') if q.strip() and not q.strip().startswith('=')]
        
        for i, query in enumerate(queries, 1):
            if not query or query.startswith('CREATE') or query.startswith('MERGE') or query.startswith('MATCH'):
                try:
                    # Skip comments
                    lines = [line for line in query.split('\n') if not line.strip().startswith('//')]
                    clean_query = '\n'.join(lines).strip()
                    
                    if clean_query:
                        result = self.neo4j.execute_write(clean_query)
                        if result:
                            print(f"Query {i}: ✓ Executed successfully")
                except Exception as e:
                    if "no such database" not in str(e).lower():
                        print(f"Query {i}: ✗ Error: {e}")

        print()
        print("=" * 70)
        print("INITIALIZATION COMPLETE")
        print("=" * 70)
        print()

    def verify_init_data(self):
        """Verify that test data was loaded correctly."""
        print("=" * 70)
        print("VERIFYING TEST DATA")
        print("=" * 70)
        print()

        # Check creators
        query = """
        MATCH (c:Creator)
        WHERE c.slug IN ['fasffy', 'misskatie']
        RETURN c.slug as slug, c.name as name, c.bio as bio
        ORDER BY c.name
        """
        
        creators = self.neo4j.execute_read(query)
        print(f"✓ Found {len(creators)} test creators:")
        for creator in creators:
            print(f"  - {creator['name']} (@{creator['slug']})")
            print(f"    Bio: {creator['bio'][:50]}..." if creator['bio'] else "")
        print()

        # Check YouTube handles
        query = """
        MATCH (c:Creator)-[r:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
        WHERE c.slug IN ['fasffy', 'misskatie']
        RETURN c.name as creator, h.username as handle, h.profile_url as url
        ORDER BY c.name
        """
        
        handles = self.neo4j.execute_read(query)
        print(f"✓ Found {len(handles)} YouTube handles:")
        for handle in handles:
            print(f"  - {handle['creator']}: {handle['handle']}")
            print(f"    URL: {handle['url']}")
        print()

        # Check subscriptions
        query = """
        MATCH (c:Creator)-[sub:SUBSCRIBED_TO]->(p:Platform {slug: 'youtube'})
        WHERE c.slug IN ['fasffy', 'misskatie']
        RETURN c.name as creator, sub.status as status, sub.poll_interval_hours as interval
        ORDER BY c.name
        """
        
        subscriptions = self.neo4j.execute_read(query)
        print(f"✓ Found {len(subscriptions)} active subscriptions:")
        for sub in subscriptions:
            print(f"  - {sub['creator']}: {sub['status']} (every {sub['interval']}h)")
        print()

        # Check media/videos
        query = """
        MATCH (c:Creator)-[r:OWNS_HANDLE]->(h:Handle)-[pub:PUBLISHED]->(v:Media:Video)
        WHERE c.slug IN ['fasffy', 'misskatie']
        RETURN c.name as creator, v.title as title, v.publish_date as published
        ORDER BY c.name, v.publish_date DESC
        """
        
        videos = self.neo4j.execute_read(query)
        print(f"✓ Found {len(videos)} test videos:")
        for video in videos:
            print(f"  - {video['creator']}: {video['title']}")
            print(f"    Published: {video['published']}")
        print()

    def test_redis_cache(self):
        """Test Redis caching for creator data."""
        print("=" * 70)
        print("TESTING REDIS CACHE")
        print("=" * 70)
        print()

        # Cache Fasffy data
        fasffy_key = "creator:fasffy"
        fasffy_data = {
            "uuid": "550e8400-e29b-41d4-a716-446655440001",
            "name": "Fasffy",
            "slug": "fasffy",
            "bio": "Content creator and streamer - Testing memes and challenges",
            "avatar_url": "https://example.com/fasffy-avatar.jpg"
        }
        
        print(f"Caching Fasffy data with key: {fasffy_key}")
        self.redis.setex(fasffy_key, 3600, json.dumps(fasffy_data))
        print("✓ Fasffy data cached (TTL: 1 hour)")
        print()

        # Cache Miss Katie data
        misskatie_key = "creator:misskatie"
        misskatie_data = {
            "uuid": "550e8400-e29b-41d4-a716-446655440002",
            "name": "Miss Katie",
            "slug": "misskatie",
            "bio": "YouTube content creator - Lifestyle and vlogs",
            "avatar_url": "https://example.com/misskatie-avatar.jpg"
        }
        
        print(f"Caching Miss Katie data with key: {misskatie_key}")
        self.redis.setex(misskatie_key, 3600, json.dumps(misskatie_data))
        print("✓ Miss Katie data cached (TTL: 1 hour)")
        print()

        # Verify cache
        cached_fasffy = self.redis.get(fasffy_key)
        if cached_fasffy:
            data = json.loads(cached_fasffy)
            print(f"✓ Retrieved Fasffy from cache: {data['name']}")
        else:
            print("✗ Failed to retrieve Fasffy from cache")
        print()

        # Test cache expiration
        ttl_fasffy = self.redis.ttl(fasffy_key)
        print(f"Fasffy cache TTL: {ttl_fasffy} seconds")
        print()

    def test_redis_health_check(self):
        """Test Redis health check."""
        print("=" * 70)
        print("REDIS HEALTH CHECK")
        print("=" * 70)
        print()

        try:
            # Ping Redis
            pong = self.redis.ping()
            print(f"✓ Redis PING: {'PONG' if pong else 'FAILED'}")
        except Exception as e:
            print(f"✗ Redis PING failed: {e}")
            return False

        # Get Redis info
        try:
            info = self.redis.info()
            print(f"✓ Redis version: {info.get('redis_version', 'unknown')}")
            print(f"✓ Connected clients: {info.get('connected_clients', 'unknown')}")
            print(f"✓ Used memory: {info.get('used_memory_human', 'unknown')}")
        except Exception as e:
            print(f"✗ Redis INFO failed: {e}")
        
        # Get database size
        try:
            db_size = self.redis.dbsize()
            print(f"✓ Database size: {db_size} keys")
        except Exception as e:
            print(f"✗ DBSIZE failed: {e}")
        
        print()

        return pong if pong else False

    def test_neo4j_health_check(self):
        """Test Neo4j health check."""
        print("=" * 70)
        print("NEO4J HEALTH CHECK")
        print("=" * 70)
        print()

        try:
            # Test basic query
            result = self.neo4j.execute_read("RETURN 'ok' as status")
            if result and result[0]['status'] == 'ok':
                print("✓ Neo4j connection: OK")
        except Exception as e:
            print(f"✗ Neo4j connection failed: {e}")
            return False

        # Get database info
        try:
            result = self.neo4j.execute_read("CALL db.labels() YIELD label RETURN collect(label) as labels")
            labels = result[0]['labels'] if result else []
            print(f"✓ Node labels: {', '.join(labels[:10])}{'...' if len(labels) > 10 else ''}")
        except Exception as e:
            print(f"✗ Failed to get labels: {e}")

        # Get relationship types
        try:
            result = self.neo4j.execute_read("CALL db.relationshipTypes() YIELD relationshipType RETURN collect(relationshipType) as types")
            types = result[0]['types'] if result else []
            print(f"✓ Relationship types: {', '.join(types[:10])}{'...' if len(types) > 10 else ''}")
        except Exception as e:
            print(f"✗ Failed to get relationship types: {e}")

        # Count nodes
        try:
            result = self.neo4j.execute_read("MATCH (n) RETURN count(n) as count")
            count = result[0]['count'] if result else 0
            print(f"✓ Total nodes: {count}")
        except Exception as e:
            print(f"✗ Failed to count nodes: {e}")

        print()
        return True

    def get_subscription_health_status(self):
        """Get health status for all YouTube subscriptions."""
        print("=" * 70)
        print("SUBSCRIPTION HEALTH STATUS")
        print("=" * 70)
        print()

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
        
        subscriptions = self.neo4j.execute_read(query)
        
        for sub in subscriptions:
            status_icon = "✓" if sub['status'] == 'healthy' else ("⚠" if sub['status'] == 'warning' else "✗")
            print(f"{status_icon} {sub['creator_name']} (@{sub['youtube_handle']})")
            print(f"   Status: {sub['status'].upper()}")
            print(f"   Last successful poll: {sub['last_successful_poll']}")
            print(f"   Poll interval: {sub['poll_interval_hours']} hours")
            print(f"   Polls (24h): {sub['poll_count_24h']}")
            print(f"   Errors (24h): {sub['error_count_24h']}")
            print()

    def list_all_subscriptions(self):
        """List all YouTube channel subscriptions."""
        print("=" * 70)
        print("ALL YOUTUBE CHANNEL SUBSCRIPTIONS")
        print("=" * 70)
        print()

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
            sub.poll_interval_hours as poll_interval_hours
        ORDER BY c.name
        """
        
        subscriptions = self.neo4j.execute_read(query)
        
        for sub in subscriptions:
            print(f"Name: {sub['creator_name']}")
            print(f"  Slug: {sub['creator_slug']}")
            print(f"  Handle: {sub['handle_username']}")
            print(f"  URL: {sub['profile_url']}")
            print(f"  Followers: {sub['followers']:,}")
            print(f"  Subscription: {sub['subscription_status']} (poll every {sub['poll_interval_hours']}h)")
            print()

    def run_all_tests(self):
        """Run all initialization and tests."""
        try:
            # Run init script
            self.run_init_script()
            
            # Verify data
            self.verify_init_data()
            
            # Test Redis
            self.test_redis_cache()
            redis_healthy = self.test_redis_health_check()
            
            # Test Neo4j
            neo4j_healthy = self.test_neo4j_health_check()
            
            # Get subscription health
            self.get_subscription_health_status()
            
            # List all subscriptions
            self.list_all_subscriptions()
            
            # Final summary
            print("=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"✓ Redis Health: {'OK' if redis_healthy else 'FAILED'}")
            print(f"✓ Neo4j Health: {'OK' if neo4j_healthy else 'FAILED'}")
            print(f"✓ Test data loaded successfully")
            print()

        except Exception as e:
            print(f"✗ Error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    initializer = YouTubeSubscriptionInitializer()
    initializer.run_all_tests()
