"""Imageboard archival and monitoring tasks with keyword filtering.

Celery tasks for:
1. Polling catalog for keyword matches
2. Archiving matched threads
3. Monitoring image count (stop at 150)
4. Handling thread lifecycle (404, timeout, new thread detection)
5. Periodic check-ins for updates
"""

from celery import shared_task, group, chain
from celery.utils.log import get_task_logger
from datetime import datetime, timezone as tz, timedelta
import requests
import json
import time
from typing import Dict, List, Any, Optional

logger = get_task_logger(__name__)

# Primary keywords for thread detection
PRIMARY_KEYWORDS = [
    "irl", "face", "celeb", "JJ", "girl", "girls", "feet", "cel",
    "panties", "gooning", "goon", "zoomers", "goddess", "built", "ss",
    "actresses", "tiny", "cosplay"
]


@shared_task(bind=True, queue="imageboards", max_retries=3)
def poll_catalog_for_keywords(
    self,
    board: str = "b",
    keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Poll 4chan catalog and detect threads matching primary keywords.

    Args:
        board: Board name (default "b")
        keywords: List of keywords to match (default PRIMARY_KEYWORDS)

    Returns:
        Dict with detection results:
        {
            "board": str,
            "polled_at": datetime,
            "total_threads": int,
            "matched_threads": int,
            "keywords_found": list,
            "archived_threads": list,
        }
    """
    if keywords is None:
        keywords = PRIMARY_KEYWORDS

    task_id = self.request.id
    logger.info(f"Polling /{board}/ catalog for keywords (task: {task_id})")

    try:
        from src.feed.storage.valkey_connection import get_valkey_connection
        from src.feed.storage.postgres_connection import get_postgres_connection

        valkey = get_valkey_connection()
        pg = get_postgres_connection()

        # Fetch catalog
        catalog_url = f"https://a.4cdn.org/{board}/catalog.json"
        resp = requests.get(catalog_url, timeout=30)
        if resp.status_code != 200:
            logger.error(f"Failed to fetch catalog: {resp.status_code}")
            raise self.retry(countdown=60, max_retries=3)

        catalog_data = resp.json()
        total_threads = 0
        matched_threads = []
        keywords_found = {}

        # Search catalog pages
        for page in catalog_data:
            for thread in page.get("threads", []):
                total_threads += 1
                thread_id = thread["no"]
                subject = thread.get("sub", "")
                text = thread.get("com", "")

                # Search for keywords (case-insensitive)
                search_text = (subject + " " + text).lower()
                found_keywords = [k for k in keywords if k.lower() in search_text]

                if found_keywords:
                    matched_threads.append({
                        "thread_id": thread_id,
                        "subject": subject,
                        "keywords": found_keywords,
                        "replies": thread.get("replies", 0),
                        "images": thread.get("images", 0),
                    })

                    for kw in found_keywords:
                        if kw not in keywords_found:
                            keywords_found[kw] = 0
                        keywords_found[kw] += 1

        logger.info(
            f"Catalog poll completed: {total_threads} total threads, "
            f"{len(matched_threads)} matched"
        )

        # Queue matched threads for archival
        if matched_threads:
            logger.info(f"Queueing {len(matched_threads)} threads for archival")

            # Create archival jobs for each matched thread
            archival_jobs = group([
                archive_and_monitor_thread.s(
                    board=board,
                    thread_id=t["thread_id"],
                    subject=t["subject"],
                    keywords=t["keywords"],
                )
                for t in matched_threads
            ])

            # Execute all archival jobs in parallel
            result = archival_jobs.apply_async()
            logger.info(f"Archival group queued: {result.id}")

        return {
            "board": board,
            "polled_at": datetime.now(tz.utc).isoformat(),
            "total_threads": total_threads,
            "matched_threads": len(matched_threads),
            "keywords_found": keywords_found,
            "archived_threads": [t["thread_id"] for t in matched_threads],
        }

    except Exception as e:
        logger.error(f"Catalog poll failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, queue="imageboards", max_retries=2)
def archive_and_monitor_thread(
    self,
    board: str,
    thread_id: int,
    subject: str = "",
    keywords: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Archive a thread and monitor it until completion conditions.

    Conditions for completion:
    1. 150 images collected
    2. Thread 404s (archived/deleted)
    3. Timeout (60 min for /b/)
    4. New priority thread detected

    Args:
        board: Board name
        thread_id: Thread ID
        subject: Thread subject
        keywords: Keywords that matched

    Returns:
        Dict with archival results
    """
    task_id = self.request.id
    logger.info(
        f"Starting archive monitor for /{board}/{thread_id} (task: {task_id})"
    )

    try:
        from src.feed.storage.valkey_connection import get_valkey_connection
        from src.feed.storage.postgres_connection import get_postgres_connection

        valkey = get_valkey_connection()
        pg = get_postgres_connection()

        # Initialize monitoring state
        monitor_key = f"thread_monitor:{board}:{thread_id}"
        state = {
            "board": board,
            "thread_id": thread_id,
            "subject": subject,
            "keywords": keywords or [],
            "status": "archiving",
            "started_at": datetime.now(tz.utc).isoformat(),
            "image_count": 0,
            "total_posts": 0,
            "last_checked": None,
            "check_count": 0,
            "archive_path": None,
        }

        # Store state in Redis for tracking
        valkey.set(monitor_key, json.dumps(state), ex=86400)  # 24 hour expiry

        # Start periodic check-in
        check_in_thread.apply_async(
            args=(board, thread_id, monitor_key),
            countdown=30,  # First check in 30 seconds
        )

        logger.info(
            f"Archive monitoring started for /{board}/{thread_id}: {subject}"
        )

        return {
            "thread_id": thread_id,
            "board": board,
            "subject": subject,
            "monitor_key": monitor_key,
            "status": "monitoring_started",
        }

    except Exception as e:
        logger.error(f"Archive setup failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


@shared_task(bind=True, queue="imageboards")
def check_in_thread(
    self,
    board: str,
    thread_id: int,
    monitor_key: str,
) -> Dict[str, Any]:
    """Periodic check-in to monitor thread status and image count.

    Polls thread for:
    - Image count (stop at 150)
    - 404 status (archived/deleted)
    - New high-priority thread detection
    - Timeout conditions

    Args:
        board: Board name
        thread_id: Thread ID
        monitor_key: Redis key for monitoring state

    Returns:
        Dict with check-in results and next action
    """
    try:
        from src.feed.storage.valkey_connection import get_valkey_connection
        import imageboard_monitor_worker

        valkey = get_valkey_connection()

        # Get current monitoring state
        state_json = valkey.get(monitor_key)
        if not state_json:
            logger.warning(f"Monitor state not found for {monitor_key}")
            return {"status": "monitor_expired"}

        state = json.loads(state_json)

        # Fetch thread data
        thread_data = self._fetch_thread(board, thread_id)

        if thread_data is None:
            # Thread archived or deleted
            logger.info(f"Thread /{board}/{thread_id} archived/deleted (404)")
            state["status"] = "archived"
            valkey.set(monitor_key, json.dumps(state), ex=86400)
            return {"status": "thread_archived", "thread_id": thread_id}

        # Count posts and images
        posts = thread_data.get("posts", [])
        images_in_thread = sum(1 for p in posts if p.get("tim"))  # tim = image timestamp
        state["image_count"] = images_in_thread
        state["total_posts"] = len(posts)
        state["last_checked"] = datetime.now(tz.utc).isoformat()
        state["check_count"] += 1

        logger.info(
            f"Check-in /{board}/{thread_id}: {images_in_thread} images, "
            f"{len(posts)} posts (check #{state['check_count']})"
        )

        # Completion condition 1: 150 images collected
        if images_in_thread >= 150:
            logger.info(
                f"✓ Archival complete /{board}/{thread_id}: "
                f"reached 150 images ({images_in_thread})"
            )
            state["status"] = "completed_image_limit"
            valkey.set(monitor_key, json.dumps(state), ex=86400)
            return {
                "status": "image_limit_reached",
                "images": images_in_thread,
                "thread_id": thread_id,
            }

        # Completion condition 2: Timeout (60 min for /b/)
        started = datetime.fromisoformat(state["started_at"])
        elapsed = datetime.now(tz.utc) - started
        timeout_seconds = 3600  # 1 hour for /b/
        if elapsed.total_seconds() > timeout_seconds:
            logger.info(
                f"✓ Archival timeout /{board}/{thread_id}: "
                f"{elapsed.total_seconds():.0f}s elapsed (collected {images_in_thread} images)"
            )
            state["status"] = "completed_timeout"
            valkey.set(monitor_key, json.dumps(state), ex=86400)
            return {
                "status": "timeout_reached",
                "elapsed_seconds": elapsed.total_seconds(),
                "images": images_in_thread,
                "thread_id": thread_id,
            }

        # Still collecting - schedule next check-in
        next_check_delay = 60  # Check every 60 seconds
        logger.debug(f"Scheduling next check-in in {next_check_delay}s")

        # Update state and reschedule
        valkey.set(monitor_key, json.dumps(state), ex=86400)

        check_in_thread.apply_async(
            args=(board, thread_id, monitor_key),
            countdown=next_check_delay,
        )

        return {
            "status": "monitoring_ongoing",
            "images": images_in_thread,
            "posts": len(posts),
            "next_check_in": next_check_delay,
        }

    except Exception as e:
        logger.error(f"Check-in failed: {e}", exc_info=True)
        # Reschedule with longer delay on error
        check_in_thread.apply_async(
            args=(board, thread_id, monitor_key),
            countdown=120,  # Wait 2 minutes before retry
        )
        return {"status": "check_in_error", "error": str(e)}

    @staticmethod
    def _fetch_thread(board: str, thread_id: int) -> Optional[Dict]:
        """Fetch thread data from 4cdn API."""
        try:
            url = f"https://a.4cdn.org/{board}/thread/{thread_id}.json"
            resp = requests.get(url, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return None
        except Exception as e:
            logger.warning(f"Error fetching thread: {e}")
        return None


@shared_task(bind=True, queue="imageboards")
def monitor_for_new_priority_thread(
    self,
    board: str = "b",
) -> Dict[str, Any]:
    """Check if a new high-priority thread was detected while monitoring.

    If a new priority thread is found before current archival completes,
    transition to the new thread (up to 5 active threads max).

    Args:
        board: Board name

    Returns:
        Dict with results
    """
    try:
        from src.feed.storage.valkey_connection import get_valkey_connection

        valkey = get_valkey_connection()

        # Get list of currently monitored threads
        monitored_pattern = f"thread_monitor:{board}:*"
        monitored_keys = valkey.keys(monitored_pattern)
        monitored_threads = set()

        for key in monitored_keys:
            try:
                state = json.loads(valkey.get(key) or "{}")
                if state.get("status") in ["archiving", "monitoring"]:
                    monitored_threads.add(state.get("thread_id"))
            except:
                pass

        # Fetch current catalog
        catalog_url = f"https://a.4cdn.org/{board}/catalog.json"
        resp = requests.get(catalog_url, timeout=30)
        if resp.status_code != 200:
            return {"status": "catalog_fetch_failed"}

        catalog_data = resp.json()
        new_priority_threads = []

        # Look for new threads matching keywords not yet monitored
        for page in catalog_data[:3]:  # Check top 3 pages (newest threads)
            for thread in page.get("threads", []):
                thread_id = thread["no"]
                if thread_id not in monitored_threads:
                    subject = thread.get("sub", "")
                    text = thread.get("com", "")
                    search_text = (subject + " " + text).lower()

                    found_keywords = [
                        k for k in PRIMARY_KEYWORDS if k.lower() in search_text
                    ]

                    if found_keywords:
                        new_priority_threads.append({
                            "thread_id": thread_id,
                            "subject": subject,
                            "keywords": found_keywords,
                        })

        # Queue new priority threads (max 5 total)
        if new_priority_threads and len(monitored_threads) < 5:
            logger.info(
                f"Found {len(new_priority_threads)} new priority threads "
                f"(currently monitoring {len(monitored_threads)})"
            )

            for thread_info in new_priority_threads[:5 - len(monitored_threads)]:
                archive_and_monitor_thread.apply_async(
                    args=(
                        board,
                        thread_info["thread_id"],
                        thread_info["subject"],
                        thread_info["keywords"],
                    )
                )

            return {
                "status": "new_threads_queued",
                "count": len(new_priority_threads),
                "monitoring": len(monitored_threads),
            }

        return {
            "status": "no_new_priority_threads",
            "monitoring": len(monitored_threads),
        }

    except Exception as e:
        logger.error(f"Priority check failed: {e}", exc_info=True)
        return {"status": "error", "error": str(e)}


@shared_task(queue="imageboards")
def coordinator_task() -> Dict[str, Any]:
    """Coordinator task that runs periodically to manage the entire workflow.

    - Polls catalog for keywords
    - Checks for new priority threads
    - Manages monitoring lifecycle

    Call this every 5 minutes via schedule.
    """
    logger.info("Running imageboard archival coordinator")

    try:
        # Poll catalog for keywords
        catalog_result = poll_catalog_for_keywords.apply_async(
            args=("b", PRIMARY_KEYWORDS)
        )

        # Check for new priority threads
        priority_result = monitor_for_new_priority_thread.apply_async(
            args=("b",),
            countdown=30,  # Run 30 seconds after catalog poll
        )

        return {
            "status": "coordinator_running",
            "catalog_task": catalog_result.id,
            "priority_task": priority_result.id,
        }

    except Exception as e:
        logger.error(f"Coordinator failed: {e}", exc_info=True)
        return {"status": "coordinator_error", "error": str(e)}
