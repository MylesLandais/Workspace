"""Neo4j storage for Reddit threads with comments and images."""

from datetime import datetime
from typing import List, Optional, Dict, Any
from ..models.post import Post
from ..models.comment import Comment
from .neo4j_connection import Neo4jConnection
from ..utils.reddit_url_extractor import extract_reddit_urls
from ..utils.youtube_url_extractor import extract_youtube_urls


def store_blog_post(
    neo4j: Neo4jConnection,
    post: Post,
    images: Optional[List[str]] = None,
    entity_matched: Optional[str] = None,
    creator_slug: Optional[str] = None,
) -> None:
    """
    Store a blog post in Neo4j.
    
    Args:
        neo4j: Neo4j connection instance
        post: Post object (from BlogAdapter)
        images: Optional list of image URLs from the post
        entity_matched: Optional entity name that matched this post
        creator_slug: Optional creator slug to link post to Creator entity
    """
    # Create blog source node (using Subreddit node type for compatibility)
    blog_name = post.subreddit
    subreddit_query = """
    MERGE (s:Subreddit {name: $name})
    ON CREATE SET s.created_at = datetime(),
                  s.source_type = 'blog'
    RETURN s
    """
    neo4j.execute_write(
        subreddit_query,
        parameters={"name": blog_name},
    )
    
    # Convert images list to format expected by store_thread
    image_dicts = []
    if images:
        for img_url in images:
            image_dicts.append({
                "url": img_url,
                "source": "post",
                "post_id": post.id,
            })
    
    # Store using existing store_thread function (with empty comments)
    store_thread(neo4j, post, [], image_dicts)
    
    # Add entity match metadata if provided
    if entity_matched:
        entity_query = """
        MATCH (p:Post {id: $post_id})
        SET p.entity_matched = $entity,
            p.updated_at = datetime()
        RETURN p.id as id
        """
        neo4j.execute_write(
            entity_query,
            parameters={
                "post_id": post.id,
                "entity": entity_matched,
            }
        )
    
    # Link post to Creator entity if provided
    if creator_slug:
        link_post_query = """
        MATCH (c:Creator {slug: $creator_slug})
        MATCH (p:Post {id: $post_id})
        MERGE (p)-[r:ABOUT]->(c)
        ON CREATE SET
            r.created_at = datetime()
        RETURN r
        """
        neo4j.execute_write(
            link_post_query,
            parameters={
                "creator_slug": creator_slug,
                "post_id": post.id,
            }
        )
        
        # Link blog source to Creator entity
        link_source_query = """
        MATCH (c:Creator {slug: $creator_slug})
        MATCH (s:Subreddit {name: $blog_name})
        MERGE (c)-[r:HAS_SOURCE]->(s)
        ON CREATE SET 
            r.source_type = 'blog',
            r.discovered_at = datetime(),
            r.created_at = datetime()
        ON MATCH SET
            r.updated_at = datetime()
        RETURN r
        """
        neo4j.execute_write(
            link_source_query,
            parameters={
                "creator_slug": creator_slug,
                "blog_name": blog_name,
            }
        )


