#!/usr/bin/env python3
"""
Archive a Reddit post with all images and metadata for Internet Archive upload.

This script:
1. Fetches the Reddit post and comments using the Reddit API
2. Extracts all image URLs (including galleries and comment images)
3. Downloads all images locally
4. Creates an index JSON file with all URLs
5. Creates an HTML archive file with local image references for Internet Archive
"""

import sys
import json
import os
import re
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse, unquote
from typing import List, Dict, Any, Optional
import requests
from html import escape

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from feed.platforms.reddit import RedditAdapter


class RedditPostArchiver:
    """Archive Reddit posts with full image caching for Internet Archive."""

    def __init__(self, output_dir: str = "data/archived_reddit"):
        """
        Initialize archiver.
        
        Args:
            output_dir: Base directory for archived content
        """
        self.output_dir = Path(output_dir)
        self.images_dir = self.output_dir / "images"
        self.metadata_dir = self.output_dir / "metadata"
        
        # Create directories
        self.images_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize Reddit adapter
        self.reddit = RedditAdapter(
            user_agent="Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            delay_min=1.0,
            delay_max=2.0,
            mock=False
        )
        
        # Track all URLs for index
        self.all_urls = {
            "post_url": None,
            "reddit_api_url": None,
            "image_urls": [],
            "comment_image_urls": [],
            "other_urls": []
        }
        
        # Track downloaded files
        self.downloaded_files = []

    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for filesystem."""
        # Remove or replace invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove leading/trailing spaces and dots
        filename = filename.strip(' .')
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:200-len(ext)] + ext
        return filename

    def _download_image(self, url: str, referrer: str = None) -> Optional[str]:
        """
        Download an image and return local filename.
        
        Args:
            url: Image URL to download
            referrer: Optional referrer URL for the request
            
        Returns:
            Local filename relative to images_dir, or None if download failed
        """
        try:
            headers = {
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
            }
            if referrer:
                headers["Referer"] = referrer
            
            response = requests.get(url, headers=headers, timeout=30, stream=True)
            response.raise_for_status()
            
            # Determine filename
            parsed = urlparse(url)
            original_filename = unquote(os.path.basename(parsed.path))
            
            # If no extension or unclear extension, try to get from content-type
            if not original_filename or '.' not in original_filename:
                content_type = response.headers.get('Content-Type', '')
                if 'image/jpeg' in content_type or 'image/jpg' in content_type:
                    ext = '.jpg'
                elif 'image/png' in content_type:
                    ext = '.png'
                elif 'image/gif' in content_type:
                    ext = '.gif'
                elif 'image/webp' in content_type:
                    ext = '.webp'
                else:
                    # Try to extract from URL
                    ext = os.path.splitext(parsed.path)[1] or '.jpg'
                # Use a hash or timestamp-based name
                original_filename = f"image_{hash(url) % 1000000}{ext}"
            
            # Sanitize filename
            filename = self._sanitize_filename(original_filename)
            
            # Ensure unique filename
            filepath = self.images_dir / filename
            counter = 1
            while filepath.exists():
                name, ext = os.path.splitext(filename)
                filepath = self.images_dir / f"{name}_{counter}{ext}"
                counter += 1
            filename = filepath.name
            
            # Download file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.downloaded_files.append({
                "url": url,
                "local_filename": filename,
                "size_bytes": filepath.stat().st_size
            })
            
            print(f"  Downloaded: {filename} ({filepath.stat().st_size} bytes)")
            return filename
            
        except Exception as e:
            print(f"  Failed to download {url}: {e}")
            return None

    def archive_post(self, post_url: str) -> Dict[str, Any]:
        """
        Archive a Reddit post with all images and metadata.
        
        Args:
            post_url: Full Reddit post URL
            
        Returns:
            Dictionary with archive metadata
        """
        print(f"Archiving post: {post_url}")
        self.all_urls["post_url"] = post_url
        
        # Extract permalink from URL
        if post_url.startswith("http"):
            parsed = urlparse(post_url)
            permalink = parsed.path
        else:
            permalink = post_url
        
        # Remove trailing slash
        permalink = permalink.rstrip("/")
        
        # Fetch thread data
        print("Fetching post and comments...")
        post, comments, raw_post_data = self.reddit.fetch_thread(permalink)
        
        if not post:
            raise ValueError(f"Failed to fetch post: {post_url}")
        
        # Store Reddit API URL
        api_url = f"https://www.reddit.com{permalink}.json"
        self.all_urls["reddit_api_url"] = api_url
        
        # Extract post images
        print("Extracting post images...")
        post_images = self.reddit.extract_all_images(post, raw_post_data)
        self.all_urls["image_urls"] = post_images
        
        # Extract comment images
        print("Extracting comment images...")
        comment_images_data = self.reddit.extract_images_from_comments(comments)
        comment_image_urls = [img["url"] for img in comment_images_data]
        self.all_urls["comment_image_urls"] = comment_image_urls
        
        # Download all images
        print(f"\nDownloading {len(post_images)} post images...")
        post_image_files = {}
        for img_url in post_images:
            local_file = self._download_image(img_url, referrer=post_url)
            if local_file:
                post_image_files[img_url] = local_file
        
        print(f"\nDownloading {len(comment_image_urls)} comment images...")
        comment_image_files = {}
        for img_url in comment_image_urls:
            local_file = self._download_image(img_url, referrer=post_url)
            if local_file:
                comment_image_files[img_url] = local_file
        
        # Create post ID-based directory for this archive
        archive_id = post.id
        archive_dir = self.output_dir / archive_id
        archive_dir.mkdir(exist_ok=True)
        
        # Create index JSON
        index_data = {
            "archive_created": datetime.utcnow().isoformat(),
            "post_url": post_url,
            "reddit_api_url": api_url,
            "post_data": {
                "id": post.id,
                "title": post.title,
                "author": post.author,
                "subreddit": post.subreddit,
                "created_utc": post.created_utc.isoformat() if post.created_utc else None,
                "score": post.score,
                "num_comments": post.num_comments,
                "upvote_ratio": post.upvote_ratio,
                "over_18": post.over_18,
                "selftext": post.selftext,
                "permalink": post.permalink,
                "original_url": post.url
            },
            "images": {
                "post_images": [
                    {
                        "url": url,
                        "local_filename": post_image_files.get(url),
                        "downloaded": url in post_image_files
                    }
                    for url in post_images
                ],
                "comment_images": [
                    {
                        "url": img["url"],
                        "comment_id": img.get("comment_id"),
                        "author": img.get("author"),
                        "local_filename": comment_image_files.get(img["url"]),
                        "downloaded": img["url"] in comment_image_files
                    }
                    for img in comment_images_data
                ]
            },
            "comments_count": len(comments),
            "comments_sample": [
                {
                    "id": c.id,
                    "author": c.author,
                    "body": c.body[:200] + "..." if len(c.body) > 200 else c.body,
                    "score": c.score,
                    "created_utc": c.created_utc.isoformat() if c.created_utc else None
                }
                for c in comments[:10]  # First 10 comments as sample
            ],
            "all_urls": self.all_urls,
            "downloaded_files": self.downloaded_files
        }
        
        # Save index JSON
        index_file = archive_dir / "index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        print(f"\nIndex saved to: {index_file}")
        
        # Create HTML archive file for Internet Archive
        html_file = archive_dir / "archive.html"
        self._create_html_archive(
            html_file,
            post,
            comments,
            post_image_files,
            comment_image_files,
            comment_images_data,
            raw_post_data
        )
        print(f"HTML archive saved to: {html_file}")
        
        # Create a URLs list file (simple text format)
        urls_file = archive_dir / "urls.txt"
        with open(urls_file, 'w', encoding='utf-8') as f:
            f.write(f"Post URL: {post_url}\n")
            f.write(f"Reddit API URL: {api_url}\n\n")
            f.write("Post Images:\n")
            for url in post_images:
                f.write(f"{url}\n")
            f.write("\nComment Images:\n")
            for url in comment_image_urls:
                f.write(f"{url}\n")
        print(f"URLs list saved to: {urls_file}")
        
        return index_data

    def _create_html_archive(
        self,
        html_file: Path,
        post,
        comments: List,
        post_image_files: Dict[str, str],
        comment_image_files: Dict[str, str],
        comment_images_data: List[Dict],
        raw_post_data: Optional[Dict]
    ):
        """Create HTML archive file with local image references."""
        
        # Group comment images by comment ID
        comment_images_by_id = {}
        for img_data in comment_images_data:
            comment_id = img_data.get("comment_id")
            if comment_id:
                if comment_id not in comment_images_by_id:
                    comment_images_by_id[comment_id] = []
                comment_images_by_id[comment_id].append(img_data)
        
        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{escape(post.title)} - Reddit Archive</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #1a1a1a;
            color: #d7dadc;
        }}
        .header {{
            background: #030303;
            border: 1px solid #343536;
            border-radius: 4px;
            padding: 16px;
            margin-bottom: 20px;
        }}
        .post-title {{
            font-size: 18px;
            font-weight: 500;
            margin-bottom: 8px;
            color: #d7dadc;
        }}
        .post-meta {{
            font-size: 12px;
            color: #818384;
            margin-bottom: 8px;
        }}
        .post-content {{
            margin-top: 12px;
            color: #d7dadc;
            white-space: pre-wrap;
        }}
        .images {{
            margin: 20px 0;
        }}
        .image-container {{
            margin-bottom: 16px;
            background: #1a1a1a;
            border: 1px solid #343536;
            border-radius: 4px;
            padding: 8px;
        }}
        .image-container img {{
            max-width: 100%;
            height: auto;
            display: block;
            border-radius: 4px;
        }}
        .comments {{
            margin-top: 30px;
        }}
        .comment {{
            background: #1a1a1a;
            border: 1px solid #343536;
            border-radius: 4px;
            padding: 12px;
            margin-bottom: 12px;
        }}
        .comment-header {{
            font-size: 12px;
            color: #818384;
            margin-bottom: 8px;
        }}
        .comment-body {{
            color: #d7dadc;
            white-space: pre-wrap;
            margin-bottom: 8px;
        }}
        .comment-images {{
            margin-top: 8px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #343536;
            font-size: 12px;
            color: #818384;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="header">
        <div class="post-title">{escape(post.title)}</div>
        <div class="post-meta">
            r/{escape(post.subreddit)} | by u/{escape(post.author or '[deleted]')} | 
            {post.score} points | {post.num_comments} comments
        </div>
"""
        
        # Add post selftext if present
        if post.selftext:
            html_content += f'        <div class="post-content">{escape(post.selftext)}</div>\n'
        
        html_content += '    </div>\n'
        
        # Add post images
        if post_image_files:
            html_content += '    <div class="images">\n'
            for url, local_file in post_image_files.items():
                # Use relative path from HTML file to images directory
                image_path = f"../images/{local_file}"
                html_content += f'        <div class="image-container">\n'
                html_content += f'            <img src="{image_path}" alt="Post image" loading="lazy">\n'
                html_content += f'        </div>\n'
            html_content += '    </div>\n'
        
        # Add comments
        if comments:
            html_content += '    <div class="comments">\n'
            html_content += f'        <h2>Comments ({len(comments)})</h2>\n'
            for comment in comments[:100]:  # Limit to first 100 comments for HTML
                html_content += '        <div class="comment">\n'
                html_content += f'            <div class="comment-header">\n'
                html_content += f'                u/{escape(comment.author or "[deleted]")} | {comment.score} points\n'
                html_content += '            </div>\n'
                html_content += f'            <div class="comment-body">{escape(comment.body)}</div>\n'
                
                # Add comment images if any
                if comment.id in comment_images_by_id:
                    html_content += '            <div class="comment-images">\n'
                    for img_data in comment_images_by_id[comment.id]:
                        img_url = img_data["url"]
                        if img_url in comment_image_files:
                            image_path = f"../images/{comment_image_files[img_url]}"
                            html_content += f'                <img src="{image_path}" alt="Comment image" loading="lazy" style="max-width: 600px; margin-top: 8px;">\n'
                    html_content += '            </div>\n'
                
                html_content += '        </div>\n'
            html_content += '    </div>\n'
        
        # Add footer
        html_content += f"""    <div class="footer">
        Archived on {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
    </div>
</body>
</html>
"""
        
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(html_content)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Archive a Reddit post with all images for Internet Archive"
    )
    parser.add_argument(
        "post_url",
        help="Reddit post URL to archive"
    )
    parser.add_argument(
        "--output-dir",
        default="data/archived_reddit",
        help="Output directory for archived content (default: data/archived_reddit)"
    )
    
    args = parser.parse_args()
    
    archiver = RedditPostArchiver(output_dir=args.output_dir)
    
    try:
        index_data = archiver.archive_post(args.post_url)
        print("\n" + "="*60)
        print("Archive complete!")
        print(f"Post ID: {index_data['post_data']['id']}")
        print(f"Images downloaded: {len([f for f in index_data['downloaded_files']])}")
        print(f"Archive directory: {archiver.output_dir / index_data['post_data']['id']}")
        print("="*60)
    except Exception as e:
        print(f"\nError archiving post: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()







