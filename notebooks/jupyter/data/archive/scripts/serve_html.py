"""Simple HTTP server to browse imageboard HTML with local images."""

import sys
import os
import re
import hashlib
import http.server
import socketserver
from pathlib import Path
from typing import Dict, Optional
from urllib.parse import urlparse, unquote


def compute_sha256_hash(data: bytes) -> str:
    """Compute SHA-256 hash of data."""
    return hashlib.sha256(data).hexdigest()


class ImageboardHTMLHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler that rewrites image URLs to local cache."""
    
    # Cache directory for images
    IMAGE_CACHE_DIR = None
    # Mapping of original URLs to local paths
    URL_TO_PATH: Dict[str, str] = {}
    # Whether we've built the mapping
    MAPPING_BUILT = False
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    def build_url_mapping(self):
        """Build mapping of image URLs to local cache paths."""
        if self.MAPPING_BUILT:
            return
        
        print("Building URL mapping from cache...")
        count = 0
        
        # Walk through cache directory
        if self.IMAGE_CACHE_DIR and self.IMAGE_CACHE_DIR.exists():
            for board_dir in self.IMAGE_CACHE_DIR.iterdir():
                if not board_dir.is_dir():
                    continue
                
                for thread_dir in board_dir.iterdir():
                    if not thread_dir.is_dir():
                        continue
                    
                    # Look for HTML file
                    html_file = thread_dir.parent.parent.parent / 'html' / f"{board_dir.name}_{thread_dir.name}.html"
                    if html_file.exists():
                        # Extract image URLs from HTML
                        self.extract_urls_from_html(html_file, thread_dir)
                        count += 1
        
        print(f"Processed {count} threads, {len(self.URL_TO_PATH)} images mapped")
        self.MAPPING_BUILT = True
    
    def extract_urls_from_html(self, html_file: Path, thread_dir: Path):
        """Extract and map image URLs from HTML file."""
        try:
            content = html_file.read_text(encoding='utf-8')
            
            # Extract image URLs
            patterns = [
                r'https://i\.4cdn\.org/[^/]+/[0-9]+\.[a-z]+',
                r'//i\.4cdn\.org/[^/]+/[0-9]+\.[a-z]+',
            ]
            
            urls = set()
            for pattern in patterns:
                urls.update(re.findall(pattern, content))
            
            # Map to local images
            for url in urls:
                if url.startswith('//'):
                    url = 'https:' + url
                
                ext = Path(urlparse(url).path).suffix or '.jpg'
                # Download to get hash
                try:
                    import requests
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    img_hash = compute_sha256_hash(response.content)
                    
                    # Find local file by hash
                    for img_file in thread_dir.iterdir():
                        if img_file.name.startswith(img_hash):
                            rel_path = img_file.relative_to(self.IMAGE_CACHE_DIR.parent)
                            self.URL_TO_PATH[url] = str(rel_path)
                            break
                except:
                    pass
                    
        except Exception as e:
            pass
    
    def do_GET(self):
        """Handle GET request."""
        # Parse path
        path = unquote(self.path)
        
        # Serve index.html for root
        if path == '/':
            path = '/index.html'
        
        local_path = Path(self.directory) / path.lstrip('/')
        
        # If it's an HTML file, rewrite it on the fly
        if local_path.exists() and local_path.suffix == '.html':
            self.serve_rewritten_html(local_path)
            return
        
        # Serve file normally
        return super().do_GET()
    
    def serve_rewritten_html(self, html_path: Path):
        """Serve HTML with rewritten image URLs."""
        try:
            content = html_path.read_text(encoding='utf-8')
            
            # Rewrite image URLs
            for url, local_path in self.URL_TO_PATH.items():
                content = content.replace(url, f"/{local_path}")
                content = content.replace(url.replace('https://', '//'), f"/{local_path}")
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, f"Error processing HTML: {e}")
    
    def log_message(self, format, *args):
        """Override logging to be quieter."""
        pass


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="HTTP server for browsing imageboard HTML with local images"
    )
    parser.add_argument(
        "port",
        type=int,
        nargs='?',
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    parser.add_argument(
        "--directory",
        type=Path,
        default=Path("cache/imageboard"),
        help="Directory to serve (default: cache/imageboard)"
    )
    
    args = parser.parse_args()
    
    # Setup handler
    ImageboardHTMLHandler.IMAGE_CACHE_DIR = args.directory / 'images'
    ImageboardHTMLHandler.directory = str(args.directory)
    
    # Build URL mapping
    ImageboardHTMLHandler().build_url_mapping()
    
    # Start server
    with socketserver.TCPServer(("", args.port), ImageboardHTMLHandler) as httpd:
        print(f"Server started at http://localhost:{args.port}")
        print(f"Serving directory: {args.directory}")
        print(f"Images cache: {ImageboardHTMLHandler.IMAGE_CACHE_DIR}")
        print(f"Press Ctrl+C to stop")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nServer stopped")


if __name__ == "__main__":
    sys.exit(main())
