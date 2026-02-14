# Imageboard Analytics Dashboard

Analytics dashboard showing most reposted images and deduplication statistics.

## Quick Start

```bash
# Generate analytics data
docker compose exec jupyterlab python generate_analytics.py

# Start analytics server
docker compose exec -d jupyterlab python serve_analytics_simple.py

# Access dashboard
# From host browser: http://localhost:8891
# From inside container: curl http://localhost:8891
```

## Access Methods

### 1. Via JupyterLab
- Open JupyterLab at http://localhost:8888
- Navigate to `/home/jovyan/workspaces/analytics.html`
- Click the file to view in browser

### 2. Via Dedicated Server
```bash
# Start server
docker compose exec -d jupyterlab python serve_analytics_simple.py

# Access at http://localhost:8891
```

### 3. Direct File Access
```bash
# View raw HTML
docker compose exec jupyterlab cat /home/jovyan/workspaces/analytics.html

# Copy file
docker cp $(docker compose ps -q jupyterlab):/home/jovyan/workspaces/analytics.html ./analytics.html
```

## Features

**Statistics Overview**
- Total image references across all threads
- Unique images after deduplication
- Duplicates prevented
- Storage used vs saved
- Threads crawled count

**Visual Charts**
- Image reuse distribution (bar chart)
- Storage analysis (doughnut chart)

**Most Reposted Images**
- Top 100 images sorted by repost count
- Sortable by: reposts, file size, space saved
- Thumbnail previews
- First thread tracking

**Data Source**
- Scans `/home/jovyan/workspaces/cache/imageboard/threads/`
- Images from `/home/jovyan/workspaces/cache/imageboard/shared_images/`
- SHA256-based deduplication

## Updating Analytics

```bash
# Refresh with latest cache data
docker compose exec jupyterlab python generate_analytics.py

# Server automatically serves updated file
# No restart needed
```

## Stopping Server

```bash
docker compose exec jupyterlab pkill -f serve_analytics_simple.py
```

## Current Stats

- **Total References**: 17,237
- **Unique Images**: 14,743
- **Duplicates Prevented**: 1,858
- **Space Saved**: 0.78 GB
- **Top Reposted**: 15 times

## Troubleshooting

**Server not responding**
```bash
# Check if running
docker compose exec jupyterlab ps aux | grep serve_analytics

# Check logs
docker compose exec jupyterlab cat /tmp/analytics_*.log

# Restart
docker compose exec jupyterlab pkill -f serve_analytics
docker compose exec -d jupyterlab python serve_analytics_simple.py
```

**Images not loading**
- Ensure static images path is correct in analytics.html
- Check that `/home/jovyan/workspaces/cache/imageboard/shared_images/` exists
- Images served via local paths relative to analytics.html

**No data shown**
```bash
# Regenerate analytics data
docker compose exec jupyterlab python generate_analytics.py

# Check JSON data
docker compose exec jupyterlab cat /home/jovyan/workspaces/analytics.html | grep -o '{{ANALYTICS_DATA}}' | wc -l
# Should be 1 (placeholder not replaced)
```
