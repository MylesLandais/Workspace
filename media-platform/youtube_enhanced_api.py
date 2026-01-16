"""API for enhanced YouTube video data with full features."""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import json

app = FastAPI(title="YouTube Enhanced API")


class YouTubeChapter(BaseModel):
    """Chapter marker model."""
    index: int
    title: str
    start_time: float
    end_time: float
    timestamp: str


class YouTubeTranscript(BaseModel):
    """Transcript segment model."""
    start: float
    end: float
    text: str


class YouTubeComment(BaseModel):
    """Comment model."""
    comment_id: str
    text: str
    author: str
    author_id: str
    like_count: int
    reply_count: int
    is_reply: bool
    parent_id: str
    timestamp: datetime


class YouTubeVideoFull(BaseModel):
    """Full video model with all features."""
    video_id: str
    title: str
    url: str
    description: str
    duration: int
    view_count: int
    like_count: int
    comment_count: int
    published_at: datetime
    thumbnail_url: str
    channel_id: str
    channel_name: str
    tags: List[str]
    categories: List[str]


class YouTubeVideoWithFeatures(BaseModel):
    """Video with all features."""
    video: YouTubeVideoFull
    chapters: List[YouTubeChapter] = []
    transcript: List[YouTubeTranscript] = []
    comments: List[YouTubeComment] = []


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "youtube-enhanced-api"}


@app.get("/api/videos/{video_id}", response_model=YouTubeVideoWithFeatures)
async def get_video_with_features(video_id: str):
    """Get a video with all features (chapters, transcript, comments)."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    # Fetch video
    video_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})
    RETURN v {
        .video_id, .title, .url, .description, .duration,
        .view_count, .like_count, .comment_count,
        .published_at, .thumbnail_url, .channel_id, .channel_name,
        .tags, .categories
    } as video
    """
    
    result = neo4j.execute_read(video_query, parameters={"video_id": video_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="Video not found")
    
    video_data = dict(result[0]["video"])
    
    # Parse tags and categories
    video_data["tags"] = json.loads(video_data.get("tags", "[]"))
    video_data["categories"] = json.loads(video_data.get("categories", "[]"))
    
    # Fetch chapters
    chapters_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_CHAPTER]->(c:YouTubeChapter)
    RETURN c {
        .index, .title, .start_time, .end_time, .timestamp
    } as chapter
    ORDER BY c.index
    """
    
    chapters_result = neo4j.execute_read(chapters_query, parameters={"video_id": video_id})
    chapters = [dict(r["chapter"]) for r in chapters_result]
    
    # Fetch transcript
    transcript_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_TRANSCRIPT_SEGMENT]->(t:YouTubeTranscript)
    RETURN t {
        .start_time as start, .end_time as end, .text
    } as segment
    ORDER BY t.start_time
    """
    
    transcript_result = neo4j.execute_read(transcript_query, parameters={"video_id": video_id})
    transcript = [dict(r["segment"]) for r in transcript_result]
    
    # Fetch comments
    comments_query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
    RETURN c {
        .comment_id, .text, .author, .author_id,
        .like_count, .reply_count, .is_reply, .parent_id, .timestamp
    } as comment
    ORDER BY c.like_count DESC, c.timestamp DESC
    """
    
    comments_result = neo4j.execute_read(comments_query, parameters={"video_id": video_id})
    comments = [dict(r["comment"]) for r in comments_result]
    
    return YouTubeVideoWithFeatures(
        video=YouTubeVideoFull(**video_data),
        chapters=chapters,
        transcript=transcript,
        comments=comments
    )


@app.get("/api/videos/{video_id}/comments", response_model=List[YouTubeComment])
async def get_video_comments(
    video_id: str,
    limit: int = Query(default=50, ge=1, le=200),
    sort_by: str = Query(default="top", regex="^(top|new|replies)$")
):
    """Get comments for a video with sorting options."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    if sort_by == "top":
        order_clause = "ORDER BY c.like_count DESC, c.timestamp DESC"
    elif sort_by == "new":
        order_clause = "ORDER BY c.timestamp DESC"
    else:  # replies
        order_clause = "ORDER BY c.reply_count DESC, c.like_count DESC"
    
    query = f"""
    MATCH (v:YouTubeVideo {{video_id: $video_id}})-[:HAS_COMMENT]->(c:YouTubeComment)
    RETURN c {{
        .comment_id, .text, .author, .author_id,
        .like_count, .reply_count, .is_reply, .parent_id, .timestamp
    }} as comment
    {order_clause}
    LIMIT $limit
    """
    
    result = neo4j.execute_read(query, parameters={"video_id": video_id, "limit": limit})
    return [dict(r["comment"]) for r in result]


