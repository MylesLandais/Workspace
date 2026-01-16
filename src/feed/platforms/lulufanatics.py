"""Adapter for Lululemon Fanatics website (lulufanatics.com).

This adapter extracts product information from Lululemon Fanatics, including:
- Product line information
- Style numbers and variants
- Release dates and types
- Price history
- Color variations
- Material specifications
"""

import re
from typing import Optional, Dict, Any, List
from datetime import datetime
from bs4 import BeautifulSoup
import requests

from .base import PlatformAdapter
from ..models.product import Product


class LululemonFanaticsAdapter(PlatformAdapter):
    """Adapter for lulufanatics.com."""
    
    def __init__(self, mock: bool = False):
        """
        Initialize Lululemon Fanatics adapter.
        
        Args:
            mock: If True, use mock data instead of fetching from web
        """
        super().__init__(mock=mock)
        self.base_url = "https://www.lulufanatics.com"
    
    def fetch_product(self, url: str) -> Optional[Product]:
        """
        Fetch product data from Lululemon Fanatics.
        
        Args:
            url: Product URL (e.g., https://www.lulufanatics.com/item/87143/...)
        
        Returns:
            Product object or None if fetch fails
        """
        if self.mock:
            return self._mock_product()
        
        try:
            response = requests.get(url, headers=self._get_headers(), timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return self._parse_product_page(soup, url)
        except Exception as e:
            print(f"Error fetching product from {url}: {e}")
            return None
    
    def _parse_product_page(self, soup: BeautifulSoup, url: str) -> Optional[Product]:
        """Parse product page HTML."""
        try:
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.get_text(strip=True) if title_elem else ""
            
            # Extract style number
            style_number = self._extract_style_number(soup)
            
            # Extract release date
            release_date = self._extract_release_date(soup)
            
            # Extract original price
            original_price = self._extract_original_price(soup)
            
            # Extract material
            material = self._extract_material(soup)
            
            # Extract description
            description = self._extract_description(soup)
            
            # Extract color
            color = self._extract_color(soup)
            
            # Extract images
            image_urls = self._extract_images(soup)
            
            # Extract price history
            price_history = self._extract_price_history(soup)
            
            # Parse product line and variant from title
            product_line, variant_type = self._parse_title(title)
            
            # Create product ID from style number or URL
            product_id = style_number or self._extract_id_from_url(url)
            
            # Determine release type
            release_type = "First Release" if "(First Release)" in title else "Re-release"
            
            return Product(
                id=product_id,
                title=title,
                description=description,
                price=original_price or 0.0,
                currency="USD",
                status="ONSALE" if original_price else "DISCONTINUED",
                brand="Lululemon",
                condition="NEW",
                size=None,  # Size not shown on product page
                category=self._infer_category(title),
                tags=self._extract_tags(title, material, variant_type),
                image_urls=image_urls,
                seller_username=None,  # Not applicable for catalog site
                seller_profile_url=None,
                likes_count=0,
                publish_date=release_date,
                source_url=url,
                created_at=datetime.now().isoformat(),
                updated_at=datetime.now().isoformat(),
            )
        except Exception as e:
            print(f"Error parsing product page: {e}")
            return None
    
    def _extract_style_number(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract style number from page."""
        # Look for "Style Number:" label
        style_elem = soup.find(string=re.compile(r'Style Number:', re.I))
        if style_elem:
            parent = style_elem.find_parent()
            if parent:
                # Get next sibling or text after label
                style_text = parent.get_text(strip=True)
                match = re.search(r'Style Number:\s*([A-Z0-9]+)', style_text, re.I)
                if match:
                    return match.group(1)
        return None
    
    def _extract_release_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract release date from page."""
        release_elem = soup.find(string=re.compile(r'Release Date:', re.I))
        if release_elem:
            parent = release_elem.find_parent()
            if parent:
                release_text = parent.get_text(strip=True)
                match = re.search(r'Release Date:\s*(\d+/\d{4})', release_text, re.I)
                if match:
                    return match.group(1)
        return None
    
    def _extract_original_price(self, soup: BeautifulSoup) -> Optional[float]:
        """Extract original price from page."""
        price_elem = soup.find(string=re.compile(r'Original Price:', re.I))
        if price_elem:
            parent = price_elem.find_parent()
            if parent:
                price_text = parent.get_text(strip=True)
                match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                if match:
                    return float(match.group(1).replace(',', ''))
        return None
    
    def _extract_material(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract material information."""
        material_elem = soup.find(string=re.compile(r'Material:', re.I))
        if material_elem:
            parent = material_elem.find_parent()
            if parent:
                material_text = parent.get_text(strip=True)
                match = re.search(r'Material:\s*(.+)', material_text, re.I)
                if match:
                    return match.group(1).strip()
        return None
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description."""
        # Look for description in various places
        desc_elem = soup.find('div', class_=re.compile(r'description|about', re.I))
        if desc_elem:
            return desc_elem.get_text(strip=True)
        
        # Fallback: look for "read more" section
        read_more = soup.find(string=re.compile(r'read more', re.I))
        if read_more:
            parent = read_more.find_parent()
            if parent:
                return parent.get_text(strip=True)
        
        return ""
    
    def _extract_color(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract color from title or page."""
        # Color is usually in the title
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text()
            # Look for color in parentheses or after dash
            match = re.search(r'-\s*([^-\(]+?)(?:\s*\(|$)', title)
            if match:
                return match.group(1).strip()
        return None
    
    def _extract_images(self, soup: BeautifulSoup) -> List[str]:
        """Extract product images."""
        images = []
        
        # Look for img tags in product gallery
        img_tags = soup.find_all('img', src=re.compile(r'item|product', re.I))
        for img in img_tags:
            src = img.get('src') or img.get('data-src')
            if src:
                if not src.startswith('http'):
                    src = f"{self.base_url}{src}"
                images.append(src)
        
        return images
    
    def _extract_price_history(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract price history table."""
        history = []
        
        # Look for price history table
        table = soup.find('table')
        if table:
            rows = table.find_all('tr')[1:]  # Skip header
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 2:
                    date_text = cells[0].get_text(strip=True)
                    price_text = cells[1].get_text(strip=True)
                    
                    # Parse price
                    price_match = re.search(r'\$?([\d,]+\.?\d*)', price_text)
                    if price_match:
                        price = float(price_match.group(1).replace(',', ''))
                        history.append({
                            "date": date_text,
                            "price": price,
                        })
        
        return history
    
    def _parse_title(self, title: str) -> tuple[Optional[str], Optional[str]]:
        """Parse product line and variant from title."""
        # Example: "Wunder Train Mesh Panel High-Rise Tight 25" - Black"
        # Product line: "Wunder Train"
        # Variant: "Mesh Panel"
        
        # Common Lululemon product lines
        product_lines = [
            "Wunder Train", "Align", "Speed Up", "Fast and Free",
            "Invigorate", "Base Pace", "Swift Speed", "All the Right Places",
            "In Movement", "Wunder Under", "To the Beat", "Time to Sweat",
        ]
        
        product_line = None
        variant_type = None
        
        for line in product_lines:
            if line in title:
                product_line = line
                # Extract variant (e.g., "Mesh Panel", "Contour Fit")
                variant_match = re.search(rf'{line}\s+([^-]+?)(?:\s+High-Rise|\s+Mid-Rise|$)', title)
                if variant_match:
                    variant_text = variant_match.group(1).strip()
                    if variant_text and variant_text != line:
                        variant_type = variant_text
                break
        
        return product_line, variant_type
    
    def _infer_category(self, title: str) -> str:
        """Infer category from title."""
        title_lower = title.lower()
        
        if any(word in title_lower for word in ['tight', 'legging', 'pant']):
            return "Bottoms"
        elif any(word in title_lower for word in ['bra', 'tank', 'top', 'shirt']):
            return "Tops"
        elif any(word in title_lower for word in ['short', 'skirt']):
            return "Bottoms"
        elif any(word in title_lower for word in ['jacket', 'hoodie', 'sweater']):
            return "Outerwear"
        else:
            return "Apparel"
    
    def _extract_tags(self, title: str, material: Optional[str], variant_type: Optional[str]) -> List[str]:
        """Extract tags from product information."""
        tags = []
        
        # Extract fit type
        if "High-Rise" in title:
            tags.append("high-rise")
        if "Mid-Rise" in title:
            tags.append("mid-rise")
        
        # Extract length
        length_match = re.search(r'(\d+)"', title)
        if length_match:
            tags.append(f"{length_match.group(1)}-inch")
        
        # Add variant type
        if variant_type:
            tags.append(variant_type.lower().replace(' ', '-'))
        
        # Add material tags
        if material:
            material_parts = [m.strip() for m in material.split(',')]
            tags.extend([m.lower() for m in material_parts])
        
        return tags
    
    def _extract_id_from_url(self, url: str) -> str:
        """Extract product ID from URL."""
        match = re.search(r'/item/(\d+)/', url)
        if match:
            return f"lulufanatics_{match.group(1)}"
        return url.split('/')[-1]
    
    def _mock_product(self) -> Product:
        """Return mock product for testing."""
        return Product(
            id="W5FMWS",
            title="Wunder Train Mesh Panel High-Rise Tight 25\" - Black (First Release)",
            description="Train hard, not hot. The mesh panels on this version of our Wunder Train tights add airflow so you stay comfortable and focused.",
            price=118.00,
            currency="USD",
            status="ONSALE",
            brand="Lululemon",
            condition="NEW",
            size=None,
            category="Bottoms",
            tags=["wunder-train", "mesh-panel", "high-rise", "25-inch", "everlux"],
            image_urls=[],
            seller_username=None,
            seller_profile_url=None,
            likes_count=0,
            publish_date="10/2023",
            source_url="https://www.lulufanatics.com/item/87143/...",
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
        )




