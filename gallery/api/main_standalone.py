"""Simple gallery server with standalone mode."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gallery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
CACHE_DIR = Path.home() / ".cache" / "gallery" / "html"
THUMBNAIL_DIR = Path.home() / ".cache" / "gallery" / "thumbnails"
DATA_DIR = Path.home() / ".cache" / "gallery" / "data"

for dir_path in [CACHE_DIR, THUMBNAIL_DIR, DATA_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# Create sample data if not exists
SAMPLE_DATA_FILE = DATA_DIR / "catalogue.json"


def create_sample_data():
    """Create sample catalogue data."""
    sample_data = {
        "sources": [
            {"name": "python", "count": 150},
            {"name": "programming", "count": 89},
            {"name": "webdev", "count": 67},
        ],
        "posts": [
            {
                "id": "sample1",
                "title": "Welcome to Gallery - Sample Post",
                "url": "https://example.com/sample1",
                "score": 100,
                "num_comments": 25,
                "upvote_ratio": 0.95,
                "over_18": False,
                "selftext": "This is a sample post to demonstrate the gallery interface.",
                "author": "gallery_admin",
                "subreddit": "python",
                "created_utc": "2024-01-01T00:00:00Z",
                "thumbnail": None,
                "cached": False
            },
            {
                "id": "sample2",
                "title": "How to Use This Gallery Interface",
                "url": "https://example.com/sample2",
                "score": 75,
                "num_comments": 12,
                "upvote_ratio": 0.90,
                "over_18": False,
                "selftext": "Browse catalogues, search for content, and view cached HTML with custom styling.",
                "author": "gallery_admin",
                "subreddit": "python",
                "created_utc": "2024-01-02T00:00:00Z",
                "thumbnail": None,
                "cached": True
            }
        ]
    }
    
    SAMPLE_DATA_FILE.write_text(json.dumps(sample_data, indent=2))
    return sample_data


def load_data():
    """Load catalogue data."""
    if SAMPLE_DATA_FILE.exists():
        try:
            with open(SAMPLE_DATA_FILE) as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading data: {e}")
            return create_sample_data()
    return create_sample_data()


@app.get("/")
async def root():
    """Serve main HTML page."""
    html_path = Path(__file__).parent.parent / "templates" / "index.html"
    if html_path.exists():
        return FileResponse(html_path)
    return HTMLResponse(content="<h1>Gallery Interface</h1><p>Templates not found. Run setup.py first.</p>")


@app.get("/gallery/styles/main.css")
async def get_stylesheet():
    """Serve CSS file."""
    css_path = Path(__file__).parent.parent / "styles" / "main.css"
    if css_path.exists():
        return FileResponse(css_path, media_type="text/css")
    return HTMLResponse(content="/* CSS not found */", media_type="text/css")


@app.get("/gallery/scripts/main.js")
async def get_script():
    """Serve JavaScript file."""
    js_path = Path(__file__).parent.parent / "frontend" / "scripts" / "main.js"
    if js_path.exists():
        return FileResponse(js_path, media_type="application/javascript")
    return HTMLResponse(content="// JS not found", media_type="application/javascript")


@app.get("/api/sources")
async def get_sources() -> JSONResponse:
    """Get available sources."""
    try:
        data = load_data()
        return JSONResponse({"sources": data["sources"]})
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        return JSONResponse({"sources": []}, status_code=500)


@app.get("/api/catalogue/{source}")
async def get_catalogue(
    source: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: str = Query("new", regex="^(new|top|controversial)$")
) -> JSONResponse:
    """Get catalogue entries from source."""
    try:
        data = load_data()
        
        posts = data.get("posts", [])
        
        if source != "all":
            posts = [p for p in posts if p.get("subreddit") == source]
        
        if sort == "top":
            posts = sorted(posts, key=lambda x: x.get("score", 0), reverse=True)
        elif sort == "new":
            posts = sorted(posts, key=lambda x: x.get("created_utc", ""), reverse=True)
        
        start = offset
        end = start + limit
        posts = posts[start:end]
        
        return JSONResponse({
            "source": source,
            "entries": posts,
            "count": len(posts)
        })
    except Exception as e:
        logger.error(f"Error getting catalogue: {e}")
        return JSONResponse(
            {"source": source, "entries": [], "count": 0, "error": str(e)},
            status_code=500
        )


@app.get("/api/search")
async def search(
    query: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200)
) -> JSONResponse:
    """Search posts."""
    try:
        data = load_data()
        posts = data.get("posts", [])
        
        query_lower = query.lower()
        results = [
            p for p in posts
            if query_lower in p.get("title", "").lower() or
               query_lower in p.get("selftext", "").lower()
        ]
        
        results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
        results = results[:limit]
        
        return JSONResponse({
            "query": query,
            "results": results,
            "count": len(results)
        })
    except Exception as e:
        logger.error(f"Error searching: {e}")
        return JSONResponse(
            {"query": query, "results": [], "count": 0, "error": str(e)},
            status_code=500
        )


@app.get("/api/post/{post_id}")
async def get_post(post_id: str) -> JSONResponse:
    """Get post metadata."""
    try:
        data = load_data()
        posts = data.get("posts", [])
        
        post = next((p for p in posts if p.get("id") == post_id), None)
        
        if not post:
            return JSONResponse(
                {"error": "Post not found"},
                status_code=404
            )
        
        return JSONResponse({"post": post})
    except Exception as e:
        logger.error(f"Error getting post: {e}")
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


@app.get("/view/{post_id}")
async def view_post(post_id: str) -> HTMLResponse:
    """View cached HTML for post."""
    try:
        html_path = CACHE_DIR / f"{post_id}.html"
        
        if not html_path.exists():
            raise HTTPException(status_code=404, detail="HTML not cached")
        
        html = html_path.read_text(encoding='utf-8')
        return HTMLResponse(content=html)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing post: {e}")
        return HTMLResponse(
            content=f"<h1>Error</h1><p>Failed to load post: {e}</p>",
            status_code=500
        )


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({
        "status": "healthy",
        "cache_dir": str(CACHE_DIR),
        "thumbnail_dir": str(THUMBNAIL_DIR),
        "sample_data": SAMPLE_DATA_FILE.exists()
    })


# Mount thumbnail directory if it exists
if THUMBNAIL_DIR.exists():
    try:
        app.mount("/gallery/thumbnails", StaticFiles(directory=str(THUMBNAIL_DIR)), name="thumbnails")
        logger.info(f"Mounted thumbnails at /gallery/thumbnails from {THUMBNAIL_DIR}")
    except Exception as e:
        logger.warning(f"Could not mount thumbnails: {e}")


if __name__ == "__main__":
    import uvicorn
    
    # Create sample data
    create_sample_data()
    
    logger.info("Starting Gallery API...")
    logger.info(f"Cache directory: {CACHE_DIR}")
    logger.info(f"Thumbnail directory: {THUMBNAIL_DIR}")
    logger.info(f"Data directory: {DATA_DIR}")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )
