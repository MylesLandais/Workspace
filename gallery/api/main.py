"""Gallery API for viewing catalogues and cached HTML."""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from pathlib import Path
import json
from datetime import datetime

from feed.repositories.cached_post_repository import CachedPostRepository
from feed.storage.neo4j_connection import get_connection
from feed.storage.cache_adapter import CacheAdapter


app = FastAPI(title="Gallery API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class GalleryService:
    """Service for gallery operations."""
    
    def __init__(self):
        self.repo = CachedPostRepository(
            neo4j=get_connection(),
            cache=CacheAdapter()
        )
        self.cache_dir = Path.home() / ".cache" / "gallery" / "html"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    async def get_catalogue(
        self,
        source: str,
        limit: int = 50,
        offset: int = 0,
        sort: str = "new"
    ) -> List[dict]:
        """Get catalogue entries from source."""
        if sort == "new":
            posts = await self.repo.get_posts_by_subreddit(
                source,
                limit=limit,
                offset=offset
            )
        elif sort == "top":
            posts = await self.repo.get_posts_by_subreddit(
                source,
                limit=limit,
                offset=offset
            )
            posts.sort(key=lambda p: p.score, reverse=True)
        else:
            posts = await self.repo.get_posts_by_subreddit(
                source,
                limit=limit,
                offset=offset
            )
        
        return [
            {
                "id": post.id,
                "title": post.title,
                "url": post.url,
                "score": post.score,
                "num_comments": post.num_comments,
                "upvote_ratio": post.upvote_ratio,
                "over_18": post.over_18,
                "selftext": post.selftext,
                "author": post.author,
                "subreddit": post.subreddit,
                "created_utc": post.created_utc.isoformat() if post.created_utc else None,
                "thumbnail": self._get_thumbnail(post.id),
                "cached": self._is_html_cached(post.id)
            }
            for post in posts
        ]
    
    def _get_thumbnail(self, post_id: str) -> Optional[str]:
        """Get thumbnail path for post."""
        thumb_path = self.cache_dir / "thumbnails" / f"{post_id}.jpg"
        if thumb_path.exists():
            return f"/gallery/thumbnails/{post_id}.jpg"
        return None
    
    def _is_html_cached(self, post_id: str) -> bool:
        """Check if HTML is cached for post."""
        html_path = self.cache_dir / f"{post_id}.html"
        return html_path.exists()
    
    def get_cached_html(self, post_id: str) -> Optional[str]:
        """Get cached HTML for post."""
        html_path = self.cache_dir / f"{post_id}.html"
        if html_path.exists():
            return html_path.read_text()
        return None
    
    def get_sources(self) -> List[str]:
        """Get available sources (subreddits/channels)."""
        with get_connection().get_session() as session:
            result = session.run("""
                MATCH (s:Subreddit)
                RETURN s.name as name, count((s)<-[:IN_SUBREDDIT]-(:Post)) as count
                ORDER BY count DESC
            """)
            return [
                {"name": record["name"], "count": record["count"]}
                for record in result.records()
            ]
    
    async def search(self, query: str, limit: int = 50) -> List[dict]:
        """Search posts."""
        with get_connection().get_session() as session:
            result = session.run("""
                MATCH (p:Post)
                WHERE p.title CONTAINS $query OR p.selftext CONTAINS $query
                RETURN p
                ORDER BY p.score DESC
                LIMIT $limit
            """, {"query": query, "limit": limit})
            
            posts = []
            for record in result.records():
                post_data = dict(record["p"])
                post_data["thumbnail"] = self._get_thumbnail(post_data.get("id"))
                post_data["cached"] = self._is_html_cached(post_data.get("id"))
                posts.append(post_data)
            
            return posts


gallery_service = GalleryService()


@app.get("/api/catalogue/{source}")
async def get_catalogue(
    source: str,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    sort: str = Query("new", regex="^(new|top|controversial)$")
) -> JSONResponse:
    """Get catalogue entries from source."""
    entries = await gallery_service.get_catalogue(source, limit, offset, sort)
    return JSONResponse({
        "source": source,
        "entries": entries,
        "count": len(entries)
    })


@app.get("/api/sources")
async def get_sources() -> JSONResponse:
    """Get available sources."""
    sources = gallery_service.get_sources()
    return JSONResponse({"sources": sources})


@app.get("/api/search")
async def search(
    query: str = Query(..., min_length=1),
    limit: int = Query(50, ge=1, le=200)
) -> JSONResponse:
    """Search posts."""
    results = await gallery_service.search(query, limit)
    return JSONResponse({
        "query": query,
        "results": results,
        "count": len(results)
    })


@app.get("/view/{post_id}")
async def view_post(post_id: str) -> HTMLResponse:
    """View cached HTML for post."""
    html = gallery_service.get_cached_html(post_id)
    if not html:
        raise HTTPException(status_code=404, detail="HTML not cached")
    return HTMLResponse(content=html)


@app.get("/api/post/{post_id}")
async def get_post(post_id: str) -> JSONResponse:
    """Get post metadata."""
    post = await gallery_service.repo.get_post(post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    return JSONResponse({
        "post": {
            "id": post.id,
            "title": post.title,
            "url": post.url,
            "score": post.score,
            "num_comments": post.num_comments,
            "upvote_ratio": post.upvote_ratio,
            "over_18": post.over_18,
            "selftext": post.selftext,
            "author": post.author,
            "subreddit": post.subreddit,
            "created_utc": post.created_utc.isoformat() if post.created_utc else None,
            "thumbnail": gallery_service._get_thumbnail(post.id),
            "cached": gallery_service._is_html_cached(post.id)
        }
    })


@app.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint."""
    return JSONResponse({"status": "healthy"})


# Mount static files for thumbnails and assets
thumb_dir = Path.home() / ".cache" / "gallery" / "thumbnails"
thumb_dir.mkdir(parents=True, exist_ok=True)
app.mount("/gallery/thumbnails", StaticFiles(directory=str(thumb_dir)), name="thumbnails")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
