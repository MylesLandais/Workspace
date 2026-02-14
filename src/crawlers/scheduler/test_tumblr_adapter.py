#!/usr/bin/env python3
"""Test script for Tumblr adapter."""

from src.feed.platforms.tumblr import TumblrAdapter

def main():
    adapter = TumblrAdapter()

    print("Testing Tumblr Adapter")
    print("=" * 60)

    blog_url = "https://blackswandive.tumblr.com"
    print(f"\nFetching posts from: {blog_url}")

    posts, next_token = adapter.fetch_posts(
        source=blog_url,
        limit=5,
        scrape_content=True
    )

    print(f"\nFetched {len(posts)} posts")

    for post in posts:
        print(f"\nPost ID: {post.id}")
        print(f"Title: {post.title}")
        print(f"URL: {post.url}")
        print(f"Created: {post.created_utc}")
        print(f"Author: {post.author}")

        metadata = adapter.get_post_metadata(post.id)
        if metadata:
            print(f"Images: {len(metadata.get('images', []))}")
            print(f"Tags: {metadata.get('tags', [])}")

    print("\n" + "=" * 60)
    print("Fetching blog metadata...")

    metadata = adapter.fetch_source_metadata(blog_url)
    if metadata:
        print(f"Blog name: {metadata.name}")
        print(f"Description: {metadata.description}")
        print(f"Public description: {metadata.public_description}")

if __name__ == "__main__":
    main()
