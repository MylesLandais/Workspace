# Imageboard Analytics Dashboard

A visual analytics dashboard showing most reposted images and deduplication statistics.

## Features

- **Most Reposted Images**: Top 100 images sorted by repost count
- **Visual Analytics**: Interactive charts showing reuse distribution and storage savings
- **Sorting Options**: Sort by reposts, file size, or space saved
- **Real-time Data**: Analytics generated from current cache

## Accessing the Dashboard

### Method 1: Via Web API
```
http://localhost:8000/api/analytics
```

### Method 2: Direct HTML File
Open `/home/warby/Workspace/jupyter/analytics.html` in a web browser

## Updating Analytics

To refresh the analytics data with the latest cache:

```bash
# Update analytics.html with current data
docker compose exec jupyterlab python generate_analytics.py
```

Or access the live API endpoint:
```
http://localhost:8000/api/analytics/data
```

## Statistics Shown

- **Total Image References**: How many times images are referenced across threads
- **Unique Images**: Number of distinct images after deduplication
- **Duplicates Prevented**: How many duplicate downloads were prevented
- **Storage Used**: Current storage size of unique images
- **Space Saved**: Storage saved by deduplication
- **Threads Crawled**: Number of threads currently cached

## Charts

1. **Image Reuse Distribution**: Bar chart showing how many images are used N times
2. **Storage Analysis**: Doughnut chart comparing unique storage vs space saved

## Top Reposted Images

Each image card shows:
- Repost count
- File size
- Space saved by deduplication
- First thread where image appeared
- Thumbnail preview

## Technical Details

- Images are stored by SHA256 hash
- Deduplication prevents storing duplicate content
- Analytics scan all cached threads in `/home/jovyan/workspaces/cache/imageboard/threads/`
- Images served from `/home/jovyan/workspaces/cache/imageboard/shared_images/`

## Recent Data

Last update: Generated from 17,237 image references
- Space saved: 0.78 GB
- Top reposted image: Used 15 times
- Duplicates prevented: 1,858 images
