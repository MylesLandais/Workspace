#!/usr/bin/env python3
"""
Creates a comprehensive 'Full' dataset pack including legacy and new data.
Consolidates all images into a single deduplicated library.
"""
import os
import shutil
import tarfile
import json
import pandas as pd
import pyarrow as pa
from pyarrow.parquet import write_table
from pathlib import Path
from datetime import datetime
import hashlib

# Source Paths
CACHE_ROOT = Path('/home/warby/Workspace/jupyter/cache/imageboard')
NEW_THREADS_DIR = CACHE_ROOT / 'threads'
NEW_IMAGES_DIR = CACHE_ROOT / 'shared_images'
LEGACY_BOARD_DIR = CACHE_ROOT / 'b'
LEGACY_IMAGES_B_DIR = CACHE_ROOT / 'images' / 'b'

# Export/Pack Paths
PACK_BASE_DIR = Path('/home/warby/Workspace/jupyter/packs')
TIMESTAMP = datetime.now().strftime('%Y%m%d')
PACK_NAME = f"imageboard_full_archive_{TIMESTAMP}"
PACK_DIR = PACK_BASE_DIR / PACK_NAME
PACK_IMAGES_DIR = PACK_DIR / 'images'

def get_file_sha256(file_path):
    hasher = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def create_full_pack():
    print(f"Creating Comprehensive Archive: {PACK_NAME}")
    
    if PACK_DIR.exists():
        shutil.rmtree(PACK_DIR)
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    PACK_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    
    all_posts = []
    
    # --- 1. Process NEW Data ---
    print("Processing new monitored data...")
    if NEW_THREADS_DIR.exists():
        thread_files = list(NEW_THREADS_DIR.glob('**/thread.json'))
        for thread_file in thread_files:
            try:
                with open(thread_file, 'r') as f:
                    data = json.load(f)
                board = thread_file.parent.parent.name
                thread_id = thread_file.parent.name
                for post in data.get('posts', []):
                    local_img = post.get('local_image')
                    if local_img:
                        src_path = NEW_IMAGES_DIR / local_img
                        if src_path.exists():
                            shutil.copy2(src_path, PACK_IMAGES_DIR / local_img)
                    
                    all_posts.append({
                        'source': 'new_monitor',
                        'board': board,
                        'thread_id': thread_id,
                        'post_no': post.get('no'),
                        'timestamp': post.get('time'),
                        'subject': post.get('sub', ''),
                        'comment': post.get('com', ''),
                        'image_rel_path': f"images/{local_img}" if local_img else None,
                        'image_sha256': local_img.split('.')[0] if local_img else None,
                        'moderated': post.get('moderated', False)
                    })
            except Exception as e:
                print(f"Error processing new thread {thread_file}: {e}")

    # --- 2. Process LEGACY Data (images/b) ---
    print("Processing legacy image data (this may take a while)...")
    if LEGACY_IMAGES_B_DIR.exists():
        legacy_threads = [d for d in LEGACY_IMAGES_B_DIR.iterdir() if d.is_dir()]
        for thread_dir in legacy_threads:
            thread_id = thread_dir.name
            # Look for a monitor.json in the other legacy location or here
            subject = "Legacy Thread"
            mon_path = LEGACY_BOARD_DIR / thread_id / 'monitor.json'
            if mon_path.exists():
                try:
                    with open(mon_path, 'r') as f:
                        mon_data = json.load(f)
                        subject = mon_data.get('subject', subject)
                except: pass
                
            for img_path in thread_dir.glob('*'):
                if img_path.is_file() and img_path.suffix.lower() in ['.jpg', '.png', '.gif', '.webm']:
                    # Use existing filename if it looks like a hash, or compute it
                    fname = img_path.name
                    if len(fname.split('.')[0]) != 64:
                        sha = get_file_sha256(img_path)
                        fname = f"{sha}{img_path.suffix}"
                    
                    dest_path = PACK_IMAGES_DIR / fname
                    if not dest_path.exists():
                        shutil.copy2(img_path, dest_path)
                    
                    all_posts.append({
                        'source': 'legacy',
                        'board': 'b',
                        'thread_id': thread_id,
                        'post_no': None,
                        'timestamp': int(img_path.stat().st_mtime),
                        'subject': subject,
                        'comment': None,
                        'image_rel_path': f"images/{fname}",
                        'image_sha256': fname.split('.')[0],
                        'moderated': False
                    })

    # --- 3. Save Unified Parquet ---
    print(f"Saving unified index with {len(all_posts)} entries...")
    df = pd.DataFrame(all_posts)
    write_table(pa.Table.from_pandas(df), PACK_DIR / "dataset_index.parquet")
    
    # --- 4. Archive ---
    print(f"Compressing into {PACK_NAME}.tar.gz...")
    archive_path = PACK_BASE_DIR / f"{PACK_NAME}.tar.gz"
    # Using a system call for tar to handle large directories more efficiently and show progress if needed
    os.system(f"tar -czf {archive_path} -C {PACK_BASE_DIR} {PACK_NAME}")
    
    print("=" * 70)
    print("COMPREHENSIVE PACK COMPLETE")
    print(f"Location: {archive_path}")
    print(f"Final Size: {os.path.getsize(archive_path) / (1024*1024):.1f} MB")
    print("=" * 70)

if __name__ == "__main__":
    create_full_pack()
