import requests
import json
import os
import time
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import hashlib

class CoomerBatchDownloader:
    def __init__(self, config_file=None):
        self.base_dir = "/home/warby/Workspace/jupyter/downloads"
        self.gallery_dir = os.path.join(self.base_dir, "galleries")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        self.failed_dir = os.path.join(self.base_dir, "failed")
        self.api_base = "https://coomer.st"

        os.makedirs(self.gallery_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
        os.makedirs(self.failed_dir, exist_ok=True)

        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        })

        self.stats = {
            'posts_scraped': 0,
            'media_downloaded': 0,
            'media_failed': 0,
            'posts_failed': 0
        }

    def fetch_api_posts(self, creator_id, service='onlyfans', max_posts=None):
        """Fetch posts via API using FlareSolverr"""
        url = f"{self.api_base}/api/v1/{service}/user/{creator_id}/posts"
        params = {}

        all_posts = []
        page = 1

        while True:
            if page > 1:
                params['o'] = (page - 1) * 50

            payload = {
                "cmd": "request.get",
                "url": url,
                "maxTimeout": 60000,
                "params": params,
                "headers": {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'application/json, text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Referer': f'{self.api_base}/',
                }
            }

            try:
                response = requests.post('http://localhost:8191/v1', json=payload, timeout=120)
                result = response.json()

                if result.get("status") != "ok":
                    print(f"  ⚠️ FlareSolverr error: {result.get('message', 'Unknown')}")
                    break

                html = result.get("solution", {}).get("response", "")

                import re
                json_match = re.search(r'\[.*\]', html, re.DOTALL)
                if not json_match:
                    print(f"  ⚠️ No JSON found in response")
                    break

                posts = json.loads(json_match.group())
                if not posts:
                    break

                all_posts.extend(posts)
                print(f"  📄 Page {page}: {len(posts)} posts")

                if max_posts and len(all_posts) >= max_posts:
                    all_posts = all_posts[:max_posts]
                    break

                if len(posts) < 50:
                    break

                page += 1
                time.sleep(1)

            except Exception as e:
                print(f"  ⚠️ Error fetching page {page}: {str(e)[:50]}")
                break

        return all_posts

    def fetch_page(self, url, max_retries=3):
        """Fetch page via FlareSolverr with retry logic"""
        payload = {
            "cmd": "request.get",
            "url": url,
            "maxTimeout": 60000,
            "headers": {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html+xml,application,application/xhtml/xml;q=0.9,*/*;q=0.8',
            }
        }

        for attempt in range(max_retries):
            try:
                response = requests.post('http://localhost:8191/v1', json=payload, timeout=120)
                result = response.json()

                if result.get("status") == "ok":
                    return result.get("solution", {}).get("response", "")
                else:
                    print(f"    ⚠️ FlareSolverr error: {result.get('message', 'Unknown')}")
            except Exception as e:
                print(f"    ⚠️ Attempt {attempt + 1}/{max_retries}: {str(e)[:50]}")

            time.sleep(2 ** attempt)

        return None

    def get_file_extension(self, url):
        """Determine file extension from URL"""
        parsed = urlparse(url)
        path = parsed.path.lower()

        if path.endswith('.mp4'):
            return '.mp4'
        elif path.endswith('.webm'):
            return '.webm'
        elif path.endswith('.jpg') or path.endswith('.jpeg'):
            return '.jpg'
        elif path.endswith('.png'):
            return '.png'
        elif path.endswith('.gif'):
            return '.gif'
        else:
            return '.jpg'

    def sanitize_filename(self, filename):
        """Sanitize filename to remove problematic characters"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename[:100]

    def construct_media_url(self, path):
        """Construct full media URL from path"""
        if path.startswith('/'):
            path = path[1:]
        return f"https://n1.coomer.st/{path}"

    def download_media(self, url, local_path, is_video=False):
        """Download media file with appropriate behavior for images/videos"""
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            min_size = 1024 * 1024 if is_video else 10000  # 1MB for videos, 10KB for images

            if size > min_size:
                print(f"    ✓ Already exists: {os.path.basename(local_path)} ({size/1024/1024:.1f} MB)")
                return True
            else:
                print(f"    ⚠️ File too small, re-downloading: {os.path.basename(local_path)}")

        try:
            response = self.session.get(url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://coomer.st/',
            }, timeout=180 if is_video else 60, stream=True)

            if response.status_code == 200:
                content_length = int(response.headers.get('content-length', 0))
                min_size = 1024 * 1024 if is_video else 10000

                if content_length > 0 and content_length < min_size:
                    print(f"    ⚠️ Content too small ({content_length} bytes), skipping")
                    return False

                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                size_mb = content_length / 1024 / 1024 if content_length > 0 else 0
                print(f"    ✓ {os.path.basename(local_path)} ({size_mb:.1f} MB)")
                return True

        except Exception as e:
            print(f"    ✗ Error: {str(e)[:50]}")

        return False

    def parse_api_post(self, post, creator_id):
        """Parse a post from API JSON data"""
        post_id = post.get('id')
        post_data = {
            'id': post_id,
            'url': f"{self.api_base}/{post.get('service', 'onlyfans')}/user/{creator_id}/post/{post_id}",
            'creator': creator_id,
            'title': post.get('title', ''),
            'published': post.get('published', ''),
            'service': post.get('service', 'onlyfans'),
            'content': post.get('substring', ''),
            'media': [],
            'scraped_at': datetime.now().isoformat()
        }

        media_count = 0

        main_file = post.get('file', {})
        if main_file and main_file.get('path'):
            path = main_file['path']
            name = main_file.get('name', f'file_{media_count + 1}')
            ext = self.get_file_extension(name)
            is_video = ext in ['.mp4', '.webm']

            post_data['media'].append({
                'index': media_count + 1,
                'url': self.construct_media_url(path),
                'filename': self.sanitize_filename(name),
                'type': 'video' if is_video else 'image',
                'extension': ext
            })
            media_count += 1

        attachments = post.get('attachments', [])
        for att in attachments:
            if att.get('path'):
                path = att['path']
                name = att.get('name', f'file_{media_count + 1}')
                ext = self.get_file_extension(name)
                is_video = ext in ['.mp4', '.webm']

                post_data['media'].append({
                    'index': media_count + 1,
                    'url': self.construct_media_url(path),
                    'filename': self.sanitize_filename(name),
                    'type': 'video' if is_video else 'image',
                    'extension': ext
                })
                media_count += 1

        return post_data

    def scrape_post(self, post_url, creator_id):
        """Scrape a post page with video support"""
        post_id = post_url.split('/')[-1]
        print(f"\n📸 {post_id}")

        html = self.fetch_page(post_url)
        if not html:
            print("  ❌ Failed to fetch page")
            self.stats['posts_failed'] += 1
            return None

        soup = BeautifulSoup(html, 'html.parser')

        post_data = {
            'id': post_id,
            'url': post_url,
            'creator': creator_id,
            'title': '',
            'published': '',
            'content': '',
            'service': 'onlyfans',
            'media': [],
            'scraped_at': datetime.now().isoformat()
        }

        title_elem = soup.find('h1', class_='post__title')
        if title_elem:
            post_data['title'] = title_elem.get_text(strip=True)

        time_elem = soup.find('time', class_='timestamp')
        if time_elem:
            post_data['published'] = time_elem.get('datetime', '')

        media_count = 0

        videos_section = soup.find('h2', string='Videos')
        if videos_section:
            video_container = videos_section.find_next('ul')
            if video_container:
                for source in video_container.find_all('source'):
                    video_url = source.get('src', '')
                    if video_url:
                        ext = '.mp4'
                        filename = source.get('src', '').split('/')[-1].split('?')[0]
                        filename = f"video_{media_count + 1}_{filename}" if not filename.endswith('.mp4') else f"video_{media_count + 1}_{filename}"

                        post_data['media'].append({
                            'index': media_count + 1,
                            'url': video_url,
                            'filename': filename,
                            'type': 'video',
                            'extension': ext
                        })
                        media_count += 1

        downloads_section = soup.find('h2', string='Downloads')
        if downloads_section:
            attachments = downloads_section.find_next('ul', class_='post__attachments')
            if attachments:
                for link in attachments.find_all('a', class_='post__attachment-link'):
                    media_url = link.get('href', '')
                    download_name = link.get('download', '')

                    if media_url and media_url not in [m['url'] for m in post_data['media']]:
                        ext = self.get_file_extension(media_url)
                        filename = download_name if download_name else f"file_{media_count + 1}{ext}"
                        filename = self.sanitize_filename(filename)

                        is_video = ext in ['.mp4', '.webm']

                        post_data['media'].append({
                            'index': media_count + 1,
                            'url': media_url,
                            'filename': filename,
                            'type': 'video' if is_video else 'image',
                            'extension': ext
                        })
                        media_count += 1

        thumbnails_section = soup.find_all('div', class_='post__thumbnail')
        for thumb in thumbnails_section:
            link = thumb.find('a', class_='fileThumb')
            if link and link.get('href'):
                media_url = link['href']
                if media_url not in [m['url'] for m in post_data['media']]:
                    ext = self.get_file_extension(media_url)
                    original_filename = link.get('download', f'file_{media_count + 1}{ext}')
                    sanitized = self.sanitize_filename(original_filename)

                    is_video = ext in ['.mp4', '.webm']

                    post_data['media'].append({
                        'index': media_count + 1,
                        'url': media_url,
                        'filename': sanitized,
                        'type': 'video' if is_video else 'image',
                        'extension': ext
                    })
                    media_count += 1

        print(f"  Title: {post_data['title'][:50] if post_data['title'] else 'Untitled'}")
        print(f"  Media: {len(post_data['media'])} files ({sum(1 for m in post_data['media'] if m['type'] == 'video')} video, {sum(1 for m in post_data['media'] if m['type'] == 'image')} image)")

        self.stats['posts_scraped'] += 1
        return post_data

    def download_post_media(self, post_data, creator_id):
        """Download all media for a post"""
        post_dir = os.path.join(self.gallery_dir, creator_id, post_data['id'])
        os.makedirs(post_dir, exist_ok=True)

        downloaded = 0
        failed = 0

        for media in post_data['media']:
            local_path = os.path.join(post_dir, media['filename'])
            is_video = media['type'] == 'video'

            if self.download_media(media['url'], local_path, is_video):
                downloaded += 1
                media['local'] = local_path
                self.stats['media_downloaded'] += 1
            else:
                failed += 1
                self.stats['media_failed'] += 1

        return downloaded, failed

    def save_post_metadata(self, post_data, creator_id):
        """Save post metadata to JSON"""
        post_dir = os.path.join(self.gallery_dir, creator_id, post_data['id'])
        post_meta_path = os.path.join(post_dir, 'metadata.json')

        with open(post_meta_path, 'w') as f:
            json.dump(post_data, f, indent=2)

    def download_creator(self, creator_id, post_urls, max_posts=None, offset=0):
        """Download all posts for a creator"""
        posts_to_process = post_urls[offset:]
        if max_posts:
            posts_to_process = posts_to_process[:max_posts]

        print(f"\n🎯 Downloading {len(posts_to_process)} posts for @{creator_id} (offset: {offset})")

        creator_dir = os.path.join(self.gallery_dir, creator_id)
        os.makedirs(creator_dir, exist_ok=True)

        all_posts = []
        total_downloaded = 0
        total_failed = 0

        for i, post_url in enumerate(posts_to_process):
            print(f"\n[{i+1}/{len(posts_to_process)}]")

            post_data = self.scrape_post(post_url, creator_id)
            if not post_data:
                continue

            downloaded, failed = self.download_post_media(post_data, creator_id)
            total_downloaded += downloaded
            total_failed += failed

            if post_data['media']:
                self.save_post_metadata(post_data, creator_id)
                all_posts.append(post_data)
            else:
                print("  ⚠️ No media found, skipping metadata save")

            time.sleep(0.5)

        gallery_metadata = {
            'creator': creator_id,
            'posts': len(all_posts),
            'total_media': total_downloaded,
            'failed_media': total_failed,
            'scraped_at': datetime.now().isoformat(),
            'posts_data': all_posts
        }

        gallery_path = os.path.join(self.metadata_dir, f"{creator_id}_gallery.json")
        with open(gallery_path, 'w') as f:
            json.dump(gallery_metadata, f, indent=2)

        print(f"\n✅ Complete!")
        print(f"   Posts: {len(all_posts)}")
        print(f"   Media: {total_downloaded} downloaded, {total_failed} failed")
        print(f"   Gallery: {creator_dir}")
        print(f"   Metadata: {gallery_path}")

        return gallery_metadata

    def get_existing_posts(self, creator_id):
        """Get list of already downloaded post IDs for incremental updates"""
        creator_dir = os.path.join(self.gallery_dir, creator_id)
        if not os.path.exists(creator_dir):
            return set()

        existing = set()
        for post_id in os.listdir(creator_dir):
            post_meta = os.path.join(creator_dir, post_id, 'metadata.json')
            if os.path.exists(post_meta):
                existing.add(post_id)

        return existing

    def download_incremental(self, creator_id, post_urls, max_new=10):
        """Download only new posts not already downloaded"""
        existing = self.get_existing_posts(creator_id)
        new_posts = [url for url in post_urls if url.split('/')[-1] not in existing]

        if not new_posts:
            print(f"\n✅ No new posts for @{creator_id} (all {len(existing)} already downloaded)")
            return None

        print(f"\n📦 Incremental update for @{creator_id}")
        print(f"   Existing: {len(existing)} posts")
        print(f"   New: {len(new_posts)} posts")
        print(f"   Max new: {max_new}")

        return self.download_creator(creator_id, new_posts[:max_new])

    def print_stats(self):
        """Print download statistics"""
        print(f"\n📊 Session Statistics:")
        print(f"   Posts scraped: {self.stats['posts_scraped']}")
        print(f"   Media downloaded: {self.stats['media_downloaded']}")
        print(f"   Media failed: {self.stats['media_failed']}")
        print(f"   Posts failed: {self.stats['posts_failed']}")

    def download_creator_from_api(self, creator_id, service='onlyfans', max_posts=None, offset=0):
        """Download all posts for a creator using the API"""
        print(f"\n🎯 Fetching posts for @{creator_id} via API (offset: {offset}, max: {max_posts})")

        posts = self.fetch_api_posts(creator_id, service, max_posts)
        if offset > 0:
            posts = posts[offset:]

        print(f"   Found {len(posts)} posts")

        creator_dir = os.path.join(self.gallery_dir, creator_id)
        os.makedirs(creator_dir, exist_ok=True)

        all_posts = []
        total_downloaded = 0
        total_failed = 0
        video_count = 0
        image_count = 0

        for i, post in enumerate(posts):
            print(f"\n[{i+1}/{len(posts)}] Post {post.get('id')}")

            post_data = self.parse_api_post(post, creator_id)

            video_count += sum(1 for m in post_data['media'] if m['type'] == 'video')
            image_count += sum(1 for m in post_data['media'] if m['type'] == 'image')

            downloaded, failed = self.download_post_media(post_data, creator_id)
            total_downloaded += downloaded
            total_failed += failed

            if post_data['media']:
                self.save_post_metadata(post_data, creator_id)
                all_posts.append(post_data)
            else:
                print("  ⚠️ No media found, skipping metadata save")

            time.sleep(0.3)

        gallery_metadata = {
            'creator': creator_id,
            'service': service,
            'posts': len(all_posts),
            'total_media': total_downloaded,
            'failed_media': total_failed,
            'videos': video_count,
            'images': image_count,
            'scraped_at': datetime.now().isoformat(),
            'posts_data': all_posts
        }

        gallery_path = os.path.join(self.metadata_dir, f"{creator_id}_gallery.json")
        with open(gallery_path, 'w') as f:
            json.dump(gallery_metadata, f, indent=2)

        print(f"\n✅ Complete!")
        print(f"   Posts: {len(all_posts)}")
        print(f"   Media: {total_downloaded} downloaded, {total_failed} failed")
        print(f"   Videos: {video_count}, Images: {image_count}")
        print(f"   Gallery: {creator_dir}")
        print(f"   Metadata: {gallery_path}")

        return gallery_metadata


def load_creators_from_file(filepath):
    """Load creator list from JSON or text file"""
    if not os.path.exists(filepath):
        return {}

    with open(filepath, 'r') as f:
        content = f.read().strip()

    if filepath.endswith('.json'):
        return json.loads(content)
    else:
        creators = {}
        for line in content.split('\n'):
            line = line.strip()
            if line and not line.startswith('#'):
                parts = line.split()
                if len(parts) >= 2:
                    creator_id = parts[0].replace('@', '')
                    urls = [u for u in parts[1:] if u.startswith('http')]
                    if urls:
                        creators[creator_id] = urls
                elif line.startswith('@'):
                    creators[line[1:]] = []
        return creators


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Coomer.st batch downloader with video support')
    parser.add_argument('--creator', '-c', help='Creator ID to download')
    parser.add_argument('--posts', '-p', nargs='+', help='Post URLs to download')
    parser.add_argument('--max-posts', type=int, default=10, help='Max posts to download')
    parser.add_argument('--offset', type=int, default=0, help='Starting offset')
    parser.add_argument('--incremental', '-i', action='store_true', help='Only download new posts')
    parser.add_argument('--config', '-f', help='Config file with creator URLs')
    parser.add_argument('--list-creators', action='store_true', help='List available creators from config')
    parser.add_argument('--all', '-a', action='store_true', help='Download all creators in config')
    parser.add_argument('--api', action='store_true', help='Use API instead of HTML scraping (recommended)')

    args = parser.parse_args()

    downloader = CoomerBatchDownloader()

    if args.list_creators and args.config:
        creators = load_creators_from_file(args.config)
        print("\n📋 Available creators:")
        for creator_id, urls in sorted(creators.items()):
            print(f"   @{creator_id}: {len(urls)} posts")
        return

    if args.all and args.config:
        creators = load_creators_from_file(args.config)
        for creator_id, urls in sorted(creators.items()):
            if args.api:
                downloader.download_creator_from_api(creator_id, max_posts=args.max_posts, offset=args.offset)
            else:
                if args.incremental:
                    downloader.download_incremental(creator_id, urls, args.max_posts)
                else:
                    downloader.download_creator(creator_id, urls, args.max_posts, args.offset)
            time.sleep(2)
        downloader.print_stats()
        return

    if args.creator:
        if args.api:
            downloader.download_creator_from_api(args.creator, max_posts=args.max_posts, offset=args.offset)
        elif args.posts:
            if args.incremental:
                downloader.download_incremental(args.creator, args.posts, args.max_posts)
            else:
                downloader.download_creator(args.creator, args.posts, args.max_posts, offset=args.offset)
        downloader.print_stats()
        return

    parser.print_help()
    print("\n💡 Examples:")
    print("   python coomer_batch_downloader.py -c myla.feet --api")
    print("   python coomer_batch_downloader.py --all --config creators.json --api --max-posts 5")
    print("   python coomer_batch_downloader.py -c myla.feet --api --max-posts 20")


if __name__ == "__main__":
    main()
