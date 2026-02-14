#!/usr/bin/env python3
"""
Create a single self-contained Parquet file with everything embedded:
- Post metadata
- Image bytes
- Original HTML for each thread

This creates an "everything bagel" archive suitable for:
- HuggingFace Dataset Viewer
- Future HTML parsing/analysis
- Complete archival
"""
import json
import sys
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
import pandas as pd
import pyarrow as pa
from pyarrow.parquet import write_table

# Configuration
CACHE_DIR = Path('/home/jovyan/workspaces/cache/imageboard')
OUTPUT_DIR = Path('/home/jovyan/workspaces/packs')
MAX_WORKERS = 8

def read_image_bytes(sha256: str) -> bytes | None:
    """Read image bytes from shared_images directory."""
    if not sha256:
        return None
    img_path = CACHE_DIR / 'shared_images' / f"{sha256}.jpg"
    if img_path.exists():
        try:
            with open(img_path, 'rb') as f:
                return f.read()
        except Exception as e:
            print(f"  Warning: Could not read image {sha256}: {e}")
            return None
    return None

def read_html_content(board: str, thread_id: str) -> str | None:
    """Read the cached HTML file for a thread."""
    html_path = CACHE_DIR / 'html' / f"{board}_{thread_id}.html"
    if html_path.exists():
        try:
            with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        except Exception as e:
            return None
    return None

def process_thread(thread_file: Path) -> list[dict]:
    """Process a single thread file and return all posts with embedded data."""
    board = thread_file.parent.parent.name
    thread_id = thread_file.parent.name
    
    try:
        with open(thread_file, 'r') as f:
            thread = json.load(f)
    except Exception as e:
        print(f"Error reading {thread_file}: {e}")
        return []
    
    # Read HTML once for all posts in this thread
    html_content = read_html_content(board, thread_id)
    
    posts = []
    for post in thread.get('posts', []):
        local_img = post.get('local_image', '')
        sha256 = local_img.split('.')[0] if local_img else None
        
        post_data = {
            # Unique ID
            'id': f"{board}_{thread_id}_{post['no']}",
            
            # Thread context
            'board': board,
            'thread_id': int(thread_id),
            'post_no': post['no'],
            'is_op': post['no'] == int(thread_id),
            
            # Timestamps
            'timestamp': post.get('time'),
            'datetime_iso': datetime.fromtimestamp(post['time']).isoformat() if post.get('time') else None,
            
            # Content
            'subject': post.get('sub', ''),
            'text': post.get('com', ''),
            'subject_raw': post.get('subject', ''),  # Original HTML
            
            # Image metadata
            'image_id': post.get('tim'),
            'image_ext': post.get('ext', ''),
            'image_sha256': sha256,
            'image_url': f"https://i.4cdn.org/{board}/{post['tim']}{post['ext']}" if post.get('tim') else None,
            'image_width': post.get('w'),
            'image_height': post.get('h'),
            'image_size_bytes': post.get('fsize'),
            
            # Embedded data (populated later)
            'image_bytes': None,  # bytes
            'html_content': html_content,  # string - same for all posts in thread
            
            # Moderation
            'is_moderated': post.get('moderated', False),
            'moderation_reason': post.get('moderation_reason') or None,
            
            # Archive metadata
            'archived_at': datetime.now().isoformat(),
            'thread_subject': thread.get('posts', [{}])[0].get('sub', '') if thread.get('posts') else '',
        }
        posts.append(post_data)
    
    return posts

def main():
    output_path = OUTPUT_DIR / f"imageboard_full_embed_{datetime.now().strftime('%Y%m%d')}.parquet"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    print("=" * 70)
    print("PACKING EVERYTHING: Single Parquet with Images + HTML")
    print("=" * 70)
    
    # Find all thread files (recursive glob)
    thread_files = list((CACHE_DIR / 'threads').glob('**/thread.json'))
    print(f"Found {len(thread_files)} threads to process")
    
    # Process all threads
    all_posts = []
    for tf in thread_files:
        posts = process_thread(tf)
        all_posts.extend(posts)
    
    print(f"Collected {len(all_posts)} posts")
    
    # Pre-load image bytes for all unique images
    print("Loading image bytes...")
    unique_hashes = {p['image_sha256'] for p in all_posts if p['image_sha256']}
    hash_to_bytes = {}
    
    for i, h in enumerate(unique_hashes):
        bytes_data = read_image_bytes(h)
        if bytes_data:
            hash_to_bytes[h] = bytes_data
        if (i + 1) % 500 == 0:
            print(f"  Loaded {i + 1}/{len(unique_hashes)} images")
    
    print(f"Loaded {len(hash_to_bytes)} unique images")
    
    # Inject image bytes into posts
    for post in all_posts:
        if post['image_sha256']:
            post['image_bytes'] = hash_to_bytes.get(post['image_sha256'])
    
    # Create DataFrame
    print("Creating DataFrame...")
    df = pd.DataFrame(all_posts)
    
    # Define explicit PyArrow schema for better compression and type safety
    schema = pa.schema([
        ('id', pa.string()),
        ('board', pa.string()),
        ('thread_id', pa.int64()),
        ('post_no', pa.int64()),
        ('is_op', pa.bool_()),
        ('timestamp', pa.int64()),
        ('datetime_iso', pa.string()),
        ('subject', pa.string()),
        ('text', pa.string()),
        ('subject_raw', pa.string()),
        ('image_id', pa.int64()),
        ('image_ext', pa.string()),
        ('image_sha256', pa.string()),
        ('image_url', pa.string()),
        ('image_width', pa.int64()),
        ('image_height', pa.int64()),
        ('image_size_bytes', pa.int64()),
        ('image_bytes', pa.binary()),  # Stores actual image data
        ('html_content', pa.string()),  # Full thread HTML
        ('is_moderated', pa.bool_()),
        ('moderation_reason', pa.string()),
        ('archived_at', pa.string()),
        ('thread_subject', pa.string()),
    ])
    
    # Convert to PyArrow with explicit schema
    table = pa.Table.from_pandas(df, schema=schema)
    
    # Write with compression
    print(f"Writing to {output_path}...")
    write_table(table, output_path, compression='snappy')
    
    # Calculate sizes
    parquet_size = output_path.stat().st_size
    images_size = sum(len(b) for b in hash_to_bytes.values())
    html_size = sum(len(p['html_content'] or '') for p in all_posts)
    
    print("\n" + "=" * 70)
    print("PACK COMPLETE")
    print("=" * 70)
    print(f"\nParquet file: {output_path.name}")
    print(f"  Total size: {parquet_size / (1024**2):.1f} MB")
    print(f"  Posts: {len(df)}")
    print(f"  Unique images embedded: {len(hash_to_bytes)}")
    print(f"  Image bytes: {images_size / (1024**2):.1f} MB")
    print(f"  HTML content: {html_size / (1024**2):.1f} MB")
    print(f"  Metadata overhead: {(parquet_size - images_size - html_size) / (1024**2):.1f} MB")
    print("\nSchema columns:")
    for field in schema:
        print(f"  {field.name}: {field.type}")
    print("\nUsage:")
    print("  # Load and view")
    print("  df = pd.read_parquet('imageboard_full_embed_20260105.parquet')")
    print("  ")
    print("  # View image from post")
    print("  from PIL import Image")
    print("  import io")
    print("  img = Image.open(io.BytesIO(df.iloc[0]['image_bytes']))")
    print("  ")
    print("  # Access original HTML for analysis")
    print("  html = df.iloc[0]['html_content']")

if __name__ == "__main__":
    main()
