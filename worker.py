#!/usr/bin/env python3
"""
Crawler Worker - Processes jobs from Redis queue
"""

import os
import sys
import json
import time
import logging
import redis
import requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('worker')

# Configuration
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379')
FLARESOLVERR_URL = os.environ.get('FLARESOLVERR_URL', 'http://localhost:8191/v1')
MAX_RETRIES = int(os.environ.get('MAX_RETRIES', 3))
REQUEST_DELAY = float(os.environ.get('REQUEST_DELAY', 0.5))
CONCURRENCY = int(os.environ.get('WORKER_CONCURRENCY', 4))

# Paths
BASE_DIR = os.environ.get('BASE_DIR', '/home/warby/Workspace/jupyter')
DOWNLOADS_DIR = os.path.join(BASE_DIR, 'downloads')
CACHE_DIR = os.path.join(BASE_DIR, 'cache')

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)


class CoomerCrawler:
    def __init__(self):
        self.redis = redis.from_url(REDIS_URL, decode_responses=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        })

    @retry(stop=stop_after_attempt(MAX_RETRIES), wait=wait_exponential(multiplier=1, min=2, max=10))
    def fetch_with_flaresolverr(self, url):
        """Fetch URL via FlareSolverr with retry"""
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
        }

        response = requests.post(FLARESOLVERR_URL, json=payload, timeout=120)
        result = response.json()

        if result.get("status") == "ok":
            return result.get("solution", {}).get("response", "")
        raise Exception(f"FlareSolverr error: {result.get('message')}")

    def extract_post_data(self, html, creator_id, post_id):
        """Extract post data from HTML"""
        soup = BeautifulSoup(html, 'html.parser')

        post_data = {
            'id': post_id,
            'creator': creator_id,
            'url': f"https://coomer.st/onlyfans/user/{creator_id}/post/{post_id}",
            'title': '',
            'published': '',
            'media': [],
            'scraped_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }

        # Extract title
        title_elem = soup.find('h1', class_='post__title')
        if title_elem:
            post_data['title'] = title_elem.get_text(strip=True)

        # Extract date
        time_elem = soup.find('time', class_='timestamp')
        if time_elem:
            post_data['published'] = time_elem.get('datetime', '')

        # Extract videos
        videos = []
        video_matches = re.findall(
            r'href="(https://n\d+\.coomer\.st/data/[^"]+\.mp4\?f=[^"]+)"',
            html
        )
        for v in video_matches:
            videos.append({'url': v, 'type': 'video'})

        # Extract images
        images = []
        img_matches = re.findall(
            r'href="(https://n\d+\.coomer\.st/data/[^"]+\.(jpg|jpeg|png|gif)[^"]*)"',
            html
        )
        for url, ext in img_matches:
            images.append({'url': url, 'type': 'image', 'ext': ext})

        post_data['media'] = videos + images
        post_data['video_count'] = len(videos)
        post_data['image_count'] = len(images)

        return post_data

    def download_media(self, media_item, creator_id, post_id):
        """Download a media file"""
        url = media_item['url']
        filename = url.split('?')[0].split('/')[-1]

        # Check cache first
        cache_path = os.path.join(CACHE_DIR, creator_id, post_id, filename)
        if os.path.exists(cache_path):
            size = os.path.getsize(cache_path)
            logger.info(f"  ✓ {filename} ({size/1024/1024:.1f} MB) - cached")
            return {'cached': True, 'path': cache_path, 'size': size}

        # Download
        download_dir = os.path.join(DOWNLOADS_DIR, 'galleries', creator_id, post_id)
        os.makedirs(download_dir, exist_ok=True)

        local_path = os.path.join(download_dir, filename)
        is_video = media_item['type'] == 'video'
        timeout = 180 if is_video else 60

        try:
            response = self.session.get(url, headers={
                'Referer': 'https://coomer.st/',
            }, timeout=timeout, stream=True)

            if response.status_code == 200:
                content_length = int(response.headers.get('content-length', 0))
                min_size = 1024 * 1024 if is_video else 10000

                if content_length > 0 and content_length < min_size:
                    logger.warning(f"  ⚠ File too small, skipping: {filename}")
                    return None

                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                size = os.path.getsize(local_path)
                logger.info(f"  ↓ {filename} ({size/1024/1024:.1f} MB)")

                # Cache it
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)

                return {'downloaded': True, 'path': local_path, 'size': size}
            else:
                logger.error(f"  ✗ HTTP {response.status_code}: {filename}")
                return None
        except Exception as e:
            logger.error(f"  ✗ Error: {str(e)[:50]}")
            return None

    def process_post(self, job_data):
        """Process a single post"""
        creator_id = job_data['creator']
        post_id = job_data['post_id']

        logger.info(f"Processing post {post_id} by @{creator_id}")

        url = f"https://coomer.st/onlyfans/user/{creator_id}/post/{post_id}"

        try:
            html = self.fetch_with_flaresolverr(url)
        except Exception as e:
            logger.error(f"Failed to fetch post {post_id}: {e}")
            return {'status': 'failed', 'error': str(e)}

        # Extract data
        post_data = self.extract_post_data(html, creator_id, post_id)

        # Save metadata
        metadata_dir = os.path.join(DOWNLOADS_DIR, 'metadata', creator_id)
        os.makedirs(metadata_dir, exist_ok=True)

        metadata_path = os.path.join(metadata_dir, f'{post_id}.json')
        with open(metadata_path, 'w') as f:
            json.dump(post_data, f, indent=2)

        # Download media
        downloaded = 0
        cached = 0
        failed = 0

        for media in post_data.get('media', []):
            result = self.download_media(media, creator_id, post_id)
            if result:
                if result.get('downloaded'):
                    downloaded += 1
                elif result.get('cached'):
                    cached += 1
            else:
                failed += 1

        logger.info(f"  Complete: {downloaded} new, {cached} cached, {failed} failed")

        return {
            'status': 'success',
            'post_id': post_id,
            'creator': creator_id,
            'videos': post_data.get('video_count', 0),
            'images': post_data.get('image_count', 0),
            'downloaded': downloaded,
            'cached': cached,
            'failed': failed,
            'metadata_path': metadata_path
        }


