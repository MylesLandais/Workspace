#!/usr/bin/env python3
"""
Alien Dataset Utility - For interns

Usage:
    python alien_dataset.py poll --subreddit NAME
    python alien_dataset.py rebuild
    python alien_dataset.py add --entity NAME --subreddits "r1,r2,r3"
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter
from feed.storage.neo4j_connection import get_connection


def cmd_poll(args):
    """Poll a subreddit for new posts."""
    neo4j = get_connection()
    reddit = RedditAdapter(mock=False, delay_min=5.0, delay_max=15.0)
    cutoff = datetime.now() - timedelta(hours=24)
    
    print(f"Polling r/{args.subreddit}...")
    posts, after = [], None
    page = 0
    new_count = 0
    
    while page < 5:
        page += 1
        fetched, after = reddit.fetch_posts(
            source=args.subreddit, sort="new", limit=100, after=after
        )
        if not fetched:
            break
        
        for p in fetched:
            if p.created_utc < cutoff:
                break
            # Check if exists
            exists = neo4j.execute_read(
                "MATCH (p:Post {id: $id}) RETURN p.id",
                parameters={"id": p.id}
            )
            if not list(exists):
                # Store post
                neo4j.execute_write("""
                    MERGE (post:Post {id: $id})
                    SET post.title = $title, post.created_utc = datetime({epochSeconds: $ts}),
                        post.score = $score, post.url = $url, post.permalink = $permalink,
                        post.subreddit = $subreddit, post.updated_at = datetime()
                    WITH post
                    MERGE (s:Subreddit {name: $subreddit})
                    ON CREATE SET s.created_at = datetime()
                    MERGE (post)-[:POSTED_IN]->(s)
                """, {
                    "id": p.id, "title": p.title, "ts": int(p.created_utc.timestamp()),
                    "score": p.score, "url": p.url, "permalink": p.permalink,
                    "subreddit": p.subreddit
                })
                new_count += 1
        
        if not after:
            break
    
    print(f"Added {new_count} new posts from r/{args.subreddit}")
    return new_count


def cmd_add(args):
    """Add new entity with subreddits."""
    neo4j = get_connection()
    entity_name = args.entity
    entity_slug = entity_name.lower().replace(" ", "-")
    subreddits = [s.strip() for s in args.subreddits.split(",")]
    
    print(f"Adding entity: {entity_name} ({entity_slug})")
    print(f"Subreddits: {', '.join([f'r/{s}' for s in subreddits])}")
    
    # Create entity
    neo4j.execute_write("""
        MERGE (c:Creator {slug: $slug})
        ON CREATE SET c.uuid = $uuid, c.name = $name, c.slug = $slug, c.created_at = datetime()
    """, {"slug": entity_slug, "uuid": str(uuid4()), "name": entity_name})
    
    # Link subreddits
    for sub in subreddits:
        neo4j.execute_write("""
            MATCH (c:Creator {slug: $slug})
            MERGE (s:Subreddit {name: $sub})
            ON CREATE SET s.created_at = datetime()
            MERGE (c)-[:HAS_SOURCE]->(s)
        """, {"slug": entity_slug, "sub": sub})
        print(f"  Linked r/{sub}")
    
    print(f"Done! Added {len(subreddits)} subreddits")


def cmd_rebuild():
    """Rebuild the unified reddit-all parquet."""
    from datetime import datetime
    import json
    import shutil
    import pandas as pd
    import pyarrow as pa
    from pyarrow.parquet import write_table
    
    print("Rebuilding reddit-all dataset...")
    
    neo4j = get_connection()
    project_root = Path(__file__).parent
    pack_dir = project_root / "packs" / "reddit-all"
    if pack_dir.exists():
        shutil.rmtree(pack_dir)
    pack_dir.mkdir(parents=True, exist_ok=True)
    
    # Load comments by post
    comments_by_post = {}
    for r in neo4j.execute_read("""
        MATCH (c:Comment)-[:REPLIED_TO]->(p:Post)
        WITH p, collect({id: c.id, body: c.body, author: c.author, score: c.score, depth: c.depth, created_utc: c.created_utc}) as comments
        RETURN p.id as post_id, comments
    """):
        if r["post_id"]:
            comments_by_post[r["post_id"]] = r["comments"]
    print(f"  Loaded comments for {len(comments_by_post)} posts")
    
    # Load images by post
    images_by_post = {}
    for r in neo4j.execute_read("""
        MATCH (p:Post)-[:HAS_IMAGE]->(i:Image)
        WITH p, collect({url: i.url, path: i.image_path, sha256: i.sha256, dhash: i.dhash, width: i.width, height: i.height}) as images
        RETURN p.id as post_id, images
    """):
        if r["post_id"]:
            images_by_post[r["post_id"]] = r["images"]
    print(f"  Loaded images for {len(images_by_post)} posts")
    
    # Load all posts
    posts = list(neo4j.execute_read("""
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
        OPTIONAL MATCH (p)-[:ABOUT]->(c:Creator)
        OPTIONAL MATCH (u:User)-[:POSTED]->(p)
        RETURN p.id as id, p.title as title, p.created_utc as created_utc, p.score as score,
               p.num_comments as num_comments, p.upvote_ratio as upvote_ratio, p.over_18 as over_18,
               p.url as url, p.selftext as selftext, p.permalink as permalink, s.name as subreddit,
               u.username as author, c.name as entity, c.slug as entity_slug, p.image_hash as image_hash
        ORDER BY p.created_utc DESC
    """))
    print(f"  Total posts: {len(posts)}")
    
    # Build records
    records = []
    for r in posts:
        post_id = r["id"]
        
        # Process comments
        clean_comments = []
        for c in comments_by_post.get(post_id, []):
            if not c: continue
            ts = c.get("created_utc") if c else None
            ts_int = int(ts) if isinstance(ts, (int, float)) else 0
            clean_comments.append({
                "id": c.get("id"), "body": c.get("body"), "author": c.get("author"),
                "score": int(c.get("score")) if c and c.get("score") else 0,
                "depth": int(c.get("depth")) if c and c.get("depth") else 0, "created_utc": ts_int,
            })
        
        # Process images
        clean_images = []
        for img in images_by_post.get(post_id, []):
            if not img: continue
            clean_images.append({
                "url": img.get("url"), "path": img.get("path"), "sha256": img.get("sha256"),
                "dhash": img.get("dhash"), "width": int(img.get("width")) if img and img.get("width") else None,
                "height": int(img.get("height")) if img and img.get("height") else None,
            })
        
        records.append({
            "id": r["id"], "title": r["title"], "created_utc": r["created_utc"], "score": r["score"],
            "num_comments": r["num_comments"], "upvote_ratio": r["upvote_ratio"], "over_18": r["over_18"],
            "url": r["url"], "selftext": r["selftext"], "permalink": r["permalink"], "subreddit": r["subreddit"],
            "author": r["author"], "entity": r["entity"], "entity_slug": r["entity_slug"], "image_hash": r["image_hash"],
            "comments": clean_comments, "images": clean_images,
        })
    
    # Write parquet
    df = pd.DataFrame(records)
    if "created_utc" in df.columns and len(df) > 0:
        df["created_utc"] = pd.to_datetime(df["created_utc"], unit="s", errors="coerce")
    
    schema = pa.schema([
        ("id", pa.string()), ("title", pa.string()), ("created_utc", pa.timestamp("us")), ("score", pa.int64()),
        ("num_comments", pa.int64()), ("upvote_ratio", pa.float64()), ("over_18", pa.bool_()), ("url", pa.string()),
        ("selftext", pa.string()), ("permalink", pa.string()), ("subreddit", pa.string()), ("author", pa.string()),
        ("entity", pa.string()), ("entity_slug", pa.string()), ("image_hash", pa.string()),
        ("comments", pa.list_(pa.struct([
            ("id", pa.string()), ("body", pa.string()), ("author", pa.string()), ("score", pa.int64()),
            ("depth", pa.int64()), ("created_utc", pa.int64())]))),
        ("images", pa.list_(pa.struct([
            ("url", pa.string()), ("path", pa.string()), ("sha256", pa.string()), ("dhash", pa.string()),
            ("width", pa.int64()), ("height", pa.int64())]))),
    ])
    
    table = pa.Table.from_pandas(df, schema=schema)
    parquet_file = pack_dir / "reddit.parquet"
    write_table(table, parquet_file)
    print(f"  Saved: reddit.parquet ({parquet_file.stat().st_size / 1024:.1f} KB)")
    
    # Copy images
    images_dir = pack_dir / "images"
    images_dir.mkdir(exist_ok=True)
    images_copied = 0
    for img_list in images_by_post.values():
        for img in img_list:
            if img and img.get("path"):
                src = Path(img["path"])
                if src.exists():
                    dst = images_dir / src.name
                    try:
                        shutil.copy2(src, dst)
                        images_copied += 1
                    except: pass
    print(f"  Images copied: {images_copied}")
    
    # Metadata
    subreddits = [r["name"] for r in neo4j.execute_read("MATCH (s:Subreddit) RETURN s.name as name")]
    entities = [{"name": r["name"], "slug": r["slug"]} for r in neo4j.execute_read("MATCH (c:Creator) RETURN c.name as name, c.slug as slug")]
    
    metadata = {
        "pack_name": "reddit-all", "domain": "reddit", "created_at": datetime.now().isoformat(),
        "description": "Single unified Reddit dataset", "statistics": {
            "total_posts": len(df), "total_comments": sum(len(c) for c in df["comments"]),
            "total_images": sum(len(i) for i in df["images"]),
        }, "subreddits": {"count": len(subreddits), "list": subreddits},
        "entities": {"count": len(entities), "list": entities},
        "files": {"main_parquet": "reddit.parquet", "images_folder": "images/"},
        "image_files_copied": images_copied,
    }
    
    with open(pack_dir / "metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print(f"\nDone! Pack at: {pack_dir}")
    print(f"Subreddits: {len(subreddits)}, Entities: {len(entities)}")


def main():
    parser = argparse.ArgumentParser(description="Alien Dataset Utility")
    subparsers = parser.add_subparsers()
    
    # Poll command
    poll = subparsers.add_parser("poll", help="Poll a subreddit for new posts")
    poll.add_argument("--subreddit", required=True, help="Subreddit name")
    poll.set_defaults(cmd=cmd_poll)
    
    # Add command
    add = subparsers.add_parser("add", help="Add new entity with subreddits")
    add.add_argument("--entity", required=True, help="Entity name")
    add.add_argument("--subreddits", required=True, help="Comma-separated subreddits")
    add.set_defaults(cmd=cmd_add)
    
    # Rebuild command
    rebuild = subparsers.add_parser("rebuild", help="Rebuild the unified dataset")
    rebuild.set_defaults(cmd=lambda _: cmd_rebuild())
    
    args = parser.parse_args()
    
    if hasattr(args, "cmd"):
        args.cmd(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
