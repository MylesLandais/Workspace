"""Celery task definitions for core jobs: Reddit polling, deduplication, and imageboards.

These tasks wrap existing job implementations and integrate them with Celery
for distributed execution, scheduling, and monitoring via Flower.
"""

from celery import shared_task
from celery.utils.log import get_task_logger
from datetime import datetime, timezone as tz
import json
from typing import Dict, Any, List

logger = get_task_logger(__name__)


# ============================================================================
# REDDIT POLLING TASKS
# ============================================================================

@shared_task(
    bind=True,
    queue="reddit",
    max_retries=3,
    default_retry_delay=60,
    rate_limit="100/m",
    time_limit=3600,  # 1 hour
)
def poll_reddit_task(
    self,
    creator_slug: str,
    subreddits: List[str],
    max_posts: int = 500,
    delay_min: float = 10.0,
    delay_max: float = 30.0,
) -> Dict[str, Any]:
    """Poll Reddit for posts from specified subreddits for a creator.

    Fetches posts, deduplicates against Neo4j, and stores new posts with
    image hash computation and creator entity linking.

    Args:
        creator_slug: Creator entity identifier (e.g., "jordyn-jones")
        subreddits: List of subreddit names to poll (e.g., ["r/Jordyn", "r/JordynJones"])
        max_posts: Maximum posts per creator (default 500)
        delay_min: Minimum delay between requests in seconds (default 10.0)
        delay_max: Maximum delay between requests in seconds (default 30.0)

    Returns:
        Dict with polling results:
        {
            "success": bool,
            "creator_slug": str,
            "subreddits": list,
            "total_posts_found": int,
            "new_posts": int,
            "duplicates": int,
            "failed_subreddits": list,
            "errors": list,
            "duration_seconds": float,
        }
    """
    task_id = self.request.id
    start_time = datetime.now(tz.utc)
    logger.info(f"Starting Reddit poll for {creator_slug} (task: {task_id})")

    try:
        from src.feed.storage.neo4j_connection import get_neo4j_connection
        from src.feed.storage.valkey_connection import get_valkey_connection
        from src.feed.polling.engine import PollingEngine
        from src.feed.platforms.reddit import RedditAdapter

        # Initialize connections
        neo4j = get_neo4j_connection()
        valkey = get_valkey_connection()
        adapter = RedditAdapter(neo4j, valkey)
        engine = PollingEngine(neo4j, adapter)

        # Poll subreddits
        results = {
            "success": True,
            "creator_slug": creator_slug,
            "subreddits": subreddits,
            "total_posts_found": 0,
            "new_posts": 0,
            "duplicates": 0,
            "failed_subreddits": [],
            "errors": [],
        }

        for subreddit in subreddits:
            try:
                logger.info(f"Polling subreddit {subreddit} for {creator_slug}")

                # Call existing poll_creator_sources logic
                posts_data = engine.fetch_subreddit_posts(
                    subreddit=subreddit,
                    creator_slug=creator_slug,
                    max_posts=max_posts,
                    delay_min=delay_min,
                    delay_max=delay_max,
                )

                if posts_data:
                    results["total_posts_found"] += len(posts_data)
                    new_count = sum(1 for p in posts_data if p.get("is_new", False))
                    results["new_posts"] += new_count
                    results["duplicates"] += len(posts_data) - new_count

                    logger.info(
                        f"Subreddit {subreddit}: {len(posts_data)} posts "
                        f"({new_count} new, {len(posts_data) - new_count} duplicates)"
                    )

            except Exception as e:
                error_msg = f"Error polling {subreddit}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results["failed_subreddits"].append(subreddit)
                results["errors"].append(error_msg)
                results["success"] = False

        # Calculate duration
        duration = (datetime.now(tz.utc) - start_time).total_seconds()
        results["duration_seconds"] = duration

        # Update task run record if available
        try:
            from src.feed.storage.postgres_connection import get_postgres_connection

            pg = get_postgres_connection()
            pg.execute_write(
                """
                UPDATE task_runs
                SET output_data = %s
                WHERE celery_task_id = %s
                """,
                (json.dumps(results), task_id)
            )
        except Exception as e:
            logger.warning(f"Failed to update task run output: {e}")

        logger.info(
            f"Reddit poll completed: {results['total_posts_found']} total posts, "
            f"{results['new_posts']} new (took {duration:.1f}s)"
        )
        return results

    except Exception as e:
        logger.error(f"Reddit poll task failed: {e}", exc_info=True)
        # Retry with exponential backoff
        raise self.retry(exc=e, countdown=2 ** self.request.retries)


