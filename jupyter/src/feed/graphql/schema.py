"""GraphQL schema for feed monitoring with subscriptions."""

from typing import List, Optional
from datetime import datetime
import strawberry
from strawberry.fastapi import GraphQLRouter

from ..storage.neo4j_connection import get_connection
from .creator_schema import (
    CreatorType,
    HandleType,
    Media,
    Platform,
    CandidateHandle,
    FeedFilter,
    CreatorQuery,
    FeedQuery,
)
from .chan_schema import (
    ChanQueryType,
    ChanThread,
    ChanPost,
    ChanImage,
    ChanStats,
    ThreadFilter,
    PostFilter,
)
from .ecommerce_schema import (
    EcommerceQuery,
    Product,
    GarmentStyle,
    ProductFilter,
    StyleFilter,
)
from .image_search_schema import (
    ImageSearchQuery,
    ImageSearchMutation,
    ImageLookupResultType,
    SimilarImageResult,
    ImageStatusResult,
    PublicSearchResult,
    ImageMatchResult,
    RecoveryResult,
    IndexResult,
    ImageSearchProvider,
    VideoIdentificationResultType,
    StashSceneType,
    StashPerformerType,
)


@strawberry.type
class Subreddit:
    """Subreddit type."""
    name: str
    post_count: int


@strawberry.type
class User:
    """User type."""
    username: str
    post_count: Optional[int] = None


@strawberry.type
class Post:
    """Post type."""
    id: str
    title: str
    created_utc: str
    score: int
    num_comments: int
    upvote_ratio: float
    over_18: bool
    url: str
    selftext: str
    permalink: Optional[str] = None
    subreddit: str
    author: Optional[str] = None
    is_image: bool = False
    image_url: Optional[str] = None


@strawberry.type
class FeedStats:
    """Feed statistics."""
    total_posts: int
    total_subreddits: int
    total_users: int
    posts_today: int


@strawberry.type
class FeedList:
    """Feed list with posts."""
    subreddit: str
    posts: List[Post]
    total_count: int


@strawberry.input
class PostFilter:
    """Filter for posts."""
    subreddit: Optional[str] = None
    min_score: Optional[int] = None
    is_image: Optional[bool] = None
    limit: int = 20
    offset: int = 0


