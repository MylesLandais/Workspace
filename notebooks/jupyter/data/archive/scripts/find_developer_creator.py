#!/usr/bin/env python3
"""Find developer creator in database and add YouTube channel"""

import sys
from pathlib import Path
from uuid import uuid4
from neo4j import GraphDatabase

# Use local Neo4j instance on localhost
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USERNAME = "neo4j"
NEO4J_PASSWORD = "password"

class SimpleNeo4jConnection:
    """Simple Neo4j connection without .env file dependency"""
    
    def __init__(self, uri, username, password):
        self.uri = uri
        self.username = username
        self.password = password
        self._driver = None
    
    def connect(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(self.uri, auth=(self.username, self.password))
            self._driver.verify_connectivity()
        return self._driver
    
    def get_session(self, **kwargs):
        driver = self.connect()
        return driver.session(**kwargs)
    
    def execute_read(self, query, parameters=None, database="neo4j"):
        with self.get_session(database=database) as session:
            result = session.execute_read(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return result
    
    def execute_write(self, query, parameters=None, database="neo4j"):
        with self.get_session(database=database) as session:
            result = session.execute_write(
                lambda tx: list(tx.run(query, parameters or {}))
            )
            return result
    
    def close(self):
        if self._driver:
            self._driver.close()
            self._driver = None

# Create connection
neo4j = SimpleNeo4jConnection(NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD)

def find_or_create_developer_creator():
    """Find or create developer creator/guild profile"""
    # Use global neo4j connection

    # First, try to find existing developer creator
    query = '''
    MATCH (c:Creator)
    WHERE toLower(c.name) CONTAINS toLower('developer') OR toLower(c.slug) CONTAINS toLower('developer')
    RETURN c.uuid as uuid, c.name as name, c.slug as slug, c.bio as bio
    LIMIT 10
    '''

    result = neo4j.execute_read(query)

    if result:
        print('Found existing developer creator(s):')
        for record in result:
            print(f"  UUID: {record['uuid']}")
            print(f"  Name: {record['name']}")
            print(f"  Slug: {record['slug']}")
            print(f"  Bio: {record.get('bio', 'N/A')}")
            print()
        return result
    else:
        print('No developer creator found, creating one...')
        
        # Create developer creator
        create_query = '''
        MERGE (c:Creator {slug: $slug})
        ON CREATE SET
            c.uuid = $uuid,
            c.name = $name,
            c.slug = $slug,
            c.bio = $bio,
            c.created_at = datetime(),
            c.updated_at = datetime()
        ON MATCH SET
            c.name = COALESCE(c.name, $name),
            c.bio = COALESCE(c.bio, $bio),
            c.updated_at = datetime()
        RETURN c
        '''
        
        params = {
            'slug': 'developer',
            'name': 'Developer',
            'bio': 'Developer guild profile for monitoring development content',
            'uuid': str(uuid4())
        }
        
        result = neo4j.execute_write(create_query, parameters=params)
        
        if result:
            creator = result[0]['c']
            print(f"  ✓ Created developer creator:")
            print(f"    UUID: {creator.get('uuid')}")
            print(f"    Name: {creator.get('name')}")
            print(f"    Slug: {creator.get('slug')}")
            print()
            return [{'uuid': creator.get('uuid'), 'name': creator.get('name'), 'slug': creator.get('slug'), 'bio': creator.get('bio')}]
        else:
            print('  ✗ Failed to create developer creator')
            return None

def add_youtube_channel_to_creator(creator_slug, youtube_url):
    """Add YouTube channel to creator"""
    # Use global neo4j connection
    
    # Extract handle from URL
    if '@' in youtube_url:
        handle = '@' + youtube_url.split('@')[1]
    else:
        handle = youtube_url
    
    print(f"\nAdding YouTube channel to {creator_slug}:")
    print(f"  URL: {youtube_url}")
    print(f"  Handle: {handle}")
    
    # Ensure YouTube platform exists
    platform_query = '''
    MERGE (p:Platform {slug: 'youtube'})
    ON CREATE SET
        p.name = 'YouTube',
        p.api_base_url = 'https://www.googleapis.com/youtube/v3',
        p.icon_url = 'https://www.youtube.com/favicon.ico',
        p.created_at = datetime(),
        p.updated_at = datetime()
    RETURN p
    '''
    neo4j.execute_write(platform_query)
    print("  ✓ YouTube platform ensured")
    
    # Add YouTube handle to creator
    handle_query = '''
    MATCH (c:Creator {slug: $slug})
    MATCH (p:Platform {slug: 'youtube'})
    MERGE (c)-[r:OWNS_HANDLE]->(h:Handle {profile_url: $profile_url})
    ON CREATE SET
        h.created_at = datetime(),
        h.username = $handle,
        h.display_name = $display_name,
        h.uuid = $uuid,
        h.updated_at = datetime(),
        r.created_at = datetime(),
        r.discovered_at = datetime()
    ON MATCH SET
        h.username = $handle,
        h.display_name = $display_name,
        h.updated_at = datetime()
    SET r.status = 'Active',
        r.verified = true,
        r.confidence = 'High',
        r.updated_at = datetime()
    MERGE (h)-[:ON_PLATFORM]->(p)
    RETURN h, r
    '''
    
    params = {
        'slug': creator_slug,
        'handle': handle,
        'display_name': handle.replace('@', ''),
        'profile_url': youtube_url,
        'uuid': str(uuid4())
    }
    
    result = neo4j.execute_write(handle_query, parameters=params)
    
    if result:
        print("  ✓ YouTube handle added successfully")
        
        # Create subscription for monitoring
        subscription_query = '''
        MATCH (c:Creator {slug: $slug})
        MATCH (p:Platform {slug: 'youtube'})
        MERGE (c)-[sub:SUBSCRIBED_TO]->(p)
        ON CREATE SET
            sub.created_at = datetime()
        SET sub.status = 'active',
            sub.poll_interval_hours = 1,
            sub.last_polled_at = datetime(),
            sub.last_successful_poll = datetime(),
            sub.poll_count_24h = 0,
            sub.error_count_24h = 0,
            sub.updated_at = datetime()
        RETURN sub
        '''
        
        neo4j.execute_write(subscription_query, parameters={'slug': creator_slug})
        print("  ✓ Subscription created for monitoring")
        
        return True
    else:
        print("  ✗ Failed to add YouTube handle")
        return False
    
    neo4j.close()

if __name__ == "__main__":
    youtube_url = "https://www.youtube.com/@bmdavis419"
    
    creators = find_or_create_developer_creator()
    
    if creators:
        creator_slug = creators[0]['slug']
        print(f"\nUsing creator: {creator_slug}")
        success = add_youtube_channel_to_creator(creator_slug, youtube_url)
        
        if success:
            print(f"\n✓ Successfully attached YouTube channel to {creator_slug}")
            print("  The channel will now be monitored for new posts and updates")
        else:
            print("\n✗ Failed to attach YouTube channel")
    else:
        print("\nNo developer creator found. Please create one first.")
