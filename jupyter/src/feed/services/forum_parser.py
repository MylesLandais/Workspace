"""Forum and thread parsing for vBulletin and other forum platforms.

Supports:
- vBulletin forums (planetsuzy.org, etc.)
- Thread parsing and image extraction
- Post content extraction
- User attribution
- Image indexing for reverse similarity search
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
import time
import random


@dataclass
class ForumPost:
    """Forum post information."""
    post_id: str
    thread_id: str
    author: str
    content: str
    post_date: Optional[str] = None
    images: List[str] = None
    attachments: List[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ForumThread:
    """Forum thread information."""
    thread_id: str
    title: str
    url: str
    forum_name: str
    author: str
    created_date: Optional[str] = None
    posts: List[ForumPost] = None
    images: List[str] = None
    tags: List[str] = None
    metadata: Optional[Dict[str, Any]] = None


class VBulletinParser:
    """Parser for vBulletin forum software."""
    
    def __init__(self, base_url: str, delay_min: float = 2.0, delay_max: float = 5.0):
        """
        Initialize vBulletin parser.
        
        Args:
            base_url: Forum base URL (e.g., "http://www.planetsuzy.org")
            delay_min: Minimum delay between requests
            delay_max: Maximum delay between requests
        """
        self.base_url = base_url.rstrip('/')
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        })
    
    def _delay(self):
        """Random delay between requests."""
        time.sleep(random.uniform(self.delay_min, self.delay_max))
    
    def parse_thread(self, thread_url: str) -> Optional[ForumThread]:
        """
        Parse a vBulletin thread.
        
        Args:
            thread_url: Full thread URL
            
        Returns:
            ForumThread object or None
        """
        self._delay()
        
        try:
            response = self.session.get(thread_url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract thread ID from URL
            thread_id_match = re.search(r'showthread\.php\?.*?t=(\d+)', thread_url)
            if not thread_id_match:
                thread_id_match = re.search(r'p=(\d+)', thread_url)
            thread_id = thread_id_match.group(1) if thread_id_match else None
            
            # Extract thread title
            title_elem = soup.find('title')
            title = title_elem.get_text(strip=True) if title_elem else "Untitled"
            
            # Extract forum name
            forum_elem = soup.find('a', href=re.compile(r'forumdisplay\.php'))
            forum_name = forum_elem.get_text(strip=True) if forum_elem else "Unknown"
            
            # Extract thread author (first post)
            first_post = soup.find('div', id=re.compile(r'post_message_\d+'))
            author = "Unknown"
            if first_post:
                author_elem = first_post.find_previous('a', class_=re.compile(r'bigusername|username'))
                if author_elem:
                    author = author_elem.get_text(strip=True)
            
            # Extract all posts
            posts = self._extract_posts(soup, thread_id)
            
            # Extract all images from thread
            all_images = []
            for post in posts:
                if post.images:
                    all_images.extend(post.images)
            
            # Extract tags/keywords from title and content
            tags = self._extract_tags(title, posts)
            
            return ForumThread(
                thread_id=thread_id or "",
                title=title,
                url=thread_url,
                forum_name=forum_name,
                author=author,
                posts=posts,
                images=list(set(all_images)),  # Deduplicate
                tags=tags
            )
        except Exception as e:
            print(f"Error parsing thread {thread_url}: {e}")
            return None
    
    def _extract_posts(self, soup: BeautifulSoup, thread_id: str) -> List[ForumPost]:
        """Extract all posts from thread."""
        posts = []
        
        # vBulletin post structure
        post_elements = soup.find_all('div', id=re.compile(r'post_message_\d+'))
        
        for post_elem in post_elements:
            # Extract post ID
            post_id_match = re.search(r'post_message_(\d+)', post_elem.get('id', ''))
            post_id = post_id_match.group(1) if post_id_match else None
            
            if not post_id:
                continue
            
            # Extract author
            author_elem = post_elem.find_previous('a', class_=re.compile(r'bigusername|username'))
            author = author_elem.get_text(strip=True) if author_elem else "Unknown"
            
            # Extract content
            content = post_elem.get_text(strip=True)
            
            # Extract images
            images = []
            img_tags = post_elem.find_all('img')
            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'http:' + src
                    elif src.startswith('/'):
                        src = self.base_url + src
                    elif not src.startswith('http'):
                        src = urljoin(self.base_url, src)
                    images.append(src)
            
            # Extract attachments
            attachments = []
            attachment_links = post_elem.find_all('a', href=re.compile(r'attachment|download'))
            for link in attachment_links:
                href = link.get('href', '')
                if href:
                    if href.startswith('/'):
                        href = self.base_url + href
                    attachments.append(href)
            
            # Extract post date
            date_elem = post_elem.find_previous('div', class_=re.compile(r'postdate|post_date'))
            post_date = date_elem.get_text(strip=True) if date_elem else None
            
            posts.append(ForumPost(
                post_id=post_id or "",
                thread_id=thread_id or "",
                author=author,
                content=content,
                post_date=post_date,
                images=images,
                attachments=attachments
            ))
        
        return posts
    
    def _extract_tags(self, title: str, posts: List[ForumPost]) -> List[str]:
        """Extract tags/keywords from thread title and posts."""
        tags = set()
        
        # Extract from title (common patterns)
        # Look for performer names, keywords in quotes or brackets
        title_lower = title.lower()
        
        # Common patterns: [Performer Name], "Performer Name", etc.
        quoted = re.findall(r'["\']([^"\']+)["\']', title)
        bracketed = re.findall(r'\[([^\]]+)\]', title)
        
        tags.update([t.strip() for t in quoted])
        tags.update([t.strip() for t in bracketed])
        
        # Extract keywords from first post
        if posts:
            first_post_content = posts[0].content.lower()
            # Look for common keywords
            keywords = ['braces', 'teen', 'fetish', 'nude', 'photos']
            for keyword in keywords:
                if keyword in first_post_content or keyword in title_lower:
                    tags.add(keyword)
        
        return list(tags)
    
    def search_threads(
        self,
        query: str,
        limit: int = 50
    ) -> List[ForumThread]:
        """
        Search for threads matching query.
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching threads
        """
        # vBulletin search URL format
        search_url = f"{self.base_url}/search.php"
        self._delay()
        
        try:
            # vBulletin search typically requires POST with form data
            search_params = {
                'do': 'process',
                'query': query,
                'searchthreadid': 0,
                'exactname': 0,
            }
            
            response = self.session.post(search_url, data=search_params, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            threads = []
            
            # Extract thread links from search results
            thread_links = soup.find_all('a', href=re.compile(r'showthread\.php'))
            
            seen_threads = set()
            for link in thread_links[:limit]:
                href = link.get('href', '')
                if href:
                    # Extract thread ID
                    thread_id_match = re.search(r't=(\d+)', href)
                    if thread_id_match:
                        thread_id = thread_id_match.group(1)
                        if thread_id not in seen_threads:
                            seen_threads.add(thread_id)
                            thread_url = urljoin(self.base_url, href)
                            thread = self.parse_thread(thread_url)
                            if thread:
                                threads.append(thread)
            
            return threads
        except Exception as e:
            print(f"Error searching threads: {e}")
            return []
