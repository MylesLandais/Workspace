"""Rewrite cached HTML to use local images by matching filenames."""

import sys
import os
import re
from pathlib import Path
from typing import Dict, Set


def extract_image_urls_from_html(html_path: Path) -> Set[str]:
    """Extract all 4chan image URLs from HTML."""
    content = html_path.read_text(encoding='utf-8')
    
    # Extract image URLs - they appear as i.4cdn.org/board/filename.ext
    pattern = r'i\.4cdn\.org/\w+/[0-9]+\.[a-z]+'
    urls = set(re.findall(pattern, content))
    
    return urls


def extract_image_urls_full(html_path: Path) -> Set[str]:
    """Extract full image URLs with protocol."""
    content = html_path.read_text(encoding='utf-8')
    
    # Extract full URLs
    pattern = r'https?://i\.4cdn\.org/\w+/[0-9]+\.[a-z]+'
    urls = set(re.findall(pattern, content))
    
    return urls


def find_matching_image(image_url: str, cache_dir: Path) -> Path:
    """
    Find matching cached image by extracting filename from URL.
    
    Args:
        image_url: Image URL (e.g., i.4cdn.org/b/1767287659124289.jpg)
        cache_dir: Cache directory
    
    Returns:
        Path to cached image or None
    """
    # Extract filename from URL
    # Format: i.4cdn.org/b/1767287659124289.jpg
    match = re.search(r'/([0-9]+)\.([a-z]+)$', image_url)
    if not match:
        return None
    
    timestamp = match.group(1)
    ext = match.group(2)
    filename = f"{timestamp}.{ext}"
    
    # Search in board/thread structure
    # URL structure: i.4cdn.org/{board}/{timestamp}.{ext}
    board_match = re.search(r'i\.4cdn\.org/(\w+)/', image_url)
    if board_match:
        board = board_match.group(1)
        thread_dir = cache_dir / board
        
        # Search all thread directories in this board
        if thread_dir.exists():
            for thread_subdir in thread_dir.iterdir():
                if thread_subdir.is_dir():
                    img_file = thread_subdir / filename
                    if img_file.exists():
                        return img_file
    
    # Also check flat structure
    flat_file = cache_dir / filename
    if flat_file.exists():
        return flat_file
    
    return None


def rewrite_html_local(
    html_file: Path,
    cache_dir: Path = None,
    output_file: Path = None
) -> Dict[str, str]:
    """
    Rewrite HTML to use local cached images.
    
    Args:
        html_file: Original HTML file
        cache_dir: Directory containing cached images (default: cache/imageboard/images)
        output_file: Output file (default: <input>_local.html)
    
    Returns:
        Dictionary mapping URLs to local paths
    """
    if cache_dir is None:
        cache_dir = Path("cache/imageboard/images")
    
    if output_file is None:
        output_file = html_file.parent / f"{html_file.stem}_local{html_file.suffix}"
    
    print(f"Processing: {html_file}")
    print(f"Cache dir: {cache_dir}")
    
    # Extract image URLs
    short_urls = extract_image_urls_from_html(html_file)
    full_urls = extract_image_urls_full(html_file)
    all_urls = short_urls.union(full_urls)
    
    print(f"Found {len(all_urls)} image URLs")
    
    # Build URL to local path mapping
    url_to_local: Dict[str, str] = {}
    found_count = 0
    missing_count = 0
    
    for url in all_urls:
        local_path = find_matching_image(url, cache_dir)
        
        if local_path:
            # Calculate relative path from HTML file location
            try:
                rel_path = os.path.relpath(local_path, html_file.parent)
                url_to_local[url] = str(rel_path)
                found_count += 1
                print(f"  ✓ {url.split('/')[-1]} -> {rel_path}")
            except ValueError:
                # Can't make relative, use absolute
                url_to_local[url] = str(local_path)
                found_count += 1
                print(f"  ✓ {url.split('/')[-1]} -> {local_path}")
        else:
            missing_count += 1
            print(f"  ✗ Missing: {url.split('/')[-1]}")
    
    # Rewrite HTML content
    content = html_file.read_text(encoding='utf-8')
    
    # Replace URLs with local paths
    for url, local_path in url_to_local.items():
        # Replace both short and full versions
        content = content.replace(f'//{url}', local_path)
        content = content.replace(f'https://{url}', local_path)
        content = content.replace(f'http://{url}', local_path)
    
    # Write output
    output_file.write_text(content, encoding='utf-8')
    
    print(f"\n" + "=" * 70)
    print(f"Output: {output_file}")
    print(f"Found locally: {found_count}")
    print(f"Missing: {missing_count}")
    print("=" * 70)
    
    return url_to_local


