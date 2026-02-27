"""Listal platform adapter for media content crawling."""

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
from ..models.media import ImageMedia, Media
from ..models.subreddit import Subreddit
from ..ontology.schema import MediaType


class ListalAdapter(PlatformAdapter):
    """Listal adapter for crawling profile images and curated lists."""

    BASE_URL = "https://www.listal.com"

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 3.0,
        delay_max: float = 7.0,
        mock: bool = False,
    ):
        """
        Initialize Listal adapter.

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
        Fetch images from a Listal profile.

        Args:
            source: Profile name or profile URL
            sort: Sort order (not used for Listal)
            limit: Maximum images per page
            after: Pagination token (not used for Listal)

        Returns:
            Tuple of (list of ImageMedia, next page token or None)
        """
        profile_url = self._make_profile_url(source)
        images = self._fetch_profile_images(profile_url, limit=limit)
        return images, None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch profile metadata.

        Args:
            source: Profile name or URL

        Returns:
            Subreddit-like metadata or None
        """
        if self.mock:
            return Subreddit(
                name=source,
                subscribers=0,
                created_utc=datetime.utcnow(),
                description=f"Listal profile: {source}",
            )

        profile_url = self._make_profile_url(source)
        try:
            response = requests.get(profile_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            image_count = self._extract_image_count(soup)
            name = self._extract_profile_name(soup) or source

            return Subreddit(
                name=source,
                subscribers=image_count,
                created_utc=datetime.utcnow(),
                description=f"Listal profile: {name} ({image_count} images)",
            )
        except Exception as e:
            print(f"Error fetching Listal profile metadata: {e}")
            return None

    def _make_profile_url(self, source: str) -> str:
        """Convert source to full profile URL."""
        if source.startswith("http"):
            return source.rstrip("/")
        if "/" in source:
            return f"{self.BASE_URL}/{source}"
        return f"{self.BASE_URL}/{source}"

    def _fetch_profile_images(
        self,
        profile_url: str,
        limit: Optional[int] = None,
    ) -> List[ImageMedia]:
        """Fetch all images from a Listal profile."""
        if self.mock:
            return self._fetch_mock_images(profile_url)

        all_images = []
        current_url = profile_url
        page_num = 1

        try:
            while current_url:
                if limit and len(all_images) >= limit:
                    break

                print(f"Fetching Listal page {page_num} from {current_url}...")
                response = requests.get(current_url, headers=self.headers, timeout=15)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')

                page_images = self._parse_profile_page(soup, profile_url, limit=limit)
                all_images.extend(page_images)
                print(f"  Found {len(page_images)} images (total: {len(all_images)})")

                current_url = self._find_next_page(soup, profile_url)
                if not current_url:
                    break

                page_num += 1
                self._delay()

        except requests.RequestException as e:
            print(f"Error fetching Listal profile {profile_url}: {e}")
        except Exception as e:
            print(f"Error parsing Listal profile {profile_url}: {e}")

        if limit:
            all_images = all_images[:limit]

        return all_images

    def _parse_profile_page(
        self,
        soup: BeautifulSoup,
        base_url: str,
        limit: Optional[int] = None,
    ) -> List[ImageMedia]:
        """Parse images from a Listal profile page."""
        images = []

        profile_name = self._extract_profile_name(soup) or self._extract_name_from_url(base_url)

        image_links = soup.find_all('a', href=lambda h: h and '/viewimage/' in h)

        limit_value = limit if limit else len(image_links)

        for link in image_links[:limit_value]:
            href = link.get('href', '')
            if not href.startswith('http'):
                href = urljoin(self.BASE_URL, href)

            image_id = self._extract_image_id(href)
            if not image_id:
                continue

            img = link.find('img')
            if not img:
                continue

            thumbnail_url = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
            if not thumbnail_url:
                continue

            if thumbnail_url.startswith('//'):
                thumbnail_url = 'https:' + thumbnail_url

            vote_count = self._extract_vote_count(link)
            views = self._extract_views(soup, image_id)

            media_item = ImageMedia(
                title=f"{profile_name} - {image_id}",
                source_url=href,
                publish_date=datetime.utcnow(),
                thumbnail_url=thumbnail_url,
                media_type=MediaType.IMAGE,
                platform_name="Listal",
                platform_slug="listal",
            )

            images.append(media_item)

        return images

    def _fetch_individual_image(self, image_url: str) -> Optional[ImageMedia]:
        """Fetch a single Listal image with full metadata."""
        if self.mock:
            image_id = self._extract_image_id(image_url) or "16806755"
            return ImageMedia(
                title=f"Listal Image {image_id}",
                source_url=image_url,
                publish_date=datetime.utcnow(),
                thumbnail_url="https://iv1.lisimg.com/image/16806755/740full-maddie-teeuws.jpg",
                media_type=MediaType.IMAGE,
                platform_name="Listal",
                platform_slug="listal",
            )

        try:
            response = requests.get(image_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            profile_name = self._extract_profile_name(soup) or "Unknown"
            image_id = self._extract_image_id(image_url) or "unknown"

            img = soup.find('img', alt=lambda t: t and profile_name in t) if profile_name else soup.find('img')
            image_url_full = None
            if img:
                src = img.get('src') or img.get('data-src')
                if src:
                    if src.startswith('//'):
                        image_url_full = 'https:' + src

            return ImageMedia(
                title=f"{profile_name} - {image_id}",
                source_url=image_url,
                publish_date=datetime.utcnow(),
                thumbnail_url=image_url_full or image_url_full,
                media_type=MediaType.IMAGE,
                platform_name="Listal",
                platform_slug="listal",
            )

        except Exception as e:
            print(f"Error fetching Listal image {image_url}: {e}")
            return None

    def parse_image_page(self, html: str) -> Dict[str, Any]:
        """Parse Listal image page HTML to extract rich metadata."""
        soup = BeautifulSoup(html, 'html.parser')

        subject_name = self._extract_profile_name(soup) or "Unknown"

        views_match = re.search(r'(\d+)\s+Views', soup.get_text())
        views = int(views_match.group(1)) if views_match else 0

        vote_el = soup.find(string=re.compile(r'\d+'))
        vote_count = 0
        if vote_el:
            vote_match = re.search(r'(\d+)', vote_el)
            if vote_match:
                vote_count = int(vote_match.group(1))

        voters = []
        voter_els = soup.select('a[href*=".listal.com"]')
        for el in voter_els[:20]:
            href = el.get('href', '')
            if href and href.startswith('/'):
                username = href.strip('/')
                if username and not any(c in username for c in ['/', '?', '#']):
                    voters.append(username)

        related_image_ids = []
        related_links = soup.select('a[href*="/viewimage/"]')
        for link in related_links[:20]:
            href = link.get('href', '')
            img_id = self._extract_image_id(href)
            if img_id and img_id not in related_image_ids:
                related_image_ids.append(img_id)

        curator_lists = []
        list_links = soup.select('a[href^="/list/"]')
        for link in list_links[:10]:
            href = link.get('href', '')
            name = link.get_text(strip=True)
            if href and name:
                curator_lists.append({
                    "list_url": href,
                    "list_name": name,
                })

        date_match = re.search(r'(\d+)\s+years?\s+ago|(\d+)\s+months?\s+ago|(\d+)\s+days?\s+ago', soup.get_text())
        added_date = datetime.utcnow()
        if date_match:
            if date_match.group(1):
                added_date = datetime.utcnow()
            elif date_match.group(2):
                added_date = datetime.utcnow()
            elif date_match.group(3):
                added_date = datetime.utcnow()

        added_by = None
        added_by_el = soup.select_one('a[href*=".listal.com"]')
        if added_by_el:
            href = added_by_el.get('href', '')
            if href:
                added_by = href.strip('/').split('.')[0]

        return {
            "subject_name": subject_name,
            "image_id": self._extract_image_id(soup.url if hasattr(soup, 'url') else "") or "unknown",
            "views": views,
            "vote_count": vote_count,
            "voters": voters,
            "related_image_ids": related_image_ids,
            "curator_lists": curator_lists,
            "added_date": added_date,
            "added_by": added_by,
        }

    def _extract_profile_name(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract profile name from page."""
        name_selectors = [
            'h1',
            '.profile-name',
            '[class*="username"]',
            'a[href*="/maddie-teeuws"]',
        ]

        for selector in name_selectors:
            el = soup.select_one(selector)
            if el:
                text = el.get_text(strip=True)
                if text and len(text) < 100:
                    return text

        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text(strip=True)
            title = re.sub(r'\s*[-|]\s*Listal.*$', '', title, flags=re.IGNORECASE)
            return title.strip()

        return None

    def _extract_name_from_url(self, url: str) -> str:
        """Extract profile name from URL."""
        match = re.search(r'listal\.com/([^/]+)', url)
        return match.group(1) if match else "unknown"

    def _extract_image_id(self, url: str) -> Optional[str]:
        """Extract image ID from URL."""
        match = re.search(r'/viewimage/(\d+)', url)
        return match.group(1) if match else None

    def _extract_image_count(self, soup: BeautifulSoup) -> int:
        """Extract total image count from profile."""
        text = soup.get_text()
        match = re.search(r'(\d+)\s+Images?', text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return 0

    def _extract_vote_count(self, element: BeautifulSoup) -> int:
        """Extract vote count from element."""
        text = element.get_text()
        match = re.search(r'(\d+)', text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return 0

    def _extract_views(self, soup: BeautifulSoup, image_id: str) -> int:
        """Extract view count from page."""
        text = soup.get_text()
        match = re.search(r'(\d+)\s+Views', text)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                pass
        return 0

    def _find_next_page(self, soup: BeautifulSoup, base_url: str) -> Optional[str]:
        """Find next page URL in pagination."""
        next_link = soup.find('a', string=re.compile(r'Next', re.I))
        if next_link:
            href = next_link.get('href')
            if href:
                if href.startswith('http'):
                    return href
                return urljoin(base_url, href)
        return None

    def _fetch_mock_images(self, profile_url: str) -> List[ImageMedia]:
        """Return mock images for testing."""
        name = self._extract_name_from_url(profile_url)
        return [
            ImageMedia(
                title=f"{name} - 16806755",
                source_url=f"https://www.listal.com/viewimage/16806755",
                publish_date=datetime.utcnow(),
                thumbnail_url="https://iv1.lisimg.com/image/16806755/740full-maddie-teeuws.jpg",
                media_type=MediaType.IMAGE,
                platform_name="Listal",
                platform_slug="listal",
            ),
        ]
