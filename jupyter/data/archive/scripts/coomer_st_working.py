#!/usr/bin/env python3
"""
Final Working FlareSolverr-Enhanced Coomer.st Scraper
"""

import requests
import json
import time
import os
import hashlib
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Tuple
import re
from datetime import datetime
import argparse

class FlareSolverrCoomerScraper:
    def __init__(self, base_url: str = "https://coomer.st", flaresolverr_url: str = "http://localhost:8191"):
        self.base_url = base_url
        self.flaresolverr_url = flaresolverr_url
        self.session = requests.Session()
        
        # Standard headers for requests
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://coomer.st/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        })
        
        self.cache_dir = "cache"
        self.downloads_dir = "downloads"
        os.makedirs(self.cache_dir, exist_ok=True)
        os.makedirs(self.downloads_dir, exist_ok=True)
    
    def solve_with_flaresolverr(self, url: str, cmd: str = "request.get", method: str = "GET", 
                             post_data: dict = None, max_retries: int = 3) -> Optional[Dict]:
        """
        Use FlareSolverr to bypass Cloudflare protection
        """
        for attempt in range(max_retries):
            try:
                print(f"FlareSolverr attempt {attempt + 1}/{max_retries} for: {url}")
                
                # Prepare FlareSolverr request
                payload = {
                    "cmd": cmd,
                    "url": url,
                    "maxTimeout": 60000,
                    "headers": {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                        'Accept': 'application/json, text/plain, */*' if method == "GET" else 'application/x-www-form-urlencoded',
                        'Accept-Language': 'en-US,en;q=0.9',
                        'Referer': 'https://coomer.st/'
                    }
                }
                
                if method.upper() == "POST" and post_data:
                    payload["postData"] = post_data
                
                # Send to FlareSolverr
                response = requests.post(f"{self.flaresolverr_url}/v1", 
                                     json=payload, 
                                     timeout=120)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get("status") == "ok":
                    solution = result.get("solution", {})
                    if solution.get("status") == 200:
                        # Extract cookies and user agent from FlareSolverr response
                        cookies = solution.get("cookies", [])
                        user_agent = solution.get("userAgent", "")
                        
                        # Update session with FlareSolverr cookies
                        if cookies:
                            self.session.cookies.update({
                                cookie['name']: cookie['value'] 
                                for cookie in cookies
                            })
                        
                        if user_agent:
                            self.session.headers.update({
                                'User-Agent': user_agent
                            })
                        
                        print(f"✅ FlareSolverr successfully solved: {url}")
                        return {
                            'content': solution.get("response", ""),
                            'cookies': cookies,
                            'user_agent': user_agent,
                            'status_code': solution.get("status")
                        }
                    else:
                        print(f"❌ FlareSolverr returned status {solution.get('status')}")
                
                print(f"❌ FlareSolverr failed: {result.get('message', 'Unknown error')}")
                
            except Exception as e:
                print(f"❌ FlareSolverr error (attempt {attempt + 1}): {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        
        return None
    
    def get_with_fallback(self, url: str, use_flaresolverr: bool = True):
        """
        Try direct request first, fallback to FlareSolverr if needed
        """
        # Always use FlareSolverr since it works reliably
        solution = self.solve_with_flaresolverr(url)
        if solution:
            class MockResponse:
                def __init__(self, content, status_code=200):
                    self.content = content.encode() if isinstance(content, str) else content
                    self.status_code = status_code
                    self.text = content
                    self.json = lambda: json.loads(content) if isinstance(content, str) and content.strip().startswith('{') else content
            
            return MockResponse(solution['content'], solution['status_code'])
        
        return None
    
    def get_creator_profile(self, creator_id: str, service: str = "onlyfans"):
        """Get creator profile information"""
        url = f"{self.base_url}/api/v1/{service}/user/{creator_id}/profile"
        
        response = self.get_with_fallback(url)
        if response and response.status_code == 200:
            try:
                return response.json()
            except:
                return None
        
        return None
    
    def get_creator_posts(self, creator_id: str, service: str = "onlyfans"):
        """Get posts for a specific creator using FlareSolverr if needed"""
        url = f"{self.base_url}/api/v1/{service}/user/{creator_id}/posts"
        
        response = self.get_with_fallback(url)
        if response and response.status_code == 200:
            try:
                content = response.text
                if content.strip().startswith('['):
                    return response.json()
                else:
                    print(f"❌ Invalid JSON response from: {url}")
                    return []
            except:
                print(f"❌ Failed to parse JSON from: {url}")
                return []
        
        print(f"❌ Failed to fetch posts for {creator_id}")
        return []
    
    def download_media_file(self, media_url: str, local_path: str) -> bool:
        """Download a media file using FlareSolverr for bypass if needed"""
        if os.path.exists(local_path):
            # Check file size to avoid re-downloading
            if os.path.getsize(local_path) > 1000:  # More than 1KB
                print(f"✅ File already exists: {local_path}")
                return True
        
        # Create directory if needed
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        # Use FlareSolverr for media downloads
        try:
            response = self.get_with_fallback(media_url)
            if response and response.status_code == 200:
                with open(local_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Downloaded: {local_path}")
                return True
        except Exception as e:
            print(f"❌ Download failed for {media_url}: {str(e)}")
        
        return False
    
    def scrape_creator(self, creator_id: str, service: str = "onlyfans", max_posts: int = 50):
        """Main scraping function"""
        print(f"🎯 Starting scrape for {creator_id} ({service})")
        
        # Get creator profile
        profile = self.get_creator_profile(creator_id, service)
        if profile:
            print(f"👤 Found creator: {profile.get('name')}")
        
        # Get posts
        posts = self.get_creator_posts(creator_id, service)
        if not posts:
            print("❌ No posts found")
            return {}
        
        posts = posts[:max_posts]
        print(f"📄 Processing {len(posts)} posts")
        
        # Process posts
        media_count = 0
        for i, post in enumerate(posts):
            print(f"📸 Post {i+1}/{len(posts)}: {post.get('title', 'No title')[:50]}")
            
            # Process main file if exists
            if 'file' in post and post['file']:
                file_path = post['file']['path']
                if file_path:
                    media_url = f"{self.base_url}{file_path}"
                    filename = os.path.basename(file_path)
                    local_path = os.path.join(self.downloads_dir, creator_id, filename)
                    
                    if self.download_media_file(media_url, local_path):
                        media_count += 1
            
            # Process attachments
            for j, attachment in enumerate(post.get('attachments', [])):
                if 'path' in attachment:
                    file_path = attachment['path']
                    if file_path:
                        media_url = f"{self.base_url}{file_path}"
                        filename = f"attachment_{j+1}_{os.path.basename(file_path)}"
                        local_path = os.path.join(self.downloads_dir, creator_id, filename)
                        
                        if self.download_media_file(media_url, local_path):
                            media_count += 1
            
            # Rate limiting
            time.sleep(1)
        
        print(f"✅ Scraping complete! Downloaded {media_count} media files")
        
        # Save metadata
        metadata = {
            'creator_id': creator_id,
            'service': service,
            'profile': profile,
            'posts_processed': len(posts),
            'media_downloaded': media_count,
            'scrape_time': datetime.now().isoformat()
        }
        
        metadata_path = os.path.join(self.downloads_dir, creator_id, 'metadata.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        return metadata

def main():
    parser = argparse.ArgumentParser(description='Enhanced Coomer.st scraper with FlareSolverr')
    parser.add_argument('--creator', help='Creator ID to scrape')
    parser.add_argument('--service', choices=['onlyfans', 'fansly', 'candfans'], 
                       default='onlyfans', help='Service to scrape from')
    parser.add_argument('--max-posts', type=int, default=50, 
                       help='Maximum number of posts to scrape')
    parser.add_argument('--output', default='downloads', help='Output directory')
    parser.add_argument('--flaresolverr-url', default='http://localhost:8191', 
                       help='FlareSolverr URL')
    
    args = parser.parse_args()
    
    if not args.creator:
        parser.error("Creator ID is required")
    
    # Initialize scraper
    scraper = FlareSolverrCoomerScraper(flaresolverr_url=args.flaresolverr_url)
    scraper.downloads_dir = args.output
    
    # Start scraping
    result = scraper.scrape_creator(args.creator, args.service, args.max_posts)
    
    if result:
        print(f"🎉 Scraping successful! Check {args.output}/{args.creator}")
    else:
        print("❌ Scraping failed")

if __name__ == '__main__':
    main()