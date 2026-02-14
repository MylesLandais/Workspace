#!/usr/bin/env python3
"""
Tumblr User Feed Example: barbie-expectations

Demonstrates fetching and analyzing a specific Tumblr user's feed.
"""

import os
import json
from datetime import datetime
from collections import Counter
from typing import List, Dict, Any

from src.feed.platforms.tumblr import TumblrAdapter


def analyze_post_patterns(posts: List[Any], adapter: TumblrAdapter) -> Dict[str, Any]:
    """
    Analyze patterns in Tumblr posts.

    Args:
        posts: List of Post objects
        adapter: TumblrAdapter instance

    Returns:
        Dictionary with analysis results
    """
    analysis = {
        'total_posts': len(posts),
        'total_images': 0,
        'total_tags': 0,
        'unique_tags': set(),
        'post_dates': [],
        'content_lengths': [],
        'image_urls': [],
        'tag_frequency': Counter(),
        'posts_by_month': Counter(),
        'entities': []
    }

    for post in posts:
        metadata = adapter.get_post_metadata(post.id)
        if metadata:
            # Count images
            analysis['total_images'] += len(metadata['images'])
            analysis['image_urls'].extend(metadata['images'])

            # Count tags
            tags = metadata.get('tags', [])
            analysis['total_tags'] += len(tags)
            analysis['unique_tags'].update(tags)
            analysis['tag_frequency'].update(tags)

            # Track post dates
            if post.created_utc:
                month_key = post.created_utc.strftime("%Y-%m")
                analysis['posts_by_month'][month_key] += 1
                analysis['post_dates'].append(post.created_utc)

            # Track content length
            if post.selftext:
                analysis['content_lengths'].append(len(post.selftext))

            # Extract entities for semantic layer
            analysis['entities'].append({
                'post_id': post.id,
                'url': post.url,
                'created_at': post.created_utc.isoformat() if post.created_utc else None,
                'title': post.title,
                'images': metadata.get('images', []),
                'tags': metadata.get('tags', []),
                'author': post.author,
                'blog': post.subreddit
            })

    # Convert set to list for JSON serialization
    analysis['unique_tags'] = list(analysis['unique_tags'])

    return analysis


def print_feed_summary(analysis: Dict[str, Any]) -> None:
    """Print a human-readable summary of the feed analysis."""
    print("\n" + "=" * 60)
    print("TUMBLR FEED ANALYSIS SUMMARY")
    print("=" * 60)

    print(f"\n📊 Basic Stats:")
    print(f"   Total Posts: {analysis['total_posts']}")
    print(f"   Total Images: {analysis['total_images']}")
    print(f"   Avg Images/Post: {analysis['total_images'] / analysis['total_posts']:.2f}")
    print(f"   Total Tags: {analysis['total_tags']}")
    print(f"   Unique Tags: {len(analysis['unique_tags'])}")

    print(f"\n📅 Posting Activity:")
    if analysis['posts_by_month']:
        for month, count in sorted(analysis['posts_by_month'].items()):
            print(f"   {month}: {count} posts")

    print(f"\n🏷️  Top Tags:")
    if analysis['tag_frequency']:
        for tag, count in analysis['tag_frequency'].most_common(10):
            print(f"   #{tag} ({count})")

    print(f"\n📝 Content Stats:")
    if analysis['content_lengths']:
        avg_length = sum(analysis['content_lengths']) / len(analysis['content_lengths'])
        print(f"   Avg Content Length: {avg_length:.0f} characters")
        print(f"   Min: {min(analysis['content_lengths'])} chars")
        print(f"   Max: {max(analysis['content_lengths'])} chars")

    print(f"\n🖼️  Recent Images (first 5):")
    for img_url in analysis['image_urls'][:5]:
        print(f"   {img_url}")

    print("\n" + "=" * 60)


