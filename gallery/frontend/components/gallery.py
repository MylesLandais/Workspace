"""Custom gallery components for viewing cached HTML."""

from pathlib import Path
from typing import Optional, List
import hashlib
import base64
from datetime import datetime
import json


class GalleryComponent:
    """Base class for gallery components."""
    
    def __init__(self, template_dir: Path):
        self.template_dir = template_dir
        self.cache_dir = Path.home() / ".cache" / "gallery" / "html"
        self.thumbnail_dir = Path.home() / ".cache" / "gallery" / "thumbnails"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.thumbnail_dir.mkdir(parents=True, exist_ok=True)
    
    def cache_html(self, post_id: str, html: str) -> Path:
        """Cache HTML content for post."""
        html_path = self.cache_dir / f"{post_id}.html"
        html_path.write_text(html, encoding='utf-8')
        return html_path
    
    def get_cached_html(self, post_id: str) -> Optional[str]:
        """Get cached HTML for post."""
        html_path = self.cache_dir / f"{post_id}.html"
        if html_path.exists():
            return html_path.read_text(encoding='utf-8')
        return None
    
    def get_cached_html_path(self, post_id: str) -> Optional[Path]:
        """Get path to cached HTML file."""
        html_path = self.cache_dir / f"{post_id}.html"
        if html_path.exists():
            return html_path
        return None
    
    def generate_thumbnail(self, post_id: str, image_url: str) -> Optional[Path]:
        """Generate thumbnail from image URL."""
        try:
            import requests
            from PIL import Image
            from io import BytesIO
            
            response = requests.get(image_url, timeout=10)
            response.raise_for_status()
            
            image = Image.open(BytesIO(response.content))
            image.thumbnail((300, 300), Image.Resampling.LANCZOS)
            
            thumb_path = self.thumbnail_dir / f"{post_id}.jpg"
            image.save(thumb_path, 'JPEG', quality=85)
            
            return thumb_path
        except Exception as e:
            print(f"Error generating thumbnail for {post_id}: {e}")
            return None
    
    def get_thumbnail_path(self, post_id: str) -> Optional[Path]:
        """Get path to thumbnail file."""
        thumb_path = self.thumbnail_dir / f"{post_id}.jpg"
        if thumb_path.exists():
            return thumb_path
        return None
    
    def get_gallery_stats(self) -> dict:
        """Get gallery statistics."""
        total_cached = len(list(self.cache_dir.glob("*.html")))
        total_thumbnails = len(list(self.thumbnail_dir.glob("*.jpg")))
        
        total_size = 0
        for path in list(self.cache_dir.glob("*")) + list(self.thumbnail_dir.glob("*")):
            if path.is_file():
                total_size += path.stat().st_size
        
        return {
            "cached_pages": total_cached,
            "thumbnails": total_thumbnails,
            "storage_size_bytes": total_size,
            "storage_size_mb": round(total_size / 1024 / 1024, 2)
        }


class CatalogueViewer(GalleryComponent):
    """Component for viewing catalogues."""
    
    def render_catalogue_item(self, post_data: dict) -> str:
        """Render single catalogue item."""
        return f"""
        <div class="catalogue-item" data-post-id="{post_data['id']}">
            {self._render_thumbnail(post_data)}
            <div class="catalogue-content">
                <h3 class="catalogue-title">{self._escape_html(post_data['title'])}</h3>
                <div class="catalogue-meta">
                    <span class="meta-item">⬆️ {post_data['score']}</span>
                    <span class="meta-item">💬 {post_data['num_comments']}</span>
                    <span class="meta-item">👤 {self._escape_html(post_data['author'] or '[deleted]')}</span>
                    {self._render_badges(post_data)}
                </div>
            </div>
        </div>
        """
    
    def _render_thumbnail(self, post_data: dict) -> str:
        """Render thumbnail if available."""
        if post_data.get('thumbnail'):
            return f'<img src="{post_data["thumbnail"]}" alt="" class="catalogue-thumbnail" loading="lazy">'
        return ''
    
    def _render_badges(self, post_data: dict) -> str:
        """Render NSFW and cached badges."""
        badges = []
        if post_data.get('over_18'):
            badges.append('<span class="cached-badge nsfw-badge">NSFW</span>')
        if post_data.get('cached'):
            badges.append('<span class="cached-badge">✓ Cached</span>')
        return ''.join(badges)
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        return (text
                .replace('&', '&amp;')
                .replace('<', '&lt;')
                .replace('>', '&gt;')
                .replace('"', '&quot;')
                .replace("'", '&#039;'))


class HtmlViewer(GalleryComponent):
    """Component for viewing cached HTML with custom styling."""
    
    def render_html_with_custom_style(self, post_id: str, original_html: str) -> str:
        """
        Render HTML with custom styling overlay.
        
        Injects custom CSS and JavaScript into the cached HTML.
        """
        custom_css = """
        <style>
            /* Custom gallery styling for cached pages */
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
            }
            
            .gallery-overlay {
                position: fixed;
                top: 10px;
                right: 10px;
                background: rgba(0, 0, 0, 0.8);
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                font-size: 12px;
                z-index: 9999;
            }
            
            img {
                max-width: 100%;
                height: auto;
            }
        </style>
        <div class="gallery-overlay">📁 Cached from Gallery</div>
        """
        
        if '</head>' in original_html:
            return original_html.replace('</head>', custom_css + '</head>')
        else:
            return custom_css + original_html
    
    def cache_and_style_html(self, post_id: str, html: str) -> Path:
        """Cache HTML with custom styling."""
        styled_html = self.render_html_with_custom_style(post_id, html)
        return self.cache_html(post_id, styled_html)


class GalleryManager:
    """Main manager for gallery operations."""
    
    def __init__(self):
        template_dir = Path(__file__).parent.parent / "templates"
        self.catalogue_viewer = CatalogueViewer(template_dir)
        self.html_viewer = HtmlViewer(template_dir)
    
    def cache_post_html(self, post_id: str, html: str, apply_styling: bool = True) -> Path:
        """Cache HTML for a post."""
        if apply_styling:
            return self.html_viewer.cache_and_style_html(post_id, html)
        else:
            return self.html_viewer.cache_html(post_id, html)
    
    def get_stats(self) -> dict:
        """Get gallery statistics."""
        return self.catalogue_viewer.get_gallery_stats()
