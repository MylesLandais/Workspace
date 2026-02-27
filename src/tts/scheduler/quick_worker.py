#!/usr/bin/env python3
"""Quick video downloader"""

import os, json, time, re, redis, requests
from bs4 import BeautifulSoup
from tenacity import retry, stop_after_attempt, wait_exponential

REDIS_URL = 'redis://localhost:6381'
FLARESOLVERR_URL = 'http://localhost:8191/v1'
DOWNLOADS_DIR = '/home/warby/Workspace/jupyter/downloads'
CACHE_DIR = '/home/warby/Workspace/jupyter/cache'

os.makedirs(DOWNLOADS_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

r = redis.from_url(REDIS_URL)

@retry(stop=stop_after_attempt(3), wait=wait_exponential(min=2, max=10))
def fetch(url):
    resp = requests.post(FLARESOLVERR_URL, json={'cmd': 'request.get', 'url': url, 'maxTimeout': 60000}, timeout=120)
    result = resp.json()
    if result.get('status') == 'ok':
        return result.get('solution', {}).get('response', '')
    raise Exception('FlareSolverr error')

def download_media(url, creator, post_id):
    filename = url.split('?')[0].split('/')[-1]
    cache_path = os.path.join(CACHE_DIR, creator, post_id, filename)
    if os.path.exists(cache_path):
        print(f'  ✓ {filename} - cached')
        return True

    download_dir = os.path.join(DOWNLOADS_DIR, 'galleries', creator, post_id)
    os.makedirs(download_dir, exist_ok=True)
    local_path = os.path.join(download_dir, filename)

    try:
        resp = requests.get(url, headers={'Referer': 'https://coomer.st/'}, timeout=120, stream=True)
        if resp.status_code == 200:
            with open(local_path, 'wb') as f:
                for chunk in resp.iter_content(8192):
                    f.write(chunk)
            size = os.path.getsize(local_path)
            print(f'  ↓ {filename} ({size/1024/1024:.1f} MB)')
            return True
    except Exception as e:
        print(f'  ✗ {str(e)[:50]}')
    return False

def process_post(creator, post_id):
    print(f'\n[{creator}] Post {post_id}')
    url = f'https://coomer.st/onlyfans/user/{creator}/post/{post_id}'
    html = fetch(url)

    if not html:
        print('  Failed to fetch')
        return

    videos = re.findall(r'href="(https://n\d+\.coomer\.st/data/[^"]+\.mp4\?f=[^"]+)"', html)
    print(f'  Found {len(videos)} video(s)')

    for video_url in videos:
        download_media(video_url, creator, post_id)
        time.sleep(0.2)

if __name__ == '__main__':
    print("Processing queue...")
    while True:
        try:
            job = r.blpop('queue:jobs', timeout=5)
            if job:
                _, job_data = job
                try:
                    data = json.loads(job_data)
                    if data.get('type') == 'post':
                        process_post(data['creator'], data['post_id'])
                except Exception as e:
                    print(f'Job error: {e}')
        except KeyboardInterrupt:
            print("\nStopped")
            break
        except Exception as e:
            print(f'Error: {e}')
            time.sleep(1)
    print("Done!")
