import requests
import json
import os
import time
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup

class CoomerPageScraper:
    def __init__(self, flaresolverr_url="http://localhost:8191"):
        self.flaresolverr_url = flaresolverr_url
        self.base_dir = "/home/warby/Workspace/jupyter/downloads"
        self.gallery_dir = os.path.join(self.base_dir, "galleries")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        
        os.makedirs(self.gallery_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def fetch_page(self, url, max_retries=3):
        """Fetch page via FlareSolverr"""
        for attempt in range(max_retries):
            try:
                payload = {
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": 60000,
                    "headers": {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                        'Accept-Language': 'en-US,en;q=0.9',
                    }
                }
                
                response = requests.post(f"{self.flaresolverr_url}/v1", json=payload, timeout=120)
                result = response.json()
                
                if result.get("status") == "ok":
                    solution = result.get("solution", {})
                    if solution.get("status") == 200:
                        return solution.get("response", "")
                        
            except Exception as e:
                print(f"  Attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2 ** attempt)
        
        return None
    
    def scrape_post(self, post_url, creator_id):
        """Scrape a single post page for all media"""
        print(f"\n📸 Scraping post: {post_url}")
        
        html = self.fetch_page(post_url)
        if not html:
            print("  ❌ Failed to fetch post page")
            return None
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Extract post data from page
        post_data = {
            'id': post_url.split('/')[-1],
            'url': post_url,
            'creator': creator_id,
            'scraped_at': datetime.now().isoformat(),
            'title': '',
            'content': '',
            'published': '',
            'media': []
        }
        
        # Get title
        title_elem = soup.find('h1', class_='post__title')
        if title_elem:
            post_data['title'] = title_elem.get_text(strip=True)
            print(f"  Title: {post_data['title'][:50]}")
        
        # Get published date
        time_elem = soup.find('time', class_='timestamp')
        if time_elem:
            post_data['published'] = time_elem.get('datetime', '')
            print(f"  Published: {post_data['published']}")
        
        # Get content
        content_elem = soup.find('div', class_='post__content')
        if content_elem:
            post_data['content'] = content_elem.get_text(strip=True)
            print(f"  Content length: {len(post_data['content'])} chars")
        
        # Find all media files
        media_files = []
        
        # Main file link
        file_thumbs = soup.find_all('div', class_='post__thumbnail')
        for i, thumb in enumerate(file_thumbs):
            link = thumb.find('a', class_='fileThumb')
            if link and link.get('href'):
                media_url = link['href']
                filename = link.get('download', f'file_{i+1}.jpg')
                
                # Get thumbnail src
                img = thumb.find('img')
                thumb_url = img['src'] if img and img.get('src') else ''
                
                media_files.append({
                    'index': i + 1,
                    'url': media_url,
                    'filename': filename,
                    'thumbnail': thumb_url,
                    'type': 'image' if filename.endswith(('.jpg', '.jpeg', '.png', '.webp')) else 'video'
                })
        
        post_data['media'] = media_files
        post_data['media_count'] = len(media_files)
        
        print(f"  Found {len(media_files)} media files")
        
        return post_data
    
    def download_media(self, media_url, local_path):
        """Download media file"""
        if os.path.exists(local_path):
            size = os.path.getsize(local_path)
            print(f"    ✓ Already exists: {os.path.basename(local_path)} ({size/1024:.1f} KB)")
            return True
        
        # Try direct download first
        try:
            response = requests.get(media_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://coomer.st/',
            }, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 10000:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                size = len(response.content)
                print(f"    ✓ Downloaded: {os.path.basename(local_path)} ({size/1024:.1f} KB)")
                return True
        except:
            pass
        
        print(f"    ✗ Failed to download: {os.path.basename(local_path)}")
        return False
    
    def download_creator_posts(self, creator_id, post_urls):
        """Download all specified posts for a creator"""
        print(f"\n🎯 Downloading {len(post_urls)} posts for {creator_id}")
        
        creator_dir = os.path.join(self.gallery_dir, creator_id)
        os.makedirs(creator_dir, exist_ok=True)
        
        all_posts = []
        
        for i, post_url in enumerate(post_urls[:10]):  # Limit to 10 posts
            print(f"\n[{i+1}/{len(post_urls[:10])}]")
            
            post_data = self.scrape_post(post_url, creator_id)
            if not post_data:
                continue
            
            # Create post directory
            post_id = post_data['id']
            post_dir = os.path.join(creator_dir, post_id)
            os.makedirs(post_dir, exist_ok=True)
            
            # Download all media
            for media in post_data['media']:
                local_path = os.path.join(post_dir, media['filename'])
                self.download_media(media['url'], local_path)
                media['local_path'] = local_path
            
            # Save post metadata
            post_meta_path = os.path.join(post_dir, 'metadata.json')
            with open(post_meta_path, 'w') as f:
                json.dump(post_data, f, indent=2)
            
            all_posts.append(post_data)
            
            # Rate limiting
            time.sleep(1)
        
        # Save gallery metadata
        gallery_metadata = {
            'creator': creator_id,
            'posts_count': len(all_posts),
            'total_media': sum(len(p['media']) for p in all_posts),
            'scraped_at': datetime.now().isoformat(),
            'posts': all_posts
        }
        
        gallery_meta_path = os.path.join(self.metadata_dir, f"{creator_id}_gallery.json")
        with open(gallery_meta_path, 'w') as f:
            json.dump(gallery_metadata, f, indent=2)
        
        print(f"\n✅ Gallery complete!")
        print(f"   Posts: {len(all_posts)}")
        print(f"   Total media: {gallery_metadata['total_media']}")
        print(f"   Gallery dir: {creator_dir}")
        print(f"   Metadata: {gallery_meta_path}")
        
        return gallery_metadata

# Main execution
scraper = CoomerPageScraper()

# Download specific posts for myla.feet
# Using the actual post URLs we found earlier
post_urls = [
    "https://coomer.st/onlyfans/user/myla.feet/post/1516930560",  # Snow White post
    "https://coomer.st/onlyfans/user/myla.feet/post/1507285131",  # Another post
]

scraper.download_creator_posts("myla.feet", post_urls)