"""Depop platform adapter for e-commerce product crawling."""

import os
import time
import random
import re
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse, urljoin
import requests
from bs4 import BeautifulSoup

from .base import PlatformAdapter
from ..models.product import Product
from ..models.subreddit import Subreddit


class DepopAdapter(PlatformAdapter):
    """Depop adapter for crawling product listings."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        mock: bool = False,
    ):
        """
        Initialize Depop adapter.
        
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
    ) -> Tuple[List[Product], Optional[str]]:
        """
        Fetch products from a Depop seller or search.
        
        Note: Depop doesn't have a public JSON API like Reddit.
        This method would need to scrape seller pages or use search.
        For now, we'll focus on individual product URLs.
        
        Args:
            source: Seller username or search term
            sort: Sort order (not used for Depop)
            limit: Maximum products per page
            after: Pagination token (not used for Depop)
        
        Returns:
            Tuple of (list of products, next page token or None)
        """
        # Depop doesn't have a public API, so we'll return empty for now
        # Individual products should be fetched via fetch_product()
        return [], None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch seller metadata (using Subreddit model for compatibility).
        
        Args:
            source: Seller username
        
        Returns:
            Subreddit-like metadata or None
        """
        # For Depop, we'd fetch seller profile info
        # Using Subreddit model for compatibility with base interface
        if self.mock:
            return Subreddit(
                name=source,
                subscribers=0,
                created_utc=datetime.utcnow(),
                description=f"Depop seller: {source}",
            )
        return None

    def fetch_product(self, product_url: str) -> Optional[Product]:
        """
        Fetch a single product from a Depop product URL.
        
        Args:
            product_url: Full URL to Depop product page
        
        Returns:
            Product object or None if fetch fails
        """
        if self.mock:
            return self._fetch_product_mock(product_url)
        
        try:
            response = requests.get(product_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            product = self._parse_product_page(soup, product_url)
            self._delay()
            return product
            
        except requests.RequestException as e:
            print(f"Error fetching product {product_url}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing product {product_url}: {e}")
            return None

    def _parse_product_page(self, soup: BeautifulSoup, url: str) -> Product:
        """Parse product data from HTML page."""
        
        # Extract product ID from URL
        product_id = self._extract_product_id(url)
        
        # Try to find JSON-LD structured data
        json_ld = self._extract_json_ld(soup)
        
        # Extract title
        title = self._extract_title(soup, json_ld)
        
        # Extract price
        price, currency = self._extract_price(soup, json_ld)
        
        # Extract description
        description = self._extract_description(soup, json_ld)
        
        # Extract images
        image_urls = self._extract_images(soup, json_ld)
        
        # Extract seller info
        seller_username, seller_id = self._extract_seller(soup)
        
        # Extract metadata
        brand = self._extract_brand(soup, json_ld)
        condition = self._extract_condition(soup)
        size = self._extract_size(soup)
        category = self._extract_category(soup, json_ld)
        tags = self._extract_tags(soup)
        status = self._extract_status(soup)
        likes_count = self._extract_likes(soup)
        
        # Extract timestamps
        created_utc = self._extract_created_date(soup, json_ld)
        
        # Extract permalink/slug
        permalink = self._extract_permalink(url)
        
        return Product(
            id=product_id,
            title=title,
            description=description,
            price=price,
            currency=currency,
            status=status,
            brand=brand,
            condition=condition,
            size=size,
            category=category,
            tags=tags,
            image_urls=image_urls,
            seller_username=seller_username,
            seller_id=seller_id,
            likes_count=likes_count,
            created_utc=created_utc,
            updated_utc=datetime.utcnow(),
            url=url,
            permalink=permalink,
        )

    def _extract_product_id(self, url: str) -> str:
        """Extract product ID from URL."""
        # URL format: https://www.depop.com/products/{username}-{product-slug}/
        # Or: https://www.depop.com/products/{product-slug}/
        match = re.search(r'/products/([^/]+)/?$', url)
        if match:
            return match.group(1)
        # Fallback: use URL hash
        return str(hash(url))

    def _extract_json_ld(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract JSON-LD structured data if present."""
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        for script in json_ld_scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and data.get('@type') in ['Product', 'Offer']:
                    return data
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and item.get('@type') in ['Product', 'Offer']:
                            return item
            except (json.JSONDecodeError, AttributeError):
                continue
        return None

    def _extract_title(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> str:
        """Extract product title."""
        if json_ld and 'name' in json_ld:
            return json_ld['name']
        
        # Try various selectors
        selectors = [
            'h1[data-testid="product-title"]',
            'h1.product-title',
            'h1',
            'meta[property="og:title"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '')
                return element.get_text(strip=True)
        
        # Fallback to page title
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text(strip=True)
        
        return "Unknown Product"

    def _extract_price(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> Tuple[float, str]:
        """Extract price and currency."""
        # Try JSON-LD first
        if json_ld:
            if 'offers' in json_ld:
                offers = json_ld['offers']
                if isinstance(offers, list) and offers:
                    offers = offers[0]
                if isinstance(offers, dict):
                    price = offers.get('price')
                    currency = offers.get('priceCurrency', 'USD')
                    if price:
                        try:
                            return float(price), currency
                        except (ValueError, TypeError):
                            pass
        
        # Try HTML selectors
        price_selectors = [
            '[data-testid="product-price"]',
            '.product-price',
            '.price',
            '[itemprop="price"]',
        ]
        
        for selector in price_selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                # Extract number from price string (e.g., "$25.00" -> 25.00)
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    try:
                        price = float(price_match.group())
                        # Try to detect currency
                        currency = 'USD'
                        if '£' in price_text or 'GBP' in price_text:
                            currency = 'GBP'
                        elif '€' in price_text or 'EUR' in price_text:
                            currency = 'EUR'
                        return price, currency
                    except ValueError:
                        pass
        
        return 0.0, 'USD'

    def _extract_description(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> str:
        """Extract product description."""
        if json_ld and 'description' in json_ld:
            return json_ld['description']
        
        # Try various selectors
        selectors = [
            '[data-testid="product-description"]',
            '.product-description',
            '[itemprop="description"]',
            'meta[property="og:description"]',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '')
                return element.get_text(strip=True)
        
        return ""

    def _extract_images(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> List[str]:
        """Extract all product image URLs."""
        images = []
        
        # Try JSON-LD
        if json_ld:
            if 'image' in json_ld:
                image_data = json_ld['image']
                if isinstance(image_data, str):
                    images.append(image_data)
                elif isinstance(image_data, list):
                    images.extend([img for img in image_data if isinstance(img, str)])
        
        # Try Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            images.append(og_image['content'])
        
        # Try gallery images
        gallery_selectors = [
            '[data-testid="product-image"]',
            '.product-image img',
            '.gallery img',
            '[data-testid="image-gallery"] img',
        ]
        
        for selector in gallery_selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://www.depop.com' + src
                    if src not in images:
                        images.append(src)
        
        # Try to find high-res image URLs (Depop pattern)
        # Depop images often follow: https://media-photos.depop.com/...
        for img_url in images:
            # Try to get higher resolution versions
            if 'media-photos.depop.com' in img_url:
                # Depop image URLs might have size parameters
                # Try to extract base URL and get full size
                base_url = re.sub(r'[?&]w=\d+', '', img_url)
                base_url = re.sub(r'[?&]h=\d+', '', base_url)
                if base_url not in images:
                    images.append(base_url)
        
        return list(dict.fromkeys(images))  # Remove duplicates while preserving order

    def _extract_seller(self, soup: BeautifulSoup) -> Tuple[Optional[str], Optional[str]]:
        """Extract seller username and ID."""
        # Try various selectors for seller info
        seller_selectors = [
            '[data-testid="seller-username"]',
            '.seller-username',
            '.product-seller',
            'a[href*="/users/"]',
        ]
        
        for selector in seller_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'a':
                    href = element.get('href', '')
                    match = re.search(r'/users/([^/]+)', href)
                    if match:
                        return match.group(1), None
                    username = element.get_text(strip=True)
                    if username:
                        return username, None
                else:
                    username = element.get_text(strip=True)
                    if username:
                        return username, None
        
        # Try to extract from URL
        url_match = re.search(r'/products/([^-]+)-', soup.find('link', rel='canonical').get('href', '') if soup.find('link', rel='canonical') else '')
        if url_match:
            return url_match.group(1), None
        
        return None, None

    def _extract_brand(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> Optional[str]:
        """Extract product brand."""
        if json_ld and 'brand' in json_ld:
            brand_data = json_ld['brand']
            if isinstance(brand_data, dict):
                return brand_data.get('name')
            elif isinstance(brand_data, str):
                return brand_data
        
        # Try HTML selectors
        brand_selectors = [
            '[data-testid="product-brand"]',
            '.product-brand',
            '[itemprop="brand"]',
        ]
        
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_condition(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract item condition."""
        condition_selectors = [
            '[data-testid="product-condition"]',
            '.product-condition',
            '[itemprop="itemCondition"]',
        ]
        
        for selector in condition_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_size(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract product size."""
        size_selectors = [
            '[data-testid="product-size"]',
            '.product-size',
            '[itemprop="size"]',
        ]
        
        for selector in size_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_category(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> Optional[str]:
        """Extract product category."""
        if json_ld and 'category' in json_ld:
            return json_ld['category']
        
        # Try HTML selectors
        category_selectors = [
            '[data-testid="product-category"]',
            '.product-category',
            '[itemprop="category"]',
        ]
        
        for selector in category_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract product tags/hashtags."""
        tags = []
        
        # Look for hashtags in description or dedicated tag elements
        tag_selectors = [
            '[data-testid="product-tags"]',
            '.product-tags',
            '.hashtags',
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get_text()
                # Extract hashtags
                hashtags = re.findall(r'#(\w+)', tag_text)
                tags.extend(hashtags)
        
        # Also check description for hashtags
        description = soup.select_one('[data-testid="product-description"]')
        if description:
            hashtags = re.findall(r'#(\w+)', description.get_text())
            tags.extend(hashtags)
        
        return list(set(tags))  # Remove duplicates

    def _extract_status(self, soup: BeautifulSoup) -> str:
        """Extract product status (ONSALE, SOLD, etc.)."""
        status_selectors = [
            '[data-testid="product-status"]',
            '.product-status',
            '.status',
        ]
        
        for selector in status_selectors:
            element = soup.select_one(selector)
            if element:
                status_text = element.get_text(strip=True).upper()
                if 'SOLD' in status_text:
                    return 'SOLD'
                elif 'SALE' in status_text or 'ON' in status_text:
                    return 'ONSALE'
        
        # Check if "Sold" appears anywhere on page
        page_text = soup.get_text().upper()
        if 'SOLD' in page_text and 'AVAILABLE' not in page_text:
            return 'SOLD'
        
        return 'ONSALE'

    def _extract_likes(self, soup: BeautifulSoup) -> int:
        """Extract number of likes."""
        like_selectors = [
            '[data-testid="product-likes"]',
            '.product-likes',
            '.likes-count',
        ]
        
        for selector in like_selectors:
            element = soup.select_one(selector)
            if element:
                like_text = element.get_text(strip=True)
                # Extract number
                match = re.search(r'\d+', like_text.replace(',', ''))
                if match:
                    try:
                        return int(match.group())
                    except ValueError:
                        pass
        
        return 0

    def _extract_created_date(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> datetime:
        """Extract listing creation date."""
        if json_ld and 'datePublished' in json_ld:
            try:
                return datetime.fromisoformat(json_ld['datePublished'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # Try HTML selectors
        date_selectors = [
            '[data-testid="product-date"]',
            '.product-date',
            '[itemprop="datePublished"]',
        ]
        
        for selector in date_selectors:
            element = soup.select_one(selector)
            if element:
                date_text = element.get_text(strip=True)
                # Try to parse relative dates like "Listed 1 year ago"
                # For now, use current time as fallback
                # TODO: Implement proper date parsing
                pass
        
        # Fallback to current time
        return datetime.utcnow()

    def _extract_permalink(self, url: str) -> Optional[str]:
        """Extract permalink/slug from URL."""
        match = re.search(r'/products/([^/]+)/?$', url)
        if match:
            return match.group(1)
        return None

    def _fetch_product_mock(self, product_url: str) -> Product:
        """Return mock product for testing."""
        return Product(
            id="mock_depop_1",
            title="Hot pink tights. Thick and stretchy.",
            description="Beautiful hot pink tights, thick and stretchy material. Perfect condition.",
            price=25.00,
            currency="USD",
            status="ONSALE",
            brand="Unknown",
            condition="Used",
            size="One Size",
            category="Tights",
            tags=["hotpink", "pink", "tights"],
            image_urls=[
                "https://media-photos.depop.com/b1/12345678/1234567890_abc123def456/P0.jpg",
                "https://media-photos.depop.com/b1/12345678/1234567890_abc123def456/P1.jpg",
            ],
            seller_username="krista_h",
            seller_id=None,
            likes_count=12,
            created_utc=datetime.utcnow(),
            updated_utc=datetime.utcnow(),
            url=product_url,
            permalink="krista_h-hot-pink-tights-thick-and",
        )







