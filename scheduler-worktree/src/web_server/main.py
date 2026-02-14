import os
import json
import redis
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from bs4 import BeautifulSoup
from collections import Counter

app = FastAPI(title="Kuroba Web BFF")

# Configuration
REDIS_URL = os.environ.get("REDIS_URL", "redis://redis:6379")
CACHE_DIR = Path(os.environ.get("CACHE_DIR", "/home/warby/Workspace/jupyter/cache/imageboard"))
THREADS_DIR = CACHE_DIR / "threads"
IMAGES_DIR = CACHE_DIR / "shared_images"
ANALYTICS_HTML = Path("/home/jovyan/workspaces/analytics.html")

# Redis
r = redis.from_url(REDIS_URL)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve Static Images
# The worker saves images to CACHE_DIR/shared_images
# We mount this at /static/images
app.mount("/static/images", StaticFiles(directory=str(IMAGES_DIR)), name="images")

class TrackRequest(BaseModel):
    board: str
    thread_id: int
    subject: str = "Manual Track"

def rewrite_post_html(html_content: str, board: str) -> str:
    if not html_content:
        return ""
    
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Rewrite links
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Handle cross-references (>>>12345)
        if href.startswith(">>>"):
            # Leave as text or make internal link
            pass
        elif href.startswith("//"):
             a["href"] = "https:" + href
    
    return str(soup)

def inject_local_images(posts: list, board: str):
    """
    Update post objects to include local image URLs if they exist.
    """
    for post in posts:
        # Check if worker processed this image
        if 'tim' in post:
            # The worker logic (from imageboard_monitor_worker.py) uses SHA256 dedupe
            # We need to know the mapping. 
            # The worker saves 'local_image' into the post object in memory, 
            # but let's check if it saved it to thread.json.
            # Looking at worker code: 
            # post['local_image'] = img_file (line 228)
            # json.dump(thread_data, f) (line 236)
            # YES! thread.json has the 'local_image' field.
            
            if 'local_image' in post:
                post['local_image_url'] = f"/static/images/{post['local_image']}"
                
        # Rewrite HTML content
        if 'com' in post:
             post['com'] = rewrite_post_html(post['com'], board)

@app.post("/api/track")
async def track_thread(req: TrackRequest):
    job = {
        "board": req.board,
        "thread_id": req.thread_id,
        "subject": req.subject
    }
    r.rpush("queue:monitors", json.dumps(job))
    return {"status": "queued", "job": job}

@app.get("/api/threads")
async def list_threads():
    """List all tracked threads from the filesystem."""
    results = []
    if not THREADS_DIR.exists():
        return []
        
    for board_dir in THREADS_DIR.iterdir():
        if not board_dir.is_dir():
            continue
        for thread_dir in board_dir.iterdir():
            json_path = thread_dir / "thread.json"
            if json_path.exists():
                try:
                    data = json.loads(json_path.read_text())
                    post_count = len(data.get("posts", []))
                    op = data.get("posts", [])[0] if data.get("posts") else {}
                    results.append({
                        "board": board_dir.name,
                        "thread_id": thread_dir.name,
                        "subject": op.get("sub") or op.get("com", "")[:50],
                        "post_count": post_count,
                        "last_modified": os.path.getmtime(json_path)
                    })
                except Exception as e:
                    print(f"Error reading {json_path}: {e}")
    
    # Sort by last modified
    results.sort(key=lambda x: x["last_modified"], reverse=True)
    return results

@app.get("/api/thread/{board}/{thread_id}")
async def get_thread(board: str, thread_id: int):
    json_path = THREADS_DIR / board / str(thread_id) / "thread.json"
    
    if not json_path.exists():
        raise HTTPException(status_code=404, detail="Thread not found locally. Please track it first.")
    
    try:
        data = json.loads(json_path.read_text())
        inject_local_images(data.get("posts", []), board)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics", response_class=HTMLResponse)
async def get_analytics():
    """Serve analytics dashboard."""
    if not ANALYTICS_HTML.exists():
        raise HTTPException(status_code=404, detail="Analytics page not found. Run generate_analytics.py first.")
    
    return ANALYTICS_HTML.read_text()

@app.get("/api/analytics/data")
async def get_analytics_data():
    """Generate and return analytics data as JSON."""
    image_usage = Counter()
    image_sizes = {}
    image_first_thread = {}

    for board_dir in THREADS_DIR.iterdir():
        if not board_dir.is_dir():
            continue
        
        for thread_dir in board_dir.iterdir():
            if not thread_dir.is_dir():
                continue
            
            thread_json = thread_dir / "thread.json"
            if not thread_json.exists():
                continue
            
            try:
                data = json.loads(thread_json.read_text())
                posts = data.get("posts", [])
                
                for post in posts:
                    local_image = post.get("local_image")
                    if local_image and isinstance(local_image, str):
                        image_usage[local_image] += 1
                        
                        if local_image not in image_first_thread:
                            image_first_thread[local_image] = thread_dir.name
                        
                        if local_image not in image_sizes:
                            img_path = IMAGES_DIR / local_image
                            if img_path.exists():
                                image_sizes[local_image] = img_path.stat().st_size
            except Exception:
                pass

    top_reposted = sorted(image_usage.items(), key=lambda x: x[1], reverse=True)[:100]

    return {
        "total_references": sum(image_usage.values()),
        "unique_images": len(image_usage),
        "duplicates_prevented": sum(image_usage.values()) - len(image_usage),
        "total_storage_gb": sum(image_sizes.values()) / (1024**3),
        "space_saved_gb": sum((count - 1) * image_sizes[img] for img, count in image_usage.items() if count > 1) / (1024**3),
        "top_reposted": [
            {
                "filename": img,
                "count": count,
                "size_bytes": image_sizes.get(img, 0),
                "size_mb": image_sizes.get(img, 0) / (1024**2),
                "first_thread": image_first_thread.get(img, "unknown"),
                "space_saved_mb": (count - 1) * image_sizes.get(img, 0) / (1024**2)
            }
            for img, count in top_reposted
        ],
        "reuse_distribution": dict(Counter(image_usage.values())),
        "threads_crawled": len(list(THREADS_DIR.rglob("thread.json")))
    }

