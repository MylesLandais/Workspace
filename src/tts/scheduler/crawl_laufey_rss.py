#!/usr/bin/env python3
"""
Crawl r/laufeyhot using RSS feed as fallback method.
Uses old.reddit.com RSS feed to collect posts that may not be available via JSON API.
"""

import sys
import time
import random
from pathlib import Path
from datetime import datetime
from typing import List

sys.path.insert(0, str(Path(__file__).parent / "src"))

import feedparser
from feed.models.post import Post
from feed.storage.neo4j_connection import get_connection


def store_posts_directly(posts: List[Post], subreddit_name: str, neo4j):
    """Store posts directly to Neo4j."""
    if not posts:
        return 0
    
    stored = 0
    
    # Create subreddit node
    subreddit_query = """
    MERGE (s:Subreddit {name: $name})
    ON CREATE SET s.created_at = datetime()
    RETURN s
    """
    neo4j.execute_write(subreddit_query, parameters={"name": subreddit_name})
    
    # Store each post
    for post in posts:
        try:
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
                p.updated_at = datetime()
            WITH p
            MATCH (s:Subreddit {name: $subreddit})
            MERGE (p)-[:POSTED_IN]->(s)
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
                    "subreddit": post.subreddit,
                },
            )
            
            # Create user node if author exists
            if post.author:
                user_query = """
                MERGE (u:User {username: $username})
                ON CREATE SET u.created_at = datetime()
                WITH u
                MATCH (p:Post {id: $post_id})
                MERGE (u)-[:POSTED]->(p)
                """
                neo4j.execute_write(
                    user_query,
                    parameters={"username": post.author, "post_id": post.id},
                )
            
            stored += 1
        except Exception as e:
            print(f"  Warning: Error storing post {post.id}: {e}")
            continue
    
    return stored


def fetch_rss_posts(subreddit: str, use_old_reddit: bool = True) -> List[Post]:
    """Fetch posts from RSS feed."""
    subreddit = subreddit.replace("r/", "").replace("/r/", "").strip()
    
    base_url = "https://old.reddit.com" if use_old_reddit else "https://www.reddit.com"
    rss_url = f"{base_url}/r/{subreddit}/.rss"
    
    print(f"  Fetching RSS: {rss_url}")
    
    try:
        feed = feedparser.parse(rss_url)
        
        if feed.bozo and feed.bozo_exception:
            print(f"  Warning: RSS parsing issue: {feed.bozo_exception}")
            return []
        
        if not feed.entries:
            print(f"  No entries in RSS feed")
            return []
        
        posts = []
        for entry in feed.entries:
            try:
                # Extract post ID from link
                link = entry.get("link", "")
                post_id = None
                
                if "/comments/" in link:
                    parts = link.split("/comments/")
                    if len(parts) > 1:
                        post_id = parts[1].split("/")[0]
                
                if not post_id:
                    # Fallback: use hash of title + link
                    post_id = f"rss_{abs(hash(entry.get('title', '') + link)) % (10**12)}"
                
                # Parse published date
                published_time = entry.get("published_parsed")
                if published_time:
                    created_utc = datetime(*published_time[:6])
                else:
                    created_utc = datetime.utcnow()
                
                # Extract subreddit from link
                subreddit_from_link = subreddit
                if "/r/" in link:
                    try:
                        subreddit_part = link.split("/r/")[1].split("/")[0]
                        subreddit_from_link = subreddit_part
                    except:
                        pass
                
                # Extract author
                author = None
                if hasattr(entry, "author"):
                    author = entry.author
                elif hasattr(entry, "tags") and entry.tags:
                    for tag in entry.tags:
                        if hasattr(tag, "term") and tag.term.startswith("author:"):
                            author = tag.term.replace("author:", "")
                            break
                
                # Extract URL - check for image links
                url = entry.get("link", "")
                
                # Check for image URLs in links
                if hasattr(entry, "links"):
                    for link_obj in entry.links:
                        href = link_obj.get("href", "")
                        if "i.redd.it" in href or "i.imgur.com" in href or "redd.it" in href:
                            url = href
                            break
                
                # Try to get summary/description
                selftext = entry.get("summary", "") or entry.get("description", "")
                
                post = Post(
                    id=post_id,
                    title=entry.get("title", "")[:500],
                    created_utc=created_utc,
                    score=0,  # RSS doesn't include score
                    num_comments=0,  # RSS doesn't include comments
                    upvote_ratio=0.0,
                    over_18=False,
                    url=url,
                    selftext=selftext[:5000] if selftext else "",
                    author=author,
                    subreddit=subreddit_from_link,
                    permalink=entry.get("link", ""),
                )
                posts.append(post)
                
            except Exception as e:
                print(f"  Error parsing entry: {e}")
                continue
        
        print(f"  Parsed {len(posts)} posts from RSS")
        return posts
        
    except Exception as e:
        print(f"  Error fetching RSS: {e}")
        return []


