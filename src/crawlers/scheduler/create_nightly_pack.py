"""Create nightly parquet packs from imageboard cache for archival."""

import sys
import os
import tarfile
import hashlib
import re
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
import argparse
import json

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "src"))


try:
    import pandas as pd
    import pyarrow as pa
    from pyarrow.parquet import write_table
except ImportError as e:
    print(f"Error: Required packages not installed: {e}")
    print("Install with: pip install pandas pyarrow")
    raise


def compute_directory_hash(dir_path: Path) -> str:
    """Compute hash of all files in directory for change detection."""
    hash_obj = hashlib.sha256()
    
    if not dir_path.exists():
        return hash_obj.hexdigest()
    
    for file_path in sorted(dir_path.rglob("*")):
        if file_path.is_file():
            relative_path = file_path.relative_to(dir_path)
            hash_obj.update(str(relative_path).encode())
            hash_obj.update(str(file_path.stat().st_mtime).encode())
            hash_obj.update(str(file_path.stat().st_size).encode())
    
    return hash_obj.hexdigest()


def parse_imageboard_thread_from_html(html_path: Path) -> Optional[Dict[str, Any]]:
    """Parse imageboard thread metadata from cached HTML file."""
    try:
        from bs4 import BeautifulSoup
        
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, "html.parser")
        
        filename = html_path.stem
        parts = filename.split("_")
        if len(parts) < 2:
            return None
        
        board = parts[0]
        thread_id = int(parts[1])
        
        title = ""
        title_elem = soup.select_one(".subject, .post-title")
        if title_elem:
            title = title_elem.get_text(strip=True)
        
        posts = soup.select(".post")
        post_count = len(posts)
        
        images = []
        for post in posts:
            for img in post.select("img"):
                img_src = img.get("src", "")
                if "i.4cdn.org" in img_src:
                    images.append({
                        "url": img_src if img_src.startswith("http") else f"https:{img_src}",
                        "alt": img.get("alt", ""),
                    })
        
        return {
            "board": board,
            "thread_id": thread_id,
            "url": f"https://boards.4chan.org/{board}/thread/{thread_id}",
            "title": title,
            "post_count": post_count,
            "image_count": len(images),
            "html_path": str(html_path),
            "html_filename": html_path.name,
            "file_size": html_path.stat().st_size,
            "file_modified": datetime.fromtimestamp(html_path.stat().st_mtime).isoformat(),
            "cached_at": datetime.now().isoformat(),
        }
    except Exception as e:
        print(f"  Error parsing {html_path}: {e}")
        return None


def get_cached_images(cache_dir: Path) -> List[Dict[str, Any]]:
    """Scan cached images directory and build metadata."""
    images = []
    images_dir = cache_dir / "images"
    
    if not images_dir.exists():
        return images
    
    for img_path in images_dir.rglob("*"):
        if img_path.is_file() and img_path.suffix.lower() in {".jpg", ".jpeg", ".png", ".gif", ".webp"}:
            try:
                file_hash = hashlib.sha256()
                with open(img_path, "rb") as f:
                    file_hash.update(f.read())
                sha256 = file_hash.hexdigest()
                
                images.append({
                    "sha256": sha256,
                    "local_path": str(img_path),
                    "relative_path": str(img_path.relative_to(images_dir)),
                    "filename": img_path.name,
                    "file_size": img_path.stat().st_size,
                    "file_modified": datetime.fromtimestamp(img_path.stat().st_mtime).isoformat(),
                    "cached_at": datetime.now().isoformat(),
                })
            except Exception as e:
                print(f"  Error processing image {img_path}: {e}")
    
    return images


