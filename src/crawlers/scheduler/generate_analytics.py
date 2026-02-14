#!/usr/bin/env python3
"""Generate analytics data for imageboard repost analysis."""
import json
from pathlib import Path
from collections import Counter

def generate_analytics():
    """Generate analytics data for web dashboard."""
    threads_dir = Path('/home/jovyan/workspaces/cache/imageboard/threads')
    shared_images = Path('/home/jovyan/workspaces/cache/imageboard/shared_images')

    # Build image usage data
    image_usage = Counter()
    image_sizes = {}
    image_first_thread = {}

    for board_dir in threads_dir.iterdir():
        if not board_dir.is_dir():
            continue
        
        for thread_dir in board_dir.iterdir():
            if not thread_dir.is_dir():
                continue
            
            thread_json = thread_dir / 'thread.json'
            if not thread_json.exists():
                continue
            
            try:
                with open(thread_json, 'r') as f:
                    data = json.load(f)
                
                posts = data.get('posts', [])
                for post in posts:
                    local_image = post.get('local_image')
                    if local_image and isinstance(local_image, str):
                        image_usage[local_image] += 1
                        
                        # Track first thread
                        if local_image not in image_first_thread:
                            image_first_thread[local_image] = thread_dir.name
                        
                        # Get file size
                        if local_image not in image_sizes:
                            img_path = shared_images / local_image
                            if img_path.exists():
                                image_sizes[local_image] = img_path.stat().st_size
            except Exception:
                pass

    # Get top reposted images
    top_reposted = sorted(image_usage.items(), key=lambda x: x[1], reverse=True)[:100]

    # Generate JSON data
    analytics_data = {
        'total_references': sum(image_usage.values()),
        'unique_images': len(image_usage),
        'duplicates_prevented': sum(image_usage.values()) - len(image_usage),
        'total_storage_gb': sum(image_sizes.values()) / (1024**3),
        'space_saved_gb': sum((count - 1) * image_sizes[img] for img, count in image_usage.items() if count > 1) / (1024**3),
        'top_reposted': [
            {
                'filename': img,
                'count': count,
                'size_bytes': image_sizes.get(img, 0),
                'size_mb': image_sizes.get(img, 0) / (1024**2),
                'first_thread': image_first_thread.get(img, 'unknown'),
                'space_saved_mb': (count - 1) * image_sizes.get(img, 0) / (1024**2)
            }
            for img, count in top_reposted
        ],
        'reuse_distribution': dict(Counter(image_usage.values())),
        'threads_crawled': len(list(threads_dir.rglob('thread.json')))
    }

    return analytics_data

def update_html():
    """Update analytics.html with current data."""
    analytics_data = generate_analytics()
    
    html_path = Path('/home/jovyan/workspaces/analytics.html')
    
    if html_path.exists():
        with open(html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # Replace placeholder with actual data
        html_content = html_content.replace('{{ANALYTICS_DATA}}', json.dumps(analytics_data))
        
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"✓ Updated analytics.html with {len(analytics_data['top_reposted'])} images")
        print(f"  Total references: {analytics_data['total_references']:,}")
        print(f"  Space saved: {analytics_data['space_saved_gb']:.2f} GB")
        return html_path
    else:
        print("✗ analytics.html not found")
        return None

if __name__ == "__main__":
    update_html()
