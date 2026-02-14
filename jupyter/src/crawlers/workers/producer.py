import json
import os
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path (needed because script is in subdirectory 'workers/')
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Import standalone repository classes (decoupled from legacy 'src/feed')
from crawling_system.storage.mysql_repo import MySQLRepository
from crawling_system.storage.valkey_repo import get_connection as get_valkey_connection

# Configuration
QUEUE_KEY = "queue:pending_crawls"
MYSQL_HOST = os.getenv("MYSQL_HOST", "crawler_mysql_control")
MYSQL_USER = os.getenv("MYSQL_USER", "root")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "secret")
MYSQL_DB = os.getenv("MYSQL_DATABASE", "crawler_control")
POLL_INTERVAL_SECONDS = int(os.getenv("PRODUCER_POLL_INTERVAL", 3600))

def deduplicate_targets(targets: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Given a list of targets (potentially from multiple subscriptions),
    returns a deduplicated list of unique targets ready for a job.
    """
    seen_values = set()
    unique_targets = []
    for target in targets:
        # Use a combination of type and value for uniqueness
        key = (target["target_type"], target["value"])
        if key not in seen_values:
            seen_values.add(key)
            unique_targets.append(target)
    return unique_targets

def run_producer():
    """
    The main producer loop. Reads targets from MySQL and pushes jobs to Valkey.
    """
    print("Starting Producer.")
    
    try:
        mysql_repo = MySQLRepository(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB
        )
        print("Connected to MySQL.")
    except Exception as e:
        print(f"CRITICAL: Failed to connect to MySQL: {e}")
        return

    try:
        valkey_repo = get_valkey_connection()
        valkey_client = valkey_repo.client
        print("Connected to Valkey.")
    except Exception as e:
        print(f"CRITICAL: Failed to connect to Valkey: {e}")
        return

    try:
        while True:
            print("--- Running scheduled job cycle ---")

            # 1. Get all active targets from Control Plane
            all_targets = mysql_repo.get_active_targets()
            if not all_targets:
                print("No active targets found in MySQL. Skipping cycle.")
                time.sleep(POLL_INTERVAL_SECONDS)
                continue

            # 2. Deduplicate targets (though logic in MySQLRepository should fetch unique)
            # This step is here for safety if retrieval logic changes.
            targets_to_crawl = deduplicate_targets(all_targets)
            print(f"Found {len(targets_to_crawl)} unique targets to process.")

            # 3. Push jobs to Valkey
            pushed_count = 0
            for target in targets_to_crawl:
                # Job payload includes target_id and target type for worker
                job_payload = {
                    "target_id": target["id"],
                    "target_type": target["target_type"],
                    "target_value": target["value"],
                    "last_crawled_at": target["last_crawled_at"].isoformat() if target["last_crawled_at"] else None
                }

                # Push job to the right side of the list (LPUSH or RPUSH is fine for FIFO queue)
                valkey_client.rpush(QUEUE_KEY, json.dumps(job_payload))
                pushed_count += 1

            print(f"Successfully pushed {pushed_count} jobs to Valkey key: {QUEUE_KEY}")

            print(f"Cycle complete. Sleeping for {POLL_INTERVAL_SECONDS} seconds.")
            time.sleep(POLL_INTERVAL_SECONDS)

    except KeyboardInterrupt:
        print("Producer shutting down...")
    except Exception as e:
        print(f"An unhandled error occurred in the producer: {e}")
    finally:
        mysql_repo.close()
        valkey_repo.close()


if __name__ == "__main__":
    # Ensure MySQL is running and populated before starting the producer
    run_producer()