def export_feed_data(analysis: Dict[str, Any], blog_name: str) -> None:
    """
    Export feed analysis to JSON files.

    Args:
        analysis: Feed analysis dictionary
        blog_name: Name of the blog for filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = "data/tumblr_feeds"
    os.makedirs(output_dir, exist_ok=True)

    # Export full analysis
    analysis_path = f"{output_dir}/{blog_name}_analysis_{timestamp}.json"
    with open(analysis_path, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, ensure_ascii=False, default=str)
    print(f"\n✅ Analysis exported to: {analysis_path}")

    # Export entities only for semantic layer
    entities_path = f"{output_dir}/{blog_name}_entities_{timestamp}.json"
    with open(entities_path, 'w', encoding='utf-8') as f:
        json.dump(analysis['entities'], f, indent=2, ensure_ascii=False, default=str)
    print(f"✅ Entities exported to: {entities_path}")


def create_sample_posts_display(posts: List[Any], adapter: TumblrAdapter, limit: int = 5) -> None:
    """
    Display sample posts in a readable format.

    Args:
        posts: List of Post objects
        adapter: TumblrAdapter instance
        limit: Number of posts to display
    """
    print("\n" + "=" * 60)
    print(f"SAMPLE POSTS (showing {min(limit, len(posts))} of {len(posts)})")
    print("=" * 60)

    for idx, post in enumerate(posts[:limit]):
        print(f"\n📝 Post #{idx + 1}")
        print(f"   ID: {post.id}")
        print(f"   Title: {post.title}")
        print(f"   URL: {post.url}")
        print(f"   Created: {post.created_utc}")

        metadata = adapter.get_post_metadata(post.id)
        if metadata:
            if metadata['images']:
                print(f"   Images: {len(metadata['images'])}")
                for img in metadata['images'][:2]:
                    print(f"      - {img}")

            if metadata['tags']:
                print(f"   Tags: {', '.join(metadata['tags'][:10])}")

            if post.selftext:
                preview = post.selftext[:200]
                print(f"   Content: {preview}...")


def main():
    """Main execution flow for barbie-expectations.tumblr.com feed."""
    print("TUMBLR USER FEED ANALYZER")
    print("=" * 60)

    # Initialize adapter
    adapter = TumblrAdapter(
        delay_min=2.0,
        delay_max=5.0,
        mock=False  # Set to True for testing
    )

    # Target blog
    blog_url = "https://barbie-expectations.tumblr.com"
    blog_name = "barbie-expectations"

    print(f"\n🎯 Analyzing blog: {blog_url}")
    print("Fetching recent posts...")

    # Fetch posts
    posts, next_token = adapter.fetch_posts(
        source=blog_url,
        limit=50,  # Fetch last 50 posts
        scrape_content=True  # Enable full content scraping
    )

    if not posts:
        print("❌ No posts found. Check the blog URL or try again later.")
        return

    print(f"✅ Fetched {len(posts)} posts")

    # Display sample posts
    create_sample_posts_display(posts, adapter, limit=3)

    # Analyze feed patterns
    print("\n📊 Analyzing feed patterns...")
    analysis = analyze_post_patterns(posts, adapter)

    # Print summary
    print_feed_summary(analysis)

    # Export data
    print("\n💾 Exporting data...")
    export_feed_data(analysis, blog_name)

    # Additional semantic insights
    print("\n🔍 Semantic Insights:")
    print(f"   - Blog focuses on: {analysis['tag_frequency'].most_common(3)}")
    print(f"   - Content style: {'Image-heavy' if analysis['total_images'] > len(posts) * 0.8 else 'Text-heavy'}")
    print(f"   - Tag diversity: High ({len(analysis['unique_tags'])} unique tags)")

    print("\n" + "=" * 60)
    print("✅ Analysis complete!")
    print("\nGenerated files:")
    print("  1. Analysis JSON: Full statistics and metrics")
    print("  2. Entities JSON: Semantic entities for knowledge graph")
    print("\nNext steps:")
    print("  - Import entities to Neo4j for relationship mapping")
    print("  - Use images for visual content analysis")
    print("  - Analyze tag patterns for content clustering")


if __name__ == "__main__":
    main()