# ============================================================================
# DEDUPLICATION TASKS
# ============================================================================

@shared_task(
    bind=True,
    queue="dedup",
    max_retries=2,
    default_retry_delay=120,
    rate_limit="10/m",  # Lower rate - compute intensive
    time_limit=7200,  # 2 hours
)
def dedup_task(
    self,
    limit: int = None,
    offset: int = 0,
    batch_size: int = 50,
    use_clip: bool = True,
) -> Dict[str, Any]:
    """Deduplicate images for posts in Neo4j.

    Computes SHA256 hashes (exact), DHASH (perceptual), and optionally
    CLIP embeddings (semantic) to identify duplicate images.

    Args:
        limit: Maximum posts to process (None for all)
        offset: Starting offset for pagination (default 0)
        batch_size: Posts per batch (default 50)
        use_clip: Use CLIP embeddings for semantic similarity (default True)

    Returns:
        Dict with deduplication results:
        {
            "success": bool,
            "processed": int,
            "successful": int,
            "new": int,
            "duplicates": int,
            "errors": int,
            "skipped": int,
            "batches": int,
            "duration_seconds": float,
        }
    """
    task_id = self.request.id
    start_time = datetime.now(tz.utc)
    logger.info(f"Starting deduplication task (task: {task_id})")

    try:
        from src.feed.storage.neo4j_connection import get_neo4j_connection
        from src.image_dedup.batch_process import BatchProcessor

        # Initialize
        neo4j = get_neo4j_connection()
        processor = BatchProcessor(neo4j)

        # Run deduplication
        results = processor.process_batch(
            limit=limit,
            offset=offset,
            batch_size=batch_size,
            use_clip=use_clip,
        )

        # Add duration
        duration = (datetime.now(tz.utc) - start_time).total_seconds()
        results["duration_seconds"] = duration
        results["success"] = True

        # Update task run record if available
        try:
            from src.feed.storage.postgres_connection import get_postgres_connection

            pg = get_postgres_connection()
            pg.execute_write(
                """
                UPDATE task_runs
                SET output_data = %s
                WHERE celery_task_id = %s
                """,
                (json.dumps(results), task_id)
            )
        except Exception as e:
            logger.warning(f"Failed to update task run output: {e}")

        logger.info(
            f"Deduplication completed: {results['processed']} posts, "
            f"{results['duplicates']} duplicates found (took {duration:.1f}s)"
        )
        return results

    except Exception as e:
        logger.error(f"Deduplication task failed: {e}", exc_info=True)
        # Retry with longer delay for compute-intensive task
        raise self.retry(exc=e, countdown=2 ** (self.request.retries + 1) * 60)


# ============================================================================
# IMAGEBOARD POLLING TASKS
# ============================================================================

