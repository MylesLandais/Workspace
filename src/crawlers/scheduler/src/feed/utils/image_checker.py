"""Utilities for checking if images exist in the database."""

from typing import List, Dict, Optional, Any
from ..storage.neo4j_connection import get_connection
from .image_hash import hash_image_url


def check_image_by_url(image_url: str) -> Dict[str, Any]:
    """
    Check if an image exists in the database by URL or hash.
    
    Args:
        image_url: Image URL to check
        
    Returns:
        Dictionary with search results
    """
    neo4j = get_connection()
    
    result = {
        "found": False,
        "url": image_url,
        "matches_by_url": [],
        "matches_by_hash": [],
        "matches_by_dhash": [],
        "hash": None,
        "dhash": None,
    }
    
    # Check by URL first
    query_by_url = """
    MATCH (p:Post)
    WHERE p.url = $url
    RETURN p.id as post_id,
           p.title as title,
           p.url as url,
           p.image_hash as image_hash,
           p.image_dhash as image_dhash,
           p.created_utc as created,
           p.subreddit as subreddit
    LIMIT 10
    """
    
    results = neo4j.execute_read(query_by_url, parameters={"url": image_url})
    if results:
        result["found"] = True
        result["matches_by_url"] = [
            {
                "post_id": r.get("post_id"),
                "title": r.get("title"),
                "subreddit": r.get("subreddit"),
                "created": r.get("created"),
                "image_hash": r.get("image_hash"),
                "image_dhash": r.get("image_dhash"),
            }
            for r in results
        ]
        return result
    
    # Compute hash and check by hash
    try:
        image_hash, image_dhash = hash_image_url(image_url, timeout=10)
        result["hash"] = image_hash
        result["dhash"] = image_dhash
        
        if image_hash:
            # Check by SHA-256 hash
            query_by_hash = """
            MATCH (p:Post)
            WHERE p.image_hash = $hash
            RETURN p.id as post_id,
                   p.title as title,
                   p.url as url,
                   p.image_hash as image_hash,
                   p.image_dhash as image_dhash,
                   p.created_utc as created,
                   p.subreddit as subreddit
            LIMIT 10
            """
            
            results = neo4j.execute_read(
                query_by_hash,
                parameters={"hash": image_hash}
            )
            
            if results:
                result["found"] = True
                result["matches_by_hash"] = [
                    {
                        "post_id": r.get("post_id"),
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "subreddit": r.get("subreddit"),
                        "created": r.get("created"),
                        "image_hash": r.get("image_hash"),
                        "image_dhash": r.get("image_dhash"),
                    }
                    for r in results
                ]
            
            # Check by dHash if available
            if image_dhash:
                query_by_dhash = """
                MATCH (p:Post)
                WHERE p.image_dhash = $dhash
                RETURN p.id as post_id,
                       p.title as title,
                       p.url as url,
                       p.image_hash as image_hash,
                       p.image_dhash as image_dhash,
                       p.created_utc as created,
                       p.subreddit as subreddit
                LIMIT 10
                """
                
                results = neo4j.execute_read(
                    query_by_dhash,
                    parameters={"dhash": image_dhash}
                )
                
                if results:
                    result["found"] = True
                    result["matches_by_dhash"] = [
                        {
                            "post_id": r.get("post_id"),
                            "title": r.get("title"),
                            "url": r.get("url"),
                            "subreddit": r.get("subreddit"),
                            "created": r.get("created"),
                            "image_hash": r.get("image_hash"),
                            "image_dhash": r.get("image_dhash"),
                        }
                        for r in results
                    ]
        
    except Exception as e:
        result["error"] = str(e)
    
    # Check Image nodes
    query_image_nodes = """
    MATCH (img:Image)
    WHERE img.url = $url
    RETURN img.url as url,
           img.hash as hash,
           count { (p:Post)-[:HAS_IMAGE]->(img) } as post_count
    LIMIT 10
    """
    
    results = neo4j.execute_read(
        query_image_nodes,
        parameters={"url": image_url}
    )
    
    if results:
        result["found"] = True
        result["image_nodes"] = [
            {
                "url": r.get("url"),
                "hash": r.get("hash"),
                "post_count": r.get("post_count"),
            }
            for r in results
        ]
    
    return result


def check_image_by_hash(image_hash: str) -> List[Dict[str, Any]]:
    """
    Check if an image exists in the database by SHA-256 hash.
    
    Args:
        image_hash: SHA-256 hash of the image
        
    Returns:
        List of matching posts
    """
    neo4j = get_connection()
    
    query = """
    MATCH (p:Post)
    WHERE p.image_hash = $hash
    RETURN p.id as post_id,
           p.title as title,
           p.url as url,
           p.image_hash as image_hash,
           p.image_dhash as image_dhash,
           p.created_utc as created,
           p.subreddit as subreddit
    LIMIT 20
    """
    
    results = neo4j.execute_read(query, parameters={"hash": image_hash})
    
    return [
        {
            "post_id": r.get("post_id"),
            "title": r.get("title"),
            "url": r.get("url"),
            "subreddit": r.get("subreddit"),
            "created": r.get("created"),
            "image_hash": r.get("image_hash"),
            "image_dhash": r.get("image_dhash"),
        }
        for r in results
    ]


def get_image_statistics() -> Dict[str, int]:
    """
    Get statistics about images in the database.
    
    Returns:
        Dictionary with statistics
    """
    neo4j = get_connection()
    
    stats = {}
    
    queries = {
        "posts_with_images": """
        MATCH (p:Post)
        WHERE p.image_hash IS NOT NULL
        RETURN count(p) as count
        """,
        "unique_image_hashes": """
        MATCH (p:Post)
        WHERE p.image_hash IS NOT NULL
        RETURN count(DISTINCT p.image_hash) as count
        """,
        "posts_with_dhash": """
        MATCH (p:Post)
        WHERE p.image_dhash IS NOT NULL
        RETURN count(p) as count
        """,
        "image_nodes": """
        MATCH (img:Image)
        RETURN count(img) as count
        """,
        "posts_linked_to_images": """
        MATCH (p:Post)-[:HAS_IMAGE]->(img:Image)
        RETURN count(DISTINCT p) as count
        """,
    }
    
    for key, query in queries.items():
        try:
            result = neo4j.execute_read(query)
            if result:
                stats[key] = result[0].get("count", 0)
        except Exception:
            stats[key] = 0
    
    return stats




