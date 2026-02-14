#!/usr/bin/env python3
"""
Complete Coomer.st Gallery Downloader with Full Metadata
Downloads complete galleries with rich context for interface display
"""

import requests
import json
import time
import os
from typing import Dict, List, Optional
from datetime import datetime
from urllib.parse import urljoin
import re

class CoomerGalleryDownloader:
    def __init__(self, flaresolverr_url: str = "http://localhost:8191"):
        self.flaresolverr_url = flaresolverr_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://coomer.st/',
        })
        
        # Output directories
        self.base_dir = "/home/warby/Workspace/jupyter/downloads"
        self.gallery_dir = os.path.join(self.base_dir, "galleries")
        self.metadata_dir = os.path.join(self.base_dir, "metadata")
        
        os.makedirs(self.gallery_dir, exist_ok=True)
        os.makedirs(self.metadata_dir, exist_ok=True)
    
    def solve_with_flaresolverr(self, url: str, max_retries: int = 3) -> Optional[str]:
        """Use FlareSolverr to bypass Cloudflare"""
        for attempt in range(max_retries):
            try:
                payload = {
                    "cmd": "request.get",
                    "url": url,
                    "maxTimeout": 60000,
                    "headers": {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Accept': 'application/json, text/plain, */*',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': 'https://coomer.st/'
                    }
                }
                
                response = requests.post(f"{self.flaresolverr_url}/v1", json=payload, timeout=120)
                result = response.json()
                
                if result.get("status") == "ok":
                    solution = result.get("solution", {})
                    if solution.get("status") == 200:
                        return solution.get("response", "")
                
            except Exception as e:
                print(f"  FlareSolverr attempt {attempt + 1} failed: {str(e)}")
                time.sleep(2 ** attempt)
        
        return None
    
    def get_creator_profile(self, creator_id: str, service: str = "onlyfans") -> Optional[Dict]:
        """Get full creator profile"""
        url = f"https://coomer.st/api/v1/{service}/user/{creator_id}"
        
        content = self.solve_with_flaresolverr(url)
        if content:
            try:
                return json.loads(content)
            except:
                pass
        return None
    
    def get_creator_posts(self, creator_id: str, service: str = "onlyfans", limit: int = 50) -> List[Dict]:
        """Get all posts for a creator"""
        url = f"https://coomer.st/api/v1/{service}/user/{creator_id}/posts?limit={limit}"
        
        content = self.solve_with_flaresolverr(url)
        if content:
            try:
                posts = json.loads(content)
                if isinstance(posts, list):
                    return posts
            except:
                pass
        return []
    
    def download_media(self, media_url: str, local_path: str) -> bool:
        """Download a media file with HTML wrapper bypass"""
        if os.path.exists(local_path):
            print(f"    ✓ Already exists: {os.path.basename(local_path)}")
            return True
        
        # First try direct download
        try:
            response = requests.get(media_url, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://coomer.st/',
                'Accept': 'image/*,*/*;q=0.8',
            }, timeout=30)
            
            if response.status_code == 200 and len(response.content) > 10000:  # Skip small error pages
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                size_kb = len(response.content) / 1024
                print(f"    ✓ Downloaded: {os.path.basename(local_path)} ({size_kb:.1f} KB)")
                return True
        except:
            pass
        
        # Fallback: use FlareSolverr
        print(f"    → Using FlareSolverr for {os.path.basename(local_path)}...")
        
        content = self.solve_with_flaresolverr(media_url)
        if content and len(content) > 10000:
            # Check if it's an HTML wrapper
            if content.strip().startswith('<'):
                # Parse HTML to get actual image URL
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content, 'html.parser')
                img_tag = soup.find('img')
                
                if img_tag and img_tag.get('src'):
                    actual_url = img_tag['src']
                    # Download the actual image
                    response = requests.get(actual_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Referer': 'https://coomer.st/',
                        'Accept': 'image/*,*/*;q=0.8',
                    }, timeout=60)
                    
                    if response.status_code == 200:
                        with open(local_path, 'wb') as f:
                            f.write(response.content)
                        size_kb = len(response.content) / 1024
                        print(f"    ✓ Downloaded via proxy: {os.path.basename(local_path)} ({size_kb:.1f} KB)")
                        return True
        
        print(f"    ✗ Failed: {os.path.basename(local_path)}")
        return False
    
    def download_gallery(self, creator_id: str, service: str = "onlyfans", max_posts: int = 10):
        """Download complete gallery with full metadata"""
        print(f"\n🎯 Downloading gallery for: {creator_id} (@{service})")
        print(f"   Output: {self.gallery_dir}/{creator_id}")
        
        # Create creator directory
        creator_dir = os.path.join(self.gallery_dir, creator_id)
        os.makedirs(creator_dir, exist_ok=True)
        
        # Get creator profile
        print(f"\n👤 Fetching creator profile...")
        profile = self.get_creator_profile(creator_id, service)
        
        if profile:
            print(f"   ✓ Creator: {profile.get('name', creator_id)}")
            print(f"   ✓ Posts: {profile.get('posts', 'N/A')}")
            print(f"   ✓ Favorites: {profile.get('favorites', 'N/A')}")
        else:
            print(f"   ⚠ Could not fetch profile")
        
        # Get posts
        print(f"\n📄 Fetching posts...")
        posts = self.get_creator_posts(creator_id, service, max_posts)
        print(f"   ✓ Found {len(posts)} posts")
        
        # Download each post with full gallery
        downloaded_count = 0
        post_metadata = []
        
        for i, post in enumerate(posts[:max_posts]):
            post_id = post.get('id', f'post_{i}')
            title = post.get('title', 'Untitled')[:50]
            published = post.get('published', '')[:10]
            
            print(f"\n📸 Post {i+1}/{len(posts[:max_posts])}: {title}")
            print(f"   Published: {published}")
            print(f"   ID: {post_id}")
            
            # Create post directory
            post_dir = os.path.join(creator_dir, f"{post_id}_{published}")
            os.makedirs(post_dir, exist_ok=True)
            
            # Download main file
            media_files = []
            if post.get('file') and post['file'].get('path'):
                file_info = post['file']
                file_path = file_info['path']
                file_name = file_info.get('name', os.path.basename(file_path))
                media_url = f"https://coomer.st{file_path}"
                local_path = os.path.join(post_dir, file_name)
                
                if self.download_media(media_url, local_path):
                    media_files.append({
                        'type': 'main',
                        'name': file_name,
                        'path': file_path,
                        'local': local_path,
                        'size': os.path.getsize(local_path) if os.path.exists(local_path) else 0
                    })
            
            # Download attachments
            for j, attachment in enumerate(post.get('attachments', [])):
                file_path = attachment.get('path')
                if not file_path:
                    continue
                    
                file_name = attachment.get('name', f"attachment_{j+1}_{os.path.basename(file_path)}")
                media_url = f"https://coomer.st{file_path}"
                local_path = os.path.join(post_dir, file_name)
                
                if self.download_media(media_url, local_path):
                    media_files.append({
                        'type': 'attachment',
                        'index': j+1,
                        'name': file_name,
                        'path': file_path,
                        'local': local_path,
                        'size': os.path.getsize(local_path) if os.path.exists(local_path) else 0
                    })
            
            # Save post metadata
            post_data = {
                'id': post_id,
                'title': post.get('title', ''),
                'content': post.get('content', ''),
                'published': post.get('published', ''),
                'edited': post.get('edited', ''),
                'service': service,
                'creator': creator_id,
                'media_count': len(media_files),
                'media': media_files,
                'embed_url': post.get('embed_url', ''),
                'share_url': f"https://coomer.st/{service}/user/{creator_id}/post/{post_id}"
            }
            post_metadata.append(post_data)
            
            # Save individual post metadata
            post_meta_path = os.path.join(post_dir, 'metadata.json')
            with open(post_meta_path, 'w') as f:
                json.dump(post_data, f, indent=2)
            
            downloaded_count += len(media_files)
            print(f"   ✓ Media files: {len(media_files)}")
            
            # Rate limiting
            time.sleep(0.5)
        
        # Save complete gallery metadata
        gallery_metadata = {
            'creator': {
                'id': creator_id,
                'service': service,
                'profile': profile,
            },
            'gallery': {
                'posts': len(post_metadata),
                'total_media': downloaded_count,
                'created': datetime.now().isoformat(),
            },
            'posts': post_metadata
        }
        
        gallery_meta_path = os.path.join(self.metadata_dir, f"{creator_id}_gallery.json")
        with open(gallery_meta_path, 'w') as f:
            json.dump(gallery_metadata, f, indent=2)
        
        print(f"\n✅ Gallery download complete!")
        print(f"   📁 Creator: {creator_id}")
        print(f"   📄 Posts: {len(post_metadata)}")
        print(f"   🖼️  Media: {downloaded_count} files")
        print(f"   📂 Gallery: {creator_dir}")
        print(f"   📋 Metadata: {gallery_meta_path}")
        
        return gallery_metadata

def main():
    downloader = CoomerGalleryDownloader()
    
    # Download myla.feet gallery with full metadata
    downloader.download_gallery(
        creator_id="myla.feet",
        service="onlyfans",
        max_posts=5  # Download 5 posts with all media
    )

if __name__ == '__main__':
    main()