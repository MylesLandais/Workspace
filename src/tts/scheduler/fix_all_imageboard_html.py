#!/usr/bin/env python3
"""
Fix offline HTML files for ALL imageboard threads.
Handles both main HTML directory and thread-specific HTML directories.
"""
import json
from pathlib import Path
from bs4 import BeautifulSoup

CACHE_DIR = Path('/home/jovyan/workspaces/cache/imageboard')

def rewrite_html_for_offline(html_text, thread_data, board, thread_id, html_location="main"):
    """
    Rewrite HTML to use local images and fix relative paths.
    
    Args:
        html_text: Raw HTML content
        thread_data: Thread data with posts
        board: Board name
        thread_id: Thread ID
        html_location: 'main' or 'thread' to determine correct relative paths
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Remove base tag (it breaks relative paths)
    base_tag = soup.find('base')
    if base_tag:
        base_tag.decompose()
    
    # Fix all relative links/scripts to be absolute to 4chan
    for tag in soup.find_all(['link', 'script', 'a', 'img', 'form']):
        for attr in ['href', 'src', 'action']:
            if tag.has_attr(attr):
                val = tag[attr]
                if val.startswith('//'):
                    tag[attr] = 'https:' + val
                elif val.startswith('/') and not val.startswith('//'):
                    tag[attr] = 'https://boards.4chan.org' + val
                elif not val.startswith('http') and not val.startswith('#') and not val.startswith('javascript'):
                    # Probable relative path like "index.html" or "b/"
                    tag[attr] = f"https://boards.4chan.org/{board}/" + val
    
    # Map of post_no to local_image
    image_map = {p['no']: p.get('local_image', '') for p in thread_data.get('posts', []) if 'local_image' in p}
    
    # Determine correct relative path prefix based on HTML location
    # Main HTML (html/): depth 1 -> ../shared_images/
    # Thread HTML (threads/b/id/index.html): depth 3 -> ../../../shared_images/
    if html_location == "thread":
        prefix = "../" * 3
    else:
        prefix = "../" * 1
    
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
    
    return soup.prettify(), updated_count

def fix_main_html(thread_json_path: Path):
    """Fix main HTML file (html/b_*.html)."""
    try:
        with open(thread_json_path, 'r') as f:
            thread_data = json.load(f)
        
        board = thread_json_path.parent.parent.name
        thread_id = thread_json_path.parent.name
        
        # Find HTML file (main directory)
        html_path = thread_json_path.parent / 'index.html'
        if not html_path.exists():
            # Check for board_threadID.html naming
            html_path = thread_json_path.parent.parent / f"{board}_{thread_id}.html"
            if not html_path.exists():
                print(f"  HTML not found: {html_path}")
                return
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_text = f.read()
        
        updated_html, count = rewrite_html_for_offline(html_text, thread_data, board, thread_id, html_location="main")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        
        print(f"  Fixed: {html_path.name} ({count} images)")
        
    except Exception as e:
        print(f"  Error processing {thread_json_path}: {e}")

def fix_thread_html(thread_json_path: Path):
    """Fix thread-specific HTML file (threads/b/*/index.html)."""
    try:
        with open(thread_json_path, 'r') as f:
            thread_data = json.load(f)
        
        board = thread_json_path.parent.parent.name
        thread_id = thread_json_path.parent.name
        
        # Find HTML file (thread directory)
        html_path = thread_json_path / 'index.html'
        if not html_path.exists():
            print(f"  HTML not found: {html_path}")
            return
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_text = f.read()
        
        updated_html, count = rewrite_html_for_offline(html_text, thread_data, board, thread_id, html_location="thread")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        
        print(f"  Fixed: {board}/{thread_id}/index.html ({count} images)")
        
    except Exception as e:
        print(f"  Error processing {thread_json_path}: {e}")

def main():
    print("=" * 70)
    print("FIXING ALL IMAGEBOARD HTML FILES")
    print("=" * 70)
    
    # Find all thread.json files
    threads_dir = CACHE_DIR / 'threads'
    if not threads_dir.exists():
        print(f"Threads directory not found: {threads_dir}")
        return
    
    thread_files = list(threads_dir.glob('**/thread.json'))
    print(f"Found {len(thread_files)} threads to fix")
    
    total_fixed = 0
    main_fixed = 0
    thread_fixed = 0
    
    for tf in thread_files:
        # Try fixing thread-specific HTML
        fixed, count = fix_thread_html(tf)
        if fixed:
            thread_fixed += 1
            total_fixed += count
        else:
            # Fix main HTML as fallback
            fixed, count = fix_main_html(tf)
            if fixed:
                main_fixed += 1
                total_fixed += count
    
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Thread-specific HTMLs fixed: {thread_fixed}")
    print(f"Main HTMLs fixed: {main_fixed}")
    print(f"Total images updated: {total_fixed}")
    print(f"\nAll HTML files now use local image paths correctly.")

if __name__ == "__main__":
    main()
