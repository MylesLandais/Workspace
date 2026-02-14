"""Check if a Reddit post exists in the database."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Try to get connection - will use environment from container
try:
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Extract post ID from URL: https://www.reddit.com/r/Sjokz/comments/1nliihd/absolutely_stunning/
    post_id = "1nliihd"
    
    # Query for the post by ID
    query = """
    MATCH (p:Post {id: $post_id})
    OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
    RETURN p.id as id,
           p.title as title,
           p.url as url,
           p.permalink as permalink,
           s.name as subreddit,
           p.created_utc as created_utc,
           p.score as score,
           p.image_hash as image_hash
    """
    
    result = neo4j.execute_read(query, parameters={"post_id": post_id})
    
    if result:
        print(f"\n✓ Found post in database:")
        for record in result:
            data = dict(record)
            print(f"  ID: {data.get('id')}")
            print(f"  Title: {data.get('title')}")
            print(f"  Subreddit: {data.get('subreddit')}")
            print(f"  URL: {data.get('url')}")
            print(f"  Permalink: {data.get('permalink')}")
            print(f"  Score: {data.get('score')}")
            print(f"  Created: {data.get('created_utc')}")
            print(f"  Image Hash: {data.get('image_hash')}")
    else:
        print(f"\n✗ Post {post_id} not found in database")
        
        # Try searching by permalink or URL
        query2 = """
        MATCH (p:Post)
        WHERE p.permalink CONTAINS $search_term OR p.url CONTAINS $search_term
        OPTIONAL MATCH (p)-[:POSTED_IN]->(s:Subreddit)
        RETURN p.id as id,
               p.title as title,
               p.url as url,
               p.permalink as permalink,
               s.name as subreddit
        LIMIT 5
        """
        result2 = neo4j.execute_read(query2, parameters={"search_term": "1e35dhj"})
        if result2:
            print(f"\n  Found {len(result2)} posts with similar IDs/URLs:")
            for record in result2:
                data = dict(record)
                print(f"    - {data.get('id')}: {data.get('title')} (r/{data.get('subreddit')})")
        
        # Check if we have any posts from r/Sjokz subreddit
        query3 = """
        MATCH (s:Subreddit {name: 'Sjokz'})
        OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
        RETURN count(p) as post_count
        """
        result3 = neo4j.execute_read(query3)
        if result3 and result3[0]["post_count"] > 0:
            print(f"\n  We have {result3[0]['post_count']} posts from r/Sjokz subreddit")
            
            # Show a few recent posts from r/Sjokz
            query4 = """
            MATCH (s:Subreddit {name: 'Sjokz'})<-[:POSTED_IN]-(p:Post)
            RETURN p.id as id, p.title as title, p.created_utc as created_utc
            ORDER BY p.created_utc DESC
            LIMIT 5
            """
            result4 = neo4j.execute_read(query4)
            if result4:
                print(f"  Recent posts from r/Sjokz:")
                for record in result4:
                    data = dict(record)
                    print(f"    - {data.get('id')}: {data.get('title')}")
        else:
            print("\n  No posts found from r/Sjokz subreddit")
            
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

