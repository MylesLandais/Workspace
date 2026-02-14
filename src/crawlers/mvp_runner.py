import os
import datetime
from sources.reddit_public import RedditPublicJsonSource
from storage.minio_store import MinioStore

def main():
    # 1. Setup Storage
    minio_endpoint = os.getenv("MINIO_ENDPOINT", "localhost:9000")
    # Clean up endpoint if it has http schema, as Minio client expects host:port
    minio_endpoint = minio_endpoint.replace("http://", "").replace("https://", "")
    
    store = MinioStore(
        endpoint=minio_endpoint,
        access_key=os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        secret_key=os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        secure=False, # Dev env is usually insecure
        bucket="raw-reddit"
    )

    # 2. Setup Source
    source = RedditPublicJsonSource()

    # 3. Define Targets (Hardcoded for MVP)
    targets = ["nixos", "dataengineering"]

    print(f"Starting MVP Crawl for: {targets}")

    # 4. Execution Loop
    for target in targets:
        print(f"Fetching r/{target}...")
        try:
            items = source.fetch_feed(target, limit=50) # Small limit for test
            count = 0
            for item in items:
                post_id = item.get("id")
                created_utc = item.get("created_utc")
                
                if not post_id or created_utc is None:
                    print(f"Skipping item missing ID or timestamp in r/{target}.")
                    continue
                
                # Path Structure: raw-reddit/subreddit/YYYY-MM-DD/post_id.json.gz
                date_str = datetime.datetime.fromtimestamp(float(created_utc)).strftime('%Y-%m-%d')
                path = f"reddit/{target}/{date_str}/{post_id}.json"
                
                # Save
                saved_path = store.save_raw(item, path)
                count += 1
            
            print(f"Saved {count} items for r/{target}")
            
        except Exception as e:
            print(f"Failed to crawl {target}: {e}")

if __name__ == "__main__":
    main()
