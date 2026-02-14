#!/usr/bin/env python3
"""
Export mock data from Neo4j to JSON files and download images.
Creates a mock_data/ folder with organized JSON and image files.
"""

import sys
import json
import os
import requests
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from typing import List, Optional
import time

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.storage.neo4j_connection import get_connection


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem."""
    # Remove invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    return filename


def is_image_url(url: str) -> bool:
    """Check if URL is a direct image URL."""
    if not url:
        return False
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']
    image_domains = ['i.redd.it', 'i.imgur.com', 'preview.redd.it']
    url_lower = url.lower()
    
    # Check domain
    for domain in image_domains:
        if domain in url_lower:
            return True
    
    # Check extension
    parsed = urlparse(url_lower)
    path = parsed.path
    for ext in image_extensions:
        if path.endswith(ext):
            return True
    
    return False


def download_image(url: str, output_path: Path, max_retries: int = 3) -> bool:
    """Download an image from URL to output path."""
    if not is_image_url(url):
        return False
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (compatible; Feed Monitor 1.0)'
        }
        
        for attempt in range(max_retries):
            try:
                response = requests.get(url, headers=headers, timeout=10, stream=True)
                response.raise_for_status()
                
                # Determine file extension from URL or content type
                parsed = urlparse(url)
                path = parsed.path
                ext = os.path.splitext(path)[1]
                
                if not ext or ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp']:
                    content_type = response.headers.get('content-type', '')
                    if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                        ext = '.jpg'
                    elif 'image/png' in content_type:
                        ext = '.png'
                    elif 'image/gif' in content_type:
                        ext = '.gif'
                    elif 'image/webp' in content_type:
                        ext = '.webp'
                    else:
                        ext = '.jpg'  # Default
                
                # Ensure output path has correct extension
                output_file = output_path.with_suffix(ext)
                
                # Write file
                with open(output_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                return True
                
            except requests.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                print(f"  Warning: Failed to download {url}: {e}")
                return False
                
    except Exception as e:
        print(f"  Warning: Error downloading {url}: {e}")
        return False
    
    return False


def export_subreddit_data(subreddit_name: str, output_dir: Path):
    """
    Export all posts from a subreddit to JSON and download images.
    
    Args:
        subreddit_name: Name of subreddit to export
        output_dir: Base output directory (creates subreddit subfolder)
    """
    neo4j = get_connection()
    
    # Create subreddit-specific directories
    subreddit_dir = output_dir / subreddit_name
    json_dir = subreddit_dir / "json"
    images_dir = subreddit_dir / "images"
    json_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\nExporting r/{subreddit_name}...")
    
    # Query posts
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
    OPTIONAL MATCH (u:User)-[:POSTED]->(p)
    RETURN p, u.username as author
    ORDER BY p.created_utc DESC
    """
    
    result = neo4j.execute_read(query, parameters={"subreddit": subreddit_name})
    
    posts = []
    downloaded_images = 0
    skipped_images = 0
    
    for record in result:
        post_node = record["p"]
        post_data = dict(post_node)
        post_data["author"] = record["author"]
        
        # Convert datetime objects to ISO strings
        for key, value in list(post_data.items()):
            if isinstance(value, datetime):
                post_data[key] = value.isoformat()
        
        # Extract image URL
        image_url = None
        url = post_data.get("url", "")
        if is_image_url(url):
            image_url = url
        
        # Add image_url field if we have one
        if image_url:
            post_data["image_url"] = image_url
            post_data["is_image"] = True
        else:
            post_data["is_image"] = False
            post_data["image_url"] = None
        
        posts.append(post_data)
        
        # Download image if available
        if image_url:
            # Create filename from post ID and title
            post_id = post_data.get("id", "unknown")
            title = post_data.get("title", "")[:50]
            safe_title = sanitize_filename(title)
            image_filename = f"{post_id}_{safe_title}"
            image_path = images_dir / image_filename
            
            if download_image(image_url, image_path):
                post_data["local_image_path"] = f"{subreddit_name}/images/{image_path.name}"
                downloaded_images += 1
                print(f"  Downloaded image for: {post_data.get('title', '')[:50]}")
            else:
                skipped_images += 1
    
    # Write JSON file
    json_file = json_dir / f"{subreddit_name}_posts.json"
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump({
            "subreddit": subreddit_name,
            "export_date": datetime.utcnow().isoformat(),
            "total_posts": len(posts),
            "images_downloaded": downloaded_images,
            "images_skipped": skipped_images,
            "posts": posts
        }, f, indent=2, default=str, ensure_ascii=False)
    
    print(f"\n✓ Exported {len(posts)} posts from r/{subreddit_name}")
    print(f"  JSON file: {json_file}")
    print(f"  Images downloaded: {downloaded_images}")
    print(f"  Images skipped: {skipped_images}")
    print(f"  Output directory: {subreddit_dir}")
    
    return posts


def export_all_subreddits(output_dir: Path, subreddits: Optional[List[str]] = None):
    """
    Export all subreddits in the database, or specific ones if provided.
    
    Args:
        output_dir: Output directory for exports
        subreddits: Optional list of specific subreddits to export (default: all)
    """
    neo4j = get_connection()
    
    if subreddits:
        # Export specific subreddits
        print(f"Exporting {len(subreddits)} specified subreddits:")
        for sub in subreddits:
            print(f"  r/{sub}")
        subreddit_list = subreddits
    else:
        # Get all subreddits
        query = """
        MATCH (s:Subreddit)
        OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
        WITH s, count(p) as post_count
        WHERE post_count > 0
        RETURN s.name as name, post_count
        ORDER BY post_count DESC
        """
        
        result = neo4j.execute_read(query)
        subreddit_list = [record["name"] for record in result]
        
        print(f"Found {len(subreddit_list)} subreddits with posts:")
        for record in result:
            print(f"  r/{record['name']}: {record['post_count']} posts")
    
    all_posts = {}
    for subreddit in subreddit_list:
        posts = export_subreddit_data(subreddit, output_dir)
        all_posts[subreddit] = posts
        time.sleep(1)  # Small delay between subreddits
    
    # Create summary file
    summary = {
        "export_date": datetime.utcnow().isoformat(),
        "total_subreddits": len(subreddit_list),
        "subreddits": {name: len(posts) for name, posts in all_posts.items()},
        "total_posts": sum(len(posts) for posts in all_posts.values())
    }
    
    summary_file = output_dir / "summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, default=str)
    
    print(f"\n{'='*70}")
    print(f"Export Complete!")
    print(f"{'='*70}")
    print(f"Summary saved to: {summary_file}")
    print(f"Total subreddits: {summary['total_subreddits']}")
    print(f"Total posts: {summary['total_posts']}")
    print(f"Output directory: {output_dir}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Export mock data from Neo4j")
    parser.add_argument(
        "--subreddit",
        help="Export specific subreddit (default: export all)",
    )
    parser.add_argument(
        "--subreddits",
        nargs="+",
        help="Export specific list of subreddits",
    )
    parser.add_argument(
        "--output-dir",
        default="mock_data",
        help="Output directory (default: mock_data)",
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update existing mock_data (adds/updates subreddits without removing others)",
    )
    
    args = parser.parse_args()
    
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.subreddit:
        export_subreddit_data(args.subreddit, output_dir)
    elif args.subreddits:
        export_all_subreddits(output_dir, subreddits=args.subreddits)
    else:
        export_all_subreddits(output_dir)


if __name__ == "__main__":
    main()

