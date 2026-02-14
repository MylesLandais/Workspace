#!/usr/bin/env python3
"""
Bulk Media Downloader for Erome.fan
Similar to j-downloader - downloads all media from an Erome.fan album to MinIO/S3.
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Optional
import time
import hashlib
from urllib.parse import urlparse
import random

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Playwright not installed. Install with: pip install playwright")

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("BeautifulSoup not installed. Install with: pip install beautifulsoup4")

import requests
from src.feed.storage.minio_connection import get_minio_connection


class EromeDownloader:
    """Downloads media from Erome.fan albums to MinIO/S3."""

    def __init__(
        self,
        bucket_name: str = "media",
        delay_min: float = 1.0,
        delay_max: float = 2.0,
    ):
        """
        Initialize Erome downloader.

        Args:
            bucket_name: MinIO bucket name
            delay_min: Minimum delay between downloads (seconds)
            delay_max: Maximum delay between downloads (seconds)
        """
        self.bucket_name = bucket_name
        self.delay_min = delay_min
        self.delay_max = delay_max
        self.minio = get_minio_connection()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        })

    def _delay(self):
        """Add random delay between downloads."""
        import random
        time.sleep(random.uniform(self.delay_min, self.delay_max))

    def _get_content_type(self, url: str) -> str:
        """
        Get content type from URL.

        Args:
            url: URL to check

        Returns:
            Content type (e.g., 'image/jpeg', 'video/mp4')
        """
        ext = url.split('.')[-1].lower()
        content_types = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'gif': 'image/gif',
            'webp': 'image/webp',
            'mp4': 'video/mp4',
            'webm': 'video/webm',
            'mov': 'video/quicktime',
        }
        return content_types.get(ext, 'image/jpeg')

    def _generate_object_key(self, url: str, index: int, total: int) -> str:
        """
        Generate object key for MinIO storage.

        Args:
            url: Image URL
            index: Image index in album
            total: Total number of images

        Returns:
            Object key path
        """
        # Create organized path: erome/<album-id>/<index>-<hash>.<ext>
        parsed = urlparse(url)
        ext = parsed.path.split('.')[-1].lower()

        # Create hash of URL for unique identifier
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8]

        # Generate padded index
        index_str = str(index).zfill(len(str(total)))

        return f"erome/{index_str}-{url_hash}.{ext}"

    def download_album(self, album_url: str) -> dict:
        """
        Download all media from an Erome.fan album.

        Args:
            album_url: Erome.fan album URL

        Returns:
            Dictionary with results
        """
        print(f"\n📦 Downloading from: {album_url}")
        print("=" * 70)

        try:
            # Use Playwright to access the page
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                )
                page = context.new_page()

                print("  🔄 Loading page...")
                page.goto(album_url, wait_until='networkidle', timeout=30000)
                time.sleep(2)

                # Get page content
                content = page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # Extract album title
                title = soup.find('title')
                album_title = title.get_text().strip() if title else "Unknown Album"
                print(f"  📌 Album: {album_title}")

                # Extract all images
                print("  🖼️  Finding images...")
                images = []

                for img in soup.find_all('img'):
                    src = img.get('src') or img.get('data-src')
                    if src and 'http' in src:
                        # Skip small/placeholder images
                        if 'logo' in src.lower() or 'icon' in src.lower():
                            continue
                        if 'cropped-logo' in src:
                            continue

                        # Skip very small images (likely thumbnails/icons)
                        classes = img.get('class', [])
                        if 'is-logo-image' in classes:
                            continue

                        # Only keep actual content images (with lazy-load classes)
                        if 'lasyload' in classes:
                            images.append(src)

                # Deduplicate images
                images = list(dict.fromkeys(images))  # Preserve order, remove duplicates
                print(f"  ✅ Found {len(images)} unique images")

                if not images:
                    print("  ❌ No images found")
                    return {
                        'album_title': album_title,
                        'album_url': album_url,
                        'total': 0,
                        'downloaded': 0,
                        'skipped': 0,
                        'failed': 0,
                        'images': [],
                    }

                # Ensure bucket exists
                print(f"  🗄️  Ensuring bucket: {self.bucket_name}")
                self.minio.ensure_bucket(self.bucket_name)

                # Download each image
                print(f"\n  📥 Downloading images...")
                print("-" * 70)

                downloaded = 0
                skipped = 0
                failed = 0
                results = []

                for i, img_url in enumerate(images, 1):
                    print(f"  [{i}/{len(images)}] ", end='', flush=True)

                    # Check if already exists
                    object_key = self._generate_object_key(img_url, i, len(images))
                    if self.minio.object_exists(self.bucket_name, object_key):
                        print(f"✓ (exists)")
                        skipped += 1
                        results.append({
                            'url': img_url,
                            'key': object_key,
                            'status': 'exists',
                        })
                        continue

                    # Download image
                    try:
                        response = self.session.get(img_url, timeout=30)
                        response.raise_for_status()

                        # Upload to MinIO
                        content_type = self._get_content_type(img_url)
                        success = self.minio.upload_bytes(
                            self.bucket_name,
                            object_key,
                            response.content,
                            content_type=content_type,
                        )

                        if success:
                            print(f"✓ {object_key}")
                            downloaded += 1
                            results.append({
                                'url': img_url,
                                'key': object_key,
                                'status': 'downloaded',
                            })
                        else:
                            print(f"✗ upload failed")
                            failed += 1
                            results.append({
                                'url': img_url,
                                'key': object_key,
                                'status': 'upload_failed',
                            })

                        self._delay()

                    except Exception as e:
                        print(f"✗ {e}")
                        failed += 1
                        results.append({
                            'url': img_url,
                            'key': object_key,
                            'status': f'error: {str(e)[:50]}',
                        })

                browser.close()

        except Exception as e:
            print(f"  ❌ Error downloading album: {e}")
            import traceback
            traceback.print_exc()
            return {
                'album_title': album_url,
                'album_url': album_url,
                'total': 0,
                'downloaded': 0,
                'skipped': 0,
                'failed': 1,
                'images': [],
            }

        # Summary
        print("-" * 70)
        print(f"\n  📊 Summary:")
        print(f"     Total images: {len(images)}")
        print(f"     Downloaded: {downloaded}")
        print(f"     Skipped (exists): {skipped}")
        print(f"     Failed: {failed}")
        print("=" * 70)

        return {
            'album_title': album_title,
            'album_url': album_url,
            'total': len(images),
            'downloaded': downloaded,
            'skipped': skipped,
            'failed': failed,
            'images': results,
        }

    def list_downloaded(self, album_id: str) -> List[dict]:
        """
        List all files downloaded for an album.

        Args:
            album_id: Album ID (extracted from URL)

        Returns:
            List of object information
        """
        try:
            from minio.commonconfig import CopySource
            client = self.minio.get_minio_client()

            # List objects in bucket
            objects = client.list_objects(
                self.bucket_name,
                prefix=f"erome/{album_id}",
                recursive=True,
            )

            results = []
            for obj in objects.objects:
                results.append({
                    'key': obj.object_name,
                    'size': obj.size,
                    'last_modified': obj.last_modified,
                })

            return results

        except Exception as e:
            print(f"Error listing objects: {e}")
            return []


def main():
    parser = argparse.ArgumentParser(
        description="Bulk download Erome.fan albums to MinIO/S3 (j-downloader style)"
    )
    parser.add_argument(
        "url",
        help="Erome.fan album URL (e.g., https://erome.fan/a/54134914032143465)"
    )
    parser.add_argument(
        "--bucket",
        default="media",
        help="MinIO bucket name (default: media)"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Only list files, don't download"
    )
    parser.add_argument(
        "--delay-min",
        type=float,
        default=1.0,
        help="Minimum delay between downloads (seconds, default: 1.0)"
    )
    parser.add_argument(
        "--delay-max",
        type=float,
        default=2.0,
        help="Maximum delay between downloads (seconds, default: 2.0)"
    )

    args = parser.parse_args()

    # Initialize downloader
    downloader = EromeDownloader(
        bucket_name=args.bucket,
        delay_min=args.delay_min,
        delay_max=args.delay_max,
    )

    # Extract album ID from URL
    album_id = args.url.rstrip('/').split('/')[-1]
    print(f"Album ID: {album_id}")

    if args.list:
        # List only
        print(f"\n📋 Listing files for album {album_id}:")
        objects = downloader.list_downloaded(album_id)
        if objects:
            for obj in objects:
                print(f"  - {obj['key']} ({obj['size']} bytes)")
        else:
            print("  (none)")
        return 0

    # Download album
    result = downloader.download_album(args.url)

    # Exit with error code if any downloads failed
    return 1 if result['failed'] > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
