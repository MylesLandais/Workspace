#!/usr/bin/env python3
"""
Coomer.st Scraper - Indirect OnlyFans Content Access
--------------------------------------------------------

A crawler for coomer.st (and related sites) that provides indirect
access to OnlyFans, Fansly, and CandFans content through public archives.

This tool scrapes:
- Creator profiles and posts
- Media files (images and videos)
- Post metadata and timestamps
- Creator information and statistics

Disclaimer: This tool only accesses publicly available archived content.
It does not bypass any paywalls or access restricted content.
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

class CoomerScraper:
    def __init__(self, base_url: str = "https://coomer.st"):
        self.base_url = base_url
        self.session = requests.Session()
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
    
    def get_creator_posts(self, creator_id: str, service: str = "onlyfans") -> List[Dict]:
        """Get posts for a specific creator"""
        url = f"{self.base_url}/api/v1/{service}/user/{creator_id}/posts"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching posts: {e}")
            return []
    
    def get_creator_info(self, creator_id: str, service: str = "onlyfans") -> Optional[Dict]:
        """Get creator information"""
        url = f"{self.base_url}/api/v1/{service}/user/{creator_id}/profile"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error fetching creator info: {e}")
            return None
    
    def download_media(self, media_url: str, filename: str) -> bool:
        """Download media file with deduplication"""
        # Generate unique hash for deduplication
        content_hash = hashlib.md5(media_url.encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{content_hash}.json")
        
        # Check if already downloaded
        if os.path.exists(cache_path):
            with open(cache_path, 'r') as f:
                cached = json.load(f)
                if cached.get('filename') == filename:
                    print(f"Already downloaded: {filename}")
                    return True
        
        try:
            response = self.session.get(media_url, stream=True, timeout=30)
            response.raise_for_status()
            
            download_path = os.path.join(self.downloads_dir, filename)
            os.makedirs(os.path.dirname(download_path), exist_ok=True)
            
            with open(download_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Cache download info
            with open(cache_path, 'w') as f:
                json.dump({
                    'filename': filename,
                    'url': media_url,
                    'timestamp': datetime.now().isoformat(),
                    'hash': content_hash
                }, f)
            
            print(f"Downloaded: {filename}")
            return True
            
        except requests.RequestException as e:
            print(f"Error downloading {media_url}: {e}")
            return False
    
    def extract_media_from_post(self, post: Dict) -> List[Tuple[str, str]]:
        """Extract media URLs from a post"""
        media_files = []
        
        # Extract attachments (images and videos)
        if 'file' in post:
            file_info = post['file']
            if file_info and 'path' in file_info:
                media_files.append((file_info['path'], file_info.get('name', 'media')))
        
        if 'attachments' in post:
            for attachment in post['attachments']:
                if 'path' in attachment:
                    media_files.append((attachment['path'], attachment.get('name', 'media')))
        
        return media_files
    
    def search_creators(self, query: str, service: str = "onlyfans", limit: int = 50) -> List[Dict]:
        """Search for creators"""
        url = f"{self.base_url}/api/v1/creators"
        params = {
            'q': query,
            'service': service,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error searching creators: {e}")
            return []
    
    def scrape_creator(self, creator_id: str, service: str = "onlyfans", max_posts: int = None) -> Dict:
        """Scrape all content from a specific creator"""
        print(f"Scraping creator {creator_id} from {service}...")
        
        # Get creator info
        creator_info = self.get_creator_info(creator_id, service)
        if not creator_info:
            return {'error': 'Failed to get creator info'}
        
        # Get posts
        posts = self.get_creator_posts(creator_id, service)
        if not posts:
            return {'error': 'No posts found'}
        
        scraped_data = {
            'creator_info': creator_info,
            'posts_processed': 0,
            'media_downloaded': 0,
            'posts': []
        }
        
        # Process each post
        for i, post in enumerate(posts):
            if max_posts and i >= max_posts:
                break
            
            post_id = post.get('id')
            print(f"Processing post {post_id} ({i+1}/{len(posts)})")
            
            # Extract media
            media_files = self.extract_media_from_post(post)
            
            # Download media
            downloaded_media = []
            for media_url, filename in media_files:
                if self.download_media(media_url, filename):
                    downloaded_media.append({
                        'url': media_url,
                        'filename': filename
                    })
            
            # Store post data
            post_data = {
                'id': post_id,
                'title': post.get('title', ''),
                'content': post.get('content', ''),
                'published': post.get('published', ''),
                'service': service,
                'creator': creator_id,
                'media_count': len(media_files),
                'media': downloaded_media
            }
            
            scraped_data['posts'].append(post_data)
            scraped_data['posts_processed'] += 1
            scraped_data['media_downloaded'] += len(downloaded_media)
            
            # Rate limiting
            time.sleep(1)
        
        # Save scraped data
        output_file = os.path.join(self.downloads_dir, f"{creator_id}_{service}_scraped.json")
        with open(output_file, 'w') as f:
            json.dump(scraped_data, f, indent=2)
        
        return scraped_data
    
    def get_trending_creators(self, service: str = "onlyfans", limit: int = 20) -> List[Dict]:
        """Get trending creators"""
        url = f"{self.base_url}/api/v1/creators/trending"
        params = {
            'service': service,
            'limit': limit
        }
        
        try:
            response = self.session.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting trending creators: {e}")
            return []

def main():
    parser = argparse.ArgumentParser(description="Coomer.st scraper for OnlyFans content")
    parser.add_argument('--creator', help="Creator ID to scrape")
    parser.add_argument('--service', choices=['onlyfans', 'fansly', 'candfans'], 
                       default='onlyfans', help='Service to scrape from')
    parser.add_argument('--search', help='Search term for creators')
    parser.add_argument('--trending', action='store_true', help='Get trending creators')
    parser.add_argument('--max-posts', type=int, help='Maximum number of posts to scrape')
    parser.add_argument('--output', default='downloads', help='Output directory')
    
    args = parser.parse_args()
    
    scraper = CoomerScraper()
    
    if args.search:
        print(f"Searching for creators: {args.search}")
        creators = scraper.search_creators(args.search, args.service)
        
        for creator in creators[:5]:  # Limit to first 5 results
            creator_id = creator.get('id') or creator.get('name')
            print(f"\nScraping: {creator.get('name', 'Unknown')} ({creator_id})")
            result = scraper.scrape_creator(creator_id, args.service, args.max_posts)
            
            if 'error' not in result:
                print(f"✓ Successfully scraped {result['posts_processed']} posts")
                print(f"✓ Downloaded {result['media_downloaded']} media files")
    
    elif args.trending:
        print(f"Getting trending creators from {args.service}")
        creators = scraper.get_trending_creators(args.service)
        
        for creator in creators:
            creator_id = creator.get('id') or creator.get('name')
            print(f"\nTrending: {creator.get('name', 'Unknown')} ({creator.get('followers', 0)} followers)")
            result = scraper.scrape_creator(creator_id, args.service, args.max_posts)
            
            if 'error' not in result:
                print(f"✓ Successfully scraped {result['posts_processed']} posts")
                print(f"✓ Downloaded {result['media_downloaded']} media files")
    
    elif args.creator:
        result = scraper.scrape_creator(args.creator, args.service, args.max_posts)
        
        if 'error' in result:
            print(f"Error: {result['error']}")
        else:
            print(f"\n✓ Successfully scraped {result['posts_processed']} posts")
            print(f"✓ Downloaded {result['media_downloaded']} media files")
            print(f"Creator: {result['creator_info'].get('name', 'Unknown')}")
    
    else:
        print("No action specified. Use --help for usage information.")

if __name__ == "__main__":
    main()