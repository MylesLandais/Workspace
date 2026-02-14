import os
import sys
import time
import json
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path (needed because script is in subdirectory 'workers/')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import standalone repository classes (decoupled from legacy 'src/feed')
from crawling_system.storage.mysql_repo import MySQLRepository
from crawling_system.storage.minio_store import MinioStore
from crawling_system.sources.reddit_public import RedditPublicJsonSource
from crawling_system.storage.valkey_repo import get_connection as get_valkey_connection

# Configuration
QUEUE_KEY = "queue:pending_crawls"
DEDUP_CACHE_KEY = "cache:seen_ids"
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "minio:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = "raw-reddit"
CRAWL_LIMIT_PER_JOB = int(os.getenv("CRAWL_LIMIT_PER_JOB", 200))
POLL_TIMEOUT = 5 # Seconds to block on Valkey BLPOP

def run_consumer():
    """
    The main worker loop. Pulls jobs from Valkey and executes crawl.
    """
    print("Starting Consumer Worker.")
    
    # Init storage and source components
    source = RedditPublicJsonSource()
    
    # MinioStore uses internal logic which needs .env, let's check if it handles env vars
    # For now, let's use simple initialization assuming standard defaults
    try:
        store = MinioStore(
            endpoint=MINIO_ENDPOINT,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            bucket=MINIO_BUCKET
        )
        print(f"Connected to MinIO at {MINIO_ENDPOINT}")
    except Exception as e:
        print(f"CRITICAL: Failed to connect to MinIO: {e}")
        # Non-fatal if we only want to test extraction, MinIO is L phase
        store = None

    # Connect to Control Plane
    try:
        mysql_repo = MySQLRepository()
        print("Connected to MySQL Control Plane.")
    except Exception as e:
        print(f"CRITICAL: Failed to connect to MySQL: {e}")
        return

    # Connect to Valkey
    try:
        valkey_client = get_valkey_connection().client
        print("Connected to Valkey.")
    except Exception as e:
        print(f"CRITICAL: Failed to connect to Valkey: {e}")
        return

    try:
        while True:
            # 1. Block and Pop Job from Queue
            # BLPOP returns (key, value) or None
            job_data = valkey_client.blpop(QUEUE_KEY, timeout=POLL_TIMEOUT)
            
            if not job_data:
                # print("Waiting for job...")
                continue
                
            queue_name, job_payload_raw = job_data
            job_payload: Dict[str, Any] = json.loads(job_payload_raw)
            
            target_id = job_payload["target_id"]
            target_type = job_payload["target_type"]
            target_value = job_payload["target_value"]
            
            print(f"\n--- Processing Job {target_id}: {target_type}/{target_value} ---")
            
            items_collected = 0
            minio_path = ""
            error_message: Optional[str] = None
            job_status = "COMPLETED"
            job_id: Optional[int] = None

            try:
                # 2. Log Job Start in MySQL Control Plane
                job_id = mysql_repo.log_job_start(target_id)
                print(f"Logged job start with ID: {job_id}")

                # 3. Execute Crawl (currently only supports 'subreddit')
                if target_type != "subreddit":
                    raise NotImplementedError(f"Target type '{target_type}' is not yet implemented.")
                    
                items_generator = source.fetch_feed(target_value, limit=CRAWL_LIMIT_PER_JOB)
                
                # 4. Process and Store Items
                for item in items_generator:
                    post_id = item.get("id")
                    created_utc = item.get("created_utc")

                    if not post_id or created_utc is None:
                        continue
                        
                    # Check Deduplication Cache (Valkey Set)
                    dedup_key = f"{target_type}:{post_id}"
                    if valkey_client.sismember(DEDUP_CACHE_KEY, dedup_key):
                        # print(f"  -> Skipping duplicate: {post_id}")
                        continue
                    
                    # Store Item to MinIO
                    if store:
                        date_str = datetime.datetime.fromtimestamp(float(created_utc)).strftime('%Y-%m-%d')
                        
                        # Store to a unique path for the job/target
                        path_key = f"reddit/{target_value}/{date_str}/{post_id}.json"
                        
                        store.save_raw(item, path_key)
                        minio_path = path_key # Store last path as representative for audit
                    
                    # Update cache and counters
                    valkey_client.sadd(DEDUP_CACHE_KEY, dedup_key)
                    items_collected += 1

                print(f"Job {job_id} complete. Collected {items_collected} new items.")

            except NotImplementedError as e:
                job_status = "FAILED"
                error_message = str(e)
            except Exception as e:
                job_status = "FAILED"
                error_message = f"Critical crawl failure: {e}"
                print(f"Job {job_id} FAILED with error: {error_message}")
            finally:
                # 5. Log Job Completion/Failure
                if job_id is not None:
                    mysql_repo.log_job_complete(
                        job_id=job_id,
                        items_collected=items_collected,
                        minio_path=minio_path,
                        status=job_status,
                        error_message=error_message
                    )
                    
    except KeyboardInterrupt:
        print("Consumer Worker shutting down...")
    except Exception as e:
        print(f"An error occurred in Consumer Worker: {e}")
    finally:
        if 'mysql_repo' in locals():
            mysql_repo.close()
        get_valkey_connection().close()
        print("Consumer Worker finished.")


if __name__ == "__main__":
    run_consumer()
