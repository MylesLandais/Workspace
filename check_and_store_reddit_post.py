#!/usr/bin/env python3
"""Check if a Reddit post exists in Neo4j and store it if missing."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection
from feed.storage.thread_storage import store_thread
from feed.utils.reddit_url_extractor import extract_post_id_from_url, parse_reddit_url


def check_and_store_post(post_url: str):
    """Check if post exists, and store it if missing."""
    # Extract post ID from URL
    post_id = extract_post_id_from_url(post_url)
    if not post_id:
        print(f"Error: Could not extract post ID from URL: {post_url}")
        return False
    
    # Connect to Neo4j
    neo4j = get_connection()
    print(f"Connected to Neo4j: {neo4j.uri}")
    
    # Check if post exists
    check_query = """
    MATCH (p:Post {id: $post_id})
    RETURN p.id as id, p.title as title, p.permalink as permalink
    """
    result = neo4j.execute_read(check_query, parameters={"post_id": post_id})
    
    if result:
        record = result[0]
        print(f"Post already exists in database:")
        print(f"  ID: {record['id']}")
        print(f"  Title: {record.get('title', 'N/A')}")
        print(f"  Permalink: {record.get('permalink', 'N/A')}")
        return True
    
    print(f"Post not found in database. Fetching from Reddit...")
    
    # Fetch the post using Reddit adapter
    reddit = RedditAdapter()
    
    # Extract permalink from URL
    parsed = parse_reddit_url(post_url)
    if parsed and parsed.get('permalink'):
        permalink = parsed['permalink']
    else:
        # Fallback: try to extract from URL structure
        if "/comments/" in post_url:
            # Extract path after domain
            from urllib.parse import urlparse
            parsed_url = urlparse(post_url)
            path_parts = parsed_url.path.strip('/').split('/')
            if len(path_parts) >= 4 and path_parts[0] == 'r' and path_parts[2] == 'comments':
                permalink = '/' + '/'.join(path_parts[:4]) + '/'
            else:
                print(f"Error: Could not extract permalink from URL")
                return False
        else:
            print(f"Error: Could not extract permalink from URL")
            return False
    
    print(f"Fetching thread: {permalink}")
    post, comments, raw_post_data = reddit.fetch_thread(permalink)
    
    if not post:
        print(f"Error: Failed to fetch post from Reddit")
        return False
    
    print(f"Fetched post:")
    print(f"  ID: {post.id}")
    print(f"  Title: {post.title}")
    print(f"  Subreddit: {post.subreddit}")
    print(f"  Comments: {len(comments)}")
    
    # Extract images
    images = []
    
    # Extract images from post
    post_images = reddit.extract_all_images(post, raw_post_data)
    for img_url in post_images:
        images.append({
            "url": img_url,
            "source": "post",
            "post_id": post.id,
        })
    
    # Extract images from comments
    comment_images = reddit.extract_images_from_comments(comments)
    images.extend(comment_images)
    
    print(f"  Images found: {len(images)}")
    
    # Store in Neo4j
    print(f"Storing in Neo4j...")
    try:
        store_thread(neo4j, post, comments, images, raw_post_data)
        print(f"Successfully stored post {post.id} in database!")
        return True
    except Exception as e:
        print(f"Error storing post: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    post_url = "https://www.reddit.com/r/TaylorSwiftPictures/comments/1pt3bnb/loving_the_look/"
    check_and_store_post(post_url)

