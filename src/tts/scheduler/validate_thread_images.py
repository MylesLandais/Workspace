import sys
from pathlib import Path
import json

# Container paths
PROJECT_ROOT = Path('/home/jovyan/workspaces')
CACHE_DIR = PROJECT_ROOT / 'cache/imageboard'
THREAD_ID = '944488457'
BOARD = 'b'
THREAD_JSON_PATH = CACHE_DIR / 'threads' / BOARD / THREAD_ID / 'thread.json'
SHARED_IMAGES_DIR = CACHE_DIR / 'shared_images'

def validate_images_from_json():
    if not THREAD_JSON_PATH.exists():
        print(f"ERROR: Thread JSON not found at {THREAD_JSON_PATH}")
        print("Attempting validation based on HTML image count instead...")
        
        # Fallback: count images in HTML file
        HTML_PATH = CACHE_DIR / 'html' / f'{BOARD}_{THREAD_ID}.html'
        if not HTML_PATH.exists():
            print(f"ERROR: HTML not found at {HTML_PATH}")
            return

        with open(HTML_PATH, 'r', encoding='utf-8') as f:
            import re
            content = f.read()
            # Count local image references
            local_refs = len(re.findall(r'shared_images/[0-9]+\.[a-z]+', content))
            
            print(f"Image Validation for b/{THREAD_ID} (Based on HTML)")
            print(f"Total Images Referenced in HTML: {local_refs}")
            
            # Check if sample images exist
            sample_refs = re.findall(r'shared_images/([0-9]+\.[a-z]+)', content)[:5]
            missing_count = 0
            for filename in sample_refs:
                if not (SHARED_IMAGES_DIR / filename).exists():
                    missing_count += 1
            
            if missing_count > 0:
                print(f"STATUS: {missing_count} sample images missing locally. Likely ALL images are missing.")
            else:
                print("STATUS: Sample images present. Assuming full set is available.")
            
        return

    try:
        with open(THREAD_JSON_PATH, 'r') as f:
            thread_data = json.load(f)
    except Exception as e:
        print(f"ERROR: Could not read thread.json: {e}")
        return

    posts = thread_data.get('posts', [])
    
    total_posts_with_files = 0
    missing_images = []
    found_images = []

    for post in posts:
        # Filter out deleted posts or posts without files
        if post.get('file_deleted', False) or post.get('tim', 0) == 0:
            continue
        
        total_posts_with_files += 1
        
        # Construct local filename (e.g., 1766611411524365.jpg)
        ext = post.get('ext', '').split('.')[-1]
        if not ext:
            continue
            
        filename = f"{post['tim']}.{ext}"
        local_path = SHARED_IMAGES_DIR / filename
        
        if local_path.exists():
            found_images.append(filename)
        else:
            missing_images.append(filename)

    print("-" * 50)
    print(f"Image Validation for b/{THREAD_ID} (Based on Thread Data)")
    print(f"Total Posts with Files: {total_posts_with_files}")
    print(f"Total Images Found Locally: {len(found_images)}")
    print(f"Total Missing Images: {len(missing_images)}")
    print("-" * 50)
    
    if missing_images:
        print("MISSING IMAGES (Needs Re-Download):")
        # Limit to 5 missing images for brevity
        for i, filename in enumerate(missing_images[:5]):
            print(f"  {i+1}. {filename}")
        if len(missing_images) > 5:
            print(f"  ... and {len(missing_images) - 5} more.")
        
        print(f"\nACTION REQUIRED: {len(missing_images)} images are missing locally.")
    else:
        print("STATUS: All thread images are present locally.")

if __name__ == "__main__":
    validate_images_from_json()