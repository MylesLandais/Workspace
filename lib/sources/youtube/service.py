from neo4j import GraphDatabase
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

class YouTubeService:
    def __init__(self, driver: GraphDatabase.driver):
        self.driver = driver

    def get_video(self, video_id: str) -> Optional[Dict[str, Any]]:
        """Get a YouTube video by ID."""
        with self.driver.session(database="neo4j") as session:
            result = session.run("""
                MATCH (v:YouTubeVideo {id: $id})
                RETURN v {
                    .id, .title, .url, .description, .duration,
                    .viewCount, .s3Key, .s3Bucket, .contentType,
                    .createdAt, .updatedAt
                } as video
                LIMIT 1
                """, id=video_id)
            
            record = result.single()
            if record:
                return dict(record["video"])
            return None

    def get_videos_paginated(
        self,
        first: int = 10,
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get YouTube videos with pagination."""
        with self.driver.session(database="neo4j") as session:
            if after:
                query = """
                    MATCH (v:YouTubeVideo)
                    WHERE id(v) > toInteger($after)
                    RETURN v {
                        .id, .title, .url, .description, .duration,
                        .viewCount, .s3Key, .s3Bucket, .contentType,
                        .createdAt, .updatedAt
                    } as video, id(v) as cursor
                    ORDER BY v.createdAt DESC
                    LIMIT $first
                    """
            else:
                query = """
                    MATCH (v:YouTubeVideo)
                    RETURN v {
                        .id, .title, .url, .description, .duration,
                        .viewCount, .s3Key, .s3Bucket, .contentType,
                        .createdAt, .updatedAt
                    } as video, id(v) as cursor
                    ORDER BY v.createdAt DESC
                    LIMIT $first
                    """
            
            result = session.run(query, first=first)
            
            edges = []
            end_cursor = None
            
            for record in result:
                video_data = dict(record["video"])
                cursor = str(record["cursor"])
                edge = {
                    "node": video_data,
                    "cursor": cursor
                }
                edges.append(edge)
                end_cursor = cursor
            
            return {
                "edges": edges,
                "pageInfo": {
                    "hasNextPage": len(edges) == first,
                    "hasPreviousPage": after is not None,
                    "startCursor": edges[0]["cursor"] if edges else None,
                    "endCursor": end_cursor
                }
            }

    def get_channel(self, handle: str) -> Optional[Dict[str, Any]]:
        """Get a YouTube channel by handle."""
        with self.driver.session(database="neo4j") as session:
            result = session.run("""
                MATCH (c:YouTubeChannel {handle: $handle})
                RETURN c {
                    .handle, .url, .crawledAt
                } as channel
                LIMIT 1
                """, handle=handle)
            
            record = result.single()
            if record:
                return dict(record["channel"])
            return None

    def get_channel_videos(
        self,
        handle: str,
        first: int = 10,
        after: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """Get videos for a channel with pagination."""
        with self.driver.session(database="neo4j") as session:
            channel = session.run("""
                MATCH (c:YouTubeChannel {handle: $handle})
                RETURN count(c) > 0 as exists
                """, handle=handle).single()
            
            if not channel["exists"]:
                return None
            
            if after:
                query = """
                    MATCH (c:YouTubeChannel {handle: $handle})-[:HAS_VIDEO]->(v:YouTubeVideo)
                    WHERE id(v) > toInteger($after)
                    RETURN v {
                        .id, .title, .url, .description, .duration,
                        .viewCount, .s3Key, .s3Bucket, .contentType,
                        .createdAt, .updatedAt
                    } as video, id(v) as cursor
                    ORDER BY v.createdAt DESC
                    LIMIT $first
                    """
            else:
                query = """
                    MATCH (c:YouTubeChannel {handle: $handle})-[:HAS_VIDEO]->(v:YouTubeVideo)
                    RETURN v {
                        .id, .title, .url, .description, .duration,
                        .viewCount, .s3Key, .s3Bucket, .contentType,
                        .createdAt, .updatedAt
                    } as video, id(v) as cursor
                    ORDER BY v.createdAt DESC
                    LIMIT $first
                    """
            
            result = session.run(query, handle=handle, first=first)
            
            edges = []
            end_cursor = None
            
            for record in result:
                video_data = dict(record["video"])
                cursor = str(record["cursor"])
                edge = {
                    "node": video_data,
                    "cursor": cursor
                }
                edges.append(edge)
                end_cursor = cursor
            
            return {
                "handle": handle,
                "url": f"https://www.youtube.com/@{handle}",
                "videos": {
                    "edges": edges,
                    "pageInfo": {
                        "hasNextPage": len(edges) == first,
                        "hasPreviousPage": after is not None,
                        "startCursor": edges[0]["cursor"] if edges else None,
                        "endCursor": end_cursor
                    }
                }
            }

    def get_all_channels(self) -> List[Dict[str, Any]]:
        """Get all YouTube channels."""
        with self.driver.session(database="neo4j") as session:
            result = session.run("""
                MATCH (c:YouTubeChannel)
                RETURN c {
                    .handle, .url, .crawledAt
                } as channel
                ORDER BY c.crawledAt DESC
                """)
            
            return [dict(record["channel"]) for record in result]
