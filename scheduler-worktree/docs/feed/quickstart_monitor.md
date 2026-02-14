# Quick Start - Feed Monitor

## Option 1: Jupyter Notebook (Recommended for Analysis)

```bash
# Open in JupyterLab
# Navigate to: notebooks/feed_monitor.ipynb
# Run all cells to see statistics, charts, and analysis
```

## Option 2: Web Interface (Real-time Dashboard)

### Start the Server

```bash
# In Docker container
docker exec -d -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py

# Check if it's running
docker exec jupyter curl http://localhost:8000/api/stats
```

### Access the Interface

Open in browser: **http://localhost:8000**

(If running in Docker, you may need to port-forward: `docker port jupyter`)

### Features

- **Live Dashboard**: Auto-refreshes every 30 seconds
- **Statistics**: Total posts, subreddits, users
- **Recent Posts**: Latest posts with metadata
- **Image Gallery**: Visual grid of collected images
- **REST API**: Programmatic access to all data

### API Examples

```bash
# Get statistics
curl http://localhost:8000/api/stats

# Get latest 20 posts
curl http://localhost:8000/api/posts?limit=20

# Get images from a subreddit
curl "http://localhost:8000/api/images?limit=10&subreddit=BrookeMonkTheSecond"

# List all subreddits
curl http://localhost:8000/api/subreddits
```

## Next Steps: NordStream Interface

The current web interface is a foundation. To build the full NordStream-style interface:

1. **Frontend**: Bun + TypeScript + Tailwind CSS
2. **Features**: 
   - Infinite masonry grid
   - Lightbox viewer
   - Graph-based filtering
   - "More like this" recommendations
3. **Backend**: Keep FastAPI as API layer

Would you like me to start building the NordStream interface?







