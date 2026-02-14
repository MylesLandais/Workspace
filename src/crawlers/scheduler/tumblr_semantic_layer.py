#!/usr/bin/env python3
"""
Tumblr Data Mining and Semantic Layer Example

This script demonstrates how to use the TumblrAdapter to mine blog content
and extract rich semantic context for knowledge graph construction.
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any

# Import TumblrAdapter
from src.feed.platforms.tumblr import TumblrAdapter


def extract_semantic_entities(post, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract semantic entities from a Tumblr post for knowledge graph.

    Args:
        post: Post object
        metadata: Post metadata (images, tags)

    Returns:
        Dictionary with extracted entities and relationships
    """
    entities = {
        'post_id': post.id,
        'url': post.url,
        'created_at': post.created_utc.isoformat() if post.created_utc else None,
        'author': post.author,
        'blog': post.subreddit,
        'title': post.title,
        'content': post.selftext,
        'images': metadata.get('images', []),
        'tags': metadata.get('tags', []),
        'entity_types': [],
        'mentions': [],
        'hashtags': []
    }

    content = post.selftext.lower()

    # Extract hashtags from tags and content
    for tag in metadata.get('tags', []):
        entities['hashtags'].append(f"#{tag}")
        entities['entity_types'].append('tag')

    # Detect common entity patterns in content
    content_patterns = {
        'location': ['philadelphia', 'nyc', 'la', 'chicago', 'usa', 'united states'],
        'activity': ['travel', 'bedroom', 'home', 'decor', 'design'],
        'mood': ['love', 'happy', 'excited', 'amazing'],
    }

    for entity_type, keywords in content_patterns.items():
        for keyword in keywords:
            if keyword in content:
                entities['mentions'].append({
                    'type': entity_type,
                    'value': keyword
                })
                if entity_type not in entities['entity_types']:
                    entities['entity_types'].append(entity_type)

    return entities


def build_semantic_layer(posts: List[Any], adapter: TumblrAdapter) -> List[Dict[str, Any]]:
    """
    Build semantic layer from Tumblr posts.

    Args:
        posts: List of Post objects
        adapter: TumblrAdapter instance

    Returns:
        List of semantic entities
    """
    semantic_layer = []

    for post in posts:
        metadata = adapter.get_post_metadata(post.id)
        if metadata:
            entity = extract_semantic_entities(post, metadata)
            semantic_layer.append(entity)

    return semantic_layer


def export_to_json(entities: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export semantic entities to JSON file.

    Args:
        entities: List of semantic entities
        output_path: Output file path
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(entities, f, indent=2, ensure_ascii=False)
    print(f"Exported {len(entities)} entities to {output_path}")


def export_to_neo4j_format(entities: List[Dict[str, Any]], output_path: str) -> None:
    """
    Export semantic entities in Neo4j Cypher format for knowledge graph import.

    Args:
        entities: List of semantic entities
        output_path: Output file path
    """
    cypher_statements = []

    for entity in entities:
        # Create blog node
        blog_cypher = f"""
        MERGE (b:Blog {{name: '{entity['blog']}}')
        ON CREATE SET b.created_at = datetime()
        """
        cypher_statements.append(blog_cypher)

        # Create post node
        title_escaped = entity['title'].replace("'", "\\'")
        post_cypher = f"""
        MERGE (p:Post {{id: '{entity['post_id']}'}})
        SET p.url = '{entity['url']}',
            p.created_at = datetime('{entity['created_at']}'),
            p.title = '{title_escaped}'
        """
        cypher_statements.append(post_cypher)

        # Create relationship: Blog -> Post
        rel_cypher = f"""
        MATCH (b:Blog {{name: '{entity['blog']}'}})
        MATCH (p:Post {{id: '{entity['post_id']}'}})
        MERGE (b)-[:PUBLISHED]->(p)
        """
        cypher_statements.append(rel_cypher)

        # Create image nodes and relationships
        for idx, img_url in enumerate(entity['images']):
            img_cypher = f"""
            MERGE (i{idx}:Image {{url: '{img_url}'}})
            MERGE (p:Post {{id: '{entity['post_id']}'}})
            MERGE (p)-[:HAS_IMAGE]->(i{idx})
            """
            cypher_statements.append(img_cypher)

        # Create tag nodes and relationships
        for tag in entity['tags']:
            tag_cypher = f"""
            MERGE (t:Tag {{name: '{tag}'}})
            MERGE (p:Post {{id: '{entity['post_id']}'}})
            MERGE (p)-[:HAS_TAG]->(t)
            """
            cypher_statements.append(tag_cypher)

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(cypher_statements))

    print(f"Exported Neo4j Cypher statements to {output_path}")


def main():
    """Main execution flow."""
    print("Tumblr Data Mining and Semantic Layer Builder")
    print("=" * 60)

    # Initialize adapter
    adapter = TumblrAdapter(
        delay_min=2.0,
        delay_max=5.0,
        mock=False  # Set to True for testing without network
    )

    # Configure blog to mine
    blog_url = "https://blackswandive.tumblr.com"
    print(f"\nMining blog: {blog_url}")

    # Fetch posts
    print("Fetching posts...")
    posts, _ = adapter.fetch_posts(
        source=blog_url,
        limit=20,
        scrape_content=True
    )

    print(f"Fetched {len(posts)} posts")

    # Build semantic layer
    print("\nBuilding semantic layer...")
    semantic_entities = build_semantic_layer(posts, adapter)

    print(f"Extracted {len(semantic_entities)} semantic entities")

    # Display sample entity
    if semantic_entities:
        print("\nSample semantic entity:")
        sample = semantic_entities[0]
        print(f"  Post ID: {sample['post_id']}")
        print(f"  Blog: {sample['blog']}")
        print(f"  Author: {sample['author']}")
        print(f"  Images: {len(sample['images'])}")
        print(f"  Tags: {sample['tags']}")
        print(f"  Entity Types: {sample['entity_types']}")
        print(f"  Mentions: {len(sample['mentions'])}")

    # Export to JSON
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_output = f"data/tumblr_semantic_{timestamp}.json"
    os.makedirs('data', exist_ok=True)
    export_to_json(semantic_entities, json_output)

    # Export to Neo4j format
    neo4j_output = f"data/tumblr_neo4j_{timestamp}.cypher"
    export_to_neo4j_format(semantic_entities, neo4j_output)

    print("\n" + "=" * 60)
    print("Data mining complete!")
    print("\nNext steps:")
    print("  1. Review JSON output for semantic entities")
    print("  2. Import Cypher statements to Neo4j knowledge graph")
    print("  3. Query the graph for insights and relationships")


if __name__ == "__main__":
    main()
