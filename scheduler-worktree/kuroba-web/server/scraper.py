import os
import requests
import hashlib
from bs4 import BeautifulSoup
from sqlalchemy.orm import Session
from models import Thread, Post
from datetime import datetime

IMAGES_DIR = "/app/static/images"

def download_image(url: str) -> str | None:
    """Downloads image and returns the local filename."""
    if not url:
        return None
    
    try:
        # Determine filename from hash or original filename
        # 4chan images are usually: timestamp.ext
        filename = url.split('/')[-1]
        local_path = os.path.join(IMAGES_DIR, filename)
        
        if os.path.exists(local_path):
            return filename
            
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            with open(local_path, 'wb') as f:
                f.write(response.content)
            return filename
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return None
    return None

def process_thread(db: Session, board: str, thread_id: int):
    url = f"https://a.4cdn.org/{board}/thread/{thread_id}.json"
    print(f"Fetching {url}...")
    
    try:
        resp = requests.get(url, timeout=30)
        if resp.status_code != 200:
            print(f"Failed to fetch thread: {resp.status_code}")
            return False
            
        data = resp.json()
        posts = data.get('posts', [])
        
        # 1. Get or Create Thread
        thread = db.query(Thread).filter(Thread.board == board, Thread.thread_id == thread_id).first()
        if not thread:
            # First post determines title
            op = posts[0]
            title = op.get('sub') or op.get('com', '')[:50]
            # Remove HTML from title if present
            title = BeautifulSoup(title, "html.parser").get_text()
            
            thread = Thread(board=board, thread_id=thread_id, title=title)
            db.add(thread)
            db.commit()
            db.refresh(thread)
        
        # 2. Process Posts
        for p in posts:
            post_no = p.get('no')
            
            # Check if post exists
            existing_post = db.query(Post).filter(Post.thread_db_id == thread.id, Post.post_no == post_no).first()
            if existing_post:
                continue
                
            # Handle Image
            local_image = None
            orig_image_url = None
            if 'tim' in p and 'ext' in p:
                # 4chan image url: https://i.4cdn.org/{board}/{tim}{ext}
                orig_image_url = f"https://i.4cdn.org/{board}/{p['tim']}{p['ext']}"
                local_image = download_image(orig_image_url)
            
            # Rewrite HTML
            comment_html = p.get('com', '')
            if comment_html:
                soup = BeautifulSoup(comment_html, 'html.parser')
                
                # Rewrite cross-thread links (>>>12345) to local links
                # (Simple version: just ensure they don't break. 
                # Ideally, point to /thread/ID#p12345)
                for a in soup.find_all('a'):
                    href = a.get('href')
                    if href and 'quotelink' in a.get('class', []):
                        # It's a quote like #p12345678
                        pass 
                
                comment_html = str(soup)
                
            new_post = Post(
                thread_db_id=thread.id,
                post_no=post_no,
                subject=p.get('sub'),
                comment=comment_html,
                original_image_url=orig_image_url,
                local_image_filename=local_image,
                created_at=datetime.utcfromtimestamp(p.get('time', 0))
            )
            db.add(new_post)
            
        thread.post_count = len(posts)
        thread.last_modified = datetime.utcnow()
        db.commit()
        return True
        
    except Exception as e:
        print(f"Error processing thread: {e}")
        return False
