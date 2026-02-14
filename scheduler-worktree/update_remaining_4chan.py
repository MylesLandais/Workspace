#!/usr/bin/env python3
"""Update remaining 4chan references while preserving URLs."""

import re
from pathlib import Path

def update_file(filepath):
    """Update file with 4chan -> imageboard, preserving URLs."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Preserve URLs: boards.4chan.org and i.4cdn.org
    # Replace 4chan with imageboard in comments/docs
    
    # Replace class names (FourChan -> Imageboard)
    content = re.sub(r'\bFourChan\b', 'Imageboard', content)
    
    # Replace function names (poll_4chan -> poll_imageboard)
    content = re.sub(r'\bpoll_4chan\b', 'poll_imageboard', content)
    
    # Replace in comments/docs (4chan -> imageboard)
    # But preserve URLs like boards.4chan.org and i.4cdn.org
    content = re.sub(r'\b4chan\b(?!\.org|\.cdn)', 'imageboard', content)
    
    # Replace 4CHAN -> IMAGEBOARD
    content = re.sub(r'\b4CHAN\b', 'IMAGEBOARD', content)
    
    # Replace in cache paths (cache/4chan -> cache/imageboard)
    content = re.sub(r'cache/4chan', 'cache/imageboard', content)
    
    # Replace in user-agent strings (4chan-archiver -> imageboard-archiver)
    content = re.sub(r'4chan-archiver', 'imageboard-archiver', content)
    
    # Replace function name in comments
    content = re.sub(r'search_4chan_api', 'search_imageboard_api', content)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Updated: {filepath}")
        return True
    return False

def main():
    """Process files."""
    files_to_update = [
        "src/feed/graphql/chan_schema.py",
        "check_monitor_status.py",
        "check_thread_location.py",
        "download_all_jj_images.py",
        "download_all_thread_images.py",
        "check_thread_images.py",
        "diagnose_monitor.py",
        "organize_imageboard_images.py",
    ]
    
    updated_count = 0
    for filepath in files_to_update:
        if Path(filepath).exists():
            if update_file(filepath):
                updated_count += 1
    
    print(f"\nTotal files updated: {updated_count}")

if __name__ == "__main__":
    main()
