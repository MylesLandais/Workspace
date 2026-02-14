# Feed Monitor - Viewing and Monitoring Collected Posts

Two ways to monitor your feed data:

## 1. Jupyter Notebook (Quick Analysis)

Open `notebooks/feed_monitor.ipynb` in JupyterLab for interactive data exploration:
- Overview statistics
- Activity timelines
- Engagement metrics
- Image posts analysis
- Top authors

## 2. Web Interface (Real-time Monitoring)

A FastAPI-based web interface with a clean, minimalist design.

### Start the Web Server

```bash
# In Docker container
docker exec -w /home/jovyan/workspace jupyter python3 src/feed/web/server.py

# Or locally
cd src/feed/web
python3 server.py
```

Then open: http://localhost:8000

### Features

- **Dashboard**: Real-time stats (total posts, subreddits, users)
- **Recent Posts**: Latest posts with metadata
- **Image Gallery**: Visual grid of collected images
- **Auto-refresh**: Updates every 30 seconds
- **API Endpoints**: RESTful API for programmatic access

### API Endpoints

- `GET /api/stats` - Overall statistics
- `GET /api/posts?limit=10&subreddit=BrookeMonkTheSecond` - Get posts
- `GET /api/images?limit=20` - Get image posts
- `GET /api/subreddits` - List all subreddits

### Example API Usage

```bash
# Get stats
curl http://localhost:8000/api/stats

# Get latest 20 posts
curl http://localhost:8000/api/posts?limit=20

# Get images from specific subreddit
curl http://localhost:8000/api/images?limit=10&subreddit=BestOfBrookeMonk
```

## Future: NordStream-Style Interface

The current web interface is a foundation. To build the full NordStream-style interface (Bun + TypeScript + Tailwind + infinite scroll), we can:

1. Create a separate frontend project using Bun
2. Keep the FastAPI backend as the API layer
3. Implement the masonry grid, lightbox viewer, and graph-based filtering

Let me know if you'd like me to start building the NordStream interface!







