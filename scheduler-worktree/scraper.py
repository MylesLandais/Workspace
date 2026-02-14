import requests
import json
import os
import mimetypes
from datetime import datetime
from urllib.parse import urlparse

# --- Configuration ---
SUBREDDITS = [
    'unixporn', 
    'MechanicalKeyboards', 
    'linux', 
    'battlestations',
    'taylorswiftpictures'
]
POST_LIMIT = 50
DATA_DIR = 'data'
MEDIA_DIR = os.path.join(DATA_DIR, 'media')
USER_AGENT = "A-Simple-Linux-Scraper-v1.0" 

def is_media_url(url):
    """Simple check to see if a URL is likely a media file."""
    if url.endswith(('.jpg', '.jpeg', '.png', '.gif', '.mp4', '.webm')):
        return True
    
    # Common direct image hosts
    domain = urlparse(url).netloc
    if domain in ('i.redd.it', 'v.redd.it'):
        return True
        
    return False

def download_media(post_id, url):
    """Downloads media from the given URL and returns the local file path."""
    if not is_media_url(url):
        return None

    if not os.path.exists(MEDIA_DIR):
        os.makedirs(MEDIA_DIR)

    headers = {'User-Agent': USER_AGENT}
    
    # Try to determine file extension from URL
    ext = os.path.splitext(urlparse(url).path)[1]
    if not ext:
        # Fallback for v.redd.it or other tricky URLs, we'll try to get it from headers later
        if 'v.redd.it' in url:
            ext = '.mp4' # Assume video
        else:
            ext = '.jpg' # Assume image

    local_filename = os.path.join(MEDIA_DIR, f"{post_id}{ext}")

    print(f"  Downloading media from {url}...")
    try:
        response = requests.get(url, headers=headers, stream=True, timeout=20)
        response.raise_for_status()

        # Final check for content type if extension was guessed
        if ext == '.jpg' or ext == '.mp4':
            content_type = response.headers.get('Content-Type', '')
            if content_type:
                guessed_ext = mimetypes.guess_extension(content_type)
                if guessed_ext:
                    local_filename = os.path.join(MEDIA_DIR, f"{post_id}{guessed_ext}")

        with open(local_filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        print(f"  Saved media to {local_filename}")
        # Return path relative to project root
        return os.path.relpath(local_filename, DATA_DIR) 

    except requests.exceptions.RequestException as e:
        print(f"  Error downloading media for post {post_id}: {e}")
        return None

def fetch_subreddit_data(subreddit_name, limit):
    """Fetches top posts from a subreddit's JSON endpoint."""
    url = f"https://www.reddit.com/r/{subreddit_name}/top.json"
    headers = {'User-Agent': USER_AGENT}
    params = {'t': 'month', 'limit': limit} 
    
    print(f"Fetching {limit} top posts from r/{subreddit_name}...")
    
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        posts_data = []
        for child in data['data']['children']:
            post = child['data']
            
            # 1. Download media if available
            local_media_path = download_media(post['id'], post['url'])

            # 2. Append metadata
            metadata = {
                'id': post['id'],
                'title': post['title'],
                'subreddit': post['subreddit_name_prefixed'],
                'url': post['url'],
                'permalink': f"https://www.reddit.com{post['permalink']}",
                'score': post['score'],
                'num_comments': post['num_comments'],
                'created_utc': datetime.fromtimestamp(post['created_utc']).isoformat(),
                'selftext': post.get('selftext', ''),
                'local_media_path': local_media_path # New field
            }
            posts_data.append(metadata)
            
        return posts_data
    
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for r/{subreddit_name}: {e}")
        return []

def scrape_data():
    """Scrapes posts from configured subreddits and saves them to JSON files."""
    
    if not os.path.exists(DATA_DIR):
        print(f"Creating data directory: {DATA_DIR}")
        os.makedirs(DATA_DIR)

    for subreddit_name in SUBREDDITS:
        posts = fetch_subreddit_data(subreddit_name, POST_LIMIT)
        
        if not posts:
            continue

        # Save data to a JSON file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(DATA_DIR, f"{subreddit_name}_{timestamp}.json")
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(posts, f, ensure_ascii=False, indent=4)
        
        print(f"Successfully saved {len(posts)} posts and media links to {filename}")

if __name__ == "__main__":
    scrape_data()
