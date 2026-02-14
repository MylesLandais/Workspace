#!/usr/bin/env python3
"""
Regenerate HTML files for all threads in the cache with proper local image paths.
This fixes older threads that were captured before the HTML rewrite logic was added.
"""
import json
from pathlib import Path
from bs4 import BeautifulSoup

CACHE_DIR = Path('/home/jovyan/workspaces/cache/imageboard')

def fix_thread_html(thread_json_path: Path):
    """Regenerate HTML for a single thread with local image paths."""
    try:
        # Load thread JSON
        with open(thread_json_path, 'r') as f:
            thread_data = json.load(f)
        
        board = thread_json_path.parent.parent.name
        thread_id = thread_json_path.parent.name
        
        # Find HTML file
        html_path = thread_json_path.parent / 'index.html'
        if not html_path.exists():
            html_path = thread_json_path.parent.parent.parent.parent / 'html' / f"{board}_{thread_id}.html"
        
        if not html_path.exists():
            print(f"  HTML not found: {html_path}")
            return
        
        # Read HTML
        with open(html_path, 'r', encoding='utf-8') as f:
            html_text = f.read()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(html_text, 'html.parser')
        
        # Create image map from thread data
        image_map = {
            p['no']: p.get('local_image', '')
            for p in thread_data.get('posts', [])
            if 'local_image' in p
        }
        
        # Determine depth based on HTML location
        is_in_threads_dir = 'threads' in str(html_path)
        depth = 3 if is_in_threads_dir else 1
        
        # Calculate relative path prefix
        prefix = "../" * depth
        
        # Update image links
        updated_count = 0
        for post_no, local_filename in image_map.items():
            if not local_filename:
                continue
            
            post_div = soup.find(id=f"pc{post_no}")
            if post_div:
                thumb_link = post_div.find('a', class_='fileThumb')
                if thumb_link:
                    thumb_link['href'] = f"{prefix}shared_images/{local_filename}"
                    img = thumb_link.find('img')
                    if img:
                        img['src'] = f"{prefix}shared_images/{local_filename}"
                        if img.has_attr('srcset'):
                            del img['srcset']
                    updated_count += 1
        
        # Remove base tag if present (it breaks relative paths)
        base_tag = soup.find('base')
        if base_tag:
            base_tag.decompose()
        
        # Write updated HTML
        updated_html = str(soup)
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        
        print(f"  Updated {updated_count} images in {html_path.name}")
        
    except Exception as e:
        print(f"  Error processing {thread_json_path}: {e}")

def main():
    print("=" * 70)
    print("FIXING IMAGEBOARD HTML FILES")
    print("=" * 70)
    
    threads_dir = CACHE_DIR / 'threads'
    if not threads_dir.exists():
        print(f"Threads directory not found: {threads_dir}")
        return
    
    # Find all thread.json files
    thread_files = list(threads_dir.glob('**/thread.json'))
    print(f"Found {len(thread_files)} threads to process")
    
    processed = 0
    for tf in thread_files:
        fix_thread_html(tf)
        processed += 1
        if processed % 10 == 0:
            print(f"  Processed {processed} threads...")
    
    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Processed {processed} threads")

if __name__ == "__main__":
    main()
