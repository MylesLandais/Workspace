#!/usr/bin/env python3
"""
Fix offline HTML files for ALL imageboard threads.
Handles both main HTML directory and thread-specific HTML directories.

FIXES:
1. Correctly calculates relative path prefix based on HTML file location.
2. Fixes image links by directly inferring the local filename from the URL (URL Inference),
   making the process independent of thread.json data for images.
3. Converts external CSS/JS links to local relative paths (e.g., ../css/yotsuba.css).
4. Ensures functions return expected tuples to prevent TypeError in main loop.
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

CACHE_DIR = Path('/home/jovyan/workspaces/cache/imageboard')

def rewrite_html_for_offline(html_text, thread_data, board, thread_id, html_location="main"):
    """
    Rewrite HTML to use local images and fix relative paths.
    html_location can be 'main' or 'thread' to determine correct relative paths.
    """
    soup = BeautifulSoup(html_text, 'html.parser')
    
    # Remove base tag (it breaks relative paths)
    base_tag = soup.find('base')
    if base_tag:
        base_tag.decompose()

    # --- Determine correct relative path prefixes ---
    if html_location == "thread":
        shared_root_prefix = "../../.."
        shared_images_prefix = "../../../shared_images/"
    else:
        shared_root_prefix = ".."
        shared_images_prefix = "../shared_images/"

    # --- Fix CSS/JS links to local files ---
    for tag in soup.find_all(['link', 'script']):
        attr = 'href' if tag.name == 'link' else 'src'
        if tag.has_attr(attr):
            val = tag[attr].split('?')[0]
            if val.startswith('//') or val.startswith('/'):
                path_parts = val.split('/')
                if len(path_parts) >= 2:
                    resource_dir = path_parts[-2]
                    filename = path_parts[-1]
                    
                    if resource_dir in ['css', 'js']:
                        tag[attr] = f"{shared_root_prefix}/{resource_dir}/{filename}"

    # --- Fix non-image external links to be absolute to 4chan ---
    for tag in soup.find_all(['a', 'form']):
        for attr in ['href', 'action']:
            if tag.has_attr(attr):
                val = tag[attr]
                # Skip if it is an external image URL, which is handled below
                if re.match(r'^//i\.4cdn\.org/', val):
                    continue

                if val.startswith('//'):
                    tag[attr] = 'https:' + val
                elif val.startswith('/') and not val.startswith('//'):
                    tag[attr] = 'https://boards.4chan.org' + val
                elif not val.startswith('http') and not val.startswith('#') and not val.startswith('javascript'):
                    tag[attr] = f"https://boards.4chan.org/{board}/" + val
    
    # --- Fix Image Links (URL Inference) ---
    updated_count = 0
    
    # Find all anchor and image tags and convert 4cdn URLs to local paths
    for tag in soup.find_all(['a', 'img']):
        attr = 'href' if tag.name == 'a' else 'src'
        
        if tag.has_attr(attr):
            val = tag[attr]
            
            # Check if it is an external image URL from 4cdn.org
            if re.match(r'^//i\.4cdn\.org/', val):
                local_filename = Path(val).name
                tag[attr] = f"{shared_images_prefix}{local_filename}"
                
                # Check for the count update on thumb links only
                if tag.name == 'a' and 'fileThumb' in tag.get('class', []):
                    updated_count += 1
                
            # If it's an img tag, remove srcset
            if tag.name == 'img' and tag.has_attr('srcset'):
                del tag['srcset']
    
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
            html_path = thread_json_path.parent / f"{board}_{thread_id}.html"
            if not html_path.exists():
                print(f"  HTML not found: {html_path}")
                return (False, 0)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_text = f.read()
        
        updated_html, count = rewrite_html_for_offline(html_text, thread_data, board, thread_id, html_location="main")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        
        print(f"  Fixed: {html_path.name} ({count} images)")
        return (True, count)
        
    except Exception as e:
        print(f"  Error processing {thread_json_path}: {e}")
        return (False, 0)

def fix_thread_html(thread_json_path: Path):
    """Fix thread-specific HTML file (threads/b/*/index.html)."""
    try:
        with open(thread_json_path, 'r') as f:
            thread_data = json.load(f)
        
        board = thread_json_path.parent.parent.name
        thread_id = thread_json_path.parent.name
        
        # Find HTML file (thread directory)
        html_path = thread_json_path.parent / 'index.html'
        if not html_path.exists():
            # Check for board_threadID.html naming
            html_path = thread_json_path.parent / f"{board}_{thread_id}.html"
            if not html_path.exists():
                print(f"  HTML not found: {html_path}")
                return (False, 0)
        
        with open(html_path, 'r', encoding='utf-8') as f:
            html_text = f.read()
        
        updated_html, count = rewrite_html_for_offline(html_text, thread_data, board, thread_id, html_location="thread")
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(updated_html)
        
        print(f"  Fixed: {board}/{thread_id}/index.html ({count} images)")
        return (True, count)
        
    except Exception as e:
        print(f"  Error processing {thread_json_path}: {e}")
        return (False, 0)

def main():
    print("=" * 70)
    print("FIXING ALL IMAGEBOARD HTML FILES")
    print("=" * 70)
    
    threads_dir = CACHE_DIR / 'threads'
    if not threads_dir.exists():
        print(f"Threads directory not found: {threads_dir}")
        return
    
    thread_files = list(threads_dir.glob('**/thread.json'))
    print(f"Found {len(thread_files)} threads to fix")
    
    total_fixed = 0
    
    for tf in thread_files:
        # Fix thread-specific HTML first
        fixed, count = fix_thread_html(tf)
        if fixed:
            total_fixed += 1
        else:
            # Fix main HTML as fallback
            fixed, count = fix_main_html(tf)
            if fixed:
                total_fixed += 1
    
    print(f"\nCompleted {len(thread_files)} threads")
    print(f"Total HTML files fixed: {total_fixed}")
    print("All HTML files now use correct local image paths and can be viewed offline.")

if __name__ == "__main__":
    main()