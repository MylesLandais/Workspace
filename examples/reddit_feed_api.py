#!/usr/bin/env python3
"""
Example FastAPI application using scraped Reddit data.

This demonstrates a simple Reddit feed API backed by Neo4j database.
"""

import os
from typing import List, Optional
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from neo4j import GraphDatabase
import boto3

# Configuration
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.getenv("MINIO_BUCKET", "model-images")

# FastAPI app
app = FastAPI(title="Reddit Feed API", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# MinIO client
s3_client = boto3.client(
    's3',
    endpoint_url=f'http://{MINIO_ENDPOINT}',
    aws_access_key_id=MINIO_ACCESS_KEY,
    aws_secret_access_key=MINIO_SECRET_KEY,
    region_name='us-east-1',
    config=boto3.Config(signature_version='s3v4'),
)


# Pydantic models
class Post(BaseModel):
    id: str
    title: str
    author: str
    score: int
    num_comments: int
    url: str
    created_at: datetime
    subreddit: str


class Comment(BaseModel):
    id: str
    author: str
    body: str
    score: int
    created_at: datetime


class PostDetail(BaseModel):
    post: Post
    comments: List[Comment]
    images: List[str]


class SubredditStats(BaseModel):
    subreddit: str
    total_posts: int
    avg_score: float
    max_score: int
    total_comments: int


def execute_query(query: str, params: dict = None) -> list:
    """Execute a Cypher query and return results."""
    with driver.session() as session:
        result = session.run(query, params or {})
        return [record.data() for record in result]


def get_image_url(object_name: str) -> Optional[str]:
    """Generate presigned URL for an image in MinIO."""
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': MINIO_BUCKET, 'Key': object_name},
            ExpiresIn=3600,
        )
        return url
    except Exception:
        return None


@app.get("/")
async def root():
    """API root with available endpoints."""
    return {
        "message": "Reddit Feed API",
        "version": "1.0.0",
        "endpoints": {
            "GET /api/feed": "Get recent posts from subreddit",
            "GET /api/posts/{post_id}": "Get post with comments and images",
            "GET /api/search": "Search posts by keyword",
            "GET /api/subreddits/{name}/stats": "Get subreddit statistics",
            "GET /api/health": "Health check",
        }
    }


@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    try:
        driver.verify_connectivity()
        return {"status": "healthy", "database": "connected"}
    except Exception:
        raise HTTPException(status_code=503, detail="Database connection failed")


@app.get("/api/feed", response_model=List[Post])
async def get_feed(
    subreddit: str = Query(default="unixporn", description="Subreddit name"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of posts"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
):
    """
    Get recent posts from a subreddit.
    
    Example: /api/feed?subreddit=unixporn&limit=10
    """
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
    RETURN p.id as id, p.title as title, p.author as author, 
           p.score as score, p.num_comments as num_comments,
           p.url as url, p.created_utc as created_at, p.subreddit as subreddit
    ORDER BY p.created_utc DESC
    SKIP $offset
    LIMIT $limit
    """
    
    results = execute_query(query, {
        'subreddit': subreddit,
        'limit': limit,
        'offset': offset
    })
    
    return [Post(**r) for r in results]


@app.get("/api/posts/{post_id}", response_model=PostDetail)
async def get_post_detail(post_id: str):
    """
    Get post with comments and images.
    
    Example: /api/posts/1q8sbv9
    """
    query = """
    MATCH (p:Post {id: $post_id})
    OPTIONAL MATCH (c:Comment)-[:COMMENT_ON]->(p)
    OPTIONAL MATCH (i:Image)-[:IMAGE_IN]->(p)
    WITH p, 
         collect({id: c.id, author: c.author, body: c.text, 
                   score: c.score, created_at: c.created_utc}) as comments,
         collect(i.object_name) as image_objects
    RETURN p, comments, image_objects
    """
    
    results = execute_query(query, {'post_id': post_id})
    
    if not results:
        raise HTTPException(status_code=404, detail="Post not found")
    
    result = results[0]
    post_data = result['p']
    comments = [Comment(**c) for c in result.get('comments', [])]
    
    # Generate presigned URLs for images
    image_urls = []
    for obj_name in result.get('image_objects', []):
        url = get_image_url(obj_name)
        if url:
            image_urls.append(url)
    
    return PostDetail(
        post=Post(**post_data),
        comments=comments,
        images=image_urls
    )


@app.get("/api/search")
async def search_posts(
    q: str = Query(..., description="Search query"),
    subreddit: Optional[str] = Query(default=None, description="Filter by subreddit"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Search posts by keyword.
    
    Example: /api/search?q=hyprland&subreddit=unixporn
    """
    if subreddit:
        query = """
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
        WHERE toLower(p.title) CONTAINS toLower($query)
        RETURN p.id as id, p.title as title, p.author as author, 
               p.score as score, p.num_comments as num_comments,
               p.url as url, p.created_utc as created_at, p.subreddit as subreddit
        ORDER BY p.created_utc DESC
        LIMIT $limit
        """
        params = {'subreddit': subreddit, 'query': q, 'limit': limit}
    else:
        query = """
        MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
        WHERE toLower(p.title) CONTAINS toLower($query)
        RETURN p.id as id, p.title as title, p.author as author, 
               p.score as score, p.num_comments as num_comments,
               p.url as url, p.created_utc as created_at, p.subreddit as subreddit
        ORDER BY p.created_utc DESC
        LIMIT $limit
        """
        params = {'query': q, 'limit': limit}
    
    results = execute_query(query, params)
    return [Post(**r) for r in results]


@app.get("/api/subreddits/{name}/stats", response_model=SubredditStats)
async def get_subreddit_stats(name: str):
    """
    Get subreddit statistics.
    
    Example: /api/subreddits/unixporn/stats
    """
    query = """
    MATCH (s:Subreddit {name: $name})
    OPTIONAL MATCH (p:Post)-[:POSTED_IN]->(s)
    WITH s, 
         count(p) as total_posts,
         avg(p.score) as avg_score,
         max(p.score) as max_score,
         sum(p.num_comments) as total_comments
    RETURN s.name as subreddit,
           total_posts,
           avg_score,
           max_score,
           total_comments
    """
    
    results = execute_query(query, {'name': name})
    
    if not results:
        raise HTTPException(status_code=404, detail="Subreddit not found")
    
    return SubredditStats(**results[0])


@app.get("/api/recent")
async def get_recent_posts(
    hours: int = Query(default=24, ge=1, le=168, description="Hours to look back"),
    limit: int = Query(default=20, ge=1, le=100),
):
    """
    Get recent posts from all subreddits within a time window.
    
    Example: /api/recent?hours=48
    """
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()
    
    query = """
    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
    WHERE datetime(p.created_utc) >= datetime($cutoff)
    RETURN p.id as id, p.title as title, p.author as author, 
           p.score as score, p.num_comments as num_comments,
           p.url as url, p.created_utc as created_at, p.subreddit as subreddit
    ORDER BY p.created_utc DESC
    LIMIT $limit
    """
    
    results = execute_query(query, {'cutoff': cutoff, 'limit': limit})
    return [Post(**r) for r in results]


if __name__ == "__main__":
    import uvicorn
    
    print("Starting Reddit Feed API...")
    print(f"Neo4j: {NEO4J_URI}")
    print(f"MinIO: {MINIO_ENDPOINT}")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