def parse_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Parse timestamp string to datetime.
    
    Supports:
    - Exact date: "2026-01-02", "2026-01-02T18:00:00"
    - Keywords: "today", "yesterday"
    - Relative: "3 days ago", "1 week ago"
    - YYYYMMDD: "20260102"
    
    Returns:
        datetime object or None if invalid
    """
    timestamp_lower = timestamp.lower().strip()
    today = datetime.now()
    
    if timestamp_lower == "today":
        return today
    
    if timestamp_lower == "yesterday":
        return today - timedelta(days=1)
    
    if "ago" in timestamp_lower:
        match = re.match(r"(\d+)\s+(day|week|month)s?\s+ago", timestamp_lower)
        if match:
            num = int(match.group(1))
            unit = match.group(2)
            
            if unit == "day":
                return today - timedelta(days=num)
            elif unit == "week":
                return today - timedelta(weeks=num)
            elif unit == "month":
                return today - timedelta(days=num * 30)
    
    date_formats = [
        "%Y-%m-%d",
        "%Y-%m-%dT%H:%M:%S",
        "%Y%m%d",
    ]
    
    for fmt in date_formats:
        try:
            return datetime.strptime(timestamp, fmt)
        except ValueError:
            continue
    
    return None


def create_nightly_pack(
    cache_dir: Path,
    output_dir: Path,
    pack_name: Optional[str] = None,
    include_html: bool = True,
    include_images: bool = True,
    include_html_content: bool = False,
    include_image_content: bool = False,
    compress: bool = True,
) -> Dict[str, Any]:
    """
    Create a nightly pack from imageboard cache.
    
    Args:
        cache_dir: Source cache directory
        output_dir: Output directory for pack
        pack_name: Custom pack name (default: nightly-YYYY-MM-DD)
        include_html: Include HTML files in parquet metadata
        include_images: Include image metadata in parquet
        include_html_content: Copy actual HTML files to pack
        include_image_content: Copy actual image files to pack (full backup)
        compress: Compress output tarball
    
    Returns:
        Dictionary with pack metadata
    """
    if pack_name is None:
        pack_name = f"nightly-{datetime.now().strftime('%Y-%m-%d')}"
    
    pack_dir = output_dir / pack_name
    pack_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print(f"CREATING NIGHTLY PACK: {pack_name}")
    print("=" * 70)
    print(f"Cache directory: {cache_dir.absolute()}")
    print(f"Output directory: {pack_dir.absolute()}")
    print()
    
    metadata: Dict[str, Any] = {
        "pack_name": pack_name,
        "created_at": datetime.now().isoformat(),
        "cache_hash": compute_directory_hash(cache_dir),
        "source_cache_dir": str(cache_dir.absolute()),
    }
    
    html_dir = cache_dir / "html"
    images_data = []
    
    if include_html and html_dir.exists():
        print("Processing HTML files...")
        threads = []
        html_files = list(html_dir.glob("*.html"))
        
        for html_file in html_files:
            thread_data = parse_imageboard_thread_from_html(html_file)
            if thread_data:
                threads.append(thread_data)
        
        if threads:
            df_threads = pd.DataFrame(threads)
            threads_file = pack_dir / "threads.parquet"
            table = pa.Table.from_pandas(df_threads)
            write_table(table, threads_file)
            print(f"  Saved {len(threads)} threads to {threads_file}")
            
            metadata["thread_count"] = len(threads)
            metadata["threads_file"] = str(threads_file.relative_to(output_dir))
    
    if include_images:
        print("\nProcessing images...")
        images_data = get_cached_images(cache_dir)
        
        if images_data:
            df_images = pd.DataFrame(images_data)
            images_file = pack_dir / "images.parquet"
            table = pa.Table.from_pandas(df_images)
            write_table(table, images_file)
            print(f"  Saved {len(images_data)} images to {images_file}")
            
            metadata["image_count"] = len(images_data)
            metadata["unique_images"] = len(set(img["sha256"] for img in images_data))
            metadata["images_file"] = str(images_file.relative_to(output_dir))
    
    if include_images and images_data:
        print("\nComputing image statistics...")
        total_size = sum(img["file_size"] for img in images_data)
        avg_size = total_size / len(images_data) if images_data else 0
        by_ext: Dict[str, Dict[str, int]] = {}
        
        for img in images_data:
            ext = img["filename"].split(".")[-1].lower()
            if ext not in by_ext:
                by_ext[ext] = {"count": 0, "size_bytes": 0}
            by_ext[ext]["count"] += 1
            by_ext[ext]["size_bytes"] += img["file_size"]
        
        metadata["stats"] = {
            "total_size_bytes": total_size,
            "avg_size_bytes": avg_size,
            "by_extension": by_ext,
        }
        print(f"  Total size: {total_size / (1024*1024):.1f} MB")
    
    if include_html_content and html_dir.exists():
        print("\nCopying HTML files...")
        pack_html_dir = pack_dir / "html"
        if pack_html_dir.exists():
            shutil.rmtree(pack_html_dir)
        shutil.copytree(html_dir, pack_html_dir)
        html_count = len(list(pack_html_dir.glob("*.html")))
        print(f"  Copied {html_count} HTML files")
        metadata["html_dir"] = "html"
        metadata["html_files_count"] = html_count
    
    if include_image_content and cache_dir.exists():
        print("\nCopying image files...")
        pack_images_dir = pack_dir / "images"
        if pack_images_dir.exists():
            shutil.rmtree(pack_images_dir)
        cache_images_dir = cache_dir / "images"
        shutil.copytree(cache_images_dir, pack_images_dir)
        image_file_count = len(list(pack_images_dir.rglob("*")))
        print(f"  Copied {image_file_count} image files")
        metadata["images_dir"] = "images"
        metadata["images_files_count"] = image_file_count
    
    metadata_file = pack_dir / "metadata.json"
    with open(metadata_file, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"\nSaved metadata to {metadata_file}")
    
    if compress:
        print(f"\nCreating archive...")
        archive_name = f"{pack_name}.tar.gz" if compress else f"{pack_name}.tar"
        archive_path = output_dir / archive_name
        
        with tarfile.open(archive_path, "w:gz" if compress else "w") as tar:
            for file_path in pack_dir.rglob("*"):
                if file_path.is_file() and file_path != archive_path:
                    tar.add(file_path, arcname=file_path.relative_to(pack_dir))
        
        archive_size = archive_path.stat().st_size
        print(f"Created archive: {archive_path}")
        print(f"Archive size: {archive_size / (1024*1024):.1f} MB")
        
        metadata["archive_file"] = str(archive_path.relative_to(output_dir))
        metadata["archive_size_bytes"] = archive_size
        
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    
    print("\n" + "=" * 70)
    print("NIGHTLY PACK COMPLETE")
    print("=" * 70)
    print(f"\nPack: {pack_name}")
    print(f"Location: {pack_dir.absolute()}")
    if include_html:
        print(f"  Threads: {metadata.get('thread_count', 0)}")
    if include_html_content:
        print(f"  HTML files copied: {metadata.get('html_files_count', 0)}")
    if include_images:
        print(f"  Images: {metadata.get('image_count', 0)}")
        print(f"  Unique images: {metadata.get('unique_images', 0)}")
        stats = metadata.get('stats', {})
        if stats:
            print(f"  Total size: {stats.get('total_size_bytes', 0) / (1024*1024):.1f} MB")
    if include_image_content:
        print(f"  Image files copied: {metadata.get('images_files_count', 0)}")
    if compress and "archive_file" in metadata:
        print(f"  Archive: {metadata['archive_file']}")
        print(f"  Archive size: {metadata.get('archive_size_bytes', 0) / (1024*1024):.1f} MB")
    
    return metadata


def list_packs(output_dir: Path) -> List[Dict[str, Any]]:
    """List all available nightly packs."""
    packs = []
    
    for pack_dir in sorted(output_dir.glob("nightly-*")):
        metadata_file = pack_dir / "metadata.json"
        if metadata_file.exists():
            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    pack_metadata = json.load(f)
                packs.append(pack_metadata)
            except Exception as e:
                print(f"Error reading {metadata_file}: {e}")
    
    return packs


def main():
    parser = argparse.ArgumentParser(
        description="Create nightly parquet packs from imageboard cache"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache/imageboard"),
        help="Source cache directory (default: cache/imageboard)"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("packs"),
        help="Output directory for packs (default: packs)"
    )
    parser.add_argument(
        "--pack-name",
        type=str,
        default=None,
        help="Custom pack name (default: nightly-YYYY-MM-DD)"
    )
    parser.add_argument(
        "--no-html",
        action="store_true",
        help="Don't include HTML files"
    )
    parser.add_argument(
        "--no-images",
        action="store_true",
        help="Don't include images"
    )
    parser.add_argument(
        "--include-html-content",
        action="store_true",
        help="Copy actual HTML files to pack (full backup)"
    )
    parser.add_argument(
        "--include-image-content",
        action="store_true",
        help="Copy actual image files to pack (full backup)"
    )
    parser.add_argument(
        "--no-compress",
        action="store_true",
        help="Don't compress output tarball"
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="List available packs instead of creating new one"
    )
    
    args = parser.parse_args()
    
    output_dir = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if args.list:
        print("=" * 70)
        print("AVAILABLE NIGHTLY PACKS")
        print("=" * 70)
        packs = list_packs(output_dir)
        
        for pack in packs:
            print(f"\n{pack['pack_name']}")
            print(f"  Created: {pack['created_at']}")
            print(f"  Threads: {pack.get('thread_count', 0)}")
            print(f"  Images: {pack.get('image_count', 0)}")
            stats = pack.get('stats', {})
            if stats:
                print(f"  Size: {stats.get('total_size_bytes', 0) / (1024*1024):.1f} MB")
            if 'archive_file' in pack:
                print(f"  Archive: {pack['archive_file']}")
        
        if not packs:
            print("No packs found")
        
        return
    
    create_nightly_pack(
        cache_dir=args.cache_dir,
        output_dir=output_dir,
        pack_name=args.pack_name,
        include_html=not args.no_html,
        include_images=not args.no_images,
        include_html_content=args.include_html_content,
        include_image_content=args.include_image_content,
        compress=not args.no_compress,
    )


if __name__ == "__main__":
    sys.exit(main())
