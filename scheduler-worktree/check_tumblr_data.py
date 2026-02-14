#!/usr/bin/env python3
"""
Check existing sources and data in Neo4j knowledge graph.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection


def check_sources_in_frontier(neo4j):
    """Check what sources are in the URL frontier."""
    print("\n" + "=" * 70)
    print("📋 URL FRONTIER (Source Management)")
    print("=" * 70)

    query = """
    MATCH (w:WebPage)
    WHERE w.domain CONTAINS 'tumblr.com'
    RETURN w.original_url as url,
           w.domain as domain,
           w.last_crawled_at as last_crawled,
           w.next_crawl_at as next_crawl,
           w.created_at as created_at
    ORDER BY w.created_at DESC
    """

    results = neo4j.execute_read(query)

    if results:
        print(f"\nFound {len(results)} Tumblr sources in frontier:\n")
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['url']}")
            print(f"   Domain: {result['domain']}")
            print(f"   Created: {result['created_at']}")
            print(f"   Last crawled: {result['last_crawled'] or 'Never'}")
            print(f"   Next crawl: {result['next_crawl']}")
            print()
    else:
        print("\n⚠ No Tumblr sources found in frontier.")


def check_posts_in_graph(neo4j):
    """Check what posts are stored in the graph."""
    print("\n" + "=" * 70)
    print("📥 POSTS IN KNOWLEDGE GRAPH")
    print("=" * 70)

    # Count posts by source
    count_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE s.source_type = 'blog'
    RETURN s.name as source,
           count(p) as post_count,
           min(p.created_utc) as first_post,
           max(p.created_utc) as last_post
    ORDER BY post_count DESC
    """

    results = neo4j.execute_read(count_query)

    if results:
        print(f"\nFound posts from {len(results)} sources:\n")
        for result in results:
            print(f"Source: {result['source']}")
            print(f"  Posts: {result['post_count']}")
            print(f"  First post: {result['first_post']}")
            print(f"  Last post: {result['last_post']}")
            print()
    else:
        print("\n⚠ No blog posts found in graph.")

    # Recent posts
    print("Recent posts:")
    recent_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE s.source_type = 'blog'
    RETURN p.id as id,
           s.name as source,
           p.title as title,
           p.created_utc as created_at
    ORDER BY p.created_utc DESC
    LIMIT 5
    """

    results = neo4j.execute_read(recent_query)
    if results:
        for result in results:
            print(f"  [{result['source']}] {result['title']}")
            print(f"    ID: {result['id']}")
            print(f"    Created: {result['created_at']}")
            print()


def check_images_in_graph(neo4j):
    """Check what images are stored in the graph."""
    print("\n" + "=" * 70)
    print("🖼️  IMAGES IN KNOWLEDGE GRAPH")
    print("=" * 70)

    # Count images
    count_query = """
    MATCH (p:Post)-[:HAS_IMAGE]->(i:Image)
    RETURN count(i) as total_images
    """

    results = neo4j.execute_read(count_query)
    if results:
        print(f"\nTotal images: {results[0]['total_images']}")

    # Images per source
    per_source_query = """
    MATCH (p:Post)-[:HAS_IMAGE]->(i:Image)
    MATCH (p)-[:POSTED_IN]->(s:Subreddit)
    RETURN s.name as source,
           count(i) as image_count
    ORDER BY image_count DESC
    """

    results = neo4j.execute_read(per_source_query)
    if results:
        print("\nImages per source:\n")
        for result in results:
            print(f"  {result['source']}: {result['image_count']} images")


def check_tags_in_graph(neo4j):
    """Check what tags are stored in the graph."""
    print("\n" + "=" * 70)
    print("🏷️  TAGS IN KNOWLEDGE GRAPH")
    print("=" * 70)

    # Total tags
    count_query = """
    MATCH (p:Post)-[:HAS_TAG]->(t:Tag)
    RETURN count(t) as total_tags
    """

    results = neo4j.execute_read(count_query)
    if results:
        print(f"\nTotal tags: {results[0]['total_tags']}")

    # Top tags
    top_tags_query = """
    MATCH (p:Post)-[:HAS_TAG]->(t:Tag)
    WITH t, count(p) as usage_count
    RETURN t.name as tag, usage_count
    ORDER BY usage_count DESC
    LIMIT 10
    """

    results = neo4j.execute_read(top_tags_query)
    if results:
        print("\nTop 10 tags:\n")
        for result in results:
            print(f"  #{result['tag']} ({result['usage_count']} uses)")


def get_overall_stats(neo4j):
    """Get overall statistics about the graph."""
    print("\n" + "=" * 70)
    print("📊 OVERALL STATISTICS")
    print("=" * 70)

    stats_queries = {
        "Total posts": "MATCH (p:Post) RETURN count(p) as count",
        "Total images": "MATCH (i:Image) RETURN count(i) as count",
        "Total tags": "MATCH (t:Tag) RETURN count(t) as count",
        "Total sources (subreddits/blogs)": "MATCH (s:Subreddit) RETURN count(s) as count",
        "Total users": "MATCH (u:User) RETURN count(u) as count",
    }

    for name, query in stats_queries.items():
        results = neo4j.execute_read(query)
        if results:
            print(f"  {name}: {results[0]['count']}")


def main():
    """Main execution."""
    print("🔍 NEO4J DATA INSPECTOR")
    print("=" * 70)

    # Connect to Neo4j
    neo4j = get_connection()
    print(f"Connected to: {neo4j.uri}\n")

    try:
        # Check each component
        get_overall_stats(neo4j)
        check_sources_in_frontier(neo4j)
        check_posts_in_graph(neo4j)
        check_images_in_graph(neo4j)
        check_tags_in_graph(neo4j)

        print("\n" + "=" * 70)
        print("✅ Inspection complete!")
        print("=" * 70)

    finally:
        neo4j.close()


if __name__ == "__main__":
    main()
