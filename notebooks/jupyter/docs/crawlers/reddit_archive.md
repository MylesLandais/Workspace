# Reddit Post Archiver for Internet Archive

This tool archives Reddit posts with all images and metadata, preparing everything for Internet Archive upload with fully cached images.

## Features

- Fetches Reddit post and comments using the Reddit JSON API
- Extracts all image URLs (including gallery posts and comment images)
- Downloads all images locally with proper caching
- Creates a comprehensive index JSON file with all URLs
- Creates an HTML archive file with local image references
- Prepares complete archive package for Internet Archive upload

## Usage

### Option 1: Python Script

```bash
python archive_reddit_post.py "https://www.reddit.com/r/TaylorSwiftPictures/comments/1pt3bnb/loving_the_look/"
```

Or with custom output directory:

```bash
python archive_reddit_post.py "POST_URL" --output-dir "data/my_archives"
```

### Option 2: Jupyter Notebook

Open `notebooks/archive_reddit_post.ipynb` and run the cells. This provides an interactive way to archive posts and view the results.

## Output Structure

The archiver creates the following structure:

```
data/archived_reddit/
├── images/                          # All downloaded images (shared across archives)
│   ├── image1.jpg
│   ├── image2.png
│   └── ...
└── {post_id}/                       # Archive directory for specific post
    ├── index.json                   # Complete index with all URLs and metadata
    ├── archive.html                 # HTML file with local image references
    └── urls.txt                     # Simple text file with all URLs
```

## Index JSON Structure

The `index.json` file contains:

- `archive_created`: Timestamp when archive was created
- `post_url`: Original Reddit post URL
- `reddit_api_url`: Reddit JSON API URL used
- `post_data`: Complete post metadata (title, author, score, etc.)
- `images`: All image URLs with download status
  - `post_images`: Images from the post itself
  - `comment_images`: Images found in comments
- `comments_count`: Total number of comments
- `comments_sample`: Sample of first 10 comments
- `all_urls`: Complete list of all URLs referenced
- `downloaded_files`: List of all downloaded files with sizes

## All URLs Index

The index includes all URLs for recreating the dataset:

- Post URL: The original Reddit post URL
- Reddit API URL: The JSON API endpoint used
- Post Image URLs: All images from the post (including gallery images)
- Comment Image URLs: All images found in comments

## HTML Archive

The `archive.html` file is designed for Internet Archive upload:

- Uses relative paths to the `images/` directory
- All images are cached locally
- Reddit-style dark theme for readability
- Includes post content, all images, and comments
- Images use relative paths so they work when uploaded to Internet Archive

## Internet Archive Upload

To upload to Internet Archive:

1. Archive the post using the script/notebook
2. The archive directory contains everything needed:
   - `archive.html` - Main HTML file
   - `images/` directory - All cached images
   - `index.json` - Complete metadata and URLs
   - `urls.txt` - Simple URL list for reference

3. When uploading to Internet Archive:
   - Upload the entire `{post_id}/` directory
   - Ensure the `images/` directory is included (or upload separately and adjust paths)
   - The HTML file references images using relative paths `../images/filename.jpg`

## Example

```python
from archive_reddit_post import RedditPostArchiver

archiver = RedditPostArchiver(output_dir="data/archived_reddit")
index_data = archiver.archive_post(
    "https://www.reddit.com/r/TaylorSwiftPictures/comments/1pt3bnb/loving_the_look/"
)

print(f"Archived post {index_data['post_data']['id']}")
print(f"Downloaded {len(index_data['downloaded_files'])} images")
```

## Notes

- Images are downloaded with proper headers and referrers to avoid 403 errors
- Filenames are sanitized for filesystem compatibility
- Duplicate downloads are avoided (same URL = same filename)
- Gallery posts are fully supported with all images extracted
- Comment images are extracted from markdown and direct URLs






