"""Shopify platform adapter for e-commerce product crawling."""

import os
import time
import random
import re
import json
from datetime import datetime
from typing import List, Optional, Tuple, Dict, Any
from urllib.parse import urlparse, urljoin, parse_qs
import requests
from bs4 import BeautifulSoup

from .base import PlatformAdapter
from ..models.product import Product
from ..models.subreddit import Subreddit


class ShopifyAdapter(PlatformAdapter):
    """Shopify adapter for crawling product listings from Shopify stores."""

    def __init__(
        self,
        user_agent: Optional[str] = None,
        delay_min: float = 2.0,
        delay_max: float = 5.0,
        mock: bool = False,
    ):
        """
        Initialize Shopify adapter.
        
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
        Fetch products from a Shopify store or collection.
        
        Note: Shopify stores may have JSON API endpoints, but this requires
        store-specific configuration. For now, we focus on individual product URLs.
        
        Args:
            source: Store domain or collection URL
            sort: Sort order (not used for Shopify)
            limit: Maximum products per page
            after: Pagination token (not used for Shopify)
        
        Returns:
            Tuple of (list of products, next page token or None)
        """
        # Shopify doesn't have a universal public API, so we'll return empty for now
        # Individual products should be fetched via fetch_product()
        return [], None

    def fetch_source_metadata(self, source: str) -> Optional[Subreddit]:
        """
        Fetch store metadata (using Subreddit model for compatibility).
        
        Args:
            source: Store domain or name
        
        Returns:
            Subreddit-like metadata or None
        """
        if self.mock:
            return Subreddit(
                name=source,
                subscribers=0,
                created_utc=datetime.utcnow(),
                description=f"Shopify store: {source}",
            )
        return None

    def fetch_product(self, product_url: str) -> Optional[Product]:
        """
        Fetch a single product from a Shopify product URL.
        
        Args:
            product_url: Full URL to Shopify product page
        
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
        """Parse product data from Shopify HTML page."""
        
        # Extract product ID from URL or page
        product_id = self._extract_product_id(url, soup)
        
        # Try to find JSON-LD structured data (Shopify often uses this)
        json_ld = self._extract_json_ld(soup)
        
        # Try to find Shopify product JSON (often in script tags)
        shopify_json = self._extract_shopify_json(soup)
        
        # Extract title
        title = self._extract_title(soup, json_ld, shopify_json)
        
        # Extract price
        price, currency = self._extract_price(soup, json_ld, shopify_json)
        
        # Extract description
        description = self._extract_description(soup, json_ld, shopify_json)
        
        # Extract images
        image_urls = self._extract_images(soup, json_ld, shopify_json)
        
        # Extract seller/store info
        seller_username, seller_id = self._extract_seller(soup, url)
        
        # Extract metadata
        brand = self._extract_brand(soup, json_ld, shopify_json)
        condition = self._extract_condition(soup)
        size = self._extract_size(soup, shopify_json)
        category = self._extract_category(soup, json_ld, shopify_json)
        tags = self._extract_tags(soup, shopify_json)
        status = self._extract_status(soup, shopify_json)
        likes_count = 0  # Shopify doesn't typically have likes
        
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

    def _extract_product_id(self, url: str, soup: BeautifulSoup) -> str:
        """Extract product ID from URL or page."""
        # Try to extract from URL variant parameter
        parsed = urlparse(url)
        query_params = parse_qs(parsed.query)
        if 'variant' in query_params:
            variant_id = query_params['variant'][0]
            # Get base product ID from URL path
            path_match = re.search(r'/products/([^/?]+)', url)
            if path_match:
                return f"{path_match.group(1)}-{variant_id}"
        
        # Try to extract from URL path
        path_match = re.search(r'/products/([^/?]+)', url)
        if path_match:
            return path_match.group(1)
        
        # Try to find product ID in page
        product_id_script = soup.find('script', string=re.compile(r'product.*id', re.I))
        if product_id_script:
            match = re.search(r'["\']id["\']\s*:\s*(\d+)', product_id_script.string)
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

    def _extract_shopify_json(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Extract Shopify product JSON from script tags."""
        # Shopify often stores product data in script tags with specific patterns
        scripts = soup.find_all('script')
        for script in scripts:
            if not script.string:
                continue
            
            # Look for Shopify product JSON patterns
            if 'product' in script.string.lower() or 'Product' in script.string:
                # Try to find JSON objects
                json_patterns = [
                    r'var\s+product\s*=\s*({.+?});',
                    r'window\.product\s*=\s*({.+?});',
                    r'product:\s*({.+?}),',
                    r'"product":\s*({.+?})',
                ]
                
                for pattern in json_patterns:
                    match = re.search(pattern, script.string, re.DOTALL)
                    if match:
                        try:
                            return json.loads(match.group(1))
                        except (json.JSONDecodeError, ValueError):
                            continue
                
                # Try to find any JSON object
                json_match = re.search(r'\{[^{}]*"id"[^{}]*\}', script.string)
                if json_match:
                    try:
                        return json.loads(json_match.group(0))
                    except (json.JSONDecodeError, ValueError):
                        continue
        
        return None

    def _extract_title(self, soup: BeautifulSoup, json_ld: Optional[Dict], shopify_json: Optional[Dict]) -> str:
        """Extract product title."""
        if json_ld and 'name' in json_ld:
            return json_ld['name']
        
        if shopify_json and 'title' in shopify_json:
            return shopify_json['title']
        
        # Try various selectors
        selectors = [
            'h1.product-title',
            'h1[data-product-title]',
            'h1',
            'meta[property="og:title"]',
            '[itemprop="name"]',
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

    def _extract_price(self, soup: BeautifulSoup, json_ld: Optional[Dict], shopify_json: Optional[Dict]) -> Tuple[float, str]:
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
        
        # Try Shopify JSON
        if shopify_json:
            # Check for price in various formats
            price = shopify_json.get('price') or shopify_json.get('price_min') or shopify_json.get('compare_at_price')
            if price:
                try:
                    # Shopify prices are often in cents
                    if isinstance(price, int) and price > 1000:
                        price = price / 100.0
                    currency = shopify_json.get('currency', 'USD')
                    return float(price), currency
                except (ValueError, TypeError):
                    pass
        
        # Try HTML selectors
        price_selectors = [
            '[data-product-price]',
            '.product-price',
            '.price',
            '[itemprop="price"]',
            '.price-current',
            '.product__price',
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

    def _extract_description(self, soup: BeautifulSoup, json_ld: Optional[Dict], shopify_json: Optional[Dict]) -> str:
        """Extract product description."""
        if json_ld and 'description' in json_ld:
            return json_ld['description']
        
        if shopify_json and 'description' in shopify_json:
            return shopify_json['description']
        
        # Try various selectors
        selectors = [
            '[data-product-description]',
            '.product-description',
            '.product__description',
            '[itemprop="description"]',
            'meta[property="og:description"]',
            '.product-single__description',
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', '')
                return element.get_text(strip=True)
        
        return ""

    def _extract_images(self, soup: BeautifulSoup, json_ld: Optional[Dict], shopify_json: Optional[Dict]) -> List[str]:
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
        
        # Try Shopify JSON
        if shopify_json:
            # Shopify often has images array
            shopify_images = shopify_json.get('images') or shopify_json.get('featured_image')
            if shopify_images:
                if isinstance(shopify_images, list):
                    images.extend([img for img in shopify_images if isinstance(img, str)])
                elif isinstance(shopify_images, str):
                    images.append(shopify_images)
        
        # Try Open Graph image
        og_image = soup.find('meta', property='og:image')
        if og_image and og_image.get('content'):
            images.append(og_image['content'])
        
        # Try gallery images
        gallery_selectors = [
            '[data-product-image]',
            '.product-image img',
            '.product__image img',
            '.product-gallery img',
            '.product-single__photo img',
            '[itemprop="image"]',
        ]
        
        for selector in gallery_selectors:
            elements = soup.select(selector)
            for img in elements:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy-src') or img.get('data-original')
                if src:
                    # Convert relative URLs to absolute
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        # Get base URL from page
                        base_url = f"{urlparse(soup.find('link', rel='canonical').get('href', '')).scheme}://{urlparse(soup.find('link', rel='canonical').get('href', '')).netloc}" if soup.find('link', rel='canonical') else 'https://shop.hanrousa.com'
                        src = base_url + src
                    # Shopify images often have size parameters, try to get full size
                    src = re.sub(r'[?&]_?w=\d+', '', src)
                    src = re.sub(r'[?&]_?h=\d+', '', src)
                    if src not in images:
                        images.append(src)
        
        return list(dict.fromkeys(images))  # Remove duplicates while preserving order

    def _extract_seller(self, soup: BeautifulSoup, url: str) -> Tuple[Optional[str], Optional[str]]:
        """Extract seller/store information."""
        # For Shopify, the "seller" is typically the store name
        # Extract from domain
        parsed = urlparse(url)
        domain = parsed.netloc
        # Remove www. and extract store name
        store_name = domain.replace('www.', '').replace('shop.', '').split('.')[0]
        
        # Try to find store name in page
        store_selectors = [
            '[data-store-name]',
            '.store-name',
            'meta[property="og:site_name"]',
        ]
        
        for selector in store_selectors:
            element = soup.select_one(selector)
            if element:
                if element.name == 'meta':
                    return element.get('content', store_name), None
                store_text = element.get_text(strip=True)
                if store_text:
                    return store_text, None
        
        return store_name, None

    def _extract_brand(self, soup: BeautifulSoup, json_ld: Optional[Dict], shopify_json: Optional[Dict]) -> Optional[str]:
        """Extract product brand."""
        if json_ld and 'brand' in json_ld:
            brand_data = json_ld['brand']
            if isinstance(brand_data, dict):
                return brand_data.get('name')
            elif isinstance(brand_data, str):
                return brand_data
        
        if shopify_json and 'vendor' in shopify_json:
            return shopify_json['vendor']
        
        # Try HTML selectors
        brand_selectors = [
            '[data-product-brand]',
            '.product-brand',
            '[itemprop="brand"]',
            '.product__vendor',
        ]
        
        for selector in brand_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_condition(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract item condition."""
        condition_selectors = [
            '[data-product-condition]',
            '.product-condition',
            '[itemprop="itemCondition"]',
        ]
        
        for selector in condition_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_size(self, soup: BeautifulSoup, shopify_json: Optional[Dict]) -> Optional[str]:
        """Extract product size/variant."""
        # Try Shopify JSON for variants
        if shopify_json and 'variants' in shopify_json:
            variants = shopify_json['variants']
            if isinstance(variants, list) and variants:
                # Get selected variant or first variant
                variant = next((v for v in variants if v.get('selected')), variants[0])
                if 'option1' in variant:
                    return variant['option1']
        
        # Try HTML selectors
        size_selectors = [
            '[data-product-size]',
            '.product-size',
            '.product-variant',
            '[itemprop="size"]',
        ]
        
        for selector in size_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_category(self, soup: BeautifulSoup, json_ld: Optional[Dict], shopify_json: Optional[Dict]) -> Optional[str]:
        """Extract product category."""
        if json_ld and 'category' in json_ld:
            return json_ld['category']
        
        if shopify_json and 'type' in shopify_json:
            return shopify_json['type']
        
        # Try HTML selectors
        category_selectors = [
            '[data-product-category]',
            '.product-category',
            '[itemprop="category"]',
            '.breadcrumb a:last-child',
        ]
        
        for selector in category_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        return None

    def _extract_tags(self, soup: BeautifulSoup, shopify_json: Optional[Dict]) -> List[str]:
        """Extract product tags."""
        tags = []
        
        # Try Shopify JSON
        if shopify_json and 'tags' in shopify_json:
            shopify_tags = shopify_json['tags']
            if isinstance(shopify_tags, list):
                tags.extend(shopify_tags)
            elif isinstance(shopify_tags, str):
                tags.extend([tag.strip() for tag in shopify_tags.split(',')])
        
        # Try HTML selectors
        tag_selectors = [
            '[data-product-tags]',
            '.product-tags',
            '.tags',
        ]
        
        for selector in tag_selectors:
            elements = soup.select(selector)
            for element in elements:
                tag_text = element.get_text()
                # Extract tags (comma-separated or space-separated)
                tag_list = [tag.strip() for tag in re.split(r'[,;]', tag_text)]
                tags.extend(tag_list)
        
        return list(set([tag for tag in tags if tag]))  # Remove duplicates and empty

    def _extract_status(self, soup: BeautifulSoup, shopify_json: Optional[Dict]) -> str:
        """Extract product status (ONSALE, SOLD, etc.)."""
        # Try Shopify JSON
        if shopify_json:
            available = shopify_json.get('available', True)
            if not available:
                return 'SOLD'
        
        # Check for sold out indicators
        sold_out_selectors = [
            '[data-sold-out]',
            '.sold-out',
            '.product-unavailable',
            '[data-product-available="false"]',
        ]
        
        for selector in sold_out_selectors:
            element = soup.select_one(selector)
            if element:
                return 'SOLD'
        
        # Check page text
        page_text = soup.get_text().upper()
        if 'SOLD OUT' in page_text and 'AVAILABLE' not in page_text:
            return 'SOLD'
        
        return 'ONSALE'

    def _extract_created_date(self, soup: BeautifulSoup, json_ld: Optional[Dict]) -> datetime:
        """Extract listing creation date."""
        if json_ld and 'datePublished' in json_ld:
            try:
                return datetime.fromisoformat(json_ld['datePublished'].replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                pass
        
        # Fallback to current time
        return datetime.utcnow()

    def _extract_permalink(self, url: str) -> Optional[str]:
        """Extract permalink/slug from URL."""
        match = re.search(r'/products/([^/?]+)', url)
        if match:
            return match.group(1)
        return None

    def _fetch_product_mock(self, product_url: str) -> Product:
        """Return mock product for testing."""
        return Product(
            id="mock_shopify_1",
            title="Net Women's Fine Netted Tights | Black",
            description="Fine netted tights in black color.",
            price=33.60,
            currency="USD",
            status="ONSALE",
            brand="HANRO",
            condition="New",
            size=None,
            category="Tights",
            tags=["tights", "net", "black"],
            image_urls=[
                "https://cdn.shopify.com/s/files/1/example/product-image.jpg",
            ],
            seller_username="hanrousa",
            seller_id=None,
            likes_count=0,
            created_utc=datetime.utcnow(),
            updated_utc=datetime.utcnow(),
            url=product_url,
            permalink="net-womens-fine-netted-tights-black-40658-3009",
        )







