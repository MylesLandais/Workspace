#!/usr/bin/env python3
"""
Scheduler - Schedules crawling jobs
"""

import os
import sys
import json
import time
import logging
import redis
import schedule

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('scheduler')

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
# Ensure decode_responses is True to handle string keys/values
if 'decode_responses' not in REDIS_URL:
    if '?' in REDIS_URL:
        REDIS_URL += '&decode_responses=True'
    else:
        REDIS_URL += '?decode_responses=True'

SCHEDULE_FILE = os.environ.get('SCHEDULE_FILE', 'config/schedule.json')


def load_schedule():
    """Load schedule configuration"""
    default_schedule = {
        "creators": [
            {"id": "myla.feet", "interval": 3600, "priority": "high"}
        ],
        "jobs": []
    }

    if os.path.exists(SCHEDULE_FILE):
        try:
            with open(SCHEDULE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load schedule: {e}")

    return default_schedule


def queue_creator(creator_id, max_posts=50, priority='normal'):
    """Queue all posts for a creator"""
    r = redis.from_url(REDIS_URL)

    job_id = f"creator:{creator_id}:{int(time.time())}"

    # Create creator job
    job_data = {
        'id': job_id,
        'type': 'creator',
        'creator': creator_id,
        'max_posts': max_posts,
        'priority': priority,
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }

    # Store job
    for key, value in job_data.items():
        r.hset(f"job:{job_id}", key, value)

    # Add to queue
    r.rpush('queue:jobs', json.dumps({'id': job_id}))

    logger.info(f"Queued creator job: {job_id}")
    return job_id


def queue_post(creator_id, post_id, priority='normal'):
    """Queue a single post"""
    r = redis.from_url(REDIS_URL)

    job_id = f"post:{creator_id}:{post_id}:{int(time.time())}"

    job_data = {
        'id': job_id,
        'type': 'post',
        'creator': creator_id,
        'post_id': post_id,
        'priority': priority,
        'created_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
    }

    for key, value in job_data.items():
        r.hset(f"job:{job_id}", key, value)

    r.rpush('queue:jobs', json.dumps({'id': job_id}))

    logger.info(f"Queued post job: {job_id}")
    return job_id


def update_stats():
    """Update global statistics"""
    r = redis.from_url(REDIS_URL)

    # Count queued jobs
    queue_len = r.llen('queue:jobs')
    r.set('stats:queue_length', queue_len)

    # Count completed jobs
    jobs_completed = r.get('stats:jobs_completed') or 0
    r.set('stats:jobs_completed', jobs_completed)

    logger.info(f"Stats updated - Queue: {queue_len}, Completed: {jobs_completed}")


def run_scheduler():
    """Run the scheduler loop"""
    logger.info("Starting scheduler")
    logger.info(f"Redis: {REDIS_URL}")
    logger.info(f"Schedule file: {SCHEDULE_FILE}")

    schedule_data = load_schedule()

    # Schedule creator updates
    for creator in schedule_data.get('creators', []):
        creator_id = creator['id']
        interval = creator.get('interval', 3600)
        priority = creator.get('priority', 'normal')

        logger.info(f"Scheduling @{creator_id} every {interval}s (priority: {priority})")

        schedule.every(interval).seconds.do(
            queue_creator, creator_id=creator_id, priority=priority
        )

    # Update stats every minute
    schedule.every(60).seconds.do(update_stats)

    # Main loop
    while True:
        schedule.run_pending()
        time.sleep(1)


if __name__ == '__main__':
    if '--loop' in sys.argv:
        run_scheduler()
    else:
        # Run once
        schedule_data = load_schedule()

        # Queue all scheduled creators
        for creator in schedule_data.get('creators', []):
            queue_creator(creator['id'], priority=creator.get('priority', 'normal'))

        logger.info("Initial jobs queued")
