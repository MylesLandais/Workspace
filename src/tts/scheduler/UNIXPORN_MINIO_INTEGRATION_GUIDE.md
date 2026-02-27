# Unixporn Dataset MinIO Integration Guide

## Overview

This document supersedes the previous integration guide. The r/unixporn media has been migrated from local disk storage to a MinIO (S3-compatible) bucket to resolve path and embedding issues. Client applications must now use public HTTP URLs for media access.

## Message to the Integration Team

This dataset has been prepared for robust, cloud-native access. The major change is the migration of all media (images, videos) from a local disk path to a shared MinIO bucket (`unixporn-media`).

**Key Context for Bunny Project Integration (~/Workspace/bunny):**

*   **Media Access:** Do not rely on local file paths or server-side mounts like `/static/unixporn/`. Use the public `media_url` field in the JSON data directly for client-side embedding (e.g., in `<img>` or `<video>` tags).
*   **Shared Services:** The `Public Endpoint` (`http://localhost:9000`) uses the shared MinIO service configured in the main development stack. Ensure your team's project has connectivity to this service or its external proxy.
*   **Data Source:** Consume the data from `data/unixporn_latest.json`. It is guaranteed to contain the MinIO URLs for all available media.

This shift resolves path and embedding issues, ensuring a scalable and reliable media serving solution.

## Dataset Location

### JSON Data Files
The primary data is available via the symlink:
`data/unixporn_latest.json` (Currently points to `unixporn_minio_ready.json`)

### MinIO Media Access Details

| Key | Value |
| :--- | :--- |
| **Bucket Name** | `unixporn-media` |
| **Object Prefix** | `unixporn/` |
| **Public Endpoint** | `http://localhost:9000` |
| **Full URL Pattern** | `{Endpoint}/{Bucket}/{Prefix}/{PostID}.{Ext}` |

**Example Media URL:**
`http://localhost:9000/unixporn-media/unixporn/1pwvpyb.mp4`

## Data Structure Changes

The `local_media_path` field has been removed and replaced with `media_url`.

### Updated Post JSON Schema
```json
{
  "id": "1pwvpyb",
  "title": "[OC] \"Ninite\" for Linux?...",
  "subreddit": "r/unixporn",
  "url": "https://v.redd.it/zkjardx7eq9g1",
  "media_url": "http://localhost:9000/unixporn-media/unixporn/1pwvpyb.mp4",
  "local_media_path": null,  // Legacy: will be null
  // ... other fields
}
```

### Key Fields
- `local_media_path`: **DEPRECATED**. Will be null in the new data.
- `media_url`: **NEW**. Public HTTP URL to the media object hosted on MinIO.

## Accessing Data

### Querying JSON for Posts with Media

The new metadata file contains the direct URL, simplifying queries.

```bash
# Get all posts with media_url populated
jq '.[] | select(.media_url != null) | {id, title, media_url}' \
  data/unixporn_latest.json

# Filter by media type (e.g., videos)
jq '.[] | select(.media_url | endswith(".mp4"))' \
  data/unixporn_latest.json
```

### Programmatic Access (Python)

```python
import json
import requests # If you need to stream the media

# Load latest dataset
with open('data/unixporn_latest.json') as f:
    posts = json.load(f)

# Process posts with media
for post in posts:
    if post.get('media_url'):
        # Use the URL directly for embedding in clients
        media_url = post['media_url']
        
        print(f"Post: {post['id']}")
        print(f"  Title: {post['title']}")
        print(f"  Media URL: {media_url}")
        
        # Example: Check if URL is live
        # response = requests.head(media_url)
        # print(f"  MinIO Status: {response.status_code}")
```

## API Integration (Proposed)

The API should now read the MinIO-ready JSON and return the `media_url` field directly, eliminating the need for local path construction.

```python
@app.get("/api/unixporn/posts")
async def get_unixporn_posts(
    limit: int = 20,
    offset: int = 0,
    has_media: bool = True  # Default to true since media is now reliable
):
    """Get unixporn posts with optional media filter."""
    with open('data/unixporn_latest.json') as f:
        posts = json.load(f)

    # Apply filter for posts that have a media URL
    if has_media:
        posts = [p for p in posts if p.get('media_url')]

    # Paginate
    paginated = posts[offset:offset + limit]

    return paginated
```

## Integration Checklist (MinIO Focus)

- [x] Media serving strategy is MinIO
- [ ] MinIO public access is configured (Check external host setup)
- [ ] Implement MinIO-based image URL access in GraphQL/REST responses
- [ ] Test media access from web client against MinIO (using the new `media_url` field)
- [ ] Implement MinIO-compatible caching headers (e.g., CDN in front of MinIO)
- [ ] Add error handling for missing media (MinIO fallback)
- [ ] Document API endpoints for frontend team
- [ ] Verify all old references to local paths are removed