@shared_task(
    bind=True,
    queue="imageboards",
    max_retries=2,
    default_retry_delay=30,
    rate_limit="100/m",
    time_limit=600,  # 10 minutes
)
def poll_imageboard_catalog(
    self,
    board: str = "b",
    poll_interval: int = 45,
) -> Dict[str, Any]:
    """Poll 4chan board catalog for new threads.

    Queries 4chan API for catalog, detects new threads by comparing to
    cached thread list in Valkey, and queues new threads for processing.

    Args:
        board: Board name (default "b")
        poll_interval: Seconds between polls (default 45)

    Returns:
        Dict with polling results:
        {
            "success": bool,
            "board": str,
            "active_threads": int,
            "new_threads": int,
            "archived_threads": int,
            "processed": int,
            "duration_seconds": float,
        }
    """
    task_id = self.request.id
    start_time = datetime.now(tz.utc)
    logger.info(f"Starting imageboard catalog poll for /{board}/ (task: {task_id})")

    try:
        from src.feed.storage.valkey_connection import get_valkey_connection
        from src.feed.archivers.catalog_poller import CatalogPoller

        # Initialize
        valkey = get_valkey_connection()
        poller = CatalogPoller(valkey, board=board, poll_interval=poll_interval)

        # Poll catalog
        results = poller.poll_catalog()
        results["board"] = board

        # Queue new threads for processing
        new_thread_count = results.get("new_threads", 0)
        if new_thread_count > 0:
            # Queue threads for process_imageboard_thread task
            for thread_id in results.get("new_thread_ids", []):
                process_imageboard_thread.delay(
                    board=board,
                    thread_id=thread_id,
                    subject="",  # Will be fetched in task
                )

        # Calculate duration
        duration = (datetime.now(tz.utc) - start_time).total_seconds()
        results["duration_seconds"] = duration
        results["success"] = True

        logger.info(
            f"Catalog poll completed for /{board}/: "
            f"{results['active_threads']} active, "
            f"{results['new_threads']} new threads"
        )
        return results

    except Exception as e:
        logger.error(f"Imageboard catalog poll failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=30)


@shared_task(
    bind=True,
    queue="imageboards",
    max_retries=2,
    default_retry_delay=60,
    rate_limit="100/m",
    time_limit=1800,  # 30 minutes
)
def process_imageboard_thread(
    self,
    board: str,
    thread_id: int,
    subject: str = "",
) -> Dict[str, Any]:
    """Process individual imageboard thread.

    Fetches thread data, downloads images, deduplicates, moderates posts,
    and saves offline-browsable HTML.

    Args:
        board: Board name (e.g., "b")
        thread_id: Thread ID on board
        subject: Thread subject (optional)

    Returns:
        Dict with processing results:
        {
            "success": bool,
            "board": str,
            "thread_id": int,
            "posts": int,
            "images": int,
            "duplicates": int,
            "moderated_posts": int,
            "duration_seconds": float,
            "html_path": str,
        }
    """
    task_id = self.request.id
    start_time = datetime.now(tz.utc)
    logger.info(f"Processing thread /{board}/{thread_id} (task: {task_id})")

    try:
        from src.feed.storage.valkey_connection import get_valkey_connection
        from src.feed.storage.neo4j_connection import get_neo4j_connection
        from imageboard_monitor_worker import process_monitor_job

        # Initialize
        valkey = get_valkey_connection()
        neo4j = get_neo4j_connection()

        # Process thread
        job_data = {
            "board": board,
            "thread_id": thread_id,
            "subject": subject,
        }

        # Call existing worker logic
        success = process_monitor_job(job_data)

        # Gather results
        results = {
            "success": success,
            "board": board,
            "thread_id": thread_id,
            "posts": 0,  # Would need to query to get exact count
            "images": 0,
            "duplicates": 0,
            "moderated_posts": 0,
        }

        # Calculate duration
        duration = (datetime.now(tz.utc) - start_time).total_seconds()
        results["duration_seconds"] = duration

        logger.info(
            f"Thread /{board}/{thread_id} processed successfully (took {duration:.1f}s)"
        )
        return results

    except Exception as e:
        logger.error(f"Thread processing failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=60)


# ============================================================================
# MAINTENANCE TASKS
# ============================================================================

@shared_task(
    bind=True,
    queue="maintenance",
    max_retries=1,
)
def cleanup_nix_environments(self, days: int = 30) -> Dict[str, Any]:
    """Clean up stale nix environments from PostgreSQL.

    Removes entries for nix environments unused for N days.

    Args:
        days: Number of days of inactivity before deletion (default 30)

    Returns:
        Dict with cleanup results:
        {
            "success": bool,
            "deleted_count": int,
            "duration_seconds": float,
        }
    """
    start_time = datetime.now(tz.utc)
    logger.info(f"Starting nix environment cleanup (older than {days} days)")

    try:
        from src.feed.scheduler.nix_runner import NixRunner
        from src.feed.storage.postgres_connection import get_postgres_connection

        pg = get_postgres_connection()
        runner = NixRunner(pg)

        # Cleanup
        deleted_count = runner.cleanup_stale_environments(days=days)

        duration = (datetime.now(tz.utc) - start_time).total_seconds()

        results = {
            "success": True,
            "deleted_count": deleted_count,
            "duration_seconds": duration,
        }

        logger.info(f"Cleanup completed: {deleted_count} environments deleted (took {duration:.1f}s)")
        return results

    except Exception as e:
        logger.error(f"Cleanup task failed: {e}", exc_info=True)
        raise self.retry(exc=e, countdown=600)
