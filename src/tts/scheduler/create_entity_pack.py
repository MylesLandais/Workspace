#!/usr/bin/env python3
"""
Create entity-based Reddit parquet packs.
Filters data by creator/entity slug and exports to parquet.
"""

import sys
import os
import tarfile
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict
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


def export_entity_pack(
    creator_slug: str,
    pack_name: Optional[str] = None,
    days_back: int = 30,
    output_dir: str = "packs",
    compress: bool = True,
) -> Dict:
    """
    Export Reddit entity data to parquet pack.
    
    Args:
        creator_slug: Creator/entity slug (e.g., 'jordyn-jones')
        pack_name: Custom pack name (default: reddit-{slug}-{date})
        days_back: Number of days of data to include
        output_dir: Directory to save pack
        compress: Whether to compress to tar.gz
    
    Returns:
        Dictionary with pack metadata
    """
    from feed.storage.neo4j_connection import get_connection
    
    # Setup paths
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    if pack_name is None:
        today = datetime.now().strftime("%Y-%m-%d")
        pack_name = f"reddit-{creator_slug}-{today}"
    
    pack_dir = output_path / pack_name
    pack_dir.mkdir(exist_ok=True)
    
    print(f"Creating Reddit entity pack: {pack_name}")
    print(f"  Creator: {creator_slug}")
    print(f"  Days back: {days_back}")
    print(f"  Output: {pack_dir}")
    
    # Connect to Neo4j
    neo4j = get_connection()
    
    # Calculate date range (epoch timestamp for Neo4j)
    to_date = datetime.utcnow()
    from_date = to_date - timedelta(days=days_back)
    from_date_timestamp = int(from_date.timestamp())
    
    metadata = {
        "pack_name": pack_name,
        "pack_type": "reddit-entity",
        "created_at": datetime.now().isoformat(),
        "date_range_days": days_back,
        "date_from": from_date.isoformat(),
        "date_to": to_date.isoformat(),
        "exported_at": datetime.now().isoformat(),
        "creator_slug": creator_slug,
    }
    
    # Export subreddits
    print("\\nQuerying subreddits...")
    subreddits_query = """
    MATCH (c:Creator {slug: $slug})-[:HAS_SOURCE]->(s:Subreddit)
    OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
    WHERE p.created_utc >= datetime({epochSeconds: $from_date_timestamp})
    RETURN 
        s.name as name,
        count(p) as post_count
    ORDER BY name
    """
    
    subreddits_result = neo4j.execute_read(
        subreddits_query,
        parameters={
            "slug": creator_slug,
            "from_date_timestamp": from_date_timestamp,
        }
    )
    
    subreddits_data = [
        {
            "name": record["name"],
            "post_count": record["post_count"] or 0,
        }
        for record in subreddits_result
    ]
    
    df_subreddits = pd.DataFrame(subreddits_data)
    if not df_subreddits.empty:
        subreddits_file = pack_dir / "subreddits.parquet"
        df_subreddits.to_parquet(subreddits_file, index=False)
        metadata["subreddit_count"] = len(df_subreddits)
        metadata["subreddits_file"] = "subreddits.parquet"
        print(f"  Exported {len(df_subreddits)} subreddits")
    else:
        print("  No subreddits found")
    
    # Export posts
    print("\\nQuerying posts...")
    posts_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE (p)-[:ABOUT]->(:Creator {slug: $slug})
       OR p.entity_matched = $entity_name
    AND p.created_utc >= datetime({epochSeconds: $from_date_timestamp})
    OPTIONAL MATCH (u:User)-[:POSTED]->(p)
    RETURN 
        p.id as id,
        p.title as title,
        p.created_utc as created_utc,
        p.score as score,
        p.num_comments as num_comments,
        p.upvote_ratio as upvote_ratio,
        p.over_18 as over_18,
        p.url as url,
        p.permalink as permalink,
        p.selftext as selftext,
        u.username as author,
        p.entity_matched as entity_matched,
        s.name as subreddit
    ORDER BY p.created_utc DESC
    """
    
    posts_result = neo4j.execute_read(
        posts_query,
        parameters={
            "slug": creator_slug,
            "entity_name": creator_slug.replace("-", " ").title(),
            "from_date_timestamp": from_date_timestamp,
        }
    )
    
    posts_data = [
        {
            "id": record["id"],
            "title": record["title"],
            "created_utc": str(record["created_utc"]),
            "score": record["score"],
            "num_comments": record["num_comments"],
            "upvote_ratio": record["upvote_ratio"],
            "over_18": record["over_18"],
            "url": record["url"],
            "permalink": record["permalink"],
            "selftext": record["selftext"],
            "author": record["author"],
            "entity_matched": record.get("entity_matched"),
            "subreddit": record["subreddit"],
        }
        for record in posts_result
    ]
    
    df_posts = pd.DataFrame(posts_data)
    if not df_posts.empty:
        posts_file = pack_dir / "posts.parquet"
        df_posts.to_parquet(posts_file, index=False)
        metadata["post_count"] = len(df_posts)
        metadata["posts_file"] = "posts.parquet"
        print(f"  Exported {len(df_posts)} posts")
    else:
        print("  No posts found")
    
    # Export images (post URLs with images)
    print("\\nQuerying images...")
    images_query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE (p)-[:ABOUT]->(:Creator {slug: $slug})
       OR p.entity_matched = $entity_name
    AND p.created_utc >= datetime({epochSeconds: $from_date_timestamp})
    AND p.url IS NOT NULL
    RETURN 
        p.id as post_id,
        p.url as image_url,
        s.name as subreddit,
        p.title as title,
        p.created_utc as created_utc,
        p.score as score
    ORDER BY p.created_utc DESC
    """
    
    images_result = neo4j.execute_read(
        images_query,
        parameters={
            "slug": creator_slug,
            "entity_name": creator_slug.replace("-", " ").title(),
            "from_date_timestamp": from_date_timestamp,
        }
    )
    
    images_data = [
        {
            "post_id": record["post_id"],
            "image_url": record["image_url"],
            "subreddit": record["subreddit"],
            "title": record["title"],
            "created_utc": str(record["created_utc"]),
            "score": record["score"],
        }
        for record in images_result
    ]
    
    df_images = pd.DataFrame(images_data)
    if not df_images.empty:
        images_file = pack_dir / "images.parquet"
        df_images.to_parquet(images_file, index=False)
        metadata["image_count"] = len(df_images)
        metadata["images_file"] = "images.parquet"
        print(f"  Exported {len(df_images)} images")
    else:
        print("  No images found")
    
    # Write metadata
    metadata_file = pack_dir / "metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2, default=str)
    print(f"\\nWrote metadata: {metadata_file}")
    
    # Compress if requested
    archive_path = None
    if compress:
        print(f"\\nCompressing to {pack_name}.tar.gz...")
        archive_path = output_path / f"{pack_name}.tar.gz"
        with tarfile.open(archive_path, "w:gz") as tar:
            for item in pack_dir.iterdir():
                tar.add(item, arcname=item.name)
        archive_size = archive_path.stat().st_size
        metadata["archive_file"] = f"{pack_name}.tar.gz"
        metadata["archive_size_bytes"] = archive_size
        print(f"  Archive size: {archive_size:,} bytes ({archive_size / (1024**2):.1f} MB)")
    
    print(f"\\nPack created successfully!")
    if archive_path:
        print(f"  Archive: {archive_path}")
    else:
        print(f"  Directory: {pack_dir}")
    
    return metadata


