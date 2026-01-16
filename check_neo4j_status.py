"""Check Neo4j connection status and database statistics."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def main():
    print("=" * 70)
    print("NEO4J CONNECTION STATUS")
    print("=" * 70)
    
    try:
        conn = get_connection()
        print(f"URI: {conn.uri}")
        print(f"Username: {conn.username}")
        print()
        
        # Test connection
        driver = conn.connect()
        print("Connection: SUCCESS")
        print()
        
        # Get total node count
        result = conn.execute_read("MATCH (n) RETURN count(*) as count")
        total_nodes = result[0]["count"] if result else 0
        print(f"Total nodes: {total_nodes:,}")
        
        # Get relationship count
        result = conn.execute_read("MATCH ()-[r]->() RETURN count(r) as count")
        total_rels = result[0]["count"] if result else 0
        print(f"Total relationships: {total_rels:,}")
        print()
        
        # Get node types
        result = conn.execute_read(
            "MATCH (n) RETURN labels(n) as labels, count(*) as count "
            "ORDER BY count DESC LIMIT 10"
        )
        print("Top node types:")
        for record in result:
            labels = record["labels"]
            count = record["count"]
            label_str = ":".join(labels) if labels else "(no label)"
            print(f"  {label_str}: {count:,}")
        print()
        
        # Check for imageboard-specific nodes
        result = conn.execute_read("MATCH (t:Thread) RETURN count(t) as count")
        thread_count = result[0]["count"] if result else 0
        
        result = conn.execute_read("MATCH (p:Post) RETURN count(p) as count")
        post_count = result[0]["count"] if result else 0
        
        result = conn.execute_read(
            "MATCH (p:Post) WHERE p.image_url IS NOT NULL RETURN count(p) as count"
        )
        image_post_count = result[0]["count"] if result else 0
        
        print("imageboard-specific data:")
        print(f"  Thread nodes: {thread_count}")
        print(f"  Post nodes: {post_count:,}")
        print(f"  Posts with images: {image_post_count:,}")
        print()
        
        conn.close()
        print("=" * 70)
        print("STATUS: CONNECTED AND OPERATIONAL")
        print("=" * 70)
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())