def store_thread(
    neo4j: Neo4jConnection,
    post: Post,
    comments: List[Comment],
    images: List[Dict[str, Any]],
    raw_post_data: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Store a Reddit thread (post + comments + images) in Neo4j.
    
    Args:
        neo4j: Neo4j connection instance
        post: Post object
        comments: List of Comment objects
        images: List of image dicts with 'url' and optional 'source', 'comment_id', etc.
        raw_post_data: Optional raw post data from Reddit API
    """
    # Create subreddit node if it doesn't exist
    subreddit_query = """
    MERGE (s:Subreddit {name: $name})
    ON CREATE SET s.created_at = datetime()
    RETURN s
    """
    neo4j.execute_write(
        subreddit_query,
        parameters={"name": post.subreddit},
    )
    
    # Convert datetime to Unix timestamp for Neo4j
    created_timestamp = int(post.created_utc.timestamp())
    
    # Store the post
    post_query = """
    MERGE (p:Post {id: $id})
    SET p.title = $title,
        p.created_utc = datetime({epochSeconds: $created_utc}),
        p.score = $score,
        p.num_comments = $num_comments,
        p.upvote_ratio = $upvote_ratio,
        p.over_18 = $over_18,
        p.url = $url,
        p.selftext = $selftext,
        p.permalink = $permalink,
        p.updated_at = datetime()
    WITH p
    MATCH (s:Subreddit {name: $subreddit})
    MERGE (p)-[:POSTED_IN]->(s)
    """
    
    neo4j.execute_write(
        post_query,
        parameters={
            "id": post.id,
            "title": post.title,
            "created_utc": created_timestamp,
            "score": post.score,
            "num_comments": post.num_comments,
            "upvote_ratio": post.upvote_ratio,
            "over_18": post.over_18,
            "url": post.url,
            "selftext": post.selftext,
            "permalink": post.permalink,
            "subreddit": post.subreddit,
        },
    )
    
    # Create user node for post author and relationship
    if post.author:
        user_query = """
        MERGE (u:User {username: $username})
        ON CREATE SET u.created_at = datetime()
        WITH u
        MATCH (p:Post {id: $post_id})
        MERGE (u)-[:POSTED]->(p)
        """
        neo4j.execute_write(
            user_query,
            parameters={"username": post.author, "post_id": post.id},
        )
    
    # Store all images
    for img_data in images:
        img_url = img_data.get("url")
        if not img_url:
            continue
        
        # Create Image node
        params = {"url": img_url, "post_id": post.id}
        
        # Build query based on whether we have image_index or comment info
        if img_data.get("source") == "comment" and img_data.get("comment_id"):
            # Image from comment
            image_query = """
            MERGE (img:Image {url: $url})
            ON CREATE SET img.created_at = datetime()
            SET img.updated_at = datetime()
            WITH img
            MATCH (p:Post {id: $post_id})
            MERGE (p)-[:HAS_IMAGE]->(img)
            WITH img
            MATCH (c:Comment {id: $comment_id})
            MERGE (c)-[:HAS_IMAGE]->(img)
            """
            params["comment_id"] = img_data["comment_id"]
        elif img_data.get("image_index") is not None:
            # Image with index (gallery post)
            image_query = """
            MERGE (img:Image {url: $url})
            ON CREATE SET img.created_at = datetime()
            SET img.updated_at = datetime()
            WITH img
            MATCH (p:Post {id: $post_id})
            MERGE (p)-[r:HAS_IMAGE]->(img)
            SET r.image_index = $image_index
            """
            params["image_index"] = img_data.get("image_index")
        else:
            # Regular post image
            image_query = """
            MERGE (img:Image {url: $url})
            ON CREATE SET img.created_at = datetime()
            SET img.updated_at = datetime()
            WITH img
            MATCH (p:Post {id: $post_id})
            MERGE (p)-[:HAS_IMAGE]->(img)
            """
        
        neo4j.execute_write(image_query, parameters=params)
    
    # Store all comments
    for comment in comments:
        comment_timestamp = int(comment.created_utc.timestamp())
        
        # Create comment node
        comment_query = """
        MERGE (c:Comment {id: $id})
        SET c.body = $body,
            c.created_utc = datetime({epochSeconds: $created_utc}),
            c.score = $score,
            c.ups = $ups,
            c.downs = $downs,
            c.depth = $depth,
            c.is_submitter = $is_submitter,
            c.permalink = $permalink,
            c.updated_at = datetime()
        WITH c
        MATCH (p:Post {id: $post_id})
        MERGE (c)-[:COMMENTED_ON]->(p)
        """
        
        neo4j.execute_write(
            comment_query,
            parameters={
                "id": comment.id,
                "body": comment.body,
                "created_utc": comment_timestamp,
                "score": comment.score,
                "ups": comment.ups,
                "downs": comment.downs,
                "depth": comment.depth,
                "is_submitter": comment.is_submitter,
                "permalink": comment.permalink,
                "post_id": post.id,
            },
        )
        
        # Create user node for comment author and relationship
        if comment.author:
            comment_author_query = """
            MERGE (u:User {username: $username})
            ON CREATE SET u.created_at = datetime()
            WITH u
            MATCH (c:Comment {id: $comment_id})
            MERGE (u)-[:WROTE]->(c)
            """
            neo4j.execute_write(
                comment_author_query,
                parameters={"username": comment.author, "comment_id": comment.id},
            )
        
        # Create parent relationship if this is a reply
        if comment.parent_id:
            # parent_id format is either "t1_comment_id" or "t3_post_id"
            if comment.parent_id.startswith("t1_"):
                # Reply to another comment
                parent_comment_id = comment.parent_id[3:]  # Remove "t1_" prefix
                parent_query = """
                MATCH (parent:Comment {id: $parent_id})
                MATCH (child:Comment {id: $child_id})
                MERGE (child)-[:REPLIES_TO]->(parent)
                """
                neo4j.execute_write(
                    parent_query,
                    parameters={"parent_id": parent_comment_id, "child_id": comment.id},
                )
            # If parent is t3_post_id, it's a top-level comment (already linked via COMMENTED_ON)
    
    # Extract and store cross-thread relationships
    store_thread_relationships(neo4j, post, comments)


def store_thread_from_crawl_result(
    neo4j: Neo4jConnection,
    crawl_result: Dict[str, Any],
) -> None:
    """
    Store a thread from a crawl result dictionary.
    
    Args:
        neo4j: Neo4j connection instance
        crawl_result: Dictionary from crawl_thread() function
    """
    if not crawl_result.get("success"):
        print(f"Skipping failed crawl result: {crawl_result.get('permalink', 'unknown')}")
        return
    
    post_data = crawl_result.get("post", {})
    if not post_data.get("id"):
        print(f"Skipping crawl result without post ID")
        return
    
    # Convert post dict to Post object
    from datetime import datetime as dt
    post = Post(
        id=post_data["id"],
        title=post_data["title"],
        created_utc=dt.fromisoformat(post_data["created_utc"]),
        score=post_data.get("score", 0),
        num_comments=post_data.get("num_comments", 0),
        upvote_ratio=post_data.get("upvote_ratio", 0.0),
        over_18=post_data.get("over_18", False),
        url=post_data.get("url", ""),
        selftext=post_data.get("selftext", ""),
        author=post_data.get("author"),
        subreddit=post_data["subreddit"],
        permalink=post_data.get("permalink"),
    )
    
    # Convert comment dicts to Comment objects
    comments = []
    for comment_data in crawl_result.get("comments", []):
        comment = Comment(
            id=comment_data["id"],
            body=comment_data.get("body", ""),
            author=comment_data.get("author"),
            created_utc=dt.fromisoformat(comment_data["created_utc"]),
            score=comment_data.get("score", 0),
            ups=comment_data.get("ups", 0),
            downs=comment_data.get("downs", 0),
            parent_id=comment_data.get("parent_id"),
            link_id=f"t3_{post.id}",
            depth=comment_data.get("depth", 0),
            is_submitter=comment_data.get("is_submitter", False),
            permalink=comment_data.get("permalink"),
        )
        comments.append(comment)
    
    # Get images list
    images = crawl_result.get("images", [])
    
    # Store in Neo4j
    store_thread(neo4j, post, comments, images)
    
    # Extract and store cross-thread relationships
    store_thread_relationships(neo4j, post, comments)


def store_thread_relationships(
    neo4j: Neo4jConnection,
    post: Post,
    comments: List[Comment],
) -> None:
    """
    Extract and store relationships between this thread and other Reddit threads,
    as well as YouTube videos mentioned in the thread.
    
    Scans post selftext and all comments for Reddit URLs and YouTube links,
    creating relationships when found.
    
    Args:
        neo4j: Neo4j connection instance
        post: Post object
        comments: List of Comment objects
    """
    # Extract Reddit URLs from post selftext
    if post.selftext:
        reddit_urls = extract_reddit_urls(post.selftext)
        for url_info in reddit_urls:
            create_thread_relationship(
                neo4j,
                source_post_id=post.id,
                target_post_id=url_info.get("post_id"),
                target_permalink=url_info.get("permalink"),
                relationship_type="cross_reference",
                source_type="post",
                source_author=post.author,
            )
        
        # Extract YouTube URLs from post selftext
        youtube_urls = extract_youtube_urls(post.selftext)
        for url_info in youtube_urls:
            create_youtube_relationship(
                neo4j,
                source_post_id=post.id,
                video_id=url_info.get("video_id"),
                video_url=url_info.get("full_url"),
                source_type="post",
                source_author=post.author,
            )
    
    # Extract URLs from comments
    for comment in comments:
        if comment.body:
            reddit_urls = extract_reddit_urls(comment.body)
            for url_info in reddit_urls:
                create_thread_relationship(
                    neo4j,
                    source_post_id=post.id,
                    target_post_id=url_info.get("post_id"),
                    target_permalink=url_info.get("permalink"),
                    relationship_type="cross_reference",
                    source_type="comment",
                    source_author=comment.author,
                    comment_id=comment.id,
                )
            
            # Extract YouTube URLs from comments
            youtube_urls = extract_youtube_urls(comment.body)
            for url_info in youtube_urls:
                create_youtube_relationship(
                    neo4j,
                    source_post_id=post.id,
                    video_id=url_info.get("video_id"),
                    video_url=url_info.get("full_url"),
                    source_type="comment",
                    source_author=comment.author,
                    comment_id=comment.id,
                )


def create_thread_relationship(
    neo4j: Neo4jConnection,
    source_post_id: str,
    target_post_id: Optional[str],
    target_permalink: Optional[str],
    relationship_type: str = "cross_reference",
    source_type: str = "comment",
    source_author: Optional[str] = None,
    comment_id: Optional[str] = None,
) -> None:
    """
    Create a relationship between two Reddit threads.
    
    Args:
        neo4j: Neo4j connection instance
        source_post_id: ID of the post containing the reference
        target_post_id: ID of the referenced post (if known)
        target_permalink: Permalink of the referenced post
        relationship_type: Type of relationship ("cross_reference", "discusses", etc.)
        source_type: Where the reference was found ("post", "comment")
        source_author: Author of the source post/comment
        comment_id: ID of the comment if source_type is "comment"
    """
    if not target_post_id and not target_permalink:
        return
    
    # First, try to find target post by ID
    if target_post_id:
        # Check if target post exists in graph
        check_query = """
        MATCH (target:Post {id: $target_id})
        RETURN target.id as id
        LIMIT 1
        """
        result = neo4j.execute_read(check_query, parameters={"target_id": target_post_id})
        
        if result:
            # Target post exists, create relationship
            rel_query = """
            MATCH (source:Post {id: $source_id})
            MATCH (target:Post {id: $target_id})
            MERGE (source)-[r:RELATES_TO]->(target)
            ON CREATE SET r.relationship_type = $relationship_type,
                          r.source_type = $source_type,
                          r.source_author = $source_author,
                          r.comment_id = $comment_id,
                          r.discovered_at = datetime()
            ON MATCH SET r.updated_at = datetime()
            """
            neo4j.execute_write(
                rel_query,
                parameters={
                    "source_id": source_post_id,
                    "target_id": target_post_id,
                    "relationship_type": relationship_type,
                    "source_type": source_type,
                    "source_author": source_author or "",
                    "comment_id": comment_id or "",
                },
            )


def create_youtube_relationship(
    neo4j: Neo4jConnection,
    source_post_id: str,
    video_id: str,
    video_url: str,
    source_type: str = "comment",
    source_author: Optional[str] = None,
    comment_id: Optional[str] = None,
) -> None:
    """
    Create a relationship between a Reddit thread and a YouTube video.
    
    Args:
        neo4j: Neo4j connection instance
        source_post_id: ID of the post containing the YouTube link
        video_id: YouTube video ID
        video_url: Full YouTube URL
        source_type: Where the link was found ("post", "comment")
        source_author: Author of the source post/comment
        comment_id: ID of the comment if source_type is "comment"
    """
    if not video_id:
        return
    
    # Create or update YouTube video node
    video_query = """
    MERGE (v:YouTubeVideo {video_id: $video_id})
    ON CREATE SET v.url = $video_url,
                  v.created_at = datetime()
    SET v.updated_at = datetime()
    WITH v
    MATCH (p:Post {id: $source_id})
    MERGE (p)-[r:REFERENCES_VIDEO]->(v)
    ON CREATE SET r.source_type = $source_type,
                  r.source_author = $source_author,
                  r.comment_id = $comment_id,
                  r.discovered_at = datetime()
    ON MATCH SET r.updated_at = datetime()
    """
    
    neo4j.execute_write(
        video_query,
        parameters={
            "video_id": video_id,
            "video_url": video_url,
            "source_id": source_post_id,
            "source_type": source_type,
            "source_author": source_author or "",
            "comment_id": comment_id or "",
        },
    )
    return
    
    # If target not found by ID, create a placeholder node or wait
    # For now, we'll create a relationship with just the permalink
    # The target post will be linked when it's crawled
    if target_permalink:
        # Extract post ID from permalink if we have it
        if not target_post_id and target_permalink:
            parts = target_permalink.strip('/').split('/')
            if len(parts) >= 4 and parts[0] == 'r' and parts[2] == 'comments':
                target_post_id = parts[3]
        
        if target_post_id:
            # Create target post placeholder if it doesn't exist
            placeholder_query = """
            MERGE (target:Post {id: $target_id})
            ON CREATE SET target.permalink = $permalink,
                          target.placeholder = true,
                          target.created_at = datetime()
            WITH target
            MATCH (source:Post {id: $source_id})
            MERGE (source)-[r:RELATES_TO]->(target)
            ON CREATE SET r.relationship_type = $relationship_type,
                          r.source_type = $source_type,
                          r.source_author = $source_author,
                          r.comment_id = $comment_id,
                          r.discovered_at = datetime()
            ON MATCH SET r.updated_at = datetime()
            """
            neo4j.execute_write(
                placeholder_query,
                parameters={
                    "source_id": source_post_id,
                    "target_id": target_post_id,
                    "permalink": target_permalink,
                    "relationship_type": relationship_type,
                    "source_type": source_type,
                    "source_author": source_author or "",
                    "comment_id": comment_id or "",
                },
            )


def create_youtube_relationship(
    neo4j: Neo4jConnection,
    source_post_id: str,
    video_id: str,
    video_url: str,
    source_type: str = "comment",
    source_author: Optional[str] = None,
    comment_id: Optional[str] = None,
) -> None:
    """
    Create a relationship between a Reddit thread and a YouTube video.
    
    Args:
        neo4j: Neo4j connection instance
        source_post_id: ID of the post containing the YouTube link
        video_id: YouTube video ID
        video_url: Full YouTube URL
        source_type: Where the link was found ("post", "comment")
        source_author: Author of the source post/comment
        comment_id: ID of the comment if source_type is "comment"
    """
    if not video_id:
        return
    
    # Create or update YouTube video node
    video_query = """
    MERGE (v:YouTubeVideo {video_id: $video_id})
    ON CREATE SET v.url = $video_url,
                  v.created_at = datetime()
    SET v.updated_at = datetime()
    WITH v
    MATCH (p:Post {id: $source_id})
    MERGE (p)-[r:REFERENCES_VIDEO]->(v)
    ON CREATE SET r.source_type = $source_type,
                  r.source_author = $source_author,
                  r.comment_id = $comment_id,
                  r.discovered_at = datetime()
    ON MATCH SET r.updated_at = datetime()
    """
    
    neo4j.execute_write(
        video_query,
        parameters={
            "video_id": video_id,
            "video_url": video_url,
            "source_id": source_post_id,
            "source_type": source_type,
            "source_author": source_author or "",
            "comment_id": comment_id or "",
        },
    )