def list_packs(output_dir: str = "packs"):
    """List available entity packs."""
    output_path = Path(output_dir)
    
    packs = []
    for item in output_path.glob("reddit-*-*.tar.gz"):
        pack_name = item.stem
        try:
            metadata_file = output_path / pack_name / "metadata.json"
            if metadata_file.exists():
                with open(metadata_file, "r") as f:
                    metadata = json.load(f)
                packs.append((pack_name, metadata))
        except:
            packs.append((pack_name, {}))
    
    return sorted(packs, key=lambda x: x[0], reverse=True)


def main():
    parser = argparse.ArgumentParser(
        description="Create entity-based Reddit parquet packs"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command")
    
    # Create command
    create_parser = subparsers.add_parser("create", help="Create an entity pack")
    create_parser.add_argument(
        "creator_slug",
        help="Creator/entity slug (e.g., jordyn-jones)"
    )
    create_parser.add_argument(
        "--pack-name",
        help="Custom pack name"
    )
    create_parser.add_argument(
        "--days-back",
        type=int,
        default=30,
        help="Number of days of data (default: 30)"
    )
    create_parser.add_argument(
        "--output-dir",
        default="packs",
        help="Output directory (default: packs)"
    )
    create_parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Don't compress to tar.gz"
    )
    
    # List command
    list_parser = subparsers.add_parser("list", help="List available packs")
    list_parser.add_argument(
        "--output-dir",
        default="packs",
        help="Pack directory (default: packs)"
    )
    
    args = parser.parse_args()
    
    if args.command == "create":
        export_entity_pack(
            creator_slug=args.creator_slug,
            pack_name=args.pack_name,
            days_back=args.days_back,
            output_dir=args.output_dir,
            compress=not args.no_compress,
        )
    
    elif args.command == "list":
        packs = list_packs(args.output_dir)
        
        if not packs:
            print(f"No entity packs found in {args.output_dir}")
            return
        
        print("Available entity packs:")
        for pack_name, metadata in packs:
            creator = metadata.get("creator_slug", "?")
            posts = metadata.get("post_count", "?")
            subreddits = metadata.get("subreddit_count", "?")
            print(f"  {pack_name}")
            print(f"    Creator: {creator}, Posts: {posts}, Subreddits: {subreddits}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
