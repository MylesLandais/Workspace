"""Fapello platform adapter for media content crawling."""

import os
import time
import random
import re
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

from .base import PlatformAdapter
from ..models.media import ImageMedia
from ..models.subreddit import Subreddit
from ..ontology.schema import MediaType


class FapelloAdapter(PlatformAdapter):
    """Fapello adapter for crawling media content."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        mock: bool = False,
    ):
        """
        Initialize Fapello adapter.
        
        Args:
            user_agent: Custom User-Agent string
            delay_min: Minimum delay between requests (seconds)
            delay_max: Maximum delay between requests (seconds)
            mock: If True, return mock data without network requests
        """
        self.user_agent = (
            user_agent
            or os.getenv("FEED_USER_AGENT", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        )
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.mock = mock
        self.headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }

    def _delay(self) -> None:
        """Add human-like delay between requests."""
        if not self.mock:
            delay = random.uniform(self.delay_min, self.delay_max)
            time.sleep(delay)

    def fetch_posts(
        self,
        source: str,
        sort: str = "new",
        limit: int = 100,
        after: Optional[str] = None,
    ) -> Tuple[List, Optional[str]]:
        """
        Fetch media items from a Fapello profile.
        
        Args:
            source: Profile username or profile URL
            sort: Sort order (not used for Fapello)
            limit: Maximum media items per page
            after: Pagination token (not used for Fapello)
        
        Returns:
            Tuple of (list of media items, next page token or None)
        """
        # Convert source to profile URL if needed
        if not source.startswith("http"):
            profile_url = f"https://fapello.com/{source}/"
        else:
            profile_url = source
        
        media_items = self.fetch_media(profile_url, limit=limit)
        return media_items, None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch profile metadata (using Subreddit model for compatibility).
        
        Args:
            source: Profile username or URL
        
        Returns:
            Subreddit-like metadata or None
        """
        if self.mock:
            return Subreddit(
                name=source,
                subscribers=0,
                created_utc=datetime.utcnow(),
                description=f"Fapello profile: {source}",
            )
        
        # Extract username from source
        if source.startswith("http"):
            match = re.search(r'fapello\.com/([^/]+)/?', source)
            if match:
                username = match.group(1)
            else:
                return None
        else:
            username = source
        
        profile_url = f"https://fapello.com/{username}/"
        
        try:
            response = requests.get(profile_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract profile metadata
            title = self._extract_profile_title(soup)
            media_count = self._extract_media_count(soup)
            likes_count = self._extract_likes_count(soup)
            
            return Subreddit(
                name=username,
                subscribers=likes_count,
                created_utc=datetime.utcnow(),
                description=f"Fapello profile: {title} ({media_count} media)",
            )
        except Exception as e:
            print(f"Error fetching profile metadata: {e}")
            return None

    def fetch_media(self, profile_url: str, limit: Optional[int] = None, max_pages: Optional[int] = None) -> List[ImageMedia]:
        """
        Fetch all media items from a Fapello profile page with pagination support.
        
        Args:
            profile_url: Full URL to Fapello profile page (e.g., https://fapello.com/sjokz/)
            limit: Maximum number of media items to fetch (None = all available)
            max_pages: Maximum number of pages to crawl (None = all pages)
        
        Returns:
            List of ImageMedia objects
        """
        if self.mock:
            return self._fetch_media_mock(profile_url)
        
        all_media_items = []
        current_url = profile_url
        page_num = 1
        seen_urls = set()  # Track seen media URLs to avoid duplicates
        
        try:
            while current_url:
                # Check page limit
                if max_pages and page_num > max_pages:
                    print(f"Reached max_pages limit ({max_pages})")
                    break
                
                # Check item limit
                if limit and len(all_media_items) >= limit:
                    print(f"Reached item limit ({limit})")
                    break
                
                print(f"Fetching page {page_num} from {current_url}...")
                response = requests.get(current_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Parse media items from current page
                page_media_items = self._parse_media_grid(soup, profile_url, limit=None)
                
                # Filter out duplicates and add new items
                new_items = []
                for item in page_media_items:
                    if item.source_url not in seen_urls:
                        seen_urls.add(item.source_url)
                        new_items.append(item)
                
                all_media_items.extend(new_items)
                print(f"  Found {len(new_items)} new items on page {page_num} (total: {len(all_media_items)})")
                
                # Find next page link
                next_url = self._find_next_page_link(soup, profile_url)
                
                if not next_url or next_url == current_url:
                    # No more pages
                    print(f"  No more pages found after page {page_num}")
                    break
                
                current_url = next_url
                page_num += 1
                
                # Delay between pages
                self._delay()
                
        except requests.RequestException as e:
            print(f"Error fetching profile {profile_url}: {e}")
        except Exception as e:
            print(f"Error parsing profile {profile_url}: {e}")
        
        # Apply limit if specified
        if limit:
            all_media_items = all_media_items[:limit]
        
        print(f"\nTotal media items collected: {len(all_media_items)}")
        return all_media_items

    def _find_next_page_link(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """
        Find the URL for the next page of media.
        
        Args:
            soup: BeautifulSoup object of current page
            base_url: Base profile URL
        
        Returns:
            URL of next page or None if no next page
        """
        # Look for "Next Page" link or pagination controls
        # Common patterns:
        # - Link with text "Next Page" or "Next"
        # - Link with rel="next"
        # - Pagination links (page 2, page 3, etc.)
        
        # Try finding "Next Page" link
        next_links = soup.find_all('a', href=True, string=re.compile(r'Next Page|Next', re.I))
        if next_links:
            href = next_links[0].get('href')
            if href:
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        # Try finding link with rel="next"
        next_link = soup.find('a', {'rel': 'next'}, href=True)
        if next_link:
            href = next_link.get('href')
            if href:
                if href.startswith('http'):
                    return href
                else:
                    return urljoin(base_url, href)
        
        # Try finding pagination link (look for page number in URL)
        # Patterns: /username/page-2/, /username/page/2/, /username?page=2, etc.
        username = self._extract_username_from_url(base_url)
        pagination_patterns = [
            re.compile(rf'{re.escape(username)}/page-(\d+)', re.I),  # page-2, page-3
            re.compile(rf'{re.escape(username)}/page/(\d+)', re.I),  # page/2, page/3
        ]
        
        # Find all links and check if any match pagination pattern
        all_links = soup.find_all('a', href=True)
        current_page = 1
        
        # Try to determine current page from URL (try multiple patterns)
        current_url_patterns = [
            re.search(r'/page-(\d+)', base_url),
            re.search(r'/page/(\d+)', base_url),
            re.search(r'[?&]page=(\d+)', base_url),
        ]
        for pattern_match in current_url_patterns:
            if pattern_match:
                current_page = int(pattern_match.group(1))
                break
        
        # Look for next page number using the patterns
        next_page_num = current_page + 1
        for link in all_links:
            href = link.get('href', '')
            for pagination_pattern in pagination_patterns:
                match = pagination_pattern.search(href)
                if match:
                    page_num = int(match.group(1))
                    if page_num == next_page_num:
                        if href.startswith('http'):
                            return href
                        else:
                            return urljoin(base_url, href)
        
        # If no link found but we know the pattern, construct next page URL
        # Try constructing URL based on detected pattern
        if current_page == 1:
            # First page - try constructing page-2 URL
            base_profile_url = f"https://fapello.com/{username}/"
            if base_url == base_profile_url or base_url == base_profile_url.rstrip('/'):
                # Construct page-2 URL
                return f"{base_profile_url}page-{next_page_num}/"
        
        return None

    def _parse_media_grid(self, soup: BeautifulSoup, base_url: str, limit: Optional[int] = None) -> List[ImageMedia]:
        """Parse media grid from profile page."""
        media_items = []
        
        # Extract username from URL
        username = self._extract_username_from_url(base_url)
        
        # Find the media grid container
        # The grid has id="content" and class: "my-6 grid lg:grid-cols-4 grid-cols-2 gap-1.5 hover:text-yellow-700 uk-link-reset"
        grid_selectors = [
            'div#content',
            '#content',
            'div[class*="grid"][class*="grid-cols"]',
            '.grid.lg\\:grid-cols-4',
        ]
        
        grid = None
        for selector in grid_selectors:
            try:
                grid = soup.select_one(selector)
                if grid:
                    break
            except Exception:
                continue
        
        if not grid:
            print("Could not find media grid container")
            return []
        
        # Find all media item links
        # Each item is in: <div><a href="https://fapello.com/{username}/{id}/"><div><img src="..."></div></a></div>
        media_links = grid.find_all('a', href=True)
        
        limit_value = limit if limit else len(media_links)
        
        for link in media_links[:limit_value]:
            href = link.get('href', '')
            if not href or not href.startswith('http'):
                href = urljoin(base_url, href)
            
            # Extract media ID from URL
            media_id = self._extract_media_id(href, username)
            if not media_id:
                continue
            
            # Find image in the link
            img = link.find('img')
            if not img:
                continue
            
            # Extract thumbnail URL
            thumbnail_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not thumbnail_url:
                continue
            
            # Convert relative URLs to absolute
            # Handle different URL formats:
            # - Relative: sjokz_1713_300px.jpg -> https://fapello.com/content/sjokz/sjokz_1713_300px.jpg
            # - Absolute: https://fapello.com/content/sjokz/sjokz_1713_300px.jpg
            # - Protocol-relative: //fapello.com/...
            
            if thumbnail_url.startswith('//'):
                thumbnail_url = 'https:' + thumbnail_url
            elif thumbnail_url.startswith('/'):
                thumbnail_url = 'https://fapello.com' + thumbnail_url
            elif not thumbnail_url.startswith('http'):
                # Relative URL - construct absolute path
                # Pattern: {username}_{id}_300px.jpg -> https://fapello.com/content/{username}/{username}_{id}_300px.jpg
                if '_300px' in thumbnail_url or username in thumbnail_url:
                    # Extract filename
                    filename = thumbnail_url.split('/')[-1]
                    thumbnail_url = f"https://fapello.com/content/{username}/{filename}"
                else:
                    thumbnail_url = urljoin(base_url, thumbnail_url)
            
            # Create ImageMedia object
            media_item = ImageMedia(
                title=f"{username} - {media_id}",
                source_url=href,
                publish_date=datetime.utcnow(),  # Fapello doesn't expose publish dates easily
                thumbnail_url=thumbnail_url,
                media_type=MediaType.IMAGE,
                platform_name="Fapello",
                platform_slug="fapello",
            )
            
            media_items.append(media_item)
        
        return media_items

    def _extract_username_from_url(self, url: str) -> str:
        """Extract username from Fapello URL."""
        match = re.search(r'fapello\.com/([^/]+)/?', url)
        if match:
            return match.group(1)
        return "unknown"

    def _extract_media_id(self, url: str, username: str) -> Optional[str]:
        """Extract media ID from Fapello media URL."""
        # URL format: https://fapello.com/{username}/{id}/
        pattern = rf'fapello\.com/{re.escape(username)}/(\d+)/?'
        match = re.search(pattern, url)
        if match:
            return match.group(1)
        return None

    def _construct_full_image_url(self, thumbnail_url: str, username: str, media_id: str) -> Optional[str]:
        """
        Try to construct full-size image URL from thumbnail URL.
        
        Thumbnails are typically: {username}_{id}_300px.jpg
        Full images might be: {username}_{id}.jpg
        """
        # Extract base URL pattern
        # If thumbnail is: https://fapello.com/content/sjokz/sjokz_1713_300px.jpg
        # Try: https://fapello.com/content/sjokz/sjokz_1713.jpg
        
        # Get the domain and path
        parsed = urlparse(thumbnail_url)
        path = parsed.path
        
        # Remove _300px from filename
        if '_300px' in path:
            full_path = path.replace('_300px', '')
            full_url = f"{parsed.scheme}://{parsed.netloc}{full_path}"
            return full_url
        
        # Alternative: construct from username and media_id
        if username and media_id:
            # Try standard pattern: https://fapello.com/content/{username}/{username}_{id}.jpg
            return f"https://fapello.com/content/{username}/{username}_{media_id}.jpg"
        
        return None

    def _extract_profile_title(self, soup: BeautifulSoup) -> str:
        """Extract profile title/name."""
        # Try various selectors for profile name
        selectors = [
            'h1',
            'h2',
            '.profile-name',
            '[class*="profile"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                text = element.get_text(strip=True)
                if text and len(text) < 200:  # Reasonable title length
                    return text
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            # Remove " - Fapello" suffix if present
            title = re.sub(r'\s*-\s*Fapello\s*$', '', title, flags=re.IGNORECASE)
            return title
        
        return "Unknown Profile"

    def _extract_media_count(self, soup: BeautifulSoup) -> int:
        """Extract total media count from profile page."""
        # Look for text like "1712 Media"
        text = soup.get_text()
        match = re.search(r'(\d+)\s+Media', text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return 0

    def _extract_likes_count(self, soup: BeautifulSoup) -> int:
        """Extract total likes count from profile page."""
        # Look for text like "472 Likes"
        text = soup.get_text()
        match = re.search(r'(\d+)\s+Likes', text, re.IGNORECASE)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return 0

    def fetch_individual_media(self, media_url: str) -> Optional[ImageMedia]:
        """
        Fetch a single media item from its individual page.
        
        This can be used to get full-size images and additional metadata.
        
        Args:
            media_url: Full URL to individual media page (e.g., https://fapello.com/sjokz/1713/)
        
        Returns:
            ImageMedia object or None if fetch fails
        """
        if self.mock:
            return self._fetch_individual_media_mock(media_url)
        
        try:
            response = requests.get(media_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract full-size image
            # Look for the main image on the page
            # Fapello individual pages typically have the full image in various locations
            img_selectors = [
                'img[class*="media"]',
                'img[class*="content"]',
                '.media-content img',
                'main img',
                'article img',
                'div[class*="media"] img',
                'div[class*="content"] img',
            ]
            
            full_image_url = None
            for selector in img_selectors:
                try:
                    imgs = soup.select(selector)
                    for img in imgs:
                        src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                        if src and '_300px' not in src:  # Avoid thumbnails
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = 'https://fapello.com' + src
                            elif not src.startswith('http'):
                                src = urljoin(media_url, src)
                            full_image_url = src
                            break
                    if full_image_url:
                        break
                except Exception:
                    continue
            
            # Extract username and media ID from URL
            username = self._extract_username_from_url(media_url)
            media_id = self._extract_media_id(media_url, username)
            
            # If we couldn't find a full image, try constructing it from the media URL
            if not full_image_url and username and media_id:
                full_image_url = f"https://fapello.com/content/{username}/{username}_{media_id}.jpg"
            
            # If we have a thumbnail URL pattern, construct it
            thumbnail_url = None
            if username and media_id:
                thumbnail_url = f"https://fapello.com/content/{username}/{username}_{media_id}_300px.jpg"
            
            media_item = ImageMedia(
                title=f"{username} - {media_id}",
                source_url=media_url,
                publish_date=datetime.utcnow(),
                thumbnail_url=thumbnail_url,
                media_type=MediaType.IMAGE,
                platform_name="Fapello",
                platform_slug="fapello",
            )
            
            # If we found a full image, we could update the thumbnail_url or add it as a separate field
            # For now, we'll use the full image URL if available
            if full_image_url:
                # In a more complete implementation, we might want to store both
                # For now, prefer full image over thumbnail
                media_item.thumbnail_url = full_image_url
            
            self._delay()
            return media_item
            
        except requests.RequestException as e:
            print(f"Error fetching media {media_url}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing media {media_url}: {e}")
            return None

    def _fetch_media_mock(self, profile_url: str) -> List[ImageMedia]:
        """Return mock media items for testing."""
        username = self._extract_username_from_url(profile_url)
        return [
            ImageMedia(
                title=f"{username} - 1713",
                source_url=f"https://fapello.com/{username}/1713/",
                publish_date=datetime.utcnow(),
                thumbnail_url=f"https://fapello.com/content/{username}/{username}_1713_300px.jpg",
                media_type=MediaType.IMAGE,
                platform_name="Fapello",
                platform_slug="fapello",
            ),
            ImageMedia(
                title=f"{username} - 1712",
                source_url=f"https://fapello.com/{username}/1712/",
                publish_date=datetime.utcnow(),
                thumbnail_url=f"https://fapello.com/content/{username}/{username}_1712_300px.jpg",
                media_type=MediaType.IMAGE,
                platform_name="Fapello",
                platform_slug="fapello",
            ),
        ]

    def _fetch_individual_media_mock(self, media_url: str) -> ImageMedia:
        """Return mock individual media for testing."""
        username = self._extract_username_from_url(media_url)
        media_id = self._extract_media_id(media_url, username) or "1713"
        return ImageMedia(
            title=f"{username} - {media_id}",
            source_url=media_url,
            publish_date=datetime.utcnow(),
            thumbnail_url=f"https://fapello.com/content/{username}/{username}_{media_id}.jpg",
            media_type=MediaType.IMAGE,
            platform_name="Fapello",
            platform_slug="fapello",
        )

