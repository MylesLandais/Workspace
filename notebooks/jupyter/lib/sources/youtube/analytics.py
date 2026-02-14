"""Advanced analytics for YouTube video data."""

from typing import Dict, List, Optional
from datetime import datetime, timedelta
from collections import Counter

from feed.storage.neo4j_connection import get_connection

class YouTubeAnalytics:
    """Analytics service for YouTube video and comment data."""
    
    def __init__(self):
        self.neo4j = get_connection()
    
    def get_video_analytics(self, video_id: str) -> Dict:
        """Get comprehensive analytics for a single video."""
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})
        OPTIONAL MATCH (v)-[:HAS_COMMENT]->(c:YouTubeComment)
        WITH v, count(c) as total_comments, sum(c.like_count) as total_likes, 
             sum(c.reply_count) as total_replies,
             max(c.like_count) as top_comment_likes
        OPTIONAL MATCH (v)-[:HAS_CHAPTER]->(ch:YouTubeChapter)
        WITH v, total_comments, total_likes, total_replies, top_comment_likes,
             count(ch) as chapter_count
        RETURN {
            video_id: v.video_id,
            title: v.title,
            duration: v.duration,
            view_count: v.view_count,
            like_count: v.like_count,
            comment_count: v.comment_count,
            total_comments: total_comments,
            total_comment_likes: total_likes,
            total_comment_replies: total_replies,
            top_comment_likes: top_comment_likes,
            chapter_count: chapter_count,
            engagement_rate: CASE 
                WHEN v.view_count > 0 
                THEN (v.like_count * 1.0) / v.view_count 
                ELSE 0 END,
            comment_rate: CASE 
                WHEN v.view_count > 0 
                THEN (total_comments * 1.0) / v.view_count 
                ELSE 0 END,
            avg_likes_per_comment: CASE 
                WHEN total_comments > 0 
                THEN (total_likes * 1.0) / total_comments 
                ELSE 0 END,
            avg_replies_per_comment: CASE 
                WHEN total_comments > 0 
                THEN (total_replies * 1.0) / total_comments 
                ELSE 0 END
        } as analytics
        """
        
        result = self.neo4j.execute_read(query, parameters={"video_id": video_id})
        
        if result:
            return dict(result[0]["analytics"])
        
        return None
    
    def get_creator_analytics(self, creator_slug: str) -> Dict:
        """Get analytics for a creator's videos."""
        query = """
        MATCH (c:Creator {slug: $slug})-[:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
        MATCH (h)-[:OWNS_VIDEO]->(v:YouTubeVideo)
        OPTIONAL MATCH (v)-[:HAS_COMMENT]->(com:YouTubeComment)
        WITH c, v, count(com) as video_comments, sum(com.like_count) as video_likes
        RETURN {
            creator_slug: c.slug,
            creator_name: c.name,
            total_videos: count(DISTINCT v),
            total_views: sum(v.view_count),
            total_likes: sum(v.like_count),
            total_comments: sum(v.comment_count),
            total_fetched_comments: sum(video_comments),
            total_comment_likes: sum(video_likes),
            avg_views_per_video: CASE 
                WHEN count(DISTINCT v) > 0 
                THEN sum(v.view_count) * 1.0 / count(DISTINCT v) 
                ELSE 0 END,
            avg_likes_per_video: CASE 
                WHEN count(DISTINCT v) > 0 
                THEN sum(v.like_count) * 1.0 / count(DISTINCT v) 
                ELSE 0 END,
            avg_comments_per_video: CASE 
                WHEN count(DISTINCT v) > 0 
                THEN sum(v.comment_count) * 1.0 / count(DISTINCT v) 
                ELSE 0 END,
            overall_engagement_rate: CASE 
                WHEN sum(v.view_count) > 0 
                THEN (sum(v.like_count) * 1.0) / sum(v.view_count) 
                ELSE 0 END,
            most_viewed_video: {
                video_id: COLLECT({v: v, views: v.view_count})[0].v.video_id,
                title: COLLECT({v: v, views: v.view_count})[0].v.title,
                views: max(v.view_count)
            },
            most_liked_video: {
                video_id: COLLECT({v: v, likes: v.like_count})[0].v.video_id,
                title: COLLECT({v: v, likes: v.like_count})[0].v.title,
                likes: max(v.like_count)
            }
        } as analytics
        """
        
        result = self.neo4j.execute_read(query, parameters={"slug": creator_slug})
        
        if result:
            return dict(result[0]["analytics"])
        
        return None
    
    def get_comment_sentiment_overview(self, video_id: str) -> Dict:
        """Get sentiment overview for video comments (keyword-based)."""
        # This is a simple keyword-based sentiment analysis
        # For production, use NLP models
        
        positive_keywords = [
            'good', 'great', 'awesome', 'amazing', 'love', 'excellent',
            'helpful', 'thanks', 'thank you', 'perfect', 'best',
            'informative', 'clear', 'useful', 'brilliant', 'fantastic'
        ]
        
        negative_keywords = [
            'bad', 'terrible', 'awful', 'hate', 'worst', 'useless',
            'confusing', 'wrong', 'boring', 'stupid', 'waste',
            'disappointed', 'unhelpful', 'poor', 'badly', 'annoying'
        ]
        
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        WITH c, toLower(c.text) as text_lower
        WHERE ANY(keyword IN $positive_keywords WHERE text_lower CONTAINS keyword)
        WITH c, 'positive' as sentiment
        RETURN count(c) as positive_count
        """
        
        positive_result = self.neo4j.execute_read(query, parameters={
            "video_id": video_id,
            "positive_keywords": positive_keywords
        })
        positive_count = positive_result[0]["positive_count"] if positive_result else 0
        
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        WITH c, toLower(c.text) as text_lower
        WHERE ANY(keyword IN $negative_keywords WHERE text_lower CONTAINS keyword)
        WITH c, 'negative' as sentiment
        RETURN count(c) as negative_count
        """
        
        negative_result = self.neo4j.execute_read(query, parameters={
            "video_id": video_id,
            "negative_keywords": negative_keywords
        })
        negative_count = negative_result[0]["negative_count"] if negative_result else 0
        
        # Get total comments
        total_query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        RETURN count(c) as total
        """
        
        total_result = self.neo4j.execute_read(total_query, parameters={"video_id": video_id})
        total_count = total_result[0]["total"] if total_result else 0
        
        neutral_count = total_count - positive_count - negative_count
        
        return {
            "video_id": video_id,
            "total_comments": total_count,
            "positive_count": positive_count,
            "negative_count": negative_count,
            "neutral_count": neutral_count,
            "positive_percentage": (positive_count / total_count * 100) if total_count > 0 else 0,
            "negative_percentage": (negative_count / total_count * 100) if total_count > 0 else 0,
            "neutral_percentage": (neutral_count / total_count * 100) if total_count > 0 else 0,
            "sentiment_score": ((positive_count - negative_count) / total_count) if total_count > 0 else 0
        }
    
    def get_comment_engagement_timeline(self, video_id: str, interval_hours: int = 24) -> List[Dict]:
        """Get comment engagement over time."""
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        WITH c, datetime(c.timestamp) as comment_time
        WITH c, 
             duration.between(comment_time, datetime(), 'PT' + toString($interval_hours) + 'H') as interval
        WITH interval.start as interval_start, interval.end as interval_end,
             count(c) as comment_count, sum(c.like_count) as total_likes
        RETURN {
            interval_start: toString(interval_start),
            interval_end: toString(interval_end),
            comment_count: comment_count,
            total_likes: total_likes,
            avg_likes_per_comment: CASE 
                WHEN comment_count > 0 
                THEN total_likes * 1.0 / comment_count 
                ELSE 0 END
        } as engagement
        ORDER BY interval_start
        """
        
        result = self.neo4j.execute_read(query, parameters={
            "video_id": video_id,
            "interval_hours": interval_hours
        })
        
        return [dict(r["engagement"]) for r in result]
    
    def get_top_commenters(self, video_id: str, limit: int = 10) -> List[Dict]:
        """Get top commenters by engagement."""
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        WITH c.author as commenter, c.author_id as author_id,
             count(c) as comment_count,
             sum(c.like_count) as total_likes,
             sum(c.reply_count) as total_replies
        ORDER BY total_likes DESC
        RETURN {
            author: commenter,
            author_id: author_id,
            comment_count: comment_count,
            total_likes: total_likes,
            total_replies: total_replies,
            avg_likes_per_comment: CASE 
                WHEN comment_count > 0 
                THEN total_likes * 1.0 / comment_count 
                ELSE 0 END
        } as top_commenter
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(query, parameters={
            "video_id": video_id,
            "limit": limit
        })
        
        return [dict(r["top_commenter"]) for r in result]
    
    def get_video_trends(self, hours: int = 24, limit: int = 20) -> List[Dict]:
        """Get trending videos based on recent engagement."""
        query = """
        MATCH (v:YouTubeVideo)
        WHERE datetime(v.published_at) > datetime() - duration('PT' + toString($hours) + 'H')
        OPTIONAL MATCH (v)-[:HAS_COMMENT]->(c:YouTubeComment)
        WITH v, count(c) as comment_count, sum(c.like_count) as total_comment_likes
        RETURN {
            video_id: v.video_id,
            title: v.title,
            channel_name: v.channel_name,
            published_at: v.published_at,
            view_count: v.view_count,
            like_count: v.like_count,
            comment_count: v.comment_count,
            fetched_comment_count: comment_count,
            fetched_comment_likes: total_comment_likes,
            engagement_score: (v.view_count * 0.1 + v.like_count + comment_count * 2 + total_comment_likes * 1.5)
        } as trend
        ORDER BY trend.engagement_score DESC
        LIMIT $limit
        """
        
        result = self.neo4j.execute_read(query, parameters={
            "hours": hours,
            "limit": limit
        })
        
        return [dict(r["trend"]) for r in result]
    
    def get_keyword_analysis(self, video_id: str, top_n: int = 10) -> Dict:
        """Analyze most common keywords in comments."""
        query = """
        MATCH (v:YouTubeVideo {video_id: $video_id})-[:HAS_COMMENT]->(c:YouTubeComment)
        UNWIND split(toLower(c.text), ' ') as word
        WITH word, count(*) as word_count
        WHERE size(word) > 3  // Filter out short words
        ORDER BY word_count DESC
        RETURN {
            word: word,
            count: word_count,
            percentage: word_count * 100.0 / sum(COUNT(*))
        } as keyword
        LIMIT $top_n
        """
        
        result = self.neo4j.execute_read(query, parameters={
            "video_id": video_id,
            "top_n": top_n
        })
        
        return [dict(r["keyword"]) for r in result]
    
    def get_channel_comparison(self, creator_slugs: List[str]) -> Dict:
        """Compare multiple channels' performance."""
        query = """
        UNWIND $slugs as slug
        MATCH (c:Creator {slug: slug})-[:OWNS_HANDLE]->(h:Handle)-[:ON_PLATFORM]->(p:Platform {slug: 'youtube'})
        MATCH (h)-[:OWNS_VIDEO]->(v:YouTubeVideo)
        WITH c, count(DISTINCT v) as video_count,
             sum(v.view_count) as total_views,
             sum(v.like_count) as total_likes,
             avg(v.view_count) as avg_views,
             avg(v.like_count) as avg_likes
        RETURN {
            creator_slug: c.slug,
            creator_name: c.name,
            video_count: video_count,
            total_views: total_views,
            total_likes: total_likes,
            avg_views: avg_views,
            avg_likes: avg_likes,
            engagement_rate: CASE 
                WHEN total_views > 0 
                THEN (total_likes * 1.0) / total_views 
                ELSE 0 END
        } as comparison
        ORDER BY comparison.total_views DESC
        """
        
        result = self.neo4j.execute_read(query, parameters={"slugs": creator_slugs})
        
        return [dict(r["comparison"]) for r in result]
