
import json
import os
from pathlib import Path
from datetime import datetime
import sys

# Add project root and src to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection

def import_reddit_data():
    env_file = project_root / ".env.docker" if (project_root / ".env.docker").exists() else None
    neo4j = get_connection(env_file)
    reddit_data_dir = project_root / "data" / "reddit"
    
    if not reddit_data_dir.exists():
        print("No reddit data directory found.")
        return

    # Find all JSON files in the reddit data directory
    json_files = list(reddit_data_dir.glob("**/*.json"))
    print(f"Found {len(json_files)} metadata files.")

    for json_file in json_files:
        print(f"Processing {json_file.name}...")
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        # Determine image path if available
        image_name = json_file.stem + ".jpeg"
        if not (json_file.parent / image_name).exists():
            # Try other extensions or specific names from metadata
            image_name = json_file.stem + ".jpg"
            if not (json_file.parent / image_name).exists():
                image_name = json_file.stem + ".mp4"
                if not (json_file.parent / image_name).exists():
                    # Check for gallery images in metadata
                    if "images_downloaded" in data:
                        image_name = data["images_downloaded"][0]
                    else:
                        image_name = None
        
        image_path = str(json_file.parent / image_name) if image_name and (json_file.parent / image_name).exists() else None


        # Insert post
        neo4j.execute_write("""
            MERGE (post:Post {id: $id})
            SET post.title = $title, 
                post.created_utc = datetime({epochSeconds: $ts}),
                post.score = $score, 
                post.url = $url, 
                post.permalink = $permalink,
                post.subreddit = $subreddit, 
                post.selftext = $selftext,
                post.updated_at = datetime(),
                post.is_image = true
            WITH post
            MERGE (s:Subreddit {name: $subreddit})
            ON CREATE SET s.created_at = datetime()
            MERGE (post)-[:POSTED_IN]->(s)
            RETURN post
        """, {
            "id": data["id"],
            "title": data["title"],
            "ts": int(data.get("created_utc", datetime.now().timestamp())),
            "score": data.get("score", 0),
            "url": data["url"],
            "permalink": data["permalink"],
            "subreddit": data["subreddit"],
            "selftext": data.get("selftext", "")
        })

        # Insert image if path exists
        if image_path:
            neo4j.execute_write("""
                MATCH (p:Post {id: $post_id})
                MERGE (i:Image {url: $url})
                SET i.image_path = $path,
                    i.updated_at = datetime()
                MERGE (p)-[:HAS_IMAGE]->(i)
            """, {
                "post_id": data["id"],
                "url": data["url"],
                "path": image_path
            })
            print(f"  Linked image: {image_path}")

    print("Import complete.")

if __name__ == "__main__":
    import_reddit_data()