def process_job(job_id):
    """Process a job from the queue"""
    logger.info(f"Processing job: {job_id}")

    crawler = CoomerCrawler()
    r = crawler.redis

    # Get job data
    job_data = r.hgetall(f"job:{job_id}")
    logger.info(f"Job Data keys: {list(job_data.keys())}, type value: {job_data.get('type')}")

    if not job_data:
        logger.error(f"Job not found: {job_id}")
        return

    job_type = job_data.get('type', 'post')
    creator = job_data.get('creator')

    result = {'job_id': job_id, 'type': job_type, 'creator': creator}

    if job_type == 'post':
        post_id = job_data.get('post_id')
        if not post_id:
            logger.error("No post_id in job")
            return

        result.update(crawler.process_post({'creator': creator, 'post_id': post_id}))

    elif job_type == 'creator':
        # Get all posts for creator
        posts = json.loads(job_data.get('posts', '[]'))
        for post_id in posts:
            r.rpush(f"queue:jobs", json.dumps({
                'type': 'post',
                'creator': creator,
                'post_id': post_id
            }))
        result['queued'] = len(posts)
        logger.info(f"Queued {len(posts)} posts for @{creator}")

    # Store result
    r.hset(f"job:{job_id}", mapping={**result, 'completed_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())})

    # Update stats
    r.incr('stats:jobs_completed')
    r.hincrby('stats', 'posts_processed', result.get('downloaded', 0) + result.get('cached', 0))


def worker():
    """Worker main loop"""
    logger.info(f"Starting worker (concurrency={CONCURRENCY})")
    logger.info(f"Redis: {REDIS_URL}")
    logger.info(f"FlareSolverr: {FLARESOLVERR_URL}")

    crawler = CoomerCrawler()

    while True:
        try:
            # Get job from queue
            job = crawler.redis.blpop('queue:jobs', timeout=1)
            if job:
                _, job_data = job
                try:
                    job_obj = json.loads(job_data)
                    process_job(job_obj.get('id', job_data[:20]))
                except json.JSONDecodeError:
                    logger.error(f"Invalid job data: {job_data[:100]}")
        except KeyboardInterrupt:
            logger.info("Worker stopped")
            break
        except Exception as e:
            logger.error(f"Worker error: {e}")
            time.sleep(5)


if __name__ == '__main__':
    import re  # Import regex for patterns

    if len(sys.argv) > 1 and sys.argv[1] == '--queue':
        # Run single job from queue
        worker()
    else:
        # Run in foreground
        worker()
