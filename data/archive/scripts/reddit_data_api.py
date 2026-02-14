"""Simple FastAPI server for Reddit data using Python 3 syntax."""

import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

from feed.storage.neo4j_connection import get_connection
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# Create FastAPI app
app = FastAPI(
    title="Reddit Data API",
    description="Simple REST API for crawled Reddit data from Neo4j",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class RedditPost(BaseModel):
    id: str
    title: str
    created_utc: str
    score: int
    num_comments: int
    upvote_ratio: float
    over_18: bool
    url: str
    selftext: str
    permalink: str
    subreddit: str
    author: Optional[str] = None
    is_image: bool = False
    image_url: Optional[str] = None


class SubredditInfo(BaseModel):
    name: str
    post_count: int


class Comment(BaseModel):
    id: str
    body: str
    author: Optional[str] = None
    score: int
    depth: int
    is_submitter: bool
    created_utc: str
    link_id: str


class Image(BaseModel):
    url: str
    image_path: Optional[str] = None


class PostWithDetails(BaseModel):
    post: RedditPost
    comments: List[Comment] = []
    images: List[Image] = []


def get_neo4j_connection():
    try:
        return get_connection()
    except Exception as e:
        print(f"Error connecting to Neo4j: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection error: {e}")


@app.get("/")
def root():
    return {
        "message": "Reddit Data API",
        "version": "1.0.0",
        "endpoints": {
            "/subreddits": "List all subreddits",
            "/posts": "Get posts",
            "/subreddit/{name}/posts": "Get posts for specific subreddit",
            "/post/{id}": "Get single post",
            "/stats": "Get statistics",
        }
    }


@app.get("/subreddits", response_model=List[SubredditInfo])
def get_subreddits():
    neo4j = get_neo4j_connection()
    
    query = """
    MATCH (s:Subreddit)
    OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
    RETURN s.name as name, count(p) as post_count
    ORDER BY post_count DESC
    """
    
    try:
        result = neo4j.execute_read(query)
        return [
            SubredditInfo(name=record["name"], post_count=record["post_count"])
            for record in result
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/posts", response_model=List[RedditPost])
def get_posts(subreddit: Optional[str] = None, min_score: Optional[int] = None, is_image: Optional[bool] = None, limit: int = 20, offset: int = 0):
    neo4j = get_neo4j_connection()
    
    where_clauses = []
    params = {"limit": limit, "offset": offset}
    
    if subreddit:
        where_clauses.append("s.name = $subreddit")
        params["subreddit"] = subreddit
    
    if min_score is not None:
        where_clauses.append("p.score >= $min_score")
        params["min_score"] = min_score
    
    if is_image is not None:
        if is_image:
            where_clauses.append("(p.url CONTAINS 'i.redd.it' OR p.url CONTAINS 'reddit.com/gallery')")
        else:
            where_clauses.append("NOT (p.url CONTAINS 'i.redd.it' OR p.url CONTAINS 'reddit.com/gallery')")
    
    where_clause = " AND ".join(where_clauses) if where_clauses else "1=1"
    
    query = f"""
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    OPTIONAL MATCH (u:User)-[:POSTED]->(p)
    WHERE {where_clause}
    RETURN p.id as id, p.title as title, toString(p.created_utc) as created_utc,
           p.score as score, p.num_comments as num_comments, p.upvote_ratio as upvote_ratio,
           p.over_18 as over_18, p.url as url, p.selftext as selftext, p.permalink as permalink,
           s.name as subreddit, u.username as author
    SKIP $offset
    LIMIT $limit
    """
    
    try:
        result = neo4j.execute_read(query, parameters=params)
        posts = []
        for record in result:
            is_image = "i.redd.it" in record.get("url", "").lower() or "reddit.com/gallery" in record.get("url", "").lower()
            posts.append(RedditPost(
                id=record["id"],
                title=record["title"],
                created_utc=record["created_utc"],
                score=record["score"],
                num_comments=record["num_comments"],
                upvote_ratio=record["upvote_ratio"],
                over_18=record["over_18"],
                url=record["url"],
                selftext=record.get("selftext", ""),
                permalink=record["permalink"],
                subreddit=record["subreddit"],
                author=record.get("author"),
                is_image=is_image,
                image_url=record["url"] if is_image else None,
            ))
        return posts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/subreddit/{name}/posts", response_model=List[RedditPost])
def get_subreddit_posts(name: str, limit: int = 20):
    return get_posts(subreddit=name, limit=limit)


@app.get("/post/{id}", response_model=PostWithDetails)
def get_post_details(id: str):
    neo4j = get_neo4j_connection()
    
    # Get post
    post_query = """
    MATCH (p:Post {id: $id})-[:POSTED_IN]->(s:Subreddit)
    OPTIONAL MATCH (u:User)-[:POSTED]->(p)
    RETURN p.id as id, p.title as title, toString(p.created_utc) as created_utc,
           p.score as score, p.num_comments as num_comments, p.upvote_ratio as upvote_ratio,
           p.over_18 as over_18, p.url as url, p.selftext as selftext, p.permalink as permalink,
           s.name as subreddit, u.username as author
    """
    
    try:
        post_result = neo4j.execute_read(post_query, parameters={"id": id})
        if not post_result:
            raise HTTPException(status_code=404, detail="Post not found")
        
        post_data = post_result[0]
        
        # Determine if image post
        is_image_post = (
            "i.redd.it" in post_data.get("url", "").lower() or
            "reddit.com/gallery" in post_data.get("url", "").lower()
        )
        
        post = RedditPost(
            id=post_data["id"],
            title=post_data["title"],
            created_utc=post_data["created_utc"],
            score=post_data["score"],
            num_comments=post_data["num_comments"],
            upvote_ratio=post_data["upvote_ratio"],
            over_18=post_data["over_18"],
            url=post_data["url"],
            selftext=post_data.get("selftext", ""),
            permalink=post_data["permalink"],
            subreddit=post_data["subreddit"],
            author=post_data.get("author"),
            is_image=is_image_post,
            image_url=post_data["url"] if is_image_post else None,
        )
        
        # Get comments
        comments_query = """
        MATCH (c:Comment)-[:REPLIED_TO]->(p:Post {id: $id})
        RETURN c.id as id, c.body as body, c.author as author,
               c.score as score, c.depth as depth, c.is_submitter as is_submitter,
               toString(c.created_utc) as created_utc, c.link_id
        ORDER BY c.depth, c.created_utc
        """
        
        comments_result = neo4j.execute_read(comments_query, parameters={"id": id})
        comments = [
            Comment(
                id=record["id"],
                body=record["body"],
                author=record.get("author"),
                score=record["score"],
                depth=record["depth"],
                is_submitter=record["is_submitter"],
                created_utc=record["created_utc"],
                link_id=record["link_id"]
            )
            for record in comments_result
        ]
        
        # Get images
        images_query = """
        MATCH (i:Image)-[:HAS_IMAGE]->(p:Post {id: $id})
        RETURN i.url as url, i.image_path as image_path
        """
        
        images_result = neo4j.execute_read(images_query, parameters={"id": id})
        images = [
            Image(url=record["url"], image_path=record.get("image_path"))
            for record in images_result
        ]
        
        return PostWithDetails(post=post, comments=comments, images=images)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats")
def get_stats():
    neo4j = get_neo4j_connection()
    
    # Total posts
    query = "MATCH (p:Post) RETURN count(p) as total"
    result = neo4j.execute_read(query)
    total_posts = result[0]["total"] if result else 0
    
    # Total comments
    query = "MATCH (c:Comment) RETURN count(c) as total"
    result = neo4j.execute_read(query)
    total_comments = result[0]["total"] if result else 0
    
    # Total images
    query = "MATCH (i:Image) RETURN count(i) as total"
    result = neo4j.execute_read(query)
    total_images = result[0]["total"] if result else 0
    
    # Subreddits
    query = "MATCH (s:Subreddit) RETURN count(s) as total"
    result = neo4j.execute_read(query)
    total_subreddits = result[0]["total"] if result else 0
    
    # Images with local files
    query = "MATCH (i:Image) WHERE i.image_path IS NOT NULL RETURN count(i) as total"
    result = neo4j.execute_read(query)
    cached_images = result[0]["total"] if result else 0
    
    return {
        "total_posts": total_posts,
        "total_comments": total_comments,
        "total_images": total_images,
        "cached_images": cached_images,
        "total_subreddits": total_subreddits,
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("Starting Reddit Data API Server")
    print("=" * 60)
    print("API endpoint: http://localhost:8001")
    print("API docs: http://localhost:8001/docs")
    print("Neo4j: bolt://neo4j:7687")
    print("=" * 60)
    print()
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
