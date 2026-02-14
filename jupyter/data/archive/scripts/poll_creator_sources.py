#!/usr/bin/env python3
"""
Entity-based Reddit polling crawler.
Queries Creator entities and their linked sources, then polls for updates.
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection


def ensure_creator_entity(neo4j, creator_slug, creator_name):
    """Ensure Creator node exists."""
    from uuid import uuid4
    
    query = """
    MERGE (c:Creator {slug: $slug})
    ON CREATE SET
        c.uuid = $uuid,
        c.name = $name,
        c.slug = $slug,
        c.created_at = datetime(),
        c.updated_at = datetime()
    ON MATCH SET
        c.updated_at = datetime()
    RETURN c
    """
    
    neo4j.execute_write(
        query,
        parameters={
            "slug": creator_slug,
            "uuid": str(uuid4()),
            "name": creator_name,
        },
    )


def link_subreddit_to_creator(neo4j, subreddit_name, creator_slug):
    """Link subreddit to Creator node."""
    query = """
    MATCH (c:Creator {slug: $creator_slug})
    MERGE (s:Subreddit {name: $subreddit})
    ON CREATE SET s.created_at = datetime()
    WITH c, s
    MERGE (c)-[r:HAS_SOURCE]->(s)
    ON CREATE SET
        r.source_type = 'reddit',
        r.discovered_at = datetime(),
        r.created_at = datetime()
    ON MATCH SET
        r.updated_at = datetime()
    RETURN r
    """
    
    neo4j.execute_write(
        query,
        parameters={
            "creator_slug": creator_slug,
            "subreddit": subreddit_name,
        },
    )


def setup_creator_mapping(neo4j):
    """Set up Creator -> Subreddit mappings."""
    print("Setting up Creator entity mappings...")
    
    mappings = {
        "jordyn-jones": "Jordyn Jones",
        "brooke-monk": "Brooke Monk",
    }
    
    creator_sources = {
        "jordyn-jones": [
            "JordynJonesCandy",
            "JordynJonesBooty",
            "jordynjonesbody",
            "JordynJones_gooners",
            "JordynJonesSimp",
            "JordynJonesSnark",
            "jordynjones",
        ],
        "brooke-monk": [
            "BrookeMonkTheSecond",
            "BestOfBrookeMonk",
            "BrookeMonkNSFWHub",
        ],
    }
    
    for creator_slug, creator_name in mappings.items():
        ensure_creator_entity(neo4j, creator_slug, creator_name)
        
        for subreddit_name in creator_sources.get(creator_slug, []):
            link_subreddit_to_creator(neo4j, subreddit_name, creator_slug)
            print(f"  Linked r/{subreddit_name} -> {creator_slug}")
    
    print(f"Setup complete: {len(mappings)} creators configured")


def get_creator_sources(neo4j):
    """Query Neo4j for Creator -> Source mappings."""
    query = """
    MATCH (c:Creator)-[:HAS_SOURCE]->(s:Subreddit)
    RETURN c.slug as creator_slug, c.name as creator_name, s.name as subreddit
    ORDER BY c.slug, s.name
    """
    
    results = neo4j.execute_read(query)
    
    sources = {}
    for record in results:
        creator_slug = record["creator_slug"]
        if creator_slug not in sources:
            sources[creator_slug] = {
                "name": record["creator_name"],
                "subreddits": [],
            }
        sources[creator_slug]["subreddits"].append(record["subreddit"])
    
    return sources


def store_post_with_creator_link(neo4j, post, creator_slug):
    """Store post and link to Creator with entity_matched tag."""
    created_timestamp = int(post.created_utc.timestamp())
    
    post_query = """
    MERGE (p:Post {id: $id})
    SET p.title = $title,
        p.created_utc = datetime({epochSeconds: $created_utc}),
        p.score = $score,
        p.num_comments = $num_comments,
        p.upvote_ratio = $upvote_ratio,
        p.over_18 = $over_18,
        p.url = $url,
        p.selftext = $selftext,
        p.permalink = $permalink,
        p.entity_matched = $entity_name,
        p.updated_at = datetime()
    WITH p
    MERGE (s:Subreddit {name: $subreddit})
    ON CREATE SET s.created_at = datetime()
    WITH p, s
    MERGE (p)-[:POSTED_IN]->(s)
    WITH p
    MATCH (c:Creator {slug: $creator_slug})
    MERGE (p)-[:ABOUT]->(c)
    """
    
    neo4j.execute_write(
        post_query,
        parameters={
            "id": post.id,
            "title": post.title,
            "created_utc": created_timestamp,
            "score": post.score,
            "num_comments": post.num_comments,
            "upvote_ratio": post.upvote_ratio,
            "over_18": post.over_18,
            "url": post.url,
            "selftext": post.selftext,
            "permalink": post.permalink,
            "entity_name": creator_slug.replace("-", " ").title(),
            "subreddit": post.subreddit,
            "creator_slug": creator_slug,
        },
    )


def poll_creator_sources(neo4j, reddit, creator_slug, subreddits, max_posts=500, delay_min=10.0, delay_max=30.0):
    """Poll all subreddits for a creator."""
    print(f"\n{'='*70}")
    print(f"Creator: {creator_slug}")
    print(f"Subreddits: {', '.join([f'r/{s}' for s in subreddits])}")
    print(f"{'='*70}")
    
    total_collected = 0
    
    for subreddit in subreddits:
        print(f"\nProcessing r/{subreddit}...")
        
        # Fetch posts with deduplication
        all_posts = []
        after = None
        page = 0
        max_pages = 10
        
        while page < max_pages and len(all_posts) < max_posts:
            page += 1
            print(f"  Page {page}...")
            
            posts, next_after = reddit.fetch_posts(
                source=subreddit,
                sort="new",
                limit=100,
                after=after,
            )
            
            if not posts:
                print("  No more posts available")
                break
            
            # Check for existing posts
            post_ids = [p.id for p in posts]
            existing = neo4j.execute_read(
                "MATCH (p:Post) WHERE p.id IN $ids RETURN p.id as id",
                parameters={"ids": post_ids}
            )
            existing_ids = {r["id"] for r in existing}
            new_posts = [p for p in posts if p.id not in existing_ids]
            
            if new_posts:
                print(f"  -> {len(new_posts)} new posts")
                all_posts.extend(new_posts)
            else:
                print(f"  -> {len(posts)} posts (all duplicates)")
            
            after = next_after
            if not after:
                break
        
        # Store new posts linked to creator
        stored = 0
        for post in all_posts:
            try:
                store_post_with_creator_link(neo4j, post, creator_slug)
                stored += 1
            except Exception as e:
                print(f"    Error storing post {post.id}: {e}")
        
        print(f"  Stored {stored}/{len(all_posts)} posts from r/{subreddit}")
        total_collected += stored
        
        # Delay between subreddits
        if subreddit != subreddits[-1]:
            delay = random.uniform(delay_min, delay_max)
            print(f"  Waiting {delay:.1f} seconds...")
            time.sleep(delay)
    
    print(f"\nTotal collected for {creator_slug}: {total_collected} posts")
    return total_collected


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Entity-based Reddit polling")
    parser.add_argument("--setup", action="store_true", help="Set up Creator mappings")
    parser.add_argument("--max-posts", type=int, default=500, help="Max posts per creator")
    parser.add_argument("--delay-min", type=float, default=10.0, help="Min delay (seconds)")
    parser.add_argument("--delay-max", type=float, default=30.0, help="Max delay (seconds)")
    parser.add_argument("--creator", type=str, help="Poll specific creator slug only")
    
    args = parser.parse_args()
    
    # Connect to Neo4j
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Setup mappings if requested
    if args.setup:
        setup_creator_mapping(neo4j)
        return
    
    # Get creator sources from graph
    creator_sources = get_creator_sources(neo4j)
    
    if not creator_sources:
        print("No Creator -> Subreddit mappings found. Run with --setup first.")
        return
    
    print(f"\nFound {len(creator_sources)} creators in database:")
    for slug, info in creator_sources.items():
        print(f"  {slug} ({info['name']}): {len(info['subreddits'])} subreddits")
    
    # Filter to specific creator if requested
    if args.creator:
        if args.creator not in creator_sources:
            print(f"Creator '{args.creator}' not found")
            return
        creator_sources = {args.creator: creator_sources[args.creator]}
    
    # Initialize Reddit adapter
    reddit = RedditAdapter(mock=False, delay_min=args.delay_min, delay_max=args.delay_max)
    
    # Poll each creator's sources
    print("\n" + "="*70)
    print("Starting polling cycle")
    print("="*70)
    
    results = {}
    for creator_slug, info in creator_sources.items():
        try:
            count = poll_creator_sources(
                neo4j,
                reddit,
                creator_slug,
                info["subreddits"],
                max_posts=args.max_posts,
                delay_min=args.delay_min,
                delay_max=args.delay_max,
            )
            results[creator_slug] = count
        except Exception as e:
            print(f"Error polling {creator_slug}: {e}")
            results[creator_slug] = 0
    
    # Summary
    print("\n" + "="*70)
    print("Polling Complete")
    print("="*70)
    total = sum(results.values())
    for creator_slug, count in results.items():
        print(f"  {creator_slug}: {count} posts")
    print(f"\nTotal: {total} posts")


if __name__ == "__main__":
    main()