def crawl_laufeyhot_rss(target_new: int = 100, delay_min: float = 30.0, delay_max: float = 60.0):
    """Crawl r/laufeyhot using RSS feed."""
    subreddit = "laufeyhot"
    
    print("=" * 70)
    print("Reddit RSS Crawler - r/laufeyhot (Fallback Method)")
    print("=" * 70)
    print(f"\nTarget: {target_new} new posts")
    print(f"Rate limit: {delay_min}-{delay_max} seconds between requests")
    
    try:
        neo4j = get_connection()
        print(f"\nConnected to Neo4j: {neo4j.uri}")
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        return 1
    
    # Check existing posts
    result = neo4j.execute_read(
        "MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name}) RETURN count(p) as total",
        parameters={"name": subreddit}
    )
    existing_count = result[0]["total"] if result else 0
    print(f"Existing posts in database: {existing_count}")
    
    all_new_posts = []
    iteration = 0
    max_iterations = 50  # Safety limit
    consecutive_no_new = 0
    
    start_time = time.time()
    
    print("\n" + "=" * 70)
    print("Starting RSS crawl...")
    print("=" * 70 + "\n")
    
    while len(all_new_posts) < target_new and iteration < max_iterations:
        iteration += 1
        print(f"--- Iteration {iteration} ---")
        
        # Fetch posts from RSS
        posts = fetch_rss_posts(subreddit, use_old_reddit=True)
        
        if not posts:
            print("  No posts retrieved")
            consecutive_no_new += 1
            if consecutive_no_new >= 3:
                print("  No new posts for 3 iterations, stopping")
                break
        else:
            # Check for duplicates
            post_ids = [p.id for p in posts]
            existing = neo4j.execute_read(
                "MATCH (p:Post) WHERE p.id IN $ids RETURN p.id as id",
                parameters={"ids": post_ids}
            )
            existing_ids = {r["id"] for r in existing}
            new_posts = [p for p in posts if p.id not in existing_ids]
            
            if new_posts:
                consecutive_no_new = 0
                all_new_posts.extend(new_posts)
                print(f"  Found {len(new_posts)} new posts (total new: {len(all_new_posts)})")
                
                # Store to database
                stored = store_posts_directly(new_posts, subreddit, neo4j)
                print(f"  Stored {stored} posts to database")
            else:
                print(f"  All {len(posts)} posts already in database")
                consecutive_no_new += 1
                if consecutive_no_new >= 5:
                    print("  No new posts for 5 iterations, stopping")
                    break
        
        if len(all_new_posts) >= target_new:
            print(f"\n✓ Reached target of {target_new} new posts!")
            break
        
        # Delay before next request
        delay = random.uniform(delay_min, delay_max)
        print(f"  Waiting {delay:.1f} seconds before next request...")
        time.sleep(delay)
    
    elapsed = time.time() - start_time
    
    # Final count
    result = neo4j.execute_read(
        "MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $name}) RETURN count(p) as total",
        parameters={"name": subreddit}
    )
    final_count = result[0]["total"] if result else 0
    
    print("\n" + "=" * 70)
    print("Crawl Complete")
    print("=" * 70)
    print(f"\nNew posts collected: {len(all_new_posts)}")
    print(f"Total posts in database: {final_count} (was {existing_count})")
    print(f"Total time: {elapsed / 60:.1f} minutes")
    
    return 0


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Crawl r/laufeyhot using RSS feed")
    parser.add_argument("--target", type=int, default=100, help="Target new posts")
    parser.add_argument("--delay-min", type=float, default=30.0, help="Min delay (seconds)")
    parser.add_argument("--delay-max", type=float, default=60.0, help="Max delay (seconds)")
    
    args = parser.parse_args()
    
    sys.exit(crawl_laufeyhot_rss(
        target_new=args.target,
        delay_min=args.delay_min,
        delay_max=args.delay_max
    ))






