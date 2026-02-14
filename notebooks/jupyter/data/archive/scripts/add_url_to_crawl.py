"""Add a URL to the crawl queue/frontier."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection
from feed.crawler.frontier import URLFrontier


def add_url_to_crawl(url: str):
    """Add a URL to the crawl queue."""
    print(f"Adding URL to crawl queue: {url}")
    
    # Get Neo4j connection
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Create frontier
    frontier = URLFrontier(neo4j)
    
    # Add URL
    added = frontier.add_url(url, priority=1.0)
    
    if added:
        print(f"✓ Successfully added URL to crawl queue")
    else:
        print(f"✗ URL already exists in queue or is invalid")
        
        # Check if it exists
        from feed.crawler.frontier import URLNormalizer
        normalizer = URLNormalizer()
        normalized = normalizer.normalize(url)
        
        query = """
        MATCH (w:WebPage {normalized_url: $normalized_url})
        RETURN w.normalized_url as url,
               w.domain as domain,
               w.last_crawled_at as last_crawled_at,
               w.next_crawl_at as next_crawl_at
        """
        result = neo4j.execute_read(query, parameters={"normalized_url": normalized})
        if result:
            print(f"  URL already in database:")
            data = dict(result[0])
            print(f"    Normalized URL: {data.get('url')}")
            print(f"    Domain: {data.get('domain')}")
            print(f"    Last crawled: {data.get('last_crawled_at')}")
            print(f"    Next crawl: {data.get('next_crawl_at')}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Add URL to crawl queue")
    parser.add_argument("url", help="URL to add to crawl queue")
    
    args = parser.parse_args()
    
    try:
        add_url_to_crawl(args.url)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()