@app.get("/api/videos/{video_id}/transcript", response_model=List[YouTubeTranscript])
async def get_video_transcript(video_id: str):
    """Get transcript for a video."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_TRANSCRIPT_SEGMENT]->(t:YouTubeTranscript)
    RETURN t {
        .start_time as start, .end_time as end, .text
    } as segment
    ORDER BY t.start_time
    """
    
    result = neo4j.execute_read(query, parameters={"video_id": video_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="Transcript not found")
    
    return [dict(r["segment"]) for r in result]


@app.get("/api/videos/{video_id}/chapters", response_model=List[YouTubeChapter])
async def get_video_chapters(video_id: str):
    """Get chapter markers for a video."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_CHAPTER]->(c:YouTubeChapter)
    RETURN c {
        .index, .title, .start_time, .end_time, .timestamp
    } as chapter
    ORDER BY c.index
    """
    
    result = neo4j.execute_read(query, parameters={"video_id": video_id})
    
    if not result:
        raise HTTPException(status_code=404, detail="Chapters not found")
    
    return [dict(r["chapter"]) for r in result]


@app.get("/api/videos/{video_id}/description")
async def get_video_description(video_id: str):
    """Get full description for a video."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    query = """
    MATCH (v:YouTubeVideo {video_id: $video_id})
    RETURN v.description as description
    """
    
    result = neo4j.execute_read(query, parameters={"video_id": video_id})
    
    if not result or not result[0]["description"]:
        raise HTTPException(status_code=404, detail="Description not found")
    
    return {"video_id": video_id, "description": result[0]["description"]}


@app.get("/api/creator/{creator_slug}/videos", response_model=List[YouTubeVideoFull])
async def get_creator_videos(
    creator_slug: str,
    limit: int = Query(default=20, ge=1, le=100)
):
    """Get all videos for a creator."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    query = """
    MATCH (c:Creator {slug: $slug})-[:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
    MATCH (h)-[:OWNS_VIDEO]->(v:YouTubeVideo)
    RETURN v {
        .video_id, .title, .url, .description, .duration,
        .view_count, .like_count, .comment_count,
        .published_at, .thumbnail_url, .channel_id, .channel_name,
        .tags, .categories
    } as video
    ORDER BY v.published_at DESC
    LIMIT $limit
    """
    
    result = neo4j.execute_read(query, parameters={"slug": creator_slug, "limit": limit})
    
    videos = []
    for r in result:
        video_data = dict(r["video"])
        video_data["tags"] = json.loads(video_data.get("tags", "[]"))
        video_data["categories"] = json.loads(video_data.get("categories", "[]"))
        videos.append(YouTubeVideoFull(**video_data))
    
    return videos


@app.get("/api/search/videos")
async def search_videos(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Search videos by title and description using fulltext search."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    query = """
    CALL db.index.fulltext.queryNodes('video_title_ft', $query) YIELD node, score
    RETURN node {
        .video_id, .title, .url, .description, .duration,
        .view_count, .like_count, .comment_count,
        .published_at, .thumbnail_url, .channel_id, .channel_name,
        .tags, .categories
    } as video, score
    ORDER BY score DESC
    LIMIT $limit
    """
    
    result = neo4j.execute_read(query, parameters={"query": q, "limit": limit})
    
    videos = []
    for r in result:
        video_data = dict(r["video"])
        video_data["tags"] = json.loads(video_data.get("tags", "[]"))
        video_data["categories"] = json.loads(video_data.get("categories", "[]"))
        videos.append(YouTubeVideoFull(**video_data))
    
    return videos


@app.get("/api/search/comments")
async def search_comments(
    q: str = Query(..., min_length=2),
    limit: int = Query(default=20, ge=1, le=100)
):
    """Search comments by text using fulltext search."""
    from feed.storage.neo4j_connection import get_connection
    
    neo4j = get_connection()
    
    query = """
    CALL db.index.fulltext.queryNodes('comment_text_ft', $query) YIELD node, score
    RETURN node {
        .comment_id, .text, .author, .like_count,
        .video_id, .timestamp
    } as comment, score
    ORDER BY score DESC
    LIMIT $limit
    """
    
    result = neo4j.execute_read(query, parameters={"query": q, "limit": limit})
    return [dict(r["comment"]) for r in result]


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
