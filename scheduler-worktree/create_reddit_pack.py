"""Create nightly parquet packs from Reddit monitoring data."""

import sys
import os
import tarfile
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import argparse
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import pandas as pd
    import pyarrow as pa
    from pyarrow.parquet import write_table
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Install with: pip install pandas pyarrow")
    raise

from feed.storage.neo4j_connection import get_connection


def compute_date_filter(days: int) -> Dict[str, datetime]:
    """Compute date filters for N days ago."""
    now = datetime.now()
    cutoff = now - timedelta(days=days)
    return {
        "now": now,
        "cutoff": cutoff,
    }


def export_reddit_data(
    output_dir: Path,
    days: int = 30,
    include_comments: bool = True,
    include_images: bool = True,
    limit_comments: int = 100000,
    creator_slug: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Export Reddit data from Neo4j to parquet.
    
    Args:
        output_dir: Output directory for parquet files
        days: Number of days to include (default: 30)
        include_comments: Include comments
        include_images: Include images
        limit_comments: Maximum comments to export
        creator_slug: Filter by creator/entity slug
    
    Returns:
        Dictionary with export metadata
    """
    dates = compute_date_filter(days)
    
    print("=" * 70)
    print(f"EXPORTING REDDIT DATA (PAST {days} DAYS)")
    print("=" * 70)
    print(f"Output directory: {output_dir.absolute()}")
    print(f"Date range: {dates['cutoff']} to {dates['now']}")
    if creator_slug:
        print(f"Creator filter: {creator_slug}")
    print()
    
    neo4j = get_connection()
    
    metadata = {
        "exported_at": datetime.now().isoformat(),
        "date_range_days": days,
        "date_from": dates["cutoff"].isoformat(),
        "date_to": dates["now"].isoformat(),
    }
    
    # Export Subreddits
    print("Exporting subreddits...")
    subreddits_query = """
    MATCH (s:Subreddit)
    OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
    WHERE p.title IS NOT NULL
    RETURN s.name as name,
           count(p) as post_count
    ORDER BY post_count DESC
    """
    
    subreddits_result = neo4j.execute_read(
        subreddits_query,
        parameters={"cutoff": dates["cutoff"].isoformat()}
    )
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
    
    metadata["subreddit_count"] = len(df_subreddits)
    metadata["subreddits_file"] = str(subreddits_file.name)
    
    # Export Posts
    print("\nExporting posts...")
    posts_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
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
           s.name as subreddit,
           u.username as author,
           p.is_image as is_image,
           p.image_url as image_url
    ORDER BY p.created_utc DESC
    """
    
    posts_result = neo4j.execute_read(
        posts_query,
        parameters={}
    )
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
    print(f"  Saved {len(df_posts)} posts to {posts_file}")
    
    metadata["post_count"] = len(df_posts)
    metadata["posts_file"] = str(posts_file.name)
    
    if include_comments:
        print("\nExporting comments...")
        comments_query = """
        MATCH (c:Comment)-[:REPLIED_TO]->(p:Post)
        WHERE c.created_utc >= $cutoff_timestamp
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
        LIMIT $limit
        """
        
        comments_result = neo4j.execute_read(
            comments_query,
            parameters={"cutoff_timestamp": int(dates["cutoff"].timestamp()), "limit": limit_comments}
        )
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
        
        metadata["comment_count"] = len(df_comments)
        metadata["comments_file"] = str(comments_file.name)
    
    if include_images:
        print("\nExporting images...")
        images_query = """
        MATCH (p:Post)-[:HAS_IMAGE]->(i:Image)
        WHERE p.created_at >= datetime($cutoff)
          AND i.image_path IS NOT NULL
        RETURN i.url as url,
               i.image_path as image_path,
               p.subreddit as subreddit,
               p.title as post_title,
               p.id as post_id
        ORDER BY p.created_utc DESC
        """
        
        images_result = neo4j.execute_read(
            images_query,
            parameters={"cutoff": dates["cutoff"].isoformat()}
        )
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
        
        metadata["image_count"] = len(df_images)
        metadata["images_file"] = str(images_file.name)
    
    print("\n" + "=" * 70)
    print("EXPORT COMPLETE")
    print("=" * 70)
    print(f"\nDatasets created in: {output_dir.absolute()}")
    print(f"  {subreddits_file.name} - {len(df_subreddits)} subreddits")
    print(f"  {posts_file.name} - {len(df_posts)} posts")
    if include_comments:
        print(f"  {comments_file.name} - {len(df_comments)} comments")
    if include_images:
        print(f"  {images_file.name} - {len(df_images)} images with local paths")
    
    return metadata


def create_reddit_pack(
    days: int = 30,
    output_dir: Path = None,
    pack_name: Optional[str] = None,
    compress: bool = True,
    include_comments: bool = True,
    include_images: bool = True,
) -> Dict[str, Any]:
    """
    Create a Reddit nightly pack.
    
    Args:
        days: Number of days to include
        output_dir: Output directory for pack
        pack_name: Custom pack name (default: reddit-nightly-YYYY-MM-DD)
        compress: Compress output tarball
        include_comments: Include comments
        include_images: Include images
    
    Returns:
        Dictionary with pack metadata
    """
    if pack_name is None:
        pack_name = f"reddit-nightly-{datetime.now().strftime('%Y-%m-%d')}"
    
    if output_dir is None:
        output_dir = Path("packs")
    
    pack_dir = output_dir / pack_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(f"CREATING REDDIT NIGHTLY PACK: {pack_name}")
    print("=" * 70)
    print(f"Time window: Past {days} days")
    print()
    
    export_metadata = export_reddit_data(
        output_dir=pack_dir,
        days=days,
        include_comments=include_comments,
        include_images=include_images,
    )
    
    pack_metadata = {
        "pack_name": pack_name,
        "pack_type": "reddit",
        "created_at": datetime.now().isoformat(),
        "date_range_days": days,
        "date_from": export_metadata["date_from"],
        "date_to": export_metadata["date_to"],
        **export_metadata,
    }
    
    metadata_file = pack_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(pack_metadata, f, indent=2)
    print(f"\nSaved pack metadata to {metadata_file}")
    
    if compress:
        print(f"\nCreating archive...")
        archive_name = f"{pack_name}.tar.gz"
        archive_path = output_dir / archive_name
        
        with tarfile.open(archive_path, "w:gz") as tar:
            for file_path in pack_dir.rglob("*"):
                if file_path.is_file() and file_path != archive_path:
                    tar.add(file_path, arcname=file_path.relative_to(pack_dir))
        
        archive_size = archive_path.stat().st_size
        print(f"Created archive: {archive_path}")
        print(f"Archive size: {archive_size / (1024*1024):.1f} MB")
        
        pack_metadata["archive_file"] = str(archive_path.relative_to(output_dir))
        pack_metadata["archive_size_bytes"] = archive_size
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(pack_metadata, f, indent=2)
    
    print("\n" + "=" * 70)
    print("REDDIT NIGHTLY PACK COMPLETE")
    print("=" * 70)
    print(f"\nPack: {pack_name}")
    print(f"Location: {pack_dir.absolute()}")
    print(f"Time window: Past {days} days")
    print(f"  Subreddits: {pack_metadata.get('subreddit_count', 0)}")
    print(f"  Posts: {pack_metadata.get('post_count', 0)}")
    if include_comments:
        print(f"  Comments: {pack_metadata.get('comment_count', 0)}")
    if include_images:
        print(f"  Images: {pack_metadata.get('image_count', 0)}")
    if compress:
        print(f"  Archive: {pack_metadata.get('archive_file', 'N/A')}")
        print(f"  Archive size: {pack_metadata.get('archive_size_bytes', 0) / (1024*1024):.1f} MB")
    
    return pack_metadata


def analyze_pack(pack_dir: Path) -> None:
    """Analyze an existing reddit pack."""
    print("=" * 70)
    print("ANALYZING REDDIT PACK")
    print("=" * 70)
    print(f"Pack directory: {pack_dir.absolute()}")
    print()
    
    metadata_file = pack_dir / "metadata.json"
    if metadata_file.exists():
        with open(metadata_file, "r", encoding="utf-8") as f:
            metadata = json.load(f)
        
        print("Pack Metadata:")
        for key, value in metadata.items():
            print(f"  {key}: {value}")
        print()
    
    print("Data Analysis:")
    
    if (pack_dir / "subreddits.parquet").exists():
        df_subreddits = pd.read_parquet(pack_dir / "subreddits.parquet")
        print(f"\nSubreddits: {len(df_subreddits)}")
        print("\nTop subreddits by post count:")
        print(df_subreddits.sort_values('post_count', ascending=False).to_string(index=False))
    
    if (pack_dir / "posts.parquet").exists():
        df_posts = pd.read_parquet(pack_dir / "posts.parquet")
        df_posts['date'] = pd.to_datetime(df_posts['created_utc'])
        
        print(f"\nPosts: {len(df_posts)}")
        print("\nPosts by date:")
        by_date = df_posts.groupby(df_posts['date'].dt.date).size()
        print(by_date.to_string())
        
        print("\nPosts by subreddit:")
        by_subreddit = df_posts.groupby('subreddit').agg({
            'id': 'count',
            'score': 'mean',
            'num_comments': 'mean'
        }).rename(columns={'id': 'count'}).sort_values('count', ascending=False)
        print(by_subreddit.to_string())
        
        print("\nTop posts by score:")
        top_posts = df_posts.nlargest(10, 'score')[['title', 'subreddit', 'score', 'num_comments', 'date']]
        print(top_posts.to_string(index=False))


def main():
    parser = argparse.ArgumentParser(
        description="Create nightly parquet packs from Reddit monitoring data"
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to include (default: 30)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("packs"),
        help="Output directory for packs (default: packs)"
    )
    parser.add_argument(
        "--pack-name",
        type=str,
        default=None,
        help="Custom pack name (default: reddit-nightly-YYYY-MM-DD)"
    )
    parser.add_argument(
        "--no-comments",
        action="store_true",
        help="Don't include comments"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Don't include images"
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Don't compress output tarball"
    )
    parser.add_argument(
        "--analyze",
        type=Path,
        metavar="PACK_DIR",
        help="Analyze existing pack directory"
    )
    
    args = parser.parse_args()
    
    if args.analyze:
        analyze_pack(args.analyze)
        return
    
    create_reddit_pack(
        days=args.days,
        output_dir=args.output_dir,
        pack_name=args.pack_name,
        compress=not args.no_compress,
        include_comments=not args.no_comments,
        include_images=not args.no_images,
    )


if __name__ == "__main__":
    sys.exit(main())
