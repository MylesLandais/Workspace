# Analytics Dashboard - Quick Access

## Access the Dashboard

**Method 1: Direct Browser (Recommended)**
```
http://localhost:8000/analytics.html
```

**Method 2: JupyterLab**
1. Open http://localhost:8888
2. Navigate to workspaces/
3. Click on analytics.html
4. Right-click and select "Open in New Browser Tab"

## Troubleshooting

**Can't access http://localhost:8000/analytics.html?**

Check if server is running:
```bash
docker compose exec jupyterlab ps aux | grep serve_analytics
```

If not running, start it:
```bash
docker compose exec -d jupyterlab python serve_analytics_on_port8000.py
```

**Images not loading?**
- Images load from `/home/jovyan/workspaces/cache/imageboard/shared_images/`
- Check file exists:
```bash
docker compose exec jupyterlab ls /home/jovyan/workspaces/cache/imageboard/shared_images/ | wc -l
```

## Current Status

```bash
# Check if dashboard is accessible
curl -I http://localhost:8000/analytics.html

# Should return: HTTP/1.0 200 OK
```

## Stats

- Total References: 17,237
- Unique Images: 14,743
- Duplicates Prevented: 1,858
- Space Saved: 0.78 GB
