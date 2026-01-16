"""API endpoints for YouTube analytics and comment threading."""

from fastapi import FastAPI, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from media_platform.services.youtube_analytics_service import YouTubeAnalytics
from media_platform.services.comment_thread_service import CommentThread

analytics = YouTubeAnalytics()
thread_service = CommentThread()


class CommentThreadNode(BaseModel):
    """Comment thread node model."""
    comment_id: str
    text: str
    author: str
    author_id: str
    like_count: int
    reply_count: int
    timestamp: datetime
    replies: List['CommentThreadNode'] = []


class CommentWithContext(BaseModel):
    """Comment with parent context."""
    comment_id: str
    text: str
    author: str
    author_id: str
    like_count: int
    reply_count: int
    timestamp: datetime
    parent_id: str
    context: List[dict]


def register_analytics_routes(app: FastAPI):
    """Register analytics routes to existing FastAPI app."""
    
    @app.get("/api/analytics/video/{video_id}")
    async def get_video_analytics(video_id: str):
        """Get comprehensive analytics for a video."""
        analytics_data = analytics.get_video_analytics(video_id)
        
        if not analytics_data:
            raise HTTPException(status_code=404, detail="Video analytics not found")
        
        return analytics_data
    
    @app.get("/api/analytics/creator/{creator_slug}")
    async def get_creator_analytics(creator_slug: str):
        """Get analytics for a creator's videos."""
        analytics_data = analytics.get_creator_analytics(creator_slug)
        
        if not analytics_data:
            raise HTTPException(status_code=404, detail="Creator analytics not found")
        
        return analytics_data
    
    @app.get("/api/analytics/video/{video_id}/sentiment")
    async def get_video_sentiment(video_id: str):
        """Get sentiment analysis for video comments."""
        sentiment_data = analytics.get_comment_sentiment_overview(video_id)
        return sentiment_data
    
    @app.get("/api/analytics/video/{video_id}/engagement-timeline")
    async def get_engagement_timeline(
        video_id: str,
        interval_hours: int = Query(default=24, ge=1, le=168)
    ):
        """Get comment engagement over time."""
        timeline_data = analytics.get_comment_engagement_timeline(
            video_id,
            interval_hours=interval_hours
        )
        return timeline_data
    
    @app.get("/api/analytics/video/{video_id}/top-commenters")
    async def get_top_commenters(
        video_id: str,
        limit: int = Query(default=10, ge=1, le=50)
    ):
        """Get top commenters by engagement."""
        top_commenters = analytics.get_top_commenters(video_id, limit=limit)
        return top_commenters
    
    @app.get("/api/analytics/video/{video_id}/keywords")
    async def get_keyword_analysis(
        video_id: str,
        top_n: int = Query(default=10, ge=5, le=50)
    ):
        """Get most common keywords in comments."""
        keywords = analytics.get_keyword_analysis(video_id, top_n=top_n)
        return keywords
    
    @app.get("/api/analytics/trending")
    async def get_trending_videos(
        hours: int = Query(default=24, ge=1, le=168),
        limit: int = Query(default=20, ge=1, le=100)
    ):
        """Get trending videos based on recent engagement."""
        trending = analytics.get_video_trends(hours=hours, limit=limit)
        return trending
    
    @app.get("/api/analytics/compare")
    async def compare_channels(
        creators: str = Query(..., description="Comma-separated creator slugs")
    ):
        """Compare multiple channels' performance."""
        creator_list = [c.strip() for c in creators.split(",")]
        comparison = analytics.get_channel_comparison(creator_list)
        return comparison
    
    @app.get("/api/comments/{video_id}/thread", response_model=List[CommentThreadNode])
    async def get_comment_thread(
        video_id: str,
        root_comment_id: Optional[str] = None
    ):
        """Get comment thread for a video."""
        thread = thread_service.get_comment_thread(video_id, root_comment_id)
        return thread
    
    @app.get("/api/comments/{comment_id}/context", response_model=CommentWithContext)
    async def get_comment_context(
        comment_id: str,
        depth: int = Query(default=2, ge=1, le=5)
    ):
        """Get comment with parent context."""
        context = thread_service.get_comment_context(comment_id, depth)
        
        if not context:
            raise HTTPException(status_code=404, detail="Comment not found")
        
        return context
    
    @app.get("/api/comments/{comment_id}/replies")
    async def get_comment_replies(
        comment_id: str,
        limit: int = Query(default=20, ge=1, le=100)
    ):
        """Get direct replies to a comment."""
        replies = thread_service.get_comment_replies(comment_id, limit=limit)
        return replies
    
    @app.get("/api/videos/{video_id}/longest-threads")
    async def get_longest_threads(
        video_id: str,
        limit: int = Query(default=10, ge=1, le=50)
    ):
        """Get longest comment threads."""
        threads = thread_service.get_longest_threads(video_id, limit=limit)
        return threads
    
    @app.post("/api/videos/{video_id}/comments/update-reply-counts")
    async def update_reply_counts(video_id: str):
        """Update reply counts for all comments in a video."""
        thread_service.update_reply_counts(video_id)
        return {"status": "success", "message": "Reply counts updated"}
