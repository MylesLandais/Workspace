"""
YouTube GraphQL API Server
Provides GraphQL endpoints for YouTube video data stored in Neo4j and MinIO.
"""

import os
from pathlib import Path
from typing import Optional, List
from datetime import datetime, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from pydantic import BaseModel

import boto3
from botocore.client import Config
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment
load_dotenv(Path.home() / "Workspace" / "jupyter" / ".env")

app = FastAPI(title="YouTube GraphQL API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Neo4j connection
neo4j_driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD"))
)

# S3 client (MinIO)
s3_client = boto3.client(
    's3',
    endpoint_url='http://localhost:9000',
    aws_access_key_id='minioadmin',
    aws_secret_access_key='minioadmin',
    config=Config(signature_version='s3v4'),
    region_name='us-east-1'
)

# Models
class YouTubeVideo(BaseModel):
    id: str
    title: str
    url: str
    description: Optional[str] = None
    duration: Optional[float] = None
    viewCount: Optional[int] = None
    s3Key: str
    s3Bucket: str
    contentType: str
    createdAt: datetime
    updatedAt: datetime

class PageInfo(BaseModel):
    hasNextPage: bool
    hasPreviousPage: bool
    startCursor: Optional[str] = None
    endCursor: Optional[str] = None

class YouTubeVideoEdge(BaseModel):
    node: YouTubeVideo
    cursor: str

class YouTubeVideoConnection(BaseModel):
    edges: List[YouTubeVideoEdge]
    pageInfo: PageInfo

class MediaSignedUrl(BaseModel):
    url: str
    expiresAt: datetime

# API Endpoints (REST/GraphQL hybrid)

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "youtube-graphql"}

@app.get("/api/videos", response_model=YouTubeVideoConnection)
async def get_videos(first: int = 10, after: Optional[str] = None):
    """Get YouTube videos with pagination (REST endpoint)."""
    with neo4j_driver.session(database="neo4j") as session:
        if after:
            query = """
                MATCH (v:YouTubeVideo)
                WHERE id(v) > toInteger($after)
                RETURN v, id(v) as cursor
                ORDER BY v.createdAt DESC
                LIMIT $first
                """
        else:
            query = """
                MATCH (v:YouTubeVideo)
                RETURN v, id(v) as cursor
                ORDER BY v.createdAt DESC
                LIMIT $first
                """
        
        result = session.run(query, first=first)
        
        edges = []
        end_cursor = None
        
        for record in result:
            node = dict(record["v"])
            cursor = str(record["cursor"])
            
            edges.append(YouTubeVideoEdge(
                node=YouTubeVideo(**node),
                cursor=cursor
            ))
            end_cursor = cursor
        
        return YouTubeVideoConnection(
            edges=edges,
            pageInfo=PageInfo(
                hasNextPage=len(edges) == first,
                hasPreviousPage=after is not None,
                startCursor=edges[0].cursor if edges else None,
                endCursor=end_cursor
            )
        )

@app.get("/api/videos/{video_id}", response_model=YouTubeVideo)
async def get_video(video_id: str):
    """Get a single YouTube video by ID."""
    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("""
            MATCH (v:YouTubeVideo {id: $id})
            RETURN v
            LIMIT 1
            """, id=video_id)
        
        record = result.single()
        if not record:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Video not found")
        
        return YouTubeVideo(**dict(record["v"]))

@app.get("/api/videos/{video_id}/playback-url", response_model=MediaSignedUrl)
async def get_playback_url(video_id: str, expiry: int = 3600):
    """Get presigned S3 URL for video playback."""
    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("""
            MATCH (v:YouTubeVideo {id: $id})
            RETURN v.s3Bucket as bucket, v.s3Key as key
            LIMIT 1
            """, id=video_id)
        
        record = result.single()
        if not record:
            from fastapi import HTTPException
            raise HTTPException(status_code=404, detail="Video not found")
        
        bucket = record["bucket"]
        key = record["key"]
        
        # Generate presigned URL
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': bucket, 'Key': key},
            ExpiresIn=expiry
        )
        
        return MediaSignedUrl(
            url=url,
            expiresAt=datetime.utcnow() + timedelta(seconds=expiry)
        )

@app.get("/api/channels")
async def get_channels():
    """Get all YouTube channels."""
    with neo4j_driver.session(database="neo4j") as session:
        result = session.run("""
            MATCH (c:YouTubeChannel)
            RETURN c
            ORDER BY c.crawledAt DESC
            """)
        
        channels = [dict(record["c"]) for record in result]
        return {"channels": channels}

if __name__ == "__main__":
    print("Starting YouTube GraphQL API...")
    print(f"Neo4j: {os.getenv('NEO4J_URI')}")
    print(f"S3: http://localhost:9000")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=4003,
        log_level="info"
    )
