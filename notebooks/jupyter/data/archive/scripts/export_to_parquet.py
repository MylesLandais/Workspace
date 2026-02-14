"""Export Neo4j data to Parquet for distribution."""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection


def create_parquet_export():
    """Create Parquet datasets from Neo4j data."""
    
    try:
        import pandas as pd
        import pyarrow as pa
        from pyarrow.parquet import write_table
    except ImportError as e:
        print(f"Error: Required packages not installed: {e}")
        print("Install with: pip install pandas pyarrow")
        raise
    
    output_dir = Path("datasets/parquet")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("EXPORTING REDDIT DATA TO PARQUET")
    print("=" * 70)
    print(f"Output directory: {output_dir.absolute()}")
    print()
    
    neo4j = get_connection()
    
    # Export Subreddits
    print("Exporting subreddits...")
    subreddits_query = """
    MATCH (s:Subreddit)
    OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
    RETURN s.name as name,
           count(p) as post_count
    ORDER BY post_count DESC
    """
    
    subreddits_result = neo4j.execute_read(subreddits_query)
    subreddits_data = [
        {
            "name": record["name"],
            "post_count": record["post_count"],
        }
        for record in subreddits_result
    ]
    
    df_subreddits = pd.DataFrame(subreddits_data)
    subreddits_file = output_dir / "subreddits.parquet"
    table = pa.Table.from_pandas(df_subreddits)
    write_table(table, subreddits_file)
    print(f"  Saved {len(df_subreddits)} subreddits to {subreddits_file}")
    
    # Export Posts
    print("Exporting posts...")
    posts_query = """
    MATCH (p:Post)
    OPTIONAL MATCH (u:User)-[:POSTED]->(p)
    RETURN p.id as id,
           p.title as title,
           p.created_utc as created_utc,
           p.score as score,
           p.num_comments as num_comments,
           p.upvote_ratio as upvote_ratio,
           p.over_18 as over_18,
           p.url as url,
           p.selftext as selftext,
           p.permalink as permalink,
           p.subreddit as subreddit,
           u.username as author,
           p.is_image as is_image,
           p.image_url as image_url
    ORDER BY p.created_utc DESC
    """
    
    posts_result = neo4j.execute_read(posts_query)
    posts_data = [
        {
            "id": record["id"],
            "title": record["title"],
            "created_utc": record["created_utc"],
            "score": record["score"],
            "num_comments": record["num_comments"],
            "upvote_ratio": record["upvote_ratio"],
            "over_18": record["over_18"],
            "url": record["url"],
            "selftext": record["selftext"],
            "permalink": record["permalink"],
            "subreddit": record["subreddit"],
            "author": record["author"],
            "is_image": record["is_image"],
            "image_url": record["image_url"],
        }
        for record in posts_result
    ]
    
    df_posts = pd.DataFrame(posts_data)
    if 'created_utc' in df_posts.columns:
        df_posts['created_utc'] = pd.to_datetime(df_posts['created_utc'], unit='s', errors='coerce')
    posts_file = output_dir / "posts.parquet"
    table = pa.Table.from_pandas(df_posts)
    write_table(table, posts_file)
    
    # Export Comments
    print("\nExporting comments...")
    comments_query = """
    MATCH (c:Comment)-[:REPLIED_TO]->(p:Post)
    OPTIONAL MATCH (s:Subreddit)<-[:POSTED_IN]->(p)
    RETURN c.id as id,
           c.body as body,
           c.author as author,
           c.score as score,
           c.depth as depth,
           c.is_submitter as is_submitter,
           c.created_utc as created_utc,
           c.link_id as link_id,
           p.subreddit as subreddit,
           p.title as post_title
    ORDER BY c.created_utc DESC
    LIMIT 100000
    """
    
    comments_result = neo4j.execute_read(comments_query)
    comments_data = [
        {
            "id": record["id"],
            "body": record["body"],
            "author": record["author"],
            "score": record["score"],
            "depth": record["depth"],
            "is_submitter": record["is_submitter"],
            "created_utc": record["created_utc"],
            "link_id": record["link_id"],
            "subreddit": record["subreddit"],
            "post_title": record["post_title"],
        }
        for record in comments_result
    ]
    
    df_comments = pd.DataFrame(comments_data)
    if 'created_utc' in df_comments.columns:
        df_comments['created_utc'] = pd.to_datetime(df_comments['created_utc'], unit='s', errors='coerce')
    comments_file = output_dir / "comments.parquet"
    table = pa.Table.from_pandas(df_comments)
    write_table(table, comments_file)
    print(f"  Saved {len(df_comments)} comments to {comments_file}")
    
    # Export Images with local paths
    print("\nExporting images...")
    images_query = """
    MATCH (p:Post)-[:HAS_IMAGE]->(i:Image)
    WHERE i.image_path IS NOT NULL
    RETURN i.url as url,
           i.image_path as image_path,
           p.subreddit as subreddit,
           p.title as post_title,
           p.id as post_id
    ORDER BY p.created_utc DESC
    """
    
    images_result = neo4j.execute_read(images_query)
    images_data = [
        {
            "url": record["url"],
            "image_path": record["image_path"],
            "subreddit": record["subreddit"],
            "post_title": record["post_title"],
            "post_id": record["post_id"],
        }
        for record in images_result
    ]
    
    df_images = pd.DataFrame(images_data)
    images_file = output_dir / "images.parquet"
    table = pa.Table.from_pandas(df_images)
    write_table(table, images_file)
    print(f"  Saved {len(df_images)} images to {images_file}")
    
    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"\nDatasets created:")
    print(f"  {output_dir / 'subreddits.parquet'} - {len(df_subreddits)} subreddits")
    print(f"  {output_dir / 'posts.parquet'} - {len(df_posts)} posts")
    print(f"  {output_dir / 'comments.parquet'} - {len(df_comments)} comments")
    print(f"  {output_dir / 'images.parquet'} - {len(df_images)} images with local paths")
    print(f"\nTotal size: {output_dir.stat().st_size / (1024*1024):.1f} MB")


def main():
    parser = argparse.ArgumentParser(
        description="Export Reddit data from Neo4j to Parquet"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("datasets/parquet"),
        help="Output directory (default: datasets/parquet)"
    )
    
    args = parser.parse_args()
    
    create_parquet_export()


if __name__ == "__main__":
    sys.exit(main())