def create_index(html_dir: Path, output_dir: Path = None):
    """Create index.html listing all browsable threads."""
    if output_dir is None:
        output_dir = html_dir
    
    # Find all _local.html files
    local_files = sorted(output_dir.glob("*_local.html"))
    
    # Create index
    index_html = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Imageboard Archive - Local Browser</title>
    <style>
        body { font-family: sans-serif; margin: 40px; background: #1a1a1a; color: #ddd; }
        h1 { color: #fff; border-bottom: 2px solid #444; padding-bottom: 10px; }
        .thread-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }
        .thread-card { background: #2a2a2a; border-radius: 8px; padding: 20px; border: 1px solid #444; }
        .thread-card a { color: #6cb3d9; text-decoration: none; font-weight: bold; }
        .thread-card a:hover { text-decoration: underline; }
        .thread-info { color: #888; font-size: 0.9em; margin-top: 10px; }
        .badge { display: inline-block; background: #6cb3d9; color: #000; padding: 2px 8px; border-radius: 4px; font-size: 0.8em; margin-left: 10px; }
    </style>
</head>
<body>
    <h1>🖼️ Imageboard Archive - Local Browser</h1>
    <p style="color: #888;">Threads with local images</p>
    <div class="thread-list">
"""
    
    for local_file in local_files:
        # Extract board/thread from filename
        match = re.match(r'(\w+)_(\d+)_local\.html', local_file.name)
        if match:
            board, thread_id = match.groups()
            index_html += f"""
        <div class="thread-card">
            <a href="{local_file.name}">/{board}/{thread_id}</a>
            <span class="badge">Local</span>
            <div class="thread-info">Board: {board} | Thread: {thread_id}</div>
        </div>
"""
    
    index_html += """
    </div>
</body>
</html>
"""
    
    index_file = output_dir / "index.html"
    index_file.write_text(index_html, encoding='utf-8')
    print(f"\nCreated index: {index_file}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Rewrite imageboard HTML to use local cached images"
    )
    parser.add_argument(
        "html_file",
        type=Path,
        nargs='?',
        help="Path to cached HTML file (or use --all)"
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=Path("cache/imageboard/images"),
        help="Directory containing cached images"
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Output directory"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Process all HTML files in directory"
    )
    
    args = parser.parse_args()
    
    if args.all:
        # Process all HTML files
        html_dir = args.html_file if args.html_file and args.html_file.is_dir() else Path("cache/imageboard/html")
        output_dir = args.output_dir or html_dir
        
        print(f"Processing all HTML files in: {html_dir}")
        
        for html_file in sorted(html_dir.glob("*.html")):
            if "_local" in html_file.name or html_file.name == "index.html":
                continue
            
            try:
                rewrite_html_local(html_file, args.cache_dir, output_dir / f"{html_file.stem}_local{html_file.suffix}")
            except Exception as e:
                print(f"Error processing {html_file.name}: {e}")
        
        # Create index
        create_index(html_dir, output_dir)
    
    elif args.html_file:
        # Process single file
        rewrite_html_local(args.html_file, args.cache_dir)
    else:
        parser.print_help()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