@strawberry.type
class Query:
    """GraphQL queries."""
    
    # E-commerce queries - delegate to EcommerceQuery
    _ecommerce_query = None
    
    def _get_ecommerce_query(self):
        """Lazy initialization of EcommerceQuery."""
        if self._ecommerce_query is None:
            self._ecommerce_query = EcommerceQuery()
        return self._ecommerce_query
    
    @strawberry.field
    def product(self, id: str) -> Optional[Product]:
        """Get product by ID."""
        return self._get_ecommerce_query().product(id)
    
    @strawberry.field
    def products(self, filter: Optional[ProductFilter] = None) -> List[Product]:
        """Get products with filtering."""
        return self._get_ecommerce_query().products(filter)
    
    @strawberry.field
    def search_products(self, query_text: str, limit: int = 20) -> List[Product]:
        """Full-text search for products."""
        return self._get_ecommerce_query().search_products(query_text, limit)
    
    @strawberry.field
    def garment_style(self, uuid: str) -> Optional[GarmentStyle]:
        """Get garment style by UUID."""
        return self._get_ecommerce_query().garment_style(uuid)
    
    @strawberry.field
    def garment_styles(self, filter: Optional[StyleFilter] = None) -> List[GarmentStyle]:
        """Get garment styles with filtering."""
        return self._get_ecommerce_query().garment_styles(filter)
    
    @strawberry.field
    def similar_styles(self, style_uuid: str, min_shared_features: int = 2) -> List[GarmentStyle]:
        """Find similar garment styles."""
        return self._get_ecommerce_query().similar_styles(style_uuid, min_shared_features)
    
    # Creator queries - delegate to sub-queries
    @strawberry.field
    def creator(self, slug: str) -> Optional[CreatorType]:
        """Get creator by slug with all handles."""
        return CreatorQuery().creator(slug)
    
    @strawberry.field
    def creators(self, limit: int = 20, offset: int = 0) -> List[CreatorType]:
        """Get list of creators."""
        return CreatorQuery().creators(limit, offset)
    
    @strawberry.field
    def feed(
        self,
        creator_id: str,
        filter: Optional[FeedFilter] = None,
    ) -> List[Media]:
        """Get aggregated omni-feed for a creator."""
        return FeedQuery().feed(creator_id, filter)
    
    # imageboard queries - delegate to ChanQueryType
    _chan_query = None
    
    def _get_chan_query(self):
        """Lazy initialization of ChanQueryType."""
        if self._chan_query is None:
            from .chan_schema import ChanQueryType
            self._chan_query = ChanQueryType()
        return self._chan_query
    
    @strawberry.field
    def chan_thread(self, board: str, thread_id: int) -> Optional[ChanThread]:
        """Get a specific imageboard thread."""
        return self._get_chan_query().thread(board, thread_id)
    
    @strawberry.field
    def chan_threads(self, filter: Optional[ThreadFilter] = None) -> List[ChanThread]:
        """Get list of imageboard threads."""
        return self._get_chan_query().threads(filter)
    
    @strawberry.field
    def chan_thread_chain(self, board: str, thread_id: int) -> List[ChanThread]:
        """Get thread chain (continuation threads)."""
        return self._get_chan_query().thread_chain(board, thread_id)
    
    @strawberry.field
    def chan_posts(self, filter: Optional[PostFilter] = None) -> List[ChanPost]:
        """Get imageboard posts."""
        return self._get_chan_query().posts(filter)
    
    @strawberry.field
    def chan_images(self, board: Optional[str] = None, thread_id: Optional[int] = None, limit: int = 50) -> List[ChanImage]:
        """Get images from imageboard threads."""
        return self._get_chan_query().images(board, thread_id, limit)
    
    @strawberry.field
    def chan_stats(self) -> ChanStats:
        """Get imageboard statistics."""
        return self._get_chan_query().chan_stats()
    
    @strawberry.field
    def cached_data(self, key: str) -> Optional[str]:
        """Get cached data from Valkey."""
        return self._get_chan_query().cached_data(key)
    
    @strawberry.field
    def stats(self) -> FeedStats:
        """Get feed statistics."""
        try:
            neo4j = get_connection()
            
            # Total posts
            query = "MATCH (p:Post) RETURN count(p) as total"
            result = neo4j.execute_read(query)
            total_posts = result[0]["total"] if result else 0
            
            # Total subreddits
            query = "MATCH (s:Subreddit) RETURN count(s) as total"
            result = neo4j.execute_read(query)
            total_subreddits = result[0]["total"] if result else 0
            
            # Total users
            query = "MATCH (u:User) RETURN count(u) as total"
            result = neo4j.execute_read(query)
            total_users = result[0]["total"] if result else 0
            
            # Posts today
            query = """
            MATCH (p:Post)
            WHERE date(p.created_utc) = date()
            RETURN count(p) as total
            """
            result = neo4j.execute_read(query)
            posts_today = result[0]["total"] if result else 0
            
            return FeedStats(
                total_posts=total_posts,
                total_subreddits=total_subreddits,
                total_users=total_users,
                posts_today=posts_today,
            )
        except Exception as e:
            print(f"Error getting stats: {e}")
            return FeedStats(total_posts=0, total_subreddits=0, total_users=0, posts_today=0)
    
    @strawberry.field
    def subreddits(self) -> List[Subreddit]:
        """Get all subreddits."""
        try:
            neo4j = get_connection()
            query = """
            MATCH (s:Subreddit)
            OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
            RETURN s.name as name, count(p) as post_count
            ORDER BY post_count DESC
            """
            result = neo4j.execute_read(query)
            return [
                Subreddit(name=record["name"], post_count=record["post_count"])
                for record in result
            ]
        except Exception as e:
            print(f"Error getting subreddits: {e}")
            return []
    
    @strawberry.field
    def feed_list(self, subreddit: Optional[str] = None) -> List[FeedList]:
        """Get feed lists for subreddits."""
        try:
            neo4j = get_connection()
            
            if subreddit:
                # Single subreddit
                query = """
                MATCH (s:Subreddit {name: $subreddit})
                OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
                OPTIONAL MATCH (u:User)-[:POSTED]->(p)
                RETURN s.name as subreddit,
                       collect({
                           id: p.id,
                           title: p.title,
                           created_utc: toString(p.created_utc),
                           score: p.score,
                           num_comments: p.num_comments,
                           upvote_ratio: p.upvote_ratio,
                           over_18: p.over_18,
                           url: p.url,
                           selftext: p.selftext,
                           permalink: p.permalink,
                           author: u.username
                       }) as posts,
                       count(p) as total_count
                """
                result = neo4j.execute_read(query, parameters={"subreddit": subreddit})
            else:
                # All subreddits
                query = """
                MATCH (s:Subreddit)
                OPTIONAL MATCH (s)<-[:POSTED_IN]-(p:Post)
                OPTIONAL MATCH (u:User)-[:POSTED]->(p)
                WITH s, p, u
                ORDER BY p.created_utc DESC
                RETURN s.name as subreddit,
                       collect({
                           id: p.id,
                           title: p.title,
                           created_utc: toString(p.created_utc),
                           score: p.score,
                           num_comments: p.num_comments,
                           upvote_ratio: p.upvote_ratio,
                           over_18: p.over_18,
                           url: p.url,
                           selftext: p.selftext,
                           permalink: p.permalink,
                           author: u.username
                       })[0..20] as posts,
                       count(p) as total_count
                """
                result = neo4j.execute_read(query)
            
            feed_lists = []
            for record in result:
                posts_data = []
                for post_data in record["posts"]:
                    if post_data.get("id"):  # Skip None posts
                        is_image = (
                            "i.redd.it" in post_data.get("url", "").lower() or
                            "reddit.com/gallery" in post_data.get("url", "").lower()
                        )
                        posts_data.append(Post(
                            id=post_data["id"],
                            title=post_data.get("title", ""),
                            created_utc=post_data.get("created_utc", ""),
                            score=post_data.get("score", 0),
                            num_comments=post_data.get("num_comments", 0),
                            upvote_ratio=post_data.get("upvote_ratio", 0.0),
                            over_18=post_data.get("over_18", False),
                            url=post_data.get("url", ""),
                            selftext=post_data.get("selftext", ""),
                            permalink=post_data.get("permalink"),
                            subreddit=record["subreddit"],
                            author=post_data.get("author"),
                            is_image=is_image,
                            image_url=post_data.get("url") if is_image else None,
                        ))
                
                feed_lists.append(FeedList(
                    subreddit=record["subreddit"],
                    posts=posts_data,
                    total_count=record["total_count"],
                ))
            
            return feed_lists
        except Exception as e:
            print(f"Error getting feed list: {e}")
            return []
    
    @strawberry.field
    def posts(self, filter: Optional[PostFilter] = None) -> List[Post]:
        """Get posts with filtering."""
        try:
            neo4j = get_connection()
            
            filter_obj = filter or PostFilter()
            
            # Build query
            where_clauses = []
            params = {
                "limit": filter_obj.limit,
                "offset": filter_obj.offset,
            }
            
            if filter_obj.subreddit:
                where_clauses.append("s.name = $subreddit")
                params["subreddit"] = filter_obj.subreddit
            
            if filter_obj.min_score is not None:
                where_clauses.append("p.score >= $min_score")
                params["min_score"] = filter_obj.min_score
            
            if filter_obj.is_image is not None:
                if filter_obj.is_image:
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
            ORDER BY p.created_utc DESC
            SKIP $offset
            LIMIT $limit
            """
            
            result = neo4j.execute_read(query, parameters=params)
            
            posts = []
            for record in result:
                is_image = (
                    "i.redd.it" in record.get("url", "").lower() or
                    "reddit.com/gallery" in record.get("url", "").lower()
                )
                posts.append(Post(
                    id=record["id"],
                    title=record.get("title", ""),
                    created_utc=record.get("created_utc", ""),
                    score=record.get("score", 0),
                    num_comments=record.get("num_comments", 0),
                    upvote_ratio=record.get("upvote_ratio", 0.0),
                    over_18=record.get("over_18", False),
                    url=record.get("url", ""),
                    selftext=record.get("selftext", ""),
                    permalink=record.get("permalink"),
                    subreddit=record["subreddit"],
                    author=record.get("author"),
                    is_image=is_image,
                    image_url=record.get("url") if is_image else None,
                ))
            
            return posts
        except Exception as e:
            print(f"Error getting posts: {e}")
            return []
    
    # Image search queries - delegate to ImageSearchQuery
    _image_search_query = None
    
    def _get_image_search_query(self):
        """Lazy initialization of ImageSearchQuery."""
        if self._image_search_query is None:
            self._image_search_query = ImageSearchQuery()
        return self._image_search_query
    
    @strawberry.field
    def check_image_crawled(self, image_url: str) -> ImageLookupResultType:
        """Check if an image URL has already been crawled/stored."""
        return self._get_image_search_query().check_image_crawled(image_url)
    
    @strawberry.field
    def find_image_source(
        self,
        image_url: str,
        include_external: bool = False
    ) -> ImageLookupResultType:
        """Find the original source of an image."""
        return self._get_image_search_query().find_image_source(image_url, include_external)
    
    @strawberry.field
    def find_exact_matches(
        self,
        image_url: str,
        include_external: bool = False
    ) -> ImageLookupResultType:
        """Find all exact and near-exact matches of an image."""
        return self._get_image_search_query().find_exact_matches(image_url, include_external)
    
    @strawberry.field
    def find_similar_images(
        self,
        image_url: str,
        min_similarity: float = 0.85,
        limit: int = 10
    ) -> SimilarImageResult:
        """Find visually similar images using CLIP embeddings."""
        return self._get_image_search_query().find_similar_images(image_url, min_similarity, limit)
    
    @strawberry.field
    def check_image_status(self, image_url: str) -> ImageStatusResult:
        """Check status of an image and determine if recovery is needed."""
        return self._get_image_search_query().check_image_status(image_url)
    
    @strawberry.field
    def public_image_search(
        self,
        image_url: str,
        providers: Optional[List[ImageSearchProvider]] = None
    ) -> PublicSearchResult:
        """Search external reverse image search APIs."""
        return self._get_image_search_query().public_image_search(image_url, providers)
    
    @strawberry.field
    def find_image_matches(self, image_url: str) -> ImageMatchResult:
        """Find image matches with ontology integration."""
        return self._get_image_search_query().find_image_matches(image_url)
    
    @strawberry.field
    def identify_video(
        self,
        video_path: str,
        watermark_patterns: Optional[List[str]] = None,
        stash_url: Optional[str] = None
    ) -> VideoIdentificationResultType:
        """Identify video using watermark detection, face matching, and database lookups."""
        return self._get_image_search_query().identify_video(video_path, watermark_patterns, stash_url)
    
    @strawberry.field
    def stash_scenes(
        self,
        stash_url: str,
        studio: Optional[str] = None,
        performer_name: Optional[str] = None,
        limit: int = 50
    ) -> List[StashSceneType]:
        """Query Stash instance for scenes."""
        return self._get_image_search_query().stash_scenes(stash_url, studio, performer_name, limit)
    
    @strawberry.field
    def stash_performers(
        self,
        stash_url: str,
        query: Optional[str] = None,
        limit: int = 50
    ) -> List[StashPerformerType]:
        """Query Stash instance for performers."""
        return self._get_image_search_query().stash_performers(stash_url, query, limit)


@strawberry.type
class Mutation:
    """GraphQL mutations."""
    
    # Image search mutations - delegate to ImageSearchMutation
    _image_search_mutation = None
    
    def _get_image_search_mutation(self):
        """Lazy initialization of ImageSearchMutation."""
        if self._image_search_mutation is None:
            self._image_search_mutation = ImageSearchMutation()
        return self._image_search_mutation
    
    @strawberry.mutation
    def recover_post(self, post_url: str) -> RecoveryResult:
        """Recover a missed Reddit post and ingest it into the database."""
        return self._get_image_search_mutation().recover_post(post_url)
    
    @strawberry.mutation
    def index_image(self, image_url: str) -> IndexResult:
        """Index an image for future reverse search."""
        return self._get_image_search_mutation().index_image(image_url)


@strawberry.type
class Subscription:
    """GraphQL subscriptions for real-time updates."""
    
    @strawberry.subscription
    async def feed_updates(self, subreddit: Optional[str] = None) -> Post:
        """Subscribe to new posts in real-time."""
        # This is a simplified version - in production, you'd use a message queue
        # or WebSocket connection to push updates
        import asyncio
        
        # For demo, we'll poll and yield new posts
        last_seen_ids = set()
        
        while True:
            try:
                neo4j = get_connection()
                
                if subreddit:
                    query = """
                    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit {name: $subreddit})
                    OPTIONAL MATCH (u:User)-[:POSTED]->(p)
                    RETURN p.id as id, p.title as title, toString(p.created_utc) as created_utc,
                           p.score as score, p.num_comments as num_comments, p.upvote_ratio as upvote_ratio,
                           p.over_18 as over_18, p.url as url, p.selftext as selftext, p.permalink as permalink,
                           s.name as subreddit, u.username as author
                    ORDER BY p.created_utc DESC
                    LIMIT 10
                    """
                    params = {"subreddit": subreddit}
                else:
                    query = """
                    MATCH (p:Post)-[:POSTED_IN]->(s:Subreddit)
                    OPTIONAL MATCH (u:User)-[:POSTED]->(p)
                    RETURN p.id as id, p.title as title, toString(p.created_utc) as created_utc,
                           p.score as score, p.num_comments as num_comments, p.upvote_ratio as upvote_ratio,
                           p.over_18 as over_18, p.url as url, p.selftext as selftext, p.permalink as permalink,
                           s.name as subreddit, u.username as author
                    ORDER BY p.created_utc DESC
                    LIMIT 10
                    """
                    params = {}
                
                result = neo4j.execute_read(query, parameters=params)
                
                for record in result:
                    post_id = record["id"]
                    if post_id not in last_seen_ids:
                        last_seen_ids.add(post_id)
                        
                        is_image = (
                            "i.redd.it" in record.get("url", "").lower() or
                            "reddit.com/gallery" in record.get("url", "").lower()
                        )
                        
                        post = Post(
                            id=record["id"],
                            title=record.get("title", ""),
                            created_utc=record.get("created_utc", ""),
                            score=record.get("score", 0),
                            num_comments=record.get("num_comments", 0),
                            upvote_ratio=record.get("upvote_ratio", 0.0),
                            over_18=record.get("over_18", False),
                            url=record.get("url", ""),
                            selftext=record.get("selftext", ""),
                            permalink=record.get("permalink"),
                            subreddit=record["subreddit"],
                            author=record.get("author"),
                            is_image=is_image,
                            image_url=record.get("url") if is_image else None,
                        )
                        
                        yield post
                
                await asyncio.sleep(5)  # Poll every 5 seconds
                
            except Exception as e:
                print(f"Error in subscription: {e}")
                await asyncio.sleep(5)


# Create schema with all queries, mutations, and subscriptions
schema = strawberry.Schema(
    query=Query,
    mutation=Mutation,
    subscription=Subscription,
)


def create_graphql_router() -> GraphQLRouter:
    """Create GraphQL router with WebSocket support."""
    return GraphQLRouter(
        schema,
    )

